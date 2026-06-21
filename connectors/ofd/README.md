# `ofd` domain skills

> Working with Platforma OFD (https://lk.platformaofd.ru). Checking clients' cash operations via the Z-Report — formalized from.
>
> **These skills are invoked by:**
> - Me in a session — on the operator's trigger ("check cash for X over <month>", "month-end close — is an OFD report needed")
> - The checklist `monthly_primary_docs.md` (if applicable for the client) — the Z-Report is expected as one of the sources
> - The morning daemon does NOT invoke these skills (a one-off operation at month-end close, not a daily sweep)

## Skills

| File | Type | What it does |
|---|---|---|
| [`check_z_report.md`](check_z_report.md) | atomic | Download the OFD Z-Report for a period for a client, parse the "Cash revenue" column, return a decision: post into 1C or not |

**For later (potential extensions, P5):**
- `list_kkts.md` — get the client's list of cash registers from the Platforma OFD account
- `check_kkt_status.md` — check a cash register's status on `kkt.nalog.gov.ru` (for a client registering a cash register)
- `compare_periods.md` — comparison of cash by month (for anomalies: "in March it was 0, in April 200k — what happened?")

## Applicability — resolved from state (not hardcoded)

Applies to clients that have an online cash register. Resolve at runtime from `state/accounts.json:kassas[]` (presence of a registered kassa / OFD provider).

**Principle:** if a client has no online cash register — the Z-Report is not needed; if they do — check every month. Cashless (card/SBP via acquiring) reaches the books via bank statements, not via the OFD report.

## Relation to `cash_vs_card_split` and monthly_check

For a client with an online cash register and acquiring, income reaches the books via two paths:

- **Cashless payments** (card/SBP via acquiring) → bank statements → NOT via the OFD report
- **Cash payments** → issued at the cash register → into OFD → into 1C via a "Retail Sales Report" (Cash register → Cash operations)

The Z-Report gives a summary specifically for cash — that is what is needed to decide "post the OFD report into 1C or not".

In `monthly_check.sources[i]` for clients with a cash register, a line of the following form is expected:
```json
{
  "title": "OFD report (Z-Report) for <month>",
  "status": "check" | "ok" | "gap",
  "decision": "needs_1c_posting" | "not_needed",
  "cash_total": 0 | <number>,
  "last_check_date": "YYYY-MM-DD"
}
```

After `check_z_report.md` runs — the updater (per T3, a new file) proposes a patch updating this line.

## Invocation format

```
1. Read `connectors/ofd/check_z_report.md`. Execute:
   client_id = "<client_id>"
   period_start = "2026-04-01"
   period_end = "2026-04-30"
   output_folder = "<client doc folder>/"  (the operator will later move it to a client/)
   Get `result`: cash_total, sessions[], kkts[], output_decision.

2. If result.cash_total > 0 — flag for the operator: "Needs to be posted into 1C via Cash register → Cash operations".
   If result.cash_total == 0 — the updater will close the line as "Not required ✓".
```

## Security

- Platforma OFD (`lk.platformaofd.ru`) — **read only**. Allowed: opening pages, selecting report parameters, clicking "Generate report", downloading xlsx.
- Never: do not click buttons that change cash register settings, do not unlink registers, do not change the list of stores, do not click "Block", "Delete".
- The login to Platforma OFD is under the operator's account. All actions are visible in the OFD log as the operator's actions.
- If an unexpected dialog appears on the page ("Confirm the action", "Your correction receipt…") — stop, screenshot, ask the operator.

## Relation to other skills and domains

- **`connectors/finkoper/`** — if a task "OFD report for the month" arrives in Finkoper, we respond to it by invoking `check_z_report.md`.
- **`connectors/updater/`** — after the Z-Report is downloaded and moved into the client's folder, the updater on T3 (a new primary-documents file) will propose a patch into `monthly_check.sources[i]`.
- **`connectors/analytic/`** — R2 (reassessment of anomalies) may use the Z-Report result if the client had an active anomaly "no primary documents for the cash register for the month".

## History

- **XXXX-05-16** — formalized from (created 2026-05-10) as part of P4-ofd_z_report.
- **Source of truth for the algorithm:**. When Platforma OFD's rules change (UI, column names, sections) — fix both places.

---

_Folder created 2026-05-16 as part of P4. Formalization of the "OFD Z-Report" knowledge from memory → reusable infrastructure._
