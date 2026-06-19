# Atomic skill: read_thread

Read the **entire thread** in Yandex.Mail (a chain of related emails).

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `thread_id_or_subject` | string | **required** (the thread id or the start of the subject) |
| `message_count` | int | `null` (if `null` — all emails in the thread; otherwise — the last N) |

## Algorithm

1. Via Claude in Chrome, open the thread (Yandex.Mail groups into threads by default).

2. Extract the thread metadata:
   - `thread_id`
   - `subject` — common subject
   - `participants` — all unique participants (names + email)
   - `message_count_total` — total number of emails in the thread
   - `first_message_at` — when the thread started
   - `last_message_at` — when the last email was
   - `folder` — folder

3. Extract the messages in chronological order (or the last N if specified):

   For each message — the same fields as in `read_message.md` (`from, to, datetime, subject, body_text, attachments[]`).

4. **Do not mark as read.**

## Return format

```json
{
  "thread_id": "...",
  "subject": "FTS demand of 2026-05-12",
  "participants": ["...", "..."],
  "message_count_total": 5,
  "messages_returned": 5,
  "first_message_at": "...",
  "last_message_at": "...",
  "folder": "...",
  "messages": [
    {"from": "...", "datetime": "...", "body_text": "...", "attachments": [...]},
    ...
  ]
}
```

## When it's called

- Me, in-session, on a "read the thread with X about Y" trigger.
- When working through an FTS / social fund demand — the whole correspondence chain is needed.
- `morning_full_scan.md` for emails that belong to an active thread with unread > 0.

## Security

Same as `read_message.md`. Read-only, no marking/deleting/sending.

## Limitations

- If the thread has many emails (>50) — take the last 50 + the `truncated` flag.
- Does not merge emails related by subject but not in the same thread — these are different entities.

---

_Version 1.0 — 2026-05-16._
