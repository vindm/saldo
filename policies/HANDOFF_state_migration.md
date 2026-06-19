# HANDOFF — Migrating the remaining clients onto state/

> ## ✅ CLOSED 2026-05-25 — migration of all 14 clients completed
>
> All 14 clients + the pilot Client K2 are migrated (15 state/ directories). 15 backward-compatible schema extensions accumulated.
>
> **Current reference:** memory `state_migration_complete.md` + `state_architecture.md` + `state_schema_extensions.md`
>
> **Open post-migration tasks:** `tracks_render_state_disconnect.md` (P1 — render tracks on overview/plan_* for all 14 clients; it was P2 for the single pilot).
>
> The file is left below as **historical context** for what the migration plan was.
>
> ---

**Created:** 2026-05-25, at the end of a long pilot session for Client K2
**Closed:** 2026-05-25 ~21:00 — migration of all 14 COMPLETED in the same session as the pilot

---

## Context

The pilot SP Client K2 is fully migrated from the "3 sources of truth" architecture (card.md + clients_data.json + mental_model.md) onto the new one: **mental_model = narrative + 7 state/*.json**. The dashboard is rewritten, all components updated. Now the pilot needs to be rolled out to the remaining 14 clients, **allowing format extensions for their specifics**.

## What is done (do NOT redo)

### Architecture — pilot Client K2
```
Direct/SP Client K2/
├── mental_model.md          ~5 KB, narrative (Work plan + Links + History)
├── Client_card.md           untouched (fallback for rollback)
├── history.md               existing
├── state/
│   ├── tasks.json           11 rich tasks v2.0 (priority, blocked_by, comments, labels, type_specific)
│   ├── identity.json        registration details + OKVED codes + contacts
│   ├── regime.json          USN/PSN/AUSN + signature + filing + business_description
│   ├── accounts.json        bank_accounts[] + foreign_accounts[] + kassas[] + bank_access
│   ├── financials.json      periods[] + yearly_pace + tax_calendar
│   ├── counterparties.json  counterparties with relation_type/linked_open_questions
│   ├── risks.json           severity red/yellow + linked_tasks + linked_law (green = a positive, not a risk)
│   └── behavior.json        communication + style + preferences + channels
└── history.jsonl            append-only log
```

### Code (do NOT change without reason)
- **`engine/state_ops.py`** — 5 atomic primitives: state_read/write, mental_model_read/write, history_append. Backup + UTF-8 validation + atomic write.
- **`engine/_loaders.py`** — 8 loaders `load_client_state_<name>()` + 5 apply functions. Also `build_snapshot_firm_from_state(client_id)` — a render-view snapshot from state.
- **`engine/generate.py`** — the enrichment loop after `clients = json.load(f)` applies apply_identity/regime/accounts/financials/counterparties_to_client.
- **`engine/_client_dashboard_v2.py`** — render_client_dashboard_v2 with the section order:
  ```
  head (name + badge + tagline + actions)
  global_mic removed
  focus_band (⚡ What matters today)
  risks_html (⚠️ Client risks — no green, no resolved)
  tracks (🎯 Active tracks)
  req_card (📋 Registration details)
  accounts_html (🏦 Accounts and cash registers)
  financials_html (💰 Financial model and calendar)
  counterparties_html (🤝 Counterparties)
  behavior_html (🗣 Client style)
  history (📜 narrative)
  ```
- **`engine/_track_modal.py`** — a Linear-style modal with meta-chips, blocked_by with titles, deps, type_specific grid, labels, comments, history. Breadcrumb simplified: only `← <client_name>`.
- **`engine/_overview_v2.py`** — `render_tracks_zone`: rich-badges on a single line under the title (deadline + priority + blocked_by + comments). ROUTINE is not shown. `_tasks_title_cache` for blocked_by title lookup.
- **`engine/_css.py`** — DESIGN_TOKENS_CSS holds the unified design system: tm-btn-primary/success/warn/tg, rich-badge, focus-band, risk-cards, fin-table, cp-cards, beh-section, acc-section. font-size minimum 12px for accessibility.

### Principles (ADHERE TO)
- **Risk = a state/threat, Task = an action.** Linked via `linked_tasks`. Dedup in the focus-band: if risk.linked_tasks ⊆ focus_task_ids — the risk is hidden.
- **green-risk = a positive**, not shown in the "Risks" section (filtered in render).
- **Single helper button:** `render_action_buttons(kind, entity_id, entity_name, prompt_text, mic_*)` in `_client_dashboard_v2.py`. Use it everywhere. Design tm-btn-primary (blue "🔍 Dig in") + tm-btn-success (green "🎤 Dictate a thought").
- **On the client dashboard:** the track card does NOT show the client name (data-attr empty via `state_tasks_to_mm_format(state_data, client_name='')`). The modal takes the name from the h1 (fallback).
- **mental_model.md = a narrative slice.** Structured blocks removed, kept: Work plan + Links between sources + History of key decisions.
- **Snapshot — a view, not a store.** Never create `state/snapshot.json`. It is derived from identity+regime+financials+counterparties via build_snapshot_firm_from_state.

## List of clients to migrate

**6 team clients:**
| id | name | specifics |
|---|---|---|
| `client_a` | Client A | T-3 OKVED change, statistics report 1-SP (freight), tasks_overrides with expected_event |
| `client_b` | Client B | **USN+PSN** (active 2026 patent, schedule + KBK code), 2 accounts at two banks |
| `client_c` | Client C | **Parallel 2021-2024 restoration track**, 8 accounts (four banks) |
| `client_d` | Client D | USN + an expired patent, **2 cash registers** with serial numbers, a discrepancy on a Finkoper task |
| `client_e` | Client E | **3 real-estate objects** (2 direct lease, 1 agent), real_estate schema needed |
| `client_f` | Client F | **Cash registers and OFD** (a large amount of un-receipted cash), 5 contracts with one large counterparty |

**9 direct clients:**
| id | name | scenario | specifics |
|---|---|---|---|
| `client_g` | Client G | B (USN+Patent) | 3 acquiring channels, self-employed contractors |
| `client_h` | Client H | B (USN+Patent) | Bank SME accounting |
| `client_i` | Client I | D (Lease) | **A frozen foreign SP, a foreign bank**, 10+ SP tenants via a marketplace |
| `client_j` | Client J | B+E (marketplace+Patent) | a marketplace with 982 files, bank switch from one bank to another from 05-01 |
| `client_k` | Client K | C (USN+self-employed) | self-employed contractors + a related SP |
| `client_l` | Client L | A (simple USN) | minimal data |
| `client_m` | Client M | A | foreign tax residency, EDI provider |
| `client_n` | Client N | F (**AUSN — the only one**) | AUSN partner bank, **a foreign individual account in USD**, cash-flow statement due June 1 |

## Recommended migration order

**Phase 1 — simple (validate the pipeline):**
1. Client L — minimal data, checks that the pipeline works on a "thin" client
2. Client M — simple USN, adds the foreign-residency nuance

**Phase 2 — direct with schema extensions:**
3. Client G — schema_extension: 3 acquiring channels, self-employed contractors as a counterparty type
4. Client H — USN+Patent via regime.patents[]
5. Client J — bank_accounts with a bank-switch history (`closed_at` + new primary), marketplace
6. Client K — self-employed as a relation_type in counterparties
7. Client I — **foreign_accounts** + the foreign SP as a separate entity or a flag
8. **Client N** — AUSN in regime.primary.type='AUSN', foreign_account.owner='individual'

**Phase 3 — team with the most complex specifics:**
9. Client B — regime.patents[] active with a schedule
10. Client D — accounts.kassas[] with serial numbers + an expired patent_history
11. Client F — large state (kassas, 5 counterparty contracts, large un-receipted cash)
12. Client E — **a new state/real_estate.json** for 3 objects
13. Client C — 8 banks in accounts + the parallel restoration track
14. Client A — tasks_overrides extension

## Format extensions (planned)

**May be needed:**
- `state/real_estate.json` — for Client E (3 objects, formula R, agent income)
- `state/patents.json` OR `regime.patents[]` — for Client B + Client G + Client H + Client J + Client D. Decide where it lives. The pilot Client K2 has `regime.patents=[]`, the schema is ready.
- `state/recovery.json` OR `tasks with task_type='recovery_period'` — for Client C's 2021-2024 restoration. Can be done via `financials.periods` archived items.
- `accounts.bank_accounts[].close_history` — for Client J (bank switch) and Client C (8 accounts)
- `counterparties.contract` — for Client F (5 contracts with one counterparty — different terms)
- In identity: `incorporation` for team clients (fresh_url + finkoper_task_ids — already partly in contour)

**DO it like this:**
1. First read Client K2's existing state (as a sample)
2. Migrate the client — create 7 state files + history.jsonl + clean up mental_model
3. If a client needs a **schema extension** — extend schema_version with a minor bump (1.0 → 1.1), document it in a file comment
4. Regenerate the dashboard + check visually
5. **Each client separately** — do not do a batch of 14 at once

## Known nuances

- **Edit-tool truncation** on long Cyrillic edits in .py — use bash+python heredoc (memory `edit_tool_pitfalls.md`)
- **Null bytes** at the tail of .py files via the mount — after each write check py_compile (memory `edit_tool_truncation_pattern.md`). Right now `_aggregator.py` and `_clients_team.py` have 19 nulls — task `#13` not done
- **Backups mandatory** before each substantive edit of `.py` / state/*.json — `.bak_YYYYMMDD_HHMMSS_<ctx>`
- **DO NOT TOUCH clients_data.json** in this phase — it is the rollback fallback. Delete only when all 15 clients are migrated and the pipeline has been verified for 2-3 days

## Architectural memory (applied automatically)

Already saved in memory/:
- `snapshot_is_view_not_store.md` — the snapshot is derived from state, not a separate file
- `edit_tool_pitfalls.md` — bash+heredoc for long edits
- `edit_tool_truncation_pattern.md` — check py_compile afterward
- `downloads_mount_access_pattern.md` — the direct path works despite the I/O error on ls
- `finkoper_blob_attachments_workflow.md` — attachments pipeline
- `decisions_journal_is_approval.md` — status "new" = approval
- `human_decisions_persistence.md` — do not overwrite manual notes
- `track_zone_filter.md` — system_internal is not shown
- `chat_buttons_pattern.md` — closing = a dialog
- + ~20 others from previous sessions

## First-move scenario for a new session

1. Read this file in full
2. Read `policies/INSTRUCTIONS.md` (the standard protocol)
3. Read `policies/safety-rules.md`
4. Read the example state files of Client K2 (`Direct/SP Client K2/state/*.json`)
5. Ask the operator: "Do we start with Client L (a simple direct one)?"
6. For each client: a short plan → approval → migration → dashboard check

## ⚠️ IMPORTANT — a regression at the end of the session

At the very end of the session I made many small UX edits via bash+python heredoc, after which the file `_client_dashboard_v2.py` ended up truncated (memory `edit_tool_truncation_pattern.md` — long Cyrillic .py edits via the mount). The file was restored from the backup `_20260524_193342_risk_ru`. This means **some of the last edits were lost** — they need to be redone in a new session:

| # | What to redo | Where |
|---|---|---|
| R1 | Remove focus-band from the concat | `_client_dashboard_v2.py:render_client_dashboard_v2` — drop `+ focus_band` from the final concat + delete the block where it is built |
| R2 | Simplify the modal breadcrumb to `← <client_name>` | `_track_modal.py:TRACK_MODAL_HTML` + JS (instead of `🏠 Dashboard > Track`) |
| R3 | Remove the "Open TG + copy reply" button from the modal | `_track_modal.py` |
| R4 | Translate periods.status into Russian (archive/calculated/...) | `_client_dashboard_v2.py:render_client_financials` |
| R5 | Translate tax_calendar.status into Russian (overlapped_by_insurance/...) | same |
| R6 | linked_task in the financial model: title via lookup in state/tasks.json | same |
| R7 | blocked_by on track cards: title via lookup | `_overview_v2.py:render_tracks_zone` (`_tasks_title_cache`) |
| R8 | Translate risk.category into Russian (CLIENT_RELATIONSHIP → client relationship) | `_client_dashboard_v2.py:render_client_risks` |
| R9 | Fix variable shadowing: inside the loop over linked_tasks rename `title` → `_lt_title` | same |
| R10 | Dedup: do not show a risk in the focus-band if its linked_tasks ∈ focus task ids | same (if focus-band is not removed) |
| R11 | Do not show green risks in the risks section (filter severity != 'green') | same |
| R12 | Remove the "Closed risks" (resolved) block from the dashboard | same |

In the new session: BEFORE any edits read the R1-R12 list + agree the order with the operator. Do it in small batches with verify after each step.

## Summary of this session

- 8 iterations of Client K2 (Iter 1-8): tasks → identity → regime → accounts → financials → counterparties → risks + behavior + view
- 10+ UX fixes: focus-band, priority color, sections in a unified format, a unified button design system (tm-btn-*), font accessibility, translation of risk categories into Russian, risk/task dedup in the focus-band
- A Linear-style track modal with 6 new sections (meta/deps/typespecific/labels/comments/history)
- Found and fixed a variable-shadowing bug in render_client_risks (the task's title instead of the risk's title)
- All 22 dashboards generate. clients_data.json untouched (rollback fallback).

## Open tasks (from the task list)

- #6 — Update INSTRUCTIONS.md + safety-rules.md for the new workflow with state_ops (not done this session)
- #8 — An onboarding template for a new client in the new architecture
- #13 — P1: null bytes in `_aggregator.py` + `_clients_team.py` (a growing threat)
- #7 — Final verification: visual comparison of dashboards against the baseline

## Final note

The operator is tired after a long session and wants to continue in a new one. That is fine. The Client K2 pilot was done thoughtfully and the Linear style is approved. **The main thing — do not redo the pilot, use it as the reference for the rest, but allow format extensions for their specifics.** Which extensions to make — discuss with the operator for each client, do not make architectural decisions silently.
