# Rules for the `analytic` daemon

> The specification of the checks the `analytic` daemon must perform (07:15 Moscow time daily) when scanning the project's working files.
> This file is the source of truth for refinements to the daemon. When adding a new rule: state the source, algorithm, severity, and the anomaly format.
>
> **⚙️ The operational infrastructure is decomposed into `policies/workflows/analytic/`** (P4 refactor, 2026-05-16):
> - `read_state.md` — reading all sources
> - `r1_duplicate_titles.md`, `r2_review_active_anomalies.md`, `r3_overdue_with_decision.md`, `r4_task_status_transitions.md`, `r5_stable_anomaly_ids.md`, `r6_save_manual_notes.md`, `r7_card_vs_json.md` — each rule in its own file
> - `update_mental_model.md` — updating mental_model per the R-table
> - `write_daily_report.md` — building the daily anomalies report
> - `morning_full_scan.md` — the composite pipeline (R4 → R2 → R3 → R5 final filter)
>
> This file remains the **specification**: rule semantics, the anomaly format, the wording history. The daemon and I in session call the operational workflows from `workflows/analytic/`.

---

## R1 — Duplicate rows in `monthly_check.sources` (by `clients_data.json`)

**Source:** `engine/clients_data.json`

**Why:** during manual JSON edits (via Edit or copy-paste), records in the `monthly_check.sources` array get accidentally duplicated. On the client dashboard this creates visual noise; at the next edit there is a risk of desync.

**Algorithm:**
```
for each client c in the array:
    titles = [s["title"].strip().lower() for s in c["monthly_check"]["sources"]]
    counts = Counter(titles)
    dups = {t: n for t, n in counts.items() if n > 1}
    if dups is non-empty:
        create an anomaly (severity=low, see the format below)
```

**Optional (precision):** compare the key `(title.strip().lower(), status)`. The same `title` with different `status` values (e.g. `ok` and `gap`) is a valid case and is not an anomaly; the same `title + status` is definitely a duplicate.

**Severity:** `low` (visual noise, does not block bookkeeping).

**Anomaly format:**
- Title: `System — duplicate row in clients_data.json for client {name_short}`
- Description: `Repeated titles found in monthly_check.sources: {list}. Each occurs {n} times.`
- Context: `Creates visual noise on the dashboard. Safe to delete the extras, keeping one record.`
- Source: `engine/clients_data.json (object {id}, monthly_check.sources)`
- Propose: `Delete the duplicates, keeping one record per title. Afterward — regenerate via generate.py.`

**History:**
- The rule was formulated 2026-05-14 after a case with the client (a duplicate "Z-Report / OFD", recorded 05-13, removed manually 05-14).

---

## R2 — Re-examining active anomalies through fresh signals over the past day

**Source:**
- Active "`gap`" and "🔴/🟡" items from `clients_data.json` (`monthly_check.sources[i]` with `status in {gap, check}` or with `lifecycle_state != awaiting_external`).
- Yesterday's report `anomalies_<YYYY-MM-DD-1>.md` (what was open yesterday).
- Today's fresh collector reports: `finkoper_*.md`, `email_*.md`, `news_*.md`, and `bank_*.md` if present.

**Why:** the analytic daemon must **not only generate new anomalies but re-evaluate existing ones**. If the fresh sources contain a fact that changes the context of an already-recorded anomaly (a manager's decision, primary documents received, a task status changed) — the daemon must link it and propose a review.

**Algorithm:**
```
1. Load the list of yesterday's active anomalies (from anomalies_<yesterday>.md).
2. For each active anomaly:
   a. Determine the client and the topic tag (bank / OFD / cash register / acts / insurance / reporting / correspondence).
   b. Find mentions of the client in today's fresh collector reports:
      - Search by name_short / name_full / name_1c / id / INN in finkoper_*.md, email_*.md, news_*.md.
      - For task chats — especially messages from the manager and the client.
      - For the DM with the manager — all new messages over the day.
   c. Map the found mentions to the anomaly's topic tag.
   d. If there is a fact that changes the context (see T1-T6 in updater-rules.md):
      - Mark the anomaly as `under review`.
      - Provide the quote + date + author of the signal.
      - Propose a new severity (↓ or DISMISSED) or new wording.
      - Reference the relevant JSON patch in updates_*.md (if the updater already formed it).
3. For anomalies with no relevant signals — leave the severity unchanged (by default) or raise it if the expected reply window has passed (rule R3 — age).
```

**Severity:** algorithmic — a re-examination has no severity of its own, it MODIFIES the existing ones.

**Marker format (inside the anomaly block):**
```
**🔁 Re-evaluation per rule R2 (fresh signal {YYYY-MM-DD}):**
Signal: {quote + author + time + source}
Topic link: {why this signal relates to this anomaly}
Proposed change: severity {old → new}, or DISMISSED, or `lifecycle_state: awaiting_external`.
JSON patch: see `updates_{YYYY-MM-DD}.md` block #{N} (if the updater already formed it).
Requires: the operator's approval to apply the review.
```

**History:**
- The rule was formulated 2026-05-16 after an incident with the client: a manager's DM on 05-15 at 15:01 ("we're connecting the cash register + sync with the marketplace app") sat in the morning `finkoper_2026-05-16.md`, but the daemon did not link it on the first run to the active anomaly "⚠ Connect the online cash register + correction receipts" in `clients_data.json` (gap, action from 05-10). The link had to be added by hand after the fact.

---

## R3 — An overdue Finkoper task when there is a directional decision in the chat

**Source:**
- `finkoper_state/latest/tasks.json` — tasks with `status=open` and `deadline < today`.
- `finkoper_<YYYY-MM-DD>.md` — the section "📨 Team chats — new → 💬 <manager>" over the last 7 days.
- The chat inside the task itself (if the Finkoper daemon read it).

**Why:** a task in Finkoper is formally overdue, but if the task chat or the DM with the manager over the last 7 days has set a new work direction / a wait for an external event — this is not "on fire, drop everything" but "controlled waiting". ON FIRE should understand this.

**Algorithm:**
```
for each overdue open task t in tasks.json:
    deadline_passed_days = today - t.deadline
    direction_decided = False
    fresh_signal = None

    # Step 1: look at the DM with the manager over the last 7 days
    for message in manager_DM[last_7_days]:
        if the message mentions t.client_name or t.id or keywords from t.title:
            if the message contains a decision verb
            ("connecting", "not doing", "handing over", "waiting", "deferred until"):
                direction_decided = True
                fresh_signal = message
                break

    # Step 2: look at the task chat (if read)
    if not direction_decided and t.last_message_at:
        for message in chat_task[t.id][last_7_days]:
            if author == manager and there is a decision verb:
                direction_decided = True
                fresh_signal = message
                break

    if direction_decided:
        # Do not mark the task as an "ON-FIRE overdue"
        create an anomaly severity=medium of type "controlled waiting":
            wording: "Task {t.id} is formally overdue by {deadline_passed_days} days,
                       but per the DM/chat on {fresh_signal.date} the direction is confirmed: {quote}.
                       Action: agree with the manager to move the task in Finkoper
                       to 'on hold' / a new deadline / closing — or
                       set internal_status=awaiting_external in our system."
    else:
        # The normal overdue rule
        create an anomaly severity=high "overdue by {deadline_passed_days} days".
```

**Severity:** `medium` when there is a decision / `high` when there is none.

**History:**
- The rule was formulated 2026-05-16 after a the client case on a task: `open + overdue 1 day`, but in a DM on 05-15 the manager set a new direction (waiting for the client to connect the cash register). Without R3 such a task lands in 🔴 ON FIRE and creates false urgency.

---

## R4 — Tracking Finkoper task status transitions

**Source:**
- `finkoper_state/latest/tasks.json` (today) vs `finkoper_state/archive/<yesterday>/tasks.json`.
- The list of task IDs that exist only in archive (disappeared) or only in latest (appeared).

**Why:** right now the finkoper daemon records this in the "✅ Disappeared from open" section, but the analytic daemon draws no further conclusions. Closing a task is an event that affects:
- open anomalies and `gap` items for the client (closing a task often clears an anomaly);
- the request log (a closed task may mean the awaited item was received);
- the calendar (the internal deadline is removed).

**Algorithm:**
```
ids_yesterday = set([t["id"] for t in archive[<yesterday>]["tasks.json"]])
ids_today = set([t["id"] for t in latest["tasks.json"]])

disappeared = ids_yesterday - ids_today      # closed or moved to "not mine"
appeared = ids_today - ids_yesterday          # new

for each task t in "disappeared":
    take the metadata from archive (client, title, deadline, responsible)
    create a marker severity=info:
        "Task {t.id} ({t.client}) disappeared from open.
         Related anomalies and gap items for the client — check whether it is time to clear/update them."

for each task t in "appeared":
    create a marker severity=info:
        "New task {t.id} ({t.client}): {t.title}. Deadline {t.deadline}.
         Check — is there a corresponding item in monthly_check.sources?"
```

**Severity:** `info` (for the "Events" section of the anomalies report).

**Link to R2:** "disappeared from open" is a strong signal for R2 to re-examine the client's active anomalies.

**History:**
- The rule was formulated 2026-05-16 together with R2 and R3.

---

## R5 — Stable anomaly_ids + checking `dismissed_anomalies[]`

**Source:** `clients_data.json` — the `dismissed_anomalies[]` field at the client level (format see `updater-rules.md`, T7).

**Why:** the operator's manual decisions to "stop flagging this anomaly" must survive between daemon runs. Without stable ids and a check of the dismissed-anomalies list, the same topic resurfaces each morning, and the operator's work does not accumulate in the system.

**Algorithm:**

```
for each candidate anomaly:
    1. Assign a stable anomaly_id by the rule:
       - <client_id>_<theme>_<period_or_object>
       - examples: 'client_f_kkt_offline', 'client_a_bank_april_missing',
                  'client_e_bank_april_missing', 'system_controlled_deals_2025'
       - theme is taken from the anomaly's topic tag (banking / ofd / kkt / acts / taxes / docs / process)
       - period — for monthly topics set YYYY-MM or quarter; for indefinite ones — null

    2. Check the client's dismissed_anomalies[]:
       for each elem in client.dismissed_anomalies:
           if elem.anomaly_id == the current anomaly_id:
               if elem.until is null or today < elem.until:
                   do not recreate the anomaly
                   create an entry in the "Events over the day (R4)" section: "Anomaly {id} dismissed by the operator DD.MM, reason: {elem.reason}"
                   skip

    3. Otherwise — normal processing of the anomaly with the assigned anomaly_id.
```

**Anomaly format (the `anomaly_id` field):**

```markdown
#### 🔴 [Banking] the client — Bank for April 2026 — the 01-15 window has closed
**anomaly_id:** `client_a_bank_april_missing`
**Description:** ...
...
```

**Severity:** not changed by this rule; R5 operates at the "whether to generate it at all" level.

**History:**
- The rule was formulated 2026-05-16 after an incident of losing the operator's manual notes: she works with the dashboard daily, corrects the daemon's conclusions, but without `dismissed_anomalies[]` and stable `anomaly_id`s her work is lost at the next run. It cements the mission `system_mission.md`: "self-learning through the operator's decisions".

---

## R6 — Preserving manual notes when overwriting `anomalies_*.md`

**Trigger:** before overwriting `journal/inbox/anomalies_<today>.md` (if the file already exists from a previous run).

**Algorithm:**

```
1. Read the old version of the file.
2. Find blocks of the operator's manual notes — markers:
   - "**📝 Updated DD.MM per the operator's message"
   - "**📝 Operator's comment:**"
   - "**Update DD.MM (operator):**"
   - "**Operator's decision:**"
3. For each found block:
   - Check whether there is already a corresponding entry in journal/operator_decisions.md
     (by content or an explicit reference).
   - If not — add an entry to operator_decisions.md (append) with timestamp = mtime
     of the old file (or today, if the mtime is uninformative).
4. Only after that — overwrite anomalies_<today>.md with the new version.
```

**Why:** the operator's manual work is first-class data and must not be lost. See.

**Severity:** not an anomaly. This is a process rule for the daemon itself.

---

## R7 — Discrepancy between `Client_card.md` and `clients_data.json` on registration details

**Source:**
- `SP <Surname>/Client_card.md` — declared as the **source of truth** (see INSTRUCTIONS.md §3).
- `engine/clients_data.json` — a copy for the dashboards.

**Why:** the card is the source of truth for the registration details, the JSON is its derivative. On a discrepancy the card wins. The updater does not write into cards (`updater-rules.md` section "What the updater does NOT do"), so JSON drift relative to the card is invisible — a separate reconciliation is needed.

**Controlled fields (per client):**

| Card field | JSON field | Parsing the card |
|---|---|---|
| Full SP name | `name_full` | a string from the "Details" table, the "Value" column |
| 1C name | `name_1c` | same |
| INN | `inn` | same |
| OGRNIP | `ogrnip` | same |
| Address | `addr` | same |
| Tax office | `ifns` | same |
| Primary OKVED | `okved` | the first field before " — " in the "Primary OKVED" row |
| Email | `email` | an empty value "—" in the card is treated as `null`/"—" in JSON |
| Phone | `phone` | same |
| Regime | `regime` | the "Regime" row from the "Tax regime" table |
| Bank | `bank_name` | the "Bank" column from the "Bank account" table |
| BIK | `bik` | the "BIK" column |
| Account | `account` | the "Account" column |
| 1C:Fresh base ID | `fresh_id` | the number from the URL `https://msk1.1cfresh.com/a/ea/<ID>/...` |

**Algorithm:**
```
for each client c in clients_data.json:
    card_path = SP <Surname from folder>/Client_card.md
    if the card is not found → severity=medium, anomaly "card missing"
    parse the card → a dict of fields per the table above
    for each pair (card_field, JSON_field):
        norm = lambda x: (str(x or '').strip().lower().replace('«','').replace('»','').replace(' ','')) or None
        if norm(card[field]) != norm(JSON[field]):
            create an anomaly severity=medium with anomaly_id = f"{c['id']}_card_json_mismatch_{field}"
            give both values, name the source of truth (the card)
```

**Severity:** `medium` (the discrepancy itself does not block bookkeeping but distorts the dashboard).

**Anomaly format:**
- Title: `R7 — card vs JSON discrepancy for client {name_short}: field {field name}`
- Description: `Card: "{val_card}". JSON: "{val_json}". Source of truth — the card (INSTRUCTIONS.md §3).`
- Context: `Reconciliation is daily. The discrepancy may have appeared after a manual edit of one source without the other.`
- Source: a reference to the card line + the json-path
- Propose: a JSON patch carrying the value from the card into JSON (if the card is fresher) OR a question to the operator "which source is fresher" (if unclear).
- `anomaly_id`: `{client_id}_card_json_mismatch_{field}` — stable, can be added to `dismissed_anomalies[]` (e.g. if the card intentionally holds a "human" spelling and JSON a machine one).

**Exceptions (not flagged):**
- An empty value "—" in the card = `null` or an empty string in JSON.
- A `email` field with value "—" in both → a match, not an anomaly.
- Extra JSON fields not present in the card (e.g. `monthly_check`, `decisions[]`, `prep_done_2026`) — the card does not describe them, not a discrepancy.

**History:**
- The rule was formulated 2026-05-16 as part of the P0 audit. Trigger: INSTRUCTIONS.md §3 declares the card the source of truth, but there is no regular reconciliation — discrepancies are caught by no one. R7 closes this gap.

---

## R8 — Age-based escalation of anomalies

**ID:** R8
**Source:** `anomalies_*.md` — the "Nth day" counter from R2 + `dismissed_anomalies[]`
**When:** on every run of the `analytic` daemon, after R2 and R5
**Severity:** automatic raise by age, if the anomaly is "escalatable"

### Goal

The daemon already tracks "Nth day" manually (via R2). R8 formalizes the thresholds: if an anomaly lingers past a threshold, severity is raised **automatically**, without a manual decision by the daemon. This removes the dependency on "manual attention" each run.

### Algorithm

1. For each active anomaly from the R2 section, extract the age — the "Nth day" counter.
2. Check `dismissed_anomalies[]` — if the anomaly_id is in the list → skip (already handled by R5).
3. Check escalatability (see the "Non-escalatable" section below) — if not → skip.
4. Apply the thresholds:

| Current severity | Age threshold | New severity |
|---|---|---|
| ⚪ low | ≥ 14 days | 🟡 medium |
| 🟡 medium | ≥ 7 days | 🔴 high |
| 🔴 high | — | stays high |
| 🟣 info | — | not escalated |

5. Add a marker `↑R8 (N days)` to the anomaly title — so the operator sees that severity was raised automatically, not by hand.
6. In the analytics report header, record: "R8 fired for: [list of anomaly_id]".

### Non-escalatable — anomalies that are NOT escalated

An anomaly is not escalated if at least one condition holds:

**By anomaly_id pattern (structural chronic):**

| Pattern | Reason |
|---|---|
| `*_recovery_*` | Long-term accounting restoration (deadline > 6 months) |
| `*_legacy_*` | Tails of past periods, removed on a planned basis |
| `*_fns_2026` | Predictable legislative changes |
| `*_mail_daemon_resets_*` | A technical daemon artifact |

**By keyword in the anomaly body:**
`Escalatable: no` — added by the daemon or the operator manually. When to apply:
- The anomaly awaits an action by an external party (the team accountant, the FTS, the client) and pressure is inappropriate.
- The anomaly is a chronic systemic constraint with no simple fix.
- A background long-term track with a deadline > 60 days or no deadline.

**By default:** all anomalies are escalatable. The marker `Escalatable: no` is added explicitly.

### Example of an anomaly with R8 escalation

```
🔴 **`client_a_period_open_awaiting_accountant` (🔴 high ↑R8 8th day)**
- **Title:** the client — the 1C period is not open: 8 days with no reply from the team accountant
- **Description:** The period from 01.01.2025 is not open in 1C:Fresh. R8 automatically raised severity
  from 🟡 medium: the 8th day exceeded the 7-day threshold. Blocks closing April.
- **Escalatable:** yes (by default)
- **Propose:** escalate to the team accountant with the note "critical, blocks closing April".
```

### Example of an anomaly with the "no" marker

```
🟡 **`<track_id>` (⚪ low, Escalatable: no, 40th day)**
- A long-term low-priority track; escalation is inappropriate.
```

### History

- The rule was formulated 2026-05-24 as part of a system audit. Trigger: the daemon already tracks
  "Nth day" manually in R2 and sometimes raises severity in the description, but the mechanism is nowhere
  formalized. R8 makes the age-based escalation systematic and predictable.
- The first candidates for application (at the time of formulation): `system_loaned_personnel_review`
  (10th day, 🟡→🔴 on the next run), `system_team_contact_in_team_md`
  (13th day, ⚪→🟡 on the next run).

---

## Candidates for the next rules (R9+)

- A check of `prep_done_2026` for empty/stale entries — flag clients that have no data for the current year.

---

## How to add a new rule

1. Give it an ID (`R{N}`) — numbering is continuous.
2. State the source (file/files).
3. Describe the algorithm in pseudocode — so it can be reproduced by hand.
4. State the severity (`high` / `medium` / `low` / `info`).
5. The anomaly template (title + description + context + source + propose).
6. In the "History" section — the date of formulation and the trigger incident.

Edits to this file — via the operator's approval. The `analytic` daemon does not modify this file itself.

---

## Updating mental_model on R-firings

**After every substantive R-firing**, the daemon must update the relevant mental_model.md (per-client or system-wide):

| Rule | mental_model section | What changes |
|---|---|---|
| R1 (duplicate rows) | — | a technical anomaly, mental_model not touched |
| R2 (re-evaluation of an active anomaly) | "Active tracks" (status/severity) + "Links" (a new strong edge) | if the re-evaluation → DISMISSED — the track moves to `done` or is deleted; if ↓severity — update the field in the track |
| R3 (overdue task + decision in chat) | "Active tracks" (`lifecycle_state` → `awaiting_external`) + "Waiting items" | a controlled-waiting marker |
| R4 (Finkoper task status transition) | "History of key decisions" (if significant) + "Active tracks" (close/open) | a task disappeared → possibly close a track; a new task → possibly open a track |
| R5 (stable anomaly_ids + dismissed_anomalies) | — | a technical rule, mental_model not touched |
| R6 (preserving manual notes) | — | a technical rule for the daemon itself |
| R7 (card vs JSON discrepancy) | "Understanding snapshot" → "Not clarified / priority low" | add an item about the discrepancy until it is resolved |

**Principles:**
- The daemon **updates mental_model itself**, without approval (this is a synthesis off the R-rules' results, not an external write action).
- mental_model header: `Last update: YYYY-MM-DD HH:MM Moscow time` + `Update trigger: Rn — short description`.
- Edit **only the changing sections**, do not rewrite the file in full.
- Before editing mental_model — apply R6 (preserving the operator's manual notes).
- If R2 contains a JSON patch for the updater — the daemon references it but does not edit the JSON (that is the updater's work, T1-T7).

**Link to the updater:** the analytic daemon changes the "understanding" (what is active now), the updater — the "state" (what is in JSON). mental_model is updated by both, symmetrically by section.
