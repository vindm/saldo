"""Add an optional timestamp (`ts`) to track history events.

As of 2026-06-21 `_tracks.add_history_event` and `_tracks.update_status` record a
full local timestamp on each track history event:

    tasks.json -> tasks[].history[] -> {date, ts, event, source, auto}

`ts` (ISO with HH:MM, e.g. "2026-06-21T14:32+06:00") lets the UI show a concrete
time and order two events of the SAME day correctly — previously events stored
only `date`, so same-day items could not be told apart and the "last update" line
sometimes showed the oldest event.

Purely additive and optional: events without `ts` fall back to `date` everywhere
(lists, the track modal). Nothing in existing state needs reshaping or back-filling
— old events simply show a date with no time; new events carry the timestamp going
forward. This migration performs NO writes; it records the schema addition in the
ledger so `migrate.py status` stays consistent. Schema-level, idempotent, no client names.
"""

ID = "0003"
DESCRIPTION = "tasks: add optional ts (timestamp) on track history events — additive, no back-fill"


def up(api):
    # No-op: nothing in prior state needs reshaping. `ts` is written only by the
    # track writers going forward; readers fall back to `date` when it is absent.
    return
