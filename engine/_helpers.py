"""_helpers.py — shared utilities for generate.py and its modules.

Extracted from generate.py as part of the decomposition refactor.

Late binding: functions that depend on the `clients` and `DIARY_INBOX`
globals from generate.py import generate inside the body — this breaks the
import cycle at module level.
"""
import os
import json
import hashlib
from datetime import datetime as _dt


def _avatar_color(name):
    """Deterministic, near-unique pastel colour per client (stable hash → HSL).

    Not a fixed palette: the hue spans the full 360° circle, so any number of
    clients each get their own colour. A secondary hash dimension nudges
    saturation/lightness so clients with near hues still separate. Text colour
    tracks the hue at a fixed darker S/L for readable initials."""
    d = hashlib.md5((name or 'x').strip().encode('utf-8')).hexdigest()
    hue = int(d[:4], 16) % 360
    v = int(d[4:6], 16)
    sat = 56 + (v % 3) * 10          # 56 / 66 / 76
    lig = 90 + ((v // 3) % 3)        # 90 / 91 / 92
    return 'hsl(%d,%d%%,%d%%)' % (hue, sat, lig), 'hsl(%d,46%%,33%%)' % hue


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


def tg_dm_url(username):
    """The single canonical Telegram open-a-chat deep-link for a handle.

    Accepts a bare or '@'-prefixed handle, returns `https://web.telegram.org/k/#@<handle>`
    (the `/k/` deep-link is the verified way to OPEN a chat; `/a/#…` does not navigate —
    see `connectors/tg/ui_playbook.md`). None for an empty/handle-less channel, so a
    display-name-only telegram channel yields no link.
    """
    h = str(username or '').lstrip('@').strip()
    return f"https://web.telegram.org/k/#@{h}" if h else None


def _format_date_ru(d):
    """13 May, Wednesday (full day name). Localized via _strings (MONTHS_GEN
    + full weekday names selected by LOCALE)."""
    from _strings import MONTHS_GEN, WEEKDAYS_FULL
    return f"{d.day} {MONTHS_GEN[d.month-1]}, {WEEKDAYS_FULL[d.weekday()]}"


_AVATAR_PALETTE = [
    '#E6F1FB:#185FA5', '#FBE9E6:#A53A18', '#EAF3DE:#3B5E2A', '#F3E6FB:#6B2AA5',
    '#FBF3D9:var(--accent-yellow)', '#E0F3F1:#1A6E64', '#FBE6F0:#A52A6B', '#EDEBFE:#534AB7',
    'var(--bg-subtle):#6B5A3A', '#E6F7FB:#176B85', '#F1F0DC:#5F6B1A', '#FBEAD9:#A55A18',
]

_SRC_LABELS = {
    'tg': 'TG', 'telegram': 'TG', 'email': 'почта', 'mail': 'почта',
    'finkoper': 'Финкопер', 'news': 'новости', 'tbank': 'ТБанк',
    'alfa': 'Альфа', 'alfabank': 'Альфа', 'vtb': 'ВТБ', 'ofd': 'ОФД',
    'operator': 'Ирина', 'cowork': 'Ирина', 'owner': 'Ирина',
    'joint': 'сессия', 'session': 'сессия', '1c': '1С', '1с': '1С',
    # automated daemons / collectors → readable operator labels (not raw ids)
    'resolution_sweep': 'авто-разбор', 'deadline_monitor': 'монитор сроков',
    'threshold_monitor': 'монитор порога', 'staleness_monitor': 'монитор',
    'mm_update': 'система', 'dashboards': 'система',
    # chat / manual entry by the operator
    'chat_irina': 'чат', 'chat': 'чат', 'чат': 'чат',
    'finkoper_chat': 'Финкопер', 'manual': 'вручную',
    # closed-vocabulary channels (policies/event-sources.md)
    'bank': 'банк', 'document': 'документ', 'system': 'система',
    'migration': 'импорт', 'миграция': 'импорт',
    'whatsapp': 'WhatsApp', 'max': 'MAX',
    'egrul': 'ЕГРЮЛ', 'websbor': 'Росстат',
}

# A source whose channel is an unmapped machine id (latin snake_case / digits)
# collapses to this generic label so the operator never sees a raw token.
_SRC_GENERIC = 'система'

# ── Closed vocabulary of source channels (the human reference is
#    policies/event-sources.md). The `detail` after ':' is free; the channel head
#    must be one of these. state_lint.event_source_noncanon flags anything else;
#    migrations 0021–0024 cleaned the historical free-form values into this set.
#    The model is three buckets: a CONNECTOR brought the signal, OR the operator
#    (`cowork`), OR the engine (`system`).
#
#    The CONNECTOR channels are NOT hardcoded as truth — they DERIVE from
#    `config/instance.yaml → connectors` (`_config.CONNECTOR_CHANNELS`, the same
#    declaration the scheduler reconciles daemons against), so enabling a connector
#    in config auto-registers its source channel with no engine edit. The literals
#    below are the safe DEFAULT/baseline (used when no config is present — repo,
#    tests, demo); config is additive on top.
from _config import CONNECTOR_CHANNELS as _CFG_CONNECTOR_CHANNELS

_CANON_CHANNELS = frozenset({
    # operator — Mom acting directly (chat with the assistant, decision,
    # manual entry, a reconciliation she did herself)
    'cowork',
    # ingest connectors — baseline; config/instance.yaml extends this set
    'tg', 'whatsapp', 'max', 'email', 'finkoper', 'bank', 'ofd', 'news',
    'document', '1c', 'egrul', 'websbor',
    # system — engine daemons / processes, + the one-time legacy import
    'system', 'migration', 'resolution_sweep', 'deadline_monitor',
    'threshold_monitor', 'staleness_monitor', 'mm_update', 'dashboards',
} | set(_CFG_CONNECTOR_CHANNELS))


def client_avatar(name):
    """(initials, inline-style) for a client avatar — one shared implementation
    used by every event row (track lists, decisions, …)."""
    n = (name or '').strip()
    for p in ('SP ', 'ИП '):
        if n.startswith(p):
            n = n[len(p):]
            break
    words = [w for w in n.split() if w]
    if not words:
        ini = '—'
    elif len(words) == 1:
        ini = words[0][:2].upper()
    else:
        ini = (words[0][0] + words[1][0]).upper()
    bg, fg = _avatar_color(name)
    return ini, ' style="background:' + bg + ';color:' + fg + '"'


def source_label(source):
    """Short Russian-facing label for a source channel ('tg:@x' -> 'TG').

    Known channels and daemons map to readable operator labels. An unmapped
    machine id (latin snake_case / contains digits or '_') collapses to the
    generic «система» so the operator never sees a raw token like
    'resolution_sweep' or 'morning_scan_27.05'. Human (Cyrillic) source text
    that isn't a machine id passes through unchanged.
    """
    head, _, detail = str(source or '').partition(':')
    raw = head.strip()
    if not raw:
        return ''
    ch = raw.lower()
    if ch == 'bank':
        d = detail.strip()
        return d if d else _SRC_LABELS['bank']   # show the specific bank name
    if ch in _SRC_LABELS:
        return _SRC_LABELS[ch]
    looks_machine = ('_' in ch or any(c.isdigit() for c in ch)
                     or any('a' <= c <= 'z' for c in ch))
    return _SRC_GENERIC if looks_machine else raw


def _plural_ru(n, one, few, many):
    """Russian plural: 1 час / 2 часа / 5 часов."""
    n = abs(int(n))
    if 11 <= n % 100 <= 14:
        return many
    r = n % 10
    if r == 1:
        return one
    if 2 <= r <= 4:
        return few
    return many


def relative_when(s, today=None):
    """Relative, Russian-facing 'when' for a history event timestamp.

    Hours/minutes when the value carries a time ('3 часа назад'); else day-based
    ('сегодня' / 'вчера' / 'N дней назад'); older than a week falls back to an
    absolute human date ('20 июня'). `s` is an ISO ts (preferred) or date string.
    """
    from datetime import datetime, date as _date
    from _strings import MONTHS_GEN
    s = str(s or '')
    if len(s) < 10:
        return s
    if today is None:
        today = _date.today()
    if 'T' in s:
        try:
            dt = datetime.fromisoformat(s)
            now = datetime.now().astimezone()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=now.tzinfo)
            secs = (now - dt).total_seconds()
            if secs >= 0:
                if secs < 60:
                    return 'только что'
                mins = int(secs // 60)
                if mins < 60:
                    return '{} {} назад'.format(mins, _plural_ru(mins, 'минуту', 'минуты', 'минут'))
                hrs = int(secs // 3600)
                if hrs < 24:
                    return '{} {} назад'.format(hrs, _plural_ru(hrs, 'час', 'часа', 'часов'))
        except (ValueError, TypeError):
            pass
    try:
        d = _date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
    except (ValueError, TypeError):
        return s
    delta = (today - d).days
    if delta <= 0:
        return 'сегодня'
    if delta == 1:
        return 'вчера'
    if delta < 7:
        return '{} {} назад'.format(delta, _plural_ru(delta, 'день', 'дня', 'дней'))
    try:
        return '{} {}'.format(d.day, MONTHS_GEN[d.month - 1])
    except Exception:
        return s


def reltime_span(s, today=None):
    """Same relative «когда» as relative_when, wrapped so the browser keeps it live.

    Emits `<span class="reltime" data-ts="<iso>">label</span>`; the reltime ticker
    in NEW_JS_FRAGMENT recomputes the label against the live clock every minute, so
    «3 часа назад» stays true even on a dashboard left open for hours. The server
    still renders the correct label, so it's right with JS off too. Bare (un-spanned)
    label when the value isn't datable."""
    label = relative_when(s, today)
    raw = str(s or '')
    if len(raw) < 10:
        return _esc(label)
    return '<span class="reltime" data-ts="%s">%s</span>' % (_esca(raw), _esc(label))


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
    From name_short='a client X.X.' take 'a client'."""
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
