"""Build the client communication graph: `behavior.channels.endpoints[]` — one registry of every
contact point, instead of the same fact scattered across `behavior.channels.primary` / `.secondary`
(free-text) and `accounts.quick_access` (channels as `service:tg`, assistants as `service:assistant`).

Why (the structural gap §9): a client is not one TG chat. Andreev has THREE telegram points — his
personal DM (`behavior.primary`, with peer_id), a "payment reports" channel and an assistant (both
only in `quick_access`, so never synced) — and the assistant is DOUBLED (a free-text `secondary`
entry + a `quick_access` assistant entry that drift apart). The daemon reads only `primary`, so
reports/documents/assistant messages miss state, against the "full picture" mission.

This migration introduces the single registry and back-fills it from the three current stores; it is
**additive** — `primary`/`secondary` are LEFT in place (render still reads them; Phase 2 moves render
onto the graph and drops them). Each endpoint:

    {id, kind, role, transport, username, peer_id, sync, direction, note}
      kind      : "dm" | "channel" | "person"
      role      : "client" | "assistant" | "accountant" | "representative" | "work_channel"
      transport : "telegram" | "email" | "phone" | "edo"
      username  : bare handle (canon, no '@')   | null
      peer_id   : int (channels carry a negative id, from the /k/#-<id> link) | null
      sync      : true  -> the TG daemon fans out and reads this endpoint
      direction : "in" | "out" | "both"
      id        : stable key, "telegram:@<handle>" / "telegram:<peer_id>" / "telegram:name:<slug>"

STRUCTURE → deterministic `up()`: open the `endpoints` slot and emit ONE endpoint per existing
primary / secondary / quick_access contact point, parsing the transport, handle and (for channels)
the peer_id out of the `/k/#…` link. Name-free — it restructures whatever fields are present, no
client identities embedded; idempotent (a channels block that already has `endpoints` is skipped).

MEANING → `RUNTIME_PASS`: (a) **dedup** endpoints that are the SAME human across stores — e.g. a
username-less `secondary` telegram person and a `quick_access` assistant with a handle — into one
endpoint (keep the handle/peer_id, union the notes); (b) assign/normalize `role` by meaning, reading
the operator's OWN data (an assistant who files taxes is an `accountant`, a docs courier is an
`assistant`, the client themself is `client`, a shared feed is a `work_channel`). Conservative: when
unsure, keep both endpoints and use the broader role — never merge two contacts on a guess.

Sync (Phase 1): `connectors/tg/tg_sync.py` fans out over `transport==telegram && sync` endpoints
(personal DM keeps the client-id watermark key; others keyed by endpoint id). Lint: every synced
telegram endpoint must carry a resolver (`peer_id` or `username`). Schema-level, zero real data.
"""
import re

ID = "0028"
DESCRIPTION = ("behavior.channels.endpoints[]: build the client communication graph from "
               "primary/secondary/quick_access (additive; primary/secondary kept for render). "
               "Deterministic structural build; runtime dedup + role by meaning.")

_TG_HOST = "web.telegram.org"
# Transports a chat-collector reads directly (the by_chat messengers). Other transports
# — email/phone/edo/finkoper/team_via_* — are handled by their own connector (or are routing
# markers), so their endpoints are recorded but not flagged for messenger fan-out.
_SYNC_TRANSPORTS = {"telegram", "whatsapp", "max"}


def _slug(s):
    return re.sub(r"[^0-9a-zа-яё]+", "_", str(s or "").strip().lower()).strip("_") or "x"


def _parse_tg_link(url):
    """(username, peer_id) from a Telegram link. Channel deep-links carry a negative numeric id."""
    u = str(url or "")
    if _TG_HOST not in u and "t.me/" not in u:
        return None, None
    frag = u.split("#", 1)[1] if "#" in u else u.rsplit("/", 1)[-1]
    frag = frag.strip()
    if frag.startswith("@"):
        return frag[1:].strip() or None, None
    if re.fullmatch(r"-?\d+", frag):
        return None, int(frag)
    if frag:
        return frag.lstrip("@") or None, None
    return None, None


def _endpoint_id(transport, username, peer_id, display):
    if username:
        return f"{transport}:@{username.lstrip('@')}"
    if peer_id is not None:
        return f"{transport}:{peer_id}"
    return f"{transport}:name:{_slug(display)}"


def _mk(kind, role, transport, username, peer_id, sync, direction, note, display=None, origin=None):
    username = (str(username).lstrip("@").strip() or None) if username else None
    return {
        "id": _endpoint_id(transport, username, peer_id, display),
        "kind": kind, "role": role, "transport": transport,
        "username": username, "peer_id": peer_id,
        "sync": bool(sync), "direction": direction,
        "note": note or None, "origin": origin,
    }


def _build_endpoints(beh, acc):
    """Deterministic structural build — one endpoint per existing contact point."""
    out, seen = [], set()

    def add(ep):
        if ep["id"] in seen:
            # merge into the existing same-id endpoint (fill nulls, union note)
            for e in out:
                if e["id"] == ep["id"]:
                    e["peer_id"] = e["peer_id"] if e["peer_id"] is not None else ep["peer_id"]
                    e["username"] = e["username"] or ep["username"]
                    if ep["note"] and ep["note"] not in (e["note"] or ""):
                        e["note"] = " | ".join(x for x in (e["note"], ep["note"]) if x)
                    e["sync"] = e["sync"] or ep["sync"]
                    return
        out.append(ep)
        seen.add(ep["id"])

    ch = (beh or {}).get("channels") or {}

    def from_channel(c, is_primary):
        t = c.get("type")
        if not t:
            return
        role = "assistant" if c.get("role") in ("assistant_of_client", "assistant") else "client"
        kind = "person" if role == "assistant" else "dm"
        add(_mk(kind, role, t, c.get("username"), c.get("peer_id"),
                sync=(t in _SYNC_TRANSPORTS), direction="both",
                note=c.get("note"), display=c.get("id"),
                origin="primary" if is_primary else "secondary"))

    prim = ch.get("primary")
    if isinstance(prim, dict):
        from_channel(prim, True)
    for c in (ch.get("secondary") or []):
        if isinstance(c, dict):
            from_channel(c, False)

    # quick_access telegram contact points (channels + assistants)
    for qa in (acc or {}).get("quick_access", []) or []:
        if not isinstance(qa, dict):
            continue
        svc = qa.get("service")
        if svc not in ("tg", "assistant"):
            continue
        uname, pid = _parse_tg_link(qa.get("url"))
        if uname is None and pid is None:
            continue
        if svc == "assistant":
            add(_mk("person", "assistant", "telegram", uname, pid,
                    sync=True, direction="both", note=qa.get("note"),
                    display=qa.get("label"), origin="quick_access"))
        else:  # service == "tg": a feed/channel (negative id) or a tg link
            kind = "channel" if (pid is not None and pid < 0) else "channel"
            add(_mk(kind, "work_channel", "telegram", uname, pid,
                    sync=True, direction="in", note=qa.get("note"),
                    display=qa.get("label"), origin="quick_access"))
    return out


def up(api):
    def fix(cid, beh):
        if not isinstance(beh, dict):
            return False, ""
        ch = beh.get("channels")
        if not isinstance(ch, dict) or "endpoints" in ch:
            return False, ""  # idempotent — graph already built
        acc = api.read(cid, "accounts.json")
        eps = _build_endpoints(beh, acc if isinstance(acc, dict) else {})
        if not eps:
            return False, ""
        ch["endpoints"] = eps
        n_tg = sum(1 for e in eps if e["transport"] == "telegram")
        return True, ("channels.endpoints[]: built %d endpoint(s) (%d telegram) from "
                      "primary/secondary/quick_access" % (len(eps), n_tg))

    api.for_each_client("behavior.json", fix)


def preflight(api):
    """Surface clients whose telegram endpoints look like the SAME contact across stores
    (a username-less person endpoint + a handle-bearing one) — candidates for runtime dedup."""
    flags = []
    for cid in api.clients():
        beh = api.read(cid, "behavior.json")
        ch = (beh or {}).get("channels") or {}
        eps = ch.get("endpoints") or []
        tg = [e for e in eps if e.get("transport") == "telegram"]
        nameless = [e for e in tg if e.get("kind") == "person" and not e.get("username")]
        handled = [e for e in tg if e.get("kind") == "person" and e.get("username")]
        if nameless and handled:
            flags.append({"shape": "assistant_dup_candidate", "occurrences": len(nameless),
                          "clients": [cid], "kind": "needs_dedup_and_role",
                          "sample": (nameless[0].get("note") or nameless[0].get("id"))[:60]})
    return flags


RUNTIME_PASS = {
    "intent": (
        "Reconcile each client's telegram `endpoints[]`. (1) DEDUP: when two endpoints are the SAME "
        "human across stores — typically a username-less `kind:person` endpoint built from a free-text "
        "`secondary` entry, and a `kind:person` endpoint WITH a handle built from a `quick_access` "
        "assistant — and the operator's OWN data confirms they are one person, MERGE them into the "
        "handled one (keep username+peer_id, union the notes, drop the duplicate). (2) ROLE by meaning, "
        "read from the operator's data: a contact who files/prepares the client's taxes -> 'accountant'; "
        "a documents/info courier -> 'assistant'; the client themself -> 'client'; a shared feed/channel "
        "-> 'work_channel'; a legal/представитель -> 'representative'. Conservative: never merge two "
        "contacts on a guess — if unsure they are the same person, keep both."),
    "scope": "behavior.channels.endpoints[]  (dedup + role)",
    "escalate": "on_anomaly",
    "guardrails": [
        "never merge two endpoints unless the operator's data confirms they are the same person",
        "the merged endpoint keeps the non-null username and peer_id; never drop a peer_id/handle",
        "role must be one of {client, assistant, accountant, representative, work_channel}",
        "never touch primary/secondary (kept for render) or any identifier/amount",
    ],
}

EXPECT = {"preflight_max": 20, "change_kinds": ["needs_dedup_and_role"]}

SCENARIO = [
    "Open a client with multiple TG points (e.g. the one whose assistant was doubled across "
    "secondary + quick_access). Confirm channels.endpoints[] lists each distinct contact ONCE, the "
    "assistant carries its @handle, channels carry their peer_id, every telegram endpoint has a role, "
    "and the synced ones (sync:true) each resolve (peer_id or username).",
]
