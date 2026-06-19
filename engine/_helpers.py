"""_helpers.py — shared utilities for generate.py and its modules.

Extracted from generate.py as part of the decomposition refactor.

Late binding: functions that depend on the `clients` and `DIARY_INBOX`
globals from generate.py import generate inside the body — this breaks the
import cycle at module level.
"""
import os
import json
from datetime import datetime as _dt


def _esc(s):
    """HTML-text-safe."""
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def _esca(s):
    """HTML-attribute-safe (for data-prompt and href)."""
    return _esc(s).replace('"', '&quot;').replace("'", '&#39;')


# ── Dynamic client grouping (the per-client `group` field) ──────────────
# Clients are tagged with a free-form `group` value in clients_index.json
# (e.g. "team", "direct", "archive", ...). The engine derives the set of
# groups from the data — nothing about the group names is hardcoded.

DEFAULT_GROUP = 'ungrouped'  # graceful fallback when a client has no `group`


def client_group(c):
    """The group label of a client dict. Falls back to DEFAULT_GROUP."""
    g = (c.get('group') if isinstance(c, dict) else None)
    g = (g or '').strip()
    return g or DEFAULT_GROUP


def _slugify_group(name):
    """ASCII slug for filenames / DOM ids / sidebar keys.

    Lowercases, keeps a-z 0-9, collapses every other run into a single '-'.
    Empty result → 'group'. Used for clients_<slug>.html etc.
    """
    import re as _r
    s = (name or '').strip().lower()
    s = _r.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s or 'group'


def _group_label(name):
    """Human label for a group — Title Case of the raw value, localized via t().

    The raw group token (e.g. "team"/"direct") is Title-cased to the English
    display key ("Team"/"Direct"), then passed through the chrome catalog so the
    ru locale renders its localized name. Unknown groups fall back to their
    Title-cased English form."""
    from _strings import t
    return t((name or DEFAULT_GROUP).strip().title())


def dynamic_groups(clients):
    """Distinct group values across clients, in first-seen order.

    Returns list[str] of raw group names (not slugs). No group list is
    hardcoded — the order follows the order clients appear in the index.
    """
    seen = []
    for c in (clients or []):
        g = client_group(c)
        if g not in seen:
            seen.append(g)
    return seen


def clients_in_group(clients, group_name):
    """All clients whose group == group_name (raw value match)."""
    return [c for c in (clients or []) if client_group(c) == group_name]


# Global translation of technical terms in visible text.
# Applied in render functions BEFORE _esc so it does not touch HTML attributes, classes, JS.
import re as _re
_TECH_TERMS_RU = {
    'awaiting_external': 'awaiting external signal',
    'closed_external_pending': 'closed, awaiting external',
    'awaiting': 'awaiting',
    'active': 'active',
    'blocked': 'blocked',
    'done': 'closed',
    'gap': 'gap',
    'check': 'check',
    'not_needed': 'not needed',
    'lifecycle_state': 'state',
    'expected_event': 'expected event',
    'client_work': 'client work',
    'system_internal': 'system',
    'Tinkoff SME Accounting': 'T-Bank accounting',
    'blocked_by': 'depends on',
    'pattern': 'pattern',
    'owner': 'owner',
    'email': 'email',
    'state': 'data',
    'mental_model': 'model',
    'uuid': 'id',
    'Finkoper': 'Finkoper',
    'finkoper': 'Finkoper',
    'Tinkoff': 'T-Bank',
    'Accounting': 'accounting',
    'Marketlead': 'Marketlead',
    'Anna': 'Anna',
    'Nazarova': 'Client A',
    'xls': 'spreadsheet',
    'PDF': 'document',
}
# Sort by length ↓ so 'awaiting_external' is replaced BEFORE 'awaiting'
_TECH_PATTERN = _re.compile(
    r'\b(' + '|'.join(sorted(_TECH_TERMS_RU.keys(), key=len, reverse=True)) + r')\b'
)

def _translate_tech_terms(text):
    """Replaces known technical terms from the mental_model with display equivalents.
    Leaves anything inside backticks (`code`) untouched — there we keep the original."""
    if not text:
        return text
    s = str(text)
    # Split into chunks: do not touch content inside backticks
    parts = _re.split(r'(`[^`]*`)', s)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            # code in backticks — leave as is
            out.append(part)
        else:
            p = _TECH_PATTERN.sub(lambda m: _TECH_TERMS_RU[m.group(1)], part)
            # strip internal snake_case ids (Latin), without touching Cyrillic:
            p = _re.sub(r'\s*\([a-z][a-z0-9]*_[a-z0-9_]+\)', '', p)   # (some_id)
            p = _re.sub(r'\b[a-z][a-z0-9]*_[a-z0-9_]+\b', '', p)       # bare snake_id
            p = _re.sub(r'\(\s*[A-Za-z][A-Za-z0-9]*-[A-Za-z0-9-]+\s*\)', '', p)  # (cp-...-id)
            p = _re.sub(r'\b[A-Za-z][A-Za-z0-9]*-[A-Za-z0-9]+-[A-Za-z0-9-]+\b', '', p)  # latin a-b-c id
            p = _re.sub(r'\(\s*\)', '', p)
            p = _re.sub(r' {2,}', ' ', p).replace(' )', ')').replace('( ', '(').replace(' ,', ',').replace(' .', '.').strip()
            out.append(p)
    return ''.join(out)


def _short(s, n=70):
    s = (s or '').strip().replace('\n', ' ')
    return s if len(s) <= n else s[:n-1] + '…'


def _format_date_ru(d):
    """13 May, Wednesday (full day name). Localized via _strings (MONTHS_GEN
    + full weekday names selected by LOCALE)."""
    from _strings import MONTHS_GEN, WEEKDAYS_FULL
    return f"{d.day} {MONTHS_GEN[d.month-1]}, {WEEKDAYS_FULL[d.weekday()]}"


def _snapshot_time():
    """HH:MM from snapshot_meta.json or now()."""
    import generate
    try:
        path = os.path.join(os.path.dirname(generate.DIARY_INBOX),
                            'finkoper_state', 'latest', 'snapshot_meta.json')
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                meta = json.load(f)
            s = meta.get('last_run', '')
            if s:
                return _dt.fromisoformat(s.replace('Z', '+00:00')).strftime('%H:%M')
    except Exception:
        pass
    return _dt.now().strftime('%H:%M')


def _client_by_name(name):
    """Find a client from `clients` by string match on the name."""
    import generate
    if not name:
        return None
    for c in generate.clients:
        if c['name_short'] in name or name in c['name_short']:
            return c
        fam = c['name_short'].replace('SP ', '').split(' ')[0]
        if fam and fam in name:
            return c
    return None


def _load_chats():
    """Returns the list of chats from chats.json or []."""
    import generate
    try:
        path = os.path.join(os.path.dirname(generate.DIARY_INBOX),
                            'finkoper_state', 'latest', 'chats.json')
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _load_all_tasks():
    """Returns the list of all tasks from tasks.json or [].

    Merges in internal_status and expected_event from clients[i].tasks_overrides[task_id].
    internal_status semantics (our system, not Finkoper):
      - 'working'           — task is actively in progress (default)
      - 'awaiting_external' — waiting for an external event, hide from URGENT/WEEK
      - 'escalated'         — escalated to the manager, awaiting a decision
    """
    import generate
    try:
        p = os.path.join(os.path.dirname(generate.DIARY_INBOX),
                         'finkoper_state', 'latest', 'tasks.json')
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                tasks = json.load(f)
        else:
            tasks = []
    except Exception:
        tasks = []
    overrides = {}
    for c in generate.clients:
        for tid, ov in (c.get('tasks_overrides') or {}).items():
            overrides[str(tid)] = ov
    for t in tasks:
        tid = str(t.get('id', ''))
        ov = overrides.get(tid)
        if ov:
            t['internal_status'] = ov.get('internal_status', 'working')
            if ov.get('expected_event'):
                t['expected_event'] = ov['expected_event']
        else:
            t.setdefault('internal_status', 'working')
    return tasks


def _client_folder_name(c):
    """Client folder name.
    From name_short='SP Client A X.X.' take 'SP Client A'."""
    parts = (c.get('name_short') or '').split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return c.get('name_short') or ''


def _parse_date_in_text(txt, today=None):
    """Finds the first DD.MM.YYYY or DD.MM date in the string.
    Returns a date or None. Default year = current."""
    import re as _re
    from datetime import date
    import generate
    today = today or generate.TODAY
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


# === R8: track aging (escalation by age) — shared helper for lint and views ===
# Age = days since the last movement (max date in the track's history[], fallback created_at).
# Only active/waiting tracks (not deferred/done). Thresholds by priority.
_R8_STALE_DAYS = {'high': 14, 'normal': 30, 'low': 60}
_R8_STATUSES = ('active', 'open', 'awaiting', 'awaiting_external')


def _r8_parse(d):
    try:
        return _dt.strptime(str(d).split('T')[0][:10], '%Y-%m-%d').date()
    except Exception:
        return None


def track_last_activity_days(tr, today):
    """Days since the track's last movement. None if there are no dates."""
    dates = []
    for h in (tr.get('history') or []):
        d = _r8_parse(h.get('date') or h.get('ts'))
        if d:
            dates.append(d)
    cr = _r8_parse(tr.get('created_at'))
    if cr:
        dates.append(cr)
    return (today - max(dates)).days if dates else None


def track_stale_days(tr, today):
    """Number of days stale if the track is aged out per R8; otherwise None."""
    if tr.get('status') not in _R8_STATUSES:
        return None
    days = track_last_activity_days(tr, today)
    if days is None:
        return None
    thr = _R8_STALE_DAYS.get(tr.get('priority', 'normal'), 30)
    return days if days >= thr else None
