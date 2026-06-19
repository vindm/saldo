# Client mental_model template

> **What this is.** A per-client mental model — a synthesized picture of the client: where the understanding stands now, which tracks are active, which connections exist between signals, what we're waiting for. It **does not duplicate** the details (`client-card.md`), the chronology (`history.md`), or the structured items (`clients_data.json`) — it provides **meaning** on top of them. Updated incrementally on every significant signal.

## Location

```
_Planning/SP {Surname}/
  client-card.md            ← static details
  history.md                ← append-only chronology
  Deadline_calendar_2026.xlsx
  mental_model.md           ← SYNTHESIS (this file)
```

For tracks and facts not tied to a specific client:
`_Planning/_systemwide/mental_model.md`

## File structure (6 sections)

### Header (3 lines)

```
> **Last updated:** YYYY-MM-DD ~HH:MM MSK
> **Update trigger:** <short description — which signal led to the update>
```

### 1. Snapshot of understanding

Three blocks in one section:

- **Known** — conclusions we're confident in, with a source reference (if it matters). Example: "USN income 6%, no employees, OKVED 49.32". Not details — conclusions.
- **In progress** — current active processes, without details (details — in the tracks below).
- **Unknown / priority low** — gaps in the data that we're aware of and keep in focus.

### 2. Active tracks

Each track is a separate subsection `### T-N — short title`. Fields:
- **Status:** `active` / `awaiting_external` / `blocked` / `done` (the last — for recently closed ones)
- **Scope / risk:** optional — if there's a financial risk or penalty, state it with a reference to the relevant Tax Code / Code of Administrative Offenses / 54-FZ article
- **What we're waiting for:** for `awaiting_external` — which external event. The trigger for action on our side
- **Linked entities:** a list of references to `monthly_check.sources[i]`, `tasks_overrides[task_id]`, `decisions[N]`, Finkoper DMs/tasks, etc. — the "strong edges" that hold the track together
- **Next action:** one line, what we do next

A check for whether something qualifies as a "track":
- Several linked entities (at least 2)
- Duration > 1 day
- It makes sense to separate it from the routine

Don't turn routine tasks into tracks. "Request a statement from the supervisor" isn't a track, it's an action. "Connecting a cash register and posting prior-period cash revenue" is a track.

### 3. Connections (strong edges)

The graph is materialized as ASCII arrows in the format:

```
Signal
    ↓ interpretation
Decision
    ↓ T7 updater
JSON patch
    ↓ in parallel
Action in Finkoper / 1C / email
    ↓ update
Card / history
```

We indicate only **strong** connections (a state change, a lifecycle_state transition, a task closure, an operator decision). Not every read.

Dismissed anomalies — as a separate block with the `anomaly_id` and the reason.

### 4. Expectations

A table:

| What we're waiting for | Where the signal will come from | When |
|---|---|---|

Don't duplicate the tracks — here only what we genuinely expect from outside (not "do the posting", but "receive the May statement").

### 5. History of key decisions

5-7 lines of "significant turning points". The full history — in `history.md`. Here — only what changes the mental model.

### 6. What I DON'T remember / should find out

An explicit list of data gaps that the system can proactively close. Hints for:
- daemons (what to look for in fresh reports)
- sessions (what to ask clarifying questions about)
- the operator herself (what not to forget to clarify)

**Filters by client type — what is NOT a gap:**

| track | Not a gap | Why |
|---|---|---|
| `team` | Email, phone, direct communication channel with the client | The operator doesn't write to the client directly. All communication goes through the supervisor. Empty contacts in the card are the norm. |
| `team` | Details for direct primary-document requests to the client | Primary documents come through the supervisor, not from the client directly. |
| `direct` | — | For direct clients, contacts are needed — they're in the operator's zone. |

> **Rule:** before adding an item to this section — check the client's `track` in `clients_data.json`. If the item isn't applicable to this type of arrangement — don't add it.

## Who updates it and when

| Source | What it updates | When |
|---|---|---|
| Updater (T1-T7) | "Active tracks", "Connections", "Expectations" | On every signal at the "changes the understanding" level |
| Analyst (R1-R7) | "Snapshot of understanding" ("In progress" block), "Active tracks" (status) | On an R-trigger that changes the context of an active track |
| Me (session with the operator) | Any section on a trigger from the operator | Before the reply, not after |
| The operator manually | Any section | At any moment. Her edit is the new model |

**Rule R6 applies symmetrically:** before overwriting mental_model.md, daemons check for manual markers (`📝`, `Operator decision:`) and move them into `operator_decisions.md`.

## What we DON'T put in mental_model

- SP details (that's `client-card.md`)
- Detailed event chronology (that's `history.md`)
- The full `monthly_check.sources` list (that's `clients_data.json`)
- Full decision text (that's `operator_decisions.md`; in mental_model — only the title and a reference)
- Version history of edits (that's git / `.bak`)

## Size

Target size: **150-300 lines**. If the file grows:
- Move large tracks into `_systemwide/<track name>.md`
- Trim the "don't remember" list after items are closed
- History of key decisions — the last 5-7, the rest in `history.md`

## The Karpathy principle

Not RAG ("each time search for relevant context") but **memory updates** ("the model updates itself; reading it costs pennies"). The mental model is what I **already know** about the client. Analysis on a trigger = updating the model, not recomputing it.

---

_Template created on 16.05.2026 as part of the P3 system audit. Version 1.0._
