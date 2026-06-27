# Skill: scheduler — reconcile the operator's Saldo daemons to the declared schedule

Keeps the **actual** set of scheduled jobs on an operator's machine in sync with the
**declared** desired-state in `config/instance.yaml`. The operator changes *what runs and
when* by editing config (or asking in chat); this skill converges the machine to it —
idempotent, dry-run first, approval to apply. It is to **jobs** what `migrations/` is to
**data**: a declarative target plus a reconciler that makes reality match it.

> **Why this exists.** The daemons (`resolution_sweep`, the morning collectors, `dashboards`)
> are declared in `config/instance.yaml → schedule`, but nothing wired that declaration to the
> real scheduled tasks on Mom's laptop — registering them was a manual, drift-prone step (a
> known tail). This skill closes that gap so every operator runs the *same* daemon set,
> correctly configured, and can answer "are my daemons actually running?"

## Source of truth (the desired set `D`)

Built from config + the runbooks — never invented:

- **`config/instance.yaml → schedule`**: `name: "HH:MM"` (local to `instance.timezone`). The set of jobs and their cadence.
- **`config/instance.yaml → connectors.<x>.enabled`** + jurisdiction: a job is in `D` only if its connector is enabled and relevant to this instance (e.g. `tbank`/`alfabank` only for the direct circuit; a non-RU instance drives its pack's portals).
- **`connectors/<name>/SKILL.md`**: the job's runbook — used to build the task prompt. The scheduled prompt is a **thin loader that points at the runbook**, never a copy of its logic, so editing the runbook does not require re-registering.

## The actual set (`A`) and ownership — the hard safety line

`A` = `list_scheduled_tasks`, **filtered to Saldo-owned tasks only**. Ownership is identified by:

- **taskId prefix `saldo-<name>`** (e.g. `saldo-resolution_sweep`, `saldo-email`, `saldo-dashboards`), and
- a **marker line** in the generated prompt: `# [saldo-managed: <instance.id>]`.

🔴 **Never create, modify, disable, or delete a task that is not Saldo-owned.** The operator's
personal scheduled tasks (job scouts, reminders, property-management routines) are off-limits —
match the prefix *and* the marker before touching anything. When unsure, treat it as not owned.

## Reconcile algorithm (dry-run by default)

1. **Build `D`** from config + runbooks (above). For each job derive the cron per its **cadence**
   (below) and the self-contained prompt (below).
2. **Build `A`** = Saldo-owned scheduled tasks from `list_scheduled_tasks`.
3. **Diff:**
   - in `D`, not in `A` → **CREATE** (`create_scheduled_task`, taskId `saldo-<name>`, cron, prompt).
   - in both, **drift** (cron/time, prompt version, enabled, description) → **UPDATE** (`update_scheduled_task`).
   - Saldo-owned in `A`, not in `D` (job removed/renamed in config) → **DISABLE** (`update_scheduled_task` `enabled:false`). Prefer disable over delete so a mistaken removal is recoverable. (Concretely: after the upgrade that folds `question_resolver` into the 07:00 sweep, the retired `saldo-question_resolver` is **disabled** here — its logic now rides `saldo-resolution_sweep`.)
   - everything else → **leave untouched** (not ours).
4. **Show the plan** — a compact table: `CREATE saldo-resolution_sweep @ 07:00`,
   `UPDATE saldo-dashboards (07:30→07:45)`, `DISABLE saldo-oldjob`, plus "N already in sync".
5. **Apply only on operator approval.** Creating/updating/disabling a job is a configuration
   change → the `track_close`-class approval gate; `create_scheduled_task` also shows its own
   approval dialog. Dry-run (plan only) needs no approval.

> 🔧 **Tooling limit — no programmatic delete.** The scheduled-task API exposes
> `create` / `list` / `update` only. "Remove" therefore means **disable** (`enabled:false`) — the
> reconcile can stop a stale Saldo job but **cannot delete the entry**. Fully removing a disabled
> task is a **manual operator action** in the app's Scheduled panel. So a reconcile leaves stale
> Saldo jobs *disabled*, and the plan should say `DISABLE` (never "delete"); flag the leftover for
> the operator to delete by hand if they want it gone.
6. **Idempotent:** re-running with no config change converges to "all in sync, nothing to do".

## Cadence — daily / weekly / monthly

A `schedule` entry's value takes one of two forms, and the cron (5-field, **local time**) is
derived from it:

- **Shorthand** `name: "HH:MM"` → **daily**: `M H * * *` (the common case — collectors, the
  nightly resolver, the cheap monitors).
- **Object** `name: { at: "HH:MM", cadence: daily|weekly|monthly, weekday: mon…sun, day: 1–28 }`:
  - `cadence: weekly` + `weekday: mon` → `M H * * 1` (turnover moves monthly, so
    `threshold_monitor` runs weekly).
  - `cadence: monthly` + `day: 1` → `M H 1 * *` (registry/credentialed jobs that needn't run
    often, e.g. `counterparty_status`). Keep `day ≤ 28` so every month fires.
  - `cadence: daily` → same as the shorthand.

Pick cadence by cost (`docs/COVERAGE-MAP.md`): cheap pure-compute → daily; data that changes
slowly or fetches that cost/credential → weekly/monthly. (One-time `fireAt` jobs are out of
scope — this reconciler manages recurring crons only.)

## Runbook resolution (job name → runbook)

A schedule job name maps to a runbook. Default: `connectors/<name>/SKILL.md`. These resolve
differently (config keys are functional; some connectors use a composite entrypoint, not
`SKILL.md`):

| Job | Runbook |
|---|---|
| `email` | `connectors/email/morning_full_scan.md` |
| `news` | `connectors/news/morning_full_scan.md` |
| `tg` | `connectors/tg/sync.md` |
| `practice_management` | `connectors/finkoper/` (the Finkoper snapshot) |
| `documents`, `whatsapp`, `max`, `resolution_sweep`, the monitors, `counterparty_status` | `connectors/<name>/SKILL.md` |
| `dashboards` | `engine/generate.py` (not a connector) |

On-demand connectors with functional config keys (NOT scheduled — resolved when invoked):
`registry` → `connectors/egrul`, `stats_portal` → `connectors/websbor`, `bank` →
`connectors/{tbank,alfabank}`. Use the same mapping for the coverage check (don't flag these as
unscheduled).

## The scheduled prompt (thin loader, self-contained)

Each run starts fresh with no memory, so the prompt must stand alone — but it stays thin by
**pointing at the runbook** (resolved above) rather than duplicating it:

```
# [saldo-managed: <instance.id>]
You are the Saldo runtime for this practice (data dir: <data.dir>).
Run the "<name>" daemon exactly per its runbook (see "Runbook resolution") against this instance.
Follow policies/INSTRUCTIONS.md (resolve each client's jurisdiction first, §0) and
policies/safety-rules.md (reads need no approval; outbound/irreversible stay gated;
close only answered open questions). Write a heartbeat to
journal/inbox/<name>_heartbeat.txt at the end.
```

No secrets in the prompt (it is stored as plaintext under `Scheduled/<taskId>/SKILL.md`).

## Pipeline ordering & readiness (effective scheduling)

The schedule encodes a **dependency chain** by clock — collectors (06:00–06:30) →
`resolution_sweep` (07:00, residue) → monitors (07:30–07:36) → `dashboards` (07:45). But Cowork
tasks fire by cron **independently**, and a run missed while the app was closed **replays on next
launch** — so a job can start before its upstream finished, or out of order. **Do not make
correctness depend on the exact wall-clock.**

Each downstream job does a **readiness check** before its real work: confirm today's upstream
heartbeats exist (`journal/inbox/<type>_heartbeat.txt` / per-account watermarks). On a missing/stale
upstream, **degrade gracefully, don't block** (matches the collectors' own "fail → empty panel,
never a broken render"):
- `resolution_sweep` — run on the state it has, but **flag** «запущен до сбора <collector> —
  остаток может быть неполным»; the residue rule still holds (it only touches still-open questions).
- monitors — derive from current state, note any staleness.
- `dashboards` — **always render** (the unconditional-render rule); it's last and must refresh the
  date daily regardless.

**Buffers.** ~30 min between tiers absorbs normal LLM-run durations; collectors are spaced ~5 min
and may overlap — safe, because every state write is atomic via `state_ops`. If a tier routinely
overruns, **widen its buffer**, never tighten — and never let `dashboards` precede the monitors.

**Ordering invariant** the reconcile preserves: *collect → resolve residue → derive → render.* If
an operator edits times so a downstream job would precede its upstream, **warn** (like the
timezone hard-stop) rather than silently registering a broken order.

## Health view — "are my daemons running?"

After reconcile, for each Saldo-owned job report: `enabled`, `nextRunAt`, `lastRunAt`, and the
**heartbeat freshness** (`journal/inbox/<name>_heartbeat.txt` vs. its expected cadence). Flag a
job that is registered but **stale** (no heartbeat within ~1 cycle) — that is the signal a
daemon silently stopped. Surface it to the operator; do not auto-"fix" by re-running.

## Timezone — a hard stop, not a warning

Cron is evaluated in the **machine's local timezone**. Derive crons from `HH:MM` directly.
**Before creating or updating any job, verify the machine's local tz equals
`instance.timezone`.** If they differ, **STOP — register/update nothing** and surface it: the
daemons would fire at the wrong wall-clock time, silently. Resolve first (fix
`instance.timezone`, or the machine clock), then re-run. Do not guess an offset, and do not
proceed with a warning. (Real example: the practice config read `Europe/Moscow`/`Europe/Lisbon`
while the operators are in Bali — `Asia/Makassar`, UTC+8; a 3–8 h drift on every job.)

## Coverage check — catch daemons that should run but aren't declared

The reconcile only creates what `schedule` declares — so a collector missing from `schedule`
silently never runs. After building `D`, cross-check it against the **enabled connectors**
(`config → connectors.*`) and report the gap so it surfaces instead of hiding:

- **Enabled + has a scheduled collector + not in `schedule`** → flag **"unscheduled — should it run?"** (this is exactly how a missing `telegram` job is caught).
- **On-demand by design** → list as such, do not flag: `ofd` (month-end close), `bank`/`tbank`/`alfabank` (direct circuit, on the operator's trigger).
- **Inline, not a job** → `mm_update` runs inside each collection pass; the standalone `mm-update-3x-daily` was deliberately disabled. Never schedule it.
- **Naming:** `practice_management` *is* the Finkoper tasks+chats snapshot — there is no separate `finkoper` job; don't double-create.

The coverage report is advisory (it does not auto-add jobs) — the operator decides what to add to `schedule`, then re-runs the reconcile.

> **Monitors are schedule-only.** A monitor (`deadline_monitor`, future `staleness_monitor`)
> derives from state and has **no `connectors.*` entry** — that is expected, not a coverage gap.
> The check flags *connectors without a schedule entry*, never *schedule entries without a
> connector*, so monitors are never false-flagged.

## Where this runs

- **On demand:** the operator says "проверь/настрой расписание демонов / set up the daemons /
  what's scheduled?" → run the reconcile (dry-run), show the plan, apply on approval.
- **After an upgrade:** part of the standard flow — pull the engine → `migrate.py up --apply`
  (data) → **run `scheduler` (jobs)** → `state_lint`. This is how a new/changed daemon (like
  `resolution_sweep`) actually lands on the operator's machine.
- **Optional periodic self-check:** a low-frequency `saldo-scheduler` job can re-reconcile
  weekly to catch drift; it reports, it does not silently re-create removed jobs.

## Deployment / migration

Manages **jobs, not data schema** → ships as engine files, no data migration. It is the
job-layer analogue of `migrate.py`: declarative target in config, idempotent reconcile, dry-run
default, approval to apply. (Cross-platform note: on Cowork the mechanism is the
`scheduled-tasks` tools; a Windows Task Scheduler / cron backend per `docs/DEPLOY-WINDOWS.md`
would consume the same `D` — out of scope for v1.)

## Related

- `config/instance.yaml → schedule` / `connectors.*` — the desired-state this skill reads.
- `connectors/resolution_sweep/SKILL.md`, the collectors (`news`/`email`/`practice_management`/`dashboards`) — the jobs it manages (`resolution_sweep` folds in the `question_resolver` open-question rung logic).
- `policies/safety-rules.md §5a` — approval model; `policies/INSTRUCTIONS.md` scheduling section.
- `migrations/README.md` — the data-layer analogue (same dry-run/idempotent discipline).
- `tests/runtime_scenarios/` — S6 is the gate for this behaviour.
