# Composite skill: news/incremental_update

Incremental news search since last_run — appends to the daily report.

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `since` | ISO datetime | `news_heartbeat.txt` last timestamp |
| `topics_filter` | string[] | `null` (`null` = all topics; otherwise — specific ones) |
| `trigger_description` | string | `null` |

## Algorithm

### Step 1. Determine `since`

If the parameter is not set — read `journal/inbox/news_heartbeat.txt`.

### Step 2. Search

```
Read `connectors/news/search_topics.md`. Execute with:
  topics = <topics_filter or the full list from README>
  since = <since>
  until = <now>
  max_results_per_topic = 5
```

### Step 3. Categorization + applicability to clients

Same as `morning_full_scan.md` steps 3-4.

### Step 4. R6 — preserving manual notes

Before appending — save the operator's manual notes into `operator_decisions.md`.

### Step 5. Appending to the daily report

If `journal/inbox/news_<today>.md` exists — append to the end:

```markdown

---

## 🔄 Appended in the incremental run HH:MM (trigger: <trigger_description>)

**News since last_run (HH:MM):**

### 🔴 Urgent (N)
[blocks]

### 🟡 Important (N)
[blocks]

### 📋 Informational (N)
[blocks]
```

If the file does not exist — create it as a full daily report.

### Step 6. Heartbeat

Update `news_heartbeat.txt`.

### Step 7. Applying to state + mandatory mm_update finale

Same as `morning_full_scan.md` step 8 (applying to state) — and MANDATORY the same mm_update finale: cross-link reconciliation across all `state/*.json` of the affected client, `resolves_when` for new questions, read-modify-write (do not overwrite `tasks_overrides`/the operator's decisions), `generate.py`/lint, self-check, audit-log. **The incremental parse updates links just as fully as the morning one — source-agnostic.**

### If there is nothing new

- Do not append.
- Return "No news on our topics for the period HH:MM..HH:MM".
- 🔴 STILL perform the unconditional dashboard render (see the "Unconditional dashboard render" section below) — even when there is no news.

## When invoked

- Me in a session on the trigger "update the news", "anything fresh on X".
- mm_update when fresh news is needed — invokes `incremental_update` (Updater/T-rules deprecated 2026-05-24).

## History

- **XXXX-05-16** — extracted as a composite during P4-news.

---

_Version 1.0 — 2026-05-16._


---

## 🔴 Unconditional dashboard render — ALWAYS, as the last action

> The dashboard render is NOT gated on the presence of changes. Whatever happened above — whether there were state edits or not, whether one client was affected or none — **as the last action the daemon MUST**:
>
> `python3 engine/generate.py` (runs `state_lint`); on exit 0 publish `cp _tmp_html/*.html ..` (from the `_data` directory).
>
> Reason: the dashboard carries time-dependent content (today's date in the header, overdue items, "in N days") that must be refreshed **daily**, regardless of whether state changed. Skipping the render on a "quiet day" = a frozen date (incident 2026-06-11→13, the operator's decision: the render is unconditional).
