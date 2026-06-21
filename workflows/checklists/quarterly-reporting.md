# Checklist: quarterly reporting

Applies to Q1 / Q2 / Q3 / Q4. Most of the items are universal; the specific reports depend on the client's tax regime.

## Stage 1. Three weeks before quarter-end — planning

- [ ] Open `Consolidated_calendar_2026.xlsx`, look at the deadlines for all clients this quarter
- [ ] For each client: open the card, see which reports we file
- [ ] Create a "need to obtain from the client" list — add to `request_log.md`
- [ ] Send clients requests for primary documents (per the `data-request-template.md` template)
- [ ] Qualified digital signature (UKEP) — not my zone. If a UKEP question surfaces during document reconciliation (expired / not suitable) — escalate to the operator

## Stage 2. Two weeks before — collecting primary documents

- [ ] For each client, check what arrived and what didn't
- [ ] For what's missing — a repeat request
- [ ] Loaded primary documents — into the client folder, sorted by month
- [ ] Update `monthly_check` in `clients_data.json`
- [ ] Regenerate the dashboards
- [ ] For problem clients — escalate to the manager

## Stage 3. Ten days before — processing

- [ ] Entering transactions into 1C / the accounting system
- [ ] Reconciliation with bank statements
- [ ] Reconciliation with acts from key counterparties
- [ ] Tax calculation
- [ ] Insurance contribution calculation (if there are employees)

## Stage 4. Five days before — preparing the reports

- [ ] USN — USN tax return
- [ ] OSNO — VAT return
- [ ] OSNO — 3-NDFL (if it's year-end)
- [ ] Payroll — RSV, 6-NDFL, EFS-1
- [ ] Statistics — if required by the OKVED code
- [ ] Income and expense ledger — update

## Stage 5. Before filing

- [ ] Reconciliation with the client — show the final figures, get an OK
- [ ] Reconciliation with the supervisor — if the amounts are large or there are non-standard transactions
- [ ] If a UKEP question surfaces during signing — escalate to the operator (she maintains the registry and sends the reports)
- [ ] Prepare tax payment orders — send them to the client for payment (or agree on a schedule)

## Stage 6. Filing

- [ ] Submit the reports through the filing system
- [ ] Wait for the acceptance receipt
- [ ] Wait for the (positive) protocol
- [ ] If rejected — decode the reason, fix it, resubmit

## Stage 7. Archiving

- [ ] Put the return, receipt, and protocol in `_registries/reporting_archive/2026/<client>/<quarter>/<report>/`
- [ ] Update the entry in `clients_data.json` (`monthly_check = ok`)
- [ ] Regenerate the dashboard
- [ ] Record the filing in the client's `history.md`
- [ ] Close the tasks in Finkoper

## What NOT to do

- Do not file a report without reconciling key figures with the client
- Do not try to "fix" the client's UKEP problem yourself — redirect to the operator (she maintains the registry)
- Do not send payment orders on the client's behalf — only preparation; the client pays themselves
- Do not close the quarter in the accounting system if there are unresolved reconciliation discrepancies
- Do not ignore FTS rejection protocols — even if the reason seems "technical", investigate immediately
- Do not file amended returns in a rush — better to go past the standard deadline than to contain an error
