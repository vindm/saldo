# Telegram UI playbook (web.telegram.org/a/) — the HOW (learnable)

Engine **canonical, read-only at runtime**; learned Field notes → the data-dir overlay
`<data.dir>/journal/playbook_notes/tg.md`. Protocol & safety: `connectors/_chat_actions.md`.
Structure: `connectors/_ui_playbook.md`. Loop: `policies/skill-evolution.md`. Steps are the
current best description and **self-correct** via the loop.

## Primitives

**`session`** — Open `web.telegram.org/a/` for **reading/sync** (the chat list + history live here).
⚠️ `/a/` and `/k/` are SEPARATE storages; `/a/` is the working session. **`/k/` is usable for
OPENING a single chat by deep-link** (`/k/#@username`, see `jump_to_chat`) — it has its own
IndexedDB and needs ~3-4 s warm-up on a cold load (a blank page at first = warming up, **not**
"not logged in"). Verify before acting.

**`jump_to_chat`** — `peer_id` (numeric) is the stable **identity + cache + watermark-compare**
key — cache it to `behavior.channels.telegram.peer_id` (and `tg_state.json`).
🟢 **Canonical open = navigate to `https://web.telegram.org/k/#@<username>` + wait ~3-4 s**
(field-verified 2026-06-28; build it with `tg_dm_url(username)`). `/k/` is a SEPARATE IndexedDB
session — on a cold load the page is blank for a few seconds (warm-up, **not** "not logged in"),
so wait before concluding. This is the link to store in `quick_access`.
🔴 **`/a/#<peer_id>` and `/a/#@username` do NOT open the chat** — the `/a/` SPA strips the hash and
returns to `/a/`. So in `/a/` `peer_id` is for identity/caching/`data-mid` comparison, never a
one-shot navigate. To open a chat *inside `/a/`* (the fallback, e.g. no @username) you must
**search → click the result with the full pointer/mouse sequence** (a plain `.click()` is dropped).

🔴 **The tab must be active/foreground** for any typed/search input — a backgrounded `/a/` tab
throttles the SPA's render and silently drops input. Foreground it first (`tabs_context` / select
the tab).

1. **Search** — the React field **rolls back BOTH `execCommand insertText` AND a plain `.value=`**.
   Use the **native value-setter + an `input` event**:
   ```js
   const inp = document.querySelector('#telegram-search-input, input[placeholder="Search"]');
   inp.focus();
   const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
   set.call(inp, 'SOZIDAI');                          // the query
   inp.dispatchEvent(new Event('input', { bubbles: true }));
   ```
   Read candidates from `#LeftColumn`.innerText ("Chats and Contacts" / "Global Search").
   🔴 **The search "sticks" — clear between queries + VERIFY.** The first query of a series can
   return the PREVIOUS query's result (field-verified 2026-06-28 on a peer_id backfill: a search
   for one client returned ANOTHER client's id → a wrong peer_id was nearly cached). Between
   queries: `set.call(inp,''); inp.dispatchEvent(new Event('input',{bubbles:true}))` + wait ~1s,
   then the new query + wait ~3.5s. **Always verify the result by name/@username before using its
   peer_id — never take the first row blind.**
2. **Take the VISIBLE result** — a `.ListItem` with a non-zero `getBoundingClientRect()`
   (height > 0). A phantom 0×0 node has no parent and cannot be clicked (list virtualisation).
3. **peer_id** is on the result's `.Avatar` (`data-peer-id` / `id="peer-story<ID>"`) — read and
   cache it the first time.
4. **Open** — dispatch the full pointer/mouse sequence at the button centre (a plain `.click()`
   fires the React handler "вхолостую"):
   ```js
   const btn = item.querySelector('.ListItem-button') || item;
   const r = btn.getBoundingClientRect();
   const o = { bubbles:true, cancelable:true, view:window,
               clientX:r.x + r.width/2, clientY:r.y + r.height/2, button:0 };
   for (const [type, Ctor] of [['pointerdown',PointerEvent],['mousedown',MouseEvent],
                               ['pointerup',PointerEvent],['mouseup',MouseEvent],['click',MouseEvent]])
     btn.dispatchEvent(new Ctor(type, o));
   ```
   Confirm `#MiddleColumn` is filled and the **header matches** before reading/sending.

**`scroll` / `load_history`** — Virtualised list; scroll up to load older messages until the
watermark. The chat list is **virtualised** — a client whose row hasn't rendered is invisible, so
iterate the **mapped client set** (`behavior.channels`), never "whatever the DOM currently shows".

**`read_messages`** — Main pane, oldest→newest, virtualised. `/a/` can preview without forcing read
(unlike WhatsApp) — confirm via the loop.
🔴 **Full-res media loads only when its message is scrolled into view** — until then `naturalWidth`
= 0 (only a ~160px avatar). To read a photo/screenshot: `msgEl.scrollIntoView({block:'center'})` →
wait → then extract. Indices `.message-list-item` **change on re-virtualisation** — don't cache an
index, **re-find the message by text**. With several full-media in one chat, take the img **inside
the target message**, not "the first big img on the page".

**`read_screenshot`** — read a value off an image in a message (e.g. a ЕНС-balance screenshot).
**This works — it is no longer a limitation** (supersedes any "ask the operator for the number off
the screenshot" rule):
1. scroll the message into view (above) so the img is full-res (`naturalWidth > 200`);
2. `canvas.drawImage(img)` → `canvas.toDataURL('image/png')` — **CORS does NOT taint**, export passes;
3. anchor-download (`a.download = …; a.click()`) → the file lands in the operator's **Downloads**;
4. `cp` to outputs / the client folder → **`Read` it as a multimodal image** — read the value by eye.
⚠️ Do **NOT** return base64 in the JS output (MCP blocks it / blows up context) — download a file
only. Blob-URLs from different messages can collide in a selector's output — **filter by size and
by parent message**.

**`attach`** — Clip icon → choose file. **`send`** — 🔴 gated (`_chat_actions` `send_message`):
compose box at the bottom; type; send button or Enter; show the draft, send only on approval.

**`download_file`** — Click the media/file message → download icon (`.File.interactive`,
`i.icon-download`) → the file lands in the operator's **Downloads** (mounted). **`detect_success`**
— the sent message appears with a status; confirm its presence, not just the click.

**`quirks`** —
- `/a/` vs `/k/`: the session is only in `/a/`; `/k/` is a separate, not-logged-in storage.
- **Open a chat by `/k/#@username`** (+ ~3-4 s warm-up); `/a/#<peer_id>` / `/a/#@username` do NOT
  open (the `/a/` SPA strips the hash). `peer_id` stays the identity/cache/`data-mid` key; inside
  `/a/` open via search + the pointer sequence.
- The React **search input drops `execCommand insertText` and `.value=`** — use the native
  value-setter + `input` event; and the **tab must be foreground** or input is throttled away.
- The message list is **virtualised**: full-res media needs `scrollIntoView`; `.ListItem` /
  `.message-list-item` can be phantoms (0×0) or re-indexed — take visible nodes, re-find by text.

## Field notes

Not here — in the overlay `<data.dir>/journal/playbook_notes/tg.md` (per
`policies/skill-evolution.md`), keyed by primitive. Corroborated, broadly-true lessons are curated
upstream into this canonical file by the developer.
