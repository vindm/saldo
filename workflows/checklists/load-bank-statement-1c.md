# Checklist: loading a bank statement into 1C:Fresh

Applies to the monthly loading of a bank statement from a file into the client's accounting system, 1C:Fresh.

**Context:**
- Statements arrive in a batch on the 1st–15th of the following month (`bank_statements_workflow.md`)
- One statement = one settlement account for one calendar month
- Some clients have several settlement accounts — each is loaded separately
- Client banks: T-Bank, Sber, Alfa, Tochka, VTB
- File formats: `.txt` (1CClientBankExchange), `.xml`, `.xlsx`
- 1C is read-only (`safety_rules.md` item 2): the "Load" button is pressed by the operator after my review
- Related to: `posting-primary-docs-1c.md` (Stage 3A), `monthly-primary-documents.md`, `cash_vs_card_split.md`, `1c_fresh_one_base_at_a_time.md`

## Stage 0. Receiving the file

Source:
- Email from the client or from a bank notification — see `email/read_message.md`
- Finkoper (client attached it to a task or chat) — see `finkoper/read_task.md` / `read_chat.md`
- Downloaded manually by the operator (`Downloads/`)

Storage: `_Inbox/<client>/statements/<bank>_<yyyymm>.<ext>` — move from Downloads via the "sort out the downloads" scenario (INSTRUCTIONS.md section 5).

## Stage 1. Identification

Before any checks, fill in the table and show it to the operator:

| Field | Where to get it |
|---|---|
| Client | From the file name / email / chat |
| Bank | From the file name / from the header of the PDF copy / from the details in the file |
| Settlement account (20 digits) | From the statement file (field `SenderAccount` in `.txt`, column in `.xlsx`) |
| Bank BIC | From the file |
| Period (from — to) | From the file |
| File format | `.txt 1CClientBankExchange` / `.xml` / `.xlsx` |
| Encoding (for `.txt`/`.xml`) | Windows-1251 or UTF-8 — otherwise garbled characters |

## Stage 2. File checks BEFORE loading

- [ ] **Account details match the 1C card.** In 1C:Fresh → `Main → Organizations → <SP> → Bank accounts`. Compare the account number (20 digits) and BIC with what's in the file. If the file has an account that isn't in 1C — stop, find out (new account for the client? or wrong client?).
- [ ] **Correct client / correct account.** Especially if the client has several accounts at one bank (T-Bank often has two accounts — main + savings). The details in the file must point unambiguously to the specific account.
- [ ] **Period doesn't overlap with an already-loaded statement.** Open in 1C `Bank and cash desk → Bank statements → filter by organization and account`, look at the last document — its end date ≤ the start date of the new statement.
- [ ] **Opening balance of the new statement = closing balance of the previous one** (for the same account). If there's a discrepancy — stop, investigate (a period may have been skipped / there was a transaction outside the statement).
- [ ] **File opens, not corrupted.** For `.txt` — open in an editor, check readability and encoding. For `.xml` — valid XML. For `.xlsx` — open, check the header and structure.
- [ ] **Total receipts and write-offs from the file vs the total from the PDF statement.** Banks usually export both `.txt`/`.xml` and `.pdf` — the totals must match to the kopeck.
- [ ] **Period completeness.** The first transaction in the file = the first business day of the month (or earlier — carryovers), the last = the last business day. No date "gaps" inside.
- [ ] **Reconcile counterparties by INN against the client card.** From the statement file, extract the list of unique INNs (payers and recipients). Compare with the "Counterparties" / "Objects and contracts" section of the client card. Unfamiliar INNs — flag to the operator in chat: "this INN isn't in the card, who is it?". Especially suspicious are one-off large payments to new counterparties — this is a typical zone for errors and fraud.

**Stage 2 result** — a report to the operator in chat: details matched / not, balances matched / not, totals matched / not, integrity ok / not. If all ✓ — move to Stage 3. If even one ✗ — stop, don't prepare the instruction.

## Stage 3. Instruction to the operator before clicking "Load"

I prepare it step by step (accounting for the one-base rule — `1c_fresh_one_base_at_a_time.md`):

1. Close all other open 1C:Fresh bases.
2. Open the client's base: `<SP Surname>`.
3. Go to: `Bank and cash desk → Bank statements`.
4. Button `Load` (or `MORE → Load from file` — depends on the configuration release).
5. Choose the load format:
   - `.txt` → "1C-Client Bank"
   - `.xml` → "Universal XML exchange"
   - `.xlsx` → "From spreadsheet" (specifying column mapping)
6. Specify the organization: `<SP Surname>`.
7. Specify the bank account: `<20-digit account number>` — **critical** if the client has several accounts.
8. Path to the file: `<full path to the file in _Inbox or Downloads>`.
9. Click "Read" / "Load" (in newer releases — two steps).
10. **After loading, do NOT post documents in bulk.** First hand them over for post-check.

## Stage 4. The operator clicks "Load"

Her action. Meanwhile, I do nothing in this base.

## Stage 5. My post-check via Chrome (read-only)

After loading, I open the base and check:

- [ ] **Number of transactions.** Compare with the number of transaction rows in the source file. They must match.
- [ ] **Total receipts and total write-offs.** Compare with the PDF statement. To the kopeck.
- [ ] **Closing balance = the balance in the bank statement.** In 1C → `Reports → Account 51 turnover sheet → select account and period` → closing balance.
- [ ] **New counterparties.** How many appeared, how many have an INN filled in, how many are empty (a potential problem when posting).
- [ ] **Acquiring — a separate line with the fee broken out?** If the statement has receipts from acquiring / an SBP aggregator / Wildberries, etc. — there must be a separate fee line. If the bank sent a "dirty" amount — flag it (`cash_vs_card_split.md`: for cashless acquiring, do not use a "Retail sales report").
- [ ] **Refunds to customers.** If there are lines marked "refund" — note them so that during posting they aren't counted as income under USN 6%.
- [ ] **Suspicious payments.** Large (>10% of monthly turnover) or with an unclear purpose — list them in chat.
- [ ] **Unposted transactions.** In 1C → filter "Not posted" / "No entries" — collect the list.
- [ ] **Duplicates.** Check whether there are transactions with the same date and amount as in the previous statement (relevant if the periods adjoin).

**Stage 5 result** — a report in chat: everything matched / there are N problems (list them with specifics).

## Stage 6. Posting and balance reconciliation

Next — per `posting-primary-docs-1c.md`:
- Stage 3A — matching transactions to counterparties and cash-flow items
- Stage 4 — balance reconciliation for accounts 51 / 50

## Stage 7. Recording

- [ ] In `clients_data.json[client].monthly_check.sources[statement_<bank>_<yyyymm>]`:
  - `last` = "loaded YYYY-MM-DD, posted YYYY-MM-DD"
  - `status` = `ok` (or `gap`, if there's something unposted / discrepancies)
- [ ] If the client has several accounts — a separate entry per account in `monthly_check.sources`.
- [ ] Entry in `_Planning/SP {Surname}/history.md` (type = `action`): "Loaded statement <bank> <last 4 of account> for <yyyymm>, N transactions, receipts X, write-offs Y".
- [ ] If unusual entries or decisions arose — record them in `_diary/operator_decisions.md` with status `new` (the updater materializes them).
- [ ] Dashboard regeneration — per INSTRUCTIONS.md section 4 (if JSON changed).

## Bank-specific notes

This section is filled in as work happens — we record nuances of specific banks as we encounter them.

- **T-Bank:** _TBD_ (where in the internet bank the export to 1C format is, any nuances with the savings account)
- **Sber (SberBusiness):** _TBD_
- **Alfa (Alfa-Business):** _TBD_
- **Tochka:** _TBD_
- **VTB (VTB-Business):** _TBD_

## What often breaks

- Loaded the statement into the wrong account (when the client has two accounts at one bank) — caught by re-checking the details in Stage 2.
- Duplicate period — caught by the period-overlap check in Stage 2.
- Garbled characters due to wrong encoding — open the file and check BEFORE loading.
- Opening balance didn't match because of a kopeck fee missed last month — investigate before loading the new period.
- Counterparties duplicated (with different INNs / without INN) — after loading, clean up manually in `Counterparties`.
- Acquiring without the fee broken out — the bank sent a "dirty" amount → incorrect income under USN.
- Refund to a customer not marked as a refund → it got counted as income.
- A new counterparty with an unfamiliar INN slipped through without reconciliation — got into the books "as is", then surfaced during reconciliation.

## What NOT to do

- **Do not click "Load" yourself** — it's a write to 1C; per `safety_rules.md` item 2, the operator presses it.
- **Do not load statements for several months in one file** — only month by month, otherwise the regulatory operations get muddled.
- **Do not load without reconciling account details** — "loaded into the wrong account" is the most painful case to untangle.
- **Do not work with two 1C:Fresh bases in parallel** (`1c_fresh_one_base_at_a_time.md`).
- **Do not post documents in bulk before the post-check** — better to catch a problem before posting than to post something erroneous.
- **Do not ignore a balance discrepancy "because it's just kopecks"** — a kopeck today = a ruble in three months that you'll have to hunt down in a rush before reporting.
