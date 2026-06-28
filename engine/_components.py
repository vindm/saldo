"""_components.py — shared UI components for the overview "system events" blocks.

ONE event row + ONE section, reused by every system-event list (recently updated
tracks, recently closed tracks, latest decisions). Same layout everywhere:

    [avatar] [headline + optional 2-line detail] [right: status pill · relative date]

Date is always rendered the same way and in the same place (right column).
"""
from _strings import tp, t
from _helpers import _esc, client_avatar


_PRIO_RANK = {'high': 0, 'normal': 1, 'low': 2}


def due_label(days):
    """THE due-date TEXT (relative wording), defined ONCE. Shared by the badge,
    the plan rows, and the track modal's data-track-due — so the same task shows
    the same words everywhere. None days = no deadline → muted «без срока»."""
    if days is None:
        return t('no due date')
    if days < 0:
        return t('overdue')
    if days == 0:
        return t('today')
    if days == 1:
        return t('tomorrow')
    return t('in {} d.').format(days)


def due_class(days):
    """Urgency class suffix for the shared .due-badge (none/overdue/today/soon/far)."""
    if days is None:
        return 'none'
    if days < 0:
        return 'overdue'
    if days == 0:
        return 'today'
    if days <= 7:
        return 'soon'
    return 'far'


def due_badge(days):
    """THE shared due-date badge — relative text (due_label) + urgency colour
    (due_class). Reused everywhere (hero «Сводка», plan rows, track modal).
    CSS lives in DESIGN_TOKENS_CSS (.due-badge) so it's available on every page.

    A `days` value already encodes the effective due date (due = TODAY + days), so
    we re-emit that date as `data-due`; the due ticker in NEW_JS_FRAGMENT then
    recomputes the wording + urgency colour against the live clock, keeping «через
    2 дня» honest on a tab left open across midnight. Server still renders the right
    value, so it's correct with JS off (and on a date-less badge, no data-due)."""
    txt = due_label(days)
    if not txt:
        return ''
    attr = ''
    if days is not None:
        try:
            import generate
            from datetime import timedelta
            attr = ' data-due="%s"' % (generate.TODAY + timedelta(days=int(days))).isoformat()
        except Exception:
            attr = ''
    return '<span class="due-badge due-badge-' + due_class(days) + '"' + attr + '>' + _esc(txt) + '</span>'


EVENT_CSS = (
    ".ev-list{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);overflow:hidden;padding:8px 0}"
    ".ev-row{display:flex;gap:10px;align-items:flex-start;padding:10px var(--space-md);"
    "border-bottom:1px solid var(--border)}"
    ".ev-row:last-child{border-bottom:none}"
    ".ev-hidden .ev-row:last-child{border-bottom:none}"
    ".ev-row.track-card-clickable{cursor:pointer}"
    ".ev-row.track-card-clickable:hover{background:var(--bg-page)}"
    ".ev-av{width:30px;height:30px;border-radius:50%;flex-shrink:0;display:flex;"
    "align-items:center;justify-content:center;font-size:12px;font-weight:600}"
    ".ev-body{min-width:0;flex:1}"
    ".ev-title{font-size:14px;font-weight:600;color:var(--text-primary)}"
    ".ev-title .ev-cl{color:var(--text-muted);font-weight:500}"
    ".ev-text{font-size:13px;color:var(--text-secondary);line-height:1.4;margin-top:2px;"
    "display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}"
    ".ev-right{flex-shrink:0;margin-left:10px;display:flex;flex-direction:column;"
    "align-items:flex-end;gap:4px;text-align:right}"
    ".ev-badges{display:flex;gap:6px;align-items:center;flex-wrap:wrap;justify-content:flex-end}"
    ".ev-status{font-size:12px;padding:2px 9px;border-radius:10px;white-space:nowrap;font-weight:500}"
    ".ev-when{font-size:12px;color:var(--text-muted);white-space:nowrap}"
    ".ev-more{display:block;width:100%;text-align:center;padding:9px;background:none;border:none;"
    "border-top:1px solid var(--border);color:var(--accent-blue);font-size:13px;font-weight:500;cursor:pointer;font-family:inherit}"
)


def event_row(name, head, detail='', when='', status=None, attrs='', due_html='', when_html=''):
    """One system-event row. `head`/`detail` are caller-built HTML (escape plain
    text yourself). `status` = (label, bg, fg) or None. `attrs` = data-track-*
    attributes to make the row open the track modal (empty = non-clickable).
    `due_html` = an optional pre-built .due-badge shown first in the right column
    (used by the «Требуют вас» queue, which is ordered by due date).
    `when_html` = a pre-built, already-escaped HTML «когда» (e.g. a reltime_span
    that ticks live); takes precedence over `when`, which is plain text and escaped."""
    ini, av = client_avatar(name)
    # Right column, two rows: line 1 = badges (due + status) side by side,
    # line 2 = event recency (source · date). The two pills share one line so a
    # row never grows to three stacked items.
    badges = ''
    if due_html:
        badges += due_html
    if status:
        lab, bg, fg = status
        badges += '<span class="ev-status" style="background:%s;color:%s">%s</span>' % (bg, fg, _esc(lab))
    bits = ''
    if badges:
        bits += '<div class="ev-badges">%s</div>' % badges
    if when_html:
        bits += '<div class="ev-when">%s</div>' % when_html
    elif when:
        bits += '<div class="ev-when">%s</div>' % _esc(when)
    right = '<div class="ev-right">%s</div>' % bits if bits else ''
    cls = 'ev-row track-card-clickable' if attrs else 'ev-row'
    det = '<div class="ev-text">%s</div>' % detail if detail else ''
    return ('<div class="%s"%s>' % (cls, attrs)
            + '<div class="ev-av"%s>%s</div>' % (av, _esc(ini))
            + '<div class="ev-body"><div class="ev-title">%s</div>%s</div>' % (head, det)
            + right + '</div>')


def render_event_section(title, rows, count=None, show=5):
    """Section header (big, count on the right) + a list of event rows, first
    `show` visible and the rest behind a 'show more' button. '' when empty."""
    rows = list(rows)
    if not rows:
        return ''
    cnt = count if count is not None else len(rows)
    visible = ''.join(rows[:show])
    hidden = rows[show:]
    more = ''
    if hidden:
        more = ('<div class="ev-hidden" style="display:none">' + ''.join(hidden) + '</div>'
                '<button type="button" class="ev-more" '
                'onclick="var m=this.previousElementSibling;m.style.display=\'block\';this.style.display=\'none\'">'
                + tp('show {} more', 'показать ещё {}').format(len(hidden)) + ' ↓</button>')
    return ('<div style="margin-bottom:var(--space-lg)">'
            '<div class="section-title"><h2>' + title + '</h2>'
            '<span class="count">' + str(cnt) + '</span></div>'
            '<div class="ev-list">' + visible + more + '</div></div>')


def render_empty_section(title, message):
    """Section header + a muted empty-state line (for always-on feeds like mail/news
    that should stay visible even with nothing new)."""
    return ('<div style="margin-bottom:var(--space-lg)">'
            '<div class="section-title"><h2>' + title + '</h2></div>'
            '<div class="ev-list"><div class="ev-row"><div class="ev-body">'
            '<div class="ev-text">' + _esc(message) + '</div></div></div></div></div>')
