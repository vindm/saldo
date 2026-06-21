"""_overview_shared.py — shared functions for the overview page.

- render_header() — header with date, time, and daemon status dots
- render_mail_block() / render_news_block() — external-signal feeds, rendered with
  the shared event component (engine/_components.py), same as the track/decision lists.
"""
from _helpers import _esc, _esca, _format_date_ru, _snapshot_time
from _loaders import _DAEMON_DIAG
from _strings import t, tp
from _icons import icon


def render_header():
    import generate
    TODAY = generate.TODAY
    time_bali = getattr(generate, 'TIME_BALI', '') or ''
    time_msk = getattr(generate, 'TIME_MSK', '') or ''
    snapshot = _snapshot_time()
    date_str = _format_date_ru(TODAY)
    LABELS = [('finkoper', 'Finkoper'), ('mail', t('Mail')),
              ('anomalies', t('Anomalies')), ('news', t('News')),
              ('updates', t('Updates'))]
    dots = []
    for key, label in LABELS:
        info = _DAEMON_DIAG.get(key, {'status': 'missing', 'count': 0, 'detail': t('not run')})
        st = info['status']
        cls = 'ok' if st == 'ok' else ('empty' if st == 'empty_unexpected' else 'missing')
        title = f"{label}: {st}"
        if st == 'ok':
            title += f", {info.get('count', 0)} {t('records')}"
        if info.get('detail'):
            title += f" — {info['detail']}"
        dots.append(f'<span class="source-dot {cls}" title="{_esca(title)}"></span>')
    dots_html = ''.join(dots)
    if time_bali and time_msk:
        time_html = (
            f'<span title="{_esca(t("Current time in Bali and Moscow"))}">'
            + icon('clock') + f' {_esc(time_bali)} WITA · {_esc(time_msk)} {t("MSK")}'
            + '</span>'
        )
    else:
        time_html = '<span>' + icon('clock') + f' {_esc(snapshot)} {t("MSK")}</span>'
    snapshot_html = ''
    if snapshot:
        snapshot_html = (
            f'<span title="{_esca(t("Last daemon snapshot"))}" class="meta">'
            f'{t("snapshot")} {_esc(snapshot)}</span>'
        )
    return (
        '<header class="page-header">'
        f'<h1>{_esc(date_str)}</h1>'
        '<div class="status-line">'
        f'{time_html}'
        '</div></header>'
    )


def render_mail_block(daemon_mail, limit=5):
    """Mail updates as the shared event list (same component as track/decision lists)."""
    from _components import event_row, render_event_section, render_empty_section
    title = tp('📬 Mail updates', '📬 Обновления в почте')
    items = [m for m in ((daemon_mail or {}).get('list') or []) if m.get('severity') in ('high', 'medium')]
    if not items:
        return render_empty_section(title, t('No mail needs a reply'))
    rows = []
    for m in items[:limit * 2]:
        head = _esc(m.get('subject') or t('(no subject)'))
        sub = t('from') + ' ' + (m.get('from_name') or '')
        if m.get('client'):
            sub += ' · ' + t('client') + ' ' + m.get('client')
        rows.append(event_row(m.get('from_name') or m.get('client') or 'mail',
                              head, _esc(sub), tp('mail', 'почта'), None, ''))
    return render_event_section(title, rows, count=len(items), show=limit)


def render_news_block(daemon_news, limit=5):
    """Accounting news as the shared event list."""
    from _components import event_row, render_event_section, render_empty_section
    title = tp('📰 Accounting news', '📰 Новости бухгалтерии')
    sev = {'high': 0, 'medium': 1, 'low': 2}
    items = sorted(((daemon_news or {}).get('list') or []), key=lambda x: sev.get(x.get('severity'), 9))
    if not items:
        return render_empty_section(title, t('No significant news'))
    rows = []
    for n in items[:limit * 2]:
        head = _esc(n.get('title') or '')
        rows.append(event_row(n.get('source') or 'news', head, _esc(n.get('source') or ''),
                              tp('news', 'новости'), None, ''))
    return render_event_section(title, rows, count=len(items), show=limit)


# Canonical set of "closed" track statuses (kept in sync with _aggregator.py).
CLOSED_TRACK_STATUSES = {"done", "dropped", "dismissed", "completed",
                         "cancelled", "closed", "resolved", "deferred"}


def is_track_active(tr):
    """True if the track is active: not system-internal and not in a closed status.

    Used by overview cards (team/direct) so closed tracks aren't shown as the
    "urgent" headline task and aren't counted in the badge.
    """
    if (tr.get('zone', 'client_work') or 'client_work') == 'system_internal':
        return False
    if (tr.get('status') or '') in CLOSED_TRACK_STATUSES:
        return False
    return True
