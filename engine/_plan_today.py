"""_plan_today.py — the "Plan — Today" page.

An actionable list of today's tasks grouped by category.
Buttons on each task: "💬 Discuss" (a prompt into the chat) and "🎤 Dictate".
"""
import json
import os

from generate import (
    clients, TODAY,
    _esc, _esca,
    DESIGN_TOKENS_CSS, OVERVIEW_SPECIFIC_CSS, NEW_JS_FRAGMENT,
)
from _helpers import _format_date_ru, _translate_tech_terms
from _strings import t
_t = t  # alias: several local helpers bind `t` to the task dict, shadowing the import
from _track_attrs import build_track_data_attrs, build_mm_tracks_index
from _overview_v2 import OVERVIEW_V2_CSS
from _overview_shared import render_header
from _sidebar import render_sidebar, SIDEBAR_CSS
from _dictate import DICTATE_CSS, DICTATE_MODAL_HTML, DICTATE_JS
from _css import PROMPT_MODAL_CSS, PROMPT_MODAL_HTML, PROMPT_MODAL_JS
from _mode_switch import MODE_SWITCH_HTML, MODE_SWITCH_CSS, MODE_SWITCH_JS
from _aggregator import aggregate_tasks
from _track_modal import TRACK_MODAL_CSS, TRACK_MODAL_HTML, TRACK_MODAL_JS
from _assistant_brief import render_assistant_rec_card, ASSISTANT_BRIEF_CSS
from _plan_waves import render_waves_page, render_waves_flat, horizon_counts, WAVES_CSS, WAVES_JS


SCENARIO_RU = {
    'A': t('USN'), 'B': t('USN+Patent'), 'B+E': t('WB+Patent'),
    'C': t('video+self-employed'), 'D': t('rental'), 'E': t('WB'), 'F': t('AUSN'),
}


def _format_due(t):
    """Due-date format for the task row."""
    dl = t.get('days_left')
    due = t.get('due_date')
    if dl is None:
        return ''
    if dl < 0:
        return '<span class="due-overdue">' + _t('overdue {}d').format(-dl) + '</span>'
    if dl == 0:
        return '<span class="due-today">' + _t('today') + '</span>'
    if dl <= 3:
        return '<span class="due-soon">' + _t('in {}d · {}').format(dl, due.strftime("%d.%m")) + '</span>'
    if due:
        return f'<span class="due-plan">{due.strftime("%d.%m")} · {dl}d</span>'
    return f'<span class="due-plan">{dl}d</span>'


def _pill_for(t):
    """Pill by the task's track/scenario."""
    track = t.get('track')
    if not track:
        return '<span class="pill pill-sys">' + _t('general') + '</span>'
    if track == 'team':
        return '<span class="pill pill-team">' + _t('team') + '</span>'
    # direct — get the scenario from the client
    cid = t.get('client_id')
    if cid:
        for c in clients:
            if c['id'] == cid:
                scn = c.get('scenario') or ''
                if scn == 'F':
                    return '<span class="pill pill-ausn">' + _t('AUSN') + '</span>'
                if scn:
                    return f'<span class="pill pill-direct">{_esc(SCENARIO_RU.get(scn, scn))}</span>'
    return '<span class="pill pill-direct">' + _t('direct') + '</span>'


SOURCE_LABEL = {
    'calendar': 'calendar',
    'monthly_check': 'monthly_check',
    'finkoper': 'finkoper',
    'request': 'request log',
    'track': 'mental_model',
    'update': 'updater',
    'tg': 'Telegram',
}



def _due_text(t):
    dl = t.get('days_left')
    due = t.get('due_date')
    if dl is None:
        return ''
    if dl < 0:
        return _t('overdue {}d').format(-dl)
    if dl == 0:
        return _t('today')
    if dl <= 3:
        if due:
            return _t('in {}d · {}').format(dl, due.strftime('%d.%m'))
        return _t('in {}d').format(dl)
    if due:
        return _t('{} · {}d').format(due.strftime('%d.%m'), dl)
    return _t('{}d').format(dl)


def _track_type_for(client_id):
    """team or direct by client_id."""
    try:
        from generate import clients
        for c in clients:
            if c.get('id') == client_id:
                return c.get('group', 'team')
    except Exception:
        pass
    return 'team'


def _render_task_row(t, mm_index=None):
    client_name = t.get('client_name', '')
    what_raw = t.get('what', '')
    what = _esc(_translate_tech_terms(what_raw))
    due_html = _format_due(t)
    pill_html = _pill_for(t)
    cid = t.get('client_id') or ''

    track_id = (t.get('id') or t.get('source_ref') or '')[:60]
    badge_text = _due_text(t)
    src_raw = t.get('source', '')
    src_label = SOURCE_LABEL.get(src_raw, src_raw)
    src_ref = t.get('source_ref', '') or ''
    source_text = src_label + (' · ' + src_ref if src_ref else '')
    details = t.get('details') or {}
    next_text = details.get('next_action', '') or ''  # details key from data
    if next_text == '—':
        next_text = ''

    dashboard_link = ''
    if cid:
        dashboard_link = (
            '<a class="task-go" href="dashboard_' + cid + '.html" '
            'title="' + _t('Dashboard') + '" onclick="event.stopPropagation()">→</a>'
        )

    # Full track from mental_model to enrich priority/status/blocked_by/labels/comments/type_specific
    full_track = None
    if mm_index is not None:
        full_track = mm_index.get((cid, track_id)) or mm_index.get(('', track_id))

    # Card from t (lightweight task) + source override
    t_for_attrs = dict(t)
    t_for_attrs['source'] = src_label
    t_for_attrs['badge'] = badge_text
    t_for_attrs['track_id'] = t.get('source_ref') or t_for_attrs.get('id')

    data_attrs = build_track_data_attrs(
        t_for_attrs, _esca,
        today=TODAY,
        mm_track=full_track,
        track_type_for=_track_type_for,
    )

    next_inline_html = ''
    if next_text and t.get('group') == 'hot':
        next_inline_html = ('<div class="task-next-inline">→ '
            + _esc(_translate_tech_terms(next_text[:80])) + '</div>')

    return (
        '<div class="task-item track-card-clickable"' + data_attrs + '>'
        '<div class="task-row">'
        '<div class="task-body">'
        '<span class="task-client">' + _esc(client_name) + '</span>'
        '<span class="task-what">' + what + '</span>'
        + next_inline_html +
        '</div>'
        '<div class="task-meta">' + pill_html + due_html + '</div>'
        '<div class="task-actions">' + dashboard_link + '</div>'
        '</div>'
        '</div>'
    )


def _render_group(group_key, title, icon, color_cls, tasks, limit=None, mm_index=None):
    """One group block. If a limit is set and there are more tasks, the rest are hidden under details."""
    if not tasks:
        return (
            '<section class="group ' + color_cls + '">'
            '<div class="group-head">'
            '<span class="group-icon">' + icon + '</span>'
            '<h3>' + title + '</h3>'
            '<span class="group-count">0</span>'
            '</div>'
            '<div class="group-empty">' + t('— empty —') + '</div>'
            '</section>'
        )
    if limit and len(tasks) > limit:
        visible_html = ''.join(_render_task_row(t, mm_index) for t in tasks[:limit])
        hidden_html = ''.join(_render_task_row(t, mm_index) for t in tasks[limit:])
        hidden_n = len(tasks) - limit
        details_html = (
            '<details class="group-more-details">'
            '<summary>' + t('Show {} more').format(hidden_n) + ' ▾</summary>'
            + hidden_html +
            '</details>'
        )
        body_html = visible_html + details_html
    else:
        body_html = ''.join(_render_task_row(t, mm_index) for t in tasks)
    return (
        '<section class="group ' + color_cls + '">'
        '<div class="group-head">'
        '<span class="group-icon">' + icon + '</span>'
        '<h3>' + title + '</h3>'
        '<span class="group-count">' + str(len(tasks)) + '</span>'
        '</div>'
        + body_html +
        '</section>'
    )


def render_plan_today():
    """Main page function."""
    groups = aggregate_tasks(TODAY)
    # Index of mental_model tracks to enrich the task objects
    try:
        from _mental_model import load_mental_models as _lmm
        mm_index = build_mm_tracks_index(_lmm())
    except Exception:
        mm_index = {}

    n_hot = len(groups['hot'])
    n_total = len(groups['all'])

    head = render_header()
    title = t('Plan — Today')

    # Group blocks — the "work waves" view by horizon (a VIEW, no writes to state)
    assistant_card = render_assistant_rec_card(groups)
    blocks_html = render_waves_flat(
        groups['all'], lambda t: _render_task_row(t, mm_index), _esc
    )

    _hc = horizon_counts(groups['all'])
    summary = (
        t('{} tasks').format(n_total) + ' · '
        + (f'<span class="sm sm-red">' + t('{} in the next 7 days').format(_hc["near"]) + '</span> · ' if _hc["near"] else '')
        + '<span class="sm">' + t('{} planned').format(_hc["soon"]) + '</span> · '
        + '<span class="sm">' + t('{} in backlog').format(_hc["backlog"]) + '</span>'
    )

    extra_css = (
        '.page-title{font-size:19px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.03em;margin:0 0 6px}'
        '.plan-summary{font-size:16px;color:var(--text-secondary);margin:0 0 var(--space-md)}'
        '.sm{font-weight:500}.sm-red{color:var(--accent-red)}'
        '.group{background:var(--bg-card);border:1px solid var(--border);'
        'border-radius:var(--radius-card);padding:0;margin-bottom:var(--space-md);'
        'border-left-width:3px}'
        '.group.g-red{border-left-color:var(--accent-red)}'
        '.group.g-amber{border-left-color:var(--accent-yellow)}'
        '.group.g-blue{border-left-color:var(--accent-blue)}'
        '.group.g-grey{border-left-color:var(--border)}'
        '.group-head{display:flex;align-items:center;gap:var(--space-sm);'
        'padding:12px var(--space-md);border-bottom:1px solid var(--border);'
        'background:var(--bg-page);border-radius:0 var(--radius-card) 0 0}'
        '.group-head h3{font-size:17px;font-weight:600;margin:0;flex:1}'
        '.group-icon{font-size:18px}'
        '.group-count{font-size:14px;color:var(--text-secondary);padding:2px 10px;'
        'background:var(--bg-card);border-radius:10px;border:1px solid var(--border);font-weight:500}'
        '.group-empty{padding:var(--space-md);text-align:center;color:var(--text-muted);'
        'font-size:15px}'
        '.group-more{padding:8px var(--space-md);text-align:center;color:var(--text-muted);'
        'font-size:14px;border-top:1px dashed var(--border)}'
        '.task-item{border-bottom:1px solid var(--border);cursor:pointer;'
        'transition:background var(--transition)}'
        '.task-item:last-child{border-bottom:none}'
        '.task-item:hover{background:var(--bg-page)}'
        '.task-row{display:grid;grid-template-columns:1fr auto auto;gap:var(--space-md);'
        'align-items:center;padding:12px var(--space-md);font-size:16px;line-height:1.5}'
        '.task-body{min-width:0;overflow:hidden}'
        '.task-client{font-size:14px;color:var(--text-secondary);margin-right:8px;'
        'white-space:nowrap;font-weight:500}'
        '.task-what{color:var(--text-primary);font-size:16px;line-height:1.5}'
        '.task-meta{display:flex;gap:8px;align-items:center;font-size:14px;flex-shrink:0}'
        '.pill{font-size:15px;padding:2px 8px;border-radius:10px;font-weight:600;'
        'border:1px solid transparent;white-space:nowrap;letter-spacing:.02em}'
        '.pill-team{background:var(--bg-page);color:var(--text-secondary);'
        'border-color:var(--border)}'
        '.pill-direct{background:#E6F1FB;color:#0C447C;border-color:#B5D4F4}'
        '.pill-ausn{background:#FAEEDA;color:#633806;border-color:#FAC775}'
        '.pill-sys{background:#EEEDFE;color:#3C3489}'
        '.due-overdue{color:var(--accent-red);font-weight:600}'
        '.due-today{color:var(--accent-red);font-weight:600}'
        '.due-soon{color:#B8893A;font-weight:500}'
        '.due-plan{color:var(--text-secondary)}'
        '.task-actions{display:flex;gap:4px;align-items:center;flex-shrink:0}'
        '.task-go{display:inline-flex;align-items:center;justify-content:center;'
        'width:32px;height:32px;font-size:16px;border:1px solid var(--border);'
        'border-radius:var(--radius-btn);text-decoration:none;color:var(--accent-blue);'
        'background:var(--bg-page)}'
        '.task-go:hover{border-color:var(--accent-blue);background:var(--bg-card)}'
        '.group-more-details{border-top:1px dashed var(--border)}'
        '.group-more-details summary{padding:10px var(--space-md);cursor:pointer;'
        'font-size:15px;color:var(--accent-blue);background:var(--bg-page);'
        'list-style:none;text-align:center;font-weight:500}'
        '.group-more-details summary::-webkit-details-marker{display:none}'
        '.group-more-details summary:hover{background:var(--bg-card);color:var(--accent-blue)}'
        '.group-more-details[open] summary{border-bottom:1px solid var(--border)}'
    )

    return (
        '<!DOCTYPE html>\n<html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMiAzMiI+PGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTUuNSIgZmlsbD0iIzFGNEU3OSIvPjxjaXJjbGUgY3g9IjE2IiBjeT0iMTYiIHI9IjEyLjciIGZpbGw9Im5vbmUiIHN0cm9rZT0iI0I3OTI1NyIgc3Ryb2tlLXdpZHRoPSIxLjMiLz48dGV4dCB4PSIxNiIgeT0iMTciIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJjZW50cmFsIiBmb250LWZhbWlseT0iQXJpYWwsSGVsdmV0aWNhLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZvbnQtd2VpZ2h0PSI3MDAiIGZpbGw9IiNmZmZmZmYiPtCY0JI8L3RleHQ+PC9zdmc+">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>' + _esc(title) + '</title>'
        '<style>' + DESIGN_TOKENS_CSS + OVERVIEW_SPECIFIC_CSS + OVERVIEW_V2_CSS
        + SIDEBAR_CSS + PROMPT_MODAL_CSS + DICTATE_CSS + TRACK_MODAL_CSS + MODE_SWITCH_CSS + ASSISTANT_BRIEF_CSS + extra_css + WAVES_CSS + '</style>'
        '</head><body>'
        '<div class="layout-shell">'
        + render_sidebar(
            active='plan_today',
            counts={'plan_today': n_hot}
        )
        + '<main class="main-content">'
        + head
        + assistant_card
        + '<h1 class="page-title">' + t('Plan — Today') + '</h1>'
        + '<div class="plan-summary">' + summary + '</div>'
        + MODE_SWITCH_HTML
        + blocks_html
        + '</main></div>'
                + PROMPT_MODAL_HTML + DICTATE_MODAL_HTML + TRACK_MODAL_HTML
        + NEW_JS_FRAGMENT + PROMPT_MODAL_JS + DICTATE_JS + TRACK_MODAL_JS + MODE_SWITCH_JS + WAVES_JS +
        '</body></html>'
    )


# ── Reusable per-client plan block ───────────────────────────────────────────
# The SAME plan rendering as the Plan page, scoped to one client (for the client
# card). For a single client no multi-client waves form, so it reads as the
# client's tasks grouped by horizon (Горит/Неделя/Бэклог) with clickable rows.
# Self-contained (own <style>/<script>) so callers drop it in without wiring CSS.
PLAN_BLOCK_CSS = (
    '.group{background:var(--bg-card);border:1px solid var(--border);'
    'border-radius:var(--radius-card);padding:0;margin-bottom:var(--space-md);border-left-width:3px}'
    '.group.g-red{border-left-color:var(--accent-red)}'
    '.group.g-amber{border-left-color:var(--accent-yellow)}'
    '.group.g-blue{border-left-color:var(--accent-blue)}'
    '.group.g-grey{border-left-color:var(--border)}'
    '.group-head{display:flex;align-items:center;gap:var(--space-sm);'
    'padding:10px var(--space-md);border-bottom:1px solid var(--border);background:var(--bg-page)}'
    '.group-head h3{font-size:16px;font-weight:600;margin:0;flex:1}'
    '.group-icon{font-size:17px}'
    '.group-count{font-size:13px;color:var(--text-secondary);padding:2px 9px;'
    'background:var(--bg-card);border-radius:10px;border:1px solid var(--border);font-weight:500}'
    '.task-item{border-bottom:1px solid var(--border);cursor:pointer;transition:background var(--transition)}'
    '.task-item:last-child{border-bottom:none}'
    '.task-item:hover{background:var(--bg-page)}'
    '.task-row{display:grid;grid-template-columns:1fr auto auto;gap:var(--space-md);'
    'align-items:center;padding:11px var(--space-md);font-size:15px;line-height:1.5}'
    '.task-body{min-width:0;overflow:hidden}'
    '.task-client{font-size:13px;color:var(--text-secondary);margin-right:8px;white-space:nowrap;font-weight:500}'
    '.task-what{color:var(--text-primary);font-size:15px;line-height:1.5}'
    '.task-meta{display:flex;gap:8px;align-items:center;font-size:14px;flex-shrink:0}'
    '.pill{font-size:14px;padding:2px 8px;border-radius:10px;font-weight:600;border:1px solid transparent;white-space:nowrap}'
    '.pill-team{background:var(--bg-page);color:var(--text-secondary);border-color:var(--border)}'
    '.pill-direct{background:#E6F1FB;color:#0C447C;border-color:#B5D4F4}'
    '.pill-ausn{background:#FAEEDA;color:#633806;border-color:#FAC775}'
    '.pill-sys{background:#EEEDFE;color:#3C3489}'
    '.due-overdue,.due-today{color:var(--accent-red);font-weight:600}'
    '.due-soon{color:#B8893A;font-weight:500}'
    '.due-plan{color:var(--text-secondary)}'
    '.task-actions{display:flex;gap:4px;align-items:center;flex-shrink:0}'
    '.task-go{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;'
    'font-size:15px;border:1px solid var(--border);border-radius:var(--radius-btn);'
    'text-decoration:none;color:var(--accent-blue);background:var(--bg-page)}'
)


def render_client_plan(client_id, today=None):
    """Self-contained per-client plan block (style+html+script) or '' if no tasks."""
    from _plan_waves import WAVES_CSS, WAVES_JS, render_waves_flat
    t_today = today or TODAY
    groups = aggregate_tasks(t_today)
    ctasks = [x for x in groups['all'] if x.get('client_id') == client_id]
    if not ctasks:
        return ''
    try:
        from _mental_model import load_mental_models as _lmm
        mm_index = build_mm_tracks_index(_lmm())
    except Exception:
        mm_index = {}
    html = render_waves_flat(ctasks, lambda x: _render_task_row(x, mm_index), _esc)
    if not html:
        return ''
    return '<style>' + PLAN_BLOCK_CSS + WAVES_CSS + '</style>' + html + '<script>' + WAVES_JS + '</script>'
