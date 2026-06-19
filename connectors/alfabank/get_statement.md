# Atomic skill: get_statement (Alfa)

Generate and download a bank statement for a client's account in Alfa-Business for a period → `_Inbox/` → parse Dr/Cr turnover. Replaces waiting for the statement from the client for the direct contour.

> Account requisites — `state/accounts.json:bank_accounts[]`. UI and applicability — the domain `README.md`.

## Parameters
| Parameter | Type | Default |
|---|---|---|
| `client_id` | string | **required** (`client_a`/`client_b`/`client_c`) |
| `period_start`, `period_end` | date | **required** |
| `format` | enum | `excel` (parse) \| `pdf` (archive) |
| `output_folder` | string | `_Inbox/<client>_<period>/` |

## Precondition
- Client is in the applicability table in `README.md`.
- Claude in Chrome: open `https://link.alfabank.ru/dashboard`. If bounced to `id.alfabank.ru` — repeat the navigate (cookie isolation, `mcp_chrome_cookie_isolation`). Do NOT log in yourself.

## Algorithm

### Step 0. ⚠️ Confirm/switch the company (CRITICAL)
1. Read the active company name (header, top right).
2. Reconcile with `client_id`. If it doesn't match — click the active company name → "Companies" panel → click the required client's card → wait ~3 sec → re-read the name. Matches — continue, otherwise stop.
3. When finished, restore the active company to the one the operator had. **And close the MCP tabs I opened** (`tabs_close_mcp`) — memory `close_browser_tabs_after_use`.

### Step 1. Open the statement
- Quick action **"Download statement"** or menu **"Statement"**.

### Step 2. Parameters
- Account — the bank account per `accounts.json` (`is_primary`); period `period_start`…`period_end`; format per `format`.

### Step 3. Generate and download
- Generate → download the file to Downloads → move it to `output_folder` (see `downloads_mount_access_pattern`).

### Step 4. Parse
- Extract **Dr/Cr** turnover + operations (date, counterparty, INN, amount, purpose). Ignore the closing balance (`bank_balances_not_our_zone`). Typical postings — `typical-postings-bank-statements`.

### Step 5. Result
```
result = {client_id, period, account, debit_total, credit_total, operations[], file_path}
```

## Security
Only generating/downloading a statement. NEVER — "Create payment", "Import payments", "Sign", "Send". An unexpected window — stop, ask the operator.
