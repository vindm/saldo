# resolution-model.md — who takes the next step (the task's resolution edge)

> Policy the runtime reads. Built **on top of** `policies/safety-rules.md §5a/§D` and
> `connectors/mm_update/SKILL.md` (Confidence, Derive-before-asking). Indexed from
> `INSTRUCTIONS.md §0.6`. It names a routing the safety rules already imply — it grants
> **no new permission**.

## The idea — task is a node (WHAT), "who acts next" is an edge (HOW)

A task names the work (the operation). **How it advances is an edge re-computed every cycle:
who takes the next step.** "Ask the operator" is not a kind of work — it is one *value* of that
edge. Do **not** mint a separate "human task" entity per gap (ENTITY-LINKING: tasks are the
hub; reverse links are derived). The edge is **derived** — no new field, no migration; it is
recomputed, never hand-set, so it cannot drift, and it flips for free the moment a collector
lands a datum or the operator raises autonomy.

## `resolution_mode` — three values, single-valued, first match wins

Derived per open task, evaluated in this order:

1. **`wait_external` — DOMINATES.** The task has unmet `blocked_by`, or `status ∈ {awaiting,
   awaiting_external, blocked}`, or its next step needs data / a counterparty a collector is
   already chasing. **Nothing for the operator to do yet.** = today's `status: awaiting`.
2. **`auto`.** The next step is inside the **§5a no-approval set** *and* every gate below holds.
   The sweep does it and logs it.
3. **`needs_operator`.** Anything not waiting that fails an `auto` gate. Surfaces as a normal
   track on the Plan. This is the **operator-audience twin of `client_followup`**
   (`needs_client` = the client-audience version, the existing «Запрос у клиента» bucket) —
   one mechanism, two audiences, not two entities.

`wait_external` is checked first so the three overview lanes stay mutually exclusive (a task
blocked on data shows in neither the unblock queue nor the auto log until the data lands).

## The `auto` gate — ALL must hold

- **Reversibility.** The next step is a §5a *record / acquire / derive / advance* — a state
  write that records an incoming fact, reads a reachable source, computes a derived value, or
  moves the track (`add_history_event`, refresh `next_action`/`assist`). It is **NOT** a
  `track_close` of a work thread, **NOT** outbound (send to a client/authority), **NOT**
  pay/submit. Those are `§D` / `external_sends` / `browser_actions` → operator. *(The one close
  `auto` may perform is an **answered `open_question`** clarification — per `question_resolver`;
  never a work thread.)*
- **Confidence.** `assist.confidence` is **high and objective** (mm_update Confidence +
  Derive-before-asking). Medium / partial / interpreted-across-sources → surface, don't
  act-and-close.
- **Clean.** **No open `state_lint` warning or live high anomaly contradicts the step.** A
  passing *aggregate* does NOT clear *line-level* flags (e.g. `payroll_line_emp`,
  `payroll_reconcile`). ← the April lesson.
- **Autonomy θ.** The instance autonomy threshold permits this action class. Today θ is **high**:
  the sweep *proposes* (advances + surfaces); fire-and-forget is enabled per class only as the
  log proves it safe (see § Autonomy posture).

Fail any → `needs_operator`. The irreversible gate (close / send / pay / submit) is **never**
opened to `auto` by lowering θ — θ only lowers the bar on the **reversible** side.

## This is not new autonomy — it names §5a / §D

`auto` ≡ exactly the set `safety-rules §5a` already lets a daemon do **without approval**
(record incoming signals, derive, advance the track). `needs_operator` ≡ exactly `§D` /
`track_close` + the external/browser gates + low confidence + an open lint/anomaly. The
resolution model adds only three things: (1) it makes "who acts next" an **explicit computed
routing** instead of the implicit always-operator default; (2) it adds the **open-lint/anomaly**
clause to the gate; (3) it runs a **sweep** so a task whose step became doable is advanced even
when no fresh signal arrived for it. No new permission is granted.

## Worked: the April payroll close (why a matching total is not `auto`)

A `payroll_pph21_bpjs` task whose total PPh parity to the incumbent matches to the
rupiah. Tempting to call `auto`. It is **not**:

- closing a payroll thread is a **`track_close` → §D → operator-only**, regardless of parity; and
- the lines carry flags (2 employees not in the roster, a BPJS gap) → the **Clean** gate fails.

So the edge is `needs_operator`. The sweep still does the **reversible half** — recompute,
confirm the match — and sets
`next_action = «Подтвердить закрытие — паритет сошёлся; проверить: 2 сотрудника не в реестре,
дыра по BPJS»`, surfacing it in «🔄 Недавно обновили». **The operator closes.** This is
mm_update §D's «Подтвердить закрытие …» pattern, generalized to every work thread.

## Open questions are tasks too

`open_question` is a `task_type`, so everything above applies to it unchanged. Its `auto` advance
is **acquisition** — read the reachable source, write the answer — and an **answered** question is
the one work item the sweep may close (per `question_resolver`). A question whose answer only a
person holds is `needs_operator`/`needs_client` (surfaced or batched), never fetched. The sweep
checks and advances questions on the same cycle as every other task — they are not a side channel.

**The `track_close` gate does NOT apply to open questions.** «A daemon never closes a track» is the
rule for **work threads** (payments, filings, client-promised work). An **answered `open_question`
is the explicit exception** — closing it is acquisition hygiene, not a work-thread close. Never cite
the `track_close` / §D prohibition as the reason an open question stayed open: if its answer is
reachable, the sweep answers it and closes it. An open question that hangs «because the safety rule
forbids closing tracks» is a **reasoning bug**, not correct behaviour.

**`no_auto_resolve` is a re-evaluatable HINT, not a permanent lock.** It marks a question whose
answer was, at authoring time, external/narrative with no single state field to watch — so the
resolver should not waste a pass guessing. But situations change: a `no_auto_resolve` question can
become **objectively resolvable** — its hypothesis/`next_action` now names a concrete state check
(«есть ли счёт X в `accounts.json`», «deprecated card → moot»). **Every sweep re-evaluates the
flag:** if the question is now answerable from reachable state, **clear the stale `no_auto_resolve`,
acquire the answer, and close** (the allowed open-question auto-close). Honor the flag only while the
answer genuinely stays person-held/narrative. A stale `no_auto_resolve` hiding a resolvable question
is exactly the failure this prevents — the runtime must not rationalise it as «structurally cannot
close».

## Recompute triggers — on-signal AND a sweep

The edge is recomputed (a) **inline on every state update** (mm_update, when a signal is folded
in — the existing path), and (b) by a periodic **sweep** over the nearest active tasks
(`connectors/resolution_sweep/SKILL.md`), several times a day, so a task that became doable
**without a fresh signal** is still advanced. The sweep is the **one scheduled** actualization
daemon; it walks every active task and **folds in** the `open_question` rung logic
(`connectors/question_resolver/SKILL.md`), which is no longer a separate scheduled job.

## Visibility — no new surface

`auto` steps are logged via `add_history_event(auto=True, source='resolution_sweep:…')` and
surface in the overview **«🔄 Недавно обновили»** (and an answered-question close in
**«✅ Недавно закрыли»**, both now always-on). `needs_operator` tasks are just the normal tracks
on the Plan — the filter `resolution_mode == needs_operator` **is** the "unblock queue", and
`assist.confidence` is an **internal routing signal only** — it is NOT rendered on the operator surface (a self-confidence score answers no question Mom has; the row carries `assist.hypothesis`/`next_action` instead). The **execution log = the existing recent-zones
+ `history.jsonl`**; the trust-ledger is the **provenance marker** (`auto` / `source` / `by`) on
entries that already exist. Nothing new is drawn.

## Autonomy posture (θ) — low-autonomy-first is calibration, not timidity

Start with θ **high**: the sweep advances and surfaces but does not fire irreversible-adjacent
actions unattended; the operator confirms. The recent-closed/updated zones + `history.jsonl`
**are** the calibration dataset: as they accumulate correct `auto` steps, θ is lowered **per
action class on evidence**. An operator reverting an `auto` step (see the April revert,
`source: operator_revert`) is a miscalibration signal feeding θ. Build the trust ledger before
trusting it.

## No schema, no migration

`resolution_mode` is **derived** (computed each cycle from `status` / `blocked_by` /
`assist.confidence` / lint / θ) and **never stored**. So this ships as **policy + skill** (engine
pull), writing only existing fields (`history` / `next_action` / `assist`) → **no migration**.
If we later *persist* a calibration outcome (an `auto` step confirmed / reversed) as a new
field, **that** is a migration.

## Related

- `policies/safety-rules.md §5a` (no-approval set), `§D` (close model) — the `auto` /
  `needs_operator` boundary **is** these rules.
- `connectors/mm_update/SKILL.md` — Confidence + Derive-before-asking (the confidence gate);
  §D «Подтвердить закрытие».
- `connectors/resolution_sweep/SKILL.md` — the periodic sweep that applies this model.
- `connectors/question_resolver/SKILL.md` — the `open_question` special case.
- `engine/state_lint.py` — the **Clean** gate reads these checks.
- `tests/runtime_scenarios/` — **S29** is the gate (April: total parity passes, edge =
  `needs_operator`).
