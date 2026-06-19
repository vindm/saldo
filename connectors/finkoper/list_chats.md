# Atomic skill: list_chats

Get a list of Finkoper team chats with metadata (without reading messages).

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `min_unread` | int | `0` (if >0 — only chats with unread >= this number) |
| `since` | ISO datetime | `null` (if set — only chats with activity after this moment) |
| `type` | enum | `all` (`all` / `group` / `personal`) |

## Algorithm

1. Via Claude in Chrome, open Finkoper, the "Employees" tab.

2. Get the list of chats:
   - Group: "WORK GROUP" (one)
   - Personal conversations: each employee in the visible feed

3. For each chat, extract **metadata** (without opening):
   - `type` — `group` / `personal`
   - `name` — chat name
   - `unread_count` — the badge to the right of the name
   - `last_message_at` — time of the last message (shown in the card preview)
   - `last_message_author` — who
   - `last_message_preview` — preview text (200 characters)

4. Apply the filters:
   - `min_unread` — filter out chats with unread < N
   - `since` — keep only those with `last_message_at >= since`
   - `type` — keep only the needed one

## Return format

```json
{
  "chats": [
    {
      "type": "personal",
      "name": "Chernyakova Anastasia",
      "unread_count": 0,
      "last_message_at": "2026-05-15T15:56:00",
      "last_message_author": "Chernyakova Anastasia",
      "last_message_preview": "I'll prepare it then and send over the link"
    }
  ],
  "count": 1,
  "filters_applied": {"min_unread": 0, "since": null, "type": "all"}
}
```

## Safety

Read-only of metadata. No opening of chats.

## When it is called

- `morning_full_scan.md` — sweep of all chats (`min_unread=0, since=null`).
- `incremental_update.md` — filter by new ones (`since=last_run`).
- Me in-session, triggered by "which chats are active" / "is there anything unread".

## Limitations

- Does not read the content of messages — that is `read_chat.md`.
- A chat with a client (via a separate tab, not "Employees") — not part of this skill.

---

_Version 1.0 — 2026-05-16._
