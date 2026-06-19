# Atomic skill: check_z_report

Check a client's cash operations via the Platforma OFD Z-Report for a given period. Download the xlsx, parse the "Cash revenue" column, return a decision "post into 1C or not".

> **Source of truth for the algorithm:** `memory/ofd_z_report_workflow.md`. When the Platforma OFD UI changes, fix both places.
>
> **After the state migration on 2026-05-25:** read the client's cash register and OFD details from `state/accounts.json:kassas[]` (has registration number/model/ofd_provider). If kassas contains a `pending_corrections` object — check it (e.g. Client A's 820K uncleared) and account for it when deciding whether to post.

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `client_id` | string | **required** (from `clients_data.json`, e.g. `client_h`) |
| `period_start` | date | **required** (first day of the month) |
| `period_end` | date | **required** (last day of the month) |
| `output_folder` | string | `_Inbox/` (the operator will later move it to `SP <Surname>/`) |
| `wait_max_minutes` | int | `7` (the Z-Report takes "up to 5 minutes", we take a margin) |

## Precondition

- Applicability checked via `README.md` (for Client A — yes; for Client A currently — no, no own cash register).
- Claude in Chrome is authorized in Platforma OFD (`lk.platformaofd.ru`).
- The `_Inbox/` folder (or the specified `output_folder`) exists.

## Algorithm

### Step 1. Open the Platforma OFD account

1. Open `https://lk.platformaofd.ru` via Claude in Chrome.
2. If it asks for login — stop, notify the operator, wait for authorization (under their account).

### Step 2. Go to the Z-Reports section

1. Left menu → **Reports** (if the menu is collapsed — expand it).
2. The **Generate report** tab (this is the default tab).
3. Find the **Z-Reports** tile (among the other report types).
4. Click the tile.

### Step 3. Report parameters

| Field | Value |
|---|---|
| **Period** | `period_start` .. `period_end` |
| **Stores** | "All stores" |
| **Cash registers** | "All cash registers" |
| **Format** | `.xlsx` |
| **Column totals** | ✓ enabled |
| **Single file** | ✓ selected (radio) |

**Tip from memory:** entering the period via the calendar sometimes sticks. More reliable — triple-click on the field, type the text directly (`DD.MM.YYYY - DD.MM.YYYY` or the format that OFD accepts; clarify on the first run).

### Step 4. Generate the report

1. Click the **Generate report** button.
2. Switch to the **Ready reports** tab (next to "Generate report").
3. Find the row with the just-created report (at the top of the list). Fields:
   - Type: "Z-Report"
   - Period: matches the parameters
   - Status: "In queue" → "Processing" → "Generated"

### Step 5. Wait for readiness

1. Every 30–60 seconds, click the **refresh** button (the 🔄 icon or "Refresh" near the table header).
2. Wait up to `wait_max_minutes` minutes (default 7).
3. If the status has not switched to "Generated" within `wait_max_minutes` — return an error: `{status: "timeout", message: "The report did not generate within {N} minutes"}`.

### Step 6. Download the file

1. When the status is "Generated" — click the **download** button (the 📥 icon or "Download") in the report row.
2. The file lands in the Windows system downloads folder (`C:\Users\user\Downloads\`).
3. The file name is whatever Platforma OFD gives (often `Z-otchet_<identifier>.xlsx`).

### Step 7. Move and rename

1. From `Downloads/`, move it to `output_folder` (default `_Inbox/`).
2. Rename per the template: `ZReport_<Surname>_<month-year>.xlsx`
   - `Surname` — the client's short name (from `clients_data.json[client_id].name_short`)
   - `month-year` — format `april-2026` (Russian month + year via a hyphen)
   - Examples: `ZReport_Zubareva_april-2026.xlsx`

### Step 8. Parse the xlsx

1. Open the file via `python+openpyxl` or Excel (via the MCP xlsx skill).
2. Find the **"Cash revenue"** column (or "Cash settlement" — clarify the exact name on the first run and update this skill).
3. For each session / each cash register — sum the values of the column.
4. Compute the total `cash_total`.
5. Build the structure by sessions and by cash registers (see the return format below).

### Step 9. Make the decision

```python
if cash_total == 0:
    output_decision = "not_needed"
    next_action = "Do NOT post the OFD report into 1C. Save the file as evidence. " \
                  "In monthly_check.sources update the status: «Not required ✓»."
else:
    output_decision = "needs_1c_posting"
    next_action = "Post into 1C via Cash register → Cash operations " \
                  "(NOT via «Retail Sales Report»). " \
                  "This is the operator's work in 1C — the Chrome agent does not write into 1C."
```

## Return format

```json
{
  "status": "ok",
  "client_id": "client_h",
  "period": "2026-04-01..2026-04-30",
  "file_path": "_Inbox/ZReport_Zubareva_april-2026.xlsx",
  "cash_total": 0,
  "sessions": [
    {
      "kkt_serial": "9286...01",
      "kkt_name": "Aqsi 5 NIGHT VISION #1",
      "session_id": 142,
      "session_open": "2026-04-01T10:00",
      "session_close": "2026-04-01T22:00",
      "cash": 0,
      "card": 12500
    },
    ...
  ],
  "kkts_summary": [
    {"kkt_name": "Aqsi 5 NIGHT VISION #1", "sessions_count": 28, "cash_total": 0, "card_total": 380500},
    {"kkt_name": "Aqsi 5 NIGHT VISION #2", "sessions_count": 30, "cash_total": 0, "card_total": 415200}
  ],
  "output_decision": "not_needed",
  "next_action": "Do NOT post the OFD report into 1C...",
  "raw_columns_found": ["Open date", "Close date", "Cash revenue", "Cashless revenue", "Total"]
}
```

`raw_columns_found` — a list of all the xlsx columns, so you can check whether a name has changed.

## Possible errors

| Error | What to do |
|---|---|
| Not authorized in Platforma OFD | Stop, notify the operator, wait for authorization |
| Timeout at the "Generated" stage | Return `status: "timeout"`. The operator will download it manually later |
| "Cash revenue" column not found | Return `status: "parse_error"` + `raw_columns_found`. OFD may have renamed it — update the skill |
| The file already exists in `output_folder` with the same name | Add a suffix `_v2`, `_v3` — do not overwrite. Flag for the operator |
| The client has 0 cash registers in Platforma OFD | Return `status: "no_kkts"` — the client has no own cash register, the skill is not applicable |

## Security

- `lk.platformaofd.ru` — read only (see the README "Security" section).
- Do not click buttons that change cash register settings, do not unlink registers.
- If a dialog "Confirm the action", "Your correction receipt…" appears — stop, screenshot, ask the operator.
- Do NOT delete files from `Downloads/` (rule `INSTRUCTIONS.md §5`). Only move them.

## When invoked

- Me in a session: "check cash for Client A for April" → `check_z_report(client_id=client_h, period_start=2026-04-01, period_end=2026-04-30)`.
- At month-end close for a client with a cash register (per the checklist `monthly_primary_docs.md`).
- After Client A connects a cash register — they will be added to the applicable clients, and this skill will start being invoked for them too.

## Relation to monthly_check and the updater

After downloading and parsing:
1. The file `ZReport_<Surname>_<month-year>.xlsx` is in `output_folder` (or in `SP <Surname>/` after a manual move).
2. On the next run the updater will detect the new file (T3) and propose a patch into `monthly_check.sources[i]`:
   - `status: check → ok` (if `cash_total == 0` and the decision is "not required")
   - `status: check → gap` (if `cash_total > 0` and it is not yet posted into 1C)
   - `last_file_received: <today>`
   - Add the structured field `cash_total: <number>`, `output_decision: <not_needed | needs_1c_posting>`.

Also — the operator may explicitly record in `operator_decisions.md`: "Z-Report for April Client A downloaded, cash 0 ₽, not posting into 1C". Then the updater on T7 will close the line as "Not required ✓" with an entry in `decisions[]`.

## Limitations

- The skill works with **one client for one period**. To sweep several — invoke it in a loop.
- The period must be closed (from `period_start` to `period_end` inclusive). Open periods ("from the 1st through today") are not supported — that is a special case.
- If the client has >5 cash registers — generating the Z-Report may take longer than 5 minutes; increase `wait_max_minutes`.

## History

- **2026-05-10** — the algorithm was formulated in memory `ofd_z_report_workflow.md` after the first manual check.
- **2026-05-16** — formalized as a reusable skill as part of P4-ofd_z_report.

---

_Version 1.0 — 2026-05-16._
