# Skill: tg/sync — sync TG chats with direct clients

**The main path is Telethon (the clientPI)**, via the `tg_sync.py` script. The Chrome-MCP scroll is kept as a fallback (bottom part of the document).

---

## A. Telethon (primary, active since 2026-05-24)

### Running (manually, if needed)

```powershell
cd "C:\Users\user\OneDrive\Desktop\WORKDIR\policies\connectors\tg"
python tg_sync.py --all                       # incremental for everyone
python tg_sync.py --client <client_id>            # one client
python tg_sync.py --full --client <client_id>,<client_id> # full rebuild
python tg_sync.py --full --all --lookback-months 4  # the first full scan
```

### Auto-run

Windows Task Scheduler, task `Cowork_TG_Sync_Daily`, daily at 06:45 local time.
Triggers `launchers/run_daily.bat`, which calls `python tg_sync.py --all`.

Check the task status:
```powershell
Get-ScheduledTask -TaskName Cowork_TG_Sync_Daily
```

Force a run now:
```powershell
Start-ScheduledTask -TaskName Cowork_TG_Sync_Daily
```

### Domain files

- `tg_sync.py` — the main script (Telethon)
- `launchers/SETUP_ONE_CLICK.bat` — `pip install` + task registration + the first full scan
- `launchers/install_scheduled_task.ps1` — task registration only (separately)
- `launchers/run_daily.bat` — what Task Scheduler runs (quietly, into the log)
- `launchers/run_full_scan.bat` — a manual full scan (with the window open)
- `secrets/tg_api.json` — api_id, api_hash, phone (SECRET)
- `secrets/operator_session.session` — Telethon session (SECRET)
- `journal/tg_state.json` — **watermark cache** keyed by client id (`last_message_id` + cached `peer_id`). NOT the rotation list — membership is derived from `behavior.channels` (every client with a `telegram` channel).
- `journal/inbox/tg_<date>.md` — message snapshots
- `journal/daemon_logs/tg_sync_<date>.log` — daemon logs

### Sync logic

**Membership (who is in `--all`):** every client whose `behavior.json` declares a `telegram` channel — derived at runtime from state, not a hand-kept list (a missing client can no longer be silently dropped — the brukh incident). Each chat is resolved by, in order: cached `peer_id` → `@username` → `phone`, so a display-name-only client with a phone is still synced. `tg_state.json` is a pure watermark cache.

On each run, for each client:
- If `last_message_id == null` OR `--full` was passed → full scan, date limit: `now - lookback_months`
- Otherwise → incremental (`min_id = last_message_id`)

The result is written to `tg_<today>.md` (append if the file exists, create otherwise).
State is updated atomically with a timestamped backup (the last 3 are kept).

### The "needs a reply" heuristic

In the output, `❓` is marked if the last message is from the client and contains:
- the `?` sign
- the words: `когда` ("when"), `сколько` ("how much"), `что делать` ("what to do"), `помогите` ("help") — matched against live Russian client messages

The task aggregator (`_aggregator.py`) picks up the marked messages into the pending category for the dashboard.

### Security rules

- **Reading** — no approval needed (like finkoper / mail)
- **Replying to a client** — only on an explicit "send" from the operator in the Cowork chat
- **Downloading attachments** — not implemented yet (TODO for P2: place into `CLIENTS/<client>/<month>/`)

### Known nuances

- On the first run, Telethon asks for a confirmation code (arrives in TG as a system message from Telegram)
- The session file is bound to the IP — moving to another computer will require a new authorization
- When changing api_hash on my.telegram.org, the old session may stay valid, but verify
- The Cowork sandbox has no access to Telegram servers → runs only on the operator's Windows machine

---

## B. Chrome-MCP live-read (ACTIVE fallback — verified live 2026-06-06)

When it's needed: the Telethon daemon didn't run (the operator's Windows machine is off / they are in Bali) → `tg_<today>.md` is stale (lag of days, not 30 min). Then I read the chat live via Chrome MCP.

⚠️ **VERSION: only `web.telegram.org/a/`** — the operator's session is logged in there. **`/k/` is NOT logged in** (separate storage), the deep-link `/k/#@username` returns an empty page — do NOT use it. The hash in `/a/` is numeric: `#<peer_id>`, not `#@username`.

⚠️ Telegram holds a WebSocket → the page NEVER reaches document_idle. `find` / `read_page` / `get_page_text` fail with "page still loading". Work ONLY via `javascript_tool` (+ `read_network_requests`).

### Detecting "new since last read" — watermark, NOT unread badges 🔴
You are scanning the loaded chat list. **Do not decide a client has nothing new because there is no
unread badge.** The badge clears the moment **any human** opens the chat in Telegram — Mom reading
it on her phone — but Saldo's read position is `journal/tg_state.json` (`last_message_id` / `last_ts`)
and is **independent of Telegram's read state**. Absence of a badge ≠ processed by Saldo.

**Iterate the MAPPED CLIENT SET, not the rendered DOM.** The list is virtualised, so a client
whose row hasn't rendered yet is invisible — scanning "what's on screen" silently drops clients
(the "догрузить список, чтобы захватить оставшихся" symptom). Walk every client in
`behavior.channels`, and for each: read the chat's **last-message timestamp** (its `.ListItem`
last-message + time, or the chat header after a jump) and **process iff it post-dates the client's
watermark**. If you can't read the timestamp reliably (virtualized list, throttled render, search
not landing) → **jump to the chat by `peer_id` and compare `data-mid` to `last_message_id`**. The
badge and chat-list sort order are at most **hints that may add a chat**; they may **never remove
one**. When in doubt, **open** — never skip. (Shared rule: `connectors/_chat_collector.md` step 3.)

### Navigation — deep-link first, foreground before search 🔴
**Prefer `jump_to_chat` by `peer_id`** (`/a/#<peer_id>`): it needs no typed input and survives
render throttling. Use search only to **discover** a peer_id the first time, then cache it and
deep-link thereafter. **Before any search, the `/a/` tab must be active/foreground** — a
backgrounded tab throttles the SPA's render and the React input drops the synthetic `insertText`
("поиск не срабатывает — вкладка в фоне"). If search still won't land, **fall back to the `peer_id`
deep-link, never to scanning the chat list for badges.** (Playbook: `connectors/tg/ui_playbook.md`
→ `jump_to_chat`.)

### Chat search (reliable)
The React search input ROLLS BACK a synthetic value-set. The working approach is a real beforeinput via execCommand:
```js
const inp=document.querySelector('input[placeholder="Search"]');
inp.focus();
document.execCommand('selectAll',false,null);
document.execCommand('insertText',false,'[client]');   // query
```
Read the results from `document.querySelector('#LeftColumn').innerText` — candidates under "Chats and Contacts"/"Global Search". Open a chat: click the needed `.ListItem` with a series of mouse events (pointerdown→mousedown→pointerup→mouseup→click) via `elementFromPoint` at the center. The hash will become `#<peer_id>`.

### Reading the body — the tab MUST be foreground/active 🔴
**The single most common live-read failure (the brukh EHC-balance incident): the controlled
tab is backgrounded `[Inactive]`, so the message body never loads.** Telegram Web's
`.MessageList` is virtualised **by visibility** — in a background/inactive tab React throttles
and the message rows are **not mounted**, so the DOM has no text to scrape. The left column and
search still render (they're cheap), which is why you can *find* the chat but not *read* it. The
absence of body text here is NOT "no messages" and NOT a hard limit — it means the tab isn't
foreground.

So, before reading the conversation body:
1. **Bring the `/a/` tab to the foreground and make it the active tab** (`tabs_create_mcp` /
   activate the tab; the same foreground rule the search step needs). A read attempt on a
   backgrounded tab is invalid — re-activate and retry, never report "технически нельзя".
2. Jump to the chat by `peer_id` (`/a/#<peer_id>`), then **drive the virtualiser**: set
   `el.scrollTop = el.scrollHeight` on `.MessageList` to force the recent rows to mount, read
   `el.innerText`. Scroll up in steps if you need older messages.
3. If the tab cannot be foregrounded at all in this environment, say so explicitly and ask the
   operator to open the chat in her own Telegram tab and leave it active — do **not** present it
   as an inherent inability to use Telegram.

🔵 **But prefer the Telethon path.** Since the rotation is now derived from `behavior.channels`
and a chat resolves by cached `peer_id` → `@username` → **phone**, a client with only a display
name + phone (brukh) is read by the reliable python daemon — her messages land in
`journal/inbox/tg_<date>.md` with no browser scraping. This Chrome live-read is the fallback for
when the operator's Windows daemon is off (e.g. Bali); it is no longer the only way to reach a
handle-less client.

### Reading messages
The feed scroll container is `.MessageList` (class `Transition MessageList custom-scroll`), virtualized. Bottom (recent): `el.scrollTop=el.scrollHeight`. Text — `el.innerText`; date dividers "April 1" etc.

### Download an attachment (statement/PDF) and read it
The file widget — `.File.interactive`, the download icon — `i.icon-download`. Clicking it → the file lands in the **operator's Downloads** (mounted). Then the sandbox:
- `ls`/`find` over Downloads gives an I/O error, but `stat`/`cp`/`cat` by the FULL path work; the file name = as in the chat.
- `cp "<full path>" /tmp/x.pdf && pdftotext -layout /tmp/x.pdf /tmp/x.txt` → grep over the text.
- Downloading a client's attachment for reading — no approval needed (this is reading data, not sending).

### Known peer_ids (for the direct `/a/#<peer_id>`)
- the client ([redacted]) → `[redacted]`  (add more as they get opened)

### Hygiene
After working, close the MCP tab (`tabs_close_mcp`).

---

## C. Applying to client state (mm_update inline) — added 2026-06-07

> Previously, a separate `mm-update-3x-daily` daemon handled the interpretation of tg signals.
> It was **disabled 2026-06-07** (the operator's decision): tg updates state **at the moment of reading**,
> as email/finkoper/news already do. After collecting `tg_<date>.md` — immediately apply
> the `mm_update` cognitive protocol (see `connectors/mm_update/SKILL.md`).

This is done by the LLM agent that performed the sync (the Chrome live-read from section B is a Claude session;
or me interactively, when I read the fresh `tg_<date>.md` after a Telethon run).
The pure-python `tg_sync.py` does NOT do interpretation — it only writes the snapshot file.

### For each client with a significant message

Read the FULL text (context matters more than keywords), load the client's state
(`tracks_by_client` + `state_ops.state_read` of all `state/*.json` + `mental_model_read`),
then apply via the API. All writers write into `state/tasks.json` / `state/*.json`
using the read-modify-write scheme (since 2026-06-07, `_tracks` was moved to state_ops):

- **A message requires action** (a request, a question, a promise to send) → `_tracks.upsert_track(cid, {'id':..., 'type':'tg_action_required', 'status':'active', 'source':'tg:<username>:<date>', ...})`
- **Movement on an existing track** (sent a statement/document, replied) → `_tracks.add_history_event(cid, tid, event, source='tg:<username>:<date>')`
- **Closing — operator only** (see `connectors/mm_update/SKILL.md` §D). The daemon NEVER closes a track. On a confirmation (the client says "paid"/"done", or objective proof lands) → `_tracks.add_history_event(cid, tid, '<what happened>', source='tg:<username>:<date>')` and refresh `next_action` to «Подтвердить закрытие — …». The track surfaces in the overview «🔄 Последние обновлённые треки» zone; the operator closes it from the card. "Will send / will do" = a promise → `add_history_event` only.
- **A new fact about the client** (new bank/detail/counterparty) → `state_ops.state_write` into the right `state/<file>.json`.
- **Risk / red flag** → a record in `state/risks.json`.

### Mandatory finale (as in mm_update SKILL.md)

1. **Cross-link reconciliation** across all of the client's files: close answered `open_question`, reassess `risks.json`, fill in ❓, update `mental_model.md` + append to `history.jsonl`.
2. **Do not overwrite the operator's decisions** — read-modify-write only: `_tracks`/`state_ops` read the whole file and write it in full, `tasks_overrides` and manual fields are preserved. No partial overwrites.
3. **Audit-log** as one block in `journal/operator_decisions.md`.
4. **lint + scoped render** (see `connectors/_rebuild.md`): `python3 engine/state_lint.py` as the gate (exit≠0 → do NOT publish, fix first), then render the affected client(s) — `python3 engine/generate.py --clients=<affected ids>` — and refresh the shared views with `python3 engine/generate.py --aggregates`. Never a bare full `generate.py` here — it overruns the 45s sandbox budget (the frozen-date incident).

### If there are no significant messages

Apply nothing. The `tg_<date>.md` file and the heartbeat are still written by the python script.

🔴 But still perform the unconditional dashboard render (see the "Unconditional dashboard render" section below) — even when there are no significant messages.

---

## D. Related skills and files

- `jurisdictions/ru/checklists/telegram-communication.md` — the RU pack's standard for working with a client in TG
- `engine/_aggregator.py` (source `tg`) — parses `journal/inbox/tg_*.md`
- `journal/tg_state.json` — the single source of truth for "read up to"


---

## 🔴 Closing render — ALWAYS, as the last action (shared service pages)

> The dashboard render is NOT gated on whether there were changes. Whatever happened above — whether state was edited or not, whether at least one client was affected or zero — **as the last action the daemon MUST**:
>
> `python3 engine/generate.py --aggregates` (runs `state_lint`; refreshes the shared service pages — today's date, overdue, "in N days" — and fits the per-command 45s budget; see `connectors/_rebuild.md`). Per-client cards roll their date at the **`dashboards` 07:45** full render. NEVER a bare full `generate.py` here — that froze the dashboard (incident 2026-06-11→13).
>
> Reason: the dashboard carries time-dependent content (today's date in the header, overdue items, "in N days") that must be refreshed **daily**, regardless of whether there were changes in state. Skipping the render on a "quiet day" = a frozen date (incident 2026-06-11→13, the operator's decision: the render is unconditional).
