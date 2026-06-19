# Checklist: posting primary documents into 1C

Applies to posting an individual document (statement, act, report) into the client's accounting system after the primary documents have been collected (see `monthly-primary-documents.md` for the overall collection). This checklist is about a **specific document → a specific 1C section**.

## Stage 1. Identifying the document type

Determine which type the document belongs to:

| Type | Indicators | 1C section |
|---|---|---|
| Bank statement | ZIP/XLS/PDF from the bank for a period | `Bank and cash desk → Bank statements` |
| Cash receipt / OFD Z-report (cash) | XLSX from the OFD, "Cash settlement" column | `Bank and cash desk → Cash transactions` |
| Acquiring (card/SBP) | Already in the bank statement as "acquiring credit" | A separate document is NOT needed |
| Aggregator partner act (Yandex Taxi, Wildberries, etc.) | PARTNER_ACT_..., XXAR, XXAP | Per the agency contract — see Stage 3 below |
| Reconciliation act with a counterparty | Reconciliation_act_... | `Purchases → Settlement reconciliation acts` (for verification, not for posting) |
| Invoice / UPD (incoming) | Inv_..., UPD_... | `Purchases → Receipts` |
| Invoice (outgoing) | for a sale | `Sales → Sale` |
| Contract / addendum | negotiation context, legal | Don't post, only into the client card + Counterparties |

## Stage 2. Cross-check with the system before posting

- [ ] Find the corresponding item in `clients_data.json[client].monthly_check.sources[*]` (by `anomaly_id` or by `title`)
- [ ] Check `lifecycle_state`:
  - `awaiting_external` → find out whether it can be posted yet (for example, if we're waiting for a cash register to be connected — don't post cash until then)
  - `active` or absent → posting is allowed
- [ ] Check `dismissed_anomalies[]` — if there was an operator decision "don't flag" for this source, read the reason; don't act against the decision

## Stage 3. Posting — by type

### A. Bank statement

- [ ] `Bank and cash desk → Bank statements → Load` (Client-Bank format, usually XML/TXT) or "Add" manually
- [ ] Per `bank_statements_workflow.md` — statements arrive in a batch on the 1st–15th of the following month, not daily
- [ ] After loading — match each transaction to a counterparty and a cash-flow item
- [ ] Acquiring receipts (from an aggregator, acquiring) are already accounted for as an "acquiring credit" — do NOT create a separate "Retail sales report" (per `cash_vs_card_split.md`)

### B. Cash transaction (physical cash)

- [ ] Check whether there's cash revenue for the period via the OFD Z-report (`ofd_z_report_workflow.md`):
  - `OFD Platform → Reports → Z-Reports` → download xlsx → "Cash settlement" column
  - If across all registers cash = 0 → do NOT post the report, mark the item `not_needed` or `done`
- [ ] If there is cash → `Bank and cash desk → Cash transactions → Cash receipt`
- [ ] **NOT via "Retail sales report"** if acquiring is cashless (per `cash_vs_card_split.md`)
- [ ] For Client B — cash through the aggregator as an agent is accounted for specially (see `client_b_yandex_taxi_cash.md`): while there's no own cash register, don't post it — there's an open task to issue correction receipts after it's connected

### C. Aggregator partner act (Yandex Taxi, Wildberries, etc.)

- [ ] Open the document, check the period, counterparty, type (agency / partner / commission)
- [ ] For the aggregator — an agency contract applies; we recognize income per the agent's report (not per the actual receipt of funds)
- [ ] `Purchases → Receipts → Services (act)` or a special agency-contract document in 1C
- [ ] Compare the amount in the act with the receipt in the bank statement (per `client_b_yandex_taxi_cash.md` — cash in the aggregator's acts is shown as an aggregated amount without receipts; it goes into the books separately via the own cash register)

### D. Incoming invoice / UPD

- [ ] `Purchases → Receipts → Services (act)` or `Goods (waybill)`
- [ ] Specify the counterparty (create it in `Counterparties` if the new one isn't in the base)
- [ ] Link it to a contract
- [ ] If on OSNO — account for VAT; if USN — without VAT

## Stage 4. Balance reconciliation

- [ ] `Reports → Turnover and balance sheet → select account and period`
- [ ] The closing balance for account 51 (Settlement accounts) must match the balance in the bank statement
- [ ] The balance for account 50 (Cash desk) — against physical cash / the OFD Z-report
- [ ] On a discrepancy → stop, investigate before continuing (see `anomaly-triage.md`)

## Stage 5. Regulatory operations (month-end close)

After **all** of the month's sources are posted and the balances match:

- [ ] `Operations → Month-end close → select period → run all 6 operations`:
  1. Adjustment of item cost
  2. Calculation of indirect write-off shares
  3. Calculation of expenses reducing USN
  4. Closing of accounts 90/91
  5. USN tax calculation (if quarter/year)
  6. Balance reformation (only in December)
- [ ] If even one operation fails with an error → stop, don't ignore it ("Fix the error in Adjustment of item cost dated 30.04.2026" is a typical `monthly_check.sources` item with status `gap`)

## Stage 6. Recording

- [ ] In `clients_data.json[client].monthly_check.sources[<item>]`:
  - `last` = "posted YYYY-MM-DD"
  - `status` = `ok`
  - If it was `gap` or `wait` — this is a transition to green; the updater records it in `decisions[]` on the next run
- [ ] Entry in `_Planning/SP {Surname}/history.md` (type = `action`)
- [ ] If the posting required manual approval (for example, a non-standard entry) — record it in `_diary/operator_decisions.md` with status `new`; the updater materializes it

## What NOT to do

- **Don't post "because the client said so on the phone"** — only per a document. If there's no document — request it (`client-reminder.md`).
- **Don't skip balance reconciliation** — without reconciliation the posting isn't considered complete.
- **Don't close the month if even one source is `gap` or `wait`** — better to raise a flag than to mask it.
- **Don't work with several 1C:Fresh bases in parallel** (`1c_fresh_one_base_at_a_time.md`) — it exceeds the simultaneous-session limit and you'll have to close them manually.
- **Don't use the "Retail sales report" with cashless acquiring** — this is a typical error (`cash_vs_card_split.md`).
- **Don't post cash for Client B before their cash register is connected** — there's an open task for correction receipts (`client_b_yandex_taxi_cash.md`).
- **Don't edit entries retroactively without a record in `operator_decisions.md`** — the audit trail is lost.
