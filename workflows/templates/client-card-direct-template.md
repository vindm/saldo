# Client card — SP <Surname F.M.> (direct arrangement)

> Source of truth for the client. **Direct arrangement** (no Finkoper, no supervisor). All roles — on the operator.

## Service arrangement

**Direct** | Sub-scenario: **<A — Simple USN / B — USN + Patent / C — Video production with self-employed contractors / D — Rental / E — Marketplace / F — AUSN>**

## Details

| Field | Value |
|---|---|
| Full name | Sole proprietor <Surname First-name Patronymic> |
| Name in the books | <Surname F. M. SP> |
| INN | <fill in> |
| OGRNIP | <fill in> |
| SP registration date | <DD.MM.YYYY> |
| Registration address | <postal code, region, district, locality, street, building, apt.> |
| Tax office of record | <code — name> |
| Tax office of registration | <code — name> |
| OKTMO | <fill in> |
| Primary OKVED | <code> — <description> |
| Additional OKVED | <codes or —> |
| Email | <fill in or —> |
| Phone | <fill in or —> |
| Telegram | <@username or —> |
| WhatsApp | <number or —> |
| Website | <url or —> |

## Tax regime

| Field | Value |
|---|---|
| Regime | **<USN Income 6% / USN I-E 15% / Patent / USN+Patent / AUSN / NPD>** |
| Patent | <— / No. <number> dated <date>, period <from>-<to>, tax <amount>, activity type> |
| Signing / UKEP | **<with the client / with the operator>** (during testing — with the client) |
| Report filing | <Taxpayer LE → client in the FTS personal account / Tinkoff SME Accounting / AUSN — not filed> |

## 2025 specifics

<USN income / patent revenue / turnover, tax, specifics>

## 2026 specifics

- **Q1 2026 income (USN / actual):** <amount>
- **Q1 2026 taxes:** <USN advance, fixed contributions, 1% over the threshold>

## Bank accounts

| Bank | BIC | Account | Purpose |
|---|---|---|---|
| <bank> | <BIC> | <account> | Settlement (main) |

**Online-banking access:** <none / view / prepare / full>

> For AUSN clients: indicate whether the bank is in the list of AUSN partners.

## Cash registers and OFD

- **Own cash register:** <no / yes: model, fiscal drive, OFD>
- **Acquiring:** <bank, contract, rate> or —
- **Payment agents:** <Prodamus / WB / others> or —

## Counterparties and contracts

| Counterparty | INN | Contract | Nature |
|---|---|---|---|
| <name> | <INN> | <number, date> | <relationship type> |

## Areas of responsibility for this client (direct arrangement)

| Stage | Who does it |
|---|---|
| Collecting primary documents (bank statement) | The operator (client's bank personal account) |
| Collecting agent / marketplace reports | The operator + client (forwarding via TG/WA) |
| Income accounting and KUDIR | The operator (Excel) |
| Calculating taxes and contributions | The operator |
| Preparing payment orders | The operator |
| Sending payment orders in the bank | **Only the operator manually** (the assistant prepares the details) |
| Preparing the tax return | The operator (if applicable — not filed on AUSN) |
| Delivering the return to the client | The operator (TG/WA) |
| Filing the return in the FTS personal account | **The client themselves**, with their UKEP |
| Monitoring the fact of payment | The operator |

> **For AUSN clients** add a block: monthly reconciliation of the FTS notification against own records + correct tagging of transactions in the partner bank's personal account.

## Bookkeeping-services contract (between the operator and the client)

- **The operator's details (which SP/self-employment you work under):** <fill in>
- **Rate and frequency:** <fill in>
- **Main communication channel:** <TG/WA>
- **When signed / validity period:** <fill in>

## Specifics and recurring processes

- <Business model in one phrase>
- <Seasonality, recurring cycles>
- <Non-standard transactions — foreign trade, agency, etc.>
- <How the client sends primary documents>

## External systems

| System | Address/ID | What's stored |
|---|---|---|
| Bookkeeping | Excel (KUDIR, KUD) — not 1C | <fill in> |
| Bank personal account | <url> | Statements, payment orders. Access <level> |
| Taxpayer LE | The operator's desktop | USN returns .xml |
| FTS personal account | nalog.gov.ru | Report filing BY THE CLIENT THEMSELVES under their UKEP |
| Telegram/WhatsApp | <@username / number> | Communication channel |
| Folder | `CLIENTS/CLIENTS 2026/<folder name>/` | Documents |

## Contacts

| Who | Contact | Role |
|---|---|---|
| <SP Name> | TG: <…>; email: <…>; phone: <…> | Client |
| The operator | <redacted> | Bookkeeper (direct arrangement) |

---

## Fill-in history

- **<DD.MM.YYYY>** — <data source, context>.

## What's needed from the operator (open fields ❓)

Each field marked ❓ in the card above — list here compactly:

1. <question>
2. <question>

## Watching (requires future actions)

- **<DD.MM.YYYY>** — <what and amount / reminder>

---

_Template created on 2026-05-23 in Stage 1A of expanding the system for the direct arrangement. Version 0.1._
