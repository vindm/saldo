# Proposal: deterministic monthly-close pipeline (for review — not built yet)

## Idea
The monthly accounting cycle per client is deterministic and ordered. Today the
plan groups tasks into "waves" by ad-hoc text/`task_type`, which is fragile (the
Cyrillic-key and cross-client-glue bugs we just fixed came from there). Instead,
model the monthly close as a **canonical pipeline of stages**. The stages already
exist as the system's declared **checklists** — we just make the engine use them.

## Stages (ordered) — sourced from the existing checklists
| # | Stage | task_type(s) (from her data) | checklist |
|---|---|---|---|
| 1 | Сбор первички | `primary_collection` | `первичка_месяца.md` |
| 2 | Разноска в 1С | `kudir_posting`, `technical_1c` | `разноска_первички_в_1С.md`, `загрузка_выписки_1С.md` |
| 3 | Закрытие месяца | `month_close`, `period_close` | (регл. операции) |
| 4 | Аудит месяца | `month_audit` | `разбор_аномалии.md` |
| 5 | Расчёт + уведомление + ПП | `pp_to_form`, `notification` | `ПП_на_ЕНП.md` |
| 6 | Подпись / оплата | `pp_sign` | — |

Feeders (parallel inputs, not stages): `bank_check`, `acquiring_reconciliation`,
`ausn_*`, `ofd/kkt_check` — they unblock stages 2–3.

## Data model — derived, nothing invented
No new data. The pipeline is a **VIEW over existing state**:
- A declared config `config/pipelines/monthly_close.yaml` lists the ordered
  stages + which `task_type`s belong to each (the table above). This is declared
  config, like the checklists — not engine logic.
- A client's position = the earliest stage that still has open tasks for the
  current period (`type_specific.period`). Done = stage's tasks all in a terminal
  status. (Both already in `tasks.json`.)

## Two projections of the same data
1. **By stage (waves):** for each stage, the clients with open tasks at that stage
   → one wave. Grouping is by the **canonical stage code**, not text → no dups, no
   Cyrillic-key bugs, no cross-client glue. (Replaces the current text/`task_type`
   grouping for monthly-cycle ops only.)
2. **By client (progress):** each client shows a 6-stage progress strip for the
   period and a deterministic "next action" = the next stage's checklist.

Non-monthly / ad-hoc tasks are unaffected — they stay as today (singles / their
own waves).

## What changes vs. the original (to verify / approve)
- Monthly waves (Сбор первички / Закрытие месяца / Аудит месяца / ПП …) become
  **canonical** — output should match today's waves for those ops, just robust.
  I'll diff against the original to confirm parity.
- The **per-client progress strip** is genuinely **new UI** (additive). Show +
  approve before wiring into a page.

## Open questions for you
1. Stage list/order correct? (6 stages above, feeders separate.)
2. Config location OK: `config/pipelines/monthly_close.yaml`?
3. Per-client progress — where: on the client dashboard, or a new column on the
   plan page? Or skip for v1 and only do the canonical by-stage waves?

## Build plan (incremental, each step verified vs original)
1. Add the stage config + a `task_type → stage` resolver (pure function, no writes).
2. Use canonical stages for monthly-cycle wave grouping; diff waves vs original.
3. (If approved) add the per-client progress projection.
