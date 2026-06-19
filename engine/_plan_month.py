"""_plan_month.py — the "Plan — Month" page.

A calendar grid of 5-6 rows × 7 columns.
Red tax dates (25, 30, 31) are highlighted with a border.
Today is purple. A cell shows the task chips.
"""
import json
from datetime import date, timedelta
from calendar import monthrange

from generate import (
    clients, TODAY,
    _esc, _esca,
    DESIGN_TOKENS_CSS, OVERVIEW_SPECIFIC_CSS, NEW_JS_FRAGMENT,
)
from _helpers import _format_date_ru, _translate_tech_terms
from _strings import t
_t = t  # alias: nested helpers bind `t` to the task dict, shadowing the import
from _overview_v2 import OVERVIEW_V2_CSS
from _overview_shared import render_header
from _sidebar import render_sidebar, SIDEBAR_CSS
from _dictate import DICTATE_CSS, DICTATE_MODAL_HTML, DICTATE_JS
from _css import PROMPT_MODAL_CSS, PROMPT_MODAL_HTML, PROMPT_MODAL_JS
from _mode_switch import MODE_SWITCH_HTML, MODE_SWITCH_CSS, MODE_SWITCH_JS
from _aggregator import aggregate_by_day, aggregate_tasks, get_loose_tasks
from _track_modal import TRACK_MODAL_CSS, TRACK_MODAL_HTML, TRACK_MODAL_JS
from _track_attrs import build_track_data_attrs
from _plan_waves import cluster_tasks, _op_title


DOW_RU = [t('Mon'), t('Tue'), t('Wed'), t('Thu'), t('Fri'), t('Sat'), t('Sun')]
MONTH_RU_NOM = [t('January'), t('February'), t('March'), t('April'), t('May'), t('June'),
                t('July'), t('August'), t('September'), t('October'), t('November'), t('December')]

# Red tax dates: 25 — USN advances/notifications; 28 — USN tax; 30/31 — fixed contributions and patent
TAX_DAYS = {25, 28, 30, 31}


def _priority_class(t):
    p = t.get('priority')
    if p == 'overdue' or p == 'urgent':
        return 'm-red'
    if p == 'soon':
        return 'm-amber'
    if p == 'plan':
        return 'm-blue'
    return 'm-grey'


_SEV = {'m-red': 0, 'm-amber': 1, 'm-blue': 2, 'm-grey': 3}


def _short_name(client_name):
    if not client_name:
        return ''
    s = client_name.replace('SP ', '')
    parts = s.split(' ')
    return parts[0][:4]


def _track_type_for(client_id):
    """team or direct by client_id."""
    try:
        from generate import clients as _cls
        for c in _cls:
            if c.get('id') == client_id:
                return c.get('group', 'team')
    except Exception:
        pass
    return 'team'


def render_plan_month():
    today = TODAY
    year = today.year
    month = today.month
    days_in_month = monthrange(year, month)[1]

    # Monday of the first week (including the 1st)
    first = date(year, month, 1)
    grid_start = first - timedelta(days=first.weekday())
    # Guarantee 6 weeks
    total_days = 42

    # Take a larger horizon to capture both the previous and the next month
    horizon = (date(year, month, days_in_month) - today).days + 14
    by_day = aggregate_by_day(days=max(horizon, 30), today=today)
    all_groups = aggregate_tasks(today)

    n_hot = len(all_groups['hot'])

    # How many tasks in this month
    month_tasks_count = sum(
        len(by_day.get(d, []))
        for d in by_day
        if d.year == year and d.month == month
    )

    # Weekday header
    dow_html = ''.join(
        f'<div class="m-dow{" m-wknd" if i >= 5 else ""}">{DOW_RU[i]}</div>'
        for i in range(7)
    )

    def _ev_chip(t):
        cli = _short_name(t.get('client_name', ''))
        what_raw = t.get('what', '')
        ev_cls = _priority_class(t)
        tooltip = _esc(t.get('client_name', '') + ' · ' + what_raw)
        cid = t.get('client_id') or ''
        short_what = _esc(what_raw[:20])
        dl = t.get('days_left'); due = t.get('due_date'); badge = ''
        if dl is not None:
            if dl < 0: badge = _t('overdue {}d').format(-dl)
            elif dl == 0: badge = _t('today')
            elif dl <= 3: badge = _t('in {}d').format(dl)
            elif due: badge = due.strftime('%d.%m')
        src_raw = t.get('source', ''); src_ref = t.get('source_ref', '') or ''
        source_text = src_raw + (' · ' + src_ref if src_ref else '')
        _b = dict(t)
        _b['id'] = (t.get('id') or src_ref)[:60]
        _b['client_id'] = cid
        _b['title'] = what_raw
        _b['source'] = source_text
        _b['track_id'] = t.get('source_ref') or _b.get('id')
        da = build_track_data_attrs(_b, _esca, today=today,
                                    track_type_for=_track_type_for,
                                    badge_override=badge, translate_fn=_translate_tech_terms)
        return (f'<div class="m-ev {ev_cls} track-card-clickable" title="{tooltip}"{da}>'
                f'<b>{_esc(cli)}</b> {short_what}</div>')

    def _ev_wave_chip(members):
        wcls = min((_priority_class(m) for m in members), key=lambda c: _SEV.get(c, 9))
        op = _op_title(members)
        op_short = (op[:15] + '…') if len(op) > 16 else op
        n = len({m.get('client_id') for m in members})
        names = ', '.join(sorted({_short_name(m.get('client_name', '')) for m in members}))
        tip = _esc(op + ' · ' + names)
        return (f'<div class="m-ev m-wave {wcls}" title="{tip}">'
                f'<b>{_esc(op_short)}</b> · {n}</div>')

    cells_html = []
    for i in range(total_days):
        d = grid_start + timedelta(days=i)
        is_other_month = (d.month != month)
        is_today = (d == today)
        is_weekend = d.weekday() >= 5
        is_tax = (d.day in TAX_DAYS) and not is_other_month

        cls = 'm-cell'
        if is_other_month:
            cls += ' m-other'
        if is_today:
            cls += ' m-today'
        if is_weekend:
            cls += ' m-wknd'
        if is_tax:
            cls += ' m-tax'

        day_tasks = by_day.get(d, []) if not is_other_month else []
        _waves, _singles = cluster_tasks(day_tasks)
        _chips = [_ev_wave_chip(m) for m in _waves] + [_ev_chip(t) for t in _singles]
        events_html = ''.join(_chips[:3])
        if len(_chips) > 3:
            events_html += f'<div class="m-more">+ {len(_chips) - 3}</div>'

        cells_html.append(
            f'<div class="{cls}">'
            f'<div class="m-day">{d.day}</div>'
            f'{events_html}'
            f'</div>'
        )

    month_grid = (
        '<section class="month-grid">'
        + dow_html
        + ''.join(cells_html)
        + '</section>'
    )

    # "No fixed date" block — same as in the Week page
    loose_tasks = get_loose_tasks(today)
    loose_html = ''

    def _loose_row(t):
        cli = t.get('client_name', '')
        what = _esc(_translate_tech_terms(t.get('what', '')))
        cid = t.get('client_id')
        src_label = {'track': _t('track'), 'monthly_check': _t('recurring'),
                     'update': _t('updater')}.get(t.get('source'), t.get('source', '?'))
        link_html = ''
        if cid:
            link_html = f'<a href="dashboard_{cid}.html" class="loose-go" title="Dashboard" onclick="event.stopPropagation()">→</a>'
        _b = dict(t)
        _b['id'] = (t.get('id') or t.get('source_ref') or '')[:60]
        _b['client_id'] = cid
        _b['client_name'] = cli
        _b['source'] = src_label
        _b['track_id'] = t.get('source_ref') or _b.get('id')
        t_da = build_track_data_attrs(_b, _esca, today=today,
                                      track_type_for=_track_type_for,
                                      translate_fn=_translate_tech_terms)
        return ('<div class="loose-row track-card-clickable"' + t_da + '>'
                f'<span class="loose-src">{src_label}</span>'
                f'<span class="loose-client">{_esc(cli)}</span>'
                f'<span class="loose-what">{what}</span>'
                f'{link_html}</div>')

    if loose_tasks:
        _lw, _ls = cluster_tasks(loose_tasks)
        _parts = []
        for _m in _lw:
            _n = len({x.get('client_id') for x in _m})
            _parts.append(
                '<div class="loose-wave"><div class="loose-wave-head">'
                f'<span class="loose-wave-op">{_esc(_op_title(_m))}</span>'
                f'<span class="loose-count">{_n} SPs</span></div>'
                + ''.join(_loose_row(t) for t in _m) + '</div>')
        if _ls:
            _srows = ''.join(_loose_row(t) for t in _ls)
            if _lw:
                _parts.append(
                    '<div class="loose-wave"><div class="loose-wave-head">'
                    '<span class="loose-wave-op">' + t('Individual tasks') + '</span>'
                    f'<span class="loose-count">{len(_ls)}</span></div>'
                    + _srows + '</div>')
            else:
                _parts.append(_srows)
        loose_html = (
            '<section class="loose-block">'
            '<div class="loose-head">'
            '<h3>' + t('No fixed date') + '</h3>'
            f'<span class="loose-count">{len(loose_tasks)}</span>'
            '<span class="loose-hint">' + t('active tracks and recurring processes') + '</span>'
            '</div>'
            + ''.join(_parts) +
            '</section>'
        )


    legend = (
        '<div class="m-legend">'
        '<span class="lg lg-red"></span>' + t('urgent/overdue ') +
        '<span class="lg lg-amber"></span>' + t('this week ') +
        '<span class="lg lg-blue"></span>' + t('planned ') +
        '<span class="lg lg-tax"></span>' + t('tax date') +
        '</div>'
    )

    extra_css = (
        '.page-title{font-size:19px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.03em;margin:0 0 6px}'
        '.plan-summary{font-size:16px;color:var(--text-secondary);margin:0 0 var(--space-md)}'
        '.month-grid{display:grid;grid-template-columns:repeat(7,minmax(140px,1fr));gap:2px;overflow-x:auto;'
        'background:var(--border);border:1px solid var(--border);'
        'border-radius:var(--radius-card)}'
        '.m-dow{background:var(--bg-page);font-size:15px;text-transform:uppercase;'
        'letter-spacing:0.04em;text-align:center;padding:8px 0;color:var(--text-primary);'
        'font-weight:600}'
        '.m-dow.m-wknd{color:var(--text-secondary)}'
        '.m-cell{background:var(--bg-card);min-height:110px;padding:8px;font-size:15px;'
        'position:relative}'
        '.m-cell.m-other{background:var(--bg-page);opacity:0.45}'
        '.m-cell.m-today{background:#EEEDFE}'
        '.m-cell.m-wknd{background:var(--bg-page)}'
        '.m-cell.m-wknd.m-today{background:#EEEDFE}'
        '.m-cell.m-tax{box-shadow:inset 0 0 0 2px #F09595}'
        '.m-day{font-size:15px;font-weight:600;color:var(--text-primary);margin-bottom:6px}'
        '.m-cell.m-today .m-day{color:#3C3489;font-weight:700}'
        '.m-cell.m-other .m-day{color:var(--text-muted)}'
        '.m-ev{display:block;font-size:15px;padding:3px 6px;border-radius:3px;'
        'margin-bottom:2px;line-height:1.35;text-decoration:none;overflow:hidden;'
        'white-space:normal;word-wrap:break-word}'
        '.m-ev b{font-weight:600;margin-right:3px}'
        '.m-ev.m-red{background:#FCEBEB;color:#791F1F}'
        '.m-ev.m-amber{background:#FAEEDA;color:#633806}'
        '.m-ev.m-blue{background:#E6F1FB;color:#0C447C}'
        '.m-ev.m-grey{background:var(--bg-page);color:var(--text-secondary)}'
        '.m-more{font-size:15px;color:var(--text-secondary);text-align:center;font-style:italic;font-weight:500}'
        '.m-legend{display:flex;gap:16px;font-size:14px;color:var(--text-primary);'
        'margin-top:var(--space-md);align-items:center;flex-wrap:wrap}'
        '.lg{display:inline-block;width:12px;height:12px;border-radius:2px;'
        'margin-right:6px;vertical-align:-1px}'
        '.lg-red{background:#FCEBEB;border:0.5px solid #F09595}'
        '.lg-amber{background:#FAEEDA;border:0.5px solid #FAC775}'
        '.lg-blue{background:#E6F1FB;border:0.5px solid #B5D4F4}'
        '.lg-tax{background:var(--bg-card);border:2px solid #F09595}'
        '.loose-block{background:var(--bg-card);border:1px solid var(--border);'
        'border-radius:var(--radius-card);margin-top:var(--space-md);overflow:hidden}'
        '.loose-head{display:flex;align-items:center;gap:8px;padding:12px var(--space-md);'
        'background:var(--bg-page);border-bottom:1px solid var(--border)}'
        '.loose-head h3{font-size:17px;font-weight:600;margin:0}'
        '.loose-count{font-size:14px;color:var(--text-secondary);padding:2px 10px;'
        'background:var(--bg-card);border-radius:10px;border:1px solid var(--border);font-weight:500}'
        '.loose-hint{margin-left:auto;font-size:14px;color:var(--text-secondary)}'
        '.loose-row{display:grid;grid-template-columns:100px 200px 1fr auto;gap:var(--space-md);'
        'align-items:center;padding:10px var(--space-md);border-bottom:1px solid var(--border);'
        'font-size:16px;line-height:1.5}'
        '.loose-row:last-child{border-bottom:none}'
        '.loose-row:hover{background:var(--bg-page)}'
        '.loose-src{font-size:15px;color:var(--text-secondary);text-transform:uppercase;'
        'letter-spacing:0.04em;font-weight:500}'
        '.loose-client{font-size:14px;color:var(--text-secondary);font-weight:500}'
        '.loose-what{font-size:16px;color:var(--text-primary);min-width:0;'
        'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;line-height:1.5}'
        '.loose-go{color:var(--accent-blue);text-decoration:none;font-size:18px;'
        'padding:4px 12px;border:1px solid var(--border);border-radius:var(--radius-btn)}'
        '.loose-go:hover{border-color:var(--accent-blue);background:var(--bg-page)}'
        '.m-ev.m-wave{font-weight:600}'
        '.loose-wave{border-bottom:1px solid var(--border)}'
        '.loose-wave-head{display:flex;align-items:center;gap:8px;padding:8px var(--space-md);background:var(--bg-page);border-bottom:1px solid var(--border)}'
        '.loose-wave-op{font-weight:600;font-size:15px;flex:1;min-width:0}'
        '.loose-wave .loose-row{padding-left:calc(var(--space-md) + 8px)}'
    )

    head = render_header()
    title = t('Plan — Month')
    period_label = f'{MONTH_RU_NOM[month-1].capitalize()} {year}'

    return (
        '<!DOCTYPE html>\n<html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMiAzMiI+PGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTUuNSIgZmlsbD0iIzFGNEU3OSIvPjxjaXJjbGUgY3g9IjE2IiBjeT0iMTYiIHI9IjEyLjciIGZpbGw9Im5vbmUiIHN0cm9rZT0iI0I3OTI1NyIgc3Ryb2tlLXdpZHRoPSIxLjMiLz48dGV4dCB4PSIxNiIgeT0iMTciIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJjZW50cmFsIiBmb250LWZhbWlseT0iQXJpYWwsSGVsdmV0aWNhLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZvbnQtd2VpZ2h0PSI3MDAiIGZpbGw9IiNmZmZmZmYiPtCY0JI8L3RleHQ+PC9zdmc+">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>' + _esc(title) + '</title>'
        '<style>' + DESIGN_TOKENS_CSS + OVERVIEW_SPECIFIC_CSS + OVERVIEW_V2_CSS
        + SIDEBAR_CSS + PROMPT_MODAL_CSS + DICTATE_CSS + TRACK_MODAL_CSS + MODE_SWITCH_CSS + extra_css + '</style>'
        '</head><body>'
        '<div class="layout-shell">'
        + render_sidebar(
            active='plan_month',
            counts={'plan_today': n_hot}
        )
        + '<main class="main-content">'
        + head
        + '<h1 class="page-title">' + t('Plan — ') + period_label + '</h1>'
        + '<div class="plan-summary">' + t('{} tasks with deadlines this month').format(month_tasks_count) + '</div>'
        + MODE_SWITCH_HTML
        + month_grid + loose_html
        + legend
        + '</main></div>'
                + PROMPT_MODAL_HTML + DICTATE_MODAL_HTML + TRACK_MODAL_HTML
        + NEW_JS_FRAGMENT + PROMPT_MODAL_JS + DICTATE_JS + TRACK_MODAL_JS + MODE_SWITCH_JS +
        '</body></html>'
    )


# ── Full navigable calendar (replaces the Week/Month tabs) ───────────────────
CAL_CSS = (
    '.page-title{font-size:19px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.03em;margin:0 0 var(--space-md)}'
    '.cal-nav{display:flex;align-items:center;justify-content:center;gap:var(--space-md);margin:0 0 var(--space-md)}'
    '.cal-arrow{font-size:22px;line-height:1;width:38px;height:38px;border:1px solid var(--border);'
    'border-radius:var(--radius-btn);background:var(--bg-card);color:var(--text-primary);cursor:pointer}'
    '.cal-arrow:hover{border-color:var(--accent-blue);color:var(--accent-blue)}'
    '#cal-label{font-size:18px;font-weight:600;min-width:200px;text-align:center;text-transform:capitalize}'
    '.month-grid{display:grid;grid-template-columns:repeat(7,minmax(130px,1fr));gap:2px;overflow-x:auto;'
    'background:var(--border);border:1px solid var(--border);border-radius:var(--radius-card)}'
    '.m-dow{background:var(--bg-page);font-size:14px;text-transform:uppercase;letter-spacing:.04em;'
    'text-align:center;padding:8px 0;color:var(--text-primary);font-weight:600}'
    '.m-dow.m-wknd{color:var(--text-secondary)}'
    '.m-cell{background:var(--bg-card);min-height:104px;padding:7px;font-size:14px;position:relative}'
    '.m-cell.m-other{background:var(--bg-page);opacity:.45}'
    '.m-cell.m-today{background:#EEEDFE}.m-cell.m-wknd{background:var(--bg-page)}'
    '.m-cell.m-wknd.m-today{background:#EEEDFE}.m-cell.m-tax{box-shadow:inset 0 0 0 2px #F09595}'
    '.m-day{font-size:14px;font-weight:600;color:var(--text-primary);margin-bottom:5px}'
    '.m-cell.m-today .m-day{color:#3C3489;font-weight:700}.m-cell.m-other .m-day{color:var(--text-muted)}'
    '.m-ev{display:block;font-size:13px;padding:2px 6px;border-radius:3px;margin-bottom:2px;line-height:1.3;'
    'text-decoration:none;overflow:hidden;white-space:normal;word-wrap:break-word;cursor:pointer}'
    '.m-ev b{font-weight:600;margin-right:3px}'
    '.m-ev.m-red{background:#FCEBEB;color:#791F1F}.m-ev.m-amber{background:#FAEEDA;color:#633806}'
    '.m-ev.m-blue{background:#E6F1FB;color:#0C447C}.m-ev.m-grey{background:var(--bg-page);color:var(--text-secondary)}'
    '.m-ev.m-wave{font-weight:600}'
    '.m-more{font-size:13px;color:var(--text-secondary);text-align:center;font-style:italic;font-weight:500}'
    '.cal-month{display:block}'
)

_SEVMAP = {'m-red': 0, 'm-amber': 1, 'm-blue': 2, 'm-grey': 3}
_EN_MONTHS_CAL = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
                  'August', 'September', 'October', 'November', 'December']


def render_calendar(today=None):
    """Full navigable calendar (‹ › month switching). Replaces Week/Month."""
    try:
        from _config import LOCALE
        loc = LOCALE if LOCALE in ('ru', 'en') else 'ru'
    except Exception:
        loc = 'ru'
    today = today or TODAY

    def _mname(mo):
        return (MONTH_RU_NOM[mo - 1].capitalize() if loc == 'ru' else _EN_MONTHS_CAL[mo - 1])

    all_tasks = aggregate_tasks(today).get('all', [])
    by_day = {}
    for tk in all_tasks:
        d = tk.get('due_date')
        if d is not None and hasattr(d, 'strftime'):
            by_day.setdefault(d, []).append(tk)

    def _shift(yy, mm, delta):
        idx = yy * 12 + (mm - 1) + delta
        return (idx // 12, idx % 12 + 1)

    yms = {(today.year, today.month)}
    for d in by_day:
        yms.add((d.year, d.month))
    yms = sorted(yms)
    # Always allow browsing a few months back and at least one ahead, plus the
    # full span where deadlines actually fall.
    (y0, m0) = min(yms[0], _shift(today.year, today.month, -3))
    (y1, m1) = max(yms[-1], _shift(today.year, today.month, 1))
    months = []
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1; y += 1

    def _ev_chip(tk, month):
        cli = _short_name(tk.get('client_name', ''))
        what_raw = tk.get('what', '')
        ev_cls = _priority_class(tk)
        tooltip = _esc(tk.get('client_name', '') + ' · ' + what_raw)
        cid = tk.get('client_id') or ''
        short_what = _esc(what_raw[:20])
        dl = tk.get('days_left'); due = tk.get('due_date'); badge = ''
        if dl is not None:
            if dl < 0: badge = _t('overdue {}d').format(-dl)
            elif dl == 0: badge = _t('today')
            elif dl <= 3: badge = _t('in {}d').format(dl)
            elif due: badge = due.strftime('%d.%m')
        src_raw = tk.get('source', ''); src_ref = tk.get('source_ref', '') or ''
        _b = dict(tk)
        _b['id'] = (tk.get('id') or src_ref)[:60]
        _b['client_id'] = cid
        _b['title'] = what_raw
        _b['source'] = src_raw + (' · ' + src_ref if src_ref else '')
        _b['track_id'] = tk.get('source_ref') or _b.get('id')
        da = build_track_data_attrs(_b, _esca, today=today, track_type_for=_track_type_for,
                                    badge_override=badge, translate_fn=_translate_tech_terms)
        return ('<div class="m-ev ' + ev_cls + ' track-card-clickable" title="' + tooltip + '"' + da + '>'
                '<b>' + _esc(cli) + '</b> ' + short_what + '</div>')

    def _ev_wave_chip(members):
        wcls = min((_priority_class(mm) for mm in members), key=lambda c: _SEVMAP.get(c, 9))
        op = _op_title(members)
        op_short = (op[:15] + '…') if len(op) > 16 else op
        n = len({mm.get('client_id') for mm in members})
        names = ', '.join(sorted({_short_name(mm.get('client_name', '')) for mm in members}))
        return ('<div class="m-ev m-wave ' + wcls + '" title="' + _esc(op + ' · ' + names) + '">'
                '<b>' + _esc(op_short) + '</b> · ' + str(n) + '</div>')

    def _grid(year, month):
        first = date(year, month, 1)
        gs = first - timedelta(days=first.weekday())
        dow = ''.join('<div class="m-dow' + (' m-wknd' if i >= 5 else '') + '">' + DOW_RU[i] + '</div>' for i in range(7))
        cells = []
        for i in range(42):
            d = gs + timedelta(days=i)
            other = (d.month != month)
            cls = 'm-cell' + (' m-other' if other else '') + (' m-today' if d == today else '')
            cls += (' m-wknd' if d.weekday() >= 5 else '') + (' m-tax' if (d.day in TAX_DAYS and not other) else '')
            dts = by_day.get(d, []) if not other else []
            w, s = cluster_tasks(dts)
            chips = [_ev_wave_chip(mm) for mm in w] + [_ev_chip(x, month) for x in s]
            ev = ''.join(chips[:3]) + (('<div class="m-more">+ ' + str(len(chips) - 3) + '</div>') if len(chips) > 3 else '')
            cells.append('<div class="' + cls + '"><div class="m-day">' + str(d.day) + '</div>' + ev + '</div>')
        return '<section class="month-grid">' + dow + ''.join(cells) + '</section>'

    cur_ym = '%d-%02d' % (today.year, today.month)
    month_divs = []
    for (yy, mm) in months:
        ymk = '%d-%02d' % (yy, mm)
        lbl = _mname(mm) + ' ' + str(yy)
        style = '' if ymk == cur_ym else ' style="display:none"'
        month_divs.append('<div class="cal-month" data-ym="' + ymk + '" data-label="' + lbl + '"' + style + '>' + _grid(yy, mm) + '</div>')

    nav = ('<div class="cal-nav"><button type="button" class="cal-arrow" id="cal-prev">‹</button>'
           '<span id="cal-label"></span>'
           '<button type="button" class="cal-arrow" id="cal-next">›</button></div>')
    cal_js = ('<script>(function(){var M=[].slice.call(document.querySelectorAll(".cal-month"));if(!M.length)return;'
              'var i=M.findIndex(function(x){return x.dataset.ym==="' + cur_ym + '";});if(i<0)i=0;'
              'function show(k){k=Math.max(0,Math.min(M.length-1,k));M.forEach(function(x,j){x.style.display=j===k?"":"none";});'
              'var L=document.getElementById("cal-label");if(L)L.textContent=M[k].dataset.label;i=k;}'
              'var p=document.getElementById("cal-prev"),n=document.getElementById("cal-next");'
              'if(p)p.addEventListener("click",function(){show(i-1);});if(n)n.addEventListener("click",function(){show(i+1);});show(i);})();</script>')

    head = render_header()
    title = t('Calendar')
    return (
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>' + _esc(title) + '</title>'
        '<style>' + DESIGN_TOKENS_CSS + OVERVIEW_SPECIFIC_CSS + OVERVIEW_V2_CSS
        + SIDEBAR_CSS + PROMPT_MODAL_CSS + DICTATE_CSS + TRACK_MODAL_CSS + MODE_SWITCH_CSS + CAL_CSS + '</style>'
        '</head><body><div class="layout-shell">'
        + render_sidebar(active='calendar')
        + '<main class="main-content">' + head
        + '<h1 class="page-title">' + title + '</h1>'
        + MODE_SWITCH_HTML + nav
        + '<div id="cal-months">' + ''.join(month_divs) + '</div>'
        + '</main></div>'
        + PROMPT_MODAL_HTML + DICTATE_MODAL_HTML + TRACK_MODAL_HTML
        + NEW_JS_FRAGMENT + PROMPT_MODAL_JS + DICTATE_JS + TRACK_MODAL_JS + MODE_SWITCH_JS + cal_js
        + '</body></html>'
    )
