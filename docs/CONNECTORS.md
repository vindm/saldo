# Connectors

A connector is a pluggable integration with one external system. Each is enabled/disabled in `config/instance.yaml` and implements a common interface.

## Interface

Every connector domain provides:

- **Atomic skills** — single operations, e.g. `read_task`, `list_messages`, `get_statement`, `check_z_report`, `search_topics`.
- **Composite pipelines** — `morning_full_scan` (full sweep) and `incremental_update` (since-last-run), built from the atomic skills.
- A `README.md` describing the domain, its skills, and parameters.

Composites write their results into the instance's data directory in a defined format that the engine loaders parse. Credentials are read from environment variables, never from config or code.

## Bundled connectors

| Connector | System | Purpose |
|---|---|---|
| `practice_management` | Finkoper | Tasks and client chats: notifications, task/chat reads, status changes |
| `email` | Mail (Yandex) | Inbox triage, thread/message reads, morning digest |
| `telegram` | Telegram | Direct-client chats sync |
| `bank` | T-Bank, Alfa | Statements & operations for the direct book |
| `ofd` | Fiscal Data Operator | Cash / Z-report reconciliation |
| `stats_portal` | Statistics portal | Annual statistical reporting checks |
| `registry` | Company registry | Requisite verification against the official registry |
| `news` | News sources | Domain news by configured topics |
| `mm_update` | (internal) | Single contract for applying any signal to client state |

## Adding a connector

1. Create `connectors/<name>/` with a `README.md`, atomic skill specs, and `morning_full_scan` / `incremental_update`.
2. Define the output format and add a loader in `engine/_loaders.py`.
3. Register it under `connectors:` in `instance.yaml`.
4. Keep the safety invariants: no destructive or outbound action without explicit approval.
