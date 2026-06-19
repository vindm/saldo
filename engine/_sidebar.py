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

SIDEBAR_CSS = (
    ".layout-shell{display:grid;grid-template-columns:210px 1fr;gap:var(--space-md);"
    "max-width:none;margin:0;padding:var(--space-md);align-items:start}"
    "@media(max-width:900px){.layout-shell{grid-template-columns:1fr}}"
    ".sb{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);padding:var(--space-md) var(--space-sm);"
    "font-size:15px;position:sticky;top:var(--space-md);"
    "max-height:calc(100vh - 2*var(--space-md));overflow-y:auto}"
    ".sb-logo{display:flex;flex-direction:column;align-items:center;text-align:center;"
    "gap:7px;padding:2px var(--space-sm) var(--space-md);"
    "border-bottom:2px solid #B79257;margin-bottom:var(--space-sm)}"
    ".sb-logo-img{width:64px;height:64px;border-radius:50%;display:block;"
    "box-shadow:0 1px 4px rgba(31,78,121,0.25)}"
    ".sb-logo-txt{display:flex;flex-direction:column;line-height:1.18}"
    ".sb-logo-txt b{font-size:14px;font-weight:700;color:#1F4E79;letter-spacing:.01em}"
    ".sb-logo-txt span{font-size:11px;color:var(--text-secondary);"
    "text-transform:uppercase;letter-spacing:.05em}"
    ".sb-group{font-size:15px;text-transform:uppercase;letter-spacing:0.04em;"
    "color:var(--text-secondary);padding:var(--space-sm) var(--space-sm) 4px;font-weight:600}"
    ".sb-item{display:flex;align-items:center;gap:8px;padding:8px var(--space-sm);"
    "border-radius:var(--radius-btn);color:var(--text-primary);"
    "text-decoration:none;font-size:15px;cursor:pointer;"
    "transition:background var(--transition),color var(--transition);"
    "margin-bottom:1px}"
    ".sb-item:hover{background:var(--bg-page);color:var(--text-primary)}"
    ".sb-item.active{background:var(--bg-page);color:var(--text-primary);"
    "font-weight:600;box-shadow:inset 3px 0 0 #B79257}"
    ".sb-item.sub{padding-left:24px;font-size:15px}"
    ".sb-item .ico{font-size:16px;line-height:1;flex-shrink:0;width:16px;"
    "display:inline-flex;justify-content:center}"
    ".sb-item .count{margin-left:auto;font-size:14px;color:var(--text-secondary);"
    "padding:2px 8px;background:var(--bg-page);border-radius:10px;font-weight:500}"
    ".sb-item.active .count{background:var(--bg-card)}"
    ".sb-item .count.alert{color:var(--accent-red);font-weight:600}"
    ".sb-divider{height:1px;background:var(--border);margin:var(--space-sm) 4px}"
    ".sb-footer{font-size:15px;color:var(--text-muted);padding:var(--space-sm);"
    "border-top:1px solid var(--border);margin-top:var(--space-sm);text-align:center}"
    ".main-content{min-width:0}"
    ".sb-item.sb-clients{border-left:3px solid #7F77DD}"
)


def _sb_item(href, label, key, active, icon='', sub=False, count=None, alert=False,
             clients_item=False):
    cls = 'sb-item'
    if sub:
        cls += ' sub'
    if key == active:
        cls += ' active'
    if clients_item:
        cls += ' sb-clients'
    cnt_html = ''
    if count is not None:
        cnt_cls = 'count alert' if alert else 'count'
        cnt_html = f'<span class="{cnt_cls}">{count}</span>'
    icon_html = f'<span class="ico">{icon}</span>' if icon else '<span class="ico"></span>'
    return f'<a class="{cls}" href="{href}">{icon_html}{label}{cnt_html}</a>'


# Icon assigned to client-group items, cycled by first-seen order so distinct
# groups read differently. Purely cosmetic — not tied to any specific name.
_GROUP_ICONS = ['👥', '🏢', '🗂️', '📁', '🧾', '📌']


def _client_group_items(active):
    """Build one sidebar item per client group present in the data."""
    from generate import clients
    groups = dynamic_groups(clients)
    items = []
    for i, g in enumerate(groups):
        slug = _slugify_group(g)
        key = 'clients_' + slug
        count = len(clients_in_group(clients, g))
        icon = _GROUP_ICONS[i % len(_GROUP_ICONS)]
        items.append(_sb_item(
            'clients_' + slug + '.html', _group_label(g), key, active,
            icon=icon, count=count, clients_item=True,
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
        '<aside class="sb">',
        '<div class="sb-logo"><img class="sb-logo-img" src="' + LOGO_DATA_URI + '" alt="' + BRAND_MONOGRAM + '">'
        '<div class="sb-logo-txt"><b>' + BRAND_NAME + '</b>'
        '<span>' + BRAND_TAGLINE + '</span></div></div>',
        _sb_item('dashboard_overview.html', t('Dashboard'), 'dashboard', active, icon='🏠'),
        _sb_item('plan_today.html', t('Plan'), 'plan_today', active,
                 icon='🔥', count=plan_today_count, alert=True),
        _sb_item('calendar.html', t('Calendar'), 'calendar', active, icon='📆'),
        _sb_item('periods.html', t('Periods'), 'periods', active, icon='🗓'),
        '<div class="sb-divider"></div>',
        '<div class="sb-group">' + t('Clients') + '</div>',
    ]
    parts.extend(_client_group_items(active))
    parts.extend([
        '<div class="sb-divider"></div>',
        _sb_item('guide.html', t('How to use'), 'guide', active, icon='📖'),
        '<div class="sb-footer">' + BRAND_NAME + '<br>v0.1</div>',
        '</aside>',
    ])
    return ''.join(parts)
