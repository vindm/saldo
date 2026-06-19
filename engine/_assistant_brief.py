"""_assistant_brief.py — assistant prose.

Says what a list cannot: context and interpretation.

Split rule:
  - chronic tracks (source=track, overdue > 7d) -> "planned tracks, not urgent"
  - everything else in hot -> urgent, phrased in plain language
"""
from generate import _esc, TODAY
from _helpers import _translate_tech_terms
from _strings import t, WEEKDAYS_FULL


ASSISTANT_BRIEF_CSS = (
    ".assistant-brief-card{"
    "background:#F4F8F1;"
    "border:0.5px solid #C3D9B8;"
    "border-left:3px solid #6B8E5A;"
    "border-radius:0 8px 8px 0;"
    "padding:10px 16px;"
    "margin-bottom:16px;"
    "display:flex;gap:10px;align-items:flex-start}"
    ".abc-icon{font-size:18px;flex-shrink:0;margin-top:2px;line-height:1}"
    ".abc-text{font-size:16px;color:#1F2937;line-height:1.65;flex:1;min-width:0}"
    ".assistant-overview-brief{"
    "background:#F4F8F1;"
    "border:0.5px solid #C3D9B8;"
    "border-left:3px solid #6B8E5A;"
    "border-radius:0 8px 8px 0;"
    "padding:12px 16px;"
    "margin-bottom:16px;"
    "display:flex;gap:10px;align-items:flex-start}"
    ".aob-icon{font-size:18px;flex-shrink:0;margin-top:2px}"
    ".aob-text{font-size:16px;color:#1F2937;line-height:1.65;flex:1;min-width:0}"
    ".task-next-inline{font-size:14px;color:#4A6FA5;margin-top:4px;display:block}"
)

WEEKDAYS_EN = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday',
    'Friday', 'Saturday', 'Sunday',
]

# Tracks overdue beyond this threshold are chronic work, not a fire
CHRONIC_DAYS = -7


def _dl_phrase(dl):
    """days_left -> a plain-language phrase."""
    if dl < 0:
        return t('overdue {}d').format(-dl)
    if dl == 0:
        return t('today')
    if dl == 1:
        return t('tomorrow')
    if dl == 2:
        return t('in 2 days')
    return t('in {}d').format(dl)


def _narrative(groups, today=None):
    """2-3 sentences in natural language."""
    if today is None:
        today = TODAY

    hot     = groups.get('hot', [])
    pending = groups.get('pending', [])

    # --- Split hot into chronic vs genuinely urgent ---
    chronic = [
        t for t in hot
        if t.get('source') == 'track' and (t.get('days_left') or 0) < CHRONIC_DAYS
    ]
    chronic_ids = {id(t) for t in chronic}
    urgent = [t for t in hot if id(t) not in chronic_ids]

    # Chronic clients (those without urgent tasks — avoid duplicates)
    urgent_names = {t.get('client_name', '') for t in urgent}
    chronic_only = [t for t in chronic if t.get('client_name', '') not in urgent_names]

    # Waiting a long time for a reply (>5 days)
    long_wait = [t for t in pending if (t.get('days_left') or 0) < -5]

    is_weekend = today.weekday() >= 5
    parts = []

    # 1. Day of week (weekends only)
    if is_weekend:
        parts.append(t('Today is {}.').format(WEEKDAYS_FULL[today.weekday()]))

    # 2. Urgent tasks — grouped by deadline
    if urgent:
        by_dl = {}
        for tk in urgent:
            dl = tk.get('days_left') or 0
            by_dl.setdefault(dl, []).append(tk)

        dl_phrases = []
        for dl in sorted(by_dl.keys())[:2]:  # max 2 deadline waves
            tasks = by_dl[dl]
            clients = list(dict.fromkeys(
                (tk.get('client_name') or '').replace('SP ', '')
                for tk in tasks if tk.get('client_name')
            ))
            cs = ', '.join(clients[:4])
            if len(clients) > 4:
                cs += t(' +{} more').format(len(clients) - 4)
            dl_phrases.append('{} — {}'.format(_dl_phrase(dl), cs))

        first = dl_phrases[0][0].upper() + dl_phrases[0][1:]
        rest = '; '.join(dl_phrases[1:])
        sentence = (first + '; ' + rest) if rest else first
        parts.append(sentence + '.')
    else:
        parts.append(t('No urgent deadlines.') if not is_weekend
                     else t('No deadlines.'))

    # 3. Chronic tracks — reassure
    if chronic_only:
        clients = list(dict.fromkeys(
            (tt.get('client_name') or '').replace('SP ', '')
            for tt in chronic_only if tt.get('client_name')
        ))
        cs = ', '.join(clients[:3])
        if len(clients) > 3:
            cs += t(' and others')
        parts.append(t('{} — planned tracks, not urgent.').format(cs))

    # 4. Long waits
    if long_wait:
        days = -(long_wait[0].get('days_left') or 0)
        cn = (long_wait[0].get('client_name') or '').replace('SP ', '')
        extra = ('' if len(long_wait) == 1
                 else t(' ({} more without a reply)').format(len(long_wait) - 1))
        parts.append(t('Waiting for a reply from {} — {}d{}.').format(cn, days, extra))

    return ' '.join(parts)


def render_assistant_rec_card(groups):
    """Card for the Plan-Today page."""
    text = _narrative(groups)
    if not text:
        return ''
    return (
        '<div class="assistant-brief-card">'
        '<span class="abc-icon">\U0001f4a1</span>'
        '<span class="abc-text">' + _esc(text) + '</span>'
        '</div>'
    )


def render_assistant_overview_brief(groups):
    """Card for the main dashboard."""
    text = _narrative(groups)
    if not text:
        return ''
    return (
        '<div class="assistant-overview-brief">'
        '<span class="aob-icon">\U0001f4a1</span>'
        '<span class="aob-text">' + _esc(text) + '</span>'
        '</div>'
    )
