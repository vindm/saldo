"""_aggregator.py — single mental model of tasks.

Redesign stage 4: glues tasks from all system sources into one sorted,
deduplicated list split into groups.

Sources:
  1. calendar registry              — statutory reporting deadlines
  2. monthly_check.sources[]        — what is in progress this month
  3. Finkoper tasks + tasks_overrides — tasks from Finkoper chats
  4. request log                    — my outgoing requests awaiting a reply
  5. mental_model.tracks            — active client tracks
  6. journal/inbox/updates_*        — what the updater proposed (needs_manual)

Minus:
  - dismissed_anomalies (from the client JSON)
  - entries in the decisions log with an anomaly_id (dismissed)

Groups (by priority, top to bottom):
  - hot:     overdue or deadline <= 3 days
  - today:   deadline today or 4-7 days
  - pending: my request, waiting on a reply from the client/colleague
  - quick:   card gaps, small tasks with no clear deadline
"""
import os
from datetime import datetime as _dt, timedelta
import _vocab


def _safe_date(val, today):
    """Converts various date formats into a date or None."""
    if val is None:
        return None
    if hasattr(val, 'date'):
        return val.date()
    if hasattr(val, 'year') and hasattr(val, 'month'):
        return val
    if isinstance(val, str):
        for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d.%m.%y'):
            try:
                return _dt.strptime(val.strip(), fmt).date()
            except Exception:
                continue
    return None


def _classify_group(due_date, today):
    """Determines the group from the deadline date."""
    if due_date is None:
        return 'quick'
    delta = (due_date - today).days
    if delta < 0:
        return 'hot'  # overdue
    if delta <= 3:
        return 'hot'
    if delta <= 7:
        return 'today'
    return 'today' if delta <= 14 else 'quick'


def aggregate_tasks(today=None):
    """Main function. Returns a dict with 4 groups.

    Returns: {
        'hot':     [task, task, ...],
        'today':   [task, task, ...],
        'pending': [task, task, ...],
        'quick':   [task, task, ...],
        'all':     [task, task, ...],   # all together, for convenience
    }

    Each task:
        {
            'id': str,           # unique identifier
            'client_id': str,    # client ID or None for system-wide items
            'client_name': str,  # client name
            'track': str,        # client group label (e.g. 'team'|'direct') | None
            'what': str,         # what needs to be done
            'due_date': date,    # when
            'days_left': int,    # days until the deadline (negative = overdue)
            'priority': str,     # 'overdue' | 'urgent' | 'soon' | 'plan' | 'open'
            'source': str,       # 'calendar' | 'monthly_check' | 'finkoper'
                                 # 'request' | 'track' | 'update'
            'source_ref': str,   # source reference/id
            'group': str,        # 'hot' | 'today' | 'pending' | 'quick'
        }
    """
    import generate
    from _loaders import (
        load_daemon_finkoper, load_daemon_updates,
    )
    from _deadlines import collect_deadlines, collect_awaiting
    from _mental_model import load_mental_models

    today = today or generate.TODAY
    PLAN_DIR = generate.PLAN_DIR
    DIARY_INBOX = generate.DIARY_INBOX
    clients = generate.clients

    # Map id -> client for quick access
    clients_by_id = {c['id']: c for c in clients}
    clients_by_name = {c['name_short']: c for c in clients}
    # Alias by family name
    clients_by_family = {}
    for c in clients:
        fam = c['name_short'].replace(_vocab.agg('sp_prefix'), '').split(' ')[0]
        clients_by_family.setdefault(fam, c)

    # Dismissed anomalies: from the client state (dismissed_anomalies). Decisions log is audit-only.
    today_iso = today.isoformat()

    def is_dismissed(client_obj, anomaly_id):
        if not anomaly_id:
            return False
        aid = anomaly_id.strip()
        if not aid:
            return False
        if client_obj:
            for d in client_obj.get('dismissed_anomalies') or []:
                if d.get('anomaly_id') == aid:
                    until = d.get('until')
                    if not until or until >= today_iso:
                        return True
        return False

    tasks = []

    # NOTE: tax_calendar is NOT a direct render source. It is an external input
    # (collected ~monthly by a daemon) that HELPS create tracks in state; the work
    # items it implies live as tracks in tasks.json and are surfaced via Source 5
    # below. Reading tax_calendar directly here surfaced stale duplicates (e.g. an
    # item a track had already deferred), so this source was removed.

    # ====== Source 3: Finkoper tasks (team only) ======
    try:
        daemon_fk = load_daemon_finkoper(DIARY_INBOX, today)
    except Exception:
        daemon_fk = None
    if daemon_fk:
        all_tasks = []
        if hasattr(daemon_fk, 'get'):
            all_tasks = (daemon_fk.get('overdue') or []) + (daemon_fk.get('soon') or []) + (daemon_fk.get('normal') or [])
        for t in all_tasks:
            cid = t.get('client_id')
            c_obj = clients_by_id.get(cid)
            if not c_obj:
                continue
            # Check tasks_overrides — it may already be closed
            task_id_str = str(t.get('id') or t.get('task_id') or '')
            overrides = c_obj.get('tasks_overrides') or {}
            ov = overrides.get(task_id_str) or {}
            if ov.get('internal_status') in ('closed_external_pending', 'closed'):
                continue
            dl = _safe_date(t.get('deadline'), today)
            what = (t.get('title') or t.get('what') or 'Finkoper task').strip()[:120]
            days_left = (dl - today).days if dl else None
            tasks.append({
                'id': f"fk_{c_obj['id']}_{task_id_str}",
                'client_id': c_obj['id'],
                'client_name': c_obj['name_short'],
                'track': 'team',
                'what': what,
                'due_date': dl,
                'days_left': days_left,
                'priority': 'overdue' if (days_left is not None and days_left < 0) else 'urgent' if (days_left is not None and days_left <= 3) else 'soon' if (days_left is not None and days_left <= 7) else 'plan',
                'source': 'finkoper',
                'source_ref': task_id_str,
                'group': _classify_group(dl, today) if dl else 'today',
                'details': {
                    'Task': '#' + task_id_str,
                    'Deadline': dl.strftime('%d.%m.%Y') if dl else '—',
                    'Status': (t.get('status') or '—'),
                    'Description': (t.get('description') or t.get('comment') or '—'),
                },
            })

    # ====== Source 4: REMOVED (request log registry) — JSON-first 2026-06-19 ======
    # The request-log registry was retired. "Awaiting / pending" items now live in
    # state/tasks.json (task_type in the awaiting set) and are already surfaced via
    # Source 5 (tracks: an awaiting task becomes a track with status
    # awaiting_external). Re-adding them here from a separate source would
    # double-count. See _deadlines.collect_awaiting for the panel/health feed.

    # ====== Source 5: mental_model.tracks ======
    try:
        mm = load_mental_models()
    except Exception:
        mm = {'tracks': []}
    for tr in mm.get('tracks', []) or []:
        if tr.get('zone', 'client_work') == 'system_internal':
            continue
        if tr.get("status") in ("done", "dropped", "dismissed", "completed", "cancelled", "closed", "resolved", "deferred"):
            continue
        # show awaiting_external — these are tracks we plan for too
        cid = tr.get('client_id')
        c_obj = clients_by_id.get(cid) if cid else None
        what = (tr.get('title') or 'Active track').strip()[:120]
        track_id = tr.get('track_id') or ''
        ft = tr.get('_full_track') or {}
        # Open questions are NOT plan tasks — they are clarifications shown in the
        # dashboard "Questions" zone (_brief.py reads them straight from state).
        _tt = ft.get('task_type') or ft.get('type') or tr.get('task_type') or tr.get('type') or ''
        if _tt == 'open_question':
            continue
        # Priority: context_full > context; next_action_full > next_action
        ctx = (ft.get('context_full') or tr.get('context') or '—')
        nxt = (ft.get('next_action_full') or tr.get('next_action') or '—')
        # due_date from _full_track if present
        ft_due = _safe_date(ft.get('due_date'), today)
        ft_dl = (ft_due - today).days if ft_due else None
        ft_grp = _classify_group(ft_due, today) if ft_due else ('today' if tr.get('status') == 'active' else 'quick')
        # Additional fields
        owner = ft.get('owner') or tr.get('owner') or ''
        last_event = ft.get('last_event') or ''
        amount_raw = ft.get('amount')
        amount_str = ('{:,.0f}'.format(float(amount_raw)).replace(',', ' ') + ' ₽') if amount_raw else ''
        linked = ft.get('linked') or {}
        linked_parts = []
        if linked.get('finkoper_task'):
            linked_parts.append('Finkoper #' + str(linked['finkoper_task']))
        if linked.get('photos'):
            linked_parts.append(str(len(linked['photos'])) + ' photos')
        linked_str = ', '.join(linked_parts)
        # history for the timeline
        history_list = ft.get('history') or []
        # details dict
        det = {}
        det['track'] = track_id
        det['status'] = tr.get('status') or '—'
        if owner:
            det['Assignee'] = owner
        det['context'] = ctx
        if last_event:
            det['Last event'] = last_event
        if amount_str:
            det['Amount'] = amount_str
        if linked_str:
            det['Related'] = linked_str
        det['next_action'] = nxt
        tasks.append({
            'id': f"tr_{cid or 'sys'}_{track_id}_{what[:30]}",
            'client_id': cid,
            'client_name': c_obj['name_short'] if c_obj else (tr.get('client_name') or 'systemwide'),
            'track': (c_obj.get('group') if c_obj else None),
            'what': what,
            'due_date': ft_due,
            'days_left': ft_dl,
            'priority': 'plan',
            'source': 'track',
            'task_type': ft.get('task_type') or ft.get('type') or tr.get('task_type') or tr.get('type') or '',
            'period': (ft.get('type_specific') or {}).get('period') or (ft.get('type_specific') or {}).get('quarter') or '',
            'status': tr.get('status') or ft.get('status') or '',
            'source_ref': track_id,
            'group': ft_grp,
            'details': det,
            '_history': history_list,
        })

    # ====== Source 6: updates_* needs_manual ======
    try:
        daemon_upd = load_daemon_updates(DIARY_INBOX, today)
    except Exception:
        daemon_upd = None
    if daemon_upd and isinstance(daemon_upd, dict):
        nm_list = daemon_upd.get('needs_manual') or []
        for u in nm_list:
            cname = u.get('client', '')
            c_obj = clients_by_name.get(cname)
            what = ('Updater: ' + (u.get('title') or u.get('what') or '')).strip()[:120]
            tasks.append({
                'id': f"upd_{cname}_{what[:30]}",
                'client_id': c_obj['id'] if c_obj else None,
                'client_name': c_obj['name_short'] if c_obj else (cname or 'general'),
                'track': (c_obj.get('group') if c_obj else None),
                'what': what,
                'due_date': None,
                'days_left': None,
                'priority': 'open',
                'source': 'update',
                'source_ref': u.get('id') or '',
                'group': 'today',
                'details': {
                    'What the updater proposed': u.get('title') or u.get('what') or '—',
                    'Description': u.get('description') or '—',
                    'Trigger source': u.get('trigger') or '—',
                },
            })

    # ====== Source 7: TG messages (journal/inbox/tg_<today>.md) ======
    # Parse markdown from tg/morning_full_scan: sections like the client header with @username and a new-message count
    # with the "needs reply" marker — these are pending tasks
    import re as _re
    tg_path = os.path.join(DIARY_INBOX, f'tg_{today.isoformat()}.md')
    if os.path.exists(tg_path):
        try:
            with open(tg_path, encoding='utf-8') as f:
                tg_md = f.read()
            sections = _re.split(r'\n## ', tg_md)
            for sec in sections[1:]:
                lines = sec.split('\n')
                if not lines:
                    continue
                header = lines[0]
                # Locale-driven (see _vocab): "<sp_prefix>Name (@user) — N <new_word>".
                # The prefix stays INSIDE the capture group — client_name is looked
                # up in clients_by_name WITH its prefix.
                _sp = _re.escape(_vocab.agg('sp_prefix'))
                _new = _re.escape(_vocab.agg('new_word'))
                m = _re.match(r'(' + _sp + r'[^(—]+?)\s*\(([^)]+)\)\s*—\s*(\d+)\s*' + _new, header)
                if not m:
                    continue
                client_name = m.group(1).strip()
                tg_username = m.group(2).strip()
                count = int(m.group(3))
                if count == 0:
                    continue
                c_obj = clients_by_name.get(client_name)
                if not c_obj:
                    continue
                _nr = _vocab.agg('needs_reply')
                msg_lines = [ln for ln in lines if '❓' in ln or _nr.lower() in ln.lower()]
                if not msg_lines:
                    continue
                for i, msg in enumerate(msg_lines):
                    raw = msg.strip()
                    # Extract the time at the start (if present)
                    time_m = _re.search(r'\*\*(\d{1,2}:\d{2})\*\*', raw)
                    time_str = time_m.group(1) if time_m else ''
                    # Extract the text after the "<needs_reply>:" marker (locale-driven)
                    _nr_pat = _re.escape(_nr).replace(r'\ ', r'\s*')
                    after = _re.search(r'❓\s*' + _nr_pat + r':?\s*(.+)$', raw, _re.IGNORECASE)
                    if after:
                        clean_text = after.group(1).strip()
                    else:
                        # Fallback: everything after the first ": "
                        clean_text = raw.split(']:', 1)[-1].strip() if ']:' in raw else raw
                        clean_text = clean_text.lstrip('- *').strip()
                    what_pretty = (f'❓ TG {time_str}: ' if time_str else '❓ TG: ') + clean_text[:120]
                    tasks.append({
                        'id': f"tg_{c_obj['id']}_{today.isoformat()}_{i}",
                        'client_id': c_obj['id'],
                        'client_name': c_obj['name_short'],
                        'track': c_obj.get('group', 'direct'),
                        'what': what_pretty,
                        'due_date': None,
                        'days_left': 0,
                        'priority': 'urgent',
                        'source': 'tg',
                        'source_ref': tg_username,
                        'group': 'pending',
                        'details': {
                            'TG-username': tg_username,
                            'Full message': raw,
                            'Time': time_str or '—',
                            'Day snapshot': f'tg_{today.isoformat()}.md',
                        },
                    })
        except Exception as e:
            print(f'[tg] parsing tg_<date>.md failed: {e}')

    # ====== Deduplication: by id AND by (client_id, normalized what) ======
    seen_ids = set()
    seen_keys = set()
    unique_tasks = []
    for t in tasks:
        if t['id'] in seen_ids:
            continue
        # Semantic key: same client + same task = duplicate
        sem_key = (t.get('client_id'), (t.get('what') or '')[:60].strip().lower())
        if sem_key in seen_keys:
            continue
        seen_ids.add(t['id'])
        seen_keys.add(sem_key)
        unique_tasks.append(t)

    # Sort within groups: hot — by days_left ASC; pending — by days waiting DESC
    def _hot_sort_key(t):
        dl = t.get('days_left')
        return (0 if dl is None else dl)

    def _pending_sort_key(t):
        # days_left for pending = -days_waiting (a large negative = waiting a long time)
        return t.get('days_left') or 0

    groups = {'hot': [], 'today': [], 'pending': [], 'quick': []}
    for t in unique_tasks:
        g = t.get('group', 'quick')
        groups.setdefault(g, []).append(t)

    groups['hot'].sort(key=_hot_sort_key)
    groups['today'].sort(key=lambda t: (t.get('days_left') is None, t.get('days_left') or 999))
    groups['pending'].sort(key=_pending_sort_key)
    groups['quick'].sort(key=lambda t: t.get('client_name', ''))

    groups['all'] = unique_tasks
    return groups


def aggregate_by_day(days=14, today=None):
    """Groups tasks by date (for the Week/Month views).

    Returns: {date: [task, task, ...], ...}
    """
    import generate
    today = today or generate.TODAY
    all_groups = aggregate_tasks(today)
    by_day = {}
    horizon = today + timedelta(days=days)
    for t in all_groups['all']:
        dl = t.get('due_date')
        if dl and today <= dl <= horizon:
            by_day.setdefault(dl, []).append(t)
    return by_day

def get_loose_tasks(today=None):
    """Tasks without a clear date — shown as a separate block in Week/Month.

    Includes:
      - active tracks from mental_model (no due_date by nature)
      - monthly_check.sources[] without a deadline (if any)
      - updater needs_manual without a due date

    Does NOT include: pending (they have a separate section in Today).
    """
    g = aggregate_tasks(today)
    loose = [t for t in g['all'] if not t.get('due_date') and t.get('group') != 'pending']
    # Sort: tracks -> monthly_check -> updates
    src_order = {'track': 0, 'monthly_check': 1, 'update': 2, 'finkoper': 3, 'request': 4}
    loose.sort(key=lambda t: (src_order.get(t.get('source'), 9), t.get('client_name', '')))
    return loose

