# Atomic skill: list_messages

Get a list of emails by filter (without reading the contents — metadata only).

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `from` | string or array | `null` (`null` = all senders; otherwise — specific emails or masks `*@nalog.gov.ru`) |
| `since` | ISO datetime | `null` (only emails after this) |
| `until` | ISO datetime | `null` (only emails before this) |
| `folder` | string | `Inbox` (`Inbox` / `Client folder` / `Spam` / `All`) |
| `label` | string | `null` (Yandex label) |
| `only_unread` | bool | `false` |
| `limit` | int | `100` |

## Algorithm

1. Via Claude in Chrome, open Yandex.Mail, switch to the needed folder.

2. Apply the filters (via the Yandex.Mail UI or search):
   - `from` — the "From" field in the filter
   - `since` / `until` — dates
   - `label` — label
   - `only_unread` — the "Unread" filter

3. Get the list of emails with metadata:
   - `message_id`
   - `url`
   - `from` (name + email)
   - `subject`
   - `datetime`
   - `folder`
   - `labels`
   - `is_unread` — bool
   - `is_in_thread` — bool, whether it belongs to a thread
   - `thread_id` — if in a thread
   - `attachments_count`
   - `preview` — first 200 characters (shown in the Yandex.Mail list)

4. Apply `limit`. If there are more emails — `truncated=true, total_seen=M`.

## Return format

```json
{
  "messages": [
    {
      "message_id": "...",
      "url": "...",
      "from": {"name": "Anastasia Chernyakova", "email": "..."},
      "subject": "No need to send or pay",
      "datetime": "2026-05-15T15:01:00",
      "folder": "Inbox",
      "labels": [],
      "is_unread": false,
      "is_in_thread": true,
      "thread_id": "...",
      "attachments_count": 0,
      "preview": "Anastasia Chernyakova: No need to send or pay..."
    }
  ],
  "count": 1,
  "truncated": false,
  "total_seen": 1,
  "filters_applied": {"from": null, "since": "...", "folder": "Inbox"}
}
```

## When it's called

- `morning_full_scan.md` — `list_messages(since=24h ago, folder=All)` + filtering in the composite by the list of known correspondents.
- `incremental_update.md` — `list_messages(since=last_run)`.
- Me, in-session, on a "which emails from X in a period" trigger.

## Security

Reads metadata only. No opening of emails (that's `read_message.md`).

## Limitations

- Does not read the contents — only what's visible in the Yandex.Mail list (the preview is usually 200 characters).
- If the Yandex.Mail filter doesn't allow an exact date — take a wider range, then filter in the composite.

---

_Version 1.0 — 2026-05-16._
