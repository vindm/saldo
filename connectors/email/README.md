# Skills for the `email` domain

> All procedures for working with Yandex.Mail as reusable infrastructure. Atomic operations — read_message, read_thread, list_messages. Composites — morning_full_scan, incremental_update.
>
> **Who calls these skills:**
> - The `Scheduled/email/SKILL.md` daemon — in the morning (`morning_full_scan`)
> - Me, in-session — on a trigger from the operator (atomic or composite)
> - The updater on a T4 event (a notification from the FTS/social fund/bank) — `read_message` for a specific email

## Atomic skills

| File | What it does | Parameters |
|---|---|---|
| [`read_message.md`](read_message.md) | Read **one** email in full: headers + body + attachments | `message_id_or_url`, `read_attachments` |
| [`read_thread.md`](read_thread.md) | Read a **thread** (the whole chain of related emails) | `thread_id_or_subject`, `message_count` |
| [`list_messages.md`](list_messages.md) | List emails by filter (sender, date, folder, label) | `from`, `since`, `folder`, `label` |

## Composite skills

| File | What it does | When |
|---|---|---|
| [`morning_full_scan.md`](morning_full_scan.md) | Morning sweep: list_messages(since=24h, filter by known correspondents) → read_message for each match → daily report | Daemon 06:15 MSK; explicit "rebuild the mail" |
| [`incremental_update.md`](incremental_update.md) | Since last_run → list_messages → targeted read_message → append to the daily report | On a "what's new in the mail" trigger during the day |

## Which one to call when

| Trigger from the operator | Skill | Parameters |
|---|---|---|
| "open the email from X with subject Y" | `read_message.md` | `message_id_or_url` or search |
| "read the thread with the FTS about the demand" | `read_thread.md` | `thread_id_or_subject=...` |
| "which emails from Sber in May" | `list_messages.md` | `from=*@sberbank.ru, since=2026-05-01` |
| "what's new in the mail" | `incremental_update.md` | `since=last_run` |
| "rebuild the mail" | `morning_full_scan.md` | — |

## Known correspondents (filter for full_scan)

- **Clients** — email from `state/<client>/identity.json.contacts.email` (via `_loaders.load_clients_from_index()`). After the Phase 2 migration on 2026-05-25, clients_data.json was archived.
- **Government bodies** — domains `@nalog.gov.ru`, `@sfr.gov.ru`, `@rosstat.gov.ru`, `@gks.ru`
- **Client banks** — `@sberbank.ru`, `@tinkoff.ru`, `@tochka.com`, `@vtb.ru`
- **Team** — Anastasia, Alyona (if email addresses exist)
- **Partners** — Yandex.Taxi (for Client A), agents (for Client A)

## Format for calling one skill from another

Analogous to `finkoper/`:

```
1. Read `connectors/email/list_messages.md`. Execute:
   from = null
   since = <24h ago>
   folder = "Inbox"
   Get the array message_metadata[].

2. For each email from a known correspondent:
   Read `connectors/email/read_message.md`. Execute:
     message_id_or_url = <id from step 1>
     read_attachments = false
   Collect the result.
```

## Security

All atomic skills are **read-only**. Per `security_rules.md §3` (updated 2026-05-16): opening an email, downloading attachments into `Downloads/` — no approval needed. Sending an email / creating a draft (with sending) / marking as read / deleting — NEVER in these skills. Creating a draft **without** sending is allowed (via an explicit approval from the operator: "make a draft").

## History

- **2026-05-16** — refactored from the monolithic `Scheduled/email/SKILL.md` (70 lines) into a decomposed structure. P4-email.

---

_Folder created 2026-05-16 as part of P4._
