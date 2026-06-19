# Atomic skill: list_tasks

Get a list of Finkoper tasks by filter. Returns an array with basic fields (without fully reading the task chat).

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `tab` | enum | `null` (values: `My tasks` / `Assigned by me` / `Observer` / `null` = all three) |
| `client_id` | string | `null` (if set — only this client) |
| `status` | enum | `open` (`open` / `closed` / `all`) |
| `since` | ISO datetime | `null` (if set — only from this creation / card start date) |
| `limit` | int | `100` (results limit) |

## Algorithm

1. Via Claude in Chrome, open Finkoper.

2. For each tab in `tab` (if `null` — all three):
   a) Open the tab.
   b) Make sure the filter `Status = <status>` (usually "Open"). If it's different — switch it.
   c) Get the list of task cards.
   d) For each card, extract **only metadata** (without opening the task):
      - `id` — from the URL or from the header
      - `url`
      - `role` — `assignee` for "My tasks", `creator` for "Assigned by me", `observer` for "Observer"
      - `title`
      - `client` — from the "Client" field of the card. Reconcile with `clients_index.json → id` (after the Phase 2 migration 2026-05-25; previously it was `clients_data.json → client_id`).
      - `created_at`, `card_start_date` (📅 in the card)
      - `deadline`
      - `priority`, `tag`
      - `responsible`, `observers`
   e) Apply the `since` filter (by `card_start_date` if present, otherwise `created_at`).
   f) Apply the `client_id` filter if set.

3. Deduplicate by `id` — if a task appeared in two tabs (e.g., `assignee + observer`), keep the "strongest" role: `assignee > creator > observer`.

4. Apply `limit`. If there are more tasks — return the first N + the flag `truncated=true, total_seen=M`.

## Return format

```json
{
  "tasks": [
    {
      "id": "26135860",
      "url": "https://app.finkoper.com/tasks/26135860",
      "role": "assignee",
      "title": "re Client A (cash payments, OFD, access)",
      "client_id": "client_a",
      "client": "SP Client A",
      "internal": false,
      "created_at": "2026-04-30T...",
      "card_start_date": "30.04.2026",
      "deadline": "2026-05-15",
      "priority": null,
      "tag": null,
      "responsible": ["the operator"],
      "observers": ["Chernyakova Anastasia"]
    }
  ],
  "count": 1,
  "truncated": false,
  "total_seen": 1,
  "filters_applied": {"tab": "all", "client_id": null, "status": "open", "since": "2026-04-01", "limit": 100}
}
```

## Safety

Read-only. No opening of tasks in this skill (that is `read_task.md`).

## When it is called

- `morning_full_scan.md` — sweeps all 3 tabs in full (`tab=null, status=open, since=2026-04-01`).
- Me in-session, triggered by "what tasks does client X have" (`client_id=X`).
- Me in-session, triggered by "what's new in this tab" (`tab=...`).
- mm_update when analyzing status transitions — compare the current list against the archive (the analytic's R-rules deprecated 2026-05-24).

## Limitations

- Does not read the task chat — only the card. For the chat — `read_task.md`.
- Volume limit: `limit=100` (but usually ≤50 tasks under the filter).
- If the list card does not show the creation date — mark `created_at=null`, **do not open** the task to clarify (that is the job of `read_task`).

---

_Version 1.0 — 2026-05-16._
