"""Open the structured TG-resolver slots on every `behavior.json` telegram channel.

The TG daemon's rotation is DERIVED from `behavior.channels` — every client with a
`telegram` channel is in rotation (no hand-kept list to drift out of; the brukh
incident: a TG client silently absent from the daemon's separate list). To act on
that membership the daemon must RESOLVE the chat, in order: cached `peer_id` ->
`@username` -> `phone`. Two of those three want a structured home on the channel
itself, so TG reachability is single-sourced in `behavior.json` rather than re-parsed
from the free-text `id` on every run (and duplicated into the journal watermark file):

    channels.<*>.{type:"telegram"} gains, where absent:
        username : "@handle"  when the channel `id` IS a handle (starts with "@"),
                   else null   (a display-name-only channel — e.g. "Valeriya Brukh |
                   SOZIDAI agency" — has no public handle; the daemon then resolves by
                   the client's phone channel, or by a peer_id cached on first contact).
        peer_id  : null        # filled by the daemon on first successful resolve, so
                   the next run deep-links by id (cheaper, survives a username change).

Additive and behaviour-preserving: `username` is only ever the `id` it already equals
(when `id` starts with "@"), else null; `peer_id` is null. No renderer reads these keys
(the card shows `type`/`id`), so dashboards are byte-identical. The CONSUMERS are the
daemon (`connectors/tg/tg_sync.py` -> `tg_resolver`) and the `tg_unresolvable` lint
check (a telegram channel with no @username, no phone, and no cached peer_id is
surfaced, never silently dropped).

Deterministic and shape-matched: the only judgment is "does `id` start with '@'" — a
name-free shape, no client identities embedded. Idempotent: a channel that already
carries `username`+`peer_id` is left untouched; only missing keys are added, so a
partial re-run is safe and a fully-applied re-run is a no-op. Schema-level — keyed
purely on the `channels`/`type`/`id`/`username`/`peer_id` field names — ZERO real data.
Mirrors the additive-slot pattern of 0017 (`financials.periods[]`) / 0018
(`tax_calendar_*[]`) / 0011 / 0013.

NOTE on tg_state.json: the journal watermark cache (`journal/tg_state.json`) is NOT
touched by this migration. It is a regenerable per-run cache keyed by client id, not
source-of-truth client state, and lives outside the per-client migration framework; the
daemon rebuilds it, keeping existing `last_message_id` watermarks and dropping the now
single-sourced resolver. No schema migration is owed for a regenerable cache.
"""

ID = "0026"
DESCRIPTION = ("behavior.channels[telegram]: add structured resolver slots username "
               "(@handle when id is one, else null) + peer_id (null) where absent — "
               "single-source TG reachability. Additive, behaviour-preserving.")


def _telegram_channels(data):
    """Yield every telegram channel dict in behavior.channels (primary + secondary)."""
    ch = (data or {}).get("channels")
    if not isinstance(ch, dict):
        return
    prim = ch.get("primary")
    if isinstance(prim, dict) and prim.get("type") == "telegram":
        yield prim
    for c in (ch.get("secondary") or []):
        if isinstance(c, dict) and c.get("type") == "telegram":
            yield c


def up(api):
    def fix(client_id, data):
        if not isinstance(data, dict):
            return False, ""
        touched = 0
        for tg in _telegram_channels(data):
            if "username" in tg and "peer_id" in tg:
                continue  # already migrated — idempotent
            if "username" not in tg:
                raw = str(tg.get("id") or "").strip()
                tg["username"] = raw if raw.startswith("@") else None
                touched += 1
            if "peer_id" not in tg:
                tg["peer_id"] = None
                touched += 1
        if not touched:
            return False, ""
        return True, ("behavior.channels[telegram]: opened %d resolver slot(s) "
                      "(username/peer_id)" % touched)

    api.for_each_client("behavior.json", fix)
