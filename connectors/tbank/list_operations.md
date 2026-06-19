# Atomic skill: list_operations

Read a client's operations **directly from the screen** in T-Bank Business (without generating a document) — for point questions: "did the payment from X go through", "what happened yesterday", "is there a credit of N rubles". Lighter and faster than `get_statement`, and leaves no document artifact in the bank.

> When a file is needed (archive / posting / month-end close) — that's `get_statement`. `list_operations` — for a quick look.

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `client_id` | string | **required** |
| `direction` | enum | `all` \| `debit` (debits) \| `credit` (credits) |
| `since` / `until` | date | period (opt.) |
| `query` | string | search by counterparty/purpose/account/amount (opt.) |
| `limit` | int | `30` |

## Precondition

- The client is in the applicability table in `README.md`.
- Claude in Chrome is authenticated in `business.tbank.ru`.

## Algorithm

### Step 0. ⚠️ Confirm and, if necessary, switch the company

Reliable method (the header switcher is finicky): open `https://business.tbank.ru/sme/all-companies` → click the required client's button-card (`button[automation-id=single-resource-large-card]`) → wait ~3 sec → reconcile the name in the header with `client_id`. Matches — continue, no — repeat. Do not touch LLC "[redacted]" without the operator's decision. Full procedure — `get_statement.md` Step 0.

### Step 1. Open operations

1. `https://business.tbank.ru/sme/dashboard` → **"Operations"** block.
2. Filter by `direction`: tabs `All / Debits / Credits`.
3. Period: "All time" → set `since`…`until` if specified.
4. Search: enter `query` in the "Counterparty, purpose, account or amount" field if specified.

### Step 2. Read the operations

Read the visible rows (date, counterparty, amount ±, purpose, account), scrolling as needed up to `limit` or the end of the period.

### Step 3. Return the result

```
result = {
  client_id, filters: {direction, since, until, query},
  operations: [{date, counterparty, amount, direction, purpose}],
  count
}
```

## Security

- Only reading the operations screen. Do not open an operation card for editing, do not click "Repeat payment", "Create payment/transfer".
