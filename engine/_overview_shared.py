"""_overview_shared.py — shared functions for the overview page.

Contains two functions reused by render_overview_v2():
- render_header() — header with date, time, and daemon status dots
- render_morning_digest() — expanded "Morning digest" block with top news/mail/updates

Extracted from _overview_legacy.py during the legacy cleanup 2026-05-17.
"""
from _helpers import _esc, _esca, _format_date_ru, _snapshot_time
from _loaders import _DAEMON_DIAG
from _strings import t


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
            f'🕐 {_esc(time_bali)} WITA · {_esc(time_msk)} {t("MSK")}'
            f'</span>'
        )
    else:
        time_html = f'<span>🕐 {_esc(snapshot)} {t("MSK")}</span>'
    snapshot_html = ''
    if snapshot:
        snapshot_html = (
            f'<span title="{_esca(t("Last daemon snapshot"))}" class="meta">'
            f'📡 {t("snapshot")} {_esc(snapshot)}</span>'
        )
    return (
        '<header class="page-header">'
        f'<h1>{_esc(date_str)}</h1>'
        '<div class="status-line">'
        f'{time_html}'
        f'{snapshot_html}'
        f'<span>📡 {dots_html}</span>'
        '</div></header>'
    )


def render_morning_digest(daemon_news, daemon_mail, daemon_updates):
    news_list = (daemon_news or {}).get('list', []) or []
    sev_order = {'high': 0, 'medium': 1, 'low': 2}
    news_sorted = sorted(news_list, key=lambda x: sev_order.get(x.get('severity'), 9))
    top_news = news_sorted[:3]
    if top_news:
        news_html = ''.join(
            f'<div class="digest-item">'
            f'<strong>{_esc(n.get("title",""))}</strong>'
            f'<div class="meta">{_esc(n.get("source",""))}'
            + (f' · <a href="{_esca(n.get("url"))}" target="_blank">{t("read")}</a>' if n.get('url') else '')
            + '</div></div>'
            for n in top_news
        )
    else:
        news_html = '<div class="muted">' + t('No significant news') + '</div>'

    mail_list = (daemon_mail or {}).get('list', []) or []
    mail_filtered = [m for m in mail_list if m.get('severity') in ('high', 'medium')]
    top_mail = mail_filtered[:3]
    if top_mail:
        mail_html = ''.join(
            f'<div class="digest-item">'
            f'<strong>{_esc(m.get("subject") or t("(no subject)"))}</strong>'
            f'<div class="meta">{t("from")} {_esc(m.get("from_name",""))}'
            + (f' · {t("client")} {_esc(m.get("client"))}' if m.get('client') else '')
            + '</div></div>'
            for m in top_mail
        )
    else:
        mail_html = '<div class="muted">' + t('No mail needs a reply') + '</div>'

    updates = (daemon_updates or {}).get('list', []) or []
    applied = [u for u in updates if u.get('category') == 'applied']
    needs_manual = [u for u in updates if u.get('category') == 'needs_manual']
    updates_rows = ''
    if applied:
        updates_rows = ''.join(
            f'<div class="digest-item">✅ {_esc(u.get("title") or u.get("body",""))}'
            + (f'<div class="meta">{_esc(u.get("label",""))}</div>' if u.get('label') else '')
            + '</div>'
            for u in applied
        )
    if needs_manual:
        updates_rows += (
            f'<div class="digest-item" style="color:var(--accent-yellow)">'
            f'⚠️ {len(needs_manual)} {t("updates need my decision")} '
            f'(see _diary/inbox/updates_*.md)</div>'
        )
    if not updates_rows:
        updates_rows = '<div class="muted">' + t('Nothing was updated') + '</div>'

    return (
        '<details class="digest" open>'
        '<summary>' + t('Morning digest') + '</summary>'
        '<div class="digest-content">'
        f'<div class="digest-block"><h4>{t("Top news")}</h4>{news_html}</div>'
        f'<div class="digest-block"><h4>{t("Top mail")}</h4>{mail_html}</div>'
        f'<div class="digest-block"><h4>{t("Overnight auto-updates")}</h4>{updates_rows}</div>'
        '</div></details>'
    )


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
