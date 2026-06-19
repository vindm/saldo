"""_deadlines.py — state-derived deadlines + awaiting aggregation (JSON-first).

JSON-first refactor (2026-06-19): the overview deadline/awaiting panels and the
health calculation no longer read the external registries (consolidated calendar,
request log, UKEP). Coverage analysis confirmed ~81% of the calendar and ~all of
the request journal already live in per-client state, so state is the single
source of truth.

Two aggregators, both ACROSS all clients (clients_index -> state/*.json):

  collect_deadlines(today) -> list[dict]
      one row per tax_calendar_2026[] entry AND per tasks.json task with a
      due_date. Shape:
        {client_id, client_name, date(date), what, amount, status,
         kind: 'tax'|'task', linked_task, days_left, bucket}
      bucket categorizes date vs TODAY:
        'overdue'   date < today and not done
        'today'     date == today and not done
        'this_week' today+1 .. today+7 and not done
        'later'     beyond +7 (or done) — kept so callers can window themselves
      "done" deadlines are still returned (bucket='done') so callers can decide;
      the not-done filter is applied via the DONE_* sets below.

  collect_awaiting(today) -> list[dict]
      one row per OPEN task whose task_type is in AWAITING_TASK_TYPES. Shape:
        {client_id, client_name, what(title), days_waiting, task_type, status}

The finkoper JSON snapshot loader (load_daemon_finkoper) is unaffected and stays
in _loaders.py.
"""
from datetime import datetime as _dt, date as _date


# Canonical "done" sets (status values stored in state/*.json, language-neutral).
# tax_calendar_2026[].status done set:
DONE_TAX_STATUSES = {
    'paid', 'done', 'submitted', 'completed', 'cancelled',
    'overlapped_by_insurance',
}
# tasks.json task.status done/closed set:
DONE_TASK_STATUSES = {
    'done', 'completed', 'cancelled', 'dropped', 'dismissed',
    'closed', 'resolved', 'deferred',
}
# task_type values that mean "we are blocked waiting on something/someone".
AWAITING_TASK_TYPES = {
    'awaiting_external',
    'client_followup',
    'primary_collection',
    'access_request',
    'awaiting_external_then_action',
}


def _parse_date(v):
    """'YYYY-MM-DD' / 'DD.MM.YYYY' / date -> date or None."""
    if v is None:
        return None
    if isinstance(v, _date):
        return v
    if not isinstance(v, str):
        return None
    s = v.strip()[:10]
    for fmt in ('%Y-%m-%d', '%d.%m.%Y'):
        try:
            return _dt.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _bucket(d, today, is_done):
    if is_done:
        return 'done'
    if d < today:
        return 'overdue'
    if d == today:
        return 'today'
    if (d - today).days <= 7:
        return 'this_week'
    return 'later'


def _iter_clients():
    """[(client_id, client_name)] from clients_index, via generate.clients."""
    try:
        import generate
        return [(c.get('id'), c.get('name_short', '')) for c in generate.clients]
    except Exception:
        try:
            from _loaders import load_clients_from_index
            return [(c.get('id'), c.get('name_short', ''))
                    for c in load_clients_from_index()]
        except Exception:
            return []


def collect_deadlines(today=None):
    """Unified deadline list across all clients, derived from state.

    Sources per client:
      - state/financials.json -> tax_calendar_2026[]  (kind='tax')
      - state/tasks.json       -> tasks[] with a due_date (kind='task')
    Returns rows sorted by date ascending; rows carry a precomputed `bucket`.
    """
    if today is None:
        import generate
        today = generate.TODAY
    import state_ops
    rows = []
    for cid, cname in _iter_clients():
        if not cid:
            continue
        # --- tax_calendar entries ---
        try:
            fin = state_ops.state_read(cid, 'financials.json') or {}
        except Exception:
            fin = {}
        for e in (fin.get('tax_calendar_2026') or []):
            d = _parse_date(e.get('date'))
            if d is None:
                continue
            status = (e.get('status') or '').strip()
            is_done = status.lower() in DONE_TAX_STATUSES
            amount = e.get('amount')
            if amount is None:
                amount = e.get('amount_estimated')
            rows.append({
                'client_id': cid,
                'client_name': cname,
                'date': d,
                'what': (e.get('what') or '').strip(),
                'amount': amount,
                'status': status,
                'kind': 'tax',
                'linked_task': e.get('linked_task'),
                'days_left': (d - today).days,
                'bucket': _bucket(d, today, is_done),
            })
        # --- tasks with a due_date ---
        try:
            tdata = state_ops.state_read(cid, 'tasks.json') or {}
        except Exception:
            tdata = {}
        for tsk in (tdata.get('tasks') or []):
            d = _parse_date(tsk.get('due_date'))
            if d is None:
                continue
            status = (tsk.get('status') or '').strip()
            is_done = status.lower() in DONE_TASK_STATUSES
            amount = (tsk.get('type_specific') or {}).get('amount')
            rows.append({
                'client_id': cid,
                'client_name': cname,
                'date': d,
                'what': (tsk.get('title') or '').strip(),
                'amount': amount,
                'status': status,
                'kind': 'task',
                'linked_task': tsk.get('id'),
                'days_left': (d - today).days,
                'bucket': _bucket(d, today, is_done),
            })
    rows.sort(key=lambda r: r['date'])
    return rows


def collect_awaiting(today=None):
    """Open tasks (across all clients) that wait on an external party.

    OPEN = status not in DONE_TASK_STATUSES. days_waiting counts from
    created_at (preferred) or due_date.
    Returns rows sorted by days_waiting descending.
    """
    if today is None:
        import generate
        today = generate.TODAY
    import state_ops
    rows = []
    for cid, cname in _iter_clients():
        if not cid:
            continue
        try:
            tdata = state_ops.state_read(cid, 'tasks.json') or {}
        except Exception:
            tdata = {}
        for tsk in (tdata.get('tasks') or []):
            ttype = (tsk.get('task_type') or tsk.get('type') or '').strip()
            if ttype not in AWAITING_TASK_TYPES:
                continue
            status = (tsk.get('status') or '').strip()
            if status.lower() in DONE_TASK_STATUSES:
                continue
            what = (tsk.get('title') or '').strip()
            if not what:
                continue
            ref = _parse_date(tsk.get('created_at')) or _parse_date(tsk.get('due_date'))
            days_waiting = (today - ref).days if ref else 0
            rows.append({
                'client_id': cid,
                'client_name': cname,
                'what': what,
                'days_waiting': max(0, days_waiting),
                'task_type': ttype,
                'status': status,
            })
    rows.sort(key=lambda r: r['days_waiting'], reverse=True)
    return rows


def deadlines_by_client(today=None):
    """Convenience index: client_id -> list[deadline rows]."""
    out = {}
    for r in collect_deadlines(today):
        out.setdefault(r['client_id'], []).append(r)
    return out


def awaiting_by_client(today=None):
    """Convenience index: client_id -> list[awaiting rows]."""
    out = {}
    for r in collect_awaiting(today):
        out.setdefault(r['client_id'], []).append(r)
    return out
