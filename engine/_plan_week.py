"""_plan_week.py — the "Plan — Week" page.

A 7-day grid with tasks by day.
Today is highlighted. Weekends are dimmed. Task color is by priority.
"""
import json
from datetime import timedelta, date

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
MONTH_RU = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def _priority_class(t):
    """Color class for the task chip."""
    p = t.get('priority')
    if p == 'overdue':
        return 'ev-red'
    if p == 'urgent':
        return 'ev-red'
    if p == 'soon':
        return 'ev-amber'
    if p == 'plan':
        return 'ev-blue'
    return 'ev-grey'


_SEV = {'ev-red': 0, 'ev-amber': 1, 'ev-blue': 2, 'ev-grey': 3}


def _short_name(client_name):
    """SP Client A X.X. → Clie"""
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


def render_plan_week():
    """Main function."""
    today = TODAY
    # Find this week's Monday
    monday = today - timedelta(days=today.weekday())
    days = [monday + timedelta(days=i) for i in range(7)]

    by_day = aggregate_by_day(days=21, today=today)
    all_groups = aggregate_tasks(today)

    n_hot = len(all_groups['hot'])

    # Count tasks for this week
    week_tasks_count = sum(len(by_day.get(d, [])) for d in days)

    def _ev_chip(t):
        cli = _short_name(t.get('client_name', ''))
        what_raw = t.get('what', '')
        what = _esc(_translate_tech_terms(what_raw[:30]))
        ev_cls = _priority_class(t)
        cid = t.get('client_id') or ''
        tooltip = _esc(t.get('client_name', '') + ' · ' + what_raw)
        dl = t.get('days_left')
        due = t.get('due_date')
        badge = ''
        if dl is not None:
            if dl < 0: badge = _t('overdue {}d').format(-dl)
            elif dl == 0: badge = _t('today')
            elif dl <= 3: badge = _t('in {}d').format(dl)
            elif due: badge = due.strftime('%d.%m')
        src_raw = t.get('source', '')
        src_ref = t.get('source_ref', '') or ''
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
        return (f'<div class="ev {ev_cls} track-card-clickable" title="{tooltip}"{da}>'
                f'<b>{_esc(cli)}</b> {what}</div>')

    def _ev_wave_chip(members):
        wcls = min((_priority_class(m) for m in members), key=lambda c: _SEV.get(c, 9))
        op = _op_title(members)
        op_short = (op[:24] + '…') if len(op) > 25 else op
        n = len({m.get('client_id') for m in members})
        inner = ''.join(_ev_chip(m) for m in members)
        return ('<details class="ev-wave ' + wcls + '"><summary><b>'
                + _esc(op_short) + '</b> · ' + str(n) + '</summary>'
                '<div class="ev-wave-body">' + inner + '</div></details>')

    cells_html = []
    for d in days:
        is_today = (d == today)
        is_weekend = d.weekday() >= 5
        cls = 'day'
        if is_today:
            cls += ' today'
        if is_weekend:
            cls += ' wknd'
        day_tasks = by_day.get(d, [])
        _waves, _singles = cluster_tasks(day_tasks)
        _chips = [_ev_wave_chip(m) for m in _waves] + [_ev_chip(t) for t in _singles]
        events_html = ''.join(_chips[:12])
        if len(_chips) > 12:
            events_html += f'<div class="ev-more">+ {len(_chips) - 12}</div>'
        if not events_html:
            events_html = '<div class="ev-empty">—</div>'
        dow = DOW_RU[d.weekday()]
        cells_html.append(
            f'<div class="{cls}">'
            f'<div class="day-head">{dow} {d.day:02}</div>'
            f'{events_html}'
            f'</div>'
        )

    week_grid = '<section class="week-grid">' + ''.join(cells_html) + '</section>'

    # "No fixed date" block — tracks and monthly_check without a deadline
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


    # Period title
    start_str = f'{days[0].day:02}.{days[0].month:02}'
    end_str = f'{days[-1].day:02}.{days[-1].month:02}'
    period_label = f'{start_str} – {end_str}'

    extra_css = (
        '.page-title{font-size:19px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.03em;margin:0 0 6px}'
        '.plan-summary{font-size:16px;color:var(--text-secondary);margin:0 0 var(--space-md)}'
        '.week-grid{display:grid;grid-template-columns:repeat(7,minmax(150px,1fr));gap:6px;overflow-x:auto}'
        '@media(max-width:900px){.week-grid{grid-template-columns:1fr}}'
        '.day{background:var(--bg-card);border:1px solid var(--border);'
        'border-radius:var(--radius-card);padding:10px;min-height:220px}'
        '.day.today{background:#EEEDFE;border-color:#AFA9EC}'
        '.day.wknd{opacity:0.75}'
        '.day-head{font-size:14px;color:var(--text-primary);text-align:center;'
        'padding-bottom:8px;margin-bottom:8px;border-bottom:1px solid var(--border);'
        'font-weight:600;text-transform:uppercase;letter-spacing:0.04em}'
        '.day.today .day-head{color:#3C3489}'
        '.ev{display:block;font-size:14px;padding:6px 8px;border-radius:4px;'
        'margin-bottom:4px;line-height:1.35;text-decoration:none;color:var(--text-primary);'
        'overflow:hidden;white-space:normal;word-wrap:break-word}'
        '.ev b{font-weight:600;margin-right:4px}'
        '.ev.ev-red{background:#FCEBEB;color:#791F1F}'
        '.ev.ev-amber{background:#FAEEDA;color:#633806}'
        '.ev.ev-blue{background:#E6F1FB;color:#0C447C}'
        '.ev.ev-grey{background:var(--bg-page);color:var(--text-secondary)}'
        '.ev:hover{opacity:0.85}'
        '.ev-empty{color:var(--text-muted);font-size:15px;text-align:center;'
        'padding:var(--space-sm) 0}'
        '.ev-more{font-size:15px;color:var(--text-secondary);text-align:center;'
        'padding:4px;font-style:italic;font-weight:500}'
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
        '.ev-wave{margin-bottom:4px}'
        '.ev-wave>summary{display:block;font-size:14px;padding:6px 8px;border-radius:4px;cursor:pointer;list-style:none;line-height:1.35;font-weight:600}'
        '.ev-wave>summary::-webkit-details-marker{display:none}'
        '.ev-wave>summary::after{content:" ▾";opacity:.55;font-weight:400}'
        '.ev-wave[open]>summary::after{content:" ▴"}'
        '.ev-wave.ev-red>summary{background:#FCEBEB;color:#791F1F}'
        '.ev-wave.ev-amber>summary{background:#FAEEDA;color:#633806}'
        '.ev-wave.ev-blue>summary{background:#E6F1FB;color:#0C447C}'
        '.ev-wave.ev-grey>summary{background:var(--bg-page);color:var(--text-secondary)}'
        '.ev-wave-body{padding:3px 0 2px 6px}'
        '.loose-wave{border-bottom:1px solid var(--border)}'
        '.loose-wave-head{display:flex;align-items:center;gap:8px;padding:8px var(--space-md);background:var(--bg-page);border-bottom:1px solid var(--border)}'
        '.loose-wave-op{font-weight:600;font-size:15px;flex:1;min-width:0}'
        '.loose-wave .loose-row{padding-left:calc(var(--space-md) + 8px)}'
    )

    head = render_header()
    title = t('Plan — Week')

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
            active='plan_week',
            counts={'plan_today': n_hot, 'plan_week': week_tasks_count}
        )
        + '<main class="main-content">'
        + head
        + '<h1 class="page-title">' + t('Plan — week · ') + period_label + '</h1>'
        + '<div class="plan-summary">' + t('{} tasks with deadlines this week').format(week_tasks_count) + '</div>'
        + MODE_SWITCH_HTML
        + week_grid + loose_html
        + '</main></div>'
                + PROMPT_MODAL_HTML + DICTATE_MODAL_HTML + TRACK_MODAL_HTML
        + NEW_JS_FRAGMENT + PROMPT_MODAL_JS + DICTATE_JS + TRACK_MODAL_JS + MODE_SWITCH_JS +
        '</body></html>'
    )
