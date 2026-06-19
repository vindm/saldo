# Composite skill: incremental_update

Pull new operations across **all** T-Bank clients since the previous run, append to the daily report, update state. Pipeline over the atomic `list_operations`. Ready to run on a schedule (morning run) and on the operator's "check T-Bank" trigger.

> "One skill — several executors" architecture: in a session a trigger calls me, the daemon/schedule calls this same composite. See memory `sync_protocol`, `use_system_data_by_default`.

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `since` | datetime | `last_run` (from the domain heartbeat) |
| `clients` | list | all from the applicability table in `README.md` |

## Algorithm

### Step 1. List of T-Bank clients

Take `clients` (default — all ✅ from `README.md`: client_d, client_e, client_f, client_g, + the clarified 5th).

### Step 2. For each client

For each `client_id`:

1. Read `connectors/tbank/list_operations.md`. Run:
   - `client_id = <current>`
   - `since = since`
   - `direction = all`
   - ⚠️ Step 0 (company confirmation) is mandatory inside `list_operations` — between clients we always switch the company and re-check.
2. Collect new operations (those that were not in the previous snapshot).

### Step 3. Diff and classification

- New credits / debits relative to the previous snapshot.
- Run through memory `typical-postings-bank-statements` (typical postings), `contractor_debt_not_our_zone` (a missed payment by a tenant/buyer is not flagged), `silence_check_payment_first` (client silence ≠ non-payment — first check the fact of payment here).

### Step 4. Record

- Append a summary to the domain's daily report (with an increment marker).
- Update the client's state for significant facts via the chain state→mental_model→generate (approval per `security_rules.md` §5b; entries in `operator_decisions.md` with status `новое` ("new") = approval).
- Update the domain's heartbeat / `last_run`.

### Step 5. Return the result

```
result = {
  since,
  per_client: [{client_id, new_ops_count, notable: [...]}],
  flags: [...]   # what to surface to the operator
}
```

## When to call which

| Trigger | Skill |
|---|---|
| "did the payment from X go through for <client>" / "what about operations" | `list_operations.md` (atomic) |
| "need a statement for <client> for <month>" | `get_statement.md` (atomic) |
| "check T-Bank" / morning run | `incremental_update.md` (this one) |

## Security

Inherits `README.md` §Security and `security_rules.md` §11. Read only; multi-company guard on every client.
