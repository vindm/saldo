# Composite skill: email/morning_full_scan

Morning full sweep of Yandex.Mail + daily report.

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `today` | date | today's date (MSK) |
| `lookback_hours` | int | `24` (for the last N hours) |

## Algorithm

### Step 1. Preparation

- Via `engine/_loaders.load_clients_from_index()` — each client enriched, email taken from `state/identity.json.contacts.email` (after the Phase 2 migration on 2026-05-25).
- Read `connectors/email/README.md` → the "Known correspondents" section — get the full filter (clients + government bodies + banks + team + partners).

### Step 2. List emails

```
Read `connectors/email/list_messages.md`. Execute with:
  from = null
  since = <now - lookback_hours>
  folder = "All"
  only_unread = false
  limit = 200
Get `all_recent_messages`.
```

### Step 3. Filter by known correspondents

From `all_recent_messages`, single out:
- Emails from an email in the client list → label `client: <id>`
- Emails from government bodies (`@nalog.gov.ru` etc.) → label `gov_authority`
- Emails from client banks → label `bank: <bank>`
- Emails from the team → label `team: <name>`
- Emails from partners (Yandex.Taxi, agents) → label `partner: <name>`

The rest — do NOT read, only count (the "Did not match the filter" section).

### Step 4. Read each matching email

For each labeled email:
```
Read `connectors/email/read_message.md`. Execute with:
  message_id_or_url = <id>
  read_attachments = false
Get `message_data`.
```

### Step 5. Categorize by severity

For each one read — determine severity by the subject and the first 500 characters:
- **🔴 Urgent** — keywords: "urgent", "today", "by end of day", "demand", "audit", "fine", "penalties", "block"
- **🟡 Needs a reply** — there's a direct question or a request for action
- **📩 Informational** — notifications, newsletters, FYI

### Step 6. R6 — preserving manual notes

If `journal/inbox/mail_<today>.json` already exists and contains the operator's manual notes — move them into `journal/operator_decisions.md` before overwriting.

### Step 7. Building the daily report

Write `journal/inbox/mail_<today>.json` — the contract the engine reads
(`engine/_loaders.load_daemon_mail`; note the file is **`mail_`**, not `email_`).
One object, an `items` array; one item per matched email, ordered urgent →
needs-reply → informational:

```json
{
  "items": [
    {
      "severity": "high",
      "from_name": "Sender name",
      "from_email": "sender@example.com",
      "subject": "Email subject",
      "when": "DD.MM HH:MM",
      "client": "client_id or null",
      "label": "client | gov_authority | bank | team | partner",
      "preview": "first ~500 characters",
      "attachments": ["name.pdf (120 KB)"]
    }
  ]
}
```

Field rules: `severity` ∈ `high` (urgent) | `medium` (needs a reply) | `low`
(informational). Emit `{"items": []}` if nothing matched (never omit the file —
heartbeat + empty list is the "ran, found nothing" signal). Do **not** record
contents of emails from unknown correspondents (only count them, outside `items`).

### Step 8. Heartbeat

Write `journal/inbox/email_heartbeat.txt`:
```
YYYY-MM-DD HH:MM OK
```

### Step 9. Applying to client state (via mm_update)

For each client with a significant email (🔴 / 🟡) — apply via the `mm_update` cognitive protocol (see `connectors/mm_update/SKILL.md`):

- **Email requires action**: `_tracks.upsert_track(cid, {type='email_action_required', status='active', source='email:<sender>:<date>', ...})` in `state/tasks.json`
- **Email confirms something on an existing track**: `_tracks.add_history_event(cid, tid, event_text, source='email:<sender>:<date>')`
- **A new fact about the client** (new bank / detail / counterparty): `state_ops.state_write` into the corresponding `state/*.json`
- **Emails from government bodies** — usually create a new track OR close an existing one (tax return accepted → `update_status('done')`)

The "Links" section was removed from mental_model.md after the 2026-05-25 migration — do not use it.

For emails from Anastasia/Alyona (team) — update `system_wide/mental_model.md` if the decision concerns the work process (this is the only mental_model where such rules remain).

### 🔴 Mandatory mm_update finale — source-agnostic (same as a signal from the operator in chat)

> Writing a track/risk is NOT the end. The reaction to an email/news item/task MUST be as deep as the reaction to a signal from the operator in chat (INSTRUCTIONS Step 7.5/8, `security_rules.md` §5b, `mm_update/SKILL.md` finale). For EACH affected client, carry it through to the end:

1. **Cross-link reconciliation** across all of their `state/*.json` (and related clients): close answered `open_question`/tracks in `tasks.json` (status=completed + history), reassess `risks.json`, fill in ❓ in the other files, update `mental_model.md` + append `history.jsonl`.
2. **`resolves_when`** on every NEW open_question track (the guard path `<file>:<dotpath>`).
3. **Read-modify-write** — do not overwrite `tasks_overrides` and the operator's manual decisions (via `_tracks`/`state_ops`).
4. **lint + publish**: `python3 engine/generate.py` (runs `state_lint`); publish dashboards (`cp _tmp_html/*.html ..`) only on exit 0.
5. **Self-check**: grep for leftover active `open_question`/`❓` on the topic — if it's hanging → the finale isn't finished.
6. **Audit-log** as one block in `journal/operator_decisions.md`.

### If there are 0 emails from known correspondents in the period

- Write `email_<today>.md` with a note "In the last 24 hours there were no emails from known correspondents."
- Still write the heartbeat (the daemon ran, the mail is just quiet).

## Security

- Do NOT mark as read.
- Do NOT delete, do NOT reply, do NOT create drafts in this skill.

## Relation to other skills

- After `morning_full_scan` — mm_update processes significant emails by the same protocol as tg/finkoper signals (see `mm_update/SKILL.md`). The Updater (T-rules) and the Analytic (R-rules) were deprecated 2026-05-24.

## History

- **XXXX-05-16** — extracted as a composite during the P4-email refactor.

---

_Version 1.0 — 2026-05-16; v1.1 — 2026-05-25: synchronization with the state/ architecture (clients_data→load_clients_from_index, mm_update instead of mental_model→Links, removed updater/T4 + analytic/R2-R3 references)._


---

## 🔴 Unconditional dashboard render — ALWAYS, as the last action

> The dashboard render is NOT gated on whether there were changes. Whatever happened above — whether state was edited or not, whether at least one client was affected or zero — **as the last action the daemon MUST**:
>
> `python3 engine/generate.py` (runs `state_lint`); on exit 0, publish `cp _tmp_html/*.html ..` (from the `_data` directory).
>
> Reason: the dashboard carries time-dependent content (today's date in the header, overdue items, "in N days") that must be refreshed **daily**, regardless of whether there were changes in state. Skipping the render on a "quiet day" = a frozen date (incident 2026-06-11→13, the operator's decision: the render is unconditional).
