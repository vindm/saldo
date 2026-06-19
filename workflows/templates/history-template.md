# Template for an entry in a client's `history.md`

> Source of truth for the chronology of work with the client. Each entry — a short factual note, accumulating by date. Doesn't duplicate primary documents (those are in the client folder), doesn't duplicate the JSON (that's in `clients_data.json`).

## Entry format

```
## YYYY-MM-DD — short title (event type)

**Type:** request | reply | action | decision | fact | reconciliation
**Source:** link to the Finkoper task / email / document / entry in `operator_decisions.md` (if any)
**What happened:** 1-3 lines, factual.
**What was done / what's planned:** 1-2 lines.
**Files:** if attached — path in `WORK/SP <Surname>/...`
```

## Event types

- **request** — we requested something from the client / supervisor / counterparty / government body
- **reply** — a reply to our request was received
- **action** — we performed an action (sent, posted into 1C, prepared a document)
- **decision** — an operational decision was made for the client (with a reference to an entry in `operator_decisions.md`)
- **fact** — an external event (a change of details, a change of contact person, new primary documents)
- **reconciliation** — the state of accounts / receivables / reporting as of a date

## When to write

Per Step 7 item 1 of `INSTRUCTIONS.md` — after closing each task for a client, as a separate approval.

## Examples

```
## 2026-05-14 — Package prepared for sending to the client (action)

**Type:** action
**Source:** client-card.md, "Specifics" section
**What happened:** Placed 4 PDFs in the `new for sending/` folder: the partner act [redacted] for April 2026, two reconciliation acts dated 08.05.2026 (XXAR-1, XXAR-2), a consolidated reconciliation act for Q1 2026 on the aggregator's agent reports.
**What was done / what's planned:** Awaiting actual sending to the client.
**Files:** `WORK/SP Client B/new for sending/`
```

```
## 2026-05-16 — Closing task #[redacted] OFD/cash (decision)

**Type:** decision
**Source:** `_diary/operator_decisions.md`, entry 2026-05-16 ~10:00; supervisor DM 15.05.2026 15:01
**What happened:** On Finkoper task #[redacted] a decision was made: we wait for the client to connect a cash register, after which — a separate task to issue receipts for prior-period cash revenue (≈ [redacted] RUB).
**What was done / what's planned:** Task closed in Finkoper 16.05 07:30. The trigger to open the future task — the cash register appearing on kkt.nalog.gov.ru.
```
