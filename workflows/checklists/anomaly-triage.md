# Checklist: triaging an anomaly from the dashboard

Applies when clicking the "🔍 Investigate" prompt next to an anomaly in the dashboard. The goal — understand whether the problem is real, what to do about it, and record the decision in the system so the anomaly doesn't resurface.

## Stage 1. Anomaly context

- [ ] Open `_Planning/_diary/incoming/anomalies_<today>.md`
- [ ] Find the specific block by its text and `anomaly_id` (format `{client_id}_{theme}_{period}`)
- [ ] Read the fields: `Description`, `Context`, `Source`, `What I propose`, severity (🔴/🟡/⚪)
- [ ] If there's a `🔁 Reassessment R2` marker next to it — read both phrasings: the original and the new

## Stage 2. The primary source

- [ ] Follow the link in the `Source` field — it's today's collector report: `finkoper_*.md` / `email_*.md` / `news_*.md` / `updates_*.md`
- [ ] Read the **full** context, not just the quote from the anomaly. The goal — see whether the source had additional signals lost in the quoting
- [ ] For Finkoper tasks — open the task itself via `Claude in Chrome`, read the whole chat (per `sync_protocol.md`)

## Stage 3. Cross-check with the client's state

- [ ] Open `client-card.md` for this client
- [ ] Read the last 3-5 entries of `history.md`
- [ ] Find the corresponding item in `monthly_check.sources[]` by `anomaly_id` or by `title`
- [ ] Compare the facts: "what the anomaly claims" vs "what's actually in the card/JSON"

## Stage 4. Classification

One of four options:

- **(A) Real problem** — the data confirms the anomaly, action is needed. Go to Stage 5(A).
- **(B) False positive** — the anomaly is wrong (for example, the file actually is in the folder but `ls` lagged; or the daemon's rule is too strict). Go to Stage 5(B).
- **(C) Controlled waiting** — the problem is real, but no action is needed from us until an external event (the client connects a cash register, the FTS replies, the bank sends a statement). Go to Stage 5(C).
- **(D) R2 reassessment needed** — over the past day a new signal appeared that changes the anomaly's context (a DM from the supervisor, the closure of a related Finkoper task). Go to Stage 5(D).

## Stage 5. Decision and recording

### 5(A). Real problem — action plan

- [ ] Formulate concrete steps to resolve it (send a request to the client / request documents from the supervisor / post into 1C / clarify a rule)
- [ ] Show the plan to the operator, get approval
- [ ] Execute the steps (see the relevant checklists: `monthly-primary-documents.md`, `reply-to-tax-authority.md`, etc.)
- [ ] After resolving — set `lifecycle_state` of the `monthly_check.sources[]` item in the JSON → `done`, or `status` → `ok`. The updater will do this on the next run via T1/T2

### 5(B). False positive — a lesson for the daemon

- [ ] Record the fact in `_diary/lessons.md` as a short one-liner: `YYYY-MM-DD | <client or general> | lesson phrasing`
- [ ] Propose a new rule for `analytics_rules.md` (R8+) or a refinement of an existing one — as a separate approval
- [ ] Add an entry to `_diary/operator_decisions.md` with status `new`: "Anomaly {anomaly_id} — false positive, cause: {…}". On the next run the updater adds it to `dismissed_anomalies[]`

### 5(C). Controlled waiting

- [ ] Add an entry to `_diary/operator_decisions.md` with status `new`: "Anomaly {anomaly_id} — `awaiting_external`, waiting for: {expected_event}, open trigger: {…}"
- [ ] On the next run (per T7) the updater adds:
  - `monthly_check.sources[i].lifecycle_state = "awaiting_external"`
  - `monthly_check.sources[i].expected_event = "..."`
  - an entry in `decisions[]` at the client level
- [ ] The item moves out of 🔴 BURNING into the "WATCHING" dashboard section

### 5(D). R2 reassessment

- [ ] Add an entry to `_diary/operator_decisions.md` with status `new`: quote the new signal, specify the `anomaly_id`, propose a new severity (↓ or REMOVED)
- [ ] The updater applies it on the next run

## Stage 6. Closing in the system

- [ ] Entry in `_diary/operator_decisions.md` (if not already there) — added
- [ ] Entry status: `new` (the updater applies it automatically on the next run)
- [ ] If the anomaly is dismissed indefinitely — it will be in `clients_data.json[client].dismissed_anomalies[]`
- [ ] Manual dashboard regeneration isn't needed — the updater applies everything and the dashboard daemon regenerates

## What NOT to do

- Don't close an anomaly "from a truncated preview" in the Finkoper bell or from a report header — always read the full context (`sync_protocol.md`, `task_analysis_depth.md`).
- Don't edit `anomalies_*.md` manually without a parallel entry in `operator_decisions.md` — the next daemon run rewrites the file and the marker is lost (`human_decisions_persistence.md`).
- Don't try to "fix" the analytics rule by editing `Scheduled/analytic/SKILL.md` directly — that's business logic, it should live in `analytics_rules.md` (see the SKILL.md → analytics_rules.md architecture).
- Don't ignore an anomaly if it's "the same for the third day in a row" — that's an R3 escalation signal; severity should rise, not fall.
