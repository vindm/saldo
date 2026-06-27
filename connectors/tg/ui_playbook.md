# Telegram UI playbook (web.telegram.org/a/) — the HOW (learnable)

Engine **canonical, read-only at runtime**; learned Field notes → the data-dir overlay
`<data.dir>/journal/playbook_notes/tg.md`. Protocol & safety: `connectors/_chat_actions.md`.
Structure: `connectors/_ui_playbook.md`. Loop: `policies/skill-evolution.md`. Steps are the
current best description and **self-correct** via the loop.

## Primitives

**`session`** — Open `web.telegram.org/a/`. ⚠️ Use `/a/`, **not** `/k/` — `/k/` is a separate
storage that is **not** logged in; the operator's session lives in `/a/`. Logged in → the chat
list. Verify before acting.

**`jump_to_chat`** — **Prefer the deep-link `/a/#<peer_id>`** (the hash is the **numeric peer
id**, not `@username`): it needs no typed input, so it survives render throttling and is the robust
path. Use the **search box only to discover a peer_id the first time** — then cache it (overlay
`journal/playbook_notes/tg.md` / `tg_state.json`) and deep-link thereafter. Verify the header
matches before reading/sending.
🔴 **The tab must be active/foreground to drive input.** A backgrounded `/a/` tab throttles the
SPA's render, so the React search input silently drops synthetic `insertText` (the "поиск не
срабатывает" symptom). Before search: bring the tab to the foreground (`tabs_context` / select the
tab). If search still won't land, **fall back to the `peer_id` deep-link, never to eyeballing the
chat list.**

**`scroll` / `load_history`** — Virtualised list; scroll up to load older messages until the
watermark.

**`read_messages`** — Main pane, oldest→newest. `/a/` can preview without forcing read (unlike
WhatsApp) — confirm current behavior via the loop.

**`attach`** — Clip icon → choose file. **`send`** — 🔴 gated (`_chat_actions` `send_message`):
compose box at the bottom; type; send button or Enter; show the draft, send only on approval.

**`download_file`** — Click the media message → download. **`detect_success`** — the sent message
appears with a status; confirm its presence, not just the click.

**`quirks`** — `/a/` vs `/k/` (above); numeric `peer_id` in deep-links; **a backgrounded tab
throttles render → typed/search input is dropped** (foreground first, or deep-link by `peer_id`);
the chat list is **virtualised** — clients not yet rendered are invisible, so iterate the **mapped
client set**, never "whatever the DOM currently shows".

## Field notes

Not here — in the overlay `<data.dir>/journal/playbook_notes/tg.md` (per
`policies/skill-evolution.md`), keyed by primitive. Corroborated, broadly-true lessons are curated
upstream into this canonical file by the developer.
