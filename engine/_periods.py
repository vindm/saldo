# -*- coding: utf-8 -*-
"""_periods.py — "Periods" lens: the monthly cycle viewed by reporting period.

For each open reporting period (April, May, June…) it shows, across all clients,
how far each pipeline STAGE has progressed: per stage, how many clients still have
open work. A view over state — writes nothing. Complements the Plan (by horizon)
and the Calendar (by due date) with a "where does each month stand" overview.
"""
from generate import (
    DESIGN_TOKENS_CSS, OVERVIEW_SPECIFIC_CSS, OUT_DIR, TODAY,
)
from _helpers import _esc
from _strings import t
from _sidebar import render_sidebar, SIDEBAR_CSS
from _overview_shared import render_header
from _aggregator import aggregate_tasks
import _plan_waves as PW
import _pipeline as P

try:
    from _config import LOCALE as _LOC
except Exception:
    _LOC = 'ru'
_LOC = _LOC if _LOC in ('ru', 'en') else 'ru'

_DONE = {'done', 'completed', 'cancelled', 'dropped', 'dismissed', 'closed', 'resolved', 'deferred', 'paid'}

PERIODS_CSS = (
    '.page-title{font-size:19px;font-weight:600;color:var(--text-secondary);'
    'text-transform:uppercase;letter-spacing:.03em;margin:0 0 6px}'
    '.pp-sub{font-size:15px;color:var(--text-secondary);margin:0 0 var(--space-md)}'
    '.pp-period{background:var(--bg-card);border:1px solid var(--border);'
    'border-radius:var(--radius-card);margin-bottom:var(--space-md);overflow:hidden}'
    '.pp-head{display:flex;align-items:center;gap:10px;padding:12px var(--space-md);'
    'background:var(--bg-page);border-bottom:1px solid var(--border)}'
    '.pp-head h3{font-size:17px;font-weight:600;margin:0;text-transform:capitalize}'
    '.pp-cohort{font-size:14px;color:var(--text-secondary);padding:2px 10px;'
    'background:var(--bg-card);border:1px solid var(--border);border-radius:10px;font-weight:500}'
    '.pp-flow{display:flex;flex-wrap:wrap;align-items:stretch;gap:6px;padding:var(--space-md)}'
    '.pp-stage{flex:1;min-width:130px;border:1px solid var(--border);border-radius:10px;'
    'padding:9px 11px;display:flex;flex-direction:column;gap:3px}'
    '.pp-stage.s-done{background:var(--green-bg);border-color:transparent}'
    '.pp-stage.s-active{background:var(--blue-bg);border-color:#B5D4F4}'
    '.pp-stage.s-over{background:#FCEBEB;border-color:#F09595}'
    '.pp-stage.s-none{background:var(--bg-page);opacity:.6}'
    '.pp-stname{font-size:13px;font-weight:600;color:var(--text-primary)}'
    '.pp-stnum{font-size:13px;color:var(--text-secondary)}'
    '.pp-arrow{align-self:center;color:var(--text-muted);font-size:13px}'
    '.pp-link{text-decoration:none;cursor:pointer}'
    '.pp-link:hover{box-shadow:inset 0 0 0 2px var(--accent-blue)}'
)


def _fmt(p):
    return PW._fmt_period(p, _LOC)


def _period_sort_key(p):
    import re
    m = re.match(r'^(\d{4})-(\d{2})$', p or '')
    if m:
        return (int(m.group(1)), int(m.group(2)))
    q = re.match(r'^(\d{4})-Q([1-4])$', p or '')
    if q:
        return (int(q.group(1)), (int(q.group(2)) - 1) * 3 + 1)  # quarter → its start month
    return (9999, 99)  # unknown periods last


def render_periods():
    today = TODAY
    all_tasks = aggregate_tasks(today).get('all', [])
    stages = P.stages()
    # period -> stage_code -> {'open': set(clients), 'all': set(clients), 'over': bool}
    data = {}
    cohort = {}
    for tk in all_tasks:
        op = PW._op_canonical(tk)
        if not isinstance(op, str) or not op.startswith('stage:'):
            continue
        code, _, per = op[len('stage:'):].partition('|')
        if not per:
            per = '—'
        cid = tk.get('client_id') or '?'
        d = data.setdefault(per, {}).setdefault(code, {'open': set(), 'all': set(), 'over': False})
        d['all'].add(cid)
        cohort.setdefault(per, set()).add(cid)
        st = (tk.get('status') or '').lower()
        if st not in _DONE:
            d['open'].add(cid)
            if (tk.get('days_left') is not None and tk['days_left'] < 0):
                d['over'] = True

    periods = sorted(data.keys(), key=_period_sort_key)
    cards = []
    for per in periods:
        coh = len(cohort.get(per, set()))
        chips = []
        for i, s in enumerate(stages):
            code = s['code']
            info = data.get(per, {}).get(code)
            title = P.stage_title(code, _LOC)
            icon = PW._STAGE_ICON.get(code, '•')
            if not info or not info['all']:
                cls, num = 's-none', '—'
            else:
                openc = len(info['open'])
                if openc == 0:
                    cls, num = 's-done', t('done')
                else:
                    cls = 's-over' if info['over'] else 's-active'
                    num = str(openc) + ' ' + t('in progress')
            if i:
                chips.append('<span class="pp-arrow">→</span>')
            inner = ('<span class="pp-stname">' + icon + ' ' + _esc(title) + '</span>'
                     '<span class="pp-stnum">' + _esc(num) + '</span>')
            if cls in ('s-active', 's-over'):
                href = 'plan_today.html#stage=' + code + '&period=' + (per if per != '—' else '')
                chips.append('<a class="pp-stage ' + cls + ' pp-link" href="' + href + '">' + inner + '</a>')
            else:
                chips.append('<div class="pp-stage ' + cls + '">' + inner + '</div>')
        cards.append(
            '<section class="pp-period"><div class="pp-head">'
            '<h3>' + _esc(_fmt(per)) + '</h3>'
            '<span class="pp-cohort">' + str(coh) + ' ' + t('clients') + '</span></div>'
            '<div class="pp-flow">' + ''.join(chips) + '</div></section>'
        )

    body = ''.join(cards) if cards else '<div class="pp-sub">' + t('No monthly-cycle tasks.') + '</div>'
    head = render_header()
    title = t('Periods')
    return (
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>' + _esc(title) + '</title>'
        '<style>' + DESIGN_TOKENS_CSS + OVERVIEW_SPECIFIC_CSS + SIDEBAR_CSS + PERIODS_CSS + '</style>'
        '</head><body><div class="layout-shell">'
        + render_sidebar(active='periods')
        + '<main class="main-content">' + head
        + '<h1 class="page-title">' + title + '</h1>'
        + '<div class="pp-sub">' + t('Each open reporting period and how far each stage has progressed across clients.') + '</div>'
        + body
        + '</main></div></body></html>'
    )
