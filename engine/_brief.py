# -*- coding: utf-8 -*-
"""_brief.py — the "Daily brief" zone on the home page. A PURE LENS over state.

Decision (2026-06-13): the brief is never stored (a view, not a store).
Everything comes from `state/*.json` + `history.jsonl` on every re-render. The
intelligence lives in the state upkeep done by the `mm_update` skill; this module
only ranks and formats.

The design strictly reuses the existing widgets (`aw-widget`/`aw-head`/`aw-row`/`aw-dl-badge`
from _analytics_widgets.ANALYTICS_CSS) — no hand-rolled markup or inline emoji.
The per-question recommendation = `type_specific.recommended`/`options` from the
open_question itself; until those exist we show `next_action` as a hypothesis + typical options.

Buttons use the shared copy-modal (data-prompt + PROMPT_MODAL_JS), not sendPrompt (file://).
Rows are clickable (track-card-clickable + data-track-*) and open the track modal —
the attributes are built by the passed make_attrs (build_track_data_attrs from _track_attrs).
"""
import os, glob, json
from datetime import date
from _helpers import track_stale_days  # R8
from _strings import t

_PRIO = {'high': 0, 'normal': 1, 'low': 2}


def _to_date(s):
    try:
        y, m, d = map(int, str(s).split('T')[0].split('-')[:3])
        return date(y, m, d)
    except Exception:
        return None


def _age_days(created, today):
    d = _to_date(created)
    return (today - d).days if d else None


def _esc(s):
    return str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _esca(s):
    return _esc(s).replace('"', '&quot;').replace("'", '&#39;')


def collect_brief(clients, state_read, today):
    decisions, questions, nearest = [], [], None
    for c in clients:
        cid = c['id']
        cname = c.get('name_short') or cid
        try:
            t = state_read(cid, 'tasks.json') or {}
        except Exception:
            t = {}
        arr = t.get('tasks', []) if isinstance(t, dict) else (t or [])
        for tr in arr:
            if not isinstance(tr, dict) or tr.get('status') not in ('active', 'open'):
                continue
            tt = tr.get('task_type') or tr.get('type')
            dd = _to_date(tr.get('due_date'))
            if dd and dd >= today and (nearest is None or dd < nearest[0]):
                nearest = (dd, cname, (tr.get('title') or '')[:60])
            if tt == 'open_question':
                a = tr.get('assist') or {}
                acts = a.get('actions') or None
                opts = ([{'label': x.get('label', ''), 'prompt': x.get('prompt', '')} for x in acts]
                        if acts else None)
                rec = None
                if acts:
                    for _i, x in enumerate(acts):
                        if x.get('recommended'):
                            rec = _i
                            break
                questions.append({
                    'id': tr.get('id', ''), 'client_id': cid, 'client': cname,
                    'text': tr.get('title') or '', 'priority': tr.get('priority', 'normal'),
                    'age': _age_days(tr.get('created_at'), today),
                    'hypothesis': a.get('hypothesis') or tr.get('next_action') or '',
                    'options': opts, 'recommended': rec,
                    'confidence': a.get('confidence'), 'updated_at': a.get('updated_at'),
                    'stale': track_stale_days(tr, today),
                })
            elif tr.get('assignee') == 'Operator' and tr.get('priority') == 'high':
                a = tr.get('assist') or {}
                decisions.append({
                    'id': tr.get('id', ''), 'client_id': cid, 'client': cname,
                    'title': tr.get('title') or '',
                    'next': a.get('hypothesis') or tr.get('next_action') or '',
                    'due': tr.get('due_date') or '', 'stale': track_stale_days(tr, today),
                })
    questions.sort(key=lambda q: (_PRIO.get(q['priority'], 1), 0 if q.get('stale') else 1, -(q['age'] or 0)))
    return {'decisions': decisions, 'questions': questions, 'nearest': nearest}


def _brief_text(vm, today, fmt_date):
    nd, qs, dec = vm['nearest'], vm['questions'], vm['decisions']
    parts = [fmt_date(today) + '.']
    parts.append(t("{} awaiting your decision").format(len(dec)) if dec
                 else t("nothing urgent on you"))
    if nd:
        parts.append(t("nearest due — {} {}").format(nd[1], nd[0].strftime('%d.%m')))
    n_old = sum(1 for q in qs if (q['age'] or 0) >= 90)
    if n_old:
        parts.append(t("{} long-standing questions can be closed").format(n_old))
    return '; '.join(parts).replace('.;', '.', 1) + '.'


def _dl_badge(dd, today, esc):
    """Due-date badge in the aw-dl-badge style."""
    if not dd:
        return ''
    n = (dd - today).days
    if n < 0:
        cls, txt = 'dl-overdue', t('overdue {}d').format(-n)
    elif n == 0:
        cls, txt = 'dl-today', t('today')
    elif n <= 3:
        cls, txt = 'dl-soon', t('in {}d').format(n)
    elif n <= 7:
        cls, txt = 'dl-week', t('in {}d').format(n)
    else:
        cls, txt = 'dl-plan', dd.strftime('%d.%m')
    return f'<span class="aw-dl-badge {cls}">{esc(txt)}</span>'


def render_brief_zone(clients, state_read, plan_dir, today, fmt_date=None,
                      esc=None, esca=None, make_attrs=None,
                      sections=('brief', 'decisions', 'questions')):
    esc = esc or _esc
    esca = esca or _esca
    fmt_date = fmt_date or (lambda d: d.strftime('%d.%m.%Y'))
    vm = collect_brief(clients, state_read, today)

    # 1) Brief — a light lead line inside the widget card
    brief = (
        '<div class="aw-widget brief-lead">'
        '<div class="aw-head">' + t('🧭 Brief for today') + '</div>'
        '<div class="aw-body brief-text">' + esc(_brief_text(vm, today, fmt_date)) + '</div>'
        '</div>'
    )

    # 2) Needs your decision
    dec = vm['decisions']
    if dec:
        rows = []
        for d in dec:
            attrs = make_attrs(d) if make_attrs else ''
            badge = _dl_badge(_to_date(d['due']), today, esc) or '<span class="brief-age">' + esc(t('decision')) + '</span>'
            _ds = (' \u00b7 \u23F3 ' + t('stale for {}d').format(d['stale'])) if d.get('stale') else ''
            sub = ('<div class="brief-sub">' + esc(d['next']) + _ds + '</div>') if (d['next'] or d.get('stale')) else ''
            rows.append(
                '<div class="aw-row track-card-clickable"' + attrs + '>' + badge +
                '<span class="aw-text">' + esc(d['client'] + ' — ' + d['title']) + sub + '</span></div>'
            )
        body = ''.join(rows)
    else:
        body = '<div class="aw-empty">' + t('Nothing urgent on you — all under control') + '</div>'
    decisions = (
        '<div class="aw-widget aw-decisions"><div class="aw-head">' + t('🚩 Needs your decision') + ' '
        '<span class="aw-count">' + str(len(dec)) + '</span></div>'
        '<div class="aw-body">' + body + '</div></div>'
    )

    # 3) Let's clarify 1-2 things
    # Open questions — ONE expandable block. Default shows 2, chosen by priority +
    # daily rotation (so different questions surface over time); the rest expand below.
    def _rich_q(q):
        attrs = make_attrs(q) if make_attrs else ''
        base = (q['client'] + ': ' + q['text']).strip(': ')
        age = ('<span class="brief-age">' + esc(t('pending {}d').format(q['age'])) + '</span>') if q['age'] else '<span class="brief-age">' + esc(t('question')) + '</span>'
        stale_chip = (' <span class="brief-stale">⏳ ' + esc(t('{}d without movement').format(q['stale'])) + '</span>') if q.get('stale') else ''
        opts = q.get('options') or [
            {'label': t('Close'),
             'prompt': base + ' — close the question: ' + (q['hypothesis'] or '') + '. Apply to state and remove from open items.'},
            {'label': t('Ask the client'),
             'prompt': base + ' — need to clarify with the client, help me phrase the request.'},
            {'label': t('Defer a quarter'),
             'prompt': base + ' — defer it with a wake-up in a quarter.'},
        ]
        rec = q.get('recommended')
        btns = []
        for i, o in enumerate(opts):
            is_rec = rec is not None and i == rec
            btns.append('<button class="brief-opt' + (' rec' if is_rec else '') + '" '
                        'data-prompt="' + esca(o.get('prompt', '')) + '">' + esc(o.get('label', ''))
                        + ('<span class="rec-tag">' + esc(t('recommended')) + '</span>' if is_rec else '') + '</button>')
        btns.append('<button class="brief-opt brief-opt-free" data-prompt="'
                    + esca(base + " — I'll answer differently, my answer: ") + '">' + esc(t('answer differently')) + '</button>')
        hyp = ('<div class="brief-hyp">' + esc(t('hypothesis:')) + ' ' + esc(q['hypothesis']) + '</div>') if q['hypothesis'] else ''
        return ('<div class="brief-q">'
                '<div class="aw-row track-card-clickable brief-q-head"' + attrs + '>' + age
                + '<span class="aw-text">' + esc(base) + stale_chip + '</span></div>' + hyp
                + '<div class="brief-opts">' + ''.join(btns) + '</div></div>')

    _qs = vm['questions']
    _srt = sorted(_qs, key=lambda q: (_PRIO.get(q.get('priority', 'normal'), 1),
                                      -(q.get('stale') or 0), -(q.get('age') or 0)))
    _high = [q for q in _srt if q.get('priority') == 'high']
    _rest = [q for q in _srt if q.get('priority') != 'high']
    _shown = list(_high[:2])
    if len(_shown) < 2 and _rest:
        _off = today.toordinal() % len(_rest)          # daily rotation through the pool
        _rot = _rest[_off:] + _rest[:_off]
        for q in _rot:
            if len(_shown) >= 2:
                break
            _shown.append(q)
    _shown_ids = {id(q) for q in _shown}
    _remaining = [q for q in _srt if id(q) not in _shown_ids]

    _shown_html = ''.join(_rich_q(q) for q in _shown)
    from collections import OrderedDict as _OD
    _byc = _OD()
    for q in _remaining:
        _byc.setdefault(q['client'], []).append(q)
    _more = []
    for _cl, _cqs in _byc.items():
        _more.append('<div class="qa-client">' + esc(_cl) + ' <span class="qa-n">' + str(len(_cqs)) + '</span></div>')
        for q in _cqs:
            _at = make_attrs(q) if make_attrs else ''
            _st = (' <span class="brief-stale">⏳ ' + esc(t('{}d without movement').format(q['stale'])) + '</span>') if q.get('stale') else ''
            _more.append('<div class="aw-row track-card-clickable qa-row"' + _at + '><span class="aw-text">' + esc(q['text']) + _st + '</span></div>')
    _more_html = ('<details class="qa-more"><summary>' + t('Show the rest') + ' (' + str(len(_remaining)) + ')</summary>'
                  '<div class="qa-more-body">' + ''.join(_more) + '</div></details>') if _remaining else ''

    questions = (
        '<div class="aw-widget aw-questions"><div class="aw-head">' + t('❓ Open questions') + ' '
        '<span class="aw-count">' + str(len(_qs)) + '</span></div>'
        '<div class="aw-body">' + _shown_html + _more_html + '</div></div>'
    ) if _qs else ''

    _parts = {'brief': brief, 'decisions': decisions, 'questions': questions}
    return '<section class="brief-zone">' + ''.join(_parts[s] for s in sections) + '</section>'

BRIEF_CSS = (
    ".brief-lead{border-left:3px solid var(--accent-blue)}"
    ".brief-text{color:var(--text-primary);font-size:15px;line-height:1.6}"
    ".brief-sub{font-size:14px;color:var(--text-secondary);margin-top:2px;line-height:1.4}"
    ".brief-age{font-size:14px;padding:3px 10px;border-radius:6px;background:var(--bg-page);"
    "color:var(--text-muted);white-space:nowrap;flex-shrink:0;min-width:100px;text-align:center}"
    ".brief-q{padding:10px 0;border-bottom:1px solid var(--border)}"
    ".brief-q:last-child{border-bottom:none}"
    ".brief-q-head{margin-bottom:2px}"
    ".brief-hyp{font-size:14px;color:var(--text-muted);margin:2px 0 8px 108px;line-height:1.4}"
    ".brief-opts{display:flex;gap:6px;flex-wrap:wrap;margin-left:108px}"
    ".brief-opt{font-size:14px;padding:4px 11px;border:1px solid var(--border);background:var(--bg-card);"
    "color:var(--text-primary);border-radius:6px;cursor:pointer;font-family:inherit;transition:all 120ms}"
    ".brief-opt:hover{border-color:var(--accent-blue);color:var(--accent-blue)}"
    ".brief-opt.rec{border-color:var(--accent-blue);background:var(--blue-bg);color:var(--accent-blue)}"
    ".rec-tag{font-size:12px;margin-left:6px;color:var(--accent-blue)}"
    ".brief-opt-free{border:none;background:none;color:var(--text-secondary)}"
    ".brief-opt-free:hover{color:var(--accent-blue)}"
    ".brief-stale{font-size:14px;color:#8A6730;background:var(--yellow-bg);padding:1px 7px;border-radius:6px;white-space:nowrap}"
    ".aw-decisions{border-left:4px solid var(--accent-red)}"
    ".aw-decisions .aw-head{color:var(--accent-red)}"
    ".aw-decisions .aw-row{background:var(--red-bg);border-bottom:none;margin-bottom:6px}"
    ".aw-decisions .aw-row:hover{background:#F4CBC4}"
    ".aw-questions{border-left:3px solid var(--border)}"
    ".aw-questions .aw-head{color:var(--text-muted)}"
    ".aw-questions-all{border-left:3px solid var(--border)}"
    ".aw-questions-all>summary{cursor:pointer;list-style:none}"
    ".aw-questions-all>summary::-webkit-details-marker{display:none}"
    ".aw-questions-all .aw-head{color:var(--text-muted)}"
    ".qa-client{font-size:13px;font-weight:600;color:var(--text-secondary);margin:10px 0 3px;text-transform:uppercase;letter-spacing:.03em}"
    ".qa-client:first-child{margin-top:0}"
    ".qa-n{color:var(--text-muted);font-weight:500}"
    ".qa-row{padding:5px 0}"
    ".qa-more{margin-top:8px;border-top:1px solid var(--border);padding-top:6px}"
    ".qa-more>summary{cursor:pointer;font-size:14px;color:var(--accent-blue);font-weight:500;list-style:none;padding:4px 0}"
    ".qa-more>summary::-webkit-details-marker{display:none}"
    ".qa-more-body{margin-top:4px}"
)


# === Narrative layer: "Analysis and recommendations" (synthesis, not fact) ===
# Stored as a fenced ```analysis {JSON} ``` block in mental_model.md (system-wide/client).
# Written/refreshed by mm_update; rendering is read-only; marks "stale" if its date < last movement.
import re as _re_an


def load_analysis_text(txt):
    """Extracts {updated_at, summary, recommendations[]} from the ```analysis block in the text. {} if missing/broken."""
    m = _re_an.search(r"```analysis\s*\n(.*?)\n```", txt or "", _re_an.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(1)) or {}
    except Exception:
        return {}


def build_client_analysis_from_state(client_id, client_name, state_read, today):
    """State-derived {summary, recommendations[]} for one client.

    Replaces the old ```analysis JSON block that used to be parsed out of
    mental_model.md. Built purely from state/tasks.json: a one-line summary of
    what's in flight + the highest-leverage open items as recommendations.
    Returns {} when there is nothing actionable (zone then renders empty).
    """
    try:
        tdata = state_read(client_id, 'tasks.json') or {}
    except Exception:
        tdata = {}
    tasks = tdata.get('tasks', []) if isinstance(tdata, dict) else (tdata or [])
    active = [tr for tr in tasks
              if isinstance(tr, dict) and tr.get('status') in ('active', 'open', 'in_progress', 'awaiting', 'awaiting_external')]
    if not active:
        return {}

    nearest = None
    for tr in active:
        dd = _to_date(tr.get('due_date'))
        if dd and (nearest is None or dd < nearest[0]):
            nearest = (dd, tr.get('title') or '')

    n = len(active)
    summary = (t('{} active item in flight').format(n) if n == 1
               else t('{} active items in flight').format(n))
    if nearest:
        summary += t('; nearest due {} — {}').format(nearest[0].strftime('%d.%m'), nearest[1])
    summary += '.'

    def _prio(tr):
        return _PRIO.get(tr.get('priority', 'normal'), 1)

    recs = []
    for tr in sorted(active, key=lambda x: (_prio(x), _to_date(x.get('due_date')) or date.max))[:3]:
        title = tr.get('title') or ''
        na = (tr.get('next_action') or '').strip()
        due = tr.get('due_date') or ''
        why_bits = []
        if due:
            why_bits.append(t('due {}').format(due))
        if na:
            why_bits.append(na)
        recs.append({
            'priority': tr.get('priority', 'normal'),
            'title': title,
            'why': ' · '.join(why_bits),
            'prompt': (client_name or client_id) + ': ' + title +
                      ('. ' + na if na else '') + ' Open state/*.json and propose the next step.',
        })
    return {'updated_at': today.isoformat(), 'summary': summary, 'recommendations': recs}


def render_analysis_zone(analysis, today, last_change=None, esc=None, esca=None):
    """The "Analysis and recommendations" block. Self-contained (an-* classes). '' if empty."""
    esc = esc or _esc; esca = esca or _esca
    if not analysis or not (analysis.get("summary") or analysis.get("recommendations")):
        return ""
    upd_d = _to_date(analysis.get("updated_at") or "")
    stale = bool(upd_d and last_change and last_change > upd_d)
    upd_txt = (t("updated {}").format(upd_d.strftime("%d.%m")) if upd_d else t("date ?"))
    stale_pill = ' <span class="an-stale">' + esc(t("stale — refresh")) + '</span>' if stale else ""
    _BADGE = {"high": ("an-bh", t("important")), "normal": ("an-bn", t("medium")), "low": ("an-bl", t("later"))}
    rows = []
    for r in (analysis.get("recommendations") or []):
        cls, lbl = _BADGE.get(r.get("priority", "normal"), _BADGE["normal"])
        why = ('<div class="an-why">' + esc(r.get("why", "")) + '</div>') if r.get("why") else ""
        btn = ('<button class="an-btn" data-prompt="' + esca(r.get("prompt", "")) + '">' + esc(t("🔍 Break it down")) + '</button>') if r.get("prompt") else ""
        rows.append('<div class="an-rec"><span class="an-badge ' + cls + '">' + lbl + '</span>'
                    '<div class="an-rec-body"><div class="an-rec-title">' + esc(r.get("title", "")) + '</div>' + why + '</div>'
                    + btn + '</div>')
    recs_html = ('<div class="an-recs-label">' + esc(t("Recommendations")) + '</div>' + ''.join(rows)) if rows else ""
    summ = ('<p class="an-summary">' + esc(analysis.get("summary", "")) + '</p>') if analysis.get("summary") else ""
    return (
        '<div class="an-widget">'
        '<div class="an-head"><span class="an-title">' + esc(t('🧠 Analysis and recommendations')) + '</span>'
        '<span class="an-meta">' + esc(upd_txt) + ' · ' + esc(t('judgment, not fact')) + stale_pill + '</span></div>'
        + summ + recs_html + '</div>'
    )


ANALYSIS_CSS = (
    ".an-widget{background:var(--bg-card);border:1px solid var(--border);border-left:3px solid #7F77DD;"
    "border-radius:var(--radius-card);padding:var(--space-md) var(--space-lg);margin-bottom:var(--space-lg);"
    "box-shadow:0 1px 2px rgba(0,0,0,0.03)}"
    ".an-head{display:flex;justify-content:space-between;align-items:baseline;gap:var(--space-sm);"
    "margin-bottom:var(--space-sm);flex-wrap:wrap}"
    ".an-title{font-size:16px;font-weight:600;color:var(--text-primary)}"
    ".an-meta{font-size:14px;color:var(--text-muted)}"
    ".an-stale{color:var(--accent-red);font-weight:600}"
    ".an-summary{font-size:15px;line-height:1.6;color:var(--text-primary);margin:0 0 var(--space-md)}"
    ".an-recs-label{font-size:14px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px}"
    ".an-rec{display:flex;align-items:flex-start;gap:10px;padding:9px 0;border-top:1px solid var(--border)}"
    ".an-badge{font-size:13px;padding:3px 10px;border-radius:6px;font-weight:600;white-space:nowrap;"
    "flex-shrink:0;min-width:64px;text-align:center}"
    ".an-bh{background:var(--red-bg);color:#791F1F}"
    ".an-bn{background:var(--blue-bg);color:#0C447C}"
    ".an-bl{background:var(--bg-page);color:var(--text-secondary)}"
    ".an-rec-body{flex:1;min-width:0}"
    ".an-rec-title{font-size:15px;font-weight:500;color:var(--text-primary)}"
    ".an-why{font-size:14px;color:var(--text-secondary);margin-top:2px;line-height:1.45}"
    ".an-btn{flex-shrink:0;font-size:14px;padding:6px 12px;border:1px solid var(--border);background:var(--bg-card);"
    "color:var(--text-primary);border-radius:var(--radius-btn);cursor:pointer;font-family:inherit;font-weight:500;"
    "transition:all var(--transition)}"
    ".an-btn:hover{border-color:var(--accent-blue);color:var(--accent-blue);background:var(--blue-bg)}"
)


def latest_history_change(plan_dir):
    """Date of the last movement in history.jsonl across all clients (to mark "stale"). None if none."""
    import glob
    latest = None
    for hp in (glob.glob(os.path.join(plan_dir, '*', 'state', 'history.jsonl'))
               + glob.glob(os.path.join(plan_dir, '*', '*', 'state', 'history.jsonl'))):
        try:
            lines = open(hp, encoding="utf-8").read().strip().splitlines()
        except Exception:
            continue
        for ln in lines[-3:]:
            try:
                d = _to_date(json.loads(ln).get("ts"))
            except Exception:
                d = None
            if d and (latest is None or d > latest):
                latest = d
    return latest
