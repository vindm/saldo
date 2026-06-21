# Composite skill: incremental_update

Incremental update of the Finkoper state since `last_run`. Appends to the daily report with a marker, updates `latest/` pointwise (without a full rotation), updates the mental_model.

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `since` | ISO datetime | `snapshot_meta.json:last_run` |
| `client_filter` | client_id | `null` (if set — only this client) |
| `trigger_description` | string | `null` (short description of the trigger for the marker in the report, e.g.: "a task about the client appeared") |

## When it is called

- Me in-session, triggered by "check Finkoper", "is there anything new", "a task appeared" (when there is no specific task_id).
- If there is a specific task_id or chat — better to call `read_task.md` / `read_chat.md` directly.

## Precondition

`journal/finkoper_state/latest/snapshot_meta.json` exists (there was at least one `morning_full_scan`).

## Algorithm (pipeline)

### Step 1. Preparation

- Read `latest/snapshot_meta.json` → `last_run` is the `since` (if the parameter is not set).
- Read `latest/tasks.json` and `chats.json` — the current state.

### Step 2. The notification bell — the main entry point

```
Read `connectors/finkoper/check_notifications.md`. Execute with:
  since = <since>
  include_old_tasks = false
Get `new_notifications`.
```

If `new_notifications.count == 0` AND `client_filter` is not set → there is nothing to update. Finish (see the "If there are no changes" step below).

### Step 3. Targeted reading of tasks from notifications

For each notification of type `task_new` / `task_updated` / `task_closed`:
```
Read `connectors/finkoper/read_task.md`. Execute with:
  task_id = <entity_id from the notification>
  read_attachments = false
  read_full_chat = true
```

If `client_filter` is set — filter out tasks not belonging to this client AFTER reading the card (or immediately by `client_id` if it is visible in the notification).

### Step 4. Targeted reading of chats from notifications

For each notification of type `chat_message` / `mention`:
```
Read `connectors/finkoper/read_chat.md`. Execute with:
  chat_id_or_name = <chat name from the notification>
  message_count = 10
  since = <since>
```

### Step 5. If `client_filter` is set without notifications — selective reconciliation

If `client_filter` is set, but there are no notifications for this client — do a selective `list_tasks(client_id=<filter>, status=open)` and compare against `latest/`. If there are discrepancies — `read_task` for them.

### Step 6. Diff (only for the affected entities)

Compare the new data against `latest/`:
- New tasks (`id` not in `latest/tasks.json`)
- Changed tasks (fields differ)
- New messages in chats
- Closed tasks (disappeared from `open`)

### Step 7. R6 — preserving manual notes

If the daily report has manual notes from the operator — save them to `journal/operator_decisions.md` before appending.

### Step 8. Appending to the daily report

If `journal/inbox/finkoper_<today>.md` exists:
- **Append at the end** the block:

```markdown

---

## 🔄 Appended in the incremental run HH:MM (trigger: <trigger_description>)

**Changes since last_run (previous: HH:MM):**

### 🆕 New tasks (N)
[blocks]

### 💬 New messages in tasks (N)
[blocks]

### 📎 New attachments (N)
[blocks]

### ✅ Disappeared from open (N)
[blocks]

### 📨 Team chats — new
[blocks]
```

If `<today>.md` does not exist — create it as a full daily report (this means the daemon did not run in the morning; the incremental replaces it).

### Step 9. Pointwise update of `latest/`

Do not do a full rotation (we don't create an archive). Pointwise:
- For a new task — add an entry to `latest/tasks.json`.
- For a changed one — update the fields.
- For a closed one — remove it from `latest/tasks.json` (it is no longer open).
- For a chat — update the entry in `latest/chats.json`.
- In `latest/snapshot_meta.json` update `last_run` to the current time + increase `tasks_count` / `chats_count` accordingly.

### Step 10. Updating the mental_model

For each affected client — update the corresponding `mental_model.md` (the updater's T1/T2/T7 rules).

The heartbeat is NOT overwritten — it is a marker of the morning run.

### If there are no changes

If steps 2-5 showed 0 changes:
- Do not append to the daily report.
- Do not update `latest/snapshot_meta.json:last_run` (or update it, but this is a question of idempotency — better to update it so the next incremental does not re-examine the same thing).
- Return into context: "Nothing new for the period HH:MM..HH:MM".

## Idempotency

- If called again with the same `since` — `check_notifications` will return the same thing or an empty array (if the first incremental already ran and updated `last_run`).
- If a `morning_full_scan` is running in parallel — better to wait, do not launch the incremental during it.

## Relationship with other skills

- After the incremental — mm_update processes the new signals (see `connectors/mm_update/SKILL.md`). The Updater (T-rules) and Analytic (R-rules) were deprecated 2026-05-24.
- Me in-session can call `incremental_update` for fresh data if the last `morning_full_scan` was a long time ago.

## History

- **XXXX-05-16** — split out as a composite skill during the P4 refactor. Before that, the incremental mode was described as a parameter of the monolithic `finkoper.md`.

---

_Version 1.0 — 2026-05-16._
