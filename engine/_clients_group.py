"""_clients_group.py — generic "Clients — <group>" page with a card grid.

One renderer for every client group. The set of groups is derived from the
data (the per-client `group` field), so this single module replaces the old
group-specific _clients_team.py / _clients_direct.py pair.

render_clients_group(group_name, clients_in_group) builds one page; generate.py
calls it once per dynamic group and writes clients_<slug>.html.

Each card shows: name, regime/scenario, health, top track action, remaining
task count, and (if present) a small "profile" link. Clicking a card opens the
client dashboard.
"""
import os
from datetime import datetime as _dt

from generate import (
    clients, TODAY, DIARY_INBOX,
    _esc, _esca,
    load_daemon_finkoper, load_daemon_anomalies,
    _load_all_tasks, calculate_health,
    DESIGN_TOKENS_CSS, OVERVIEW_SPECIFIC_CSS, NEW_JS_FRAGMENT, PLAN_DIR,
)
from _deadlines import collect_deadlines, collect_awaiting
from _helpers import (
    _format_date_ru, _translate_tech_terms,
    _slugify_group, _group_label, client_group,
)
from _strings import t
from _mental_model import load_mental_models
from _overview_v2 import OVERVIEW_V2_CSS
from _overview_shared import render_header, is_track_active
from _sidebar import render_sidebar, SIDEBAR_CSS
from _dictate import DICTATE_CSS, DICTATE_MODAL_HTML, DICTATE_JS
from _css import PROMPT_MODAL_CSS, PROMPT_MODAL_HTML, PROMPT_MODAL_JS


def _plural_tasks(n):
    """Localized "N task(s)" label."""
    return t('{} task').format(n) if abs(n) == 1 else t('{} tasks').format(n)


def _client_profile_rel(c):
    """Relative path to a client's profile.md if it exists, else None.

    The engine does NOT parse profile.md — it only links to it. The file lives
    next to the client's state/ dir: <data>/<folder>/profile.md.
    """
    folder = c.get('folder') or os.path.join('clients', c.get('id', ''))
    abs_path = os.path.join(PLAN_DIR, folder, 'profile.md')
    if os.path.exists(abs_path):
        # Link relative to the dashboards/ output dir → into the data tree.
        # Kept as a best-effort relative hop; harmless if it 404s in a viewer.
        return os.path.relpath(abs_path, _DASHBOARD_DIR_FOR_LINKS())
    return None


def _DASHBOARD_DIR_FOR_LINKS():
    import generate
    return getattr(generate, 'OUT_DIR', '.')


def _scenario_short(c):
    """Short right-hand label on the card: regime, or scenario fallback."""
    regime = (c.get('regime') or '').strip()
    if regime:
        return regime[:30]
    scenario = (c.get('scenario') or '').strip()
    return scenario or ''


def _render_group_card(c, color, n_tracks, key_anom, top_track):
    """A single client card — group-agnostic."""
    right_label = _scenario_short(c)
    head_html = (
        f'<div class="dc-name-row">'
        f'<span class="dc-name">{_esc(c["name_short"])}</span>'
        f'<span class="dc-regime">{_esc(right_label)}</span>'
        f'</div>'
    )

    if key_anom:
        action_html = f'<div class="dc-action">{_esc(_translate_tech_terms(key_anom))}</div>'
        has_top = True
    elif top_track:
        tt = (top_track.get('title') or '')[:90]
        action_html = f'<div class="dc-action">{_esc(_translate_tech_terms(tt))}</div>'
        has_top = True
    elif color == 'green':
        action_html = '<div class="dc-action dc-action-calm">' + t('No urgent tasks or anomalies') + '</div>'
        has_top = False
    else:
        action_html = '<div class="dc-action dc-action-calm">' + t('No active tasks') + '</div>'
        has_top = False

    remaining = max(0, n_tracks - 1) if has_top else 0
    meta_bits = []
    if remaining > 0:
        meta_bits.append('<span class="dc-more">+ ' + t('{} more').format(_plural_tasks(remaining)) + '</span>')
    profile_rel = _client_profile_rel(c)
    if profile_rel:
        meta_bits.append(
            '<span class="dc-profile" title="' + t('A prose profile.md exists for this client') + '">📄 ' + t('profile') + '</span>'
        )
    meta_html = f'<div class="dc-meta-row">{"".join(meta_bits)}</div>' if meta_bits else ''

    href = f'dashboard_{c["id"]}.html'
    return (
        f'<a href="{href}" class="dc-card dc-card-{color}">'
        + head_html + action_html + meta_html
        + '</a>'
    )


_EXTRA_CSS = """
.page-title{font-size:22px;font-weight:500;margin:0 0 var(--space-xs)}
.cd-summary{font-size:15px;color:var(--text-secondary);margin:0 0 var(--space-md)}
.cd-summary .hs{margin-right:var(--space-md);font-size:15px}
.dc-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--space-md);margin:var(--space-md) 0}
@media(max-width:1100px){.dc-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:700px){.dc-grid{grid-template-columns:1fr}}

.dc-card{position:relative;display:flex;flex-direction:column;gap:var(--space-sm);
  background:var(--bg-card);border:1px solid var(--border);
  border-radius:var(--radius-card);
  padding:var(--space-md) var(--space-md) var(--space-md) calc(var(--space-md) + 4px);
  text-decoration:none;color:inherit;
  box-shadow:0 1px 3px rgba(0,0,0,0.04);
  transition:transform 150ms,box-shadow 150ms;
  min-height:124px;cursor:pointer}
.dc-card::before{content:"";position:absolute;left:0;top:14px;bottom:14px;
  width:3px;border-radius:2px;background:var(--border)}
.dc-card-red::before{background:var(--accent-red)}
.dc-card-yellow::before{background:var(--accent-yellow)}
.dc-card-green::before{background:var(--accent-green)}
.dc-card-grey::before{background:var(--text-muted)}
.dc-card:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(0,0,0,0.08)}

.dc-name-row{display:flex;justify-content:space-between;align-items:baseline;gap:var(--space-sm)}
.dc-name{font-size:16px;font-weight:500;color:var(--text-primary);line-height:1.3;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;flex:1}
.dc-regime{font-size:13px;color:var(--text-muted);white-space:nowrap;flex-shrink:0}

.dc-action{font-size:15px;color:var(--text-primary);line-height:1.4}
.dc-action-calm{color:var(--text-muted)}

.dc-meta-row{display:flex;gap:var(--space-md);margin-top:auto;padding-top:var(--space-xs);align-items:center}
.dc-more{font-size:13px;color:var(--text-muted)}
.dc-profile{font-size:13px;color:var(--text-secondary)}
"""


def render_clients_group(group_name, group_clients=None):
    """Render the clients page for one group.

    group_name   — raw group label (e.g. "team", "direct", "archive").
    group_clients — clients in this group; if None, derived from globals.
    """
    if group_clients is None:
        group_clients = [c for c in clients if client_group(c) == group_name]

    deadlines = collect_deadlines(TODAY)
    awaiting = collect_awaiting(TODAY)
    daemon_finkoper = load_daemon_finkoper(DIARY_INBOX, TODAY)
    daemon_anomalies = load_daemon_anomalies(DIARY_INBOX, TODAY)
    mm = load_mental_models()

    tasks_all = _load_all_tasks()
    tracks_by_client = {}
    for tr in mm.get('tracks', []) or []:
        cid = tr.get('client_id')
        if cid and is_track_active(tr):
            tracks_by_client.setdefault(cid, []).append(tr)

    # Health + sorting (red → yellow → green → grey, then by name)
    enriched = []
    for c in group_clients:
        h = calculate_health(c, today=TODAY,
                             daemon_finkoper=daemon_finkoper,
                             daemon_anomalies=daemon_anomalies,
                             deadlines=deadlines, awaiting=awaiting)
        color = h.get('color', 'grey')
        ord_key = {'red': 0, 'yellow': 1, 'green': 2, 'grey': 3}.get(color, 4)
        enriched.append((ord_key, color, c))
    enriched.sort(key=lambda x: (x[0], x[2]['name_short']))

    cards_html = []
    health_counts = {'red': 0, 'yellow': 0, 'green': 0, 'grey': 0}
    for _, color, c in enriched:
        health_counts[color] = health_counts.get(color, 0) + 1
        n_tracks = len(tracks_by_client.get(c['id'], []))
        family = c['name_short'].replace('SP ', '').split(' ')[0]

        # Key anomaly (high severity, not dismissed)
        key_anom = None
        client_dismissed = c.get('dismissed_anomalies') or []
        today_iso = TODAY.isoformat()
        for a in (daemon_anomalies or {}).get('list', []) or []:
            if a.get('client') != c['name_short']:
                continue
            if a.get('severity') != 'high':
                continue
            aid = (a.get('anomaly_id') or '').strip()
            if aid and any(
                dd.get('anomaly_id') == aid
                and (not dd.get('until') or dd.get('until') >= today_iso)
                for dd in client_dismissed
            ):
                continue
            key_anom = (a.get('title') or '')[:80]
            break

        top_track = None
        if not key_anom and n_tracks > 0:
            _prio = {'high': 0, 'normal': 1, 'low': 2}
            top_track = sorted(
                tracks_by_client[c['id']],
                key=lambda tr: _prio.get(tr.get('priority', 'normal'), 1),
            )[0]

        cards_html.append(_render_group_card(c, color, n_tracks, key_anom, top_track))

    grid_html = '<div class="dc-grid">' + ''.join(cards_html) + '</div>'

    health_summary = (
        '<span class="hs hs-red">🔴 ' + t('{} urgent').format(health_counts["red"]) + '</span>'
        ' <span class="hs hs-yellow">🟡 ' + t('{} soon').format(health_counts["yellow"]) + '</span>'
        ' <span class="hs hs-green">🟢 ' + t('{} ok').format(health_counts["green"]) + '</span>'
    )

    label = _group_label(group_name)
    slug = _slugify_group(group_name)
    active_key = 'clients_' + slug
    title = t('Clients — {}').format(label)

    head = render_header()
    return (
        '<!DOCTYPE html>\n<html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMiAzMiI+PGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTUuNSIgZmlsbD0iIzFGNEU3OSIvPjxjaXJjbGUgY3g9IjE2IiBjeT0iMTYiIHI9IjEyLjciIGZpbGw9Im5vbmUiIHN0cm9rZT0iI0I3OTI1NyIgc3Ryb2tlLXdpZHRoPSIxLjMiLz48dGV4dCB4PSIxNiIgeT0iMTciIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJjZW50cmFsIiBmb250LWZhbWlseT0iQXJpYWwsSGVsdmV0aWNhLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZvbnQtd2VpZ2h0PSI3MDAiIGZpbGw9IiNmZmZmZmYiPtCY0JI8L3RleHQ+PC9zdmc+">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>' + _esc(title) + '</title>'
        '<style>' + DESIGN_TOKENS_CSS + OVERVIEW_SPECIFIC_CSS + OVERVIEW_V2_CSS
        + SIDEBAR_CSS + PROMPT_MODAL_CSS + DICTATE_CSS + _EXTRA_CSS + '</style>'
        '</head><body>'
        '<div class="layout-shell">'
        + render_sidebar(active=active_key)
        + '<main class="main-content">'
        + head
        + '<h1 class="page-title">' + _esc(title) + '</h1>'
        + '<div class="cd-summary">' + t('{} {} clients').format(len(group_clients), _esc(label)) + '<br>' + health_summary + '</div>'
        + grid_html
        + '</main></div>'
        + PROMPT_MODAL_HTML + DICTATE_MODAL_HTML
        + NEW_JS_FRAGMENT + PROMPT_MODAL_JS + DICTATE_JS +
        '</body></html>'
    )
