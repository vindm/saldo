# Skills of the `finkoper` domain

> All procedures for working with the Finkoper system as reusable infrastructure. Atomic operations (read_task, read_chat, list_tasks, list_chats, check_notifications) are system calls. Composites (morning_full_scan, incremental_update) are pipelines.
>
> **Who calls these skills:**
> - The daemon `Scheduled/finkoper/SKILL.md` — in the morning (composite `morning_full_scan`)
> - Me in-session — triggered by the operator (atomic or composite depending on the trigger)
> - The `analytic` daemon — during R-checks of a specific task (atomic `read_task`)
> - The `updater` daemon — on T2 (task status transition) to refine the card (atomic `read_task`)

## Atomic skills

| File | What it does | Parameters |
|---|---|---|
| [`read_task.md`](read_task.md) | Read **one** task in full: card + chat + attachments | `task_id`, `read_attachments` |
| [`read_chat.md`](read_chat.md) | Read **one** chat (group or personal) — the last N messages | `chat_id_or_name`, `message_count` |
| [`list_tasks.md`](list_tasks.md) | Get a list of tasks by filter (tab, client, date, status) | `tab`, `client_id`, `since`, `status` |
| [`list_chats.md`](list_chats.md) | Get a list of chats with unread/last message | `min_unread`, `since` |
| [`check_notifications.md`](check_notifications.md) | Open the notification bell, return new signals | `since` |

Each atomic skill:
- Performs **one operation** (reads one entity or one list)
- Does not write to `latest/`, does not edit JSON, does not update state — that is the job of composites or the caller
- Does not write to the daily report — it returns data into the caller's context

## Composite skills

| File | What it does | When it is called |
|---|---|---|
| [`morning_full_scan.md`](morning_full_scan.md) | Full morning sweep: list_tasks across 3 tabs → read_task for all → list_chats + read_chat for new ones → check_notifications → diff against `latest/` → daily report + snapshot rotation + heartbeat + applying signals via mm_update | Daemon in the morning at 06:30; explicit "rebuild Finkoper" |
| [`incremental_update.md`](incremental_update.md) | Incremental update: check_notifications(since=last_run) → for new signals, targeted read_task / read_chat → appends to the daily report with a marker, updates `latest/` + applies signals via mm_update to state | Me in-session, triggered by "check Finkoper", "something new came up" |

## When to call which one

| Trigger from the operator | Skill | Parameters |
|---|---|---|
| "open task #N" | `read_task.md` | `task_id=N, read_attachments=true` |
| "what's in the chat with Anastasia" | `read_chat.md` | `chat_id_or_name=Anastasia Chernyakova, message_count=20` |
| "what tasks does Client A have" | `list_tasks.md` | `client_id=client_a, status=open` |
| "check Finkoper" | `incremental_update.md` | — |
| "rebuild Finkoper" | `morning_full_scan.md` | — |
| "what's new overall" | `check_notifications.md` | `since=last_run` |

## Format for calling one skill from another

In a composite skill, state explicitly:

```
1. Read `connectors/finkoper/list_tasks.md`. Execute the algorithm with parameters:
   tab = "My tasks"
   status = "open"
   since = "2026-04-01"
   client_id = null
   Get the list of task_id.

2. For each task in the list:
   Read `connectors/finkoper/read_task.md`. Execute with:
     task_id = <id from step 1>
     read_attachments = false
   Collect the result into new_snapshot.tasks.
```

This is the standard pattern: `Read <path> → execute → collect the result → next call`. No formal YAML/JSON workflow, human-readable.

## Safety

All skills are **read-only**. Per `security_rules.md §4` (updated 2026-05-16): reading tasks, chats, downloading attachments into `Downloads/` — no approval required. Sending messages / changing statuses / deleting — NEVER in these skills.

## History

- **2026-05-16** — refactored from the monolithic `finkoper.md` (203 lines, 3 modes) into a decomposed structure following the SRP principle. P4 refactor.
- **2026-05-24** — P-fix "reduce turns" after two consecutive runs hit the limit of 100. Added the sections "Optimized pipeline v2" in `morning_full_scan.md`, "UI map" in `check_notifications.md`, "Known pitfalls" in `read_chat.md` and `read_task.md`. Target budget for the morning sweep — 20–35 turns (was 45–85+).
- **2026-05-24 (evening)** — **canonical attachment-extraction pipeline** added to `read_task.md`. Solving the Client A task #26779260 showed that the built-in "Download all attachments" button in the wizard works via JS click → ZIP in Downloads → cp via the direct mount path → unzip → cp into `WORKDIR/_Inbox/` → Read as a multimodal image. Fully autonomous, ~8-12 turns for a task with 4 attachments. The memory `finkoper_blob_attachments_workflow.md` recorded that the workflow is solved. Safety rules §4 updated — no approval required. The `morning_full_scan.md` skill, Principle 2, was updated with a reference to the canonical pipeline.

---

_Folder created 2026-05-16 as part of the P4 reusable-skills infrastructure._
