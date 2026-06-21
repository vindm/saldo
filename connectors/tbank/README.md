# Skills for the `tbank` domain

> Working with T-Bank Business (https://business.tbank.ru) via Claude in Chrome. Direct access to the bank accounts of **direct-contour** clients — we pull statements and operations ourselves, without waiting for the client to send a statement.
>
> **Who calls these skills:**
> - Me in a session — on the operator's trigger ("T-Bank statement for X for <month>", "what about operations for X on T-Bank")
> - Daemon / schedule — the composite `incremental_update` (pull new operations across all T-Bank clients)
> - Checklist `monthly_primary_docs.md` / `quarterly_reporting.md` — the T-Bank statement as the source of turnover for direct clients

## ⚠️ Key difference from other banks

`bank_statements_only_main_vtb` (Alfa/T-Bank/Sber "automatically") — that's about the **team contour in 1C:Fresh**, where banks flow into 1C themselves. Here we mean the **direct contour**: there is no auto-feed into 1C, so direct access to T-Bank is our primary channel for obtaining turnover, not a duplicate.

**For direct clients on T-Bank we pull the statement ourselves before month-end close — waiting for the statement from the client is cancelled** (the operator's decision 2026-06-06, see `tbank_data_source.md`).

## ⚠️ Risk #1 — multi-company

A single operator login sees several SPs (company switcher at the top right). **It's easy to read the wrong client.** Every skill MUST, as its first step, confirm the active company and reconcile it with the target `client_id`. On a mismatch — switch and re-check; until then, do not read anything as client data.

## Skills

| File | Type | What it does |
|---|---|---|
| [`get_statement.md`](get_statement.md) | atomic | Generate and download a statement for a period by client (Excel/PDF) → `<client doc folder>/` → parse Dr/Cr turnover |
| [`list_operations.md`](list_operations.md) | atomic | Read operations from the screen (without generating a document): filter Debits/Credits/period/search |
| [`incremental_update.md`](incremental_update.md) | composite | Across all T-Bank clients, pull new operations since last_run, append to the daily report, update state |

**For later (potential extensions):**
- `get_requisites.md` — a client's account requisites (Requisites)
- `morning_full_scan.md` — full sweep of all T-Bank clients (if we switch to daily collection)
- `compare_periods.md` — comparing turnover by month for anomalies

## Applicability — resolved from state (not hardcoded)

Applies to direct-contour clients whose company is visible in the T-Bank switcher under the operator's login. Resolve at runtime:
- which clients are direct-contour → roster `clients_index.json` (`group`);
- each client's account(s) (incl. AUSN flag, several accounts, T-Kassa) → `state/accounts.json:bank_accounts[]`/`kassas[]`.

**Principle:** the skill applies only to clients whose company is actually visible in the switcher. If the company is not there — stop, escalate to the operator (access not granted). A non-SP legal entity in the switcher that is not in the roster — do not post its data until the operator clarifies its status.

## UI map (verified live 2026-06-06)

- **Company switcher** — top right, the active company name (e.g. "a client"). Full list (verified 2026-06-06): a client, a client, a client, a client, LLC "[redacted]".
- **Switching procedure (RELIABLE, verified 2026-06-06):** the header switcher is finicky (React doesn't always catch a synthetic click) — switch via `https://business.tbank.ru/sme/all-companies`: there, the companies are real button-cards (`button[automation-id=single-resource-large-card]`), click a card → reload ~3 sec → verify the name in the header. There is no stable per-company URL (switching is session-based), always all-companies + check. Don't spawn parallel tabs.
- ⚠️ A client may have **several bank accounts**. For the statement, take `is_primary` from `accounts.json` or the explicitly specified account; on ambiguity — ask the operator.
- Operations (for reading from the screen): **Main** → "Operations" block, filters `All / Debits / Credits`, period "All time", search "Counterparty, purpose, account or amount".
- Statement: **Actions → "Create statement"** or **Documents → Statements**. List: `/sme/documents/statements`. New-statement form: `/sme/documents/statements/order`.
- "New statement" form: type `One-time` / `Template` → select `Bank account` → `Period` → `Statement formats` (PDF / Excel / 1C) → e-mail (opt.) → `Create`. **The statement can be downloaded from history rather than emailed** (`/sme/documents/statements`).
- For accounting we take **Excel** (turnover parsing) and/or PDF (archive). Per `bank_balances_not_our_zone`: only the period's Dr/Cr turnover matters, the closing balance is ignored.

## Security

**🔑 PIN/access code — the assistant does NOT enter it.** If the bank asks for a PIN/confirmation code, that is a credential, the assistant does NOT enter it (§6, applies even with the operator's explicit permission) and does NOT store it in files. Protocol: stop, tell the operator "the bank is asking for a code" → **4-digit** — the operator enters it herself (her static code); **longer than 4 characters** — it comes to the operator by SMS, also entered by the operator. After unlocking, the assistant continues reading. (brief; full version — `security_rules.md` §11)

- T-Bank — **read only**: statements, operations, requisites. You may generate and download a statement (this is a document artifact, not a movement of money).
- **NEVER:** "Create payment or transfer", "Issue invoice", "Create an SBP payment link", payment templates, e-signature/signing, changing settings, limits, rights, adding/closing companies and accounts.
- All actions in the T-Bank log appear as the operator's actions — caution matters more than speed.
- An unexpected confirmation/signing window — stop, screenshot, ask the operator.

## History

- **XXXX-06-06** — domain created. The operator's direct access to T-Bank Business of direct clients appeared; formalized as a data source. UI verified live. Closed ❓ Q-<client_id>-tbank-account (account number + access presence).
