#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tg_sync.py — Telethon-based sync of Telegram chats with direct clients.

Usage:
    python tg_sync.py --all                       # every client with a TG channel
    python tg_sync.py --client <client_id>            # one client
    python tg_sync.py --client <client_id>,<client_id>        # several
    python tg_sync.py --full --client <client_id>     # force full rescan
    python tg_sync.py --lookback-months 6 --all   # custom history depth

Rotation membership is DERIVED from each client's behavior.json (every client whose
channels declare a `telegram` channel is in rotation) — NOT from a hand-kept list.
A chat is resolved by, in order: cached peer_id -> @username -> phone, so a client
with only a display name + phone (no public @username) is still synced. tg_state.json
is a pure WATERMARK cache keyed by client id, never the membership list.

Reads:
    <repo>/secrets/tg_api.json     — api_id, api_hash, phone, session_name
    <data.dir>/clients_index.json  — roster (membership + display names)
    <data.dir>/clients/<id>/state/behavior.json — telegram channel + resolver
    <data.dir>/journal/tg_state.json — last_message_id + cached peer_id per client
Writes:
    <data.dir>/journal/inbox/tg_<today>.md  (append if exists, create otherwise)
    <data.dir>/journal/tg_state.json         (atomic, with timestamped backup)
"""
from __future__ import annotations
import argparse
import asyncio
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from telethon import TelegramClient
    from telethon.tl.custom.message import Message  # noqa: F401
except ImportError:
    print("ERROR: Telethon is not installed. Run: pip install telethon", file=sys.stderr)
    sys.exit(1)

# ============== Paths ==============
HERE = Path(__file__).resolve().parent                 # connectors/tg/
REPO_DIR = HERE.parent.parent                           # saldo/ (repo root)
ENGINE_DIR = REPO_DIR / "engine"

# The data dir (clients/ + journal/) is configured per-practice in
# config/instance.yaml — the SAME source the engine uses — not derived from the
# script's own location. Reuse engine/_config so the daemon and the dashboards
# always agree on which practice they are operating on.
def _resolve_data_dir() -> Path:
    import os
    if os.environ.get("ABA_DATA_DIR"):
        return Path(os.environ["ABA_DATA_DIR"]).resolve()
    try:
        sys.path.insert(0, str(ENGINE_DIR))
        from _config import DATA_DIR as _DD  # type: ignore
        return Path(_DD).resolve()
    except Exception:
        # Legacy / standalone fallback: journal next to the repo's parent.
        return REPO_DIR.parent.resolve()

DATA_DIR = _resolve_data_dir()
CLIENTS_DIR = DATA_DIR / "clients"
ROSTER_FILE = DATA_DIR / "clients_index.json"

SECRETS_FILE = REPO_DIR / "secrets" / "tg_api.json"
SESSION_PATH = REPO_DIR / "secrets" / "operator_session"  # Telethon will append .session
STATE_FILE = DATA_DIR / "journal" / "tg_state.json"
INBOX_DIR = DATA_DIR / "journal" / "inbox"
LOG_DIR = DATA_DIR / "journal" / "daemon_logs"

MSK = timezone(timedelta(hours=3))

# ============== Rotation set — derived from behavior.channels ==============
# The rotation is NOT a hand-kept list (that drifts: a TG client missing from the
# list is silently never read — the brukh incident). It is DERIVED at runtime from
# each client's state: every client whose behavior.json declares a telegram channel
# is in rotation. tg_state.json is then a pure WATERMARK cache keyed by client id
# (last_message_id + cached peer_id), never the membership list.

def load_roster() -> list:
    """Roster entries from clients_index.json (id + display name). [] if absent."""
    try:
        entries = json.loads(ROSTER_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [e for e in entries if isinstance(e, dict) and e.get("id")]

def _channels(behavior: dict) -> list:
    ch = (behavior or {}).get("channels") or {}
    out = []
    prim = ch.get("primary")
    if isinstance(prim, dict):
        out.append(prim)
    out += [c for c in (ch.get("secondary") or []) if isinstance(c, dict)]
    return out

def tg_resolver(behavior: dict) -> dict | None:
    """Extract how to REACH this client on Telegram from behavior.channels.

    Returns {label, username, phone} or None if the client has no telegram channel.
    `username` is the @handle when the channel id is one (else None); `phone` is the
    first phone channel on the client (Telethon can resolve a saved contact by phone
    even when no @username exists — the brukh case: display name + phone, no handle).
    """
    chans = _channels(behavior)
    tg = next((c for c in chans if c.get("type") == "telegram"), None)
    if tg is None:
        return None
    raw = str(tg.get("id") or "").strip()
    username = None
    if raw.startswith("@"):
        username = raw
    elif tg.get("username"):
        username = str(tg["username"]).strip()
    phone = next((str(c.get("id")).strip() for c in chans
                  if c.get("type") == "phone" and str(c.get("id") or "").strip()), None)
    peer_id = tg.get("peer_id")
    return {"label": raw or username or "", "username": username,
            "phone": phone, "peer_id": peer_id}

def load_behavior(cid: str) -> dict:
    p = CLIENTS_DIR / cid / "state" / "behavior.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

# ============== Helpers ==============

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def save_json_atomic(path: Path, data: dict) -> None:
    """Robust write: bytes + fsync + only-keep-last-3 backups (OneDrive-friendly)."""
    import os
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_suffix(path.suffix + f".bak_{ts}")
    if path.exists():
        shutil.copy2(path, backup)

    payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    tmp = path.with_suffix(path.suffix + ".tmp")
    # Write + fsync to guarantee bytes hit disk before rename
    with open(tmp, "wb") as f:
        f.write(payload)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass  # OneDrive virtual fs may not support fsync
    # On Windows, os.replace works across same filesystem; OneDrive should be OK
    os.replace(str(tmp), str(path))

    # Keep only 3 most-recent backups to avoid clutter
    bak_pattern = f"{path.name}.bak_*"
    baks = sorted(path.parent.glob(bak_pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    for old_bak in baks[3:]:
        try:
            old_bak.unlink()
        except OSError:
            pass

def fmt_msk(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MSK).strftime("%Y-%m-%d %H:%M")

def short_text(msg) -> str:
    """Display-friendly text including markers for attachments."""
    parts = []
    body = (msg.text or "").strip()
    if body:
        # one-line collapse, truncate long text
        body = body.replace("\n", " / ")
        if len(body) > 500:
            body = body[:497] + "…"
        parts.append(body)
    if msg.photo:
        parts.append("[photo]")
    if msg.document:
        fname = None
        for attr in (getattr(msg.document, "attributes", None) or []):
            if hasattr(attr, "file_name") and attr.file_name:
                fname = attr.file_name
                break
        parts.append(f"[file: {fname}]" if fname else f"[{msg.document.mime_type or 'document'}]")
    if msg.voice:
        dur = ""
        try:
            dur = f" {int(msg.voice.attributes[0].duration)}s"
        except Exception:
            pass
        parts.append(f"[voice{dur}]")
    if msg.video:
        parts.append("[video]")
    if msg.audio:
        parts.append("[audio]")
    if msg.sticker:
        alt = ""
        try:
            for attr in msg.sticker.attributes:
                if hasattr(attr, "alt") and attr.alt:
                    alt = f" {attr.alt}"
                    break
        except Exception:
            pass
        parts.append(f"[sticker{alt}]")
    if msg.contact:
        parts.append(f"[contact: {msg.contact.first_name or ''}]".strip())
    if msg.geo:
        parts.append("[geolocation]")
    if not parts:
        parts.append("[empty]")
    return " ".join(parts)

def needs_reply(text: str, from_me: bool) -> bool:
    """Rough heuristic: a question from the client."""
    if from_me:
        return False
    t = text.lower()
    return ("?" in t) or any(m in t for m in ["когда", "сколько", "что делать", "помогите"])  # RU trigger words: "when", "how much", "what to do", "help" (matched against live client messages)

# ============== Sync one client ==============

async def resolve_entity(client, resolver: dict, state_entry: dict):
    """Resolve a TG chat by, in order: cached peer_id -> @username -> phone.

    Returns (entity, how) or raises the last error. The phone arm is what lets a
    client with only a display name + phone (no public @username) still be synced.
    """
    last_err = None
    peer_id = state_entry.get("peer_id") or resolver.get("peer_id")
    if peer_id not in (None, ""):
        try:
            return await client.get_entity(int(peer_id)), f"peer_id={peer_id}"
        except Exception as e:
            last_err = e
    if resolver.get("username"):
        uname = resolver["username"].lstrip("@")
        try:
            return await client.get_entity(uname), f"@{uname}"
        except Exception as e:
            last_err = e
    if resolver.get("phone"):
        try:
            return await client.get_entity(resolver["phone"]), f"phone {resolver['phone']}"
        except Exception as e:
            last_err = e
    raise last_err or RuntimeError("no resolver (no peer_id, @username, or phone)")


async def sync_client(client, slug: str, resolver: dict, state_entry: dict,
                      full: bool, lookback_months: int) -> dict:
    if resolver is None:
        return {"slug": slug, "label": "", "skipped": "no telegram channel in behavior.json", "messages": []}

    label = resolver.get("label") or "?"
    print(f"  [{slug}] {label} — ", end="", flush=True)
    try:
        entity, how = await resolve_entity(client, resolver, state_entry)
    except Exception as e:
        print(f"UNRESOLVED: {e}")
        return {"slug": slug, "label": label, "error": f"unresolved ({e})", "messages": []}

    last_id = state_entry.get("last_message_id")
    try:
        last_id = int(last_id) if last_id is not None else None
    except (ValueError, TypeError):
        last_id = None

    mode = "full" if (full or last_id is None) else "incremental"
    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * lookback_months)

    kwargs = {"reverse": False}  # iter newest → oldest
    if mode == "incremental":
        kwargs["min_id"] = last_id

    messages = []
    count_in = count_out = 0
    async for msg in client.iter_messages(entity, **kwargs):
        if mode == "full" and msg.date < cutoff:
            break
        messages.append({
            "id": msg.id,
            "date_utc": msg.date.isoformat(),
            "date_msk": fmt_msk(msg.date),
            "from_me": bool(msg.out),
            "text": short_text(msg),
            "has_media": bool(msg.media),
        })
        if msg.out:
            count_out += 1
        else:
            count_in += 1

    messages.reverse()  # chronological for output

    new_state = dict(state_entry)
    # Cache the resolved peer_id so the next run deep-links by id (cheaper, and
    # survives a username change). Watermark cache only — never the membership list.
    try:
        new_state["peer_id"] = int(entity.id)
    except Exception:
        pass
    if messages:
        last = messages[-1]
        new_state["last_message_id"] = str(last["id"])
        new_state["last_read_at"] = datetime.now().isoformat()
        new_state["last_message_text"] = last["text"][:200]
        new_state["last_message_from"] = "me" if last["from_me"] else "client"
        new_state["unread_count"] = 0
    else:
        new_state["last_read_at"] = datetime.now().isoformat()

    print(f"{mode} via {how}, {len(messages)} msgs ({count_in} from client, {count_out} from me)")
    return {
        "slug": slug, "label": label, "mode": mode, "via": how,
        "messages": messages, "new_state": new_state,
        "count_in": count_in, "count_out": count_out,
    }

# ============== Markdown rendering ==============

def render_markdown(results, names, append_mode, lookback_months) -> str:
    now_msk = datetime.now(MSK)
    total = sum(len(r.get("messages", [])) for r in results)
    pending = sum(
        1 for r in results for m in r.get("messages", [])
        if needs_reply(m["text"], m["from_me"])
    )

    lines = []
    if not append_mode:
        lines.append(f"# TG messages for {now_msk.strftime('%Y-%m-%d')}\n\n")
        lines.append(
            f"**Summary:** {total} messages · {pending} need a reply · "
            f"generated {now_msk.strftime('%H:%M')} MSK · "
            f"first-time scan depth: {lookback_months} mo.\n\n---\n\n"
        )
    else:
        lines.append(f"\n---\n\n## Extra sync {now_msk.strftime('%H:%M')} MSK — {total} new\n\n")

    for r in results:
        slug = r["slug"]
        name = names.get(slug, slug)
        username = r.get("label") or "?"

        if r.get("skipped"):
            lines.append(f"## {name} ({username}) — skipped\n- {r['skipped']}\n\n")
            continue
        if r.get("error"):
            lines.append(f"## {name} ({username}) — ERROR\n- {r['error']}\n\n")
            continue

        msgs = r["messages"]
        if not msgs:
            lines.append(f"## {name} ({username}) — no changes\n\n")
            continue

        lines.append(
            f"## {name} ({username}) — {len(msgs)} msgs "
            f"({r['count_in']} from client, {r['count_out']} from me) · mode: {r['mode']}\n\n"
        )
        for m in msgs:
            arrow = "← to me" if not m["from_me"] else "→ to client"
            marker = " ❓" if needs_reply(m["text"], m["from_me"]) else ""
            lines.append(f"- **{m['date_msk']}** [{arrow}]:{marker} {m['text']}\n")
        lines.append(f"\n_Read up to msg_id: {r['new_state']['last_message_id']}_\n\n")

    return "".join(lines)

# ============== Main ==============

async def main_async(args) -> int:
    if not SECRETS_FILE.exists():
        print(f"ERROR: {SECRETS_FILE} not found", file=sys.stderr)
        return 1
    secrets = load_json(SECRETS_FILE)
    for k in ("api_id", "api_hash", "phone"):
        if not secrets.get(k):
            print(f"ERROR: '{k}' is empty in tg_api.json", file=sys.stderr)
            return 1

    # Watermark cache (keyed by client id). May be {} / partial on first run.
    state = load_json(STATE_FILE) if STATE_FILE.exists() else {}

    # Membership is DERIVED from behavior.channels, not from tg_state keys.
    roster = load_roster()
    names = {e["id"]: (e.get("name_short") or e.get("name_full") or e["id"]) for e in roster}
    resolvers = {}
    for e in roster:
        rv = tg_resolver(load_behavior(e["id"]))
        if rv is not None:
            resolvers[e["id"]] = rv
    tg_clients = sorted(resolvers.keys())

    if not roster:
        # Legacy / no-roster fallback: behave as before, off the watermark file.
        print("WARN: clients_index.json not found — falling back to tg_state.json keys",
              file=sys.stderr)
        legacy = [k for k in state.keys() if not k.startswith("_")]
        names = {k: k for k in legacy}
        for k in legacy:
            resolvers.setdefault(k, {"label": state[k].get("tg_username") or k,
                                     "username": state[k].get("tg_username"),
                                     "phone": None, "peer_id": state[k].get("peer_id")})
        tg_clients = sorted(legacy)

    if args.all:
        targets = tg_clients
    elif args.client:
        targets = [c.strip() for c in args.client.split(",") if c.strip()]
        bad = [c for c in targets if c not in names and c not in resolvers]
        if bad:
            print(f"ERROR: unknown clients: {bad}", file=sys.stderr)
            print(f"Available (clients with a telegram channel): {tg_clients}", file=sys.stderr)
            return 1
    else:
        print("ERROR: specify --all or --client SLUG", file=sys.stderr)
        return 1

    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    print(f"tg_sync: {len(targets)} client(s), lookback={args.lookback_months}mo, full={args.full}")
    print(f"Session: {SESSION_PATH}.session")

    client = TelegramClient(str(SESSION_PATH), secrets["api_id"], secrets["api_hash"])
    await client.start(phone=secrets["phone"])
    me = await client.get_me()
    print(f"✓ authorization ok as @{me.username or me.first_name} (id={me.id})\n")

    results = []
    for slug in targets:
        r = await sync_client(client, slug, resolvers.get(slug),
                              state.get(slug, {}), args.full, args.lookback_months)
        results.append(r)
        if "new_state" in r:
            state[slug] = r["new_state"]

    await client.disconnect()

    today = datetime.now(MSK).strftime("%Y-%m-%d")
    out_file = INBOX_DIR / f"tg_{today}.md"
    append_mode = out_file.exists()
    content = render_markdown(results, names, append_mode, args.lookback_months)

    # Atomic write: read-modify-write via tmp+rename.
    # This creates a new inode → the virtiofs cache on the Cowork side
    # sees the fresh content immediately (no delay).
    existing = out_file.read_text(encoding="utf-8") if out_file.exists() else ""
    combined = existing + content if append_mode else content
    tmp = out_file.with_suffix(out_file.suffix + ".tmp")
    tmp.write_text(combined, encoding="utf-8")
    import os as _os
    _os.replace(str(tmp), str(out_file))
    print(f"\n✓ written to {out_file.name} (append={append_mode}, total={len(combined)} chars)")

    save_json_atomic(STATE_FILE, state)
    print("✓ tg_state.json updated (backup alongside)")
    return 0

def main():
    p = argparse.ArgumentParser(
        description="Telethon-based sync of TG chats with direct clients.",
        epilog="Examples:\n"
               "  python tg_sync.py --all\n"
               "  python tg_sync.py --client <client_id>\n"
               "  python tg_sync.py --full --client <client_id>,<client_id> --lookback-months 6",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--all", action="store_true", help="Every client with a telegram channel (from behavior.json)")
    p.add_argument("--client", help="Comma-separated list of slugs (<client_id>,<client_id>,...)")
    p.add_argument("--full", action="store_true", help="Force a full rescan")
    p.add_argument("--lookback-months", type=int, default=4, help="First-time depth (default 4 mo)")
    args = p.parse_args()
    sys.exit(asyncio.run(main_async(args)))

if __name__ == "__main__":
    main()
