# Checklist: preparing a payment order for the single tax payment (ENP)

Applies to preparing a payment order for USN / patent regime taxes / sole proprietor's own insurance contributions in 1C:Fresh. Per `workflow_responsibilities.md`, this is the bookkeeper's zone up to the moment "payment order status in 1C = in progress"; after that, the client signs and pays.

## Stage 1. Calculating the amount

- [ ] Open the client's base in 1C:Fresh (per `1c_fresh_one_base_at_a_time.md` — close the previous base)
- [ ] **USN advance payments and tax:** `Reports → USN reporting → Tax calculation` → select period (Q1, H1, 9M, year)
- [ ] **Patent:** amount from the client card (`client-card.md`, "Patent" section, payment schedule)
- [ ] **Sole proprietor's own insurance contributions:** fixed part for the year + 1% over 300,000 RUB (accounting for proportionality if the SP has been registered less than a year — and likewise for other newly registered SPs)
- [ ] **IMPORTANT:** if the calculated USN advance = 0, the payment order is **not prepared** (per `notification_zero_advance.md`). Mark the item in the JSON as `done` with status "advance = 0", do not create a payment order

## Stage 2. Checking the budget classification code (KBK) and deadline

- [ ] **KBK (for 2026):**
  - USN income 6% (object "income") → `18210501011011000110`
  - Patent (PSN) → `18210504020021000110` (for crediting to the municipal district budget; verify against the client card — for the client 2026 it is specified this way)
  - Sole proprietor's own insurance contributions → single tax payment (ENP) via the unified KBK `18201061201010000510` (for 2026 — verify current value at `nalog.gov.ru`)
- [ ] **Payment deadline:**
  - USN Q1 2026 — 28.04.2026
  - USN H1 2026 — 28.07.2026
  - USN 9M 2026 — 28.10.2026
  - USN annual 2025 — 28.04.2026 (SP without employees)
  - Patent 2026 (the client) — 12,957 RUB by 02.04.2026 + 25,913 RUB by 28.12.2026
  - SP insurance contributions for 2026 — fixed part by 28.12.2026; 1% over 300k by 01.07 of the following year
  - If the deadline falls on a non-working day, it moves to the next business day
- [ ] **Bookkeeper's internal deadline** = the statutory deadline minus 5 calendar days (shifting back off non-working days). Both the message to the operator and the client's signature must fit within this

## Stage 3. Preparing the payment order in 1C

- [ ] `Bank and cash desk → Payment orders → Create → Tax payment`
- [ ] **Recipient:** Federal Treasury of the RF (single tax payment, ENP). Details are filled in automatically
- [ ] **Amount:** from Stage 1
- [ ] **KBK:** from Stage 2
- [ ] **Payment purpose** — per template:
  - USN: "Single tax payment. Advance payment for USN for {period} {year}"
  - Patent: "Single tax payment. PSN tax under patent No. {patent number} for {period}"
  - Insurance contributions: "Single tax payment. Sole proprietor's own insurance contributions for {year}, fixed part" or "...1% over 300,000 RUB for {year}"
- [ ] **Payment order date:** the date of preparation (not the payment date — the client sets that in their online banking)
- [ ] **Settlement account:** the client's main account from the card (field `account`)
- [ ] Save the payment order — **do NOT post.** Per `safety_rules.md §2`, writing to 1C is done by the operator manually; I prepare the draft, she posts it

## Stage 4. Status "In progress"

- [ ] Move the payment order to status "In progress" — this is the readiness signal per `workflow_responsibilities.md`
- [ ] Optionally — a short message to the operator in the Finkoper chat of the corresponding task: "Payment order for {client} {period} is ready, status 'in progress'" (via approval and an explicit "send")
- [ ] If the payment order parallels a notification of calculated taxes — make sure the notification is also prepared (per `workflow_responsibilities.md` this is part of the bookkeeper's zone: "Reports → Regulated reports → Notifications")

## Stage 5. Reconciliation and message to the client

- [ ] Prepare a short message to the client (via the operator or directly — per the client's practice) with the final amount and payment deadline
- [ ] Template (via approval):
  ```
  Hello, [name]!
  I've prepared a payment order for {tax/contribution} for {period}:
  Amount: {…} RUB
  Payment deadline: by {date}
  KBK: {…}
  Purpose: {…}
  Pay through your bank client (ENP).
  ```

## Stage 6. Recording

- [ ] In `clients_data.json[client].prep_done_2026`, update the corresponding key:
  - `pay_q1_2026`, `pay_h1_2026`, `pay_9m_2026`, `pay_2026`, `pay_strakhi_2026` — value `true` (or `"prepared"` if we adopt such semantics)
- [ ] Entry in `_Planning/SP {Surname}/history.md` (type = `action`)
- [ ] If `clients_data.json` changed — the updater will pick it up on the next run, the dashboard regenerates
- [ ] Close the corresponding task in Finkoper (if any) after confirmation from the operator

## What NOT to do

- **Do not sign with the digital signature** (per `safety_rules.md §6 and §7`) — that's the operator / client.
- **Do not send the payment on the client's behalf** — the client does it themselves through their own online banking.
- **Do not prepare a payment order when the USN advance is zero** — per `notification_zero_advance.md`.
- **Do not use KBKs from prior years** — every year, verify the current KBK at `nalog.gov.ru` or in the client card.
- **Do not skip the internal-deadline shift** — 5 calendar days before the statutory deadline, otherwise the client won't have time to sign.
- **Do not open multiple 1C:Fresh bases at once** (`1c_fresh_one_base_at_a_time.md`) — exceeds the session limit.
