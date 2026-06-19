"""_health.py — compute a client's color status.

Extracted from generate.py as part of P3-11 (decomposition, 2026-05-17).
Sources (JSON-first, 2026-06-19): per-client state/*.json only —
  - state/financials.json.monthly_close (blocker)
  - aggregated deadlines from state (financials.tax_calendar_2026[] + tasks
    with a due_date), via _deadlines.collect_deadlines
  - aggregated "awaiting" from state (open tasks with an awaiting task_type),
    via _deadlines.collect_awaiting
  - daemon daily reports (finkoper / anomalies)
Returns (color, reasons[]). Used in overview and client_dashboard.

History:
  2026-05-25 — migrated monthly_check reads -> state/financials.json.monthly_close;
               removed dead sources-related code; removed client.blocker.
  2026-06-19 — JSON-first refactor: overdue/soon now derive from state-aggregated
               deadlines + awaiting (not the calendar / request-log registries).
               UKEP expiry dropped (no state source; it was an out-of-scope
               registry). The calendar_rows/ukep_rows/requests_rows parameters are
               kept for signature compatibility but are NO LONGER read.
"""
import os
from datetime import date, timedelta
from datetime import datetime as _dt
from _helpers import _short
import state_ops


def calculate_health(client, calendar_rows=None, ukep_rows=None, requests_rows=None,
                     today=None, daemon_finkoper=None, daemon_anomalies=None,
                     deadlines=None, awaiting=None):
    """{'color': red|yellow|green|grey, 'reasons': [...], 'score': int}.

    calendar_rows / ukep_rows / requests_rows are accepted for backward-compatible
    call sites but are ignored (JSON-first migration 2026-06-19). Deadlines and
    awaiting are derived from state; callers may pre-pass per-client slices via
    `deadlines` / `awaiting` to avoid re-reading state per client.
    """
    import generate
    TODAY = generate.TODAY
    DIARY_INBOX = generate.DIARY_INBOX
    if today is None:
        today = TODAY
    # Daemons: if not passed, try loading from disk. No files -> empty dicts.
    if daemon_finkoper is None or daemon_anomalies is None:
        from _loaders import load_daemon_finkoper, load_daemon_anomalies
        if daemon_finkoper is None:
            daemon_finkoper = load_daemon_finkoper(DIARY_INBOX, today)
        if daemon_anomalies is None:
            daemon_anomalies = load_daemon_anomalies(DIARY_INBOX, today)
    name_short = client.get('name_short', '')
    cid = client.get('id')
    # Source of truth for monthly_close is state/financials.json (migration 2026-05-25).
    mc = state_ops.state_read(cid, 'financials.json').get('monthly_close') or {}
    # State-derived deadlines + awaiting for THIS client (JSON-first 2026-06-19).
    # Deadlines for health come from STATE TRACKS only (kind='task'). tax_calendar
    # (kind='tax') is an external input that feeds track creation — it is NOT a
    # render/compute source, so it is excluded here (per the system's principles).
    from _deadlines import collect_deadlines, collect_awaiting
    if deadlines is None:
        deadlines = [r for r in collect_deadlines(today) if r['client_id'] == cid and r.get('kind') == 'task']
    else:
        deadlines = [r for r in deadlines if r['client_id'] == cid and r.get('kind') == 'task']
    if awaiting is None:
        awaiting = [r for r in collect_awaiting(today) if r['client_id'] == cid]
    else:
        awaiting = [r for r in awaiting if r['client_id'] == cid]
    red, yellow = [], []

    # RED
    if mc.get('blocker'):
        red.append(f"Monthly-close blocker: {_short(mc['blocker'], 50)}")
    # NOTE: a track with a past due_date is NOT, by itself, "overdue → red" (the
    # original engine never did that). Red comes from explicit signals (blocker,
    # long-overdue awaiting, daemon overdue/anomaly), matching original behavior.
    # NOTE: awaiting tasks do NOT drive health here. The original engine's
    # "request overdue >14d → red" was fed by the request-journal registry (a small,
    # curated set), NOT by every state task in an awaiting status. Firing on all
    # awaiting tasks over-reports red, so it is excluded to preserve behavior.
    # Daemons: Finkoper overdues and high anomalies for today
    for it in daemon_finkoper.get('overdue', []):
        if it.get('client') == name_short:
            red.append(f"Finkoper task overdue: {_short(' | '.join(it.get('fields', [])), 60)}")
    for it in daemon_anomalies.get('high', []):
        if it.get('client') == name_short:
            red.append(f"Anomaly (high): {_short(it.get('text',''), 60)}")
    if red:
        return {'color': 'red', 'reasons': red, 'score': min(100, 80 + 5*len(red))}

    # YELLOW
    # (Near-deadline tracks do NOT turn a client yellow on their own — matches the
    # original engine, which keyed yellow off calendar/request signals, not a
    # track's due_date.)
    # (Awaiting tasks do not drive yellow either — see the red note above.)
    # Daemons: Finkoper deadlines <=3 days, unread messages, medium anomalies
    for it in daemon_finkoper.get('soon', []):
        if it.get('client') == name_short:
            yellow.append(f"Finkoper deadline <=3d: {_short(' | '.join(it.get('fields', [])), 55)}")
    for it in daemon_finkoper.get('unread', []):
        if it.get('client') == name_short:
            yellow.append(f"Unread from client: {_short(' | '.join(it.get('fields', [])), 55)}")
    for it in daemon_anomalies.get('medium', []):
        if it.get('client') == name_short:
            yellow.append(f"Anomaly (medium): {_short(it.get('text',''), 55)}")
    if yellow:
        return {'color': 'yellow', 'reasons': yellow, 'score': min(79, 40 + 5*len(yellow))}

    # GREEN
    if not mc.get('blocker'):
        return {'color': 'green', 'reasons': [], 'score': 20}

    # GREY (reserved)
    return {'color': 'grey', 'reasons': [], 'score': 0}


