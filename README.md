# Saldo

**An AI-native operating system for a multi-client bookkeeping practice.** You *read* the dashboards to see the state of the whole practice; you *change* everything by talking to an AI assistant in plain language. Behind it, a Python engine deterministically renders that assistant's structured memory into the screens you read — so **`dashboards = render(state)`**, and the assistant's only job is to keep the state correct.

[![Live demo](https://img.shields.io/badge/▶_live_demo-1F4E79)](https://vindm.github.io/saldo/)
![License: FSL-1.1-MIT](https://img.shields.io/badge/license-FSL--1.1--MIT-blue)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Status: production](https://img.shields.io/badge/status-daily%20production-success)
![Runtime: Cowork + static generator](https://img.shields.io/badge/runtime-Cowork%20%2B%20static%20generator-lightgrey)

> *Saldo* — the balance that's left when everything reconciles.

![Saldo walkthrough — overview, plan, an expanded operation, a task with its hypothesis, and the prompt hand-off to Cowork](docs/demo.gif)

<sub>From the overview to the Plan, expand a batchable operation to see it fan out across clients, open a task for its hypothesis and history, then hand the generated prompt to Cowork — and back to the updated dashboard. Recorded against a fully **synthetic** example instance (Aurora, Cobalt, Harbor… plus two Indonesian clients, Melati and Kirana, for the multi-jurisdiction path). No real data.</sub>

**▶ [Click through the live demo](https://vindm.github.io/saldo/)** — the same synthetic instance, rendered by the engine and published to GitHub Pages.

## What it is, in one mental model

Think of it as a small operating system for a bookkeeping practice, where **the AI is the runtime** and **the files are the database**:

- **State is the source of truth — and the AI's memory.** Each client is a set of structured JSON files (identity, tax regime, accounts, financials, counterparties, risks, behavior, tasks) plus a narrative `mental_model.md` and an append-only `history.jsonl`. This *same* state is the database, the render input, and what the assistant remembers between sessions.
- **The dashboards are a pure render of that state.** A deterministic Python generator turns the JSON into static HTML. Nothing is stored twice; the HTML is a disposable build artifact — *you never edit it by hand.*
- **Claude (in Cowork) is the runtime.** The assistant gathers signals from the practice's tools, updates the state, drafts the client-facing work, and regenerates the dashboards. The engine only renders; there is no server to operate.
- **Multi-jurisdiction, one operator.** Tax content — regimes, the recurring cycles (monthly close + payroll / quarterly tax / AUSN), the authority and portal, terminology, currency — lives in a **jurisdiction pack** (`jurisdictions/<code>/`), and each client binds to one. **Locale ≠ jurisdiction:** a Russian-speaking operator can keep books for an Indonesian company — the UI stays in their language while the filings follow the client's jurisdiction. Two packs ship today: `ru` (USN / AUSN / OSNO / PSN; FTS; ENP/KBK) and `id` (Indonesia: UMKM final PPh 0.5%, PPh 21 + BPJS payroll, unifikasi withholding, SPT Masa, annual SPT Tahunan Badan). Adding a jurisdiction is pure data — no engine change.

So Saldo is **a Cowork plugin that turns Claude into a specialist for a bookkeeping practice** with many client entities. It bundles the practice's domain workflows as Skills and its external systems as connectors, and leans on Cowork's approval model — Claude shows its plan and waits before it writes state or contacts a client. It lives in the same lane as Anthropic's own role plugins (finance, small-business), but it's extracted from a system I built solo and **run in daily production** for a real practice.

## How you actually use it

There are only two surfaces, and they map onto the two things you ever do:

| You want to… | …so you | Where |
|---|---|---|
| **See what's going on** — what's overdue, what's waiting on you, where each client stands | read the generated dashboards | the HTML (overview · plan · periods · client cards) |
| **Change something** — answer an open question, run a close, add a client, draft a message | talk to the assistant in plain language | the Cowork chat |

A typical morning: open the **overview**, see the practice's open questions with the assistant's proposed call on each, approve or redirect them in chat, let it run the batchable operations, and review the messages it drafted in the practice's brand. The assistant keeps the model current on its own (recording incoming signals needs no approval); what **requires your explicit approval** is anything sent to a client, any browser action, and closing a track — the human stays in the loop where it matters.

## How it works

```
  you ──talk──▶  Claude (Cowork)  ──edits──▶  state/*.json  ──render──▶  dashboards
  │              gathers signals,             (single source     (pure, deterministic
  │              drafts the work               of truth +         static HTML)
  │              under approval                AI memory)              │
  └────────────────────── read ◀──────────────────────────────────────┘
        morning collectors (email, bank, OFD, tasks…) feed state — additive, optional
                  state_lint / integrity checks gate every render
```

The loop is the product: **you read state as a dashboard, and you change it by talking to the system.**

## What makes it interesting (engineering)

- **One single-source-of-truth, shared by code and agent.** The per-client JSON is simultaneously the database, the generator's input, and the assistant's memory. The agent is a first-class participant in the same `view = f(state)` discipline the UI obeys — it reads and writes *only* state, never the rendered output.
- **Deterministic, fault-tolerant generation — no server.** A missing or malformed source degrades to an empty panel with a status dot, never a crash. The whole UI is a build artifact you can delete and regenerate.
- **JSON-first.** Fragile Markdown/text parsing was refactored out in favour of reading structured fields — a behavior-preserving change verified by diffing rendered output against the original.
- **A real plan model, not a task dump.** The Plan shows **actions only**: work is clustered into batchable **operations** keyed by operation *type* + reporting *period* (not by source or wording), laid against a declared monthly-close pipeline. Open questions route to the Dashboard; passive "waiting on the client" items to a separate lane; risks to the client card.
- **Prompt-injection-resistant safety model.** Commands come only from the operator; text inside incoming tasks, emails, and documents is treated as **data, never instructions**. Recording incoming signals into state is automatic (the daemons' job); anything sent to a client, any browser action, and closing a track require explicit approval; a fixed browser deny-list blocks sends, e-signature, ledger edits, and deletes.
- **Bilingual by configuration.** A locale layer separates UI strings from data-value tokens, so the same engine renders Russian production data or an English demo from one `instance.locale` flag.
- **Practice-agnostic core.** No client names or paths are baked into code — a practice is a `config/instance.yaml` plus a private data directory that never enters the repo.

## The surfaces

- **Morning collectors** pull fresh signals from the practice's systems — practice-management tasks/chats, email, the messengers (Telegram / WhatsApp / Max), cloud + local **documents**, bank statements, fiscal-data/OFD, the statistics portal, the company registry, and news — as JSON into the instance's data directory. They are *additive*: the dashboards are correct without them.
- **Monitors and resolvers** then derive from state with no external calls: a `resolution_sweep` that recomputes each task's next step and auto-closes open questions a reachable source has already settled, plus `deadline` / `staleness` / `threshold` / `counterparty` monitors. A `scheduler` reconciles all of these to the timetable declared in `config/instance.yaml`, touching only Saldo-owned jobs.
- **Dashboards**: a practice-wide **overview**, a **Plan** of the day's work (batchable operations / individual tasks / a "waiting" lane), a navigable **Calendar**, a **Periods** view of where each reporting month stands across the close pipeline, and a **card per client** — each opening on a one-line *situation brief* ("the story of the client right now"), with a per-row *hypothesis* lens on every task.
- **Client-facing output**: a monthly one-pager rendered in the practice's brand, drawn from a dedicated client-clean field so internal working notes never leak to the client. Sending is approval-gated.
- **Workflow library**: per-jurisdiction checklists (monthly close, payroll, withholding, tax-payment orders, quarterly/annual reporting, client reminders, anomaly triage) and message templates, rendered in the practice's brand and tone.
- **Self-update**: when the published engine moves ahead, the dashboard surfaces a "new version available" item; one click hands Claude a guarded upgrade prompt that pauses for confirmation, applies any pending migrations, and re-runs the lint/integrity checks.

## Architecture at a glance

```
engine/        Reusable Python: dashboard generation, state I/O, linting, integrity checks
connectors/    Pluggable collectors, monitors & skills behind a common interface (enable/disable in config)
jurisdictions/ Per-jurisdiction packs (ru, id): regimes, pipeline, authorities, checklists — pure data
workflows/     Cross-jurisdiction checklists + message templates (configurable content)
migrations/    Versioned, idempotent state migrations (NNNN_slug.py) run on upgrade
policies/      Operating instructions, safety rules, brand & tone, system map
config/        instance.yaml — locale, brand, enabled connectors, schedule, data-dir path
instances/     Self-contained example instance with SYNTHETIC data (for demos/screenshots)
docs/          Architecture, usage, migration, connector spec, roadmap
```

A change to behaviour edits the markdown the runtime reads (`policies/`, `jurisdictions/`, `connectors/`); a change to data/state ships a versioned **migration** under `migrations/`. The upgrade path on an operator's machine is: pull the engine → `migrate.py status` → `up` (preview) → `up --apply` → `state_lint`.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the design (incl. the plan/task model), [`docs/USAGE.md`](docs/USAGE.md) for the daily flow, [`jurisdictions/README.md`](jurisdictions/README.md) for authoring a jurisdiction pack, and [`docs/MIGRATION.md`](docs/MIGRATION.md) for moving an existing practice onto it with zero feature loss.

## Quick start (demo instance)

```bash
pip install pyyaml
cp config/instance.example.yaml config/instance.yaml   # points at instances/example
python3 engine/generate.py                             # renders dashboards from synthetic data
open instances/example/data/dashboards/dashboard_overview.html
```

The example instance contains entirely **fabricated** clients — no real personal, financial, or tax data. To run a real practice, point `data.dir` at a private directory **outside** this repo; it never enters version control.

## Testing

Run the end-to-end smoke test against the bundled synthetic example instance (no real data, CI-safe):

```bash
python3 engine/selftest.py
```

It byte-compiles every module, renders the example, checks pages + inter-page links, runs `state_lint` / `system_integrity_check` / `migrate status`, and verifies a deterministic re-render. Exit 0 = green.

## License

[**Functional Source License (FSL-1.1-MIT)**](LICENSE). You may use, modify, and redistribute Saldo for any purpose **except a Competing Use** — you can't repackage it as a commercial product/service that substitutes for or competes with it. Using it to run your own bookkeeping practice (including paid client work) is explicitly permitted. Each released version automatically converts to the permissive MIT license two years after its release.
