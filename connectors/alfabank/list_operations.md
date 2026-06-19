# Atomic skill: list_operations (Alfa)

Read a client's operations from the screen (Operations Feed) without generating a document — for point questions ("did the payment go through", "what came in yesterday").

## Parameters
| Parameter | Type | Default |
|---|---|---|
| `client_id` | string | **required** |
| `direction` | enum | `all` \| `in` (incoming) \| `out` (outgoing) |
| `since`/`until` | date | period (opt.) |
| `query` | string | search (counterparty/INN/BIC/purpose/amount) |

## Algorithm
### Step 0. ⚠️ Confirm/switch the company
As in `get_statement.md` Step 0 ("Companies" switcher → card → name check).

### Step 1. Operations Feed
- Left menu **"Operations Feed"**. Filters: Incoming/Outgoing (`direction`), period (`since`…`until`), search (`query`).

### Step 2. Read
- Read the visible operations (date, counterparty, amount ±, purpose, account).

### Step 3. Result
```
result = {client_id, filters, operations[], count}
```

## Security
Read only. Do not open a payment for repeat/edit, do not click "Create payment".
