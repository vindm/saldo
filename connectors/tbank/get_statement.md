# Atomic skill: get_statement

Generate and download a bank statement for a client's account in T-Bank Business for a period, save it to `<client doc folder>/`, parse Dr/Cr turnover. Replaces waiting for the statement from the client for the direct contour.

> **Source of truth for the algorithm:** this file + the domain `README.md`. When the T-Bank UI changes, fix both places.
> **Account requisites** for the client — `state/accounts.json:bank_accounts[]` (for direct clients they live in `clients/direct/SP <Surname>/state/`).

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `client_id` | string | **required** (`<client_id>` / `<client_id>` / `<client_id>` / `<client_id>` …) |
| `period_start` | date | **required** (first day of the month) |
| `period_end` | date | **required** (last day of the month) |
| `format` | enum | `excel` (for parsing) \| `pdf` (archive). Default `excel` |
| `output_folder` | string | `<client doc folder>/<client>_<period>/` |

## Precondition

- The client is in the applicability table in `README.md` (the company is visible in the switcher).
- Claude in Chrome is authenticated in T-Bank (`business.tbank.ru`). On the first entry from the MCP tab a login wall is possible — (ask the operator to open T-Bank once in a regular tab, then retry).
- The `output_folder` exists.

## Algorithm

### Step 0. ⚠️ Confirm and, if necessary, switch the company (CRITICAL)

⚠️ The header switcher is finicky (React doesn't always catch a synthetic click). **A reliable switching method is via the all-companies page:**

1. Open `https://business.tbank.ru/sme/all-companies` (redirects to cash-management with the list of all companies).
2. The companies there are real button-cards (`button[automation-id=single-resource-large-card]`), click deterministically. Click the required client's card (the client=<client_id>, the client=<client_id>, the client=<client_id>, the client=<client_id>).
3. Wait for the reload (~3 sec). Reconcile the active company name in the header with the target `client_id`. **Matches — continue; no — repeat.** T-Bank has no stable per-company URL (switching is session-based), so always via all-companies + check.
4. LLC "[redacted]" — without a separate decision from the operator, do not touch the data (see `README.md` applicability table).
5. When the work is finished, restore the active company to the one the operator had, the same way. **And close the MCP tabs I opened** (`tabs_close_mcp`) — don't leave junk behind.


### Step 1. Open the new-statement form

1. **Actions → "Create statement"** (or go to `https://business.tbank.ru/sme/documents/statements/order`).
2. Type: **One-time**.

### Step 2. Parameters

1. **Bank account** — select the account. ⚠️ Some direct clients have SEVERAL bank accounts. For the **full KUDIR/income, generate the statement for EACH active bank account** from `accounts.json:bank_accounts[]` (where `closed_at=null` and purpose starts with "bank account"), not just `is_primary`. Personal accounts (40817...) and overnight/deposits are not for the KUDIR. For a point question ("did the payment go through") the relevant account is enough.
2. **Period** — `period_start` … `period_end`.
3. **Statement formats** — mark per `format` (Excel for parsing / PDF for archive). Both are possible.
4. E-mail — **leave blank** — we'll download the statement from history.

### Step 3. Generate and download

1. Click **"Create"**. (This is a document artifact, not a payment — allowed.)
2. Go to the statement history `https://business.tbank.ru/sme/documents/statements`, wait for readiness (usually quick), download the file to Downloads.
3. Move it to `output_folder` (canonical download pipeline — as in: access Downloads via direct path).

### Step 4. Parse turnover

1. Open the Excel/PDF via Read/bash.
2. Extract: period, account no., **Dr (debits) and Cr (credits) turnover**, the list of operations (date, counterparty, INN, amount, purpose).
3. **Ignore the closing balance** — only the period's turnover matters.
4. For typical postings, check against (utilities→60, SBP to own card→84, bookkeeping services from [redacted]→60).

### Step 5. Return the result

```
result = {
  client_id, period_start, period_end,
  account, debit_total, credit_total,
  operations: [{date, counterparty, inn, amount, direction, purpose}],
  file_path
}
```

## After the skill

- The file stays in `<client doc folder>/` for posting (the operator moves it into `SP <Surname>/`).
- Updating `monthly_check` / `state` by turnover is a separate step via the chain state→mental_model→generate (with approval per `security_rules.md` §5b).
- For AUSN clients (see `state/regime.json`): the statement = reconciliation with what the bank already reported to the FTS, **not** the basis of the KUDIR.

## Security

- Only generating/downloading a statement. **NEVER** click "Create payment/transfer", "Issue invoice", templates, e-signature.
- An unexpected confirmation window — stop, screenshot, ask the operator.
