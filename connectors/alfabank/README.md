# Skills for the `alfabank` domain

> Working with Alfa-Business Online (https://link.alfabank.ru/dashboard) via Claude in Chrome. Direct access to the bank accounts of **direct-contour** clients — we pull bank statements/operations ourselves. Sister domain to `tbank/` (same pattern, different UI).
>

## ⚠️ Key point (same as tbank)

- For direct clients on Alfa we pull the bank statement ourselves before month-end close — **waiting for the statement from the client is cancelled** (the operator's decision 2026-06-06, general direct-contour policy).
- `bank_statements_only_main_vtb` — that's about the team contour in 1C:Fresh, not this.

## ⚠️ Risk #1 — multi-company

A single operator login sees several SPs. Before reading client data you MUST confirm the active company and reconcile it with the target `client_id`. Reading the wrong client = incident.

## ⚠️ Access and role

- Login via **Alfa-ID (SSO)**. The MCP tab may be bounced to `id.alfabank.ru/oidc/login` (cookie isolation) — **repeat the navigate to `link.alfabank.ru/dashboard`** (the session is picked up on the 2nd attempt, `?alfaidAuth=true`). Do NOT log in yourself.
- The operator's role is **"Document Flow"**: viewing, statements, documents. Payments/signing are NOT this role (and not allowed to us). A plus for read-only.

## Skills

| File | Type | What it does |
|---|---|---|
| [`get_statement.md`](get_statement.md) | atomic | Statement for a period by client (Excel/PDF) → `<client doc folder>/` → parse Dr/Cr turnover |
| [`list_operations.md`](list_operations.md) | atomic | Operations from the screen (Operations Feed) without generating a document |
| [`incremental_update.md`](incremental_update.md) | composite | New operations since last_run across all Alfa clients |

## Applicability — resolved from state (not hardcoded)

Applies to **direct-contour** clients that have an Alfa-Business account. Resolve at runtime, never hardcode:
- which clients are direct-contour → roster `clients_index.json` (`group`);
- each client's Alfa account number(s) + BIC → `state/accounts.json:bank_accounts[]` (use `closed_at=null`).

⚠️ One login sees several SPs (including companies that are not the practice's). ALWAYS reconcile the active company by INN against the target `client_id` before reading — reading the wrong client is an incident.

## UI map (verified live 2026-06-06)

- **Company switcher:** click the active company name / "[redacted]" at the top right → profile panel → **"Companies"** section (cards: name + INN + balance) → clicking a card switches (~3 sec). Verify the active company name afterwards.
- **Statement:** quick action **"Download statement"** or left menu **"Statement"**. Format — Excel (parse) / PDF (archive).
- **Operations (reading):** left menu **"Operations Feed"**, filters Incoming/Outgoing/Account/Counterparty/Status/Amount.
- **Account requisites:** the "Requisites" link on the account card (BIC/correspondent account).
- The account number on the dashboard is printed with spaces (`40802 810 X XXXX XXXXXXX`) — collapse the spaces when parsing.
- Per `bank_balances_not_our_zone`: what matters is Dr/Cr turnover, not the closing balance.

## Security

**🔑 PIN/access code — the assistant does NOT enter it.** If the bank asks for a PIN/confirmation code, that is a credential, the assistant does NOT enter it (§6, applies even with the operator's explicit permission) and does NOT store it in files. Protocol: stop, tell the operator "the bank is asking for a code" → **4-digit** — the operator enters it herself (her static code); **longer than 4 characters** — it comes to the operator by SMS, also entered by the operator. After unlocking, the assistant continues reading. (full version — `security_rules.md`)

- Read only: statements, operations, requisites. **NEVER:** "Create payment", "Import payments", "Sign", "Send", "Issue invoice", changing data at the FTS, changing settings/tariff. Any movement of money is not allowed.
- Actions in the Alfa log appear as the operator's actions.
- An unexpected confirmation/signing window — stop, screenshot, ask the operator.

## History

- **XXXX-06-06** — domain created. The operator's direct access to Alfa-Business (Document Flow role) for the direct-contour clients on Alfa; UI verified live; accounts entered into state.
