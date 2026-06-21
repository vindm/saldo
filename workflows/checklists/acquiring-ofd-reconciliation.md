# Acquiring reconciliation: cash register ↔ OFD Platform ↔ bank ↔ 1C

Apply monthly at month-end for clients with an online cash register and acquiring. Current coverage — only the client (2 cash registers, T-Bank acquiring, account <redacted>). As other clients acquire cash registers/acquiring — expand the coverage.

## Why

To verify that **every cashless transaction through acquiring** went through the full cycle:

```
customer pays by card
     ↓
the acquirer terminal approves (response code 000)
     ↓
the cash register forms a fiscal document → OFD → FTS
     ↓
the bank credits the aggregated amount to the settlement account (T+1)
     ↓
1C posts the credit from the statement
```

If the chain breaks at any step, a discrepancy forms. The most dangerous case — when **the money is in the bank but there's no fiscal receipt in the OFD** (a violation of part 1, Art. 1.2 of 54-FZ → part 4, Art. 14.5 of the Code of Administrative Offenses). Without regular reconciliation, such failures are only discovered upon an FTS claim.

## What to collect (3 sources)

| Source | Where to get it | What's needed |
|---|---|---|
| **OFD Platform** | lk.platformaofd.ru → Reports → Receipt feed → period "month" → xlsx | All receipts for the month with fields: date/time, RNM, FD, settlement type, cash, electronic, total, FTS status |
| **Bank statement** | 1C (Bank → Bank statements → period) or T-Bank personal-account export xlsx | All acquiring credits (operation type "Receipt by payment cards" / "Crediting of funds via acquiring terminals") + acquirer fees for the month |
| **Cash register personal account** (opt.) | the cash register vendor's personal account → Receipts → period | A reconciliation source in case of an OFD↔bank discrepancy — it shows the layer of "local" cash-register records that may not have reached the OFD |

## Reconciliation algorithm

### Step 1. OFD amount for the month

In the OFD export, filter `Settlement type = Receipt`, `FTS status = Accepted`, and sum the **"Electronic"** column (cashless).

Group by date — get a "day → cashless amount per OFD" table.

### Step 2. Acquiring amount per the bank for the month

In the statement (or 1C), filter receipts from the acquirer bank with the purpose "Crediting of funds via acquiring terminals" (or similar). Group by date — get a "day → bank credit amount" table.

Account for **T+1**: the bank credits the receipt the next business day. That is, `Σ OFD 07.05` = `Σ bank 08.05` (adjusted for the minus acquirer fee, which goes as a separate line the same day).

### Step 3. Reconciliation

Compare month by month:

```
∑ OFD electronic for the month (receipts, accepted by FTS)
       =?=
∑ bank acquiring credits for the month (with the T+1 adjustment at month boundaries)
```

Permissible delta = 0. If ≠ 0 — investigate.

### Matrix of 4 discrepancy scenarios

| OFD | Bank | Cash register | Scenario | What to do |
|---|---|---|---|---|
| ✅ yes | ✅ yes | ✅ yes | **OK** | Nothing |
| ❌ no | ✅ yes | ✅ yes | **Cash register didn't transmit the FD** (the client incident, 4400 on 07.05.2026) | Correction receipt "Receipt" for the same amount on the same register → notice to the FTS per the note to Art. 14.5 of the Code of Administrative Offenses |
| ✅ yes | ❌ no | ✅ yes | **Stuck acquirer transaction** | Request the transaction status from the acquirer bank; on reverse — a receipt-refund |
| ✅ yes | ✅ yes | ❌ no | **Cash register worked offline / the record was lost locally but reached the OFD** | Cross-check against the cash-register logs; usually safe (the fiscal document exists) |
| ❌ no | ❌ no | ✅ yes | **Test transaction / reversal** | Clarify with the client; doesn't go into the books |

### Step 4. Cross-check with 1C

In 1C (Bank → Bank statements → period), the "Receipt by payment cards" / "Acquiring credit" amount for the month = the amount from the bank. If the statements are loaded into 1C via 1C.Direct (the client — since 23.05.2026) — they usually match, but verify.

## Artifacts after reconciliation

After each monthly reconciliation, record:

1. **In the client's `state/financials.json`** — add an entry to `reconciliations[]` (a new field; on first use, register it in `state_schema_extensions`):
   ```json
   {
     "period": "2026-05",
     "type": "acquiring_reconciliation",
     "ofd_total_electronic": <number>,
     "bank_acquiring_total": <number>,
     "delta": <number>,
     "status": "ok" | "incident",
     "incident_ref": "<link to the task>" (if incident)
   }
   ```
2. **In `_diary/operator_decisions.md`** — a short entry: "Acquiring reconciliation <client> for <month>: OK / discrepancy X → task Y".
3. If it's an incident — open a separate track in `state/tasks.json` with type `investigation` (like `client_a_acquiring_diff_4400_07may` today).

## Incident sample — the client, 4,400 RUB, 07.05.2026

See files:
- `<client doc folder>/client_a_<redacted>/` — 4 photo attachments from the client (T-Bank slip, Z-report, receipt card from the cash register)
- `a client/Notice_FTS_non-application_of_cash_register_07.05.2026.docx` — a sample notice to the FTS per the note to Art. 14.5 of the Code of Administrative Offenses
- `a client/Notice_FTS_non-application_of_cash_register_07.05.2026_README.md` — instructions for the notice
- OFD export: `<redacted>__2026__05__01__2026__05__25.xlsx` (in outputs, a copy in `a client/` as a result of the reconciliation)

Reconciliation figures for May 2026 (excerpt):
- 07.05 per OFD (electronic): 1,800 + 2,800 = 4,600 RUB
- 08.05 in the bank (acquiring): 9,000 RUB
- Delta: 9,000 − 4,600 = **4,400 RUB** ← a missing FD; the receipt 07.05 00:04 is visible in the cash register, but not in the OFD

## When to apply

| Trigger | Action |
|---|---|
| Month-end close for the client | Reconciliation is mandatory; result — into `state/financials.json` + `_diary/operator_decisions.md` |
| New OFD report received from the client / supervisor | Run the reconciliation immediately |
| Client complaint "I don't see the payment in the register/bank" | Targeted reconciliation by day/amount |
| Another team client acquires a cash register + acquiring | Expand coverage, add to |

## Related documents

- Memory: `monthly_acquiring_reconciliation.md` (project)
- Memory: `cash_vs_card_split.md` (1C posting rules — it explains why the OFD report isn't needed for posting cashless income; here — why it IS needed for **monitoring** 54-FZ compliance)
- Memory: `bank_statements_workflow.md` (statements arrive in a monthly batch)
- Memory: `ofd_z_report_workflow.md` (separately — the cash Z-report)
- Skill: `_system/skills/ofd/check_z_report.md`
