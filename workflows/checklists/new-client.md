# Checklist: onboarding a new client

## Stage 1. Basic information (obtain from the supervisor / manager)

- [ ] Full name of the sole proprietor (SP)
- [ ] INN
- [ ] OGRNIP
- [ ] SP registration date
- [ ] Primary OKVED + additional ones
- [ ] Registration address
- [ ] Tax regime (OSNO / USN income / USN income-minus-expenses / patent / NPD / a combination)
- [ ] Date of transition to the current tax regime
- [ ] Whether there are employees, how many
- [ ] From which period we take over the service
- [ ] Whether there was bookkeeping before us, in what state it was handed over

## Stage 2. Contacts

- [ ] Name and contact of the SP themselves (phone + email)
- [ ] Authorized person / assistant
- [ ] Convenient communication channel (Finkoper / WhatsApp / Telegram / call)
- [ ] Convenient contact time

## Stage 3. Financial infrastructure

- [ ] Settlement accounts (bank, last 4 digits, currency)
- [ ] Whether there's an online cash register (model, fiscal drive, OFD)
- [ ] Whether there's acquiring (bank, rate)
- [ ] Whether there are corporate cards

## Stage 4. Accounting systems and access

- [ ] Which accounting software (1C, in-house, none)
- [ ] Access to 1C yes/no, through what
- [ ] Access to the FTS personal account
- [ ] Access to the bank client (view-only)
- [ ] Access to the OFD
- [ ] UKEP — issued to whom, validity period, where stored
- [ ] Powers of attorney — to whom, to which bodies, term

## Stage 5. Business specifics

- [ ] What is the main source of income
- [ ] Seasonality
- [ ] Regular counterparties (suppliers, customers)
- [ ] Non-standard transactions (agency, foreign trade, property)
- [ ] Document flow: how they send primary documents, in what form

## Stage 6. Taxes and reporting

- [ ] Which taxes they pay and the payment deadlines
- [ ] Which reports we file
- [ ] Where we file (FTS, social fund, Rosstat)
- [ ] Through which filing system (Kontur.Extern / SBIS / directly)

## Stage 7. Creating in the system

- [ ] Create folder `SP Surname/` in the project root
- [ ] Create `_Planning/SP Surname/` with `client-card.md` (per template)
- [ ] Fill in the card with everything collected
- [ ] Add an entry to `_Planning/_data/clients_data.json`
- [ ] Create `Deadline_calendar_2026.xlsx` or copy it from the template
- [ ] Run `generate.py` — confirm the dashboard is created
- [ ] Add to `request_log.md` rows for what's left to obtain from the client
- [ ] Hand the collected UKEP data to the supervisor (she maintains the registry `UKEP_and_powers_of_attorney.md`)

## Stage 8. First task

- [ ] Check which reports are coming up (per the consolidated calendar)
- [ ] If there's an unclosed period — plan the primary documents

## What NOT to do

- Don't create an entry in `clients_data.json` before at least the basic card fields are filled in (name, INN, tax regime, bank)
- Don't run `generate.py` while the JSON has empty required fields — the dashboard will come out broken
- Don't ask the client everything at once with 50 questions — split it into blocks by checklist stage
- Don't make assumptions about the tax regime, counterparties, or business specifics — only what was explicitly stated or is in the documents
- Don't sign the client up for services/plans without the supervisor's sign-off
