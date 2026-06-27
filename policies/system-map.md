# SYSTEM MAP — how it is built and what to update when new information arrives

> Authoritative reference. Read at the start of EVERY task (CLAUDE.md). Goal: a clear understanding of where each file lives, who is the source of truth, and what to update when a new fact arrives. If reality has diverged from this file — fix the file first.

## 1. Data flow (one rule)

```
FACT → state/*.json (edited by hand, source of truth)
         → mental_model.md (narrative: Plan/Links/History — edited by hand)
         → history.jsonl (append-only log)
         → generate.py → dashboard + Card (DERIVED, not edited by hand)
         → state_lint (proves the links are reconciled)
         → snapshot (rollback point)
```

**A hard fact lives in exactly ONE file (the relevant `state/*.json`). Everything else references it or is generated.** This is precisely why "update all the files" should not be heavy: by hand we touch only the fact-owner file + the related tracks/risks; the dashboard and the card rebuild themselves.

## 2. File registry

### Client `state/` — SOURCE OF TRUTH (8 core + 1 optional), one per client
| File | Owns (what goes here) |
|---|---|
| `identity.json` | INN, OGRNIP, full name, address, tax office, OKVED activity codes, contacts, tax residency |
| `regime.json` | **jurisdiction** (pack code, default `ru`), tax regime + object/rate (regime enums are **pack-scoped** — RU: USN/AUSN/OSNO/PSN, see `jurisdictions/<code>/regimes.yaml`), patents[], signature, filing, accounting_system |
| `accounts.json` | bank_accounts[], foreign_accounts[], kassas[] (cash registers), acquiring_channels[], bank_access, kkt_mode, **quick_access[]** (access registry: links/logins/passwords/identifiers for the client's services) |
| `financials.json` | turnover/income by period, taxes, tax_calendar, personal_taxes |
| `counterparties.json` | counterparties (b2b/b2c/self-employed/agents), INN, income shares, contracts |
| `risks.json` | risks[] (severity green/yellow/red; **kind: risk/question/blocker** — only kind=risk is shown as cards, questions/blockers roll up into the footer since they duplicate tracks) + resolved_risks[] |
| `behavior.json` | client style, communication channels, frequencies (e.g. bank statements) |
| `tasks.json` | tracks: tasks, waiting items, open_question[] (resolves_when/no_auto_resolve) + `assist{}` on each track (hypothesis + personalized actions from mm_update) |
| `real_estate.json` | real-estate objects + contracts + mortgage (optional; so far only the client) |

### Other files in a client folder
| File | Role |
|---|---|
| `mental_model.md` | human-facing narrative (Plan + Links + History) + an `## Analysis and recommendations` block (fenced ```` ```analysis ```` JSON — rendered on the dashboard, guarded by lint `analysis_missing`/`analysis_stale`) — edited by hand / mm_update |
| `history.jsonl` | append-only log of state changes (`state_ops.history_append`) |
| `Client_card.md` | DEPRECATED (dead). Not a view (the view is the dashboard), not a backup (the backup is `snapshot.py` snapshots). Do not read, edit, or generate. |
| `history.md` | legacy, not used |

### `engine/` — the engine

Reusable Python, no client-specific knowledge. Data dir + dashboard dir come from config (`_config.py`: `DATA_DIR`/`DASHBOARD_DIR`/`LOCALE` from `config/instance.yaml` + `ABA_*` env). `generate.py` writes finished HTML **directly into `DASHBOARD_DIR`** (no `_tmp_html` staging / `cp` publish step — that was the legacy mount workaround).

| Script | Role |
|---|---|
| `_config.py` | resolves `DATA_DIR`, `DASHBOARD_DIR`, `LOCALE`, `BRAND` from `instance.yaml` + env. The practice-agnostic boundary. |
| `state_ops.py` | atomic state write (backup + UTF-8) + `history_append` + roster |
| `_loaders.py` | pure `json.load` of per-client state + optional daemon JSON (`journal/inbox/*.json`); no Markdown/xlsx parsing |
| `_aggregator.py` | `aggregate_tasks()` — collects active tracks from every `state/tasks.json` (Source of truth) + optional daemon signals into the plan model. **Excludes `open_question`** (those go to the Dashboard questions block). |
| `_plan_waves.py` | the Plan renderer: `cluster_tasks` (group ≥2 tasks by `(_op_canonical, group)` — **operation, not client count**), `_op_canonical` (stage-first, period-explicit), `render_waves_flat` (Operations / Individual / collapsed "Waiting" lane, urgency-coloured). |
| `_pipeline.py` + `jurisdictions/<j>/cycles/*.yaml` | the declared recurring **cycles** (RU: monthly_close primary + payroll / tax_quarterly / ausn; legacy single `pipeline.yaml` auto-wrapped); `cycles()` lists them, `locate_stage(task_type)` maps a type to its `(cycle, stage)` across all cycles. |
| `_plan_today.py` | the **Plan** page (`render_plan_today`) + `render_client_plan` (same renderer scoped to one client → the client card). |
| `_plan_month.py` | the navigable **Calendar** (`render_calendar`). |
| `_periods.py` | the **Periods** view — one band per recurring **cycle**, each reporting period × its stages as a progress stepper, counted by **task**; stage chips jump to the Plan. |
| `_brief.py` | Dashboard "Brief" + the single expandable **"Open questions"** block (2 by priority + daily rotation, rest grouped by client). A pure lens over state. |
| `_overview_v2.py` / `_client_dashboard_v2.py` | overview + per-client card renderers. |
| `_strings.py` / `_vocab.py` | locale layer — UI strings (`t()`) and data-value tokens, driven by `instance.locale` (ru/en). |
| `_sidebar.py` | left menu — Dashboard · Plan · Calendar · Periods · Clients (one item per group, dynamic) · How to use. |
| `_guide.py` | the in-app **How to use** page (`guide.html`). |
| `state_lint.py` | state invariants (an error blocks publishing; warn/info = a signal) |
| `system_integrity_check.py` | read-only "doc vs reality" guard: roster vs `state/`, NUL/JSON/UTF-8, orphan modules, broken pointers. Exit != 0 on ERROR. |
| `snapshot.py` | tar snapshot of the data ("brain") for rollback |
| `_waker.py` | auto-wakes deferred tracks (`status=deferred` + `wake_date<=today`) before render |
| `safe_edit.py` | safe editing of Cyrillic files (instead of the Edit/Write tool) |

> **Group, not track.** Client grouping is dynamic: each client carries a `group` field; sidebar items and group dashboards are derived from the distinct values (no hardcoded team/direct).

### `policies/`
INSTRUCTIONS.md (process, 8 steps) · safety-rules.md (boundaries + §5b chain) · skill-evolution.md (self-improving skills: mechanics evolve via per-provider connectors/<x>/ui_playbook.md, safety doesn't) · system-map.md (this file) · workflows/<domain>/ (finkoper, email, news[multi-jurisdiction], tg, ofd, tbank, alfabank, egrul, websbor, mm_update, documents[doc collector: GDrive+Yandex.Disk+local inbox, incremental], whatsapp + max[single-account chat collectors, by_chat — shared base connectors/_chat_collector.md, alongside tg], question_resolver[open-question rung logic — run within resolution_sweep, not a separate scheduled job], resolution_sweep[the one scheduled actualization daemon: edge re-check over all active tasks, incl. open questions], deadline_monitor[MONITOR: approaching/overdue deadlines from state], staleness_monitor[MONITOR: missing-data & reconciliation, successor to analytic R-rules], threshold_monitor[MONITOR weekly: turnover limits + facility expiry], counterparty_status[collector+monitor monthly: registry re-check of counterparties], scheduler[reconciles Saldo daemons to config schedule], one_c[paused]) · coverage map: docs/COVERAGE-MAP.md · multi-account fan-out: connectors/_sources.md · jurisdictions/<code>/checklists/ · templates/ · brand-and-tone.md (style of client documents) · secrets/ (NOT in git/snapshots)

### `journal/`
operator_decisions.md (**append-only audit narrative** of "what/why/when"; NOT a source of truth — dismissed items live in `state/risks.json:dismissed[]`, facts in `state/*.json`; markdown parsing of dismissed items retired 2026-06-07) · inbox/ (collector-daemon reports: finkoper/email/news/tg by date)

### `brand_kit/` (corporate style)
`Letterhead_template.docx` (the letterhead for all client documents) · `Brand_guide.docx` · `Logos/` (monogram + horizontal, color/white) · `_generator/brand_kit.js` (docx-js module). Application rules — `policies/brand-and-tone.md`. Apply to ALL client documents and messages.

## 3. MAP "new info → what to update"

Columns: **Owner** (you edit by hand) · **Links** (check/close) · **Guard** (lint code). At the end of every row: `mental_model.md` + `history.jsonl` + `generate.py`+publish + lint(exit 0) + snapshot.

| New info | Owner (state) | Links to check/close | Lint guard |
|---|---|---|---|
| **New/changed account** | `accounts.json:bank_accounts[]` | close the `Q-*` track about the account in tasks; risks: AUSN-single-bank; counterparties if the account is tied to acquiring | primary, acct_fmt, bik_fmt, dup_acct, ausn_one_bank, tbank_bik |
| **Registration details** (INN/OGRNIP/address/tax office/OKVED) | `identity.json` | tasks: Q about the detail; reconcile with the company registry (EGRIP) | inn_csum, ogrnip, inn |
| **Regime change / patent** | `regime.json` (primary/patents/**jurisdiction**) | tasks: Q about regime/patent; risks; financials.tax_calendar | regime invariants are **pack-scoped** (`jurisdictions/<code>/lint.yaml` — RU: usn_rate, ausn_rate, ausn_partner, account_format) |
| **Counterparty / INN / shares** | `counterparties.json` | tasks: Q-cp-inns; risks (schemes) | cp_inn_csum, cp_inn(cross) |
| **Cash register/OFD/acquiring** | `accounts.json:kassas/acquiring_channels` + `kkt_mode` | tasks: Q-kkt; risks (cash / Federal Law 54-FZ) | — |
| **Access/link to a client service** (Finkoper, bank portal, FTS portal, 1C base, payment provider, OFD) | `accounts.json:quick_access[]` | sync with acquiring_channels.url / regime.fresh_base_url; render on the card = the "Quick access" section; pull it in work via `_loaders.get_access(client_id, service)` | — |
| **Income/turnover/tax for a period** | `financials.json` | tasks: month_close/ausn_*; risks | — |
| **Risk arose/resolved** | `risks.json` (risks[] ↔ resolved_risks[]) | tasks: linked_tasks | risk_sev, risk_link |
| **Real estate/rental** | `real_estate.json` | risks (formula/mortgage); counterparties (tenant) | — |
| **Behavior/channels** | `behavior.json` | tasks (e.g. statement frequency) | — |
| **Answer to an open question** | the relevant state file | **close the Q in tasks (status=completed + completed_at + history)** — `resolves_when` will highlight it if you forget | orphan_q |
| **New track/task** | `tasks.json` | blocked_by on existing items; for a question — `resolves_when` or `no_auto_resolve` | dup_id, blocked_ref, no_resolves_when |
| **Client leaving/status change** | identity/regime/behavior + tasks | risks; all active tracks | — |
| **News/law** (system-wide) | by affected: regime/financials/risks/tasks | go through ALL clients (`CLIENT_FOLDERS`) | lu_future |

## 4. The "apply a fact" pipeline (mandatory)

1. **Write** to the fact-owner file via `state_ops.state_write` (Cyrillic — NOT via the Edit/Write tool, only bash/python, CLAUDE.md RULE #1).
2. **Reconcile links** per the table in §3 — close Q-tracks, re-evaluate risks, fill in the ❓ markers in adjacent files (CLAUDE.md RULE #2, rules §5b Step 1.5).
3. **For a new question** — set `resolves_when` (the path where the answer will appear) or `no_auto_resolve` (if the answer is external/narrative).
4. **mental_model.md** (✅ into History) + **history.jsonl** (append).
5. **`python3 engine/generate.py`** → writes the dashboards directly into `DASHBOARD_DIR` (from config) and runs lint at the end. On a lint error, fix before relying on the output. (For a dry run point `ABA_DATA_DIR`/`ABA_DASHBOARD_DIR`/`ABA_LOCALE` at a copy.)
6. **Self-check:** `python3 engine/state_lint.py <client>` + grep for residual active `open_question`/`❓` on the topic.
7. **Snapshot** for substantial edits: `python3 engine/snapshot.py <label>`.

## 5. Plan model & task taxonomy (what the engine does with tasks)

The Plan is **actions only**. `aggregate_tasks` (`_aggregator.py`) collects active tracks from each client's `state/tasks.json`; `render_waves_flat` (`_plan_waves.py`) renders them. Classification:

| `task_type` | Where it shows | Why |
|---|---|---|
| `open_question` | Dashboard "Open questions" block (`_brief.py`) — **not** the Plan | a clarification, not an action |
| `monitoring`, or `awaiting_external` with **no due date** | Plan → collapsed **"Waiting"** lane (bottom) | passive — nothing to do but wait; a `monitoring` item is also a risk on the card |
| everything else with an action (incl. dated `awaiting_external` — sign PO, payment control, first-docs) | Plan → **Operations** (batchable) / **Individual** | real work |

**Grouping = by operation, not by client count / source / wording / group.** An operation (wave) = ≥2 tasks sharing `(operation, reporting period)` across all clients (Team/Direct is a filter, not a batching axis — member rows carry their group so the toggle filters within a wave). `_op_canonical` resolves **stage-first**: a pipeline `task_type` → `stage:<code>|<period>` (period-explicit). Source-flavoured types (e.g. `finkoper_recurring`) are treated as generic so they re-infer by topic. Keyword inference is a **legacy bridge** — the durable fix is a precise `task_type` in `state` (JSON-first). Recommended semantic types to keep data clean: `service_payment` (client pays us), the pipeline stage types, `acquiring`, plus a `type_specific.period: "YYYY-MM"` whenever the reporting period differs from the due month.

The declared recurring **cycles** live in `jurisdictions/<j>/cycles/*.yaml` (`_pipeline.py`; a legacy single `pipeline.yaml` is auto-wrapped as one `monthly_close` cycle). RU has four: the **primary** monthly close (collect source docs → post to 1C → month close → month audit → calc+notice+payment order → sign/pay) plus **payroll**, **tax_quarterly** (УСН/ЕНС), and **ausn_monthly** (AUSN runs its own shape — bank-side marking → calc+pay — so `ausn_monthly` is NOT in the monthly-close `tax_pp`). Stage codes are globally unique, so `locate_stage` maps each `task_type` to exactly one `(cycle, stage)`. The **Periods** view renders one band per cycle × period × stage, counted by **task** (not by client).
