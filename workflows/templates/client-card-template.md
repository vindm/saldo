# Client card — SP <Surname F.M.>

> Source of truth for the client. The deadline calendar, checklists, and request replies should rely on this card. Keep it up to date.

## Details

| Field | Value |
|---|---|
| Full name | Sole proprietor <Surname First-name Patronymic> |
| Name in 1C | <Surname F. M. SP> |
| INN | <fill in> |
| OGRNIP | <fill in> |
| SP registration date | <DD.MM.YYYY> |
| Residence address | <postal code, region, district, locality, street, building, apt.> |
| OKTMO | <fill in> |
| OKATO | <fill in> |
| Tax office | <code — inspectorate name> |
| Primary OKVED | <code> — <description> |
| OKOPF | <fill in> |
| OKFS | <fill in> |
| Email | <fill in or —> |
| Phone | <fill in or —> |

> ⚠️ If the INN region ≠ the region of the SP's actual registration — record it here. Regional rates/benefits are tied to the region where the SP is on record.

## Tax regime

| Field | Value |
|---|---|
| Regime | <USN / OSNO / AUSN / PSN> |
| USN object | <Income 6% / Income minus expenses 15%> *(if USN)* |
| Patent(s) | <not applicable / see below> |
| Employees | <No / Yes: N people> |
| AUSN application | <yes/no> |
| Tax holidays | <not applied / clarify — justification> |

## First-year specifics *(if the SP was registered less than a year ago)*

- Registration date: <DD.MM.YYYY> — effectively operating for <N> months.
- Fixed insurance contributions for <year> are calculated proportionally from the registration date. Full amount for <year> — <…> RUB; proportionally ≈ <…> RUB. Payment deadline — 28.12.<year>.
- USN return for <year> — for the partial year.
- 1% over 300,000 RUB — the 300k threshold for a partial year is calculated proportionally.

## Patent *(if applicable)*

| Field | Value |
|---|---|
| Activity | <name> |
| Patent No. | <fill in> |
| Issued | <DD.MM.YYYY> |
| Validity period | <from — to> |
| Potential income | <amount> RUB |
| Rate | <%> |
| Patent tax | <amount> RUB |
| KBK | <fill in> |

**Patent payment schedule:**
- <amount> RUB — by <DD.MM.YYYY> — <status>
- <amount> RUB — by <DD.MM.YYYY> — <status>

## Bank accounts

| Bank | BIC | Account | Purpose |
|---|---|---|---|
| <Bank> | <BIC> | <settlement account> | <main / acquiring / other> |

## Cash registers and OFD *(if applicable)*

- Cash register in 1C as of <date>: <count / 0>.
- Cash register: <registered / not registered> (check — kkt.nalog.gov.ru).
- OFD: <operator, personal account>.
- Customer receipts issued by: <the SP themselves / an agent (name)>.

## Counterparties and contracts *(if there are stable relationships with key counterparties)*

| Counterparty | INN | Contract | Nature |
|---|---|---|---|
| <name> | <INN> | <No. and date> | <subject of the contract> |

## Customer receivables *(if there's a balance in 1C as of the card update date)*

As of <date> in 1C: customer receivables **<amount> RUB** — <comment, source, what to reconcile>.

## Areas of responsibility for this client

| Stage | Who does it | Where |
|---|---|---|
| Collecting primary documents, calculation, preparing returns/notifications, preparing payment orders | The bookkeeper (the operator) | 1C:Fresh |
| Setting tasks, monitoring, and sending reports (returns, notifications, reports) | The supervisor | Third-party services (NOT 1C) |
| Signing and paying tax and contribution payment orders | The client | Their own online banking |
| Monitoring the fact of payment | The client | — |

**Bookkeeper's internal deadline** — 5 calendar days before the statutory deadline: by this point the calculation is done, the payment order prepared, the documents handed to the supervisor/client.

## Specifics and recurring processes

- <Regular primary-document flow: from where, how often, in what form>
- <Specifics of sending documents / reports>
- <Statistical reports for this OKVED (check via websbor.gks.ru)>
- <State of overdue tasks in 1C as of the card update date>

## External systems

| System | Address/ID | What's stored |
|---|---|---|
| 1C:Fresh | https://msk1.1cfresh.com/a/ea/<ID>/ru_RU/ | Bookkeeping. Base ID: **<…>**. Subscriber: <…> |
| 1C servicing partner | <name, phone> | Tech support |
| Finkoper | https://app.finkoper.com/ | Tasks from the supervisor |
| Email — folder | <folder name> | Incoming documents and correspondence |
| Local folder | `WORK/SP <Surname>/` | Downloaded documents |

## Contacts

| Who | Contact | Role |
|---|---|---|
| SP <Surname F.M.> | <email>, <phone> | Client |
| Supervisor | <name, contact> | Setting tasks, sending reports |

---

**Filled in / updated:** <DD.MM.YYYY> — <data source (organization card in 1C:Fresh, bank statement, etc.)>.

**What's left to check (not critical):**
- <item 1>
- <item 2>
