# Roadmap

## Done

- [x] Engine extracted from the bespoke system into `engine/` (reusable Python, runs as-is).
- [x] Connectors, workflows, and policies separated from data.
- [x] `.gitignore` excludes all client data, secrets, backups, and generated HTML.
- [x] Product framework: README, architecture, migration guide, connector spec, config schema.

## In flight

- [ ] **English documentation port** — translate `policies/`, `connectors/`, `workflows/` to English and scrub any client names to generic placeholders.
- [ ] **Config-driven data dir** — replace the hardcoded client→folder map in `state_ops.py` with `data.dir` + the roster's `folder` field from `instance.yaml`.
- [ ] **Synthetic example instance** — fabricate one client conforming to the state schema so `generate.py` runs out of the box; capture dashboard screenshots for the README.

## Next

- [ ] **Engine i18n** — extract Russian UI strings and collector-parsing tokens into a locale layer driven by `instance.locale` (deliberate pass, so parsers don't break).
- [ ] **Connector interface formalization** — a thin base so a new integration is a drop-in.
- [ ] **Setup CLI** — `init` a new instance (scaffold data dir, config, schedule).

## Parity guarantee

Every step preserves feature parity with the original system; see [`MIGRATION.md`](MIGRATION.md). The original practice can move onto the product at any point once the config-driven data dir lands.
