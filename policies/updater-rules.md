# Rules for the `updater` daemon

> The specification of the updater daemon's logic (07:00 Moscow time daily, after `finkoper` and the collectors `news`/`email`, before `analytic` and `dashboard`).
> This file is the source of truth for the updater's logic. When adding a new rule: state the trigger, source, proposal format, severity.
>
> **⚙️ The operational infrastructure is decomposed into `policies/workflows/updater/`** (P4 refactor, 2026-05-16):
> - `read_state.md` — reading all sources
> - `propose_patches.md` — T1-T6 (proposed JSON patches)
> - `apply_t7.md` — T7 (auto-apply of the operator's decisions)
> - `auto_apply_routine.md` — routine technical updates
> - `save_manual_notes.md` — preserving manual notes before overwriting
> - `update_mental_model.md` — updating mental_model per the T-table
> - `write_daily_report.md` — building the daily report
> - `morning_full_scan.md` — the composite pipeline
>
> This file remains the **specification**: trigger semantics, the proposal format, the wording history. The daemon and I in session call the operational workflows from `workflows/updater/`.

---

## Purpose

The updater takes today's fresh collector reports (`finkoper_*.md`, `email_*.md`, `news_*.md`, and `bank_*.md` if present) and **reconciles them with the system's current state** (`clients_data.json`, `registries/`, `Client_card.md`, `history.md` per client). Its job is to **propose pointed updates to the system's state** (JSON patches, registry entries, card notes), but **not to apply them**. Application is via the operator's approval.

Without the updater, new facts that land in the morning reports remain "knowledge in .md" but never reach `clients_data.json` → never reach the dashboard. That is the main justification for the updater's existence.

---

## What the updater does

1. **Reads today's fresh collector reports** (all that appeared in `journal/inbox/` with today's date).
2. **Reads the system's current state:** `clients_data.json`, `registries/request_log.md`, `registries/inbound_sort.md`, `registries/Consolidated_calendar_2026.xlsx`, the local client folders (`SP *`), the cards and histories.
3. **Reconciles:** which fresh fact is relevant to which field in JSON / registry / card. If a fact changes the state — it forms a **patch proposal**.
4. **Writes a report** `journal/inbox/updates_<YYYY-MM-DD>.md` with three sections:
   - **✅ Applied automatically** — only trivial technical updates (e.g. refreshing `monthly_check.today` to the system date; adding the last-sync date).
   - **🔧 Proposed JSON patches** — concrete diffs for `clients_data.json` and the registries, ready to apply with one "OK" from the operator.
   - **🟡 Needs a manual decision** — facts for which there is no unambiguous patch (e.g. an ambiguous message from the manager), with a concrete question for the operator.

## What the updater does NOT do

- **Does not edit `clients_data.json` and the registries itself** (except for "applied automatically" — see the list below).
- **Does not change task statuses in Finkoper** (a separate manager zone + an explicit approval).
- **Does not send anything externally** (letters, messages, files).
- **Does not delete files.**
- **Does not write into client cards and histories** — that is done by the operator (or me in session) after the actual actions.

## What counts as "applied automatically"

Only safe technical updates with no ambiguity:

| Action | Trigger |
|---|---|
| Update `monthly_check.today` in all clients to today's date | Every run |
| Move the "🟢 received" mark in the request log to "closed" if the answer is processed and there is confirmation in one of today's reports | On an explicit match of topic and a mention of the sender's name |
| **Apply a JSON patch per an `operator_decisions.md` entry with status `new`** | Trigger T7. An entry in the operator's decision journal with status `new` = the operator's approval. See T7 below. |
| Write the updater heartbeat (`updater_heartbeat.txt`) | End of run |

Everything else goes through the "🔧 Proposed patches" or "🟡 Needs a manual decision" sections.

**The basis for T7's automatic application:** the operator's clarification on 2026-05-16 in the Cowork chat — "this is your main job, after all — gather the data and update the system, always apply it!". Before that, T7 only formed "🔧 Proposed patches"; now it applies them right away. Source: `journal/inbox/updates_2026-05-16.md`, the section "The main change in the updater's working rule".

---

## Triggers for proposing a JSON patch

### T1 — A manager's decision in a task chat or a DM changes the work direction

**Source:** `finkoper_<YYYY-MM-DD>.md`, the sections "💬 New messages in tasks" and "📨 Team chats — new" (personal DMs with the managers).

**Signal:** in a fresh message from the manager — an explicit directive, an actual decision, cancellation of a prior plan, handing over a task, agreeing an approach. E.g.: "we're connecting the cash register", "we're not replying to the client, drop it", "I'm handing task X to you with deadline Y", "the OFD report is processed, there was no cash".

**What to propose:** for each pair (message, relevant item in `clients_data.json`) — a diff updating the `action` / `note` / `lifecycle_state` / `status` of the corresponding item (e.g. `monthly_check.sources[i]`) or an entry in the client's `special_notes`.

**Example (the current Client F case, 05-15 at 15:01):**

```
🔧 Proposed JSON patch

File: engine/clients_data.json
Path: client_f → monthly_check.sources[6] (title "⚠ Connect the online cash register + correction receipts")

Changes:
  lifecycle_state: (none) → "awaiting_external"
  expected_event: (none) → "Client connects the cash register + sync with the marketplace app"
  status: "gap" → "gap" (unchanged; lifecycle_state removes it from the on-fire list, but the status problem remains until receipts are actually issued)
  action: "Message in task chat #<task_id> sent 22:07 — awaiting the manager's confirmation. After the 'ok' — I gather a comparison of 3 cash-register operators..."
       → "Direction confirmed by the manager 2026-05-15 (DM 15:01): the client connects the cash register + sync with the marketplace app. Awaiting completion of cash-register registration and connection to the OFD. After — a separate task to issue receipts for past-period cash revenue (≈ a large amount). Trigger: the client reports registration / the register appears in the FTS registry."
  note: leave unchanged OR append: "Direction confirmed 2026-05-15: the client handles the cash register, posting the cash revenue — after connection to the OFD."

Source: finkoper_2026-05-16.md, section "📨 Team chats — new → 💬 the manager → item 2 (15:01)"

After applying: run generate.py to regenerate the dashboard; expected effect — the item moves from 🔴 ON FIRE to "WATCHING".
```

### T2 — A Finkoper task status change (open → closed / paused)

**Source:** `finkoper_<YYYY-MM-DD>.md`, the section "✅ Disappeared from open" and/or the `status` field in `finkoper_state/latest/tasks.json`.

**What to propose:** if the task is linked to an item in `monthly_check.sources` or to an active anomaly — a diff: either `status: gap → ok`, or dismissing the anomaly. If there was a decision in the task chat before closing — duplicate it into the `action` of the corresponding item.

### T3 — A new primary-document file in the client's local folder

**Source:** comparing `ls SP *` with yesterday's state (a listing snapshot is needed in `journal/finkoper_state/files_snapshot.json` or equivalent).

**What to propose:** for the corresponding `monthly_check.sources[i]` item — `status: check/gap → check (file received, awaiting posting into 1C)` + a field `last_file_received: YYYY-MM-DD`.

### T4 — A new notification from the FTS / social fund / a bank for a client

**Source:** `email_<YYYY-MM-DD>.md`, the section of letters from government bodies and banks.

**What to propose:** adding an item to the client's `special_notes` + a row in `registries/request_log.md` (received / needs processing).

### T5 — A new anomaly in the news relevant to a client

**Source:** `news_<YYYY-MM-DD>.md` with an explicit deadline and/or fine + reconciliation with client details (OKVED, regime, counterparties, operation volume).

**What to propose:** adding an item to the relevant client's `monthly_check.sources` (or a roll-up item in the system-wide block) with the deadline from the news.

### T6 — A calendar change (Consolidated_calendar_2026.xlsx)

**Source:** the file's mtime + a row diff.

**What to propose:** if a new row for a client appeared in the calendar and it is not in `monthly_check.sources` — a diff adding it.

---

### T7 — Fresh entries in the operator's decision journal

**Source:** `journal/operator_decisions.md` — an append-only journal; the daemons do NOT overwrite it.

**Signal:** new entries in the journal with status `new` (not `applied` and not `cancelled`). Entries newer than the updater's `last_processed_at` (kept in `journal/inbox/updater_heartbeat.txt` or a separate field).

**What to propose:** for each journal entry with status `new`, form a JSON patch in `clients_data.json`. Possible patch directions:

1. **Changes to `monthly_check.sources[i]` fields** — `lifecycle_state`, `status`, `action`, `note`, `last`, `expected_event`. If the entry says "remove from priority, awaiting X" → `lifecycle_state = awaiting_external`, `expected_event = X`.

2. **Changes to `tasks_overrides`** — if the decision concerns a Finkoper task (by `task_id`). E.g. `internal_status = awaiting_external | escalated`.

3. **Adding an entry to `decisions[]`** at the client level — a structured log of the decision made, linked to anomaly_id / source-title / task_id.

   The structure of `decisions[i]`:
   ```json
   {
     "date": "2026-05-16",
     "decision_text": "Awaiting the client connecting the cash register, posting the cash deferred",
     "anomaly_id": "client_f_kkt_offline",
     "applied_fields": ["sources[6].lifecycle_state", "tasks_overrides.<task_id>"],
     "source": "operator_decisions.md, entry 2026-05-16 ~10:00"
   }
   ```

4. **Adding to `dismissed_anomalies[]`** at the client level — if the operator decided to "stop flagging it". The structure:

   ```json
   {
     "anomaly_id": "client_f_manager_clarify",
     "dismissed_at": "2026-05-16",
     "reason": "we do not clarify the wording with the manager",
     "until": null
   }
   ```

   `until` = null — indefinite. Otherwise — an ISO date after which the anomaly is relevant again.

**After applying a patch** — the updater itself changes the journal entry's status from `new → applied YYYY-MM-DD HH:MM`, appending the list of JSON fields that were changed. The operator does not change the status by hand (only if they want to roll back — then `applied → cancelled DD.MM, reason: ...`).

**Journal entry statuses:**
- `new` — awaiting processing by the updater on the next run. Counts as approval.
- `applied YYYY-MM-DD HH:MM` — the patch is applied in JSON, the dashboard regenerated.
- `cancelled DD.MM, reason: …` — the decision was cancelled by the operator after applying. The updater must roll back the corresponding JSON fields on the next run.

**Special attention:** T7 is a MANDATORY trigger. The operator's decisions are **first-class data** of the system and must not be lost when the daily reports are overwritten. If there are unprocessed entries in the journal — the updater is not considered to have completed its run.

---

### Preserving manual notes when overwriting daily reports

Before overwriting `updates_<today>.md` (if the file already exists from a previous run), the updater must:

1. Read the old version of the file.
2. Find blocks of the operator's manual notes — markers:
   - `**📝 Updated DD.MM per the operator's message`
   - `**📝 Operator's comment:**`
   - `**Update DD.MM (operator):**`
   - `**Operator's decision:**`
3. For each found block:
   - Check whether there is already a corresponding entry in `journal/operator_decisions.md` (by content or an explicit reference).
   - If not — add an entry to `operator_decisions.md` (append) with timestamp = mtime of the old file (or today, if the mtime is uninformative).
4. Only after that — overwrite `updates_<today>.md` with the new version.

This rule applies symmetrically to the analytic daemon for `anomalies_*.md` (see `analytics-rules.md`).

---

## Format of the "🔧 Proposed JSON patches" section in the report

Each patch is a separate block:

```
### <Number>. <Client or "System-wide"> — <short gist>

**File:** <relative path to the file>
**Path within the file:** <JSON path or registry section>
**Trigger:** <Tn from the trigger list>
**Source:** <a concrete quote + a reference to the collector report>

**Changes:**
- <field>: <old value> → <new value>
- <field>: <old value> → <new value>

**Expected effect on the dashboard:** <one line — what changes after applying and regenerating>

**Requires:** the operator's approval. Application — a separate step.
```

---

## Source of truth and priorities

On a source discrepancy the updater picks by priority:
1. The client card (`Client_card.md`)
2. clients_data.json
3. Today's fresh collector report (finkoper, email, news)
4. The registries

A discrepancy between (1) and (2) is an R2 anomaly for the analytic daemon; the updater only records it in "🟡 Needs a manual decision".

---

## Updating mental_model on T1-T7

**After applying any JSON patch or recording a fact**, the updater must update the relevant `mental_model.md`:

- For a client patch → `SP <Surname>/mental_model.md`
- For a system-wide fact → `_system-wide/mental_model.md`

**What is updated (by mental_model section):**

| Updater trigger | mental_model section | What changes |
|---|---|---|
| T1 (manager's decision) | "Active tracks" + "Links" | a new/updated track, an edge chain with the decision quote |
| T2 (Finkoper task status change) | "Active tracks" + "History of key decisions" | a track status change (`active` ↔ `done` ↔ `awaiting_external`); an entry in history if significant |
| T3 (new primary-document file) | "Active tracks" (the "What's in the folder" field) + "Waiting items" (clear) | a note about receiving the file, clear the corresponding waiting item |
| T4 (FTS/social fund/bank notification) | "Active tracks" (a new T-N if significant) | creating a track to process the requirement |
| T5 (news with an explicit deadline/fine) | "Understanding snapshot" → "In progress" + "Active tracks" (if applicable) | check applicability to the client, create a track if needed |
| T6 (calendar change) | "Waiting items" | updating deadlines |
| T7 (`operator_decisions.md` entry) | "Active tracks" + "Links" + "History of key decisions" | the track moves to a new status, an edge chain is added to "Links", a short entry to "History" |

**Format of an entry in mental_model:**
- Each update changes the header: `**Last update:** YYYY-MM-DD HH:MM Moscow time` + `**Update trigger:** Tn — short description of the signal`.
- In the sections, edit **only what changes**. Do not rewrite the file in full.
- If rule R6 (preserving manual notes) found a manual edit by the operator — carry it into `operator_decisions.md` BEFORE overwriting the mental_model section.

**When not to update mental_model:**
- If the fact is routine (received a statement → posted it → ok). That goes into `history.md`, not mental_model.
- If the event was already expected and changes nothing in the synthesis. mental_model is about **turning points**, not a log.

**The Karpathy principle:** update, do not recompute. Each T-trigger = an incremental change to the model, not a rebuild from scratch.

---

## Safety

- The updater **never** modifies Client_card.md, history.md, or the scripts (`generate.py`).
- Changes to `clients_data.json` — only via applying a patch on the operator's approval (not the updater itself).
- All proposed patches are logged in `updates_<YYYY-MM-DD>.md`, applied ones — on a separate line "Applied YYYY-MM-DD HH:MM per approval".
- E-signatures and powers of attorney — the updater ignores them (the manager's zone, `memory/ukep_not_my_zone.md`).

---

## Heartbeat

At the end of a run the updater writes `journal/inbox/updater_heartbeat.txt` with a timestamp. By its absence the analytic daemon understands that the updater did not run.

---

## History of the rules

- 2026-05-16 | initial version | formulated after the Client F incident: the manager's decision to connect the cash register (05-15 15:01 DM) was recorded in the morning finkoper report on 05-16, but did not reach `clients_data.json` → the dashboard kept holding the task in 🔴 ON FIRE. The cause — the absence of updater rules formalizing the carry-over of facts from .md reports into JSON.
