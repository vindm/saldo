"""_client_dashboard_v2.py — P3-12 (2026-05-17): client dashboard built on top of mental_model.

Main renderer for the client dashboard on top of mental_model.
Structure: header -> understanding snapshot (3 columns) -> active client tracks
-> waiting items + what I do NOT remember -> key decisions history
-> collapsed feed of today's signals (legacy blocks).
"""
import os
from datetime import date, timedelta
from _helpers import _esc, _esca, _format_date_ru
from _css import (
    DESIGN_TOKENS_CSS, OVERVIEW_SPECIFIC_CSS,
    PROMPT_MODAL_CSS, PROMPT_MODAL_HTML, PROMPT_MODAL_JS,
)
from _dictate import (
    DICTATE_CSS, DICTATE_MODAL_HTML, DICTATE_JS, render_dictate_button,
)
from _mental_model import load_mental_models
from _overview_v2 import (
    OVERVIEW_V2_CSS,
    render_tracks_zone, render_awaitings_zone, render_gaps_zone,
)
from _health import calculate_health
from _sidebar import render_sidebar, SIDEBAR_CSS
from _v2_sections import render_v2_block, V2_SECTIONS_CSS
from _track_modal import TRACK_MODAL_CSS, TRACK_MODAL_HTML, TRACK_MODAL_JS
from _strings import t
_t = t  # alias: several functions use a local var named `t` (loop/dict comp)


def _md_bold(text):
    """Light markdown: **bold** -> <b>bold</b>. _esc first, then expansion."""
    import re as _re
    safe = _esc(text)
    return _re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', safe)


def render_action_buttons(kind, entity_id, entity_name, prompt_text, mic_kind='', mic_title='', mic_extra=''):
    """Unified action-button component (UX-fix #8, 2026-05-25).

    Used everywhere actions on an entity are needed (client/track/risk/future).
    Styles — unified design system .tm-btn-primary + .tm-btn-success.

    Args:
        kind: 'client' | 'task' | 'risk' | ... — for prompt logic
        entity_id, entity_name: for data-mic-* attributes
        prompt_text: what to copy on "Review" click
        mic_kind, mic_title, mic_extra: for render_dictate_button

    Returns:
        HTML string with two buttons.
    """
    discuss_btn = (
        '<button class="tm-btn tm-btn-primary" type="button" '
        'onclick="event.stopPropagation();event.preventDefault();" '
        'data-prompt="' + _esca(prompt_text) + '">'
        + _t('🔍 Review') + '</button>'
    )
    dictate_btn = render_dictate_button(
        kind=mic_kind or kind,
        id=entity_id,
        client=entity_name,
        title=mic_title or ('note on ' + kind),
        extra=mic_extra,
        btn_class='tm-btn',
    ).replace('btn-mic', 'tm-btn-success btn-mic').replace(
        '>🎤 Dictate<', '>🎤 Dictate a note<'
    )
    return discuss_btn + dictate_btn


def render_client_snapshot(snapshot):
    """Understanding snapshot: 3 columns firm / in_progress / unclear."""
    firm = snapshot.get('firm') or []
    inp = snapshot.get('in_progress') or []
    unc = snapshot.get('unclear') or []
    if not (firm or inp or unc):
        return ''

    def col(title, items, color):
        if not items:
            inner = '<div class="empty">—</div>'
        else:
            rows = ''.join('<div class="row">' + _md_bold(it) + '</div>' for it in items[:8])
            if len(items) > 8:
                rows += ('<div class="row" style="color:var(--text-muted)">'
                         '... ' + _t('and {} more').format(len(items) - 8) + '</div>')
            inner = rows
        return (
            '<div class="snapshot-col">'
            '<div class="snapshot-col-title" style="color:' + color + '">'
            + _esc(title) + '</div>'
            '<div class="snapshot-list">' + inner + '</div>'
            '</div>'
        )

    return (
        '<div class="section-title"><h2>' + _t('🧭 Understanding snapshot') + '</h2></div>'
        '<section class="snapshot-grid">'
        + col(_t('Firmly understood'), firm, 'var(--accent-green)')
        + col(_t('In progress'), inp, 'var(--accent-yellow)')
        + col(_t('Not yet clarified'), unc, 'var(--text-secondary)')
        + '</section>'
    )


def render_client_history(history):
    """Key decisions history — list from section 5 of mental_model."""
    if not history:
        return ''
    items = ''.join(
        '<div class="history-item">' + _esc(it) + '</div>'
        for it in history[:7]
    )
    return (
        '<div class="section-title"><h2>' + _t('📜 Key decisions history') + '</h2>'
        '<span class="count">' + str(len(history)) + '</span></div>'
        '<section class="history-list">' + items + '</section>'
    )


CLIENT_V2_EXTRA_CSS = (
    ".breadcrumb{font-size:var(--fs-meta);color:var(--text-muted);"
    "margin-bottom:var(--space-xs)}"
    ".breadcrumb a:hover{color:var(--accent-blue)}"
    ".client-head{display:flex;justify-content:space-between;align-items:flex-start;"
    "margin-bottom:var(--space-lg);padding-bottom:var(--space-md);"
    "border-bottom:1px solid var(--border)}"
    ".client-head h1{font-size:var(--fs-h1);font-weight:500;margin:0}"
    ".client-head .h-dot{display:inline-block;width:10px;height:10px;border-radius:50%;"
    "margin-right:var(--space-sm);vertical-align:middle}"
    ".client-head .h-dot.health-red{background:var(--accent-red)}"
    ".client-head .h-dot.health-yellow{background:var(--accent-yellow)}"
    ".client-head .h-dot.health-green{background:var(--accent-green)}"
    ".client-head .h-dot.health-grey{background:var(--border)}"
    ".client-head .meta-info{font-size:var(--fs-meta);color:var(--text-secondary);"
    "text-align:right;line-height:1.6}"
    ".snapshot-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--space-md);"
    "margin-bottom:var(--space-lg)}"
    "@media(max-width:900px){.snapshot-grid{grid-template-columns:1fr}}"
    ".snapshot-col{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);padding:var(--space-md)}"
    ".snapshot-col-title{font-size:13px;text-transform:uppercase;letter-spacing:.04em;"
    "font-weight:500;margin-bottom:var(--space-sm)}"
    ".snapshot-list .row{font-size:var(--fs-meta);color:var(--text-secondary);"
    "line-height:1.5;padding:4px 0;border-bottom:1px dashed var(--border)}"
    ".snapshot-list .row:last-child{border-bottom:none}"
    ".snapshot-list .empty{color:var(--text-muted);font-size:var(--fs-meta);"
    "text-align:center;padding:var(--space-sm)}"
    ".history-list{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);padding:var(--space-sm) 0;"
    "margin-bottom:var(--space-lg)}"
    ".history-item{font-size:var(--fs-meta);color:var(--text-secondary);line-height:1.5;"
    "padding:6px var(--space-md);border-bottom:1px solid var(--border)}"
    ".history-item:last-child{border-bottom:none}"
)


def _filter_mm_by_client(mm, client_id):
    """Returns a sub-dict of mm for a single client only.

    v2 (2026-05-25): if the client has state/tasks.json, take tracks from there
    (single source of truth for tasks). Fallback: old mm['tracks'].
    """
    base = {
        'tracks': [t for t in mm.get('tracks', []) if t.get('client_id') == client_id],
        'awaitings': [w for w in mm.get('awaitings', []) if w.get('client_id') == client_id],
        'gaps': [g for g in mm.get('gaps', []) if g.get('client_id') == client_id],
    }
    try:
        from _loaders import load_client_state_tasks, state_tasks_to_mm_format
        state_data = load_client_state_tasks(client_id)
        if state_data:
            # On the client dashboard client_name='' so track cards don't duplicate the client name
            base['tracks'] = state_tasks_to_mm_format(state_data, client_name='')['tracks']
    except Exception:
        pass  # silent fallback to mm['tracks']
    return base



def render_client_requisites(c):
    """Compact client details card from clients_data.json."""
    def row(label, value, mono=False):
        if not value or str(value).strip() in ('-', 'None', ''):
            return ''
        val_class = 'req-val mono' if mono else 'req-val'
        return (
            '<div class="req-row">'
            '<span class="req-label">' + _esc(label) + '</span>'
            '<span class="' + val_class + '">' + _esc(str(value)) + '</span>'
            '</div>'
        )

    inn = c.get('inn') or ''
    ogrnip = c.get('ogrnip') or ''
    reg_date = c.get('reg_date') or ''
    ifns = c.get('ifns') or ''
    okved = c.get('okved') or ''
    okved_name = c.get('okved_name') or ''
    addr = c.get('addr') or c.get('pill_region') or ''
    regime = c.get('regime') or ''
    phone = c.get('phone') or ''
    email = c.get('email') or ''
    tg = (c.get('messengers') or {}).get('telegram') or ''
    wa = (c.get('messengers') or {}).get('whatsapp') or ''
    bank = c.get('bank_name') or (c.get('bank_access') or {}).get('bank') or ''
    bik = c.get('bik') or ''
    acc_sys = c.get('accounting_system') or ''
    filing = c.get('filing_method') or {}
    submission = filing.get('submission') or ''
    sig = filing.get('signature_holder') or ''

    okved_full = (okved + ' — ' + okved_name) if okved and okved_name else okved

    left = (
        row(_t('INN'), inn, mono=True) +
        row(_t('OGRNIP'), ogrnip, mono=True) +
        row(_t('Reg. date'), reg_date) +
        row(_t('IFNS'), ifns) +
        row(_t('OKVED'), okved_full) +
        row(_t('Address'), addr)
    )
    right = (
        row(_t('Regime'), regime) +
        row(_t('Phone'), phone, mono=True) +
        row('Email', email) +
        row('Telegram', tg) +
        row('WhatsApp', wa) +
        row(_t('Bank'), bank) +
        row(_t('BIK'), bik, mono=True) +
        row(_t('Accounting'), acc_sys) +
        row(_t('Filing'), submission) +
        row(_t('Signature'), sig)
    )

    if not left.strip() and not right.strip():
        return ''

    return (
        '<div class="section-title"><h2>' + _t('📋 Client details') + '</h2></div>'
        '<section class="req-section">'
        '<div class="req-grid">'
        '<div class="req-col">' + left + '</div>'
        '<div class="req-col">' + right + '</div>'
        '</div>'
        '</section>'
    )


REQ_CARD_CSS = (
    ".req-card{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);padding:var(--space-md);"
    "margin:0 0 var(--space-md)}"
    ".req-card > summary{cursor:pointer;font-size:var(--fs-h2);font-weight:500;"
    "list-style:none;display:flex;align-items:center;gap:var(--space-sm);margin:0}"
    ".req-card > summary::-webkit-details-marker{display:none}"
    ".req-card > summary::before{content:\"▸\";display:inline-block;"
    "transition:transform 150ms;color:var(--text-muted)}"
    ".req-card[open] > summary::before{transform:rotate(90deg)}"
    ".req-card[open] > summary{margin-bottom:var(--space-md);"
    "padding-bottom:var(--space-sm);border-bottom:1px solid var(--border)}"
    ".req-grid{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-lg)}"
    "@media(max-width:700px){.req-grid{grid-template-columns:1fr}}"
    ".req-row{display:flex;gap:var(--space-sm);padding:5px 0;"
    "border-bottom:1px dashed var(--border);font-size:var(--fs-meta)}"
    ".req-row:last-child{border-bottom:none}"
    ".req-label{color:var(--text-muted);min-width:90px;flex-shrink:0}"
    ".req-val{color:var(--text-primary);word-break:break-all}"
    ".req-val.mono{font-family:var(--font-mono,monospace);font-size:13px;"
    "color:var(--text-secondary)}"
)





def render_client_risks(risks_data, tasks_lookup=None):
    """Section '⚠️ Client risks' — renders state/risks.json.
    Iter 9 (kind-split), 2026-06-13: only real risks are shown as cards
    (kind=risk or no kind — backward-compat for unmigrated). Open
    questions (kind=question) and onboarding/operational blockers (kind=blocker) are already
    visible in the tracks zone — they are not duplicated as cards here, but summarized in a footer line.
    Cards are collapsed: severity+title+next step visible; details under <details>.
    R11: green not shown. R12: resolved block removed.
    """
    if not risks_data:
        return ''
    risks = risks_data.get('risks') or []
    if not risks:
        return ''
    active_risks = [r for r in risks if r.get('severity') != 'green']
    if not active_risks:
        return ''

    sev_order = {'red': 0, 'yellow': 1, 'grey': 3}
    _CATEGORY_RU = {
        'business': 'business',
        'business_positive': 'business',
        'client_relationship': 'client relationship',
        'regulatory': 'regulatory',
        'compliance': 'regulatory',
        'financial': 'finance',
        'operational': 'operations',
        'tax': 'taxes',
        'accounting': 'accounting',
        'data_quality': 'data gap',
        'infrastructure': 'infrastructure',
        'client_behavior': 'client behavior',
    }

    def _kind(r):
        k = r.get('kind')
        return k if k in ('risk', 'question', 'blocker') else 'risk'

    real_risks = [r for r in active_risks if _kind(r) == 'risk']
    questions = [r for r in active_risks if _kind(r) == 'question']
    blockers = [r for r in active_risks if _kind(r) == 'blocker']

    cards = []
    for r in sorted(real_risks, key=lambda x: sev_order.get(x.get('severity', 'grey'), 9)):
        sev = r.get('severity', 'grey')
        title = r.get('title', '')
        desc = r.get('description', '')
        next_action = r.get('next_action') or ''
        linked_tasks = r.get('linked_tasks') or []
        linked_law = r.get('linked_law') or ''

        meta_bits = []
        if r.get('category'):
            meta_bits.append(_CATEGORY_RU.get(r['category'], r['category']))
        if r.get('since'):
            meta_bits.append('since ' + r['since'])
        meta = ' · '.join(meta_bits)

        summ_next = ('<span class="risk-next-inline">→ ' + _esc(next_action) + '</span>') if next_action else ''
        summary = (
            '<summary class="risk-summary">'
            '<span class="risk-title">' + _esc(title) + '</span>'
            + summ_next
            + '</summary>'
        )

        body_parts = []
        if meta:
            body_parts.append('<div class="risk-meta">' + _esc(meta) + '</div>')
        if desc:
            body_parts.append('<div class="risk-desc">' + _esc(desc) + '</div>')
        if linked_tasks:
            _lt_parts = []
            for _lt_id in linked_tasks[:3]:
                _lt_title = (tasks_lookup or {}).get(_lt_id, _lt_id) or _lt_id
                _lt_parts.append(_lt_title)
            body_parts.append(
                '<div class="risk-linked-tasks">🔗 linked: '
                + ', '.join(_esc(t) for t in _lt_parts)
                + ('…' if len(linked_tasks) > 3 else '')
                + '</div>'
            )
        if linked_law:
            body_parts.append('<div class="risk-law">⚖ ' + _esc(linked_law) + '</div>')

        cards.append(
            '<details class="risk-card risk-sev-' + sev + '">'
            + summary
            + '<div class="risk-body">' + ''.join(body_parts) + '</div>'
            + '</details>'
        )

    def _plural(n, one, few, many):
        n10, n100 = n % 10, n % 100
        if n10 == 1 and n100 != 11:
            return str(n) + ' ' + one
        if 2 <= n10 <= 4 and not (12 <= n100 <= 14):
            return str(n) + ' ' + few
        return str(n) + ' ' + many

    foot_bits = []
    if questions:
        foot_bits.append(str(len(questions)) + (' open question' if len(questions) == 1 else ' open questions'))
    if blockers:
        foot_bits.append(str(len(blockers)) + (' blocker' if len(blockers) == 1 else ' blockers'))
    footer = ''
    if foot_bits:
        footer = ('<div class="risks-derived">Also for this client: '
                  + ' and '.join(foot_bits) + ' — in the «Plan / Tracks» zone.</div>')

    if not cards and not footer:
        return ''

    sev_counts = {'red': 0, 'yellow': 0}
    for r in real_risks:
        s = r.get('severity', 'grey')
        if s in sev_counts:
            sev_counts[s] += 1
    counter = ''
    if sev_counts['red']:
        counter += ' 🔴' + str(sev_counts['red'])
    if sev_counts['yellow']:
        counter += ' 🟡' + str(sev_counts['yellow'])

    grid = ('<section class="risks-grid">' + ''.join(cards) + '</section>') if cards else ''
    return (
        '<div class="section-title"><h2>' + _t('⚠️ Client risks') + '</h2>'
        '<span class="count">' + counter.strip() + '</span></div>'
        + grid + footer
    )


def render_client_financials(fin, tasks_lookup=None):
    """💰 Financial model and calendar — from state/financials.json. Iter 19b (R4/R5/R6), 2026-05-25."""
    if not fin:
        return ''
    periods = fin.get('periods') or []
    cal = fin.get('tax_calendar_2026') or []
    yp = fin.get('yearly_pace_2026') or {}
    if not (periods or cal):
        return ''

    _PERIOD_STATUS_RU = {
        'archive': 'archive',
        'archive_micro': 'archive (micro)',
        'calculated': 'calculated',
        'calculated_invoice_sent_to_client': 'invoice sent to client',
        'paid': 'paid',
        'current': 'current',
        'in_progress': 'in progress',
        'scheduled': 'scheduled',
        'pending': 'pending',
        'archive_pre_switch': 'archive (pre-switch)',
        'awaiting_extraction': 'waiting for statement',
        'calculated_paid': 'calculated, paid',
        'calculated_payment_pending_check': 'calculated, checking payment',
        'current_ausn': 'current (AUSN)',
        'last_period_serviced': 'last serviced period',
    }
    _CAL_STATUS_RU = {
        'overlapped_by_insurance': 'offset by contributions',
        'in_progress': 'in progress',
        'scheduled': 'scheduled',
        'scheduled_calc_by_fact': 'scheduled (calc by fact)',
        'paid': 'paid',
        'upcoming': 'upcoming',
        'overdue': 'overdue',
        'sent': 'sent',
        'cancelled': 'cancelled',
        'pending': 'pending',
        'done': 'done',
        'auto_passed': 'passed automatically',
        'awaiting_extraction_q1': 'waiting for Q1 statement',
        'decision_required': 'decision required',
        'payment_check_in_progress': 'checking payment',
        'presumably_paid': 'presumably paid',
        'scheduled_conditional': 'scheduled (conditional)',
        'scheduled_finalization': 'scheduled (finalization)',
    }

    def _fmt_money(v):
        if v is None:
            return '—'
        try:
            return '{:,.2f}'.format(float(v)).replace(',', ' ').replace('.00', '')
        except Exception:
            return str(v)

    pace_html = ''
    if yp:
        ea = yp.get('estimated_annual_income')
        gx = yp.get('growth_vs_prev_year_x')
        bits = []
        if ea:
            bits.append('~' + _fmt_money(ea) + ' ₽ annual')
        if gx:
            bits.append('growth ×' + str(gx))
        if bits:
            pace_html = (
                '<div class="fin-pace">📈 Pace 2026: '
                + _esc(' · '.join(bits)) + '</div>'
            )

    periods_html = ''
    if periods:
        rows = []
        for p in periods:
            per = p.get('period', '')
            inc = _fmt_money(p.get('income_usn'))
            est = ' (est.)' if p.get('income_usn_estimated') else ''
            taxes = p.get('taxes') or {}
            tbits = []
            if taxes.get('usn_advance') is not None:
                tbits.append('USN advance ' + str(taxes['usn_advance']))
            if taxes.get('one_pct_overage'):
                tbits.append('1%=' + str(taxes['one_pct_overage']))
            if taxes.get('fixed_insurance_paid'):
                tbits.append('fixed ' + _fmt_money(taxes['fixed_insurance_paid']))
            tax_s = ' · '.join(tbits) if tbits else '—'
            status_raw = p.get('status', '')
            status_ru = _PERIOD_STATUS_RU.get(status_raw, status_raw)
            rows.append(
                '<tr><td class="fin-period">' + _esc(per) + '</td>'
                '<td class="fin-income">' + _esc(inc + ' ₽' + est) + '</td>'
                '<td class="fin-tax">' + _esc(tax_s) + '</td>'
                '<td class="fin-status">' + _esc(status_ru) + '</td></tr>'
            )
        periods_html = (
            '<div class="fin-subtitle">' + _t('📊 Periods') + '</div>'
            '<table class="fin-table">'
            '<thead><tr><th>' + _t('Period') + '</th><th>' + _t('USN income') + '</th><th>' + _t('Taxes') + '</th><th>' + _t('Status') + '</th></tr></thead>'
            '<tbody>' + ''.join(rows) + '</tbody></table>'
        )

    calendar_html = ''
    if cal:
        from datetime import date
        today_iso = date.today().isoformat()
        past_rows = []
        future_rows = []
        for ev in cal:
            d = ev.get('date', '')
            amt = ev.get('amount')
            amt_est = ev.get('amount_estimated')
            if amt is not None:
                amt_s = _fmt_money(amt) + ' ₽'
            elif amt_est is not None:
                amt_s = '~' + _fmt_money(amt_est) + ' ₽ (forecast)'
            else:
                amt_s = '—'
            st_raw = ev.get('status', '')
            st_ru = _CAL_STATUS_RU.get(st_raw, st_raw)
            st_class = 'cal-st-' + ('past' if d < today_iso else 'future')
            lt = ev.get('linked_task') or ''
            if lt:
                _lt_title_v = (tasks_lookup or {}).get(lt) or ''
                if _lt_title_v:
                    lt_s = '<span class="cal-task-title">' + _esc(_lt_title_v) + '</span>'
                else:
                    lt_s = '<code>' + _esc(lt) + '</code>'
            else:
                lt_s = '—'
            row_html = (
                '<tr class="' + st_class + '"><td class="cal-date">' + _esc(d) + '</td>'
                '<td>' + _esc(ev.get('what', '')) + '</td>'
                '<td class="cal-amt">' + _esc(amt_s) + '</td>'
                '<td class="cal-st">' + _esc(st_ru) + '</td>'
                '<td class="cal-task">' + lt_s + '</td></tr>'
            )
            if d < today_iso:
                past_rows.append(row_html)
            else:
                future_rows.append(row_html)
        _cal_head = (
            '<thead><tr><th>' + _t('Date') + '</th><th>' + _t('What') + '</th><th>' + _t('Amount') + '</th>'
            '<th>' + _t('Status') + '</th><th>' + _t('Task') + '</th></tr></thead>'
        )
        future_table = (
            '<table class="fin-table fin-cal-table">' + _cal_head
            + '<tbody>' + ''.join(future_rows) + '</tbody></table>'
        ) if future_rows else ''
        past_block = ''
        if past_rows:
            past_block = (
                '<details class="cal-past"><summary>Past in 2026 ('
                + str(len(past_rows)) + ')</summary>'
                '<table class="fin-table fin-cal-table">' + _cal_head
                + '<tbody>' + ''.join(past_rows) + '</tbody></table></details>'
            )
        calendar_html = (
            '<div class="fin-subtitle">' + _t('📅 Tax calendar 2026') + '</div>'
            + future_table + past_block
        )

    return (
        '<div class="section-title"><h2>' + _t('💰 Financial model and calendar') + '</h2></div>'
        '<section class="fin-section">'
        + pace_html + periods_html + calendar_html +
        '</section>'
    )


def render_client_counterparties(cp_data):
    """🤝 Counterparties — from state/counterparties.json. Iter 21, 2026-05-25."""
    if not cp_data:
        return ''
    cps = cp_data.get('counterparties') or []
    if not cps:
        return ''

    cards = []
    for cp in cps:
        name = cp.get('name', '')
        inn = cp.get('inn') or '—'
        rel = cp.get('relation_type', '')
        rel_ru = {
            'b2b_customer_main': 'B2B (main)',
            'b2b_customer': 'B2B',
            'b2b_supplier': 'Supplier',
            'agent': 'Agent',
            'payment_aggregator': 'Acquiring',
            'sz_executor': 'Self-employed contractor',
            'self_employed_contractor': 'Self-employed contractor',
        }.get(rel, rel or '—')
        cat = cp.get('category') or ''
        cat_ru = {
            'gov_order': '🏛 gov orders',
            'marketplace': '🛒 marketplace',
            'rental': '🏠 rental',
            'it_consulting': 'IT consulting',
            'labor': 'labor/individual contractors',
            'monthly_recurring': 'monthly',
            'payment_processor': 'payment processing',
            'production_client': 'client (production)',
            'production_executor': 'executor (production)',
            'rental_aggregator': '🏠 rental (via aggregator)',
            'rental_tenant': '🏠 tenant',
            'subcontractor_ip': 'subcontractor SP',
        }.get(cat, cat)
        since = cp.get('since') or ''
        tags = cp.get('tags') or []
        notes = cp.get('notes') or ''
        linked_q = cp.get('linked_open_questions') or []
        linked_t = cp.get('linked_tasks') or []
        req = cp.get('requisites') or {}

        req_bits = []
        if req.get('bank_name'):
            req_bits.append(req['bank_name'])
        if req.get('bik'):
            req_bits.append('BIK ' + req['bik'])
        if req.get('account'):
            req_bits.append('acct …' + req['account'][-4:])
        if req.get('phone'):
            req_bits.append('tel ' + req['phone'])
        req_html = ('<div class="cp-req">' + _esc(' · '.join(req_bits)) + '</div>') if req_bits else ''

        meta_bits = [rel_ru]
        if cat_ru:
            meta_bits.append(cat_ru)
        if since:
            meta_bits.append('since ' + since)
        meta = ' · '.join(meta_bits)

        tags_html = ''
        if tags:
            tags_html = '<div class="cp-tags">' + ''.join(
                '<span class="cp-tag">' + _esc(t) + '</span>' for t in tags
            ) + '</div>'

        notes_html = ('<div class="cp-notes">' + _esc(notes) + '</div>') if notes else ''

        lq_html = ''
        if linked_q:
            lq_html = (
                '<div class="cp-linked">❓ open questions: '
                + ', '.join('<code>' + _esc(q) + '</code>' for q in linked_q)
                + '</div>'
            )
        lt_html = ''
        if linked_t:
            lt_html = (
                '<div class="cp-linked">🎯 tasks: '
                + ', '.join('<code>' + _esc(t) + '</code>' for t in linked_t)
                + '</div>'
            )

        cards.append(
            '<div class="cp-card">'
            '<div class="cp-name">' + _esc(name) + '</div>'
            '<div class="cp-meta">' + _esc(meta) + '</div>'
            '<div class="cp-inn">INN: <code>' + _esc(inn) + '</code></div>'
            + req_html + tags_html + notes_html + lq_html + lt_html
            + '</div>'
        )

    return (
        '<div class="section-title"><h2>' + _t('🤝 Counterparties') + '</h2>'
        '<span class="count">' + str(len(cps)) + '</span></div>'
        '<section class="cp-grid">' + ''.join(cards) + '</section>'
    )





def render_client_accounts(acc):
    """🏦 Accounts and registers — from state/accounts.json. v2 P2 25.05.2026.

    Supports the flat state structure (bank_name/bik/account/owner_type/etc).
    Shows ALL accounts (not only primary), including closed ones with a marker.
    Includes acquiring_channels[] and pending_corrections for kassas.
    """
    if not acc:
        return ''
    banks = acc.get('bank_accounts') or []
    foreign = acc.get('foreign_accounts') or []
    kassas = acc.get('kassas') or []
    acquiring = acc.get('acquiring_channels') or []
    bacc = acc.get('bank_access') or {}
    has_any = banks or foreign or kassas or acquiring or bacc.get('note') or bacc.get('primary_bank')
    if not has_any:
        return ''

    blocks = []

    # 💳 Bank accounts (ALL — primary + secondary + closed)
    if banks:
        rows = []
        for b in banks:
            bits = []
            bank_name = b.get('bank_name') or ''
            if bank_name:
                primary_mark = ' ⭐' if b.get('is_primary') else ''
                bits.append('<span class="acc-bank">' + _esc(str(bank_name)) + primary_mark + '</span>')
            acct = b.get('account')
            if acct:
                bits.append('<span class="acc-num">' + _esc('…' + str(acct)[-4:]) + '</span>')
            bik = b.get('bik')
            if bik:
                bits.append('<span class="acc-bik">BIK ' + _esc(str(bik)) + '</span>')
            purpose = b.get('purpose') or b.get('id', '')
            closed_at = b.get('closed_at')
            status_label = ''
            if closed_at:
                status_label = ' <span class="acc-status" style="color:#9ca3af;">closed ' + _esc(str(closed_at)) + '</span>'
            elif b.get('bik_change_pending'):
                _at = b.get('bik_change_at', '')
                status_label = ' <span class="acc-status" style="color:#dc2626;">⚠ BIK changing ' + _esc(str(_at)) + '</span>'
            rows.append(
                '<div class="acc-row">'
                + ' · '.join(bits)
                + (' <span class="acc-purpose">' + _esc(str(purpose)) + '</span>' if purpose else '')
                + status_label
                + '</div>'
            )
        blocks.append('<div class="acc-block-title">💳 Bank accounts (' + str(len(banks)) + ')</div>' + ''.join(rows))

    # 🌍 Foreign accounts
    if foreign:
        rows = []
        for f in foreign:
            bits = []
            bank = f.get('bank_name') or f.get('bank') or ''
            ctry = f.get('country') or ''
            owner = f.get('owner_type') or ''
            curr = f.get('currency') or ''
            head = (str(bank) + (' (' + str(ctry) + ')' if ctry else '')).strip()
            if head:
                bits.append('<span class="acc-bank">' + _esc(head) + '</span>')
            if curr:
                bits.append('<span class="acc-num">' + _esc(str(curr)) + '</span>')
            if owner:
                owner_ru = {'ip': 'SP account', 'individual': 'individual account', 'related_entity': 'related entity'}.get(owner, owner)
                bits.append('<span class="acc-purpose">' + _esc(str(owner_ru)) + '</span>')
            note = f.get('notes') or ''
            rows.append(
                '<div class="acc-row">' + ' · '.join(bits)
                + ('<div class="acc-note">' + _esc(str(note)) + '</div>' if note else '')
                + '</div>'
            )
        blocks.append('<div class="acc-block-title">🌍 Foreign accounts (' + str(len(foreign)) + ')</div>' + ''.join(rows))

    # 🧾 Registers and OFD (Aqsi 5 + RNM + pending_corrections if present)
    if kassas:
        rows = []
        for k in kassas:
            bits = []
            if k.get('model'):
                bits.append('<span class="acc-bank">' + _esc(str(k['model'])) + '</span>')
            if k.get('rnm'):
                bits.append('<span class="acc-num">RNM ' + _esc(str(k['rnm'])) + '</span>')
            _ofd = k.get('ofd_provider') or k.get('ofd')
            if _ofd:
                bits.append('<span class="acc-purpose">' + _esc(str(_ofd)) + '</span>')
            purpose = k.get('location_or_purpose') or k.get('purpose') or ''
            if purpose:
                bits.append('<span class="acc-purpose">' + _esc(str(purpose)) + '</span>')
            status = k.get('status', '')
            _kkt_status_ru = {
                'registering': '⚠ registering',
                'active': 'active',
                'exists_details_unknown': 'exists, details TBD',
                'archived': 'archived',
            }
            if status == 'registering':
                bits.append('<span class="acc-status" style="color:#dc2626;">⚠ registering</span>')
            elif status:
                bits.append('<span class="acc-status">' + _esc(_kkt_status_ru.get(status, status)) + '</span>')
            shifts = k.get('shifts_count_period')
            period = k.get('period')
            if shifts is not None and period:
                bits.append('<span class="acc-purpose">' + str(shifts) + ' shifts ' + _esc(str(period)) + '</span>')
            if not bits:
                bits.append('<span class="acc-bank">KKT</span>')
            row = '<div class="acc-row">' + ' · '.join(bits) + '</div>'
            _knote = k.get('notes')
            if _knote:
                row += ('<div class="acc-note" style="color:var(--text-muted);'
                        'font-size:13px;margin-top:2px;">' + _esc(str(_knote)) + '</div>')
            pc = k.get('pending_corrections')
            if pc and isinstance(pc, dict):
                amt = pc.get('total_amount')
                law = pc.get('law_violation', '')
                penalty = pc.get('potential_penalty_amount_max')
                escape = pc.get('escape_mechanism', '')
                row += ('<div class="acc-note" style="background:#fef2f2;border-left:3px solid #dc2626;padding:6px 8px;margin-top:4px;">'
                        '🔴 <b>Unrecorded revenue: ' + (str(amt) + ' ₽' if amt else '?') + '</b>'
                        + (' · ' + _esc(str(law)) if law else '')
                        + (' · penalty up to ' + str(penalty) + ' ₽' if penalty else '')
                        + ('<br>↪️ ' + _esc(str(escape)) if escape else '')
                        + '</div>')
            rows.append(row)
        blocks.append('<div class="acc-block-title">🧾 Registers and OFD (' + str(len(kassas)) + ')</div>' + ''.join(rows))

    # 💳 Acquiring channels (Client A 3 channels, Client B Prodamus+YooKassa)
    if acquiring:
        rows = []
        for a in acquiring:
            bits = []
            _prov = a.get('provider') or a.get('provider_bank')
            if _prov:
                bits.append('<span class="acc-bank">' + _esc(str(_prov)) + '</span>')
            if a.get('provider_inn'):
                bits.append('<span class="acc-num">INN ' + _esc(str(a['provider_inn'])) + '</span>')
            _pages = a.get('pages') or ([a.get('url')] if a.get('url') else [])
            for _pg in _pages:
                if _pg:
                    bits.append('<span class="acc-purpose">' + _esc(str(_pg)) + '</span>')
            role = a.get('agent_role') or ''
            if role:
                _role_ru = {
                    'acquirer': 'acquirer',
                    'payment_gateway': 'payment gateway',
                    'payment_saas': 'payment service',
                }.get(role, role)
                bits.append('<span class="acc-purpose">' + _esc(str(_role_ru)) + '</span>')
            since = a.get('since')
            if since:
                bits.append('<span class="acc-purpose">since ' + _esc(str(since)) + '</span>')
            status = a.get('status', '')
            if status and status != 'active':
                _astat_ru = {
                    'idle_since_connection': 'idle since connection',
                }.get(status, status)
                bits.append('<span class="acc-status">' + _esc(str(_astat_ru)) + '</span>')
            _purpose = a.get('purpose')
            if _purpose:
                bits.append('<span class="acc-purpose">' + _esc(str(_purpose)) + '</span>')
            if a.get('confirmed') is False:
                bits.append('<span class="acc-status">not confirmed</span>')
            if not bits:
                bits.append('<span class="acc-bank">Acquiring</span>')
            _arow = '<div class="acc-row">' + ' · '.join(bits) + '</div>'
            _anote = a.get('notes')
            if _anote:
                _arow += ('<div class="acc-note" style="color:var(--text-muted);'
                          'font-size:13px;margin-top:2px;">' + _esc(str(_anote)) + '</div>')
            rows.append(_arow)
        blocks.append('<div class="acc-block-title">💳 Acquiring channels (' + str(len(acquiring)) + ')</div>' + ''.join(rows))

    # 🔑 Online banking access
    if bacc.get('primary_bank') or bacc.get('access_level') or bacc.get('note'):
        bits = []
        if bacc.get('primary_bank'):
            bits.append('<span class="acc-bank">' + _esc(str(bacc['primary_bank'])) + '</span>')
        level = bacc.get('access_level')
        level_ru = {'none': 'no access', 'view_only': 'view only', 'full': 'full', 'via_partner': 'via partner'}.get(level, level)
        if level_ru:
            bits.append('<span class="acc-purpose">' + _esc(str(level_ru)) + '</span>')
        if bacc.get('is_ausn_partner'):
            bits.append('<span class="acc-purpose" style="color:#059669;">🤝 AUSN partner</span>')
        head_row = '<div class="acc-row">' + (' · '.join(bits) if bits else '') + '</div>' if bits else ''
        note = bacc.get('note') or ''
        note_html = ('<div class="acc-note">ℹ️ ' + _esc(str(note)) + '</div>') if note else ''
        blocks.append('<div class="acc-block-title">🔑 Online banking access</div>' + head_row + note_html)

    return (
        '<div class="section-title"><h2>' + _t('🏦 Accounts and registers') + '</h2></div>'
        '<section class="acc-section">'
        + ''.join(blocks) +
        '</section>'
    )


def render_client_real_estate(re_data):
    """🏠 Real estate — from state/real_estate.json. P2 25.05.2026.
    Only for clients with a populated real_estate.json (currently Client A).
    """
    if not re_data:
        return ''
    objects = re_data.get('objects') or []
    if not objects:
        return ''
    legal_basis = re_data.get('legal_basis') or {}
    summary = re_data.get('summary') or {}

    rows = []
    for o in objects:
        addr = o.get('address_short') or o.get('address_full', '')
        otype = o.get('type', '')
        otype_ru = {'non_residential': 'non-residential', 'residential': 'residential', 'land': 'land', 'commercial': 'commercial'}.get(otype, otype)
        area = o.get('area_sqm')
        cadastr = o.get('cadastr', '')
        ag = o.get('agreement') or {}
        ag_type = ag.get('type', '')
        ag_type_ru = {'direct_lease': 'direct lease', 'agent_rental': 'via agent', 'sublease': 'sublease'}.get(ag_type, ag_type)
        ag_to = ag.get('valid_to', '')
        rate = ag.get('rate_or_formula', '')
        ta = o.get('tenant_or_agent') or {}
        ta_name = ta.get('name', '')
        ta_inn = ta.get('inn', '')
        mort = o.get('mortgage')

        head_bits = []
        head_bits.append('<span class="acc-bank">' + _esc(str(addr)) + '</span>')
        if otype_ru:
            head_bits.append('<span class="acc-purpose">' + _esc(str(otype_ru)) + '</span>')
        if area:
            head_bits.append('<span class="acc-num">' + str(area) + ' m²</span>')

        deal_bits = []
        if ag_type_ru:
            deal_bits.append('<b>' + _esc(str(ag_type_ru)) + '</b>')
        if ta_name:
            deal_bits.append(_esc(str(ta_name)) + (' (INN ' + _esc(str(ta_inn)) + ')' if ta_inn else ''))
        if ag_to:
            deal_bits.append('until ' + _esc(str(ag_to)))
        if rate:
            deal_bits.append('💰 ' + _esc(str(rate)))

        mort_html = ''
        if mort and isinstance(mort, dict):
            mb = mort.get('bank', '')
            mu = mort.get('until', '')
            mort_html = '<div class="acc-note" style="color:#7c2d12;">🏦 Mortgage ' + _esc(str(mb)) + (' until ' + _esc(str(mu)) if mu else '') + '</div>'

        cadastr_html = ('<div class="acc-note" style="font-size:11px;color:#6b7280;">cadastral ' + _esc(str(cadastr)) + '</div>') if cadastr else ''

        rows.append(
            '<div class="acc-row" style="border-left:3px solid #059669;padding-left:8px;">'
            + ' · '.join(head_bits)
            + ('<div style="margin-top:2px;">' + ' · '.join(deal_bits) + '</div>' if deal_bits else '')
            + cadastr_html
            + mort_html
            + '</div>'
        )

    title_extra = ' (' + str(summary.get('total_objects')) + ')' if summary.get('total_objects') else ''

    legal_html = ''
    if legal_basis.get('marriage_contract_at'):
        legal_html = '<div class="acc-note" style="font-size:11px;color:#6b7280;margin-top:6px;">📜 Marriage contract dated ' + _esc(str(legal_basis['marriage_contract_at'])) + '</div>'

    return (
        '<div class="section-title"><h2>' + _t('🏠 Real estate') + title_extra + '</h2></div>'
        '<section class="acc-section">'
        + ''.join(rows)
        + legal_html
        + '</section>'
    )


def render_client_behavior(beh):
    """🗣 Client communication style — from state/behavior.json. UX-fix #6, 2026-05-25.
    Human-readable mapping of technical values: 2026-05-25.
    """
    if not beh:
        return ''
    comm = beh.get('communication') or {}
    channels = beh.get('channels') or {}
    if not (comm or channels):
        return ''

    # Dictionaries mapping technical values from state/behavior.json to display text
    _SPEED_RU = {
        'active_problem_solver': 'solves problems herself',
        'fast': 'fast',
        'fast_active': 'fast and active',
        'moderate_with_travel_delays': 'moderate (occasional pauses due to travel)',
        'passive': 'passive',
        'self_managing': 'self-managing',
        'slow': 'slow',
        'slow_polite': 'slow, polite',
        'slow_with_delays': 'slow, with delays',
        'technical_competent': 'technically competent',
        'variable': 'variable',
        'via_team_lead': 'via team lead',
    }
    _TONE_RU = {
        'formal_concise': 'formal, concise',
        'friendly': 'friendly',
        'friendly_curious': 'friendly, curious',
        'friendly_emoji': 'friendly, with emoji',
        'friendly_with_emoji': 'friendly, with emoji',
        'minimal': 'minimal',
        'minimal_via_team': 'minimal, via team',
        'polite': 'polite',
        'polite_thanks': 'polite, thankful',
        'polite_with_thanks': 'polite, thankful',
        'professional_active': 'professional and active',
        'professional_technical': 'professional, technical',
        'short_factual': 'short, factual',
        'via_team': 'via team',
    }
    _FORMALITY_RU = {
        'informal_ty': 'informal (ty)',
        'formal_vy': 'formal (vy)',
        'formal_team_distant': 'formal, via team',
        'neutral': 'neutral',
        'mixed': 'mixed',
    }
    _EMOJI_RU = {
        'frequent': 'frequent',
        'frequent_thanks': 'frequent (thanks)',
        'none': 'none',
        'occasional': 'occasional',
        'occasional_thank_you': 'occasional (thanks)',
        'rare': 'rare',
    }
    _CHANNEL_TYPE_RU = {
        'finkoper': 'Finkoper',
        'team_via_anastasia': 'team via assistant',
        'team_via_anastasia_and_representative': 'team via assistant and representative',
        'team_via_finkoper': 'team via Finkoper',
        'telegram': 'Telegram',
        'edo': 'EDO',
        'email': 'email',
        'phone': 'phone',
    }

    def _ru(d, v):
        return d.get(v, v) if v else v

    blocks = []

    # Channels
    primary = channels.get('primary') or {}
    secondary = channels.get('secondary') or []
    if primary or secondary:
        ch_bits = []
        if primary.get('id'):
            ptype = _ru(_CHANNEL_TYPE_RU, primary.get('type', ''))
            ch_bits.append('<span class="beh-ch-primary">📱 ' + _esc(ptype + ': ' + primary['id']) + '</span>')
        for s in secondary:
            if s.get('id'):
                stype = _ru(_CHANNEL_TYPE_RU, s.get('type', ''))
                ch_bits.append('<span class="beh-ch-secondary">' + _esc(stype + ': ' + s['id']) + '</span>')
        tz = channels.get('timezone')
        if tz:
            ch_bits.append('<span class="beh-tz">🌐 ' + _esc(tz) + '</span>')
        if ch_bits:
            blocks.append('<div class="beh-block">' + ''.join(ch_bits) + '</div>')

    # Style + speed
    style = comm.get('style') or {}
    speed = comm.get('response_speed') or {}
    parts = []
    if speed.get('level'):
        parts.append(_t('Speed:') + ' <b>' + _esc(_ru(_SPEED_RU, speed['level'])) + '</b>')
    if style.get('tone'):
        parts.append(_t('tone:') + ' ' + _esc(_ru(_TONE_RU, style['tone'])))
    if style.get('formality'):
        parts.append(_esc(_ru(_FORMALITY_RU, style['formality'])))
    if style.get('emoji_usage') and style['emoji_usage'] != 'none':
        parts.append(_t('emoji:') + ' ' + _esc(_ru(_EMOJI_RU, style['emoji_usage'])))
    if parts:
        blocks.append('<div class="beh-style">' + ' · '.join(parts) + '</div>')
    if speed.get('description'):
        blocks.append('<div class="beh-note">' + _esc(speed['description']) + '</div>')

    # Preferences
    prefs = comm.get('preferences') or {}
    likes = prefs.get('likes') or []
    dislikes = prefs.get('dislikes') or []
    asks = prefs.get('asks_for_pattern') or ''
    if likes or dislikes:
        pref_bits = []
        if likes:
            pref_bits.append('<div class="beh-likes">👍 likes: ' + _esc(', '.join(likes)) + '</div>')
        if dislikes:
            pref_bits.append('<div class="beh-dislikes">👎 dislikes: ' + _esc(', '.join(dislikes)) + '</div>')
        if asks:
            pref_bits.append('<div class="beh-asks">💭 ' + _esc(asks) + '</div>')
        blocks.append('<div class="beh-prefs">' + ''.join(pref_bits) + '</div>')

    notes_extra = beh.get('notes')
    if notes_extra:
        blocks.append('<div class="beh-note">' + _esc(notes_extra) + '</div>')

    return (
        '<div class="section-title"><h2>' + _t('🗣 Client communication style') + '</h2></div>'
        '<section class="beh-section">' + ''.join(blocks) + '</section>'
    )


def render_client_dashboard_v2(c, daemon_mail=None, daemon_anomalies=None):
    """Main function — client dashboard on top of mental_model."""
    import generate
    TODAY = generate.TODAY
    DIARY_INBOX = generate.DIARY_INBOX
    from _loaders import load_daemon_finkoper
    from _deadlines import collect_deadlines, collect_awaiting
    deadlines = collect_deadlines(TODAY)
    awaiting = collect_awaiting(TODAY)
    daemon_finkoper = load_daemon_finkoper(DIARY_INBOX, TODAY)

    mm = load_mental_models()
    # Analysis & recommendations zone — state-derived (no mental_model.md parsing).
    from _brief import render_analysis_zone, build_client_analysis_from_state, ANALYSIS_CSS as _AN_CSS
    import state_ops as _sop_an
    _an_data = build_client_analysis_from_state(c['id'], c.get('name_short'), _sop_an.state_read, TODAY)
    _an_zone = render_analysis_zone(_an_data, TODAY, last_change=None, esc=_esc, esca=_esca)
    mm_client = _filter_mm_by_client(mm, c['id'])
    # by_client bundle (snapshot firm/in_progress/unclear, history, v2 sections) — all
    # assembled from state/*.json + history.jsonl inside load_mental_models().
    by_client = (mm.get('by_client') or {}).get(c['id'], {})
    snapshot = by_client.get('snapshot', {})
    history = by_client.get('history', [])

    h = calculate_health(c, today=TODAY,
                          daemon_finkoper=daemon_finkoper,
                          daemon_anomalies=daemon_anomalies,
                          deadlines=deadlines, awaiting=awaiting)
    health = h.get('color', 'grey')

    # Header
    n_tracks = len(mm_client['tracks'])
    n_aw = len([a for a in awaiting if a.get('client_id') == c['id']])
    n_gaps = len(mm_client['gaps'])
    time_bali = getattr(generate, 'TIME_BALI', '') or ''
    time_msk = getattr(generate, 'TIME_MSK', '') or ''
    time_line = ''
    if time_bali and time_msk:
        time_line = '<br>🕐 ' + _esc(time_bali) + ' WITA · ' + _esc(time_msk) + ' MSK'
    # Breadcrumb leads to the matching client-group list, not to overview.
    from _helpers import client_group as _client_group, _slugify_group as _slug_grp, _group_label as _grp_label
    _grp = _client_group(c)
    _grp_slug = _slug_grp(_grp)
    back_url = 'clients_' + _grp_slug + '.html'
    back_label = '← All ' + _grp_label(_grp) + ' clients'
    # client tagline (UX): take business_description from state/regime if present
    _biz_desc = ''
    # P2-fix 25.05.2026: DEPARTING/foreign_entities badges + team-meta
    _extra_badges = ''
    _team_meta = ''
    try:
        from _loaders import load_client_state_regime as _lcsr, load_client_state_identity as _lci
        _r = _lcsr(c['id'])
        if _r:
            _biz_desc = _r.get('business_description') or ''
            _contour = _r.get('contour') or {}
            if _contour.get('type') == 'team':
                _leader = _contour.get('leader', '')
                _base = _contour.get('fresh_base_id', '')
                _bits = []
                if _leader:
                    _bits.append('🧑‍💼 ' + _leader)
                if _base:
                    _bits.append('1C:Fresh ' + _base)
                if _bits:
                    _team_meta = '<div class="client-team-meta" style="font-size:11px;color:#6b7280;margin-top:2px;">' + _esc(' · '.join(_bits)) + '</div>'
        _id = _lci(c['id'])
        if _id:
            _serv = _id.get('servicing_status') or {}
            _status = _serv.get('status', '')
            if _status == 'departing':
                _dep_to = _serv.get('departed_to', '')
                _extra_badges += ' <span class="badge" style="background:#fee2c2;color:#9a3412;border:1px solid #fdba74;">🚪 DEPARTING' + ((' → ' + _esc(_dep_to)) if _dep_to else '') + '</span>'
            elif _status == 'departed':
                _extra_badges += ' <span class="badge" style="background:#e5e7eb;color:#374151;border:1px solid #9ca3af;">🚪 DEPARTED</span>'
            elif _status == 'liquidating':
                _extra_badges += ' <span class="badge" style="background:#fecaca;color:#991b1b;border:1px solid #f87171;">⚠ LIQUIDATING</span>'
            elif _status == 'paused':
                _rv = _serv.get('review_date', '')
                _extra_badges += ' <span class="badge" style="background:#e0e7ff;color:#3730a3;border:1px solid #a5b4fc;">⏸ PAUSED' + ((' until ' + _esc(_rv)) if _rv else '') + '</span>'
            _fe = _id.get('foreign_entities') or []
            for _e in _fe:
                _country = _e.get('country', '')
                _st = _e.get('status', '')
                if _country and _st in ('frozen', 'active'):
                    _kik = ' ⚠CFC' if _e.get('kik_concern') else ''
                    _extra_badges += ' <span class="badge" style="background:#fef3c7;color:#92400e;border:1px solid #fcd34d;">🌍 ' + _esc(_country) + ' ' + _esc(_st) + _kik + '</span>'
    except Exception:
        pass
    head = (
        '<div class="breadcrumb">'
        '<a href="' + back_url + '">' + back_label + '</a>'
        '</div>'
        '<div class="client-head">'
        '<div><h1><span class="h-dot health-' + health + '"></span>'
        + _esc(c['name_short'])
        + (lambda: (
            ' <span class="badge ' + (
                'badge-ausn' if (c.get('scenario')=='F')
                else 'badge-direct'
            ) + '">' + _esc(
                (_grp_label(_grp) + ' \u00b7 ' + {
                    'A':'USN','B':'USN+Patent','B+E':'WB+Patent',
                    'C':'video+SE','D':'rental','E':'WB','F':'AUSN',
                }.get(c.get('scenario',''), c.get('scenario','')))
                if c.get('scenario')
                else _grp_label(_grp)
            ) + '</span>'
        ))()
        + _extra_badges
        + '</h1>'
        + _team_meta
        + (('<div class="client-tagline">' + _esc(_biz_desc) + '</div>') if _biz_desc else '')
        + '<div class="client-actions">'
        + render_action_buttons(
            kind='client',
            entity_id=c['id'],
            entity_name=c['name_short'],
            prompt_text=('Let\'s review client ' + (c.get('name_short') or '') +
                ': open their state/*.json (source of truth) and mental_model, '
                'assess active tasks and risks, suggest today\'s priorities.'),
            mic_kind='general note on client',
            mic_title='general note from the client dashboard',
            mic_extra='health=' + health,
        )
        + '</div>'
        + '</div>'
        '<div class="meta-info">'
        '<span class="meta-label">' + _t('updated') + '</span> '
        + _format_date_ru(TODAY)
        + time_line +
        '</div>'
        '</div>'
    )

    req_card = render_client_requisites(c)
    snap = render_client_snapshot(snapshot)
    # R6/R9: shared tasks_lookup for risks and financial model
    _tasks_lookup = {}
    try:
        from _loaders import load_client_state_tasks
        _t_for_lookup = load_client_state_tasks(c['id']) or {}
        _tasks_lookup = {t.get('id'): t.get('title', '') for t in (_t_for_lookup.get('tasks') or [])}
    except Exception:
        _tasks_lookup = {}
    risks_html = ''
    try:
        from _loaders import load_client_state_risks
        _r = load_client_state_risks(c['id'])
        if _r:
            risks_html = render_client_risks(_r, tasks_lookup=_tasks_lookup)
    except Exception:
        pass
    financials_html = ''
    counterparties_html = ''
    accounts_html = ''
    quick_access_html = ''
    real_estate_html = ''
    behavior_html = ''
    try:
        from _loaders import (load_client_state_financials, load_client_state_counterparties,
                              load_client_state_accounts, load_client_state_behavior)
        _f = load_client_state_financials(c['id'])
        if _f:
            financials_html = render_client_financials(_f, tasks_lookup=_tasks_lookup)
        _cp = load_client_state_counterparties(c['id'])
        if _cp:
            counterparties_html = render_client_counterparties(_cp)
        _acc = load_client_state_accounts(c['id'])
        if _acc:
            accounts_html = render_client_accounts(_acc)
            quick_access_html = render_client_quick_access(_acc)
        # P2 25.05.2026: real_estate (Client A only)
        try:
            from state_ops import state_read, state_exists
            real_estate_html = ''
            if state_exists(c['id'], 'real_estate.json'):
                _re_data = state_read(c['id'], 'real_estate.json')
                if _re_data:
                    real_estate_html = render_client_real_estate(_re_data)
        except Exception:
            real_estate_html = ''

        _beh = load_client_state_behavior(c['id'])
        if _beh:
            behavior_html = render_client_behavior(_beh)
    except Exception:
        pass
    # Client card = a per-client plan: the SAME plan rendering as the Plan page,
    # scoped to this client (horizon groups + clickable rows). Falls back to the
    # legacy tracks zone only if the client has no plan tasks.
    from _plan_today import render_client_plan
    _client_plan = render_client_plan(c['id'], TODAY)
    if _client_plan:
        tracks = ('<div class="section-title"><h2>' + _t('🎯 Active tracks') + '</h2></div>'
                  + _client_plan)
    else:
        tracks = render_tracks_zone(mm_client) if n_tracks else (
            '<div class="section-title"><h2>' + _t('🎯 Active tracks') + '</h2></div>'
            '<div class="side-list"><div class="empty">'
            + _t('Mental_model is empty or has no tracks') + '</div></div>'
        )
    awaitings = render_awaitings_zone(
        [a for a in awaiting if a.get('client_id') == c['id']]
    )
    gaps = render_gaps_zone(mm_client)
    side = '<section class="side-cols">' + awaitings + gaps + '</section>'
    hist = render_client_history(history)
    # v2 sections (Financial model, Calendar, Plan, Risks, Pattern, Links, Counterparties)
    v2_block = render_v2_block(by_client)

    # Global «🎤 Dictate» button for the client — right under the header
    global_mic = (
        '<div style="margin:0 0 var(--space-md);text-align:right">'
        + render_dictate_button(
            kind='general note on client',
            id=c['id'],
            client=c['name_short'],
            title='general note from the client dashboard',
            extra='health=' + health,
        ) +
        '</div>'
    )

    # Stage 1 sidebar: active item = team or direct based on the client's track
    sidebar_active = 'clients_' + _slug_grp(_client_group(c))
    title = c['name_short']
    return (
        '<!DOCTYPE html>\n<html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMiAzMiI+PGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTUuNSIgZmlsbD0iIzFGNEU3OSIvPjxjaXJjbGUgY3g9IjE2IiBjeT0iMTYiIHI9IjEyLjciIGZpbGw9Im5vbmUiIHN0cm9rZT0iI0I3OTI1NyIgc3Ryb2tlLXdpZHRoPSIxLjMiLz48dGV4dCB4PSIxNiIgeT0iMTciIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJjZW50cmFsIiBmb250LWZhbWlseT0iQXJpYWwsSGVsdmV0aWNhLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZvbnQtd2VpZ2h0PSI3MDAiIGZpbGw9IiNmZmZmZmYiPkJLPC90ZXh0Pjwvc3ZnPg==">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>' + _esc(title) + '</title>'
        '<style>' + DESIGN_TOKENS_CSS + OVERVIEW_SPECIFIC_CSS + OVERVIEW_V2_CSS + REQ_CARD_CSS \
        + CLIENT_V2_EXTRA_CSS + PROMPT_MODAL_CSS + DICTATE_CSS + SIDEBAR_CSS + V2_SECTIONS_CSS + TRACK_MODAL_CSS + _AN_CSS + QUICK_ACCESS_CSS + '</style>'
        '</head><body>'
        '<div class="layout-shell">'
        + render_sidebar(active=sidebar_active)
        + '<main class="main-content">'
        + head + quick_access_html + _an_zone + risks_html + tracks + req_card + accounts_html + real_estate_html + financials_html + counterparties_html + behavior_html + hist
        + '</main></div>'
        + PROMPT_MODAL_HTML + PROMPT_MODAL_JS
        + DICTATE_MODAL_HTML + DICTATE_JS + TRACK_MODAL_HTML + TRACK_MODAL_JS + QUICK_ACCESS_JS +
        '</body></html>'
    )


# ============================================================
# 🔗 Quick access (quick_access[] from state/accounts.json)
# Added by request 2026-06-14.
# ============================================================
QUICK_ACCESS_CSS = """
.qa-section{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px;margin-bottom:var(--space-lg,20px);}
.qa-tile{background:#fff;border:1px solid #e6e8ec;border-radius:12px;padding:14px;}
.qa-tile.qa-off{opacity:.5;}
.qa-head{display:flex;align-items:center;gap:10px;}
.qa-ic{width:34px;height:34px;border-radius:8px;background:#eef3fb;display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0;}
.qa-tt{line-height:1.25;min-width:0;}
.qa-name{font-size:14px;font-weight:600;color:#1F4E79;}
.qa-go{margin-left:auto;text-decoration:none;font-size:13px;border:1px solid #cdd3db;border-radius:8px;padding:6px 11px;color:#1F4E79;white-space:nowrap;}
.qa-go:hover{background:#f4f7fc;}
.qa-cred{display:flex;align-items:center;gap:8px;font-size:13px;padding-top:9px;margin-top:9px;border-top:1px solid #eef0f3;}
.qa-cred + .qa-cred{border-top:none;padding-top:0;margin-top:7px;}
.qa-lbl{color:#6b7280;min-width:50px;}
.qa-val{font-family:ui-monospace,Menlo,Consolas,monospace;color:#1f2937;overflow-wrap:anywhere;}
.qa-btn{border:1px solid #cdd3db;background:#fff;border-radius:7px;padding:3px 9px;font-size:12px;color:#374151;cursor:pointer;}
.qa-btn:hover{background:#f4f7fc;}
.qa-cp{margin-left:auto;}
.qa-rev + .qa-cp{margin-left:6px;}
.qa-note{font-size:12px;color:#6b7280;margin-top:10px;line-height:1.45;}
.qa-need{display:inline-block;font-size:11px;color:#9a6708;background:#faeeda;border-radius:6px;padding:1px 7px;margin-right:6px;}
"""

QUICK_ACCESS_JS = """
<script>
(function(){
  var DOTS='\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022\\u2022';
  document.querySelectorAll('.qa-rev').forEach(function(b){
    b.addEventListener('click',function(){
      var pw=b.parentNode.querySelector('.qa-pw');if(!pw)return;
      if(pw.dataset.shown==='1'){pw.textContent=DOTS;pw.dataset.shown='0';b.textContent='show';}
      else{pw.textContent=pw.dataset.pw;pw.dataset.shown='1';b.textContent='hide';}
    });
  });
  document.querySelectorAll('.qa-cp').forEach(function(b){
    b.addEventListener('click',function(){
      var v=b.getAttribute('data-v')||'';
      var t=document.createElement('textarea');t.value=v;document.body.appendChild(t);t.select();
      try{document.execCommand('copy');}catch(e){}document.body.removeChild(t);
      var old=b.textContent;b.textContent='\\u2713';setTimeout(function(){b.textContent=old;},900);
    });
  });
})();
</script>
"""

_QA_ICONS = {'prodamus':'💳','cloudpayments':'💳','ukassa':'💳','bank':'🏦','fns':'🏛','ofd':'🧾','finkoper':'🗂','onec':'🧮','assistant':'👤','mail':'✉️','tg':'💬'}

def render_client_quick_access(acc):
    """🔗 Quick access — links/logins/passwords to client services from accounts.quick_access[]."""
    if not acc:
        return ''
    items = acc.get('quick_access') or []
    if not items:
        return ''
    tiles = []
    for it in items:
        label = it.get('label') or it.get('service') or _t('Service')
        disabled = it.get('status') == 'disabled'
        ic = _QA_ICONS.get(it.get('service'), '🔗')
        url = it.get('url')
        go = ''
        if url and not disabled:
            go = '<a class="qa-go" href="' + _esca(str(url)) + '" target="_blank" rel="noopener">' + _t('Open ↗') + '</a>'
        head = ('<div class="qa-head"><div class="qa-ic">' + ic + '</div>'
                '<div class="qa-tt"><div class="qa-name">' + _esc(str(label)) + '</div></div>'
                + go + '</div>')
        creds = ''
        login = it.get('login')
        if login:
            creds += ('<div class="qa-cred"><span class="qa-lbl">' + _t('login') + '</span>'
                      '<span class="qa-val">' + _esc(str(login)) + '</span>'
                      '<button class="qa-btn qa-cp" data-v="' + _esca(str(login)) + '">' + _t('copy') + '</button></div>')
        pw = it.get('password')
        if pw:
            creds += ('<div class="qa-cred"><span class="qa-lbl">' + _t('password') + '</span>'
                      '<span class="qa-val qa-pw" data-pw="' + _esca(str(pw)) + '">••••••••••</span>'
                      '<button class="qa-btn qa-rev">' + _t('show') + '</button>'
                      '<button class="qa-btn qa-cp" data-v="' + _esca(str(pw)) + '">' + _t('copy') + '</button></div>')
        note = it.get('note') or ''
        need = '<span class="qa-need">' + _t('login/password needed') + '</span>' if it.get('cred_status') == 'need' else ''
        note_html = ('<div class="qa-note">' + need + _esc(str(note)) + '</div>') if (note or need) else ''
        cls = 'qa-tile qa-off' if disabled else 'qa-tile'
        tiles.append('<div class="' + cls + '">' + head + creds + note_html + '</div>')
    return (
        '<div class="section-title"><h2>' + _t('🔗 Quick access') + '</h2></div>'
        '<section class="qa-section">' + ''.join(tiles) + '</section>'
    )

