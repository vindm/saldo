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
- `journal/tg_state.json` — last_message_id for each direct client
- `journal/inbox/tg_<date>.md` — message snapshots
- `journal/daemon_logs/tg_sync_<date>.log` — daemon logs

### Sync logic

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

### Chat search (reliable)
The React search input ROLLS BACK a synthetic value-set. The working approach is a real beforeinput via execCommand:
```js
const inp=document.querySelector('input[placeholder="Search"]');
inp.focus();
document.execCommand('selectAll',false,null);
document.execCommand('insertText',false,'[client]');   // query
```
Read the results from `document.querySelector('#LeftColumn').innerText` — candidates under "Chats and Contacts"/"Global Search". Open a chat: click the needed `.ListItem` with a series of mouse events (pointerdown→mousedown→pointerup→mouseup→click) via `elementFromPoint` at the center. The hash will become `#<peer_id>`.

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
4. **lint**: `python3 engine/generate.py` (runs `state_lint`); publish dashboards only on exit 0.

### If there are no significant messages

Apply nothing. The `tg_<date>.md` file and the heartbeat are still written by the python script.

🔴 But still perform the unconditional dashboard render (see the "Unconditional dashboard render" section below) — even when there are no significant messages.

---

## D. Related skills and files

- `policies/checklists/tg_communication.md` — the standard for working with a client in TG
- `engine/_aggregator.py` (source `tg`) — parses `journal/inbox/tg_*.md`
- `journal/tg_state.json` — the single source of truth for "read up to"


---

## 🔴 Unconditional dashboard render — ALWAYS, as the last action

> The dashboard render is NOT gated on whether there were changes. Whatever happened above — whether state was edited or not, whether at least one client was affected or zero — **as the last action the daemon MUST**:
>
> `python3 engine/generate.py` (runs `state_lint`); on exit 0, publish `cp _tmp_html/*.html ..` (from the `_data` directory).
>
> Reason: the dashboard carries time-dependent content (today's date in the header, overdue items, "in N days") that must be refreshed **daily**, regardless of whether there were changes in state. Skipping the render on a "quiet day" = a frozen date (incident 2026-06-11→13, the operator's decision: the render is unconditional).
