"""_changelog.py - the "Changelog" page: a field-level review of state changes.

Reads <DATA_DIR>/journal/state_audit.jsonl (written by state_ops on every state
write) and renders it grouped by ISO week, then by client. Shows WHICH fields
changed (added / removed / changed) - never the values - so an operator can
review weekly "what moved in the internal state" without opening every file.

Practice-agnostic: client display names come from the live clients_index via
generate.clients; nothing here is hardcoded.
"""
import datetime

from generate import (
    clients, TODAY,
    _esc,
    DESIGN_TOKENS_CSS, OVERVIEW_SPECIFIC_CSS,
)
from _overview_v2 import OVERVIEW_V2_CSS
from _overview_shared import render_header
from _sidebar import render_sidebar, SIDEBAR_CSS
from _css import PROMPT_MODAL_CSS, PROMPT_MODAL_HTML, PROMPT_MODAL_JS
from _strings import t
import state_ops


def _client_names():
    """id -> display name, from the live roster (fallback: the id itself)."""
    out = {}
    for c in clients:
        out[c.get('id')] = c.get('name_short') or c.get('name_full') or c.get('id')
    return out


def _parse_ts(s):
    try:
        return datetime.datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def _fmt_time(dt):
    if not dt:
        return ''
    return dt.strftime('%d.%m %H:%M')


def _chips(rec):
    """Render the added/removed/changed key chips for one record."""
    out = []
    for kind, css in (('added', 'cl-add'), ('removed', 'cl-del'), ('changed', 'cl-chg')):
        keys = rec.get(kind) or []
        if not keys:
            continue
        label = t(kind)
        keys_html = ', '.join('<code>' + _esc(str(k)) + '</code>' for k in keys)
        out.append('<span class="cl-chip ' + css + '">' + label + '</span> ' + keys_html)
    return '<br>'.join(out) if out else '<span class="muted">-</span>'


def render_changelog():
    head = render_header()
    title = t('Changelog')
    names = _client_names()

    records = state_ops.audit_read()
    # newest first
    records = sorted(records, key=lambda r: r.get('ts') or '', reverse=True)

    # group by ISO (year, week)
    weeks = {}  # (iso_year, iso_week) -> list of records
    for r in records:
        dt = _parse_ts(r.get('ts'))
        if dt:
            iso = dt.isocalendar()
            key = (iso[0], iso[1])
        else:
            key = (0, 0)
        weeks.setdefault(key, []).append(r)

    body_parts = []
    if not records:
        body_parts.append('<div class="cl-empty">' + t('No state changes recorded yet.') + '</div>')

    for key in sorted(weeks.keys(), reverse=True):
        recs = weeks[key]
        year, week = key
        if year:
            week_label = t('Week') + ' ' + str(week) + ', ' + str(year)
        else:
            week_label = t('Undated')
        n_changes = len(recs)
        n_clients = len({r.get('client') for r in recs})
        head_line = (
            '<div class="cl-week-head"><h2>' + _esc(week_label) + '</h2>'
            '<span class="cl-week-meta">' + str(n_changes) + ' ' + t('changes')
            + ' · ' + str(n_clients) + ' ' + t('clients') + '</span></div>'
        )

        # group by client within the week
        by_client = {}
        for r in recs:
            by_client.setdefault(r.get('client'), []).append(r)

        rows = []
        for cid in sorted(by_client.keys(), key=lambda c: names.get(c, c or '')):
            crecs = by_client[cid]
            inner = []
            for r in crecs:
                dt = _parse_ts(r.get('ts'))
                ctx = r.get('ctx') or ''
                inner.append(
                    '<tr>'
                    '<td class="cl-file"><code>' + _esc(str(r.get('file', ''))) + '</code></td>'
                    '<td class="cl-keys">' + _chips(r) + '</td>'
                    '<td class="cl-ctx"><span class="muted">' + _esc(str(ctx)) + '</span></td>'
                    '<td class="cl-time">' + _esc(_fmt_time(dt)) + '</td>'
                    '</tr>'
                )
            rows.append(
                '<div class="cl-client">'
                '<h3>' + _esc(names.get(cid, cid or '?')) + '</h3>'
                '<table class="cl-table"><tbody>' + ''.join(inner) + '</tbody></table>'
                '</div>'
            )

        body_parts.append('<section class="cl-week">' + head_line + ''.join(rows) + '</section>')

    content = (
        '<h1 class="page-title">' + t('Changelog') + '</h1>'
        '<p class="cl-lead">' + t('Field-level log of every change to client state, newest first. '
                                  'Shows which fields moved, not their values.') + '</p>'
        + ''.join(body_parts)
    )

    extra_css = (
        '.page-title{font-size:22px;font-weight:500;margin:0 0 var(--space-md)}'
        '.cl-lead{font-size:14px;line-height:1.6;color:var(--text-secondary);'
        'margin:0 0 var(--space-lg);max-width:760px}'
        '.cl-empty{color:var(--text-muted);font-size:15px;padding:var(--space-lg);'
        'background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-card)}'
        '.cl-week{margin-bottom:var(--space-xl)}'
        '.cl-week-head{display:flex;align-items:baseline;gap:var(--space-md);'
        'border-bottom:1px solid var(--border);margin-bottom:var(--space-md);'
        'padding-bottom:var(--space-xs)}'
        '.cl-week-head h2{font-size:18px;font-weight:500;margin:0}'
        '.cl-week-meta{font-size:13px;color:var(--text-muted)}'
        '.cl-client{margin-bottom:var(--space-md)}'
        '.cl-client h3{font-size:14px;font-weight:600;margin:0 0 var(--space-xs);'
        'color:var(--text-primary)}'
        '.cl-table{width:100%;border-collapse:collapse;background:var(--bg-card);'
        'border:1px solid var(--border);border-radius:var(--radius-card);overflow:hidden;'
        'font-size:14px;max-width:860px}'
        '.cl-table td{padding:7px var(--space-sm);border-bottom:1px solid var(--border);'
        'vertical-align:top}'
        '.cl-table tr:last-child td{border-bottom:none}'
        '.cl-file{white-space:nowrap;width:1%}'
        '.cl-keys{line-height:1.6}'
        '.cl-ctx{white-space:nowrap;width:1%}'
        '.cl-time{white-space:nowrap;width:1%;color:var(--text-muted);text-align:right}'
        '.cl-chip{font-size:12px;padding:1px 7px;border-radius:8px;font-weight:600;'
        'display:inline-block;border:1px solid transparent}'
        '.cl-add{background:#EAF3DE;color:#3D6107;border-color:#C0DD97}'
        '.cl-del{background:#FCEBEB;color:#9B1C1C;border-color:#F09595}'
        '.cl-chg{background:#E6F1FB;color:#0C447C;border-color:#B5D4F4}'
        'code{font-family:monospace;background:var(--bg-page);padding:1px 4px;'
        'border-radius:3px;font-size:13px}'
        '.muted{color:var(--text-muted)}'
    )

    return (
        '<!DOCTYPE html>\n<html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>' + _esc(title) + '</title>'
        '<style>' + DESIGN_TOKENS_CSS + OVERVIEW_SPECIFIC_CSS + OVERVIEW_V2_CSS
        + SIDEBAR_CSS + PROMPT_MODAL_CSS + extra_css + '</style>'
        '</head><body>'
        '<div class="layout-shell">'
        + render_sidebar(active='changelog')
        + '<main class="main-content">'
        + head
        + content
        + '</main></div>'
        + PROMPT_MODAL_HTML + PROMPT_MODAL_JS
        + '</body></html>'
    )
