"""
Generator for client dashboards and the summary overview.
Run: python3 generate.py
With no arguments it reads clients_data.json from its own folder and writes HTML into _tmp_html/.

HEALTH FIELD (computed client-state color, recalculated every run):
  🔴 RED    — has a blocker; prep overdue; "Execution status=Overdue";
              UKEP expired; ≥3 gap/blocked sources; request overdue >14 days.
  🟡 YELLOW — internal deadline ≤3 days (prep not closed); due ≤7 days; UKEP ≤30 days;
              request overdue ≤14 days / waiting >7 days; 1–2 gap/wait sources.
  🟢 GREEN  — no RED/YELLOW (after the migration: monthly_check.sources[] no longer exists).
  ⚪ GREY   — otherwise (reserved).
Sources (JSON-first 2026-06-19): per-client state/*.json only — deadlines from
           financials.tax_calendar_2026[] + tasks with a due_date; awaiting from
           open tasks with an awaiting task_type (see _deadlines.py).

Hybrid daemon-reading architecture:
- Finkoper: JSON snapshot in journal/finkoper_state/latest/
  ({tasks,chats,snapshot_meta}.json)
- News/Mail/Anomalies/Updates: JSON files
  journal/inbox/<type>_<date>.json matching the daemons' actual format.
- Deadlines + awaiting: aggregated from per-client state/*.json via _deadlines.py
  (registries retired 2026-06-19).
- Client cards: clients_data.json

Option --print-summary: after generation it prints two blocks to stdout —
"=== SOURCES ===" and "=== HEALTH ===". Used by the scheduled
`dashboard` task for the regeneration log.

Client dashboard (dashboard_<client>.html — the same Scandinavian
minimalism as the overview):

Layout:
- Header with health indicator and a "← All clients" breadcrumb
- Left column: 🔧 In progress now + ⚠️ Noticed
- Right column: ⏳ Waiting + 📖 Recent actions
- Full width: 📥 Event feed for the last 7 days
Below <1100px everything stacks into a single column.

The 5 functional blocks are fed by:
- 🔧 load_client_open_tasks() — Finkoper tasks.json, overdue/soon/normal categories
- ⏳ _deadlines.collect_awaiting() — open tasks with an awaiting task_type (state)
- 📥 build_client_timeline() — Finkoper + mail + anomalies over 7 days, top 15
- ⚠️ load_daemon_anomalies() filtered by client
- 📖 load_client_history() — the client's history, last 5 entries

All interactive buttons copy prompts to the clipboard via the copyPrompt()
JS function. The user ALWAYS has Cowork open — she just Ctrl+V into the chat.

Older renderer versions are kept: gen_overview_legacy() and
gen_html_legacy() — to roll back, just switch the calls in the main loop.

Main screen (dashboard_overview.html):

Design: Scandinavian minimalism
- Palette: terracotta / mustard / sage / dusty blue
- Warm off-white background, white cards
- System sans-serif, generous spacing
- Color used only as a meaningful accent

Layout:
1. Header with the date and source-status dots
2. Priority zone: 3 columns (Urgent / This Week / Awaiting reply)
3. Grid of client cards (6)
4. Collapsed morning digest

The old function was renamed render_overview() → gen_overview_legacy()
in case a rollback is needed.
"""
import os, sys, json
from datetime import date, timedelta
from datetime import datetime as _dt
from _helpers import (
    _esc, _esca, _short, _format_date_ru, _snapshot_time,
    _client_by_name, _load_chats, _load_all_tasks,
)
from _css import (
    DESIGN_TOKENS_CSS, OVERVIEW_SPECIFIC_CSS, CLIENT_DASHBOARD_CSS, NEW_JS_FRAGMENT,
)
from _loaders import (
    _DAEMON_DIAG, _set_diag, _log_once,
    load_daemon_finkoper, load_daemon_anomalies, load_daemon_mail,
    load_daemon_news, load_daemon_updates,
)
from _health import calculate_health
from _strings import t, WEEKDAYS, MONTHS_GEN
# _client_dashboard_v2 is imported inside the main loop (cycles via _overview_v2)
from _overview_shared import render_header, render_morning_digest


HERE = os.path.dirname(os.path.abspath(__file__))
# Config-driven paths: client data and the output directory come from _config
# (env ABA_DATA_DIR / ABA_DASHBOARD_DIR, default instances/example/...).
from _config import DATA_DIR, DASHBOARD_DIR
DATA_PATH = os.path.join(DATA_DIR, 'clients_data.json')  # legacy ref, not used in the current loading
OUT_DIR = DASHBOARD_DIR
os.makedirs(OUT_DIR, exist_ok=True)

# Data root (for client folders: history.jsonl, mental_model.md, etc.)
PLAN_DIR  = DATA_DIR

# Registries REMOVED (JSON-first refactor 2026-06-19): the consolidated calendar,
# UKEP registry and request log are no longer data sources. Deadlines + awaiting
# are aggregated from per-client state via _deadlines.collect_deadlines /
# collect_awaiting. The only remaining JSON snapshot is the finkoper daemon below.

# Daemon journal: missing dir/files → graceful degradation. JSON files named
# anomalies_<YYYY-MM-DD>.json / mail_... / news_... / updates_... + finkoper_state/.
DIARY_INBOX = os.path.join(DATA_DIR, 'journal', 'inbox')

# Clients are loaded from state via clients_index.json.
# clients_data.json is no longer the entry point — it is archived as clients_data.json.archived_*.
# All client information now lives only in state/*.json.
from _loaders import load_clients_from_index
clients = load_clients_from_index()
# load_clients_from_index() already calls all 8 apply_*_to_client (identity/regime/accounts/
# financials/counterparties/risks/behavior/tasks), so clients[] contains all fields
# (inn, regime, account, monthly_check→financials_v2.monthly_close, dismissed_anomalies,
# tasks_overrides, messengers, etc.) — from state as the source of truth.

# Time zones: the user works in Bali (UTC+8); the team and FTS deadlines are in MSK (UTC+3).
# TODAY = the Bali date (the user's working day). FTS / Tax Code deadlines are always in MSK.
try:
    from zoneinfo import ZoneInfo
    TZ_BALI = ZoneInfo('Asia/Makassar')  # WITA, UTC+8
    TZ_MSK = ZoneInfo('Europe/Moscow')   # MSK, UTC+3
    from datetime import datetime as _dt_with_tz
    _NOW_BALI = _dt_with_tz.now(TZ_BALI)
    _NOW_MSK = _dt_with_tz.now(TZ_MSK)
    TODAY = _NOW_BALI.date()
    TIME_BALI = _NOW_BALI.strftime('%H:%M')
    TIME_MSK = _NOW_MSK.strftime('%H:%M')
except ImportError:
    TODAY = date.today()
    TIME_BALI = ''
    TIME_MSK = ''
# Localized weekday / month-genitive arrays come from _strings (selected by LOCALE).
# Names kept as DAYS_RU / MONTHS_RU_GEN for backward compatibility with importers.
DAYS_RU = WEEKDAYS
MONTHS_RU_GEN = MONTHS_GEN
TODAY_HUMAN = f"{TODAY.day} {MONTHS_RU_GEN[TODAY.month-1]} {TODAY.year}, {DAYS_RU[TODAY.weekday()]}"
TODAY_SHORT = TODAY.strftime("%d.%m.%Y")
TODAY_ISO = TODAY.strftime("%Y-%m-%d")

def base_items_for_2026():
    # Each item has a unique task_id so that "my part is done" can be marked
    # via the client's state/financials.json → prep_done and removed from the dashboard's active list.
    # (prep_done_2026 in clients_data.json is no longer the source of truth).
    return [
        ("decl_usn_2025",     date(2026,4,27), "USN tax return", "USN tax return for 2025","Manager", "Prepare the tax return in 1C (status \"In progress\")"),
        ("notif_q1_2026",     date(2026,4,27), "ENP", "Notification of the USN advance for Q1 2026","Manager", "Calculate, prepare the notification in 1C (status \"In progress\")"),
        ("pay_q1_2026",       date(2026,4,28), "Payment", "Pay the USN tax for 2025 + USN advance Q1 2026","Client", "Create the ENP payment order in 1C"),
        ("contrib_1pct_2025", date(2026,7,1),  "Contributions", "1% over 300,000 ₽ for 2025","Client", "Calculate, payment order in 1C"),
        ("notif_h1_2026",     date(2026,7,27), "ENP", "Notification of the USN advance for H1 2026","Manager", "Calculate, prepare in 1C"),
        ("pay_h1_2026",       date(2026,7,28), "Payment", "USN advance H1 2026","Client", "Payment order in 1C"),
        ("notif_9m_2026",     date(2026,10,26),"ENP", "Notification of the USN advance for 9 months 2026","Manager", "Calculate, prepare in 1C"),
        ("pay_9m_2026",       date(2026,10,28),"Payment", "USN advance 9 months 2026","Client", "Payment order in 1C"),
        ("contrib_fixed_2026",date(2026,12,28),"Contributions", "Fixed SP insurance contributions 2026","Client", "Calculate, payment order in 1C"),
    ]

def shift_back(d):
    while d.weekday() >= 5: d -= timedelta(days=1)
    return d
def internal_dl(d): return shift_back(d - timedelta(days=5))
def fmt_short(d): return f"{d.day:02d}.{d.month:02d}"




NEW_CSS_FRAGMENT = (
    ".new-blocks{margin-bottom:24px}.new-blocks>section{margin-bottom:16px}"
    ".new-blocks h2 .badge{margin-left:8px;font-size:14px;font-weight:600;padding:2px 8px;border-radius:999px;background:#f3f4f6;color:#374151;vertical-align:middle}"
    ".empty-block{color:#9ca3af;font-style:italic;font-size:15px;margin:6px 0}"
    ".task-card{background:#fafafa;border:1px solid #e5e7eb;border-radius:8px;padding:10px 12px;margin-bottom:8px;box-shadow:0 1px 2px rgba(0,0,0,.02)}"
    ".task-card.status-overdue{border-color:#fca5a5;border-left:3px solid #ef4444}"
    ".task-card.status-soon{border-color:#fcd34d;border-left:3px solid #f59e0b}"
    ".task-card.status-normal{border-left:3px solid #e5e7eb}"
    ".task-card.status-unread{background:#eff6ff}"
    ".task-header{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-bottom:4px}"
    ".task-id{font-size:14px;color:#6b7280;font-variant-numeric:tabular-nums}"
    ".task-title{font-weight:600;font-size:15px;color:#1f2937;flex:1;min-width:200px}"
    ".badge-overdue{font-size:14px;font-weight:600;background:#fee2e2;color:#b91c1c;padding:2px 8px;border-radius:999px}"
    ".badge-soon{font-size:14px;font-weight:600;background:#fef3c7;color:#a16207;padding:2px 8px;border-radius:999px}"
    ".badge-unread{font-size:14px;font-weight:600;background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:999px}"
    ".task-meta{font-size:14px;color:#6b7280;margin-bottom:6px}"
    ".task-actions{display:flex;flex-wrap:wrap;gap:6px}"
    ".pending-item{background:#fafafa;border:1px solid #e5e7eb;border-radius:8px;padding:10px 12px;margin-bottom:8px}"
    ".pending-item.status-overdue{border-left:3px solid #ef4444}"
    ".pending-item.status-waiting{border-left:3px solid #f59e0b}"
    ".pending-text{font-size:15px;color:#1f2937}"
    ".pending-meta{font-size:14px;color:#6b7280;margin:4px 0 6px}"
    ".pending-actions{display:flex;gap:6px}"
    ".timeline-list{list-style:none;margin:0;padding:0}"
    ".timeline-item{display:grid;grid-template-columns:auto auto 1fr auto;gap:8px;align-items:start;padding:8px 10px;border-top:1px solid #f1f2f4;font-size:15px}"
    ".timeline-item:first-child{border-top:0}"
    ".timeline-item .time{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:#6b7280;font-size:14px;white-space:nowrap;padding-top:1px}"
    ".timeline-item .icon{font-size:14px;line-height:1.2}"
    ".timeline-item .title{color:#1f2937}"
    ".timeline-item details{grid-column:1/-1;font-size:15px;color:#4b5563;margin-top:4px}"
    ".timeline-item details summary{cursor:pointer;color:#6b7280;font-size:14px}"
    ".timeline-item .open-link{font-size:14px;color:#1e40af;text-decoration:none;white-space:nowrap}"
    ".timeline-item.severity-high{background:#fef2f2;border-left:3px solid #ef4444}"
    ".timeline-item.severity-medium{background:#fffbeb;border-left:3px solid #f59e0b}"
    ".timeline-item.severity-low,.timeline-item.severity-none{background:transparent;border-left:3px solid transparent}"
    ".anomaly-item{background:#fafafa;border:1px solid #e5e7eb;border-radius:8px;padding:10px 12px;margin-bottom:8px}"
    ".anomaly-item.severity-high{border-left:3px solid #ef4444}"
    ".anomaly-item.severity-medium{border-left:3px solid #f59e0b}"
    ".anomaly-item.severity-low{border-left:3px solid #d1d5db}"
    ".anomaly-header{font-size:15px;margin-bottom:4px}"
    ".anomaly-description{font-size:15px;color:#4b5563;margin-bottom:6px}"
    ".anomaly-item details{font-size:15px;color:#4b5563;margin-bottom:6px}"
    ".history-item{background:#fafafa;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;margin-bottom:6px}"
    ".history-item summary{cursor:pointer;font-size:15px;color:#1f2937}"
    ".history-date{font-family:ui-monospace,monospace;color:#6b7280;font-size:14px;margin-right:8px}"
    ".history-type-badge{font-size:14px;background:#e5e7eb;color:#374151;padding:1px 7px;border-radius:999px;margin-right:8px}"
    ".history-title{font-weight:600}"
    ".history-summary{font-size:15px;color:#4b5563;margin-top:6px}"
    ".history-full{font-size:14px;color:#4b5563;white-space:pre-wrap;font-family:inherit;background:#fff;border:1px solid #e5e7eb;border-radius:6px;padding:8px;margin-top:6px}"
    ".copy-btn{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border:1px solid #d1d5db;border-radius:6px;background:#f9fafb;cursor:pointer;font-size:15px;color:#1f2937;text-decoration:none;transition:all .15s}"
    ".copy-btn:hover{background:#e5e7eb;border-color:#9ca3af}"
    ".copy-tooltip{position:absolute;background:#10b981;color:#fff;padding:6px 12px;border-radius:6px;font-size:15px;z-index:1000;pointer-events:none;animation:fadeInOut 3s ease-in-out}"
    "@keyframes fadeInOut{0%,100%{opacity:0}15%,85%{opacity:1}}"
)



def print_summary():
    """Short summary for the regenerate daemon.
    Printed if --print-summary is in sys.argv.
    Contains 2 blocks: SOURCES (from _DAEMON_DIAG) and HEALTH (per client)."""
    print()
    print("=== " + t('SOURCES') + " ===")
    ICON_BY_STATUS = {'ok':'🟢', 'empty_unexpected':'🟡', 'missing':'🔴', 'error':'🔴'}
    for key in ('finkoper', 'mail', 'anomalies', 'news', 'updates'):
        info = _DAEMON_DIAG.get(key, {'status': 'missing', 'count': 0, 'detail': t('not started')})
        st = info['status']
        emoji = ICON_BY_STATUS.get(st, '🟡')
        print(f"{emoji} {key:<10} {st:<18} count={info['count']:<4} {info['detail']}")

    print()
    print("=== HEALTH ===")
    from _deadlines import collect_deadlines, collect_awaiting
    deadlines = collect_deadlines(TODAY)
    awaiting  = collect_awaiting(TODAY)
    df  = load_daemon_finkoper(DIARY_INBOX, TODAY)
    da  = load_daemon_anomalies(DIARY_INBOX, TODAY)
    icons = {'red':'🔴','yellow':'🟡','green':'🟢','grey':'⚪'}
    for c in clients:
        h = calculate_health(c, today=TODAY, daemon_finkoper=df, daemon_anomalies=da,
                             deadlines=deadlines, awaiting=awaiting)
        icon = icons.get(h['color'], '?')
        n = len(h['reasons'])
        first = h['reasons'][0] if h['reasons'] else '(' + t('no triggers') + ')'
        print(f"{icon} {h['color'].upper():<6} {c['name_short']:<22} {n} reasons: {_short(first, 70)}")


if __name__ == '__main__':
    # Auto-wake of deferred tracks (deferred + wake_date<=today → awaiting).
    # Must run BEFORE rendering: the renderers re-read tasks.json from disk.
    from _waker import wake_deferred_tracks
    _woken = wake_deferred_tracks(today=TODAY_ISO)
    if _woken:
        print(f'[waker] deferred tracks woken: {_woken}')
    _mail_all = load_daemon_mail(DIARY_INBOX, TODAY)
    _anom_all = load_daemon_anomalies(DIARY_INBOX, TODAY)


    from _client_dashboard_v2 import render_client_dashboard_v2
    for c in clients:
        out_path = os.path.join(OUT_DIR, f"dashboard_{c['id']}.html")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(render_client_dashboard_v2(c, daemon_mail=_mail_all, daemon_anomalies=_anom_all))
        print(f"OK: {c['name_short']} \u2192 {out_path}")

    from _overview_v2 import render_overview_v2
    ov_path = os.path.join(OUT_DIR, "dashboard_overview.html")
    with open(ov_path, 'w', encoding='utf-8') as f:
        f.write(render_overview_v2())
    print(f"OK: overview \u2192 {ov_path}")

    # Client pages \u2014 one per dynamic group (derived from the per-client `group`
    # field). No group list is hardcoded: a new `group` value in the index
    # produces a new clients_<slug>.html on the next run.
    from _clients_group import render_clients_group
    from _helpers import dynamic_groups, clients_in_group, _slugify_group
    for _g in dynamic_groups(clients):
        _slug = _slugify_group(_g)
        _grp_clients = clients_in_group(clients, _g)
        _g_path = os.path.join(OUT_DIR, f"clients_{_slug}.html")
        with open(_g_path, 'w', encoding='utf-8') as f:
            f.write(render_clients_group(_g, _grp_clients))
        print(f"OK: clients_{_slug} ({len(_grp_clients)}) \u2192 {_g_path}")

    # Plan — Today
    from _plan_today import render_plan_today
    pt_path = os.path.join(OUT_DIR, "plan_today.html")
    with open(pt_path, 'w', encoding='utf-8') as f:
        f.write(render_plan_today())
    print(f"OK: plan_today \u2192 {pt_path}")

    # Calendar (navigable; replaces the former Week/Month tabs)
    from _plan_month import render_calendar
    cal_path = os.path.join(OUT_DIR, "calendar.html")
    with open(cal_path, "w", encoding="utf-8") as f:
        f.write(render_calendar())
    print(f"OK: calendar \u2192 {cal_path}")

    # Periods — the monthly cycle by reporting period (stage progress)
    from _periods import render_periods
    per_path = os.path.join(OUT_DIR, "periods.html")
    with open(per_path, "w", encoding="utf-8") as f:
        f.write(render_periods())
    print(f"OK: periods \u2192 {per_path}")

    # "How to use" section
    from _guide import render_guide
    g_path = os.path.join(OUT_DIR, "guide.html")
    with open(g_path, 'w', encoding='utf-8') as f:
        f.write(render_guide())
    print(f"OK: guide \u2192 {g_path}")

    if '--print-summary' in sys.argv:
        print_summary()

    # === STATE LINT — invariant checks ===
    try:
        import state_lint, json as _json, datetime as _dt
        _viols = state_lint.lint_all()
        _errs = [v for v in _viols if v['severity'] == 'error']
        with open(os.path.join(HERE, '_LINT.json'), 'w', encoding='utf-8') as _f:
            _json.dump({'ts': _dt.datetime.now().isoformat(timespec='seconds'),
                        'errors': _errs,
                        'warns': [v for v in _viols if v['severity'] == 'warn']},
                       _f, ensure_ascii=False, indent=2)
        print('\n=== STATE LINT ===')
        state_lint.report(_viols)
        if _errs:
            print('\n❌ LINT FAILED: errors present — DO NOT PUBLISH (do not run cp _tmp_html/*.html ..), fix the links first.')
            sys.exit(2)
        print('✅ LINT OK — invariants satisfied, the dashboard can be published.')
    except SystemExit:
        raise
    except Exception as _e:
        print('⚠\ufe0f  LINT did not run (not blocking publication):', _e)
