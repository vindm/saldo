# Composite skill: incremental_update (Alfa)

Pull new operations across all Alfa clients since last_run, append to the daily report, update state. Pipeline over the atomic `list_operations`. Ready for scheduling.

## Parameters
| Parameter | Type | Default |
|---|---|---|
| `since` | datetime | `last_run` (domain heartbeat) |
| `clients` | list | all ✅ from `README.md` (<client_id>, <client_id>, <client_id>) |

## Algorithm
1. List of Alfa clients from `README.md`.
2. For each: Read `list_operations.md`, run `client_id=<current>, since=since, direction=all`. ⚠️ Step 0 (company switching) is mandatory between clients.
3. Diff against the previous snapshot; run through, `contractor_debt_not_our_zone`, `silence_check_payment_first`.
4. Append a summary to the daily report; significant items — into state via the chain (`security_rules.md` §5b); update the heartbeat.
5. Result: `{since, per_client:[{client_id,new_ops_count,notable}], flags}`.

## When to call which
| Trigger | Skill |
|---|---|
| "did the payment / operations go through for X on Alfa" | `list_operations.md` |
| "need an Alfa statement for X for <month>" | `get_statement.md` |
| "check Alfa" / morning run | `incremental_update.md` |

## Security
Inherits `README.md` and `security_rules.md`. Read only; multi-company guard on every client.
