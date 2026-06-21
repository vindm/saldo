# Skill domain: tg (Telegram)

Reading Telegram chats with direct clients via `web.telegram.org/k/`.
A source of tasks for the direct circuit (track="direct") in the dashboard.

## One skill

**`sync.md`** — universal sync. Automatically selects the mode:
- Full (the last 4 months) — if the client is being read for the first time
- Incremental (since last_seen) — if state already exists

It can work for one client, for a list, or for all direct. This same skill is called by the morning daemon.

## Files

- `README.md` — this file
- `sync.md` — the main skill
- `read_chat.md`, `morning_full_scan.md`, `incremental_update.md` — **deprecated**, kept as redirects to sync.md

## State

`journal/tg_state.json` — last_message_id, last_read_at, unread_count for each direct client.

## Output

`journal/inbox/tg_<date>.md` — a snapshot of the day's messages.

After collecting the snapshot, the LLM agent **immediately applies `mm_update` inline** to the significant messages (see `sync.md` §C). The separate `mm-update-3x-daily` daemon was disabled 2026-06-07.

## Daemon schedule

06:45 MSK daily — calls sync with all clients via the `scheduled-tasks` MCP (cron `45 6 * * *`).

## Security rules

- **Reading** — no approval needed (like finkoper / mail)
- **Downloading an attachment** — no approval needed, into `CLIENTS/<client>/<month>/`
- **Writing to a client** — only with an explicit "send" in the Cowork chat
- See also `policies/checklists/tg_communication.md`

## Known technical nuances

- ⚠️ Live-read via Chrome MCP — only `web.telegram.org/a/` (the session is logged in there); `/k/` is NOT logged in. The hash in `/a/` is numeric `#<peer_id>`. Chat search — `execCommand('insertText')` in `input[placeholder="Search"]`. Details — `sync.md` §B
- Active WebSockets in TG interfere with Chrome MCP `screenshot` / `read_page` (they wait for document_idle). Use `javascript_tool` for DOM operations — it works
- DOM classes: `.message`, `.bubble`, `.text-content`; `data-mid` = message_id
