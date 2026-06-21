"""_overview_v2.py — P3-8 (2026-05-17): overview redesign on top of mental_model.

The main overview screen takes as its first picture of the world NOT the fresh
signals but the synthesized mental_model: active client tracks + the system-wide
track, expectations (external signals), and knowledge gaps.
The old render_priorities_zone() is still available — it moved into a
collapsed "Today's signal feed" block.

The module is imported from generate.py's main loop (when generate.py runs
as __main__). This is safe — by then generate.py's module level has already
done its work.
"""
import os
import re
from datetime import date
from generate import (
    clients, TODAY, PLAN_DIR, DIARY_INBOX,
    _esc, _esca, _dt,
    load_daemon_finkoper, load_daemon_anomalies, load_daemon_mail,
    load_daemon_news, load_daemon_updates,
    _load_all_tasks, calculate_health,
    _format_date_ru,
    DESIGN_TOKENS_CSS, OVERVIEW_SPECIFIC_CSS, NEW_JS_FRAGMENT,
)
from _deadlines import collect_deadlines, collect_awaiting
from _helpers import _translate_tech_terms, relative_when, source_label
from _strings import t, tp
from _sidebar import render_sidebar, SIDEBAR_CSS
from _health import calculate_health
from _track_modal import TRACK_MODAL_CSS, TRACK_MODAL_HTML, TRACK_MODAL_JS
from _mode_switch import MODE_SWITCH_HTML, MODE_SWITCH_CSS, MODE_SWITCH_JS
from _analytics_widgets import render_all_widgets, render_widgets_split, ANALYTICS_CSS
from _overview_shared import render_header, render_mail_block, render_news_block
from _mental_model import (
    load_mental_models, _track_severity, _parse_date_in_text,
)
from _dictate import (
    DICTATE_CSS, DICTATE_MODAL_HTML, DICTATE_JS, render_dictate_button,
)
from _css import PROMPT_MODAL_CSS, PROMPT_MODAL_HTML, PROMPT_MODAL_JS
import state_ops  # source of truth for state/*.json (migration 2026-05-25)
from _brief import (render_brief_zone, brief_lead_html, BRIEF_CSS,
                    latest_history_change, ANALYSIS_CSS)
from _components import event_row, render_event_section, EVENT_CSS
OVERVIEW_V2_CSS = (
    ".focus-line{background:var(--blue-bg);color:var(--accent-blue);"
    "padding:var(--space-sm) var(--space-md);border-left:3px solid var(--accent-blue);"
    "border-radius:0 var(--radius-card) var(--radius-card) 0;margin-bottom:var(--space-lg);"
    "font-size:var(--fs-base);line-height:1.5}"
    ".focus-line .label{font-weight:500;margin-right:var(--space-xs)}"
    # UX-fix #9: section-title is large with a border + big margin-top for a visual break
    ".section-title{display:flex;justify-content:space-between;align-items:baseline;"
    "margin:48px 0 var(--space-md);padding-bottom:var(--space-sm);"
    "border-bottom:2px solid var(--border)}"
    ".section-title h2{font-size:var(--fs-h2);font-weight:600;margin:0;color:var(--text-primary)}"
    ".section-title .count{font-size:var(--fs-meta);color:var(--text-muted);font-weight:500}"
    ".tracks-grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-md);"
    "margin-bottom:var(--space-md)}"
    "@media(max-width:1000px){.tracks-grid{grid-template-columns:1fr}}"
    ".rich-badge.deadline{background:var(--bg-page);color:var(--text-muted);text-transform:uppercase;letter-spacing:.04em}"
    ".rich-badge.deadline.sev-yellow{background:var(--yellow-bg);color:#8A6730}"
    ".rich-badge.deadline.sev-red{background:var(--red-bg);color:var(--accent-red)}"
    ".rich-badge.deadline.sev-awaiting{background:var(--blue-bg);color:var(--accent-blue)}"
    ".track-deadline-badge{flex-shrink:0;font-size:15px;padding:3px 9px;border-radius:10px;text-transform:uppercase;letter-spacing:.04em;font-weight:500;background:var(--bg-page);color:var(--text-muted)}"
    ".track-deadline-badge.sev-yellow{background:var(--yellow-bg);color:#8A6730}"
    ".track-deadline-badge.sev-red{background:var(--red-bg);color:var(--accent-red)}"
    ".track-deadline-badge.sev-awaiting{background:var(--blue-bg);color:var(--accent-blue)}"
    ".track-deadline-badge.sev-grey{background:var(--bg-page);color:var(--text-muted)}"
    ".track-card{background:var(--bg-card);border-radius:var(--radius-card);"
    "padding:var(--space-sm) var(--space-md);position:relative;"
    "box-shadow:0 1px 2px rgba(0,0,0,0.03)}"
    ".track-card::before{content:\"\";position:absolute;left:0;top:12px;bottom:12px;"
    "width:3px;border-radius:0 2px 2px 0;background:var(--border)}"
    ".track-card.sev-red::before{background:var(--accent-red)}"
    ".track-card.sev-yellow::before{background:var(--accent-yellow)}"
    ".track-card.sev-grey::before{background:var(--text-muted)}"
    ".track-card.sev-awaiting::before{background:var(--accent-blue)}"
    "a.track-card{text-decoration:none;color:inherit;display:block}"
    ".track-card-clickable{cursor:pointer;transition:transform 150ms,box-shadow 150ms,background 150ms}"
    ".track-card-clickable:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,0.08);background:var(--bg-page)}"
    ".track-meta-line{display:flex;justify-content:space-between;align-items:baseline;"
    "font-size:15px;letter-spacing:.04em;text-transform:uppercase;margin-bottom:var(--space-xs)}"
    ".track-meta-line .meta-left{font-weight:500;color:var(--text-secondary)}"
    ".track-meta-line.sev-red .meta-left{color:var(--accent-red)}"
    ".track-meta-line.sev-yellow .meta-left{color:var(--accent-yellow)}"
    ".track-meta-line.sev-awaiting .meta-left{color:var(--accent-blue)}"
    ".track-badge{font-size:15px;padding:1px 8px;border-radius:10px;"
    "background:var(--bg-page);color:var(--text-secondary)}"
    ".track-badge.sev-red{background:var(--red-bg);color:var(--accent-red)}"
    ".track-badge.sev-yellow{background:var(--yellow-bg);color:var(--accent-yellow)}"
    ".track-badge.sev-awaiting{background:var(--blue-bg);color:var(--accent-blue)}"
    ".track-title{font-size:var(--fs-base);font-weight:500;margin:var(--space-xs) 0}"
    ".track-context{font-size:var(--fs-meta);color:var(--text-secondary);line-height:1.5;"
    "margin-bottom:var(--space-xs)}"
    ".track-next{font-size:var(--fs-meta);color:var(--accent-blue);margin-top:var(--space-xs)}"
    ".track-next.sev-awaiting{color:var(--text-secondary)}"
    ".track-next .arrow{margin-right:var(--space-xs)}"
    ".track-card a.open-dashboard{font-size:15px;color:var(--text-muted);float:right}"
    ".track-card a.open-dashboard:hover{color:var(--accent-blue)}"
    ".side-cols{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-md);"
    "margin-bottom:var(--space-lg)}"
    "@media(max-width:1000px){.side-cols{grid-template-columns:1fr}}"
    ".side-list{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);padding:4px 0;font-size:var(--fs-meta)}"
    ".side-list .row{padding:6px var(--space-md);border-bottom:1px solid var(--border)}"
    ".side-list .row:last-child{border-bottom:none}"
    ".side-list .row.two-col{display:grid;grid-template-columns:1fr auto;gap:var(--space-sm);"
    "align-items:baseline}"
    ".side-list .row .when{color:var(--text-secondary);font-size:15px}"
    ".side-list .row .when.overdue{color:var(--accent-red)}"
    ".side-list .row .client-tag{color:var(--text-muted);font-size:15px;"
    "display:block;margin-top:1px}"
    ".side-list .empty{padding:var(--space-md);text-align:center;color:var(--text-muted)}"
    ".clients-group{margin-bottom:var(--space-lg)}"
    ".clients-group-head{display:flex;align-items:center;gap:var(--space-sm);"
    "margin:var(--space-md) 0 var(--space-sm)}"
    ".clients-group-head h3{margin:0;font-size:16px;font-weight:600;color:var(--text-primary);"
    "text-transform:capitalize}"
    ".clients-group-count{font-size:13px;color:var(--text-secondary);padding:1px 8px;"
    "background:var(--bg-page);border-radius:10px}"
    ".clients-grid-compact{display:grid;grid-template-columns:repeat(3,1fr);"
    "gap:var(--space-sm);margin-bottom:var(--space-sm)}"
    "@media(max-width:1000px){.clients-grid-compact{grid-template-columns:repeat(2,1fr)}}"
    ".client-card-compact{background:var(--bg-card);border:1px solid var(--border);"
    "border-left-width:3px;border-radius:0 var(--radius-card) var(--radius-card) 0;"
    "padding:var(--space-sm) var(--space-md);"
    "transition:transform var(--transition),box-shadow var(--transition)}"
    ".client-card-compact:hover{transform:translateY(-1px);box-shadow:0 2px 8px rgba(0,0,0,0.04)}"
    ".client-card-compact.health-red{border-left-color:var(--accent-red)}"
    ".client-card-compact.health-yellow{border-left-color:var(--accent-yellow)}"
    ".client-card-compact.health-green{border-left-color:var(--accent-green)}"
    ".client-card-compact.health-grey{border-left-color:var(--border)}"
    ".client-card-compact h3{font-size:15px;font-weight:500;margin:0 0 var(--space-xs)}"
    ".client-card-compact .meta{font-size:15px;color:var(--text-secondary);"
    "display:flex;gap:var(--space-sm);flex-wrap:wrap}"
    ".client-card-compact a{display:block;margin-top:var(--space-xs);font-size:15px;"
    "color:var(--accent-blue)}"
    ".collapse-band{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);margin-bottom:var(--space-md)}"
    ".collapse-band summary{padding:var(--space-sm) var(--space-md);cursor:pointer;"
    "font-size:var(--fs-base);font-weight:500;list-style:none;"
    "display:flex;justify-content:space-between;align-items:center}"
    ".collapse-band summary::-webkit-details-marker{display:none}"
    ".collapse-band summary .hint{font-size:var(--fs-meta);color:var(--text-muted);font-weight:400}"
    ".collapse-band summary::after{content:'\\25BC';color:var(--text-muted);font-size:15px}"
    ".collapse-band[open] summary::after{content:'\\25B2'}"
    ".collapse-band .inner{padding:0 var(--space-md) var(--space-md)}"
    ".card-actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:var(--space-xs)}"".card-actions.card-nav{margin-top:var(--space-xs);padding-top:var(--space-xs);border-top:1px dashed var(--border)}"
    ".btn-mini{font-size:15px;padding:3px 9px;border:1px solid var(--border);"
    "background:var(--bg-page);color:var(--text-primary);border-radius:var(--radius-btn);"
    "cursor:pointer;font-family:inherit;transition:all var(--transition)}"
    ".btn-mini:hover{border-color:var(--accent-blue);color:var(--accent-blue);"
    "background:var(--bg-card)}"
    ".side-list .row.with-action{display:flex;justify-content:space-between;gap:var(--space-sm);"
    "align-items:flex-start}"
    ".side-list .row .row-content{flex:1;min-width:0}"
    ".side-list .row .row-actions{flex-shrink:0;display:flex;gap:4px}"
    # .prompt-modal* CSS -> PROMPT_MODAL_CSS in _css.py, added to <style> separately (2026-05-24)
    ".client-card-compact h3{display:flex !important;align-items:center;gap:6px}"
    ".client-card-compact h3 .name{flex:1;min-width:0}"
    ".badge{font-size:14px;padding:1px 6px;border-radius:8px;font-weight:500;border:1px solid var(--border);white-space:nowrap;flex-shrink:0;line-height:1.4}"
    ".badge-team{background:var(--bg-page);color:var(--text-secondary)}"
    ".badge-direct{background:#E6F1FB;color:#0C447C;border-color:#B5D4F4}"
    ".badge-ausn{background:#FAEEDA;color:#633806;border-color:#FAC775}"
    ".track-filter{display:inline-flex;gap:2px;padding:3px;background:var(--bg-page);border:1px solid var(--border);border-radius:8px;margin:var(--space-md) 0;align-items:center}"
    ".track-filter button{font-size:15px;padding:5px 12px;border:0;background:transparent;color:var(--text-secondary);cursor:pointer;border-radius:6px;font-family:inherit;font-weight:500;transition:all 120ms}"
    ".track-filter button:hover{color:var(--text-primary)}"
    ".track-filter button.active{background:var(--bg-card);color:var(--text-primary);box-shadow:0 1px 2px rgba(0,0,0,0.06),0 0 0 0.5px rgba(0,0,0,0.04)}"
    ".track-filter .filter-spacer{margin-left:var(--space-sm);font-size:14px;color:var(--text-muted);font-style:italic}"
)


def render_focus_line(mm, daemon_anomalies=None):
    today = TODAY
    chunks = []
    soon_red = []
    soon_yellow = []
    awaiting_long = []
    for tr in mm.get('tracks', []) or []:
        if tr.get('zone', 'client_work') == 'system_internal':
            continue
        sev, badge = _track_severity(tr, today)
        if sev == 'red' and tr.get('status') == 'active':
            soon_red.append((badge, tr))
        elif sev == 'yellow' and tr.get('status') == 'active':
            soon_yellow.append((badge, tr))
        elif sev == 'awaiting' and tr.get('status') == 'awaiting_external':
            awaiting_long.append(tr)
    if soon_red:
        n = len(soon_red)
        first = soon_red[0][1]
        first_title = first.get('title', '')[:60]
        client = first.get('client_name') or t('general')
        chunks.append(t("urgent tracks: {} (nearest — {}: {})").format(n, client, _esc(_translate_tech_terms(first_title))))
    if soon_yellow:
        chunks.append(t("{} more in the week zone").format(len(soon_yellow)))
    if awaiting_long:
        chunks.append(t("{} awaiting an external signal").format(len(awaiting_long)))
    if not chunks:
        text = t('A day with no urgent tracks. A good time to tackle "what I don\'t remember" or push routine work forward.')
    else:
        text = '; '.join(chunks).capitalize() + '.'
    return (
        '<div class="focus-line">'
        '<span class="label">' + t('Focus of the day:') + '</span>'
        + text +
        '</div>'
    )


def _track_type(client_id):
    """team or direct by client_id."""
    try:
        from generate import clients
        for c in clients:
            if c.get('id') == client_id:
                return c.get('track', 'team')
    except Exception:
        pass
    return 'team'


def _tg_for_client(client_id):
    """Returns the client's tg-username by client_id (or empty)."""
    try:
        from generate import clients
        for c in clients:
            if c.get('id') == client_id:
                msg = c.get('messengers') or {}
                return msg.get('telegram') or ''
    except Exception:
        pass
    return ''


def render_track_card(tr, sev=None, badge=None, _tasks_title_cache=None):
    """Render ONE clickable track card (opens the shared track modal).
    Extracted from render_tracks_zone so other zones (recent updated / recent
    closed) reuse the exact same card + modal. sev/badge computed if omitted.
    """
    if _tasks_title_cache is None:
        _tasks_title_cache = {}
    if sev is None:
        sev, badge = _track_severity(tr)
    # UX-fix: show the client badge only if there is a REAL client name
    # (on the client dashboard it is noise — all tracks belong to that client)
    _cn_raw = tr.get('client_name')
    client_short = (_cn_raw.replace('SP ', '') if _cn_raw and 'SP ' in _cn_raw else (_cn_raw or ''))
    track_id = tr.get('track_id', '')
    title = tr.get('title', '')
    context = tr.get('context', '') or ''
    next_action = tr.get('next_action', '') or ''
    status_label_map = {
        'active': '',
        'awaiting_external': t('WAITING'),
        'blocked': t('BLOCKED'),
        'done': t('CLOSED'),
    }
    status_label = status_label_map.get(tr.get('status'), '')
    # T-1 -> Track 1 for the reader
    track_id_ru = track_id
    m_tid = re.match(r'^T-(\d+)$', track_id) if track_id else None
    if m_tid:
        track_id_ru = t('Track ') + m_tid.group(1)
    meta_left_parts = [track_id_ru] + ([client_short.upper()] if client_short else [])
    if status_label:
        meta_left_parts.append(status_label)
    meta_left = ' · '.join(p for p in meta_left_parts if p)
    dash_link = ''
    if tr.get('client_id'):
        dash_link = (
            '<a class="open-dashboard" href="dashboard_'
            + _esca(tr["client_id"]) + '.html">' + t('→ dashboard') + '</a>'
        )
    if sev == 'awaiting':
        next_html = ''
        if next_action:
            next_html = (
                '<div class="track-next sev-awaiting">'
                '<span class="arrow">⏳</span>'
                + _esc(_translate_tech_terms(next_action)) +
                '</div>'
            )
    else:
        next_html = ''
        if next_action:
            next_html = (
                '<div class="track-next">'
                '<span class="arrow">→</span>'
                + _esc(_translate_tech_terms(next_action)) +
                '</div>'
            )
    ctx_html = ''
    if context:
        ctx_html = '<div class="track-context">' + _esc(_translate_tech_terms(context)) + '</div>'
    prompt_discuss = (
        'Let\'s break down the task "' + (tr.get('title') or '') + '" for client ' +
        (tr.get('client_name') or 'general situation') + '. '
        'Open the client\'s state/*.json (source of truth) and mental_model, connect the links, propose the next step.'
    )
    actions_html = ''  # UX-fix #8: action buttons removed from cards, access via click->modal
    # Track card — a clickable <div>: clicking opens the modal with the full track map.
    # No internal buttons — actions moved into the modal.
    client_id = tr.get('client_id') or ''
    import json as _json
    ft = tr.get('_full_track') or {}
    # due date string for chip
    _ft_due_raw = ft.get('due_date') or tr.get('due_date') or ''
    _ft_due_str = ''
    if _ft_due_raw:
        try:
            from datetime import datetime as _dtt2
            _dobj = _dtt2.strptime(str(_ft_due_raw)[:10], '%Y-%m-%d').date()
            _ddelta = (_dobj - TODAY).days
            if _ddelta < 0:
                _ft_due_str = t('overdue {}d').format(-_ddelta)
            elif _ddelta == 0:
                _ft_due_str = t('today')
            elif _ddelta <= 3:
                _ft_due_str = t('in {}d · {}').format(_ddelta, _dobj.strftime('%d.%m'))
            else:
                _ft_due_str = t('{} · {}d').format(_dobj.strftime('%d.%m'), _ddelta)
        except Exception:
            _ft_due_str = str(_ft_due_raw)[:10]
    # history JSON
    _ft_history = ft.get('history') or []
    _ft_history_json = _json.dumps(_ft_history, ensure_ascii=False) if _ft_history else ''
    # details JSON
    _ft_owner = ft.get('owner') or tr.get('owner') or ''
    _ft_last_ev = ft.get('last_event') or ''
    _ft_amount = ft.get('amount')
    _ft_amount_s = ('{:,.0f}'.format(float(_ft_amount)).replace(',', ' ') + ' ₽') if _ft_amount else ''
    _ft_linked = ft.get('linked') or {}
    _ft_lparts = []
    if _ft_linked.get('finkoper_task'): _ft_lparts.append('Finkoper #' + str(_ft_linked['finkoper_task']))
    if _ft_linked.get('photos'): _ft_lparts.append(str(len(_ft_linked['photos'])) + ' photos')
    _ft_linked_s = ', '.join(_ft_lparts)
    _det = {}
    _det['Track'] = track_id_ru
    _det['Status'] = tr.get('status') or '—'
    if _ft_owner: _det['Owner'] = _ft_owner
    _det['Context'] = _translate_tech_terms(tr.get('context_full') or tr.get('context') or '')
    if _ft_last_ev: _det['Last event'] = _ft_last_ev
    if _ft_amount_s: _det['Amount'] = _ft_amount_s
    if _ft_linked_s: _det['Linked'] = _ft_linked_s
    _det['Next action'] = _translate_tech_terms(tr.get('next_action_full') or tr.get('next_action') or '')
    _details_json_s = _json.dumps(_det, ensure_ascii=False)
    _ft_source = ft.get('source') or tr.get('source') or ''
    # === v2 rich data for the Linear-style modal ===
    _task_type_raw = tr.get('task_type') or tr.get('type') or ''
    _task_type_ru_map = {
        'bank_check': '🏦 bank check',
        'kudir_posting': '📒 income-ledger posting',
        'pp_to_form': '💳 prepare payment order',
        'awaiting_external': '⏳ awaiting external',
        'client_followup': '📞 ask the client',
        'regime_question': '⚙️ regime question',
        'open_question': '❓ open question',
        'investigation': '🔍 investigation',
        'regulatory_action': '📜 regulatory',
        'regulatory_watch': '👁 regulatory watch',
        'infrastructure': '🛠 infrastructure',
        'regular_check': '🔄 routine check',
        'recovery_period': '⏪ period recovery',
        'other': '·',
    }
    _task_type_ru = _task_type_ru_map.get(_task_type_raw, _task_type_raw)
    _assignee = tr.get('owner') or tr.get('assignee') or ''
    _priority = tr.get('priority') or 'normal'
    _labels = tr.get('labels') or tr.get('anchors') or []
    _type_specific = tr.get('type_specific') or {}
    _comments = tr.get('comments') or []
    # blocked_by with titles
    _bb_titles = []
    for _bid in (tr.get('blocked_by') or []):
        _bb_titles.append({'id': _bid, 'title': _tmap.get(_bid, _bid) if '_tmap' in dir() else _bid})
    # fallback if _tmap is not in scope (on overview)
    if not _bb_titles and tr.get('blocked_by'):
        for _bid in tr.get('blocked_by'):
            _bb_titles.append({'id': _bid, 'title': _bid})
    # Modal unification (2026-05-25): use a single builder from _track_attrs.
    # This guarantees the SAME set of data-track-* attributes on overview,
    # the client dashboard (via the same render_tracks_zone), and the plan (plan_today/week/month).
    from _track_attrs import build_track_data_attrs as _build_attrs
    # take today from generate (TODAY = Bali date) with a None fallback
    try:
        import generate as _gen
        _today_for_build = getattr(_gen, 'TODAY', None)
    except Exception:
        _today_for_build = None
    # Prepare tr for the builder: add the already-computed local fields
    _tr_for_builder = dict(tr)
    _tr_for_builder['details'] = _det
    _tr_for_builder['_history'] = ft.get('history') if isinstance(ft, dict) else []
    _tr_for_builder['source'] = _ft_source
    if _ft_due_raw:
        _tr_for_builder['due_date'] = _ft_due_raw
    # 2026-05-25: do NOT pass badge_override — let the builder compute it from
    # due_date via _format_due_str. We used to pass a local 'badge' from
    # _track_severity (which could be 'routine' even with a deadline), so the
    # modal showed different things when opened from the plan vs the dashboard.
    track_data_attrs = _build_attrs(
        _tr_for_builder,
        _esca,
        today=_today_for_build,
        tg_for=_tg_for_client,
        track_type_for=_track_type,
        status_label=status_label,
        translate_fn=_translate_tech_terms,
        blocked_titles={b['id']: b['title'] for b in _bb_titles},
    )
    # v2 rich fields (Iter 1b, 2026-05-25): priority/blocked_by/comments badges
    rich_badges = []
    if tr.get('priority') == 'high':
        rich_badges.append('<span class="rich-badge prio-high" title="' + t('High priority') + '">' + t('🔥 URGENT') + '</span>')
    elif tr.get('priority') == 'low':
        rich_badges.append('<span class="rich-badge prio-low" title="' + t('Low priority') + '">' + t('not urgent') + '</span>')
    if tr.get('blocked_by'):
        _bb = tr['blocked_by']
        # Title lookup via state/tasks.json (as in risk linked_tasks)
        _cid = tr.get('client_id', '')
        if _cid and _cid not in _tasks_title_cache:
            try:
                from _loaders import load_client_state_tasks as _lcst
                _td = _lcst(_cid)
                _tasks_title_cache[_cid] = {_t.get('id'): _t.get('title', '') for _t in (_td.get('tasks', []) if _td else [])}
            except Exception:
                _tasks_title_cache[_cid] = {}
        _tmap = _tasks_title_cache.get(_cid, {})
        _titles = []
        for _bid in _bb[:2]:
            _t = _tmap.get(_bid, _bid)
            # Truncate long titles
            if len(_t) > 40:
                _t = _t[:40] + '…'
            _titles.append(_t)
        _bb_str = ', '.join(_titles) + ('…' if len(_bb) > 2 else '')
        rich_badges.append('<span class="rich-badge blocked-by" title="' + _esca(t('Blocked: {}').format(', '.join(_bb))) + '">🔒 ' + _esc(t('waiting')) + ' ' + _esc(_bb_str) + '</span>')
    if tr.get('comments') and len(tr['comments']) > 0:
        rich_badges.append('<span class="rich-badge comments" title="' + str(len(tr["comments"])) + ' comments">💬 ' + str(len(tr['comments'])) + '</span>')
    rich_html = ('<div class="rich-badges">' + ''.join(rich_badges) + '</div>') if rich_badges else ''

    # priority=high -> extra class on the card (red highlight)
    prio_class = ' track-prio-high' if tr.get('priority') == 'high' else ''

    # Deadline badge — first in the shared badge row below the title (NOT next to the title)
    # due_date takes priority: if the field is set, compute the badge from it
    # (consistent with the modal _format_due_str); the text-parsed badge from
    # _track_severity stays as a fallback when due_date is empty.
    _chip_text = _ft_due_str if _ft_due_raw else badge
    deadline_chip = ''
    if _chip_text and _chip_text != 'routine':
        deadline_chip = ('<span class="rich-badge deadline sev-' + sev + '">'
                         + _esc(_translate_tech_terms(_chip_text)) + '</span>')
    # All badges on one line: deadline + priority + blocked_by + comments
    all_badges = deadline_chip + (
        rich_html[len('<div class="rich-badges">'):-len('</div>')]
        if rich_html else ''
    )
    all_badges_html = ('<div class="rich-badges">' + all_badges + '</div>') if all_badges else ''
    return (
        '<div class="track-card track-card-clickable sev-' + sev + prio_class + '"' + track_data_attrs + '>'
        '<div class="track-title">' + _esc(_translate_tech_terms(title)) + '</div>'
        + all_badges_html + ctx_html
        + '</div>'
    )


def render_tracks_zone(mm, title=None, include_closed=False, empty_hide=False, empty_text=None):
    """Render a grid of clickable track cards (each opens the shared track modal).

    Reused for several zones: the client dashboard's "Active tracks", and the
    overview's recently-updated / recently-closed lists. Params let a caller change the heading,
    include recently-closed tracks (so an overnight auto-close is still shown for
    review), and hide the whole zone when empty.
    """
    # 'deferred' — snoozed tracks (waiting for wake_date), not shown on the dashboard
    _CLOSED_STATUSES = ('done', 'dropped', 'dismissed', 'completed', 'cancelled', 'closed', 'resolved', 'deferred')
    tracks = [
        t for t in (mm.get('tracks', []) or [])
        if t.get('zone', 'client_work') != 'system_internal'
        and (include_closed or t.get('status') not in _CLOSED_STATUSES)
    ]
    _zone_title = title or t('🎯 Active tracks')
    _tasks_title_cache = {}  # client_id -> {task_id: title} for blocked_by lookup
    if not tracks:
        if empty_hide:
            return ''
        return (
            '<div class="section-title"><h2>' + _zone_title + '</h2></div>'
            '<div class="side-list"><div class="empty">'
            + (empty_text or t('Client mental_models not found or contain no active tracks.')) +
            '</div></div>'
        )
    sev_order = {'red': 0, 'yellow': 1, 'grey': 2, 'awaiting': 3}
    enriched = []
    for tr in tracks:
        sev, badge = _track_severity(tr)
        if tr.get('status') == 'blocked':
            ord_key = 4
        elif tr.get('status') == 'done':
            ord_key = 5
        else:
            ord_key = sev_order.get(sev, 6)
        enriched.append((ord_key, sev, badge, tr))
    enriched.sort(key=lambda x: x[0])
    cards = [render_track_card(tr, sev, badge, _tasks_title_cache)
             for _, sev, badge, tr in enriched]
    active_n = sum(1 for t in tracks if t.get("status") != "done")
    count_html = (str(len(tracks)) + ' ' + t('(active {})').format(active_n)) if title is None else str(len(tracks))
    return (
        '<div class="section-title">'
        '<h2>' + _zone_title + '</h2>'
        '<span class="count">' + count_html + '</span>'
        '</div>'
        '<section class="tracks-grid">'
        + ''.join(cards) +
        '</section>'
    )


def _deadline_row_html(d):
    """One side-list row for a state-derived deadline (kind tax|task)."""
    delta = d.get('days_left', 0)
    if delta < 0:
        when = t('overdue {}d').format(-delta)
        cls = ' overdue'
    elif delta == 0:
        when = t('today')
        cls = ' overdue'
    else:
        when = d['date'].strftime('%d.%m') + ' · ' + t('in {}d').format(delta)
        cls = ''
    client_tag = ''
    if d.get('client_name'):
        client_tag = '<span class="client-tag">' + _esc(d['client_name']) + '</span>'
    return (
        '<div class="row two-col">'
        '<div>' + _esc(_translate_tech_terms(d.get('what', ''))) + client_tag + '</div>'
        '<div class="when' + cls + '">' + _esc(when) + '</div>'
        '</div>'
    )


def render_deadlines_panels(deadlines):
    """Two side-list columns built from state-aggregated deadlines:
       🔥 Urgent (overdue + today) and 📅 This week (+1..+7).
       Both exclude 'done'/'later' buckets."""
    urgent = [d for d in deadlines if d['bucket'] in ('overdue', 'today')]
    this_week = [d for d in deadlines if d['bucket'] == 'this_week']
    urgent.sort(key=lambda r: r['days_left'])
    this_week.sort(key=lambda r: r['days_left'])

    def _col(title, rows, empty_text):
        if rows:
            body = ''.join(_deadline_row_html(d) for d in rows[:12])
            if len(rows) > 12:
                body += ('<div class="row"><span class="muted">... '
                         + t('and {} more').format(len(rows) - 12) + '</span></div>')
        else:
            body = '<div class="empty">' + empty_text + '</div>'
        return (
            '<div>'
            '<div class="section-title"><h2>' + title + '</h2>'
            '<span class="count">' + str(len(rows)) + '</span></div>'
            '<div class="side-list">' + body + '</div>'
            '</div>'
        )

    return (
        '<section class="side-cols">'
        + _col(t('🔥 Urgent'), urgent, t('Nothing urgent'))
        + _col(t('📅 This week'), this_week, t('Nothing due this week'))
        + '</section>'
    )


def render_awaitings_zone(awaiting):
    """⏳ Awaiting reply — state-derived (open tasks with an awaiting task_type)."""
    aw_all = list(awaiting or [])
    if not aw_all:
        rows_html = '<div class="empty">' + t('Nothing external pending') + '</div>'
    else:
        rows = []
        for w in aw_all[:12]:
            dw = w.get('days_waiting', 0) or 0
            when = t('waiting {}d').format(dw)
            cls = ' overdue' if dw > 7 else ''
            client_tag = ''
            if w.get('client_name'):
                client_tag = '<span class="client-tag">' + _esc(w["client_name"]) + '</span>'
            prompt_remind = tp(
                'Draft a polite reminder (for my review, do not send): we are waiting for "{what}". '
                'Marker: {when}. Recipient: {who}. Tone by the age of the wait, in the practice brand voice.',
                'Составь вежливое напоминание (черновик мне на проверку, не отправляй): ждём «{what}». '
                'Маркер: {when}. Получатель: {who}. Тон — по давности ожидания, в фирменном стиле.'
            ).format(what=(w.get('what') or ''), when=when,
                     who=(w.get('client_name') or tp('from context', 'из контекста')))
            rows.append(
                '<div class="row with-action">'
                '<div class="row-content">'
                + _esc(_translate_tech_terms(w.get("what",""))) + client_tag +
                '<div class="when' + cls + '" style="margin-top:2px">' + _esc(when) + '</div>'
                '</div>'
                '<div class="row-actions">'
                '<button class="btn-mini" data-prompt="' + _esca(prompt_remind) + '" title="' + t('Remind') + '">🔔</button>'
                + render_dictate_button(
                    kind='expectation',
                    client=w.get('client_name', '') or '',
                    title=w.get('what', '') or '',
                    extra=when,
                ) +
                '</div>'
                '</div>'
            )
        rows_html = ''.join(rows)
        if len(aw_all) > 12:
            rows_html += '<div class="row"><span class="muted">... ' + t('and {} more').format(len(aw_all)-12) + '</span></div>'
    return (
        '<div>'
        '<div class="section-title"><h2>' + t('⏳ Expectations') + '</h2>'
        '<span class="count">' + str(len(aw_all)) + '</span></div>'
        '<div class="side-list">' + rows_html + '</div>'
        '</div>'
    )


def render_gaps_zone(mm):
    gaps = mm.get('gaps', []) or []
    if not gaps:
        rows_html = '<div class="empty">' + t('Mental_models say everything is clear') + '</div>'
    else:
        rows = []
        for g in gaps[:10]:
            client_tag = ''
            if g.get('client_name'):
                client_tag = '<span class="client-tag">' + _esc(g["client_name"]) + '</span>'
            _cl = (tp('Client: ', 'Клиент: ') + g['client_name'] + '. ') if g.get('client_name') else ''
            prompt_clarify = tp(
                'Help close a gap: "{text}". {cl}Propose where to find the answer, what request to draft '
                '(for my approval), and whether to ask the client or a colleague. Send nothing without my OK.',
                'Помоги закрыть пробел: «{text}». {cl}Предложи, где искать ответ, какой запрос составить '
                '(черновик на аппрув) и кого спросить — клиента или коллегу. Без моего «ок» ничего не отправляй.'
            ).format(text=(g.get('text') or ''), cl=_cl)
            rows.append(
                '<div class="row with-action">'
                '<div class="row-content">' + _esc(_translate_tech_terms(g["text"])) + client_tag + '</div>'
                '<div class="row-actions">'
                '<button class="btn-mini" data-prompt="' + _esca(prompt_clarify) + '" title="' + t('Clarify') + '">❓</button>'
                + render_dictate_button(
                    kind='knowledge gap',
                    client=g.get('client_name', '') or '',
                    title=g.get('text', '') or '',
                ) +
                '</div>'
                '</div>'
            )
        rows_html = ''.join(rows)
        if len(gaps) > 10:
            rows_html += '<div class="row"><span class="muted">... ' + t('and {} more').format(len(gaps)-10) + '</span></div>'
    return (
        '<div>'
        '<div class="section-title"><h2>' + t('❓ Awaiting clarification') + '</h2>'
        '<span class="count">' + str(len(gaps)) + '</span></div>'
        '<div class="side-list">' + rows_html + '</div>'
        '</div>'
    )


# ── Recent track activity (two overview zones: updated / closed, grouped by day) ──
# Source channels that mean "an automated collector/daemon" (vs the operator's own
# edits operator/cowork/owner/joint). Used only to float daemon-touched tracks to
# the TOP of the "updated" list in the morning — NOT to exclude the operator's edits
# (she wants to see her own changes too).
_DAEMON_SRC_CHANNELS = {
    'tg', 'telegram', 'email', 'mail', 'finkoper', 'news',
    'tbank', 'alfa', 'alfabank', 'vtb', 'bank', 'ofd',
}

# Statuses that mean a track is CLOSED (for the "recently closed" zone). 'deferred'
# is snoozed, not closed, so it is excluded from both zones.
_CLOSED_FOR_ZONE = ('done', 'completed', 'dismissed', 'cancelled', 'resolved', 'dropped', 'closed')


def _is_daemon_event(h):
    """True if this history event was written by an automated collector/daemon."""
    ch = str(h.get('source') or '').split(':', 1)[0].strip().lower()
    return ch in _DAEMON_SRC_CHANNELS


def _event_day(h):
    from datetime import datetime, date as _date
    s = str(h.get('ts') or h.get('date') or '')
    try:
        return datetime.fromisoformat(s).date()
    except (TypeError, ValueError):
        try:
            y, m, dd = s.split('T')[0].split('-')[:3]
            return _date(int(y), int(m), int(dd))
        except (ValueError, AttributeError):
            return None


def _track_latest_event_day(tr):
    """Most recent history-event date on the track (any source). None if none."""
    ft = tr.get('_full_track') or {}
    best = None
    for h in (ft.get('history') or tr.get('history') or []):
        d = _event_day(h)
        if d and (best is None or d > best):
            best = d
    return best


def _track_has_daemon_event_since(tr, cut):
    if cut is None:
        return False
    ft = tr.get('_full_track') or {}
    for h in (ft.get('history') or []):
        d = _event_day(h)
        if d and d >= cut and _is_daemon_event(h):
            return True
    return False


def _track_close_day(tr):
    """Date a track was closed: completed_at if present, else its last event day."""
    ft = tr.get('_full_track') or {}
    ca = ft.get('completed_at')
    if ca:
        d = _event_day({'date': ca})
        if d:
            return d
    return _track_latest_event_day(tr)


def _track_last_event(tr):
    """Most recent history event on the track. Tie-break by array position
    (append-only history): same-day events -> later index = newer."""
    ft = tr.get('_full_track') or {}
    hist = ft.get('history') or []
    if not hist:
        return None
    best = max(range(len(hist)),
               key=lambda i: (str(hist[i].get('ts') or hist[i].get('date') or ''), i))
    return hist[best]


# status -> (en, ru, bg, fg) for the right-corner pill
_STATUS_SPEC = {
    'active': ('active', 'активен', '#EAF3DE', '#3D6107'),
    'awaiting': ('waiting', 'ждём', '#E6F1FB', '#185FA5'),
    'awaiting_external': ('waiting', 'ждём', '#E6F1FB', '#185FA5'),
    'blocked': ('blocked', 'заблокирован', '#FCEBEB', '#9B1C1C'),
    'done': ('closed', 'закрыт', '#ECEBE6', '#5F5E5A'),
    'completed': ('closed', 'закрыт', '#ECEBE6', '#5F5E5A'),
    'closed': ('closed', 'закрыт', '#ECEBE6', '#5F5E5A'),
    'resolved': ('resolved', 'решён', '#ECEBE6', '#5F5E5A'),
    'cancelled': ('cancelled', 'отменён', '#F1EFE8', '#888780'),
    'dismissed': ('dismissed', 'снят', '#F1EFE8', '#888780'),
    'dropped': ('dropped', 'снят', '#F1EFE8', '#888780'),
    'deferred': ('deferred', 'отложен', '#F1EFE8', '#888780'),
}


def _status_spec(tr):
    st = ((tr.get('_full_track') or {}).get('status') or tr.get('status') or '').lower()
    s = _STATUS_SPEC.get(st)
    if s:
        return (tp(s[0], s[1]), s[2], s[3])
    return (st, '#F1EFE8', '#5F5E5A') if st else None


def _build_modal_attrs(tr):
    """data-track-* attributes so an event row opens the SAME track modal as a card.
    Strips data-track-type so the team/direct toggle never hides recent rows."""
    import re as _re
    from _track_attrs import build_track_data_attrs as _ba
    ft = tr.get('_full_track') or {}
    det = {
        'Track': tr.get('track_id', ''),
        'Status': tr.get('status') or ft.get('status') or '—',
        'Context': _translate_tech_terms(tr.get('context_full') or tr.get('context') or ''),
        'Next action': _translate_tech_terms(tr.get('next_action_full') or tr.get('next_action') or ''),
    }
    own = ft.get('owner') or tr.get('owner')
    if own:
        det['Owner'] = own
    trb = dict(tr)
    trb['details'] = det
    trb['_history'] = ft.get('history') if isinstance(ft, dict) else []
    trb['source'] = ft.get('source') or tr.get('source') or ''
    due = ft.get('due_date') or tr.get('due_date')
    if due:
        trb['due_date'] = due
    attrs = _ba(trb, _esca, today=TODAY, tg_for=_tg_for_client,
                track_type_for=_track_type, status_label='',
                translate_fn=_translate_tech_terms, blocked_titles={})
    return _re.sub(r'\s*data-track-type="[^"]*"', '', attrs)


def _track_event_row(tr):
    """A track rendered as the shared event row (clickable -> track modal)."""
    cn = tr.get('client_name') or ''
    cn_short = cn.replace('SP ', '') if cn else ''
    title = _esc(_translate_tech_terms(tr.get('title', '') or tr.get('track_id', '')))
    head = ('<span class="ev-cl">' + _esc(cn_short) + ' · </span>' if cn_short else '') + title
    last = _track_last_event(tr)
    detail = _esc(_translate_tech_terms((last.get('event') or '').strip())) if last else ''
    when = ''
    if last:
        when = ' · '.join(p for p in [source_label(last.get('source')),
                                      relative_when(last.get('ts') or last.get('date'), TODAY)] if p)
    return event_row(cn, head, detail, when, _status_spec(tr), _build_modal_attrs(tr))


def collect_recent_track_zones(mm, days=3):
    """Two morning event sections: (updated_html, closed_html) — same component as
    the decisions block. updated = open tracks touched within `days` (daemon-touched
    first, then newest); closed = tracks closed within `days`. 5 shown + show more."""
    from datetime import timedelta
    cut = (TODAY - timedelta(days=days - 1)) if TODAY else None
    updated, closed = [], []
    for tr in (mm.get('tracks') or []):
        if (tr.get('zone', 'client_work') or 'client_work') == 'system_internal':
            continue
        ft = tr.get('_full_track') or {}
        raw_status = (ft.get('status') or tr.get('status') or '')
        if raw_status in _CLOSED_FOR_ZONE:
            d = _track_close_day(tr)
            if d and cut and d >= cut:
                closed.append((d.isoformat(), tr))
        elif raw_status == 'deferred':
            continue
        else:
            d = _track_latest_event_day(tr)
            if d and cut and d >= cut:
                daemon = _track_has_daemon_event_since(tr, cut)
                updated.append(((1 if daemon else 0, d.isoformat()), tr))
    updated.sort(key=lambda x: x[0], reverse=True)
    closed.sort(key=lambda x: x[0], reverse=True)
    upd_rows = [_track_event_row(tr) for _, tr in updated]
    cls_rows = [_track_event_row(tr) for _, tr in closed]
    updated_html = render_event_section(tp('🔄 Recently updated', '🔄 Недавно обновили'),
                                        upd_rows[:10], count=len(upd_rows))
    closed_html = render_event_section(tp('✅ Recently closed', '✅ Недавно закрыли'),
                                       cls_rows[:10], count=len(cls_rows))
    return updated_html, closed_html


def render_clients_grid_compact(mm, deadlines, awaiting,
                                  daemon_finkoper, daemon_anomalies):
    today = TODAY
    tracks_by_client = {}
    for tr in mm.get('tracks', []) or []:
        cid = tr.get('client_id')
        if not cid:
            continue
        tracks_by_client.setdefault(cid, []).append(tr)
    # State-derived deadlines/awaiting, indexed by client for per-card lookups
    # and passed straight into calculate_health (no registry reads).
    deadlines_by_cid = {}
    for d in deadlines:
        deadlines_by_cid.setdefault(d['client_id'], []).append(d)
    from _helpers import (
        dynamic_groups, clients_in_group as _clients_in_group,
        _slugify_group, _group_label, client_group as _client_group,
    )
    cards_by_group = {}  # raw group name -> list[card_html]
    for c in clients:
        h = calculate_health(c, today=today,
                              daemon_finkoper=daemon_finkoper,
                              daemon_anomalies=daemon_anomalies,
                              deadlines=deadlines, awaiting=awaiting)
        color = h.get('color', 'grey')
        n_tracks = len(tracks_by_client.get(c['id'], []))
        # Nearest upcoming deadline (within 60d, not done) from state.
        nearest = None
        for d in deadlines_by_cid.get(c['id'], []):
            if d['bucket'] == 'done':
                continue
            dd = d['date']
            if dd < today or (dd - today).days > 60:
                continue
            if nearest is None or dd < nearest:
                nearest = dd
        key_anom = None
        # R5 filter: decisions journal (primary) + client's state/risks.json.dismissed (secondary)
        # See roadmap P4-decisions_journal_as_authority. So anomalies marked
        # as "applied"/"dismissed" don't resurface as key_anom on the card.
        # 2026-05-25: migrated from c.get('dismissed_anomalies') to state/risks.json.
        client_dismissed = state_ops.state_read(c['id'], 'risks.json').get('dismissed', []) or []
        today_iso = today.isoformat()
        for a in (daemon_anomalies or {}).get('list', []) or []:
            if a.get('client') != c['name_short']:
                continue
            if a.get('severity') != 'high':
                continue
            aid = (a.get('anomaly_id') or '').strip().strip('`').strip()
            if aid and any(
                d.get('anomaly_id') == aid
                and (not d.get('until') or d.get('until') >= today_iso)
                for d in client_dismissed
            ):
                continue  # dismissed via the client's state/risks.json.dismissed
            key_anom = (a.get('title') or '')[:30]
            break
        meta_parts = []
        if n_tracks == 1:
            meta_parts.append('🎯 ' + t('1 track'))
        else:
            meta_parts.append('🎯 ' + t('{} tracks').format(n_tracks))
        if nearest:
            meta_parts.append('📅 ' + nearest.strftime("%d.%m"))
        if key_anom:
            meta_parts.append('⚠ ' + _esc(key_anom))
        prompt_open_client = tp(
            'Open the picture for client {name}: read mental_model, the latest history entries and active '
            'tracks. Update the model with any fresh signal first. What is in focus?',
            'Открой картину по клиенту {name}: прочитай mental_model, последние записи history и активные '
            'треки. Сначала обнови модель свежими сигналами. Что в фокусе?'
        ).format(name=c["name_short"])
        group_val = _client_group(c)           # raw group label
        group_slug = _slugify_group(group_val)  # filter/DOM key
        scenario_val = c.get('scenario', '') or ''
        SCENARIO_RU = {
            'A': 'USN',
            'B': 'USN+Patent',
            'B+E': 'WB+Patent',
            'C': 'video+self-employed',
            'D': 'rental',
            'E': 'WB',
            'F': 'AUSN',
        }
        badge_cls = 'badge-ausn' if scenario_val == 'F' else 'badge-direct'
        scenario_ru = SCENARIO_RU.get(scenario_val, scenario_val)
        badge_txt = (_group_label(group_val) + ' \u00b7 ' + scenario_ru) if scenario_val else _group_label(group_val)
        cards_by_group.setdefault(group_val, []).append(
            '<div class="client-card-compact health-' + color + '" '
            'data-track="' + group_slug + '">'
            '<h3><span class="name">' + _esc(c["name_short"]) + '</span>'
            '<span class="badge ' + badge_cls + '">' + _esc(badge_txt) + '</span></h3>'
            '<div class="meta">' + ''.join('<span>' + p + '</span>' for p in meta_parts) + '</div>'
            '<div class="card-actions">'
            '<button class="btn-mini" data-prompt="' + _esca(prompt_open_client) + '">'
            + t('💬 Open in chat') + '</button>'
            + render_dictate_button(
                kind='client',
                id=c['id'],
                client=c['name_short'],
                title='general thought about the client',
                extra='health=' + color + (' · nearest deadline ' + nearest.strftime('%d.%m') if nearest else ''),
            ) +
            '</div>'
            '<div class="card-actions card-nav">'
            '<a class="btn-mini" href="dashboard_' + c["id"] + '.html" '
            'style="text-decoration:none">' + t('Dashboard →') + '</a>'
            '</div>'
            '</div>'
        )
    # One labeled subsection per group, in first-seen (dynamic) order.
    sections = []
    for g in dynamic_groups(clients):
        slug = _slugify_group(g)
        g_cards = cards_by_group.get(g, [])
        sections.append(
            '<div class="clients-group" data-group="' + slug + '">'
            '<div class="clients-group-head"><h3>' + _esc(_group_label(g))
            + '</h3><span class="clients-group-count">' + str(len(g_cards)) + '</span></div>'
            '<section class="clients-grid-compact">'
            + ''.join(g_cards) +
            '</section>'
            '</div>'
        )
    return (
        '<div class="section-title"><h2>' + t('👥 Clients') + '</h2></div>'
        + ''.join(sections)
    )


def render_overview_v2():
    # JSON-first (2026-06-19): deadlines/awaiting come from state, not registries.
    deadlines = collect_deadlines(TODAY)
    awaiting  = collect_awaiting(TODAY)
    daemon_finkoper  = load_daemon_finkoper(DIARY_INBOX, TODAY)
    daemon_anomalies = load_daemon_anomalies(DIARY_INBOX, TODAY)
    daemon_mail      = load_daemon_mail(DIARY_INBOX, TODAY)
    daemon_news      = load_daemon_news(DIARY_INBOX, TODAY)
    daemon_updates   = load_daemon_updates(DIARY_INBOX, TODAY)
    mm = load_mental_models()

    head = render_header()
    focus = render_focus_line(mm, daemon_anomalies)
    tracks = render_tracks_zone(mm)
    deadline_panels = render_deadlines_panels(deadlines)
    awaitings = render_awaitings_zone(awaiting)
    gaps = render_gaps_zone(mm)
    side = '<section class="side-cols">' + awaitings + gaps + '</section>'
    grid_compact = render_clients_grid_compact(
        mm, deadlines, awaiting,
        daemon_finkoper, daemon_anomalies,
    )

    # Group filter \u2014 one button per group present in the data (dynamic).
    from _helpers import (
        dynamic_groups as _dyn_groups, clients_in_group as _cin,
        _slugify_group as _slug, _group_label as _glabel,
    )
    n_total = len(clients)
    _filter_btns = [
        '<button class="filter-btn active" data-filter="all" type="button">'
        + t('All ') + str(n_total) + '</button>'
    ]
    _valid_filters = ['all']
    for g in _dyn_groups(clients):
        gslug = _slug(g)
        _valid_filters.append(gslug)
        _filter_btns.append(
            '<button class="filter-btn" data-filter="' + gslug + '" type="button">'
            + _esc(_glabel(g)) + ' ' + str(len(_cin(clients, g))) + '</button>'
        )
    track_filter_html = (
        '<div class="track-filter">'
        + ''.join(_filter_btns)
        + '<span class="filter-spacer">' + t('\u21b3 choice is remembered') + '</span>'
        '</div>'
    )

    mail_block = render_mail_block(daemon_mail)
    news_block = render_news_block(daemon_news)
    # Two morning zones of the SAME clickable track cards as the plan / client card,
    # mirrored on the main screen for a morning focus: recently UPDATED tracks and
    # recently CLOSED tracks, grouped by day. Includes changes from daemons AND the
    # operator (daemon-touched tracks float to the top in the morning).
    updated_zone, closed_zone = collect_recent_track_zones(mm)
    recent_link = ''
    if updated_zone or closed_zone:
        recent_link = (
            '<div style="margin:0 0 var(--space-lg);font-size:13px">'
            '<a href="changelog.html">' + tp('All state changes', 'Все изменения state') + ' →</a></div>'
        )

    # modal HTML/JS -> PROMPT_MODAL_HTML/JS from _css.py (2026-05-24)

    # Group filter JS \u2014 hides whole group subsections + individual cards.
    import json as _json
    _valid_js = _json.dumps(_valid_filters)
    track_filter_js = (
        '<script>'
        '(function(){'
        'var btns=document.querySelectorAll(".track-filter .filter-btn");'
        'if(!btns.length)return;'
        'var groups=document.querySelectorAll(".clients-group");'
        'var VALID=' + _valid_js + ';'
        'function apply(f){'
        'btns.forEach(function(b){b.classList.toggle("active",b.dataset.filter===f);});'
        'groups.forEach(function(g){'
        'var gv=g.dataset.group||"";'
        'g.style.display=(f==="all"||f===gv)?"":"none";});'
        'try{localStorage.setItem("dashboard_group_filter",f);}catch(e){}'
        '}'
        'var saved=null;'
        'try{saved=localStorage.getItem("dashboard_group_filter");}catch(e){}'
        'if(saved&&VALID.indexOf(saved)>=0)apply(saved);'
        'btns.forEach(function(b){b.addEventListener("click",function(){apply(b.dataset.filter);});});'
        '})();'
        '</script>'
    )

    # Shared "🎤 Dictate" button in the header
    global_mic = (
        '<div style="margin:0 0 var(--space-md);text-align:right">'
        + render_dictate_button(
            kind='general thought',
            title='general thought about the dashboard',
            extra='date: ' + _format_date_ru(TODAY),
        ) +
        '</div>'
    )

    # Analytics widgets (pure functions of state, always current)
    JOURNAL_PATH = os.path.join(PLAN_DIR, 'journal', 'decisions_log.md')
    _w = render_widgets_split(
        clients_data_path=None,
        journal_path=JOURNAL_PATH,
        calculate_health_func=calculate_health,
        clients=clients,
        daemon_finkoper=daemon_finkoper,
        daemon_anomalies=daemon_anomalies,
    )
    
    # Auto-close (deprecated rule-based, kept but currently does nothing)
    auto_close_widget = ''



    from _track_attrs import build_track_data_attrs as _bta
    import re as _re_brief
    def _make_attrs(item):
        _a = _bta({'id': item.get('id', ''), 'client_id': item.get('client_id', '')},
                  _esca, today=TODAY, tg_for=_tg_for_client,
                  track_type_for=_track_type, translate_fn=_translate_tech_terms)
        # strip data-track-type: the brief is a global top, it must not be hidden
        # by the Team/Direct toggle (mode-switch filters by this attribute)
        return _re_brief.sub(r'\s*data-track-type="[^"]*"', '', _a)
    # System-wide top: a deterministic, state-derived brief (no mental_model.md parsing).
    _last_change = latest_history_change(PLAN_DIR)
    questions_zone = render_brief_zone(clients, state_ops.state_read, PLAN_DIR, TODAY,
                                       fmt_date=_format_date_ru, esc=_esc, esca=_esca,
                                       make_attrs=_make_attrs, sections=('questions',))
    # "Today summary" = brief lead (agent-written if present, else deterministic over
    # the whole picture) + Top-5 embedded as a sub-section — one coherent block.
    _summary_lead = brief_lead_html(clients, state_ops.state_read, PLAN_DIR, TODAY,
                                    _format_date_ru, _esc)
    summary_block = (
        '<div class="aw-widget" style="margin-bottom:var(--space-lg)">'
        '<div class="aw-head">' + tp('🧭 Today summary', '🧭 Сводка на сегодня') + '</div>'
        + _summary_lead + _w['top5'] +
        '</div>'
    )
    title = t("Bookkeeping — ") + _format_date_ru(TODAY)
    return (
        '<!DOCTYPE html>\n<html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMiAzMiI+PGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTUuNSIgZmlsbD0iIzFGNEU3OSIvPjxjaXJjbGUgY3g9IjE2IiBjeT0iMTYiIHI9IjEyLjciIGZpbGw9Im5vbmUiIHN0cm9rZT0iI0I3OTI1NyIgc3Ryb2tlLXdpZHRoPSIxLjMiLz48dGV4dCB4PSIxNiIgeT0iMTciIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJjZW50cmFsIiBmb250LWZhbWlseT0iQXJpYWwsSGVsdmV0aWNhLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZvbnQtd2VpZ2h0PSI3MDAiIGZpbGw9IiNmZmZmZmYiPtCY0JI8L3RleHQ+PC9zdmc+">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>' + _esc(title) + '</title>'
        '<style>' + DESIGN_TOKENS_CSS + OVERVIEW_SPECIFIC_CSS + OVERVIEW_V2_CSS + PROMPT_MODAL_CSS + DICTATE_CSS + SIDEBAR_CSS + TRACK_MODAL_CSS  + ANALYTICS_CSS + BRIEF_CSS + ANALYSIS_CSS + EVENT_CSS + '</style>'
        '</head><body>'
        '<div class="layout-shell">'
        + render_sidebar(active='dashboard')
        + '<main class="main-content">'
        + head + _w['stats']
        + summary_block
        + questions_zone
        + updated_zone + closed_zone + recent_link
        + _w['activity']
        + mail_block + news_block
        + global_mic
        + '</main></div>'
        + PROMPT_MODAL_HTML
        + DICTATE_MODAL_HTML
        + TRACK_MODAL_HTML
        + NEW_JS_FRAGMENT
        + PROMPT_MODAL_JS
        + DICTATE_JS
        + TRACK_MODAL_JS
        + track_filter_js +
        '</body></html>'
    )
