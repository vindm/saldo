# Composite skill: news/morning_full_scan

Morning sweep of relevant topics + categorization + daily report.

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `today` | date | today's date (MSK) |
| `lookback_hours` | int | `24` |

## Algorithm

### Step 1. Preparation

- Read `connectors/news/README.md` → "Search topics" section.
- Load clients via `engine/_loaders.load_clients_from_index()` — gives 15 enriched records with regime/okved/financials from state (after the Phase 2 migration).

### Step 2. Search across all topics

```
Read `connectors/news/search_topics.md`. Execute with:
  topics = [the full list from README, except UKEP]
  since = <now - lookback_hours>
  until = <now>
  max_results_per_topic = 10
Get `all_items`.
```

### Step 3. Categorization by severity

For each news item:
- **🔴 Urgent** — takes effect within the next 30 days OR has an explicit deadline OR mentions a penalty/blocking OR affects clients' current deadlines
- **🟡 Important** — takes effect later than 30 days; clarifications of fundamental points; changes our practice in the medium term
- **📋 Informational** — FYI, general context, no direct impact

### Step 4. Assessing applicability to clients

For each news item — note which of all clients it affects:
- By regime (from `state/regime.json`: USN / patent / AUSN / OSNO)
- By OKVED (the client 49.32 taxi, the client 68.20 rental, the client 49.41 freight, etc.)
- By presence of a cash register (from `state/accounts.json:kassas[]`)
- If the news applies to everyone — mark "all clients"

### Step 5. R6 — preserving manual notes

If `journal/inbox/news_<today>.json` exists and contains the operator's manual notes — save them into `operator_decisions.md`.

### Step 6. Building the daily report

Write `journal/inbox/news_<today>.json` — this is the contract the engine reads
(`engine/_loaders.load_daemon_news`). One object, an `items` array; one item per
news piece, ordered urgent → important → informational:

```json
{
  "items": [
    {
      "severity": "high",
      "title": "Headline / gist of the news",
      "source": "Source name (verified domain)",
      "body": "2-3 sentences: the gist, who it affects, deadline if any.",
      "url": "https://source/article"
    }
  ]
}
```

Field rules: `severity` ∈ `high` (urgent) | `medium` (important) | `low`
(informational). Emit `{"items": []}` if nothing was found (never omit the file —
the heartbeat + an empty list is the "ran, found nothing" signal). Do **not**
include UKEP/e-signature or foreign-source items (filtered out per README).

### Step 7. Heartbeat

Write `journal/inbox/news_heartbeat.txt`:
```
YYYY-MM-DD HH:MM OK
```

### Step 8. Applying to client state (via mm_update)

If a news item is 🔴 OR applies to a specific client with an active track — apply it via the cognitive protocol `mm_update` (see `connectors/mm_update/SKILL.md`):

- **High confidence** (clearly applicable): `_tracks.upsert_track(cid, {type='regulatory_change', status='active', due_date=<deadline>, title=<gist>})` in `state/tasks.json`
- **Medium**: the same `upsert_track` with `title="🔧 Check: <gist>"`
- **Informational**: `state_ops.state_write(cid, 'risks.json', {..., 'yellow': [...new {category: 'monitoring'}]}, ctx='news_monitoring')` OR update `state/financials.json.tax_calendar[]` if the news is about deadlines

The "Monitoring" section was removed from mental_model.md after the 2026-05-25 migration — do not use it.

For system-wide topics (changes to the team's work process) — update `system_wide/mental_model.md` (this is the only mental_model where such rules remain).

### 🔴 Mandatory mm_update finale — source-agnostic (as with a signal from the operator in chat)

> Recording a track/risk is NOT the end. A reaction to a letter/news/task MUST be just as deep as a reaction to a signal from the operator in chat (INSTRUCTIONS Step 7.5/8, `security_rules.md` §5b, `mm_update/SKILL.md` finale). For EACH affected client, carry it through to the end:

1. **Cross-link reconciliation** across all of its `state/*.json` (and related clients): close answered `open_question`/tracks in `tasks.json` (status=completed + history), reassess `risks.json`, fill in ❓ in the other files, update `mental_model.md` + append `history.jsonl`.
2. **`resolves_when`** on every NEW open_question track (sentinel path `<file>:<dotpath>`).
3. **Read-modify-write** — do not overwrite `tasks_overrides` and the operator's manual decisions (via `_tracks`/`state_ops`).
4. **lint + publish**: `python3 engine/generate.py` (runs `state_lint`); publish dashboards (`cp _tmp_html/*.html ..`) only on exit 0.
5. **Self-check**: grep for residual active `open_question`/`❓` on the topic — if anything is hanging → the finale is not finished.
6. **Audit-log** as a single block in `journal/operator_decisions.md`.

### If there is no news for the period

- Write `news_<today>.md` with the note "No significant news found in the last N hours".
- Write the heartbeat (the daemon ran).

## Security

- Web search only via the WebSearch tool.
- Do not download raw HTML, only snippets and headlines.

## Relation to other skills

- Afterward — mm_update (see `connectors/mm_update/SKILL.md`) applies the news to the state of affected clients: `state/tasks.json` for new tracks, `state/risks.json` for monitoring. The Updater and Analytic skills were deprecated 2026-05-24, `monthly_check.sources` does not exist.

## History

- **XXXX-05-16** — extracted as a composite during P4-news.

---

_Version 1.0 — 2026-05-16; v1.1 — 2026-05-25: synchronization with the state/ architecture (clients_data→load_clients_from_index, mm_update instead of mental_model→Monitoring, removed updater/T5 references)._


---

## 🔴 Unconditional dashboard render — ALWAYS, as the last action

> The dashboard render is NOT gated on the presence of changes. Whatever happened above — whether there were state edits or not, whether one client was affected or none — **as the last action the daemon MUST**:
>
> `python3 engine/generate.py` (runs `state_lint`); on exit 0 publish `cp _tmp_html/*.html ..` (from the `_data` directory).
>
> Reason: the dashboard carries time-dependent content (today's date in the header, overdue items, "in N days") that must be refreshed **daily**, regardless of whether state changed. Skipping the render on a "quiet day" = a frozen date (incident 2026-06-11→13, the operator's decision: the render is unconditional).
