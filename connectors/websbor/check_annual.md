# Atomic skill: check_annual (statistics portal / websbor.gks.ru)

Annual check of each SP's obligation to file statistical reporting on the statistics portal website. Run once in January — after receiving a new INN/OGRNIP or on the operator's command.

> **Source of truth:**. When the websbor.gks.ru UI changes — update both places.

## Parameters

| Parameter | Type | Default |
|---|---|---|
| `clients` | list[string] | all the team SPs from `clients_data.json` |
| `year` | int | current year |
| `output_folder` | string | `registries/` |

## Precondition

- Claude in Chrome is open and ready for navigation.
- `clients_data.json` is available (for each SP's INN).
- January of the current year or an explicit command from the operator.

## Algorithm

### Step 1. Prepare the client list

Read `clients_data.json`, collect for each team client:
- `name_short` — short name
- `inn` — INN
- `okpo` or `ogrn` — if present in the card

### Step 2. Check each SP on websbor.gks.ru

For each client, do the following via Claude in Chrome:

1. Open `https://websbor.gks.ru/online/#!/gs/statistic-codes`
2. Enter the client's **INN** in the search field.
3. Click **Find** (or Enter).
4. Read the result:
   - If "List of federal statistical observation forms" — there are required forms → record the list of forms and the filing deadlines.
   - If "No reporting required" / an empty result — no obligation → mark `none`.
5. Take a screenshot or copy the result text.

**Important:** the site may fail to find an SP by an INN with a leading zero — in that case try the OGRNIP.

### Step 3. Build a summary

Compose a table:

| Client | INN | Status | Forms (if any) | Filing deadline |
|---|---|---|---|---|
| a client | ... | no obligation | — | — |
| a client | ... | yes | MP(micro) | by 05.02 |
| ... | | | | |

### Step 4. Save the result

Write the summary to a file:
`registries/stat_reporting_<year>.md`

Format: check date + table + list of clients that have an obligation.

### Step 5. Flag for the operator

- If any of the SPs **have** required forms — notify the operator with the specific forms and deadlines.
- If everyone is "no obligation" — briefly confirm that it was checked, all clear.
- Remind to repeat the check next January.

## Hard rules

- **Do not file** reports on behalf of clients — only check the obligation.
- If the site is unavailable or returns an error — notify the operator, do not consider the check complete.
- Do not copy clients' personal data (INN) into third-party services other than websbor.gks.ru.

## When to invoke

- Every January.
- After adding a new client — a one-off check.
- On an explicit command from the operator.

## Related materials

- — the annual check rule
- `registries/stat_reporting_<year>.md` — the check result
- `connectors/websbor/README.md` — domain overview (create when expanding)
