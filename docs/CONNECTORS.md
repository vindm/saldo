# Connectors

A connector is a pluggable integration with one external system. Each is enabled/disabled in `config/instance.yaml` and implements a common interface.

## Interface

Every connector domain provides:

- **Atomic skills** — single operations, e.g. `read_task`, `list_messages`, `get_statement`, `check_z_report`, `search_topics`.
- **Composite pipelines** — `morning_full_scan` (full sweep) and `incremental_update` (since-last-run), built from the atomic skills.
- A `README.md` describing the domain, its skills, and parameters.

Composites write their results into the instance's data directory in a defined format that the engine loaders parse. Credentials are read from environment variables, never from config or code.

## Bundled connectors

### External-system collectors

| Connector | System | Purpose |
|---|---|---|
| `practice_management` | Finkoper | Tasks and client chats: notifications, task/chat reads, status changes |
| `email` | Mail (Yandex) | Inbox triage, thread/message reads, morning digest |
| `messengers` | Telegram, WhatsApp, Max | Direct-client chats sync (session-level access: one operator account reaches every chat by search) |
| `bank` | T-Bank, Alfa | Statements & operations for the direct book |
| `ofd` | Fiscal Data Operator | Cash / Z-report reconciliation |
| `stats_portal` | Statistics portal (websbor) | Annual statistical reporting checks |
| `registry` | Company registry (egrul) | Requisite verification against the official registry |
| `documents` | Local docs folders | Ingest client documents (receipts, statements, payment proofs); matches a payment receipt to its `tax_calendar` entry and records `payment_ref` |
| `news` | News sources | Domain news by configured topics |

### Internal / runtime connectors

These have no external API; they read and write client state, drive the upgrade cycle, or reconcile the operator's environment. The monitors/resolvers are the daemon half of the hybrid model (daemons write state, the operator closes from the card).

| Connector | Role | Purpose |
|---|---|---|
| `mm_update` | state contract | Single contract for applying any signal to client state |
| `onboarding` | state | Add a new client: gather identity/regime, resolve jurisdiction, register via `state_ops`, regenerate — operator-gated, additive (no migration) |
| `deadline_monitor` | monitor | Writes upcoming tax-calendar deadlines into state; drops entries once terminal (`status:paid` + `payment_ref`) |
| `staleness_monitor` | monitor | Flags tracks with no movement (stale) for nudge or postpone |
| `threshold_monitor` | monitor | Watches regime thresholds (e.g. turnover approaching a regime/PKP limit) |
| `counterparty_status` | monitor | Counterparty (contractor) status / reliability signals |
| `question_resolver` | resolver | The `open_question` rung logic (acquire / close) — **run within `resolution_sweep`, not separately scheduled** |
| `resolution_sweep` | resolver | The one scheduled actualization daemon (07:00): performs the reversible half of every active task's resolution — incl. open questions via the `question_resolver` rung logic — and surfaces the rest (`policies/resolution-model.md`) |
| `scheduler` | environment | Reconciles the operator's scheduled tasks to `config/instance.yaml → schedule` (Saldo-owned `saldo-<name>` jobs only) |
| `migration_runtime` | upgrade | Drives the runtime half of migrations during an upgrade (`migrate.py next → apply → record`) |
| `update` | upgrade | Operator self-update: checks GitHub, runs the guarded pull → migrate → rebuild via `tools/update.py` |

## Adding a connector

1. Create `connectors/<name>/` with a `README.md`, atomic skill specs, and `morning_full_scan` / `incremental_update`.
2. Define the output format and add a loader in `engine/_loaders.py`.
3. Register it under `connectors:` in `instance.yaml`.
4. Keep the safety invariants: no destructive or outbound action without explicit approval.
