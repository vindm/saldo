# Skill: resolution_sweep — re-check every active task's next step, advance what the system can do itself

**The one scheduled actualization daemon (the same runtime)** that walks **every active task** (not only open
questions), recomputes each task's **resolution edge** (`policies/resolution-model.md`), and
**takes the next step itself** whenever that step is in the `safety-rules §5a` no-approval set
and passes the `auto` gate. Tasks that need a person stay normal tracks; tasks waiting on
external data are left. This is the missing **sync moment**: collectors only touch a task when a
**fresh signal arrives for it** — this sweep advances a task whose next step became doable from
data **already in hand**, even when no new signal arrived.

> **Folds in `question_resolver`.** That file is the named `open_question` rung logic, **not a
> separate scheduled job**; this sweep is the single scheduled daemon and runs that logic over
> open questions as part of its pass over **all** active tasks. Same engine:
> it runs the **mm_update** protocol (`connectors/mm_update/SKILL.md`) — reads, decides, writes
> state via `state_ops`/`_tracks`. "The daemon is the same me, just launched on a schedule."

## Why this exists

The system was designed so that the moment state changes, the runtime re-decides each affected
task and does the next step if it can. But the trigger was **reactive only** — `mm_update` fires
when a signal arrives **for a task**. A task whose next step is already doable from data in hand,
with no fresh signal, sat untouched. (Concretely: an April payroll whose `next_action` read
«можно закрывать — паритет сошёлся» stayed active because nothing re-triggered it; migrations
were deterministic Python and never ran a runtime pass over the existing tasks.) This sweep is
that pass, standing — it re-evaluates the **nearest active tasks** every cycle.

## Trigger & ordering

- Scheduled via `config/instance.yaml → schedule.resolution_sweep` (`07:00`, **after** the morning
  collectors so it works only the **residue** — never re-doing a collector's job — and **before**
  the monitors, honoring collect → resolve → derive → render). It is the **only** scheduled
  resolution job (the former separate `question_resolver` 07:00 job is folded in here). A midday
  second pass to re-check tasks that **no fresh signal** touched is desirable, not yet scheduled.
- On demand: the operator says "пройдись по задачам / сделай сверку / advance what you can".
- Process `status: active` tasks whose last sweep attempt isn't already this cycle (a per-task
  attempt log makes a same-cycle re-run a no-op). Skip `deferred`; skip `zone: system_internal`.

## Algorithm — per active task

> Cognitive, one task at a time. Load the client's full state first (mm_update Step 2). Resolve
> the client's jurisdiction (INSTRUCTIONS §0) before any portal / term / deadline.

For each active task, compute `resolution_mode` (`policies/resolution-model.md`) and act:

1. **`wait_external` first — it DOMINATES.** Unmet `blocked_by`, `status` awaiting/blocked, or
   the next step needs data / a counterparty a collector is already chasing → **leave it**.
   Record nothing new unless the wait reason itself changed (anti-spam).
2. **Read the next step** — `next_action`, `assist.hypothesis`, `assist.actions[]`. They usually
   already name the source and key (a file in Drive, a registry by INN, the payroll sheet).
3. **Classify reversibility** (the auto gate):
   - **Reversible / §5a** — acquire (Drive/registry/1C/OFD/bank read), derive/compute, record a
     fact, advance the track (`add_history_event`, refresh `next_action`/`assist`). Candidate for
     `auto`.
     **An `open_question` is walked and advanced like any task**, not skipped: its reversible
     advance IS the acquisition — read the reachable source named in its hypothesis (Drive file,
     registry by key, 1C/OFD/statement), write the answer to the right `state/*.json`, and (only
     here) close the answered question. I.e. the sweep runs `question_resolver`'s rung-1/2 logic
     as its `auto` action for `open_question`; rung-3 (input only a person holds) is surfaced/
     batched, never fetched.
   - **Irreversible** — a **`track_close` of a work thread**, outbound (send to a client/
     authority), pay/submit → **never `auto`** (`§D` / `external_sends` / `browser_actions`). The
     **one** exception is an **answered `open_question`** close → hand to `question_resolver`.
4. **Check the rest of the `auto` gate:** `assist.confidence` is **high & objective** (mm_update
   Confidence + Derive-before-asking); **Clean** — read this task's `state_lint` state, and if any
   warning or live high anomaly sits on it, the step is **not** `auto`; **θ** permits the class.
5. **Act:**
   - **`auto` (all gates pass).** Do the reversible step via the matching workflow; write via
     `state_ops`/`_tracks`; `add_history_event(auto=True, source='resolution_sweep:…')`; refresh
     `next_action`/`assist`. For an answered `open_question`, delegate the close to
     `question_resolver` (the only auto-close).
   - **`needs_operator` (a gate failed).** Do the **reversible half** if there is one (recompute,
     confirm the match), then set `next_action` to the **operator** step — for a ready-but-
     close-gated work thread, «Подтвердить закрытие — <почему готово>; проверить: <открытые
     флаги>» (mm_update §D) — and leave `status` active so it surfaces in «🔄 Недавно обновили».
     **Never** close, send, pay, or submit.
6. **Always log the attempt** — including "проверено, продвигать нечего" (coalesced/anti-spam,
   exactly as `question_resolver` logs its misses). The track history is the per-task diary; the
   `auto` steps are the trust-ledger that lets θ be lowered on evidence.

## Open questions are in scope (not a separate pass)

`open_question` is just a `task_type`, so the sweep walks and advances it like every other active
task — checking each cycle whether its answer has become reachable and, if so, acquiring it and
closing it (the one auto-close). `connectors/question_resolver/SKILL.md` is the **named rung
logic** for that acquisition, not a competing daemon and **not separately scheduled**: this sweep is the single scheduled pass
and runs that logic over open questions alongside every other task, so a question whose source
landed by run time is answered in the same pass. Same gate, same
provenance, same anti-spam attempt log.

**Re-evaluate `no_auto_resolve` every pass — it is a hint, not a lock.** A question flagged
`no_auto_resolve` is normally skipped (its answer was external/narrative). But check each pass
whether it has become **objectively resolvable** — its hypothesis/`next_action` now points at a
concrete state check (e.g. «есть ли счёт X в `accounts.json`», a deprecated card → moot). If so,
**clear the stale flag, do the read, and close** (the allowed open-question auto-close) — do NOT
leave it hanging and do NOT invent a `track_close` reason: the `track_close`/§D prohibition is for
**work threads only**, never for an answered open question. Honor the flag only while the answer
genuinely stays person-held.

## The Clean gate (the April lesson) — an aggregate does not clear line flags

A passing **total** (payroll PPh parity to the rupiah) does **not** make the close `auto` — and
in fact closing a payroll thread is `track_close` = operator-only anyway. Beyond that: if
`state_lint` warns on the task (`payroll_line_emp` — an employee not in the roster;
`payroll_reconcile`; a live high anomaly), the step is `needs_operator` regardless of the
matching total. Surface the flags in `next_action`; the operator decides. Confidence is the
brake: when in doubt, advance-and-surface, never act-and-close.

## Safety (inherits `policies/safety-rules.md §5a/§D`)

- **Reads & reversible advances need no approval** — acquisition and `state_ops`/`_tracks`
  writes that record/derive/advance are the sweep's job, applied directly.
- **Closing a work thread is the operator's, never the sweep's** (`track_close` gate, mm_update
  §D). The sweep updates + sets «Подтвердить закрытие …»; the operator closes from the card.
- **Outbound stays gated** — any message/filing to a client or authority is **drafted** only.
- **Browser fetches** — read-only registry/portal lookups are acquisition; if the safety config
  gates `browser_actions`, run them as the approved job, not per-task.
- Credentials / PIN / captcha → stop, leave the task, name the blocker for the operator.

## Autonomy θ — propose first

Today θ is **high**: the sweep **advances + surfaces**; it does not fire close/send/pay/submit,
and (per action class) holds even a reversible `auto` step behind the operator until the log
proves the class safe. θ is lowered **per class, on evidence** from the recent-zones +
`history.jsonl`. An operator revert (`source: operator_revert`) is a miscalibration signal. Full
rationale: `policies/resolution-model.md § Autonomy posture`.

## Deployment note (lands by pulling the engine — no migration)

Writes only **existing** fields (track `status` is only ever *advanced*, plus `history` /
`next_action` / `assist`), so it ships as **engine files + a schedule line — no data migration**
(no schema change). Registering the actual job is the manual daemon-wiring step
(`connectors/scheduler/SKILL.md`, Saldo-owned `saldo-resolution_sweep`). If we later persist a
calibration outcome (an `auto` step confirmed/reversed) as a new field, **that** is a migration.

## Related

- `policies/resolution-model.md` — the edge spec this skill applies (the `auto` gate, θ).
- `connectors/question_resolver/SKILL.md` — the `open_question` rung logic this sweep runs (not separately scheduled; the only auto-close).
- `connectors/mm_update/SKILL.md` — Confidence, Derive-before-asking, §D «Подтвердить закрытие».
- `policies/safety-rules.md §5a/§D` — the `auto` / `needs_operator` boundary **is** these rules.
- `engine/state_lint.py` — the **Clean** gate reads these checks.
- `tests/runtime_scenarios/` — **S29** is the gate (April: total parity passes, edge = `needs_operator`).
