# Roadmap

## Done

- [x] **Engine extracted** from the bespoke system into `engine/` — reusable Python, runs as-is.
- [x] **Connectors, workflows, and policies separated from data.**
- [x] **Config-driven data dir** — the hardcoded client→folder map is gone; `state_ops`/`generate.py` resolve `data.dir` (from `config/instance.yaml`) + each client's `folder` from the roster. The engine is practice-agnostic.
- [x] **Synthetic example instance** — `instances/example` ships fabricated clients conforming to the state schema, so `python3 engine/generate.py` renders out of the box; dashboard screenshots captured for the README.
- [x] **Engine i18n** — a locale layer (`_strings.py` for UI text, `_vocab.py` for data-value tokens) driven by `instance.locale`, so the same engine renders Russian production data or the English demo without breaking parsers.
- [x] **English documentation port** — README, `docs/`, `policies/`, `connectors/`, and `config` schema in English; client names scrubbed to generic placeholders.
- [x] **`.gitignore`** excludes real client data, secrets, backups, generated HTML, and the local `instance.yaml`, while committing the synthetic `instances/example` so a fresh clone runs.

## In flight

- [ ] **Reconcile `policies/INSTRUCTIONS.md` to the new layout** — replace remaining legacy references (`clients_data.json`, `registries/`, `<client doc folder>/`, OS-specific Downloads paths, the old daemon schedule) with the `instances/<id>/data/` structure.
- [ ] **Monthly-close pipeline polish** — finish wiring the declared `config/pipelines/monthly_close.yaml` stages through the Periods view (see [`MONTHLY-PIPELINE-PROPOSAL.md`](MONTHLY-PIPELINE-PROPOSAL.md)).

## Next

- [ ] **Connector interface formalization** — a thin base class/contract so a new integration is a config-driven drop-in (see [`CONNECTORS.md`](CONNECTORS.md)).
- [ ] **Setup CLI** — `init` a new instance (scaffold the data dir, `instance.yaml`, schedule) and `doctor` to validate config.
- [ ] **CI smoke test** — render the example instance and assert `LINT OK` on every push, to guard parity and catch locale-coupling regressions.

## Parity guarantee

Every step preserves feature parity with the original system; see [`MIGRATION.md`](MIGRATION.md). The original practice can migrate onto the product now that the config-driven data dir has landed.
