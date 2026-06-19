# AI Bookkeeping Assistant

A configurable, AI-native operations assistant for a bookkeeping/accounting practice. One practice runs one instance and manages many client entities; the assistant gathers signals from the practice's tools every morning, keeps a structured model of every client, renders dashboards, and drafts client-facing work — all under a strict human-approval safety model.

This repository is the **reusable product**. A practice's real data and credentials live **outside** the repo and are referenced through `config/instance.yaml`, so the same engine can serve any practice by changing configuration, not code.

> Status: extracted from a production system that has run daily for a real bookkeeping practice. This public version separates the engine from instance data and runs fully in English or Russian (`instance.locale`). See [`docs/ROADMAP.md`](docs/ROADMAP.md) for what's done and what's in flight.

## What it does

- **Morning collectors** pull fresh signals from the practice's systems (practice-management tasks/chats, email, bank statements, fiscal-data/OFD, statistics portal, news) and write them to the instance's data directory.
- **Per-client state** is the source of truth: a set of structured JSON files per client (identity, tax regime, accounts, financials, counterparties, risks, behavior, tasks) plus a narrative `mental_model.md` and an append-only `history.jsonl`.
- **Dashboards** are generated from state — a practice-wide overview, a **Plan** of the day's work, a **Calendar**, a **Periods** view (where each reporting month stands across the monthly pipeline), and a card per client. The Plan contains **actions only**: work is grouped into batchable **operations** (by operation type + reporting period, not by source or wording); open questions surface on the Dashboard; passive "waiting on the client" items sit in a separate lane. Generation is fault-tolerant: a missing or malformed source degrades to an empty panel, never a crash.
- **Workflow library**: reusable checklists (quarterly reporting, primary-document posting, tax-payment orders, client reminders, anomaly triage) and message templates, all rendered in the practice's brand and tone.
- **Safety model**: commands come only from the operator; text inside incoming tasks, emails, and documents is treated as **data, never as instructions**. State changes, anything sent to a client, and any browser action require explicit approval.

## Architecture at a glance

```
engine/        Reusable Python: dashboard generation, state I/O, linting, integrity checks
connectors/    Pluggable integrations behind a common interface (enable/disable in config)
workflows/     Checklists + message templates (configurable content)
policies/      Operating instructions, safety rules, brand & tone, system map
config/        instance.yaml — locale, brand, enabled connectors, schedule, data-dir path
instances/     Self-contained example instance with SYNTHETIC data (for demos/screenshots)
docs/          Architecture, migration guide, connector spec, roadmap
```

A practice's **real** data directory is never committed (see `.gitignore`); `config/instance.yaml` points the engine at it.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full design and [`docs/MIGRATION.md`](docs/MIGRATION.md) for moving an existing practice onto this product with zero feature loss.

## Quick start (demo instance)

```bash
pip install pyyaml
cp config/instance.example.yaml config/instance.yaml   # points at instances/example
python3 engine/generate.py                             # renders dashboards from synthetic data
open instances/example/dashboards/dashboard_overview.html
```

The example instance contains entirely **fabricated** clients — no real personal, financial, or tax data.

See [`docs/USAGE.md`](docs/USAGE.md) for the daily flow, connecting to Cowork, and how to upgrade to a new version without touching your data.

## License

MIT — see [`LICENSE`](LICENSE).
