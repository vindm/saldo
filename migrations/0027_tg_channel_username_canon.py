"""Canonicalize a `behavior.json` telegram channel's handle: `username` WITHOUT '@', `id` = '@'+username.

`0026` opened the resolver slots (`username`, `peer_id`) but left `username` carrying whatever the
`id` carried — so a handle channel ended up with `username` = "@handle" (the '@' duplicated) while a
display-name channel kept `id` = the name. Two shapes for the same fact. This fixes the model to one
canonical form so cards, the collector, and the link-builder never reinvent formats:

    channels.<*>.{type:"telegram"} with a handle  ->  username = "<handle>"   (no '@')
                                                       id       = "@<handle>"

The handle is taken from whichever slot holds it: a non-empty `username` (its '@' stripped) else an
`id` that starts with '@' (its '@' stripped). A telegram channel with **no** handle — only a display
name (e.g. "Valeriya Brukh | SOZIDAI agency", `username` null) — is LEFT untouched: `id` stays the
name, `username` stays null (its handle is filled later as operator data, not by this schema migration).

Pairs with:
  - `engine/_helpers.tg_dm_url(username)` — the one link-builder: a bare or '@'-handle -> the canonical
    open-a-chat deep-link `https://web.telegram.org/k/#@<handle>` (see `connectors/tg/ui_playbook.md`).
  - `connectors/tg/tg_sync.py` -> `tg_resolver` now prefers the structured `username` field.
  - `state_lint` -> `tg_channel_noncanon` (WARN): a handle channel whose `username` has '@' or whose
    `id` != '@'+username is flagged, so the model can't drift back.

Behaviour-preserving for the dashboards (no renderer reads `username`/the '@' form of `id`; the card
shows the channel `id`, and for handle channels the visible `id` is unchanged — already "@handle").
Idempotent: a channel already in canon form (bare `username`, `id` == '@'+username) is skipped, so a
partial re-run is safe and a fully-applied re-run is a no-op. Deterministic and shape-matched — the
only operations are "strip a leading '@'" and "prepend '@'", no client identities embedded — ZERO
real data. Sibling of `0026`; mirrors the normalize-in-place pattern of 0021-0024.
"""

ID = "0027"
DESCRIPTION = ("behavior.channels[telegram]: canon handle — username WITHOUT '@', id = '@'+username "
               "(handle channels only; display-name channels untouched). Behaviour-preserving, idempotent.")


def _telegram_channels(data):
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
            uname = str(tg.get("username") or "").strip()
            rawid = str(tg.get("id") or "").strip()
            # derive the handle: from username, else from an '@'-style id
            handle = uname.lstrip("@") if uname else (rawid.lstrip("@") if rawid.startswith("@") else "")
            if not handle:
                continue  # display-name-only channel — no handle to canonicalize
            want_uname, want_id = handle, "@" + handle
            if tg.get("username") == want_uname and tg.get("id") == want_id:
                continue  # already canon — idempotent
            tg["username"] = want_uname
            tg["id"] = want_id
            touched += 1
        if not touched:
            return False, ""
        return True, ("behavior.channels[telegram]: canon handle (username bare / id=@username) "
                      "on %d channel(s)" % touched)

    api.for_each_client("behavior.json", fix)
