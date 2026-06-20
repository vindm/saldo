# -*- coding: utf-8 -*-
"""_plan_waves.py — "work waves" view for the Plan-Today page.

A VIEW transformation over aggregate_tasks(...)['all']: it writes NOTHING to state.
Tasks are grouped by OPERATION (a wave = >=2 different SPs sharing one
operation+track) within deadline horizons.

v3: waves are collapsed by default — the page reads as a "list of the day's
operations". A collapsed wave = one dense row with vital signs (operation icon,
title, readiness bar, N SPs, due date, anomaly) plus inline action buttons
(Process wave / Dictate) — act without expanding. Expanding shows a summary line
(readiness in words) and the per-SP task list. At the top there is an
"Expand/Collapse all" control; each wave's state is remembered in localStorage.
Taxonomy is by task_type only (JSON-first; no title-text inference). Everything is
derived from state, no writes.
"""
import re

from _strings import t, tp
from _icons import icon

_QUOTES = '«»"„“”\''


def _attr(s):
    """Escaping for an HTML attribute."""
    return (str(s or '')
            .replace('&', '&amp;').replace('"', '&quot;')
            .replace('<', '&lt;').replace('>', '&gt;'))


def _wave_key(t):
    """Operation key from text: the first 2 significant words."""
    w = t.get('what') or ''
    w = re.sub(r'\([^)]*\)', '', w)
    for q in _QUOTES:
        w = w.replace(q, '')
    w = re.sub(r'\d', '', w)
    w = w.lower()
    w = re.sub(r'[^a-zа-яё ]', ' ', w)  # keep Latin AND Cyrillic (i18n pass had stripped Cyrillic)
    w = re.sub(r'\s+', ' ', w).strip()
    return ' '.join(w.split()[:2])


_OP_RU = {
    'bank_check': ('🏦', t('bank check')),
    'kudir_posting': ('📒', t('KUDIR posting')),
    'pp_to_form': ('💳', t('prepare payment order')),
    'ausn_reconciliation': ('⚖️', t('AUSN reconciliation')),
    'ausn_monthly': ('📅', t('AUSN monthly')),
    'ausn_markup_review': ('⚙️', t('AUSN markup review')),
    'ausn_bank_marking': ('🏦', t('AUSN bank marking')),
    'month_close': ('📅', t('month close')),
    'period_close': ('📅', t('period close')),
    'month_audit': ('🔎', t('month audit')),
    'kkt_check': ('🧾', t('cash register check')),
    'acquiring_reconciliation': ('💳', t('acquiring')),
    'service_payment': ('💰', t('client service payment')),
    'ens_reconciliation': ('⚖️', t('ENS reconciliation')),
    'sz_checks_reconciliation': ('⚖️', t('self-employed receipts reconciliation')),
    'client_followup': ('📞', t('client follow-up')),
    'client_action': ('👤', t('client action')),
    'primary_collection': ('📂', t('source documents collection')),
    'regulatory_watch': ('👁', t('regulatory monitoring')),
    'regulatory_monitoring': ('👁', t('regulatory monitoring')),
    'regulatory_action': ('📜', t('regulatory')),
    'regular_check': ('🔄', t('routine check')),
    'finkoper_recurring': ('🔄', t('recurring task')),
    'email_action_required': ('✉️', t('reply to email')),
    'ndfl_register': ('📄', t('NDFL register')),
    'recovery_period': ('⏪', t('period recovery')),
    'declaration': ('📄', t('tax return')),
    'notification': ('📨', t('notification')),
    'pp_sign': ('✍️', t('sign payment order')),
    'patent': ('📃', t('patent')),
    'statreport': ('📊', t('statistical reporting')),
    'egrul': ('🗂', t('EGRIP extract')),
    'technical_1c': ('🛠', t('technical in 1C')),
    'balance_reconciliation': ('⚖️', t('balance reconciliation')),
}


def _common_task_type(members):
    tts = {(m.get('task_type') or '').strip() for m in members}
    tts.discard('')
    return next(iter(tts)) if len(tts) == 1 else ''


def _horizon_of(t):
    dl = t.get('days_left')
    if dl is None:
        return 'backlog'
    if dl <= 7:
        return 'near'
    if dl <= 30:
        return 'soon'
    return 'backlog'


HORIZONS = [
    ('near',    t('Urgent — due in ≤ 7 days'),      '🔥', 'g-red'),
    ('soon',    t('Planned — this month'),          '📋', 'g-amber'),
    ('backlog', t('Backlog — no due date and later'), '📥', 'g-grey'),
]


# Aliases for synonymous task_type -> canonical.
_OP_ALIAS = {
    'regulatory_monitoring': 'regulatory_watch',
    # "AUSN operation markup in the bank portal" is one operation regardless of
    # which bank's portal — merge the bank-marking variant into the markup review
    # so the two clients batch into a single "AUSN markup" wave (not two).
    'ausn_bank_marking': 'ausn_markup_review',
}

# Generic types are statuses/processes, NOT operations: you can't merge a wave on
# them (otherwise heterogeneous tasks stick together). For these we bucket as a
# generic/other operation keyed by the cleaned text, so they don't glue together.
_GENERIC_TYPES = {
    'awaiting_external', 'awaiting_external_then_action', 'open_question',
    'other', 'investigation', 'infrastructure', 'long_term_parallel',
    'multi_step_preparation', 'preparation', 'strategic_decision',
    'monitoring', 'documentation', 'team_conversation_required',
    'access_request', 'extraction', 'client_action',
    # source-based (where the task came from, not what it IS) -> re-infer by topic
    'finkoper_recurring',
}


# Operation inference from the task title — used ONLY when task_type is missing or
# generic. Merges title variants (e.g. "Аванс УСН 1кв" / "Аванс УСН 1 кв") into one
# wave, exactly as the original engine did. Patterns cover ru (real data) + en (demo).
_OP_KEYWORDS = [
    (re.compile(r'контроль оплат|оплат\w*\s+услуг|поступлени|service payment|client payment', re.I), 'service_payment'),
    (re.compile(r'кудир|kudir|income ledger', re.I), 'kudir_posting'),
    (re.compile(r'эквайр|acquir', re.I), 'acquiring_reconciliation'),
    (re.compile(r'егрип|егрюл|egr[iu][pl]|registry extract', re.I), 'egrul'),
    (re.compile(r'росстат|websbor|статотч|rosstat|stat\.?\s*report|statistic', re.I), 'statreport'),
    (re.compile(r'размет\w*.*аусн|аусн.*размет|ausn.*mark|mark.*ausn', re.I), 'ausn_markup_review'),
    (re.compile(r'аусн|ausn', re.I), 'ausn_reconciliation'),
    (re.compile(r'подпис.*пп|пп.*подпис|подпис\w*\s+плат|sign.*payment order|payment order.*sign', re.I), 'pp_sign'),
    (re.compile(r'сформир.*пп|пп.*сформир|платёжк|платежк|payment order|form.*payment', re.I), 'pp_to_form'),
    (re.compile(r'деклараци|declaration|tax return', re.I), 'declaration'),
    (re.compile(r'уведомлени|notification', re.I), 'notification'),
    (re.compile(r'первичк|primary doc', re.I), 'primary_collection'),
    (re.compile(r'выписк|провер\w*\s+банк|банк\w*\s+(?:выписк|провер)|bank statement|bank check', re.I), 'bank_check'),
    (re.compile(r'закрыти\w*.*(?:месяц|период)|закрыть\s+месяц|month.*clos|clos.*month|period clos', re.I), 'month_close'),
    (re.compile(r'аудит|audit', re.I), 'month_audit'),
    (re.compile(r'касс|ккт|чек\w*\s+коррекц|cash register|kkt', re.I), 'kkt_check'),
    (re.compile(r'патент|patent', re.I), 'patent'),
    (re.compile(r'енс\b|сальдо\s+енс|single tax account|\bens\b', re.I), 'ens_reconciliation'),
    (re.compile(r'запрос.*клиент|уточнить\s+у|спросить|ask.*client|client.*request|follow.?up', re.I), 'client_followup'),
    (re.compile(r'письм|на\s+письмо|email|letter', re.I), 'email_action_required'),
]


def _stage_of_token(tok):
    """If an operation token (task_type OR keyword-inferred) belongs to a pipeline
    stage, return 'stage:<code>', else None."""
    try:
        import _pipeline as _P
        si = _P.stage_index_of((tok or '').strip())
        return ('stage:' + _P.stages()[si]['code']) if si is not None else None
    except Exception:
        return None


_RU_MONTHS_NOM = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль',
                  'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
_EN_MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
              'August', 'September', 'October', 'November', 'December']


def _period_of(t):
    """Reporting period of a task: explicit period (from state type_specific.period,
    propagated by the aggregator) > type_specific > due month. NOT the due date —
    "close April" keeps period=April even if its deadline is in June."""
    if t.get('period'):
        return str(t['period'])
    ts = t.get('type_specific') or {}
    for k in ('period', 'quarter', 'service_quarter'):
        if ts.get(k):
            return str(ts[k])
    due = t.get('due_date')
    if due is not None and hasattr(due, 'strftime'):
        return due.strftime('%Y-%m')
    return ''


def _fmt_period(p, loc='ru'):
    m = re.match(r'^(\d{4})-(\d{2})$', p or '')
    if m:
        mo = int(m.group(2))
        if 1 <= mo <= 12:
            months = _RU_MONTHS_NOM if loc == 'ru' else _EN_MONTHS
            return months[mo - 1] + ' ' + m.group(1)
    return p or ''


def _op_canonical(t):
    # Monthly-cycle operations collapse into their canonical pipeline stage so the
    # plan reads as the deterministic monthly process — detected from the task_type
    # OR from title keywords. Stage ops are PERIOD-EXPLICIT ('stage:code|YYYY-MM') so
    # "close April" and "close May" are distinct, batchable waves. Off-pipeline ops
    # fall through: task_type(+alias) -> keyword token -> text key.
    raw = (t.get('task_type') or '').strip()
    s = _stage_of_token(raw)
    if s:
        per = _period_of(t)
        return s + ('|' + per if per else '')
    tt = _OP_ALIAS.get(raw, raw)
    if tt and tt not in _GENERIC_TYPES:
        return tt
    txt = _clean_op_text(t.get('what') or '')
    for rx, token in _OP_KEYWORDS:
        if rx.search(txt):
            st = _stage_of_token(token)
            if st:
                per = _period_of(t)
                return st + ('|' + per if per else '')
            return token
    return 'x:' + _wave_key(t)


def _wave_op_token(members):
    return _op_canonical(members[0]) if members else ''


def _op_key(t):
    # Group by OPERATION only — a wave spans ALL clients sharing an operation+period,
    # regardless of client group. Group (Team/Direct) is a filter, not a batching
    # axis: splitting one batch of identical work by group just fragments it. The
    # Team/Direct toggle filters the member rows inside a wave instead.
    return _op_canonical(t)


def _capf(s):
    """Capitalize the first letter (for consistent casing of wave names)."""
    s = (s or '').strip()
    return (s[:1].upper() + s[1:]) if s else s


def _clean_op_text(s):
    """Clean the raw task text into a wave name: strip document numbers, dates,
    amounts, quoted/parenthesized content and trailing noise."""
    s = re.sub('«[^»]*»', '', s)                                   # «quoted content»
    s = re.sub(r'\([^)]*\)', '', s)                               # (...)
    s = re.sub('\\bfor\\s+[\\d.,\u00a0\u202f ]+₽', '', s)         # "for 26 357.83 ₽"
    s = re.sub('[\\d.,\u00a0\u202f ]+₽', '', s)                    # bare amount ₽
    s = re.sub(r'№\s*\S+', '', s)                                 # invoice no.
    s = re.sub(r'\bdated\s+\d{1,2}\.\d{1,2}(?:\.\d{2,4})?', '', s)  # "dated 30.04(.2026)"
    s = re.sub(r'\b\d{1,2}\.\d{2}\.\d{2,4}\b', '', s)            # 25.04.2026
    s = re.sub(r'\b\d{3,}[-/]\d{3,}\b', '', s)                    # 0000-000015
    s = re.sub(r'\b\d{6,}\b', '', s)                              # long numbers
    s = re.sub(r'\s{2,}', ' ', s)
    s = re.sub(r'\s+([.,;:])', r'\1', s)
    return s.strip(' .,;:—–-\u00a0\u202f')


def _op_title(tasks):
    cands = [_clean_op_text(t.get('what') or '') for t in tasks]
    cands = [c for c in cands if c]
    base = min(cands, key=len) if cands else t('Tasks')
    if len(base) > 42:
        base = base[:40].rstrip() + '…'
    return _capf(base) or t('Tasks')


_STAGE_ICON = {
    'primary_collection': '📂', 'posting_1c': '📒', 'month_close': '📅',
    'month_audit': '🔎', 'tax_pp': '💳', 'sign_pay': '✍️',
}


def _op_label(members):
    tok = _wave_op_token(members)
    if isinstance(tok, str) and tok.startswith('stage:'):
        try:
            import _pipeline as _P
            from _config import LOCALE
            loc = LOCALE if LOCALE in ('ru', 'en') else 'ru'
        except Exception:
            loc = 'ru'
        code, _, per = tok[len('stage:'):].partition('|')
        title = _P.stage_title(code, loc)
        if per:
            title += ' · ' + _fmt_period(per, loc)
        return _capf(title)
    if tok in _OP_RU:
        return _capf(_OP_RU[tok][1])
    return _op_title(members)


def _op_icon(members):
    """Monochrome line icon (SVG) for the wave's operation."""
    from _icons import icon
    tok = _wave_op_token(members)
    if isinstance(tok, str) and tok.startswith('stage:'):
        return icon(tok[len('stage:'):].split('|')[0])
    if tok in _OP_RU:
        return icon(tok)
    return icon('dot')


def _min_dl(tasks):
    dls = [t.get('days_left') for t in tasks if t.get('days_left') is not None]
    return min(dls) if dls else None


def _wave_due_badge(dl):
    if dl is None:
        return ''
    if dl < 0:
        return '<span class="wave-due due-overdue">' + t('overdue {}d').format(-dl) + '</span>'
    if dl == 0:
        return '<span class="wave-due due-today">' + t('today') + '</span>'
    if dl <= 7:
        return '<span class="wave-due due-soon">' + t('in {}d').format(dl) + '</span>'
    return '<span class="wave-due due-plan">{}d</span>'.format(dl)


# ---- readiness / anomalies (from open tasks, no writes) ----

def _member_state(t):
    st = (t.get('status') or '').lower()
    if st == 'blocked':
        return 'blocked'
    if st.startswith('awaiting'):
        return 'waiting'
    return 'ready'


def _wave_readiness(members):
    c = {'ready': 0, 'waiting': 0, 'blocked': 0}
    for m in members:
        c[_member_state(m)] += 1
    return c


def _wave_anomalies(members):
    out = []
    for m in members:
        st = (m.get('status') or '').lower()
        dl = m.get('days_left')
        if st == 'blocked' or (m.get('priority') == 'overdue') or (dl is not None and dl < 0):
            nm = m.get('client_name') or ''
            if nm and nm not in out:
                out.append(nm)
    return out


def _readiness_bar(rd, title=''):
    segs = []
    for kind, cls in (('ready', 'wb-ready'), ('waiting', 'wb-wait'), ('blocked', 'wb-block')):
        if rd[kind]:
            segs.append('<span class="wb {cls}" style="flex:{n}"></span>'.format(cls=cls, n=rd[kind]))
    if not segs:
        return ''
    t = ' title="{}"'.format(_attr(title)) if title else ''
    return '<span class="wave-bar"{t}>{s}</span>'.format(t=t, s=''.join(segs))


def _readiness_text(rd, n):
    parts = []
    if rd['ready']:
        parts.append(t('{} ready').format(rd['ready']))
    if rd['waiting']:
        parts.append(t('{} waiting').format(rd['waiting']))
    if rd['blocked']:
        parts.append(t('{} blocked').format(rd['blocked']))
    comp = ' · '.join(parts)
    if rd['ready'] == n and n:
        plan = t('can run as a batch')
    elif rd['ready']:
        plan = t('run the ready ones, follow up on the rest')
    else:
        plan = t('waiting on data — nothing to run yet')
    return comp, plan


def horizon_counts(all_tasks):
    hc = {'near': 0, 'soon': 0, 'backlog': 0}
    for t in all_tasks:
        hc[_horizon_of(t)] += 1
    return hc


# Standard, reusable accounting operations — these read as the same operation on
# every client, so they form a wave even with a single member. Ad-hoc per-client
# task types (review_checkpoint, access_request, client_followup, monitoring,
# awaiting_external, …) are deliberately absent: they only batch when >=2 clients
# share the exact operation, otherwise they render as individual tasks.
# Reusable operation tokens (matched against _op_canonical / op_key). These read
# as the same operation on every client, so they form a wave even with a single
# member. Ad-hoc op tokens (review_checkpoint, regulatory_watch, monitoring,
# access_request, client_followup, awaiting_external, patent-from-keyword, …) are
# deliberately absent — they only batch when >=2 clients share the exact op.
_REUSABLE_OP_TYPES = frozenset({
    'primary_collection', 'kudir_posting', 'posting_1c', 'technical_1c',
    'ndfl_register', 'balance_reconciliation', 'ens_reconciliation',
    'ausn_reconciliation', 'ausn_markup_review', 'ausn_bank_marking',
    'sz_checks_reconciliation', 'service_payment', 'acquiring',
    'acquiring_reconciliation', 'bank_check', 'kkt_check', 'declaration',
    'statreport', 'regular_check', 'finkoper_recurring', 'tax_pp', 'pp_to_form',
    'notification', 'sign_pay', 'pp_sign', 'month_close', 'period_close',
    'month_audit', 'patent',
})


def _is_wave_group(op_key, members):
    """A group is a wave if the batch is real (>=2) or the operation token is a
    standard, reusable one (a pipeline stage or a whitelisted recurring op)."""
    if len(members) >= 2:
        return True
    op = str(op_key)
    if op.startswith('stage:'):
        return True
    return op in _REUSABLE_OP_TYPES


def cluster_tasks(tasks):
    """Flat list → (waves, singles). A wave = >=2 DIFFERENT clients sharing one
    operation+track. Reused by the Week/Month pages."""
    groups = {}
    for t in tasks:
        groups.setdefault(_op_key(t), []).append(t)
    waves, singles = [], []
    for op_key, members in groups.items():
        # A wave is a RECURRING bookkeeping operation — so a standard, reusable
        # action (a pipeline stage or a whitelisted recurring op like a
        # reconciliation / register / collection / service-payment / AUSN markup)
        # is a wave even with a single member, and reads identically on the
        # all-clients plan and on one client's card. Ad-hoc one-offs (a "control:
        # is the contract signed?", an access request) are NOT recurring
        # operations: they render as individual tasks unless >=2 clients share the
        # exact op.
        if _is_wave_group(op_key, members):
            waves.append(members)
        else:
            singles.extend(members)
    waves.sort(key=lambda m: (_min_dl(m) if _min_dl(m) is not None else 10**9, -len(m)))
    return waves, singles


def build_horizons(all_tasks):
    out = []
    for hkey, htitle, hicon, hcls in HORIZONS:
        tlist = [t for t in all_tasks if _horizon_of(t) == hkey]
        if not tlist:
            continue
        groups = {}
        for t in tlist:
            groups.setdefault(_op_key(t), []).append(t)
        waves, singles = [], []
        for members in groups.values():
            if len(members) >= 2:  # group by operation, not by client count
                waves.append(members)
            else:
                singles.extend(members)
        waves.sort(key=lambda m: (-len(m), _min_dl(m) if _min_dl(m) is not None else 999))
        singles.sort(key=lambda t: (t.get('days_left') if t.get('days_left') is not None else 999))
        out.append((htitle, hicon, hcls, len(tlist), waves, singles))
    return out


_RENDER_ROW = None


def _render_wave(members, esc, htitle):
    # data-track-type drives the Team/Direct filter. A wave can now span groups:
    # if all members share one group use it; otherwise "mixed" (the inner member
    # rows still carry their own group, so they filter correctly).
    _grps = {(m.get('track') or '') for m in members}
    _grps.discard('')
    track = next(iter(_grps)) if len(_grps) == 1 else 'mixed'
    op = _op_label(members)
    op_ic = _op_icon(members)
    n = len({m.get('client_id') for m in members})
    nt = len(members)
    clients = ', '.join(sorted({m.get('client_name') or '' for m in members} - {''}))
    wid = _attr(htitle + '|' + op + '|' + track)
    stg = _attr(_wave_op_token(members))  # canonical token e.g. "stage:month_close|2026-04" — for stage-jump matching

    rd = _wave_readiness(members)
    bar = _readiness_bar(rd, t('{} ready · {} waiting · {} blocked').format(rd['ready'], rd['waiting'], rd['blocked']))
    comp, plan = _readiness_text(rd, nt)

    head_icon = ('<span class="wave-ic">' + op_ic + '</span>') if op_ic else ''  # raw SVG, not escaped
    # Wave-header "anomaly" client labels removed per owner decision (2026-06-19):
    # no red client list in the wave header.
    anomaly_html = ''

    batch_prompt = _attr(tp(
        'Process the wave "{op}": {clients}. For each client open state/*.json (source of truth) and '
        'mental_model, check the linked sources and reconcile the links. First update the model with the '
        'new signals. Give a status per client and an overall wave plan: what to batch now, where we wait, '
        'where it is blocked. Make state changes via mm_update (with my approval); draft any outward message '
        'for my review — do not send.',
        'Обработай волну «{op}»: {clients}. По каждому клиенту открой state/*.json (источник истины) и '
        'mental_model, проверь связанные источники и сверь связи. Сначала обнови модель новыми сигналами. '
        'Дай статус по каждому и общий план волны: что сделать пачкой сейчас, где ждём, где блок. Правки '
        'state — через mm_update (с моим аппрувом); сообщения наружу — черновиком мне на проверку, не '
        'отправляй.').format(op=op, clients=clients))

    actions = (
        '<span class="wave-acts">'
        '<button class="wave-act wave-act-go" data-prompt="{bp}" title="' + _attr(t('Process the whole wave at once')) + '">' + icon('search') + ' ' + t('Process wave') + '</button>'
        '<button class="wave-act wave-act-mic" data-wave-op="{wop}" data-wave-clients="{wcl}" '
        'data-wave-n="{n}" title="' + _attr(t('Dictate for the wave')) + '">' + icon('pencil') + ' ' + t('Dictate') + '</button>'
        '</span>').format(bp=batch_prompt, wop=_attr(op), wcl=_attr(clients), n=n)

    assist_html = ''
    if comp:
        assist_html = '<span class="wave-assist"><b>{c}</b> · {p}</span>'.format(c=esc(comp), p=esc(plan))

    rows = ''.join(_RENDER_ROW(t) for t in members)
    return (
        '<div class="wave collapsed" data-track-type="{tt}" data-wave-id="{wid}" data-stage="{stg}">'
        '<div class="wave-head wave-toggle">'
        '<span class="wave-chevron">{chev}</span>'
        '<span class="wave-op">{ic}{op}</span>'
        '<span class="wave-count">{nt}</span>'
        '{badge}'
        '{bar}'
        '{anom}'
        '</div>'
        '<div class="wave-sub">{assist}{acts}</div>'
        '<div class="wave-body">{rows}</div>'
        '</div>'.format(
            chev=icon('chevron'),
            tt=esc(track), wid=wid, stg=stg, ic=head_icon, op=esc(op), bar=bar, n=n, nt=nt,
            badge=_wave_due_badge(_min_dl(members)), anom=anomaly_html,
            acts=actions, assist=assist_html, rows=rows))


def render_waves_page(all_tasks, render_row, esc):
    global _RENDER_ROW
    _RENDER_ROW = render_row
    sections = []
    for htitle, hicon, hcls, hcount, waves, singles in build_horizons(all_tasks):
        body = []
        for members in waves:
            body.append(_render_wave(members, esc, htitle))
        if singles:
            srows = ''.join(render_row(t) for t in singles)
            if waves:
                body.append(
                    ('<div class="wave wave-singles collapsed" data-wave-id="{wid}">'
                     '<div class="wave-head wave-toggle">'
                     '<span class="wave-chevron">{chev}</span>'
                     '<span class="wave-op">{label}</span>'
                     '{badge}<span class="wave-count">{n}</span></div>'
                     '<div class="wave-body">{rows}</div></div>').format(
                        chev=icon('chevron'),
                        wid=_attr(htitle + '|singles'), label=t('Individual tasks'),
                        n=len(singles), badge=_wave_due_badge(_min_dl(singles)), rows=srows))
            else:
                body.append(srows)
        sections.append(
            '<section class="group {hcls}">'
            '<div class="group-head"><span class="group-icon">{ic}</span>'
            '<h3>{title}</h3><span class="group-count">{n}</span></div>'
            '<div class="horizon-body">{body}</div>'
            '</section>'.format(hcls=hcls, ic=hicon, title=esc(htitle),
                                n=hcount, body=''.join(body)))
    if not sections:
        return ''
    toolbar = ('<div class="waves-toolbar">'
               '<button class="waves-expand-all" type="button">' + t('Expand all') + '</button>'
               '</div>')
    return toolbar + ''.join(sections)


WAVES_CSS = (
    '.horizon-body{padding:0}'
    '.wave{border-bottom:1px solid var(--border)}'
    '.wave:last-child{border-bottom:none}'
    '.wave-head{display:flex;align-items:center;gap:10px;padding:8px var(--space-md) 8px 5px;'
    'border-bottom:1px solid var(--border);background:transparent;cursor:pointer;'
    'user-select:none;transition:background 120ms}'
    '.wave-head:hover{background:var(--bg-card)}'
    '.wave-head:hover .wave-op{color:var(--accent-blue)}'
    '.wave.collapsed .wave-head{border-bottom:none}'
    '.wave.collapsed .wave-sub{display:none}'
    '.wave.collapsed .wave-body{display:none}'
    '.wave-chevron{font-size:15px;color:var(--text-muted);transition:transform .15s;'
    'flex-shrink:0;width:16px;height:16px;display:inline-flex;align-items:center;'
    'justify-content:center;line-height:1}'
    '.wave-chevron .ic{width:15px;height:15px;stroke-width:2.25}'
    '.wave:not(.collapsed) .wave-chevron{transform:rotate(90deg)}'
    '.wave-head:hover .wave-chevron{color:var(--text-secondary)}'
    '.wave-op{font-weight:500;font-size:15px;flex:0 1 auto;min-width:0;color:var(--text-primary);'
    'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:inline-flex;align-items:center}'
    '.wave-ic{margin-right:8px;color:var(--text-muted);display:inline-flex;flex-shrink:0}'
    '.wave-ic .ic{width:16px;height:16px}'
    '.wave-bar{display:inline-flex;height:6px;width:64px;border-radius:4px;overflow:hidden;'
    'background:var(--border);flex-shrink:0}'
    '.wave-bar .wb{display:block;height:100%}'
    '.wb-ready{background:var(--accent-green)}'
    '.wb-wait{background:var(--accent-yellow)}'
    '.wb-block{background:var(--accent-red)}'
    '.wave-count{font-size:12px;color:var(--text-secondary);background:var(--border);'
    'border:none;border-radius:6px;padding:1px 7px;font-weight:600;min-width:20px;'
    'text-align:center;line-height:1.5;white-space:nowrap;flex-shrink:0;margin:0 auto 0 8px}'
    '.wave-head:hover .wave-count{color:var(--text-primary)}'
    '.wave-due{font-size:13px;font-weight:600;white-space:nowrap;flex-shrink:0}'
    '.wave-anomaly{font-size:12px;font-weight:600;color:var(--accent-red);background:var(--red-bg);'
    'border-radius:8px;padding:2px 9px;white-space:nowrap;flex-shrink:0}'
    '.wave-acts{display:flex;gap:6px;flex-shrink:0;margin-left:auto}'
    '.wave-act{font-size:13px;font-weight:500;padding:4px 10px;border-radius:var(--radius-btn);'
    'border:1px solid var(--border);background:var(--bg-card);color:var(--text-primary);cursor:pointer;'
    'font-family:inherit;white-space:nowrap;transition:all 150ms;line-height:1.3}'
    '.wave-act:hover{border-color:var(--accent-blue);background:var(--blue-bg);color:var(--accent-blue)}'
    '.wave-act-go{border-color:var(--accent-blue);color:var(--accent-blue)}'
    '.wave-sub{display:flex;align-items:center;gap:12px;flex-wrap:wrap;'
    'padding:7px var(--space-md);background:var(--bg-page);'
    'border-bottom:1px solid var(--border)}'
    '.wave-assist{font-size:13px;color:var(--text-secondary);flex:1;min-width:120px}'
    '.wave-assist b{color:var(--text-primary);font-weight:600}'
    '.wave .task-item{background:var(--bg-card)}'
    '.wave .task-row{padding-left:calc(var(--space-md) + 8px)}'
    '.wave-singles .wave-op{color:var(--text-secondary);font-weight:500}'
    '.waves-toolbar{display:flex;justify-content:flex-end;margin-bottom:8px}'
    '.plan-sec-h-ops{display:flex;align-items:center;justify-content:space-between;gap:12px}'
    '.waves-expand-all{font-size:13px;color:var(--text-secondary);background:none;border:none;'
    'cursor:pointer;font-family:inherit;font-weight:500;padding:4px 10px;border-radius:6px;'
    'text-transform:none;letter-spacing:0;transition:all 120ms}'
    '.waves-expand-all:hover{background:var(--bg-card);color:var(--accent-blue)}'
)


_WAVES_JS_TEMPLATE = """
<script>
(function(){
  var KEY = 'plan_waves_expanded';
  function load(){ try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch(e){ return {}; } }
  function save(s){ try { localStorage.setItem(KEY, JSON.stringify(s)); } catch(e){} }
  // everything collapsed by default (class collapsed in markup); expand the saved ones
  var st = load();
  Array.prototype.forEach.call(document.querySelectorAll('.wave[data-wave-id]'), function(w){
    if(st[w.getAttribute('data-wave-id')]) w.classList.remove('collapsed');
  });
  function syncBtn(){
    var btn = document.querySelector('.waves-expand-all');
    if(!btn) return;
    btn.textContent = document.querySelector('.wave.collapsed') ? '__EXPAND_ALL__' : '__COLLAPSE_ALL__';
  }
  syncBtn();
  document.addEventListener('click', function(e){
    // dictate for the wave
    var mic = e.target.closest('.wave-act-mic');
    if(mic){
      e.preventDefault();
      if(typeof window.openMicModal === 'function'){
        window.openMicModal({
          kind: 'wave', id: '',
          client: mic.getAttribute('data-wave-clients') || '',
          title: mic.getAttribute('data-wave-op') || '',
          extra: (mic.getAttribute('data-wave-n') || '') + ' SPs'
        });
      }
      return;
    }
    // expand/collapse all
    var all = e.target.closest('.waves-expand-all');
    if(all){
      e.preventDefault();
      var expand = !!document.querySelector('.wave.collapsed');
      var s = load();
      Array.prototype.forEach.call(document.querySelectorAll('.wave[data-wave-id]'), function(w){
        var id = w.getAttribute('data-wave-id');
        if(expand){ w.classList.remove('collapsed'); if(id) s[id]=1; }
        else { w.classList.add('collapsed'); if(id) delete s[id]; }
      });
      save(s); syncBtn();
      return;
    }
    // other buttons/links (incl. "Process" with data-prompt) — do not collapse
    if(e.target.closest('button,a')) return;
    var head = e.target.closest('.wave-toggle');
    if(!head) return;
    var wave = head.closest('.wave');
    if(!wave) return;
    wave.classList.toggle('collapsed');
    var id = wave.getAttribute('data-wave-id');
    if(id){ var s2 = load(); if(wave.classList.contains('collapsed')){ delete s2[id]; } else { s2[id]=1; } save(s2); }
    syncBtn();
  });
})();
</script>
"""

WAVES_JS = (_WAVES_JS_TEMPLATE
            .replace('__EXPAND_ALL__', t('Expand all'))
            .replace('__COLLAPSE_ALL__', t('Collapse all')))


# Stage-jump: when the Plan is opened from "Periods" with #stage=CODE&period=YYYY-MM,
# expand + scroll to + highlight the matching wave(s). Appended so it runs after the
# main expand/collapse-restore logic.
_STAGE_JUMP_JS = (
    '<script>(function(){var h=location.hash||"";var ms=h.match(/stage=([^&]+)/);'
    'if(!ms)return;var st=decodeURIComponent(ms[1]);var mp=h.match(/period=([^&]*)/);'
    'var per=mp?decodeURIComponent(mp[1]):"";var needle="stage:"+st+(per?"|"+per:"");'
    'var first=null;[].slice.call(document.querySelectorAll(".wave[data-stage]")).forEach(function(w){'
    'if((w.getAttribute("data-stage")||"").indexOf(needle)>=0){w.classList.remove("collapsed");'
    'w.style.boxShadow="inset 0 0 0 2px var(--accent-blue)";if(!first)first=w;}});'
    'if(first)setTimeout(function(){first.scrollIntoView({behavior:"smooth",block:"center"});},80);})();</script>'
)
WAVES_JS = WAVES_JS + _STAGE_JUMP_JS


# ── Flat plan: stage+period waves + singles in ONE urgency-sorted, colour-coded
# stream (no Горит/Неделя/Бэклог horizon buckets — the per-wave day badge already
# shows urgency, and bucketing split one stage across horizons). Dateless backlog
# is tucked into a collapsed block at the end.
WAVES_CSS = WAVES_CSS + (
    '.plan-item{background:transparent;border:none;'
    'border-bottom:1px solid var(--border);border-radius:0;margin-bottom:0;overflow:hidden}'
    '.plan-item .wave{border-bottom:none}'
    '.plan-item.plan-single .task-item{border-bottom:none}'
    '.plan-item:hover{background:var(--bg-page)}'
    '.plan-bk{margin-top:var(--space-md);border:1px solid var(--border);border-radius:var(--radius-card);'
    'background:var(--bg-card);overflow:hidden}'
    '.plan-bk>summary{cursor:pointer;padding:11px var(--space-md);font-weight:600;color:var(--text-secondary);'
    'background:var(--bg-page);list-style:none}'
    '.plan-bk>summary::-webkit-details-marker{display:none}'
    '.plan-bk[open]>summary{border-bottom:1px solid var(--border)}'
    '.plan-sec-h{font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;'
    'color:var(--text-secondary);margin:var(--space-md) 0 7px;padding-left:2px}'
    '.plan-sec-h:first-child{margin-top:0}'
    # Section cards: each block sits on its own white card on the canvas
    '.sec-card{background:var(--bg-card);border:1px solid var(--border);'
    'border-radius:var(--radius-card);padding:14px 16px;margin-bottom:14px}'
    '.sec-card .plan-item:last-child{border-bottom:none}'
    '.sec-card .plan-item:last-child .task-item{border-bottom:none}'
    '.plan-wait{margin-top:var(--space-md);border:1px dashed var(--border);border-radius:var(--radius-card);background:var(--bg-page);overflow:hidden;opacity:.9}'
    '.plan-wait>summary{cursor:pointer;padding:11px var(--space-md);font-weight:600;color:var(--text-muted);list-style:none}'
    '.plan-wait>summary::-webkit-details-marker{display:none}'
    '.plan-wait[open]>summary{border-bottom:1px dashed var(--border)}'
    '.plan-wait .plan-item{opacity:.85}'
)


def _urg_cls(dl):
    if dl is None:
        return 'g-grey'
    if dl < 0:
        return 'g-red'
    if dl <= 7:
        return 'g-amber'
    if dl <= 30:
        return 'g-blue'
    return 'g-grey'


def render_waves_flat(all_tasks, render_row, esc):
    """Plan list with waves and individual tasks kept in SEPARATE blocks (no
    interleaving) so collapsible operation-bars never mix with single-task rows.
    Each block is urgency-sorted and colour-coded; dateless items collapse into a
    backlog block at the end. "Expand all" lives on the Operations section header
    (the only block with collapsible groups)."""
    global _RENDER_ROW
    _RENDER_ROW = render_row
    waves, singles = cluster_tasks(all_tasks)

    # Passive "we just wait / watch" items are NOT actions: monitoring (a risk-watch)
    # and awaiting_external with no due date ("ждём, наша часть дождаться"). They go to
    # a de-emphasised "Waiting" lane at the bottom, not the action plan. Dated awaits
    # (Sign PO / pay-control / payment, with a deadline + a chase action) stay as tasks.
    def _is_passive(x):
        tt = (x.get('task_type') or '')
        return tt == 'monitoring' or (tt == 'awaiting_external' and x.get('days_left') is None)

    wait_singles = [x for x in singles if _is_passive(x)]
    singles = [x for x in singles if not _is_passive(x)]
    wait_waves = [w for w in waves if all(_is_passive(m) for m in w)]
    waves = [w for w in waves if not all(_is_passive(m) for m in w)]

    w_dated = sorted([w for w in waves if _min_dl(w) is not None], key=_min_dl)
    w_undated = [w for w in waves if _min_dl(w) is None]
    s_dated = sorted([x for x in singles if x.get('days_left') is not None],
                     key=lambda x: x['days_left'])
    s_undated = [x for x in singles if x.get('days_left') is None]

    def _wave_item(w):
        return '<div class="plan-item ' + _urg_cls(_min_dl(w)) + '">' + _render_wave(w, esc, 'plan') + '</div>'

    def _single_item(x):
        return '<div class="plan-item plan-single ' + _urg_cls(x.get('days_left')) + '">' + render_row(x) + '</div>'

    label_blocks = bool(w_dated) and bool(s_dated)

    def _card(inner):
        return '<section class="sec-card">' + inner + '</section>'

    sections = []
    if w_dated:
        hdr = ('<div class="plan-sec-h plan-sec-h-ops"><span>'
               + t('Operations (batchable)') + '</span>'
               + '<button class="waves-expand-all" type="button">'
               + t('Expand all') + '</button></div>')
        sections.append(_card(hdr + ''.join(_wave_item(w) for w in w_dated)))
    if s_dated:
        hdr = ('<div class="plan-sec-h">' + t('Individual tasks') + '</div>') if label_blocks else ''
        sections.append(_card(hdr + ''.join(_single_item(x) for x in s_dated)))

    # Backlog (dateless, non-passive) — a normal section, expanded, like the others.
    if w_undated or s_undated:
        n = len(w_undated) + len(s_undated)
        hdr = '<div class="plan-sec-h">' + t('Backlog — no due date and later') + ' (' + str(n) + ')</div>'
        body = ''.join(_wave_item(w) for w in w_undated) + ''.join(_single_item(x) for x in s_undated)
        sections.append(_card(hdr + body))

    # Waiting (passive: monitoring + dateless awaiting) — a normal section at the
    # bottom, expanded, consistent with the others.
    if wait_waves or wait_singles:
        wn = len(wait_waves) + len(wait_singles)
        hdr = '<div class="plan-sec-h">' + t('Waiting — on the client/bank side') + ' (' + str(wn) + ')</div>'
        body = ''.join(_wave_item(w) for w in wait_waves) + ''.join(_single_item(x) for x in wait_singles)
        sections.append(_card(hdr + body))

    if not sections:
        return ''
    return ''.join(sections)
