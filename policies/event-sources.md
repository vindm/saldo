# Event source channels — the controlled vocabulary

> Every history event (and a task's own `source`) is attributed to a **channel**:
> who or what brought the update. The channel is a **closed set** — not free form.
> Format is `channel:detail`: the `channel` head MUST be one of the tokens below;
> the `detail` after the first `:` is free (a handle, a ticket #, a filename, a
> decision ref). The machine source of truth is `engine/_helpers.py →
> _CANON_CHANNELS`; `state_lint` (`event_source_noncanon`, warn) flags anything
> outside it. The canonical writer is `_tracks.add_history_event(..., source=...)`
> — the channel is ALWAYS `source`, never `by`.

## The model: a source is always one of three things

An update was brought in by **a connector**, or made by **the operator** (Mom),
or produced by **the engine itself**. That is the whole taxonomy:

1. **Connector** — an integration ingested the signal. The channel **is the
   connector** (it mirrors the `connectors/` directory). Banks generalize to one
   `bank` channel (the specific bank in the detail); the `documents` collector
   writes `document`.
2. **Operator** (`cowork`) — Mom acting directly: her chat with the assistant, a
   decision, a manual entry, a reconciliation she did. (`chat` and `session` are
   the operator too — they fold into `cowork`, migration 0024.)
3. **System** (`system` + named daemons, + `migration`) — an engine pass produced
   it: a monitor, the resolution sweep, an analysis, the one-time legacy import.

### 1. Connectors (channel == the connector)

| channel | label | connector(s) in `connectors/` | detail example |
|---|---|---|---|
| `tg` | «TG» | `tg` | `tg:@username` |
| `whatsapp` | «WhatsApp» | `whatsapp` | `whatsapp:+7…` |
| `max` | «MAX» | `max` | `max:handle` |
| `email` | «почта» | `email` | `email:ФНС` |
| `finkoper` | «Финкопер» | `finkoper` | `finkoper:#11496548` |
| `bank` | «банк» (+ name) | `tbank`, `alfabank`, … (generalized) | `bank:Сбер`, `bank:Mandiri` |
| `ofd` | «ОФД» | `ofd` | `ofd:z-отчёт` |
| `news` | «новости» | `news` | `news:подзаконка` |
| `document` | «документ» | `documents` | `document:выписка-ЕНС`, `document:договор-№63` |
| `egrul` | «ЕГРЮЛ» | `egrul` | `egrul:ОГРНИП` |
| `websbor` | «Росстат» | `websbor` | `websbor:форма` |
| `1c` | «1С» | (data source; no daemon) | `1c:base-id` |

This set is **not hardcoded as truth** — the connector channels DERIVE from `config/instance.yaml → connectors` (`_config.CONNECTOR_CHANNELS`, the same declaration the scheduler reconciles daemons against). Enabling a connector there automatically makes its `source` channel valid — no engine edit (a few config keys map to a different channel name: `practice_management`→`finkoper`, `documents`→`document`, `stats_portal`→`websbor`, `registry`→`egrul`; `bank` stays generic). The literals in `_helpers._CANON_CHANNELS` are only the safe baseline for when no config is present (repo/tests/demo); config is additive. A new connector still needs a one-line display label in `_SRC_LABELS` for a pretty chip, else it falls back to «система».

### 2. Operator — `cowork` («Ирина»)

Mom acting directly: her chat with the assistant, a decision, a manual entry, a
reconciliation she performed. `chat` and `session` are the operator → `cowork`
(do not use them as separate channels). Detail example: `cowork:решение-10.06`.

### 3. System — `system` («система») + named daemons + `migration`

An automated engine pass with no more specific connector. Named daemons keep
their own label so the operator sees WHAT ran: `resolution_sweep` → «авто-разбор»,
`deadline_monitor` → «монитор сроков», `threshold_monitor` → «монитор порога»,
`staleness_monitor` → «монитор», `mm_update`/`dashboards` → «система». Anything
else automated → `system:<detail>`. `migration` («импорт») is the one-time legacy
→ Saldo import provenance.

## Rules for picking a channel

- **Which bucket?** A connector brought it → the connector's channel. Mom did it
  → `cowork`. The engine produced it → `system`. There is no fourth option.
- **Channel = who/what BROUGHT it, not why.** A decision Mom made is `cowork`
  (the ref goes in the detail), never `decision_…` as a channel. A daemon flag is
  `system:<flag>`, not `*_unclear` as a channel.
- **A document is `document`** (the `documents` collector), not the document's
  name as a channel. A bank *portal* is `bank`; a bank *statement file* is
  `document`.
- **Banks are generic.** One `bank` channel; the specific bank in the detail, so
  the set stays small and jurisdiction-neutral. The card shows the bank name.
- **Detail is free, channel is closed.** Handle / ticket / filename / ref go in
  the detail; never invent a new channel head.

## Lint guard

`event_source_noncanon` (`state_lint.py`) flags, at **warn** level, any source
whose channel head is not in `_CANON_CHANNELS`. Migrations 0021–0024 cleaned the
historical free-form values into this vocabulary; the warn keeps new drift visible.

## Follow-up (not built): connectors derived from client reality

Today `config/instance.yaml → connectors` is the declared list (it drives both the scheduler's daemons and this vocabulary). The next step is to derive that list **dynamically from the clients' actual channels** — the banks in `accounts.json`, the messengers in `behavior.json → channels`, the portals in `quick_access` — so an instance runs (and accepts sources from) exactly the connectors its current clients need, no more. The scheduler already filters by `enabled` + relevance (e.g. `tbank`/`alfabank` only for the direct circuit); full dynamism would compute the enabled set from a «channels in use» view over state. Relates to `connectors/scheduler` + `connectors/onboarding`.
