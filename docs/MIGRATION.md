# Migration & install runbook

Two audiences:

- **A. A brand-new practice** that wants to start using the product (no prior system).
- **B. An existing practice** already running the original bespoke system on its own machine, with daemons connected to real data, that wants to cut over to this product **with zero feature loss** (this is the path for the reference instance — "mom's").

The key fact that makes both low-risk: **dashboards render from `state/*.json` only.** Collectors/daemons are *additive* signals, not a render dependency — a missing collector degrades to an empty panel, never a crash. So once a practice's state is in place, the dashboards work immediately; connectors are wired up afterwards, incrementally.

---

## A. New practice — first run

Requirements: Python 3.10+, `pip install pyyaml`.

```bash
git clone <repo> ai-bookkeeping-assistant && cd ai-bookkeeping-assistant
cp config/instance.example.yaml config/instance.yaml
python3 engine/generate.py          # renders the SYNTHETIC example instance
open instances/example/dashboards/dashboard_overview.html
```

Then point it at your own (private) data directory and fill in brand/locale — see **§C Configuration** and **§D Data layout**. Your real data lives **outside the repo** (`.gitignore` blocks `instances/*/data`, secrets, `*.html`).

Onboarding via Cowork: see [`docs/USAGE.md`](USAGE.md) (connect the folder, run the morning routine, talk to the assistant).

---

## B. Existing practice — cut over from the previous version (zero feature loss)

The original is already state-driven, so this is mostly **configuration + a one-time data reshape**, not a rewrite. Do it as a *parallel* install — the old tree keeps running untouched until the new dashboards match.

### Reality of the legacy layout (reference instance)

| Legacy (old system) | Product (this repo) |
|---|---|
| `_Планирование/Прямые/ИП <Name>/state/*.json` + `mental_model.md` + `history.jsonl` | `<DATA_DIR>/clients/<id>/state/*.json` + `mental_model.md` + `history.jsonl` |
| `_Планирование/_data/clients_index.json` (roster, `track`=team/direct) | `<DATA_DIR>/clients_index.json` (roster, `group`) |
| `_дневник/входящие/` (daemon reports, **Markdown**) | `<DATA_DIR>/journal/inbox/` (daemon reports, **JSON**) |
| `_дневник/finkoper_state/` | `<DATA_DIR>/journal/finkoper_state/` |
| `_реестры/Сводный_календарь_2026.xlsx`, `журнал_запросов.md`, `УКЭП…md` | superseded — deadlines/requests now live as **tracks in `state/tasks.json`** (the registries are no longer a render source) |

### Step 0 — prerequisites & safety

- Install the repo on the operator's machine (e.g. `~/ai-bookkeeping-assistant`). Keep the **old `_Планирование` tree exactly where it is** — it is the rollback.
- `pip install pyyaml`.
- Pick a private data dir **outside the repo**, e.g. `~/ABA-data` (never committed).

### Step 1 — migrate the state (one command)

```bash
python3 tools/migrate_legacy_instance.py \
    "/path/to/_Планирование" \
    "$HOME/ABA-data"
```

This reads the legacy roster and copies each client's `state/*.json` (skipping `*.bak`), `mental_model.md`, and `history.jsonl` into `<DATA_DIR>/clients/<id>/`, and writes a new `clients_index.json` with `group` (from the legacy `track`). It **mutates nothing** in the source — it reshapes a copy. Expected output: `Migrated N/N clients`.

> Note: the migrator does **not** copy daemon snapshots, the inbox, or the legacy registries (those are handled in Step 4). It doesn't need to — the dashboards render from the state it just copied.

### Step 2 — configure the instance

Create `config/instance.yaml`:

```yaml
locale: ru                      # Russian UI + Russian data tokens
data:
  dir: /Users/<you>/ABA-data    # the migrated data dir (private, outside repo)
brand:
  name: "Ирина Винокурова · бухгалтерское сопровождение"
  monogram: "ИВ"
  primary: "#1F4E79"
  accent:  "#B79257"
connectors: { ... }             # enable later, in Step 4
```

(`ABA_DATA_DIR` / `ABA_DASHBOARD_DIR` / `ABA_LOCALE` env vars override the file — handy for a dry run.)

### Step 3 — render & parity-check (the acceptance gate)

```bash
ABA_DATA_DIR="$HOME/ABA-data" ABA_LOCALE=ru python3 engine/generate.py
```

Open `<DATA_DIR>/../dashboards/dashboard_overview.html`. Then confirm parity against the old dashboards:

- **Client count** matches the old roster (e.g. 16/16).
- **Health colours** match (run `python3 engine/state_lint.py` — must exit clean).
- **Plan total** (number of tasks) matches; spot-check a few clients' cards.
- Differences should be *only* the intended product improvements (plan = actions; open questions on the dashboard; the "Waiting" lane; operation/period grouping). Anything else is a migration bug — fix before cutover.

A dry run of exactly this on the reference instance produced 16/16 clients, matching health (15 green / 1 red) and a matching plan total — see `docs/ARCHITECTURE.md` for the model.

### Step 4 — wire up the collectors (incremental, after rendering is verified)

The old daemons wrote **Markdown** into `_дневник/входящие`; the product reads **JSON** from `<DATA_DIR>/journal/inbox/` (see [`docs/CONNECTORS.md`](CONNECTORS.md) for each file's shape). Migrate them one at a time — the dashboard stays correct without them:

1. Point each morning collector (practice-management/finkoper, email, telegram, bank, OFD, stats, news) at the new data dir and have it emit the product JSON shape into `journal/inbox/`.
2. The legacy registries (`Сводный_календарь`, `журнал_запросов`, `УКЭП`) are **not** re-imported as render sources — that information now lives as tracks in `state/tasks.json` (already migrated). If a deadline only existed in the old calendar and not as a track, add it as a track via the assistant (`mm_update`).
3. Verify each collector writes valid JSON (`generate.py` logs a benign `… missing` line when a daemon file is absent — that's the graceful-degradation path, not an error).

### Step 5 — schedule the morning run

Recreate the morning routine on the operator's machine (the same cadence as before: collectors → `generate.py`). In Cowork this is a scheduled task; standalone it's a cron entry. Keep the existing time.

### Step 6 — cut over

Once the new dashboards match feature-for-feature and the collectors are emitting:

- Switch the operator's daily entry point to the new dashboards.
- **Archive** the old `_Планирование` tree (rename to `_Планирование_OLD_<date>`); do **not** delete it.
- Point the Cowork workspace folder at the new data dir / repo.

### Rollback

The old tree is untouched and archived; reverting = pointing back at it. The product also writes per-edit `.bak` files and supports `snapshot.py` for restore points. Nothing in this process is destructive.

---

## C. Configuration boundary

`config/instance.yaml` (+ `ABA_*` env overrides) declares everything practice-specific: `locale`, `brand`, `data.dir`, enabled `connectors`, and schedule. The engine itself is practice-agnostic — no client names, paths, or surnames are baked into code. See [`docs/ARCHITECTURE.md`](ARCHITECTURE.md#configuration-boundary).

## D. Data layout (what `data.dir` must contain)

```
<DATA_DIR>/
  clients_index.json            # roster: [{id, name_short, group, folder:"clients/<id>"}]
  clients/<id>/
    state/*.json                # SOURCE OF TRUTH (identity, regime, accounts, financials,
                                #   counterparties, risks, behavior, tasks [, real_estate])
    mental_model.md             # narrative (prose; the engine does NOT parse it)
    history.jsonl               # append-only change log
  journal/inbox/*.json          # daemon/collector reports (optional, additive)
  journal/finkoper_state/…      # practice-management snapshot (optional)
```

## Feature-parity checklist

- [ ] All clients load from `clients_index.json` and enrich from `state/*.json`
- [ ] Overview: stats, "Open questions" block, analysis, top-5, digest
- [ ] Plan: actions only (Operations / Individual / collapsed "Waiting" lane); calendar; periods
- [ ] Per-client cards render (health, tracks = per-client plan, risks, quick-access, financials)
- [ ] `state_lint.py` exits clean (no dangling tracks / cross-link gaps)
- [ ] Each previously-active collector enabled and producing JSON into `journal/inbox`
- [ ] Safety invariants enforced (approval gates, incoming-text-as-data, browser deny-list)
