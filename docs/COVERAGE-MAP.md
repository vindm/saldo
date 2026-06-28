# Coverage map — what the data-aggregation daemons see, and what they miss

Reference for the data-aggregation layer. Pairs with `connectors/mm_update/SKILL.md` (how a
signal becomes state) and `connectors/scheduler/SKILL.md` (how jobs are registered). Audited
2026-06-25 against the example client profiles.

## The shape of the gap

Collectors ingest **four inbound channels** — email, Telegram, Finkoper (team-via-Полина),
RU tax news — plus **on-demand RU banks** (T-Bank/Alfa), OFD (month-end), EGRIP, Rosstat.
**Coverage follows the channel, not the client.** Anything arriving by any other route is
invisible until a human types it in. **Within a client, coverage now follows the ENDPOINT**: the chat collectors fan out over `behavior.channels.endpoints[]` (migration 0028), reading every `sync:true` endpoint — the personal DM, shared **work channels**, and **assistants/accountants** — not just the personal chat (closing the §9 gap where channels and assistants lived only in `quick_access` and were never read). And a whole class of facts arrives by **no channel at
all** and must be *computed* — and nothing computes it.

> The sweep's `question_resolver` rung logic only resolves questions that already exist. These gaps are signals that
> **never become questions**, because no channel carries them — silent blind spots, not open
> items.

## Coverage matrix (source → collector → clients)

| Source / channel | Collector | Status | Clients relying on it |
|---|---|---|---|
| Email | `email` | ✓ daily | meridian, lumen, cobalt, slate, **marlin (НПД чеки)**, ember |
| Telegram | `tg` | ✓ daily · **per-endpoint fan-out** (DM + work channels + assistants) | 10 (vertex, slate, quartz, cedar, marlin, ember, indigo, basalt, meridian, lumen) |
| Finkoper / via Полина | `practice_management` | ✓ daily | aurora, harbor, northwind, cobalt, onyx, cirrus, pueblo |
| RU + ID tax law | `news` | ✓ daily, **multi-jurisdiction** | RU + ID (topics per jurisdiction pack) |
| T-Bank / Alfa | `tbank` / `alfabank` | ◑ on-demand | ~half |
| OFD fiscal | `ofd` | ◑ month-end | northwind, cobalt, pueblo |
| EGRIP / Rosstat | `egrul` / `websbor` | ◑ on-demand | — |
| **WhatsApp / Max** | `whatsapp` / `max` | spec'd (by_chat) | **melati (WhatsApp primary)**; Max for RU clients |
| **Google Drive / Yandex.Disk** | `documents` | ✓ spec'd (incremental) | **melati (whole flow)**, RU clients' doc folders |
| **Local per-client folders** (cloud syncs down + manual drops) | `documents` (provider `local`) | ✓ spec'd | every client (`docs_root/docs_folder`); the single ingest path; resolves "needs a document" questions |
| **EDO (Контур)** | — | ✗ | basalt (contracts) |
| **Tochka / Sber / VTB / Mandiri / foreign** | — | ✗ | northwind, onyx, harbor, **cirrus (VTB+Sber+Alfa)**, melati (Mandiri), vertex & quartz (foreign) |
| **Prodamus / CloudPayments / YooKassa / Moka POS** | — | ✗ | meridian, vertex, slate, **melati (Moka)** |
| **Coretax / BPJS / OSS** | — | ✗ | **melati (all ID portals)** |
| 1C | — | ✗ paused | 7 clients (cirrus cluster) |
| Indonesian tax news | `news` (multi-jurisdiction) | ✓ | melati — PP55/PPN/BPJS via `id` pack `news` block |

## Gap register

### Fetch gaps — a real channel nobody reads
| # | Gap | Severity | Evidence | Fix |
|---|---|---|---|---|
| G1 | **Cloud documents** (GDrive + Yandex.Disk) | HIGH | melati's entire flow; **Mandiri statements arrive here** (covers ID bank without a bank API) | `documents` collector — **building now** |
| G2 | **WhatsApp** | HIGH | melati primary channel; future Bali salon | `whatsapp` collector — **spec'd** (`connectors/whatsapp/SKILL.md`; single-account by_chat, daily) |
| G3 | Non-T-Bank/Alfa banks (Tochka/Sber/VTB/Mandiri/foreign) | MED | money flow dark; foreign = currency-control reporting | per-bank collectors — **postponed** (not daily, human-gated 2FA). ID Mandiri covered via G1. |
| G4 | Revenue platforms (Prodamus/CloudPayments/YooKassa/Moka) | MED | gross revenue + fees invisible; only net settlement seen | per-platform collectors — **postponed** (not daily, access-gated) |
| G5 | Portals (Coretax/BPJS/OSS/ЛК ФНС inbox) | MED | requirements/notifications missed | collectors — **postponed** (access-gated) |
| G6 | EDO (Контур) | LOW | basalt contracts | postponed |
| G7 | 1C facts | — | cirrus договоры/счета/кадровое | **blocked** (1C paused) |

### Compute gaps — no channel; must derive from state; no daemon exists
| # | Gap | Severity | Evidence | Fix |
|---|---|---|---|---|
| C1 | **Deadline / tax_calendar watcher** | HIGH | `tax_calendar_<year>` rendered but never escalated; ID SPT/BPJS monthly has no reminder | `deadline_monitor` — **spec'd** (`connectors/deadline_monitor/SKILL.md`; pure compute, daily, lead tiers 14/7/2 + overdue). |
| C2 | Threshold/limit watch (USN; ID UMKM 4.8B PPN; **0.5% facility expiry**) | HIGH | melati had "следить за окончанием льготы 0,5%" as a manual backlog item | `threshold_monitor` — **spec'd** (`connectors/threshold_monitor/SKILL.md`; reads `yearly_pace` + regimes.yaml; tiers 80/90/100% + facility expiry) |
| C3 | Counterparty status (НПД lost / liquidated) | MED | marlin НПД; meridian/vertex agents | `counterparty_status` — **spec'd** (`connectors/counterparty_status/SKILL.md`; monthly EGRUL/НПД re-check) |
| C4 | Account-block / enforcement (ФНС приостановление, ФССП) | MED→HIGH if fires | none watched | needs portal access — later |
| C5 | Foreign-account currency-control reporting | MED | vertex (foreign), quartz (зарубежный банк) | later |
| C6 | Loan / lease schedules | LOW/MED | cirrus VTB credit + leases; onyx mortgage | later |
| C8 | Staleness / reconciliation (missing expected statement; bank≠OFD≠declared) | MED | nothing notices a non-arrival | `staleness_monitor` — **spec'd** (`connectors/staleness_monitor/SKILL.md`; pure compute, daily; revives the analytic R-rules) |

## Prioritization & cadence (decided 2026-06-25)

| Item | Type | Priority | Cadence | Access mode |
|---|---|---|---|---|
| G1 `documents` (GDrive + Yandex.Disk) | collector | **NOW** | daily, incremental (cheap) | auto, read-only |
| G2 `whatsapp` | collector | **NOW** | daily | auto (if connected) |
| C1 `deadline_monitor` | monitor | SOON | daily-cheap *or* weekly | none (pure compute) |
| C8 `staleness_monitor` | monitor | SOON | daily-cheap | none |
| C2 threshold | monitor | SOON* | weekly | needs revenue data first |
| C3 counterparty status | collector+monitor | LATER | monthly | auto (EGRUL) |
| G3 banks | collector | POSTPONED | monthly / on-demand | **human-gated (2FA)** |
| G4 platforms | collector | POSTPONED | monthly / on-demand | access-gated |
| G5 portals | collector | POSTPONED | on-demand | access-gated |

**Principle — cadence by cost.** External fetches needing credentials or 2FA (banks,
platforms, portals) run **infrequently and human-gated**. Pure-compute monitors (deadlines,
staleness) can run **as often as wanted** — they hit no API and need no access, so the cost
you avoid by spacing banks out simply doesn't apply. Cheap **incremental** fetches (cloud
docs: list only files changed since the watermark) run **daily**. Slow-moving data runs less
often: `threshold_monitor` **weekly** (turnover moves monthly), `counterparty_status`
**monthly** (registries change slowly + each INN is a fetch). The `scheduler` expresses this
via `{ cadence: weekly|monthly }` (`connectors/scheduler/SKILL.md`).

## Multi-account per connector

A channel collector is never one account — it is the operator's own account(s) **plus** each
client's account of that kind, often across providers (Yandex.Mail + Gmail; GDrive +
Yandex.Disk; per-client bank logins). The shared **source registry + fan-out** convention
(`connectors/_sources.md`) handles this for every channel: operator accounts in `config →
sources`, client accounts in `quick_access`, one incremental pass per account, routed to
clients by correspondent, each source tagged `access: auto | human_gated`. Banks, 1C and
portals (postponed) are the **same registry** — just more rows, `human_gated`, sparse cadence.

## Design rule

Two daemon shapes, both feeding `mm_update`: **collectors** fetch an external channel into
`journal/inbox/`; **monitors** derive risk from `state/*.json` already present. New coverage =
a new spec of one of these two shapes — no engine Python change (the runtime is the AI).
