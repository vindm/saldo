# DEPRECATED — the finkoper skill has been decomposed

This file is kept as a stub for compatibility. The business logic has been split across atomic and composite skills:

**See [`finkoper/README.md`](finkoper/README.md)** — overview of all skills in the domain.

## Decomposition map

| Was in the old `finkoper.md` | Now |
|---|---|
| `full` mode | [`finkoper/morning_full_scan.md`](finkoper/morning_full_scan.md) |
| `incremental` mode | [`finkoper/incremental_update.md`](finkoper/incremental_update.md) |
| `object` mode for a task | [`finkoper/read_task.md`](finkoper/read_task.md) |
| `object` mode for a chat | [`finkoper/read_chat.md`](finkoper/read_chat.md) |
| "fresh task snapshot" step | [`finkoper/list_tasks.md`](finkoper/list_tasks.md) + [`finkoper/read_task.md`](finkoper/read_task.md) |
| "fresh chat snapshot" step | [`finkoper/list_chats.md`](finkoper/list_chats.md) + [`finkoper/read_chat.md`](finkoper/read_chat.md) |
| "reconcile with the notification bell" step | [`finkoper/check_notifications.md`](finkoper/check_notifications.md) |

## Why we decomposed it

Each skill is one operation (SRP). Atomic skills are reused by different composites and different executors (the daemon, me in-session, the analytic, the updater). See the history in `README.md`.

---

_File left as a stub on 2026-05-16 during the P4 refactor. Delete at the next consolidation._
