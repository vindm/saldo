# Checklist: monthly primary documents

Applies to the monthly close of primary documents for a client.

## Stage 1. Collecting sources

For each source in the client's `monthly_check` (from `clients_data.json`):

- [ ] Bank statements — for all accounts, for the full month
- [ ] Cash register reports — Z-reports, OFD reports (if there's a cash register)
- [ ] Acquiring reports (if any)
- [ ] Acts with counterparties — for the month
- [ ] Invoices (if on OSNO)
- [ ] UPDs (if applicable)
- [ ] Contracts with new counterparties
- [ ] Documents for the business's personal transactions (from personal cards)

## Stage 2. Completeness check

- [ ] All statements cover the entire month with no gaps
- [ ] No "gaps" in the numbering of acts/invoices
- [ ] All large transactions (>50% of monthly turnover) are confirmed by documents
- [ ] The opening balance of the month matches the closing balance of the previous one

## Stage 3. Processing

- [ ] Entering transactions into 1C / the accounting system
- [ ] Linking documents to transactions
- [ ] Calculating advance payments (USN, patent)
- [ ] Calculating payroll taxes (if there are employees)

## Stage 4. Reconciliations

- [ ] Reconcile account balances
- [ ] Reconcile with key counterparties (if there are suspicions)
- [ ] Check disputed transactions

## Stage 5. Closing

- [ ] Update `monthly_check` in `clients_data.json` (statuses per source)
- [ ] Regenerate the dashboard
- [ ] Record a brief month summary in the client's `history.md`
- [ ] Raise a flag if there are unresolved items

## What often gets missed

- Cash transactions in physical cash (not reflected in the bank)
- Business expenses from personal cards
- Acquiring transactions — receipt amounts ≠ sales amounts (minus the fee)
- Refunds to customers

## What NOT to do

- Don't accept primary documents without checking dates — a frequent problem is "the document is dated last quarter, arrived backdated"
- Don't enter transactions into the books without supporting documents "because the client said so on the phone"
- Don't skip cash transactions just because they're "small"
- Don't close the month if even one source in `monthly_check` has status `gap` or `wait` — raise a flag, don't mask it
