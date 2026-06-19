#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tg_sync.py — Telethon-based sync of Telegram chats with direct clients.

Usage:
    python tg_sync.py --all                       # all clients from tg_state.json
    python tg_sync.py --client client_a            # one client
    python tg_sync.py --client client_a,client_b        # several
    python tg_sync.py --full --client client_a     # force full rescan
    python tg_sync.py --lookback-months 6 --all   # custom history depth

Reads:
    secrets/tg_api.json            — api_id, api_hash, phone, session_name
    journal/tg_state.json          — last_message_id per client
Writes:
    journal/inbox/tg_<today>.md      (append if exists, create otherwise)
    journal/tg_state.json            (atomic, with timestamped backup)
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
SYSTEM_DIR = HERE.parent.parent                         # policies/
PLANNING_DIR = SYSTEM_DIR.parent                        # workdir root

SECRETS_FILE = SYSTEM_DIR / "secrets" / "tg_api.json"
SESSION_PATH = SYSTEM_DIR / "secrets" / "operator_session"  # Telethon will append .session
STATE_FILE = PLANNING_DIR / "journal" / "tg_state.json"
INBOX_DIR = PLANNING_DIR / "journal" / "inbox"
LOG_DIR = PLANNING_DIR / "journal" / "daemon_logs"

MSK = timezone(timedelta(hours=3))

# Maps client_id slugs to human-readable names. In the live deployment these are
# the real sole-proprietor names; the entries below are anonymized examples.
CLIENT_NAMES = {
    "client_a": "SP Client A",
    "client_b": "SP Client B",
    "client_c": "SP Client C",
    "client_d": "SP Client D",
    "client_e": "SP Client E",
}

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

async def sync_client(client, slug: str, state_entry: dict, full: bool, lookback_months: int) -> dict:
    username = (state_entry.get("tg_username") or "").lstrip("@")
    if not username:
        return {"slug": slug, "skipped": "tg_username is empty", "messages": []}

    print(f"  [{slug}] @{username} — ", end="", flush=True)
    try:
        entity = await client.get_entity(username)
    except Exception as e:
        print(f"FAIL: {e}")
        return {"slug": slug, "error": str(e), "messages": []}

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
    if messages:
        last = messages[-1]
        new_state["last_message_id"] = str(last["id"])
        new_state["last_read_at"] = datetime.now().isoformat()
        new_state["last_message_text"] = last["text"][:200]
        new_state["last_message_from"] = "me" if last["from_me"] else "client"
        new_state["unread_count"] = 0
    else:
        new_state["last_read_at"] = datetime.now().isoformat()

    print(f"{mode}, {len(messages)} msgs ({count_in} from client, {count_out} from me)")
    return {
        "slug": slug, "mode": mode,
        "messages": messages, "new_state": new_state,
        "count_in": count_in, "count_out": count_out,
    }

# ============== Markdown rendering ==============

def render_markdown(results, state, append_mode, lookback_months) -> str:
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
        name = CLIENT_NAMES.get(slug, slug)
        username = state.get(slug, {}).get("tg_username", "?")

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

    state = load_json(STATE_FILE)
    valid_slugs = [k for k in state.keys() if not k.startswith("_")]

    if args.all:
        targets = valid_slugs
    elif args.client:
        targets = [c.strip() for c in args.client.split(",") if c.strip()]
        bad = [c for c in targets if c not in valid_slugs]
        if bad:
            print(f"ERROR: unknown clients: {bad}", file=sys.stderr)
            print(f"Available: {valid_slugs}", file=sys.stderr)
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
        r = await sync_client(client, slug, state[slug], args.full, args.lookback_months)
        results.append(r)
        if "new_state" in r:
            state[slug] = r["new_state"]

    await client.disconnect()

    today = datetime.now(MSK).strftime("%Y-%m-%d")
    out_file = INBOX_DIR / f"tg_{today}.md"
    append_mode = out_file.exists()
    content = render_markdown(results, state, append_mode, args.lookback_months)

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
               "  python tg_sync.py --client client_a\n"
               "  python tg_sync.py --full --client client_a,client_b --lookback-months 6",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--all", action="store_true", help="All clients from tg_state.json")
    p.add_argument("--client", help="Comma-separated list of slugs (client_a,client_b,...)")
    p.add_argument("--full", action="store_true", help="Force a full rescan")
    p.add_argument("--lookback-months", type=int, default=4, help="First-time depth (default 4 mo)")
    args = p.parse_args()
    sys.exit(asyncio.run(main_async(args)))

if __name__ == "__main__":
    main()
