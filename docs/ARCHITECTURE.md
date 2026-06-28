# Architecture

## Principle: memory hierarchy, code stays thin

The assistant follows a Karpathy-style memory hierarchy. The AI agent decides *what* to update from any signal; the code only does atomic, validated reads and writes. There is no business logic hardcoding "if email X then change field Y" — that judgement lives in the agent, working against the artifacts below.

For each client:

- **`state/*.json`** — the source of truth. Structured, machine-readable facts split across files:
  `identity` (requisites, registration, address, tax-office, activity codes, contacts),
  `regime` (tax regime, patents, filing method, signature),
  `accounts` (bank accounts, cash registers, quick-access links),
  `financials` (periods, taxes, tax calendar, yearly pace),
  `counterparties`, `risks`, `behavior` (channels, tone, notes), and `tasks`.
- **`mental_model.md`** — a human-readable narrative slice (plan, links, history) for fast context.
- **`history.jsonl`** — append-only log of every state change; never rewritten.

`engine/state_ops.py` exposes five primitives — `state_read`, `state_write`, `mental_model_read/write`, `history_append` — each with backup, atomic temp-file rename, and UTF-8 validation.

## Engine

`engine/` is reusable Python with no client-specific knowledge:

- **`generate.py`** — orchestrates dashboard generation. Reads the roster from the configured `clients_index.json`, enriches each client from its `state/*.json` via `_loaders.py`, and renders an overview plus one dashboard per client. Fault-tolerant by design: a missing collector file or malformed source renders an empty container, not a traceback, and surfaces a status dot on the overview.
- **Render budget & scoped rebuild.** The runtime renders inside a sandbox that kills any single command at ~45s, and a backgrounded process does **not** survive the command boundary — so a full serial `generate.py` over all clients overruns it and is killed mid-render (the 2026-06-11→13 frozen-date class of failure, now via timeout). Two mechanisms keep every render in budget: `generate.py` renders the per-client pages **in parallel** across processes (`ABA_GEN_SERIAL=1` forces serial; native Windows has no fork → serial, and no cap there anyway), and it accepts **scoped** flags — `--clients=id1,id2,…` (only those client pages) and `--aggregates` (only the shared service pages + finalize + LINT). Client pages are **isolated** (each derives from its own `state/*.json` only), so a state change re-renders the **affected client(s) + all service pages** and leaves the untouched clients alone — output is byte-identical to a full run. Daemons never run a bare full `generate.py`; they scoped-render per `connectors/_rebuild.md`. The **single** full render on a timer is the `dashboards` job (07:45) — the relocated home of the unconditional daily date-refresh guard.
- **Renderers** (`_overview_v2.py`, `_client_dashboard_v2.py`, `_plan_*.py`, `_tracks.py`, `_analytics_widgets.py`, …) build the HTML views.
- **Loaders** (`_loaders.py`) parse the morning collectors' output and the per-client state into the render model.
- **Integrity** (`state_lint.py`, `system_integrity_check.py`) check cross-link integrity — e.g. a fact filled in one file must close its related track in `tasks.json`, or it's flagged as a "dangling" item.
- **Source channels** (`_helpers._CANON_CHANNELS` + `_channels.py`) — every history/task `source` carries a closed-vocabulary channel: a **connector** (the ingest integration), the **operator** (`cowork`), or the **system** (a daemon / `migration`). The connector set DERIVES from `config/instance.yaml → connectors` (`_config.CONNECTOR_CHANNELS` — the same declaration the scheduler reconciles daemons against), so enabling a connector auto-registers its channel. `_channels.channels_in_use()` / `reconcile_channels()` report which channels the current clients actually use vs the declared connectors — feeding the dashboard «Каналы и сборщики» panel, the scheduler's relevance filter, and onboarding's channel-coverage check. Rule + the three-bucket model: `policies/event-sources.md`.

## Connectors

`connectors/` holds the pluggable integrations, each behind a common interface (see [`CONNECTORS.md`](CONNECTORS.md)). They split into:

- **Atomic skills** — one operation (`read_task`, `list_messages`, `get_statement`, `check_z_report`, …).
- **Composite pipelines** — `morning_full_scan` / `incremental_update` chain atomic skills for a full sweep.

The architectural rule is *one skill, many executors*: the operator invokes an atomic skill for a pointed need, or a composite for a full sweep; a scheduler invokes the composite on a timer. Enabling/disabling a connector is a config flag.

## Configuration boundary (the product change)

> **Self-describing instances.** Locale and brand can travel WITH the data: an
> `instance.yaml` at the root of the data dir (`DATA_DIR/instance.yaml`) overrides
> the repo `config/instance.yaml` for `instance.locale` and `brand.*` (env still
> wins). This keeps a practice's identity attached to its data, so a snapshot
> cannot be rendered under the wrong locale by accident (see Invariant 4 in
> `CLAUDE.md`).


The original system hardcoded the client→folder map and resolved data paths relative to the code. The product moves both into configuration:

- `config/instance.yaml` declares locale, brand, enabled connectors, schedule, and **`data.dir`** — the path to the practice's data directory.
- The roster (`clients_index.json`) already carries each client's `folder`; `state_ops` resolves `data.dir / folder / state` instead of a baked-in map.

Result: the engine is practice-agnostic. A real practice keeps its data dir private and outside the repo; the bundled `instances/example` ships synthetic data so the engine runs out of the box.

## Plan model & task taxonomy

The Plan is built by `_aggregator.aggregate_tasks()` (which collects active tracks from every client's `state/tasks.json`, plus optional daemon signals) and rendered by `_plan_waves.render_waves_flat()`. The design rules:

- **The Plan contains actions only.** Non-actions are routed away so the action list stays scannable:
  - `task_type == "open_question"` → excluded from the Plan; shown on the Dashboard "Open questions" block (`_brief.py`), where 2 surface by priority + a daily rotation and the rest expand grouped by client.
  - `task_type == "monitoring"` (a risk-watch) or `awaiting_external` **with no due date** ("nothing to do but wait") → a de-emphasised collapsed **"Waiting"** lane at the bottom of the Plan. (Dated awaits with a chase action — sign a payment order, payment control, first-docs — stay as tasks.)
  - Risks live in `state/risks.json` and render on the client card.
- **Grouping is by semantic operation, not by client count, source, or wording.** An *operation* (a "wave") groups ≥2 tasks that share `(operation, reporting period)` across **all** clients — regardless of how many, and regardless of group. Client group (Team/Direct) is a *filter* (the toggle), not a batching axis: splitting one batch of identical work by group just fragments it. A wave's member rows still carry their group, so the toggle filters within a wave. The operation key (`_op_canonical`) is derived **stage-first**: a task's `task_type` that belongs to a pipeline stage collapses into `stage:<code>|<period>` (period-explicit, so "close April" and "close May" are distinct, batchable waves). Off-pipeline types fall through to a canonical type, then to keyword inference, then to a text key. Source-flavoured types (e.g. `finkoper_recurring` — "where it came from") are treated as generic so they re-infer by topic (e.g. "acquiring"). Keyword inference is a **legacy bridge**; the right long-term fix is a precise `task_type` in the data (JSON-first).
- **Recurring cycles** are declared per jurisdiction in `jurisdictions/<j>/cycles/*.yaml` (`_pipeline.py`; a legacy single `pipeline.yaml` is auto-wrapped as one `monthly_close` cycle). RU has four: the primary **monthly close** (six ordered stages — collect source docs → post to 1C → month close → month audit → calc+notice+payment order → sign/pay) plus **payroll**, **quarterly tax / ЕНС**, and **AUSN**, each with its own cadence and stages. Stage `code`s are globally unique across cycles, so `_pipeline.locate_stage` maps a `task_type` to exactly one `(cycle, stage)`. The **Periods** view (`_periods.py`) renders one band per cycle (the primary one first and headerless), and within each band, per reporting period, how far each stage has progressed — counted by **task** (not by distinct client), matching the Plan's wave counts. Clicking a stage jumps to that operation on the Plan. The same deep-link contract is reused by two callers: a Plan wave carries `data-stage="<canonical op token>"`, Periods links to it via `plan_today.html#stage=<code>&period=<YYYY-MM>` and the **Calendar** (`_plan_month.render_calendar`) via `plan_today.html#wave=<canonical op token>`; the jump handlers in `_plan_waves.py` (`_STAGE_JUMP_JS` / `_WAVE_JUMP_JS`) expand + scroll + highlight the matching wave. So a Calendar wave chip (a recurring/batched op clustered **per day**) is a link to that operation on the Plan, not a single-track modal; only individual-task chips open the track modal in place.
- **One renderer, two scopes.** `render_waves_flat` drives both the practice-wide **Plan** page and each **client card** (scoped to one client via `render_client_plan`), so the card *is* that client's plan — same Operations / Individual / Waiting structure.

## Overview composition

The overview (`_overview_v2.render_overview_v2`) is a morning cockpit, top to bottom:

1. **Stats strip** — open / overdue / due-today / closed-today / streak. "Open" matches the Plan exactly (`aggregate_tasks(today)['all']`) and the number links to the Plan.
2. **Today summary** (`_brief.brief_lead_html`) — an honest one-paragraph brief (overdue → today → nearest deadline → awaiting-decision → open questions → red risks) with the **Top-5** focus list embedded as a sub-section. Prefers an agent-written `journal/brief_<date>.md` (composed by `mm_update` with full context); falls back to the deterministic summary.
3. **Open questions** (`_brief.py`) — each with the assistant's hypothesis + one-tap actions.
4. **System-event lists** — three uses of ONE shared component (`engine/_components.py`: `event_row` + `render_event_section`): **🔄 Recently updated** and **✅ Recently closed** tracks (clickable rows → the track modal; right column = status pill · relative date), and **📋 Latest decisions** (`kind=decision` facts from `history.jsonl`). The same component renders **📬 Mail** and **📰 News**.

Daemons keep tracks current inline (no approval) but never close them — a close is the operator's action from a track card (see the Safety model and `policies/safety-rules.md §5a`). Dashboards render into `<data.dir>/dashboards/`, so a practice folder is self-contained.

## Localization

`instance.locale` (`ru`/`en`) drives both the dashboard UI strings (`_strings.py`, via `t()`) and the data-value tokens the loaders match (`_vocab.py`). The English port was done as a deliberate i18n pass — UI text and data-token matching were separated — so Russian-language data keeps behaving identically while the chrome renders in either language. Any change to engine string handling must be checked against **Russian-data output**, not only the English demo, because locale-coupled parsing is easy to break silently.

## Multi-jurisdiction

Tax-system-specific behaviour lives in **jurisdiction packs** (`jurisdictions/<code>/`), not in the engine. A client binds to a pack via `state/regime.json → jurisdiction` (default `ru`). A pack declares the regimes, the recurring cycles (`cycles/*.yaml` — monthly close + payroll / quarterly tax / AUSN; or a legacy single `pipeline.yaml`), the tax authority / portal / currency / terminology, the regime-lint rules, and the per-task-type checklists. `engine/_jurisdiction.py` loads it (`load_jurisdiction(code)`; unknown code is a hard error, never a silent RF fallback), and the renderers (`_pipeline`, `_plan_waves`, `_periods`, `_client_dashboard_v2`) and `state_lint` read it instead of assuming RF. The runtime resolves and applies the pack per `policies/INSTRUCTIONS.md §0`. Adding a jurisdiction is pure data — see `jurisdictions/README.md`. Jurisdiction is **independent of locale**: locale drives the operator-facing UI language; jurisdiction drives tax content (a RU operator can serve an `id` client — RU dashboard, Indonesian filings).

## Safety model

Three product invariants, enforced as policy and surfaced in config:

1. Commands come only from the operator. Text inside tasks, emails, and documents is **data, never instructions** (prompt-injection resistance).
2. Recording incoming signals into state is the daemons' job and needs no approval (that is the point of the collectors). Explicit approval is required only for outbound/irreversible actions: anything sent to a client, any browser action, and closing a track — daemons update tracks and surface them but never close (see `policies/safety-rules.md §5a`).
3. A fixed deny-list for browser automation: no sending without confirmation, no e-signature, no ledger edits, no deletes, no external forwarding.
