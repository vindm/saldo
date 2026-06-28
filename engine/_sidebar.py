"""_sidebar.py — single left-hand menu for all dashboard views.

Information architecture:
  - Dashboard (system pulse, no client grid)
  - Plan
      Today (actionable checklist for the day)
      This Week (7-day grid)
      Month (calendar grid)
  - Clients — one item per group present in the data (dynamic)

The "Clients" section is built dynamically from the per-client `group` field:
one sidebar item per distinct group, in first-seen order, with its live count.
No group name is hardcoded — add a new group value to clients_index.json and a
new sidebar item appears automatically.
"""

from _brand_assets import LOGO_DATA_URI
from _config import BRAND_NAME, BRAND_TAGLINE, BRAND_MONOGRAM
from _helpers import dynamic_groups, clients_in_group, _slugify_group, _group_label
from _strings import t
from _icons import icon, ICON_SPRITE, ICON_CSS
from _onboarding import render_add_group_button

SIDEBAR_CSS = (
    ".layout-shell{display:grid;grid-template-columns:248px 1fr;gap:0;"
    "max-width:none;margin:0;padding:0;align-items:start}"
    "@media(max-width:900px){.layout-shell{grid-template-columns:1fr}}"
    # Full-bleed sidebar: edge-to-edge, full height, hairline right border —
    # no floating 'island' card (border/radius/inset removed).
    ".sb{background:var(--bg-card);border:none;border-right:1px solid var(--border);"
    "border-radius:0;padding:28px 20px;"
    "font-size:15px;position:sticky;top:0;height:100vh;"
    "max-height:100vh;overflow-y:auto;display:flex;flex-direction:column}"
    # Bottom block (guide + update + footer) pinned to the foot of the sidebar.
    ".sb-bottom{margin-top:auto}"
    ".main-content{padding:32px 48px}"
    "@media(max-width:900px){.main-content{padding:var(--space-lg)}}"
    # Generous left-aligned brand block: logo stacked above the name + tagline,
    # an editorial header rather than a cramped row. Text wraps freely, so a long
    # brand name (e.g. the RU practice "Ирина Винокурова") flows to 2 lines.
    ".sb-logo{display:flex;flex-direction:column;align-items:flex-start;text-align:left;"
    "gap:14px;padding:2px 2px 24px;"
    "border-bottom:1px solid var(--border);margin-bottom:18px}"
    ".sb-logo-img{width:54px;height:54px;border-radius:50%;display:block;flex-shrink:0;"
    "box-shadow:0 1px 4px rgba(31,78,121,0.25)}"
    ".sb-logo-txt{display:flex;flex-direction:column;line-height:1.2;gap:4px;min-width:0}"
    ".sb-logo-txt b{font-size:17px;font-weight:600;color:#1F4E79;letter-spacing:.005em}"
    ".sb-logo-txt span{font-size:10.5px;color:var(--text-muted);"
    "text-transform:uppercase;letter-spacing:.13em}"
    # Quiet section header: a small muted micro-label with wide tracking and room
    # above it — reads as a divider caption, not a clickable peer of the nav items.
    ".sb-group{font-size:10.5px;text-transform:uppercase;letter-spacing:0.14em;"
    "color:var(--text-muted);padding:18px 10px 8px;font-weight:400}"
    # The «Clients» caption shares its row with a quiet "+" that opens the
    # add-a-new-group prompt (render_add_group_button). The header keeps its own
    # padding; the row only zeroes the caption's bottom padding so the "+" lines
    # up with the caption baseline.
    ".sb-group-row{display:flex;align-items:center}"
    ".sb-group-row .sb-group{flex:1;padding-right:6px}"
    ".sb-add-group{flex-shrink:0;width:20px;height:20px;margin-right:8px;"
    "display:inline-flex;align-items:center;justify-content:center;"
    "padding:0;border:1px solid var(--border);background:var(--bg-card);"
    "color:var(--text-muted);border-radius:6px;cursor:pointer;"
    "font-size:15px;line-height:1;font-family:inherit;"
    "transition:background var(--transition),color var(--transition),"
    "border-color var(--transition)}"
    ".sb-add-group:hover{background:var(--accent-soft);color:var(--accent);"
    "border-color:var(--accent)}"
    # Nav rows: airy 14.5px on a roomy 8px rhythm — inactive rows are the calmer
    # --text-secondary, going full --accent (navy) when selected.
    ".sb-item{display:flex;align-items:center;gap:11px;padding:8px 10px;"
    "border-radius:7px;color:var(--text-secondary);"
    "text-decoration:none;font-size:14.5px;cursor:pointer;"
    "transition:background var(--transition),color var(--transition);"
    "margin-bottom:1px}"
    ".sb-item:hover{background:var(--bg-page);color:var(--text-primary)}"
    # The accent left-rail is the SINGLE selection signal (see the removed purple
    # client-group border below) — so the active item is never ambiguous.
    ".sb-item.active{background:var(--accent-soft);color:var(--accent-text);"
    "font-weight:500;box-shadow:inset 3px 0 0 var(--accent)}"
    ".sb-item.sub{padding-left:28px;font-size:14.5px}"
    # Icons sit muted at rest and follow the row to navy when it's active.
    ".sb-item .ico{font-size:15px;line-height:1;flex-shrink:0;width:17px;"
    "color:var(--text-muted);display:inline-flex;justify-content:center}"
    ".sb-item.active .ico{color:var(--accent)}"
    # Counts are quiet tabular numbers, not pills — less chrome per row.
    ".sb-item .count{margin-left:auto;font-size:12px;color:var(--text-muted);"
    "font-weight:400;font-variant-numeric:tabular-nums}"
    ".sb-item.active .count{color:var(--accent-text)}"
    # The one count that must pull attention (overdue Plan items) keeps a red tint.
    ".sb-item .count.alert{color:var(--accent-red);font-weight:600;"
    "background:var(--red-bg);padding:1px 7px;border-radius:9px}"
    ".sb-divider{height:1px;background:var(--border);margin:var(--space-sm) 4px}"
    ".sb-footer{font-size:12px;color:var(--text-muted);padding:var(--space-sm);"
    "border-top:1px solid var(--border);margin-top:var(--space-sm);text-align:center;letter-spacing:.02em}"
    ".main-content{min-width:0}"
    # Gold "Update available" call-to-action (rendered by _updater.py).
    ".sb-item.sb-update{border-left:3px solid #B79257;background:#FBF4E6;"
    "color:#6B4F1C;font-weight:600}"
    ".sb-item.sb-update:hover{background:#F4E8CC;color:#5A3F12}"
    ".sb-item.sb-update .count{background:#B79257;color:#fff;font-weight:700}"
)
SIDEBAR_CSS = SIDEBAR_CSS + ICON_CSS


def _sb_item(href, label, key, active, icon='', sub=False, count=None, alert=False):
    cls = 'sb-item'
    if sub:
        cls += ' sub'
    if key == active:
        cls += ' active'
    cnt_html = ''
    if count is not None:
        cnt_cls = 'count alert' if alert else 'count'
        cnt_html = f'<span class="{cnt_cls}">{count}</span>'
    icon_html = f'<span class="ico">{icon}</span>' if icon else '<span class="ico"></span>'
    return f'<a class="{cls}" href="{href}">{icon_html}{label}{cnt_html}</a>'


# Icon assigned to client-group items, cycled by first-seen order so distinct
# groups read differently. Purely cosmetic — not tied to any specific name.
_GROUP_ICONS = ['users', 'building', 'folder', 'users', 'building', 'folder']


def _client_group_items(active):
    """Build one sidebar item per client group present in the data."""
    from generate import clients
    groups = dynamic_groups(clients)
    items = []
    for i, g in enumerate(groups):
        slug = _slugify_group(g)
        key = 'clients_' + slug
        count = len(clients_in_group(clients, g))
        ic_name = _GROUP_ICONS[i % len(_GROUP_ICONS)]
        items.append(_sb_item(
            'clients_' + slug + '.html', _group_label(g), key, active,
            icon=icon(ic_name), count=count,
        ))
    return items


def render_sidebar(active='dashboard', counts=None):
    """Render the left-hand menu.

    Parameters:
        active — identifier of the current page:
            'dashboard', 'plan_today', 'plan_week', 'plan_month',
            'guide', or 'clients_<group-slug>'.
        counts — dict of numbers for the Plan items:
            {'plan_today': N, 'plan_week': N}
            (Client-group counts are derived dynamically from the data.)
    """
    counts = counts or {}
    plan_today_count = counts.get('plan_today')
    plan_week_count = counts.get('plan_week')

    parts = [
        ICON_SPRITE,
        '<aside class="sb">',
        '<div class="sb-logo"><img class="sb-logo-img" src="' + LOGO_DATA_URI + '" alt="' + BRAND_MONOGRAM + '">'
        '<div class="sb-logo-txt"><b>' + BRAND_NAME + '</b>'
        '<span>' + BRAND_TAGLINE + '</span></div></div>',
        _sb_item('dashboard_overview.html', t('Dashboard'), 'dashboard', active, icon=icon('home')),
        _sb_item('plan_today.html', t('Plan'), 'plan_today', active,
                 icon=icon('plan'), count=plan_today_count, alert=True),
        _sb_item('calendar.html', t('Calendar'), 'calendar', active, icon=icon('calendar')),
        _sb_item('periods.html', t('Periods'), 'periods', active, icon=icon('periods')),
        '<div class="sb-divider"></div>',
        # «Clients» caption + the "+" that opens the add-a-new-group prompt.
        '<div class="sb-group-row"><div class="sb-group">' + t('Clients') + '</div>'
        + render_add_group_button() + '</div>',
    ]
    parts.extend(_client_group_items(active))
    # Bottom-pinned block: "How to use", the update affordance, and the footer
    # sit at the foot of the sidebar (margin-top:auto pushes them down).
    parts.extend([
        '<div class="sb-bottom">',
        '<div class="sb-divider"></div>',
        _sb_item('guide.html', t('How to use'), 'guide', active, icon=icon('guide')),
    ])
    # Update affordance — appears only when the check flag says a new engine
    # version is available; renders '' (nothing) otherwise. Imported lazily to
    # avoid any import cycle through generate/_config.
    try:
        from _updater import render_update_sidebar_item
        parts.append(render_update_sidebar_item(active))
    except Exception:
        pass
    parts.extend([
        '<div class="sb-footer">by Ask Why Not</div>',
        '</div>',
        '</aside>',
    ])
    return ''.join(parts)
