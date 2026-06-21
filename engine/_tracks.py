"""_tracks.py — CRUD + render API for tracks[] in clients_data.json.

Architecture decision:
- tracks = structured data (JSON)
- mental_model.md = narrative (Snapshot, Financial model, Risks, Counterparties, Pattern, Links, History)
- tracks are NO LONGER derived from mental_model

See also the skill `_system/skills/mm_update/SKILL.md`.
"""
import json
import re as _re
import shutil
import os
from datetime import date, datetime
from pathlib import Path


def _clients_data_path():
    """Returns the Path to clients_data.json. Via generate if available, otherwise hardcoded."""
    try:
        import generate
        return Path(generate._data_path) if hasattr(generate, '_data_path') else \
               Path(os.path.dirname(os.path.abspath(__file__))) / 'clients_data.json'
    except Exception:
        return Path(os.path.dirname(os.path.abspath(__file__))) / 'clients_data.json'


def load_all_tracks():
    """Loads all tracks of all clients from state/tasks.json.
    Phase 2 hotfix: source is state (clients_data.json archived)."""
    try:
        import state_ops
        from _loaders import load_clients_from_index
    except Exception:
        return []
    try:
        clients = load_clients_from_index()
    except Exception:
        clients = [{'id': cid, 'name_short': cid} for cid in state_ops.CLIENT_FOLDERS.keys()]
    out = []
    for c in clients:
        client_id = c.get('id')
        client_name = c.get('name_short', '')
        tasks_data = state_ops.state_read(client_id, 'tasks.json')
        if not isinstance(tasks_data, dict):
            continue
        for tr in (tasks_data.get('tasks') or []):
            out.append({
                **tr,
                'client_id': client_id,
                'client_name': client_name,
            })
    return out


def tracks_by_client(client_id):
    """All tracks of one client."""
    return [t for t in load_all_tracks() if t.get('client_id') == client_id]


def open_tracks_by_client(client_id):
    """Tracks of one client with status active or awaiting."""
    return [t for t in tracks_by_client(client_id) if t.get('status') in ('active', 'awaiting')]


def all_open_tracks():
    """All open tracks of all clients."""
    return [t for t in load_all_tracks() if t.get('status') in ('active', 'awaiting')]


def _save_clients_data(data):
    """DISABLED: clients_data.json was archived during the migration.
    Track writers were moved to state_ops + state/tasks.json (see below).
    The old call now fails loudly instead of silently writing to a dead file."""
    raise RuntimeError(
        "_save_clients_data is disabled: clients_data.json is archived. "
        "The source of truth for tracks is state/tasks.json via state_ops.state_write."
    )


def _load_tasks(client_id):
    """Read-modify-write helper: reads the whole state/tasks.json of a client.
    Returns (data, tasks_list). If the file is missing — a minimal structure."""
    import state_ops
    data = state_ops.state_read(client_id, 'tasks.json')
    if not isinstance(data, dict) or not data:
        data = {'schema_version': '2.0', 'client_id': client_id, 'tasks': []}
    data.setdefault('tasks', [])
    return data, data['tasks']


def _save_tasks(client_id, data, ctx):
    """Atomically writes the WHOLE dict back via state_ops (backup + UTF-8 + validation).
    Since we write back the entire object we read, top-level fields
    (tasks_overrides, schema_version, etc.) and manual decisions are preserved."""
    import state_ops
    from datetime import date
    data['last_updated'] = date.today().isoformat()
    state_ops.state_write(client_id, 'tasks.json', data, ctx=ctx)
    return True


def upsert_track(client_id, track):
    """Create or update a track by id in state/tasks.json.

    DECISION PROTECTION: updating an existing track does a MERGE
    (existing.update(track)), NOT a full replace — fields absent from the incoming
    dict (context, comments, completed_at, manual notes) are preserved.
    tasks_overrides and other top-level fields are not touched.
    """
    try:
        data, tasks = _load_tasks(client_id)
    except KeyError:
        return False
    tid = track.get('id')
    for t in tasks:
        if t.get('id') == tid:
            t.update(track)  # merge — do not overwrite existing fields
            return _save_tasks(client_id, data, ctx='upsert_track_{}'.format(tid or 'new'))
    tasks.append(track)
    return _save_tasks(client_id, data, ctx='new_track_{}'.format(tid or 'new'))


def add_history_event(client_id, track_id, event_text, source='', auto=False):
    """Append an event to a track's history (state/tasks.json).

    source is REQUIRED (attribution of the update to its source).
    Format `channel:detail`: owner:chat | tg:@user | email:sender |
    finkoper:#NNNNN | news:topic | T-Bank:statement | Alfa:statement | VTB:statement |
    OFD:Z-report | 1C | joint:session. event_text — human-readable
    description (not tech abbreviations).
    """
    from datetime import date, datetime
    if not source or not str(source).strip():
        raise ValueError(
            "add_history_event: source is required (format channel:detail, "
            "e.g. tg:@user / email:tax-authority / finkoper:#123 / owner:chat). "
            "Every update must be attributed to a source."
        )
    try:
        data, tasks = _load_tasks(client_id)
    except KeyError:
        return False
    for t in tasks:
        if t.get('id') == track_id:
            t.setdefault('history', []).append({
                'date': date.today().isoformat(),
                'ts': datetime.now().astimezone().isoformat(timespec='seconds'),
                'event': event_text,
                'source': source,
                'auto': auto,
            })
            return _save_tasks(client_id, data, ctx='history_{}'.format(track_id))
    return False


def update_status(client_id, track_id, new_status, reason=''):
    """Change a track's status + add a history event (state/tasks.json).
    On close (done/completed/dismissed) sets completed_at."""
    from datetime import date, datetime
    try:
        data, tasks = _load_tasks(client_id)
    except KeyError:
        return False
    for t in tasks:
        if t.get('id') == track_id:
            old = t.get('status', 'active')
            t['status'] = new_status
            if new_status in ('done', 'completed', 'dismissed') and not t.get('completed_at'):
                t['completed_at'] = date.today().isoformat()
            t.setdefault('history', []).append({
                'date': date.today().isoformat(),
                'ts': datetime.now().astimezone().isoformat(timespec='seconds'),
                'event': 'Status: {} -> {}'.format(old, new_status) + (' ({})'.format(reason) if reason else ''),
                'auto': False,
            })
            return _save_tasks(client_id, data, ctx='status_{}_{}'.format(track_id, new_status))
    return False


# ============== Render adapter (for compatibility with the old mm dict format) ==============

def _track_severity(track, today=None):
    """Color + badge for a track. Signature-compatible with _mental_model._track_severity."""
    today = today or date.today()
    status = track.get('status', 'active')
    if status == 'awaiting':
        return ('awaiting', 'waiting')
    if status == 'done':
        return ('grey', 'closed')
    # Active — look at due_date
    due = track.get('due_date')
    if due:
        try:
            d = date(*[int(x) for x in due.split('-')])
            delta = (d - today).days
            if delta < 0:
                return ('red', f'overdue {abs(delta)} d')
            if delta <= 3:
                return ('red', f'{delta} d')
            if delta <= 31:
                return ('yellow', f'{delta} d')
            return ('grey', f'{delta} d')
        except Exception:
            pass
    return ('grey', 'routine')


def to_mm_format():
    """Returns a structure compatible with the old mm format (for existing renderers).
    {tracks: [...], awaitings: [...], gaps: [...], by_client: {...}}

    v2: for clients with a populated state/tasks.json —
    tracks come from state (single source of truth, migration complete).
    Fallback: tracks from clients_data.json[].tracks[] (old schema).
    """
    out = {'tracks': [], 'awaitings': [], 'gaps': [], 'by_client': {}}

    # Phase 2 hotfix: load clients from state via clients_index.
    try:
        from _loaders import load_clients_from_index, load_client_state_tasks, state_tasks_to_mm_format
        _state_available = True
    except Exception:
        _state_available = False
    try:
        data = load_clients_from_index() if _state_available else []
    except Exception:
        data = []
    if not data:
        return out

    for c in data:
        client_id = c.get('id')
        client_name = c.get('name_short', '')

        # v2: try to read state/tasks.json
        state_tracks = None
        if _state_available and client_id:
            try:
                state_data = load_client_state_tasks(client_id)
                if state_data and state_data.get('tasks'):
                    state_tracks = state_tasks_to_mm_format(state_data, client_name=client_name)['tracks']
            except Exception:
                state_tracks = None

        source_tracks = state_tracks if state_tracks is not None else (c.get('tracks') or [])

        for tr in source_tracks:
            if state_tracks is not None:
                mm_track = dict(tr)
                mm_track['client_id'] = client_id
                mm_track['client_name'] = client_name
                mm_track.setdefault('zone', 'client_work')
                if not mm_track.get('track_id'):
                    # P2-hotfix: track_id = the full state.id, without split('_')[-1].
                    # Previously only the last fragment was used → the ID in the plan did not match the ID
                    # on the client dashboard, and the modal opened different cards.
                    mm_track['track_id'] = tr.get('id', '') or ''
                if mm_track.get('status') == 'awaiting':
                    mm_track['status'] = 'awaiting_external'
                ctx = mm_track.get('context', '') or ''
                nx = mm_track.get('next_action', '') or ''
                mm_track['context_full'] = ctx
                mm_track['next_action_full'] = nx
                mm_track['context'] = ctx[:400]
                mm_track['next_action'] = nx[:500]
                mm_track.setdefault('reply_draft', '')
                mm_track.setdefault('raw', '')
                mm_track['derived_from'] = 'state/tasks.json'
                mm_track['urgent'] = (tr.get('priority') == 'high')
                mm_track['_full_track'] = tr
            else:
                mm_track = {
                    'client_id': client_id,
                    'client_name': client_name,
                    'zone': 'client_work',
                    'track_id': tr.get('id', '') or '',  # P2-hotfix: full ID
                    'title': tr.get('title', ''),
                    'status': 'awaiting_external' if tr.get('status') == 'awaiting' else tr.get('status', 'active'),
                    'context': tr.get('context', '')[:400],
                    'next_action': tr.get('next_action', '')[:500],
                    'context_full': tr.get('context', ''),
                    'next_action_full': tr.get('next_action', ''),
                    'reply_draft': tr.get('reply_draft', ''),
                    'raw': '',
                    'derived_from': 'clients_data.json',
                    'urgent': tr.get('urgent', False),
                    '_full_track': tr,
                }
            out['tracks'].append(mm_track)
    return out
