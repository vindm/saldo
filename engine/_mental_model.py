"""_mental_model.py — state-derived "mental model" assembly + track severity.

JSON-first (2026-06-19): the Markdown parser that used to read mental_model.md
was DELETED. The engine never parses mental_model.md anymore — that file is now
pure prose for the agent. Everything the dashboards consume (tracks, awaitings,
gaps, per-client snapshot/history, the v2 finmodel/calendar/plan sections) is
assembled FROM state/*.json + history.jsonl.

This module keeps the SAME public surface its callers relied on:
  - load_mental_models() -> {tracks, awaitings, gaps, by_client}
  - _track_severity(track, today) -> (color, badge)
so _overview_v2 / _aggregator / _clients_group / _client_dashboard_v2 keep working.
"""
import os
from datetime import date
import _vocab


def _parse_date_in_text(txt, today=None):
    """Finds the first DD.MM.YYYY or DD.MM date in a string.
    Returns date or None. The year defaults to the current one."""
    import generate
    TODAY = generate.TODAY
    import re as _re
    today = today or TODAY
    m = _re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', txt)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except Exception:
            return None
    m = _re.search(r'(\d{1,2})\.(\d{1,2})(?!\d)', txt)
    if m:
        try:
            return date(today.year, int(m.group(2)), int(m.group(1)))
        except Exception:
            return None
    return None


def _awaitings_from_state(client_id, client_name):
    """"Expectations" rows derived from state: tasks waiting on something external
    (status awaiting/awaiting_external, or task_type document_request)."""
    from _loaders import load_client_state_tasks
    tasks_data = load_client_state_tasks(client_id)
    if not tasks_data:
        return []
    out = []
    for t in (tasks_data.get('tasks') or []):
        status = t.get('status')
        ttype = t.get('task_type') or t.get('type')
        is_waiting = status in ('awaiting', 'awaiting_external') or ttype == 'document_request'
        if not is_waiting:
            continue
        what = (t.get('title') or '').strip()
        if not what:
            continue
        when = t.get('due_date') or ''
        na = (t.get('next_action') or '').strip()
        out.append({
            'client_id': client_id,
            'client_name': client_name,
            'what': what,
            'source': t.get('assignee', '') or '',
            'when': ('due ' + when) if when else (na or ''),
        })
    return out


def _gaps_from_state(client_id, client_name):
    """"Awaiting clarification" rows derived from state: OPEN QUESTIONS in risks.json
    (kind=='question'), which are the things we do not yet know."""
    from _loaders import load_client_state_risks
    risks_data = load_client_state_risks(client_id)
    if not risks_data:
        return []
    out = []
    for r in (risks_data.get('risks') or []):
        if r.get('severity') == 'green':
            continue
        if r.get('kind') != 'question':
            continue
        text = (r.get('title') or '').strip()
        if not text:
            continue
        out.append({
            'client_id': client_id,
            'client_name': client_name,
            'text': text[:140],
        })
    return out


def _by_client_from_state(client_id, client_name):
    """Per-client bundle (snapshot / history / v2 sections) built entirely from state."""
    from _loaders import (
        build_snapshot_firm_from_state,
        build_snapshot_in_progress_from_state,
        build_snapshot_unclear_from_state,
        build_history_from_state,
        build_v2_sections_from_state,
    )
    firm = build_snapshot_firm_from_state(client_id) or []
    in_progress = build_snapshot_in_progress_from_state(client_id) or []
    unclear = build_snapshot_unclear_from_state(client_id) or []
    history = build_history_from_state(client_id) or []
    v2 = build_v2_sections_from_state(client_id) or {}
    bundle = {
        'snapshot': {'firm': firm, 'in_progress': in_progress, 'unclear': unclear},
        'history': history,
    }
    bundle.update(v2)  # finmodel / tax_calendar / forward_plan / red_flags / behavior_pattern / source_links / counterparties
    return bundle


def load_mental_models():
    """Assemble the "mental model" view entirely from state (no Markdown parsing).

    Returns the same dict shape callers expect:
        {tracks: [...], awaitings: [...], gaps: [...], by_client: {cid: {...}}}
    - tracks: from state/tasks.json via _tracks.to_mm_format() (JSON, as before)
    - awaitings/gaps: derived from state (waiting tasks / open questions)
    - by_client[cid]: snapshot (firm/in_progress/unclear) + history + v2 sections
    """
    import generate
    clients = generate.clients

    try:
        from _tracks import to_mm_format
        tracks_mm = to_mm_format()
    except Exception:
        tracks_mm = {'tracks': []}

    out = {
        'tracks': tracks_mm.get('tracks', []),
        'awaitings': [],
        'gaps': [],
        'by_client': {},
    }
    for c in clients:
        cid = c.get('id')
        cname = c.get('name_short')
        out['awaitings'].extend(_awaitings_from_state(cid, cname))
        out['gaps'].extend(_gaps_from_state(cid, cname))
        out['by_client'][cid] = _by_client_from_state(cid, cname)

    # System-wide bucket kept for callers that look it up (no state → empty shells).
    out['by_client']['_system'] = {
        'snapshot': {'firm': [], 'in_progress': [], 'unclear': []},
        'history': [],
    }
    return out


def _track_severity(tr, today=None):
    import generate
    TODAY = generate.TODAY
    today = today or TODAY
    status = tr.get('status', 'active')
    if status == 'awaiting_external':
        return ('awaiting', 'waiting')
    if status == 'blocked':
        return ('red', 'blocked')
    if status == 'done':
        return ('grey', 'closed')
    nearest = None
    for field in ('title', 'context', 'next_action'):
        d = _parse_date_in_text(tr.get(field, ''), today)
        if d and d >= today:
            if nearest is None or d < nearest:
                nearest = d
    if nearest:
        delta = (nearest - today).days
        if delta <= 3:
            return ('red', f'{delta} d')
        if delta <= 7:
            return ('yellow', f'{delta} d')
        if delta <= 31:
            return ('yellow', f'{delta} d')
        return ('grey', f'{delta} d')
    return ('grey', 'routine')
