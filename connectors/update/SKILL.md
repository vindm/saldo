# Update procedure — check for a new engine version, migrate, rebuild, report

**Who runs this:** the runtime (Cowork / Claude) in a session with the operator
(Mom). She triggers it by saying *«проверь обновления Saldo»* / *«обнови
систему Saldo»* / *«check for saldo updates»*, or by clicking **«Обновить
Saldo»** / the gold **«Доступно обновление»** item in the dashboard (both copy a
trigger prompt). Not a developer flow — Dima updates the engine with normal git;
the operator only ever pulls + runs.

The whole cycle — **check → snapshot → pull → migrate → reconcile-schedule →
actualize-state (sweep) → rebuild → verify → report** — is driven here, end to
end, from that one phrase. Pulling a new version, running its migrations AND
bringing the situation current are all the **runtime's** job on her machine — the
operator never touches a terminal, never registers a daemon, never runs a sweep. The operator never
touches a terminal.

> **Trigger prompt** the dashboard buttons copy (kept in sync with
> `engine/_updater.py → UPDATE_PROMPT_RU`):
>
> *«Проверь обновления Saldo по workflow connectors/update/SKILL.md. Если есть
> новая версия — сделай резервную копию, скачай её, покажи мне, что именно
> изменится (новые версии, миграции данных), и ТОЛЬКО после моего «да» применяй
> обновление и миграции, пересобери дашборд, проверь, что всё работает, и
> отчитайся. Если миграция требует пошагового применения — веди её по одной.»*

## Context

The "is there a new version" check is also **inline in the engine** —
`generate.py` does a `git fetch` + rev-list at render time (`engine/_updater.py`)
and shows the gold «Доступно обновление» item only when origin is ahead. This
file is the **full operator-driven cycle**, including the guarded, pause-for-OK
apply.

Two apply paths, chosen by what the pull brings:

- **Pure-schema migrations** (the common case) — applied automatically by
  `tools/update.py` / `migrate.py up --apply`, no per-migration pause.
- **Runtime-work migrations** (a migration declaring `preflight` / `RUNTIME_PASS`
  / `SCENARIO`) — `migrate.py up` **refuses** these (exit code 2). They must be
  applied **one at a time** via `connectors/migration_runtime/SKILL.md`, so the
  prework, the deterministic script, the judgment rewrite and the verification
  stay in order. This file hands off to that loop.

Paths:

```bash
REPO="…/saldo"
DATA_DIR="$(cd "$REPO/engine" && python3 -c 'from _config import DATA_DIR; print(DATA_DIR)')"
```

## Steps (pause-for-OK)

Steps 0–4 are read-only / backup-only and may run without asking. **Do NOT
apply (step 6) until the operator has said «да»** to the step-5 preview.

0. **Check first — is there anything to do?** A new version is available iff
   origin is ahead of HEAD:

   ```bash
   cd "$REPO" && git fetch --quiet && \
     echo "behind=$(git rev-list --count HEAD..@{u} 2>/dev/null || echo 0)"
   ```

   `behind=0` → tell the operator she is already up to date and **stop**. No
   snapshot, no pull. Otherwise note what the new version brings (the headline
   already shown on the update page) and continue.

1. **Snapshot first** (restoreable rollback point):

   ```bash
   python3 engine/snapshot.py pre-update
   ```

2. **Pull the new engine only** — no migrate, no rebuild yet, so we can inspect
   the migrations the pull brought BEFORE touching her data:

   ```bash
   python3 tools/update.py --no-migrate --no-generate --no-open --no-pause
   ```

3. **See what is pending** against her data (read-only — writes nothing):

   ```bash
   python3 engine/migrate.py status --data-dir "$DATA_DIR"
   python3 engine/migrate.py next   --json --data-dir "$DATA_DIR"
   ```

   `next --json` tells you, for the next migration, its `description`, read-only
   `preflight` findings, and whether it has a `runtime_pass` / `scenario`. Walk
   it (re-run after each is verified) to see the whole pending set.

4. **Dry-run the deterministic part** to preview exact changes (still writes
   nothing; a runtime-work migration will print a STOP pointing at the stepwise
   flow — that is expected):

   ```bash
   python3 engine/migrate.py up --data-dir "$DATA_DIR"
   ```

5. **PAUSE — show the operator, in her locale, exactly what will change** and
   wait: the new version, each pending migration and what it does to her data,
   any prose a `RUNTIME_PASS` proposes to rewrite, and that a backup exists. Ask
   plainly, e.g. *«Готов применить. Изменится: … . Применяю? (да / нет)»*. **If
   she does not say «да», stop — nothing changed.** This is the **one**
   approval: after «да» the migrations apply on their own and come back to
   her only if a migration breaches its expectations or a check fails (see
   the stepwise path below).

6. **Apply (only after «да»).** Pick the path:

   - **No runtime-work migration pending** → apply the batch and rebuild:

     ```bash
     python3 engine/migrate.py up --apply --data-dir "$DATA_DIR"
     python3 engine/generate.py
     ```

   - **A runtime-work migration is pending** (step 3 showed a `runtime_pass` /
     `scenario`, or step 4 / `up --apply` exits 2) → **drive
     `connectors/migration_runtime/SKILL.md`**, which applies each migration
     **autonomously**: read → `apply <id> --apply` → `RUNTIME_PASS` rewrites
     within guardrails via `state_ops` → role-play `SCENARIO` → `record <id>
     --rung verified`. It **escalates back to the operator only on a surprise**
     — an anomaly (`next --json` says `autonomous:false`), a guardrail breach,
     or a scenario fail — not on every migration. When `migrate.py next`
     reports done, regenerate:

     ```bash
     python3 engine/generate.py
     ```

6a. **Reconcile the schedule — register any newly-shipped daemon.** A pull can
   add, rename, or retire jobs in `config/instance.example.yaml → schedule` (e.g.
   add `resolution_sweep`; retire `question_resolver`, now folded into it). Carry the
   new/changed/removed entries into her
   `config/instance.yaml → schedule` (her config is her own — the pull does not
   overwrite it), then drive `connectors/scheduler/SKILL.md` so the desired set
   is reconciled to real OS tasks — idempotent, Saldo-owned `saldo-*` only,
   never touching her personal tasks, with its own approval gate. **This is how
   a daemon shipped by the engine actually starts running on her machine — the
   runtime does it, not the operator.**

6b. **Actualize state — run the sweep once.** A migration reshapes *fields*; the
   situation still has to be brought current. Drive
   `connectors/resolution_sweep/SKILL.md` over all active tasks: recompute each
   task's edge (`policies/resolution-model.md`), **advance the reversible**
   (acquire/derive, answer open questions whose source is now reachable, fix
   stale `status`), **surface `needs_operator`**, leave `wait_external`. Closes/
   sends stay gated. This is the actualization pass — without it the upgrade only
   migrated bytes; with it the runtime reasons over current state again
   (CLAUDE.md Invariant 0 / the behavioural-change rule). It runs **now**, as part
   of the upgrade — not «later, over the next nightly», which is the deferral
   anti-pattern. (The scheduled 07:40 job from 6a then keeps it current daily.)

7. **Verify** (green exit is necessary but not sufficient — CLAUDE.md Invariant 0):

   ```bash
   python3 engine/state_lint.py              # expect LINT OK
   python3 engine/system_integrity_check.py  # expect ALL CLEAN
   ```

   Then **scenario-verify**: pick a representative client and confirm the runtime
   still reasons correctly after the migration (resolves the right jurisdiction
   pack, right rules, no stale artefacts). For a non-RU client, role-play one of
   `tests/runtime_scenarios/`.

8. **Report back in the operator's locale**, short and plain: the version she is
   on now, what changed for her, **what the actualization sweep advanced and what
   now needs her** (the «Требуют вас» queue), that a backup was made, and that the
   dashboard is rebuilt. Tell her to **refresh the dashboard tab** — that is the
   "relaunch" equivalent, nothing to restart. (The Claude desktop app's own
   "Relaunch to update" button, if lit, is Anthropic's app updater — separate
   from Saldo.)

## The Windows one-click icon

`tools/windows/update_saldo.bat` → `tools/update.py` runs the SAME cycle fully
automatic for the **pure-schema** case. When the pull brings a **runtime-work**
migration, `update.py` stops at the migrate step (exit 2) and tells the operator
to open Saldo and say *«обнови Saldo»* — i.e. it hands the per-migration judgment
+ approval to this runtime flow rather than applying it unattended.

## Rollback

```bash
python3 engine/snapshot.py --list
python3 engine/snapshot.py --restore <pre-update-snapshot>   # try --dry-run first
```

Migrations are idempotent and every state write is backed up by `state_ops`, so
re-running is safe; the snapshot is the belt-and-braces restore point.
