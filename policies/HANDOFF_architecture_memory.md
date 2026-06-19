# HANDOFF: Client memory architecture
_Created: 2026-05-25 · Continue in a new session_

---

## Problem

Data about a client lives in three places at once:
- `Client_card.md` — the human-readable source
- `clients_data.json` — the machine source for the dashboard
- `mental_model.md` — the analytical layer, parsed by a fragile regex

**Every update requires three manual steps. Miss one — and the dashboard lies silently.**

Concrete bugs that have already happened:
1. The parser dropped every item starting with `- **` → "Firmly understood" was always empty
2. Resolved items (✅) were not filtered out of "Not clarified" → stale questions lingered
3. A multi-line replace silently failed (the previous replace had changed the first line) → the OKVED code stayed in "Awaiting explanation"

All three were fixed (parser + mental_model files), dashboards regenerated. But those are symptoms, not a cure.

**Root cause:** there is no contract between the writer (me) and the reader (the parser). Plain text + regex = perpetual schema drift.

---

## Proposed solution: a Karpathy-style memory hierarchy

The operator never writes into the .md files by hand — only I (the AI) do. The operator writes to me in chat.
The dashboard is the single source of truth for the operator.

### Architecture

```
SP <Surname>/
│
├── SNAPSHOT.md          ← "CLAUDE.md for the client"
│                          ~500 words, always current, I read it first on every task
│                          quick_summary + firm[] + unclear[] + active tracks in brief
│                          Updated after EVERY significant event
│
└── state/
    ├── identity.json       # INN, OGRNIP, registration details, OKVED — rarely changes
    ├── accounts.json       # banks, accounts, cash registers, foreign accounts
    ├── regime.json         # USN/PSN/AUSN, patents — once a year
    ├── behavior.json       # behavior pattern, style — accrues slowly
    ├── financials.json     # income/taxes by quarter — quarterly
    ├── open_items.json     # tracks, open questions — changes often
    ├── risks.json          # risks with severity and articles of the Tax Code / Administrative Code
    ├── counterparties.json # counterparties with INN and relation type
    └── history.jsonl       # event log — ONLY append, never overwritten
```

### Key principles

1. **SNAPSHOT.md = living document** — not parsed, read in full. I consolidate it when it grows (remove the stale, push details → state/)
2. **state/ files = long-term memory** — read only when concrete detail is needed
3. **One update_client()** — the single write point. Takes a signal → atomically updates the needed files → history.jsonl (append) → generate.py
4. **No parser** — generate.py reads JSON directly, no regex over markdown
5. **history.jsonl append-only** — the full history of all signals, never lost

### What disappears
- `mental_model.md` as a parsed source → becomes an optional narrative diary (the machine does not read it)
- `clients_data.json` → absorbed into state/identity.json + state/financials.json etc.
- `Client_card.md` as a source → becomes a generated view from state/

### Update pipeline

```python
update_client('client_k2', signal='egrul', data={inn, ogrnip, okved})
# → state/identity.json  (update fields)
# → SNAPSHOT.md          (add to firm[], remove from unclear[])
# → state/history.jsonl  (append: {date, type, summary, source})
# → generate.py          (regenerate the dashboard)
```

---

## What needs to be done in a new session

### Step 1 — Finalize the schema of the state/ files
Read the inventory (or ask the agent again) and for each file determine:
- Exact fields and types
- Example values from real clients
- Optional fields (only for some clients: real_estate, patents, kassas, etc.)

### Step 2 — Write update_client.py
The function takes: client_id + signal_type + data dict
Signals: egrul | tg_message | finkoper_task | manual | financials_update | bank_statement | anomaly_dismiss | risk_add

### Step 3 — Rewrite generate.py
Read from state/*.json instead of parsing mental_model.md. Remove the `_mental_model.py` parser entirely.

### Step 4 — Write a migration script
For each of the 15 clients: parse the existing data from clients_data.json + mental_model.md → create SNAPSHOT.md + state/*.json

### Step 5 — Update INSTRUCTIONS.md
Lock in the new workflow: any signal → update_client() → dashboard. Never write into the state/ files directly.

---

## Nuances worth remembering

- **The operator never writes into files** — only into chat. I am the only writer.
- **Karpathy memory**: not RAG (retrieval from a large base), but a living document that the AI updates after every interaction
- **history.jsonl** — an append-only log, not a JSON array (otherwise it grows and gets rewritten in full)
- **real_estate[]** (Client E), **patents[]** (some clients), **kassas[]** (Client F, Client D) — optional blocks
- **service_contract** — direct clients only (9 people), absent for the team (6)
- **Team vs Direct** — different fields: the team has fresh_url + finkoper_task_ids, the direct clients have telegram + bookkeeping-services contract + sub-scenario A/B/C/D/E/F
- **SNAPSHOT.md must fit in ~500 words** — if it grows, consolidate
- 
---

## Context for starting a new session

Read:
1. This file
2. `policies/INSTRUCTIONS.md`
3. `policies/safety-rules.md` (it already has section 5b about the update chain)
4. One example mental_model.md (e.g. SP Client K2) to understand the current format

Current state of the dashboards: **working**, all 22 dashboards generate correctly. The parser is fixed. Company-registry (EGRIP) data is entered for all 9 direct clients. The migration can begin.
