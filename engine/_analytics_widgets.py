"""_analytics_widgets.py — v3 (2026-05-24): stats-strip + top5 + deadlines.

All metrics computed on-the-fly. No scheduled reports.
Home page: light stats -> top-5 tasks today (+ button) -> all deadlines -> news.
Top-5, deadlines and stats are a single unified block; news lives separately in overview.
"""
import os
import re as _re
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from _strings import t, tp


def _today():
    try:
        import generate
        return generate.TODAY
    except Exception:
        return date.today()


def _parse_date(s):
    if not s:
        return None
    try:
        return date(*[int(x) for x in str(s).split("-")])
    except Exception:
        pass
    # DD.MM.YYYY
    try:
        parts = str(s).split(".")
        if len(parts) == 3:
            return date(int(parts[2]), int(parts[1]), int(parts[0]))
    except Exception:
        pass
    return None


def _close_date(t):
    """Date a track was closed, from structured fields only (no text matching).
    Prefers completed_at; falls back to the latest history entry date."""
    d = _parse_date(t.get("completed_at"))
    if d:
        return d
    hist_dates = [d for d in (_parse_date(ev.get("date")) for ev in (t.get("history") or [])) if d]
    return max(hist_dates) if hist_dates else None


# All statuses that mean a track is CLOSED (no longer in work). Kept in sync with
# _overview_shared.CLOSED_TRACK_STATUSES / _components. 'deferred' is snoozed (not
# closed and not active) — excluded from BOTH open and closed counts.
_CLOSED_STATUSES = {"done", "dropped", "dismissed", "completed", "cancelled", "resolved", "closed"}


def compute_progress_to_zero(all_tracks, window_days=7):
    today = _today()
    cutoff = today - timedelta(days=window_days)
    closed_recent = 0
    created_recent = 0
    open_count = 0
    closed_dates = set()
    for t in all_tracks:
        status = t.get("status")
        if (t.get("zone", "client_work") or "client_work") == "system_internal":
            continue
        if status in _CLOSED_STATUSES:
            d = _close_date(t)
            if d:
                if d >= cutoff:
                    closed_recent += 1
                closed_dates.add(d)
        elif status == "deferred":
            pass  # snoozed — neither open work nor a closure
        else:
            open_count += 1
        ca = _parse_date(t.get("created_at"))
        if ca and ca >= cutoff:
            created_recent += 1
    streak = 0
    cur = today
    while cur in closed_dates:
        streak += 1
        cur = cur - timedelta(days=1)
    closed_today = sum(1 for t in all_tracks if t.get("status") in _CLOSED_STATUSES
        and _close_date(t) == today)
    return {
        "open": open_count, "closed_recent": closed_recent, "created_recent": created_recent,
        "streak": streak, "closed_today": closed_today, "daily_goal": 5,
        "window_days": window_days,
    }


def find_stale_tracks(all_tracks, days_threshold=30):
    today = _today()
    cutoff = today - timedelta(days=days_threshold)
    stale = []
    for t in all_tracks:
        if t.get("status") not in ("active", "awaiting"):
            continue
        history = t.get("history") or []
        if not history:
            continue
        last_dates = [d for d in (_parse_date(ev.get("date")) for ev in history) if d]
        if not last_dates:
            continue
        last = max(last_dates)
        if last < cutoff:
            stale.append({**t, "days_stale": (today - last).days, "last_event_date": last.isoformat()})
    stale.sort(key=lambda x: -x["days_stale"])
    return stale


def upcoming_deadlines(all_tracks, window_days=30):
    today = _today()
    cutoff = today + timedelta(days=window_days)
    upcoming = []
    for t in all_tracks:
        if t.get("status") not in ("active", "awaiting"):
            continue
        due = _parse_date(t.get("due_date"))
        if due and today <= due <= cutoff:
            upcoming.append({**t, "days_left": (due - today).days})
    upcoming.sort(key=lambda x: x["days_left"])
    return upcoming


def overdue_tracks(all_tracks):
    today = _today()
    overdue = []
    for t in all_tracks:
        if t.get("status") not in ("active", "awaiting"):
            continue
        due = _parse_date(t.get("due_date"))
        if due and due < today:
            overdue.append({**t, "days_overdue": (today - due).days})
    overdue.sort(key=lambda x: -x["days_overdue"])
    return overdue


def suspicious_tracks(all_tracks):
    return []


def pending_decisions(journal_path):
    p = Path(journal_path)
    if not p.exists():
        return []
    txt = p.read_text(encoding="utf-8")
    entries = _re.split(r"\n(?=### \d{4}-\d{2}-\d{2})", txt)
    pending = []
    for entry in entries:
        if not entry.strip().startswith("### "):
            continue
        if _re.search(r"\*\*Status:\*\*\s*new\b", entry):
            head_match = _re.match(r"### ([^\n]+)", entry)
            if head_match:
                pending.append({"header": head_match.group(1)[:120], "snippet": entry[:300]})
    return pending


def compute_focus_top5(all_tracks, overdue, upcoming, max_count=5):
    """Top-5: overdue first (oldest), then today / 1-2 days out."""
    seen = set()
    result = []
    def _add(t):
        tid = t.get("id") or t.get("source_ref") or t.get("title", "")
        if tid in seen:
            return
        seen.add(tid)
        result.append(t)
    for t in overdue:
        _add(t)
        if len(result) >= max_count:
            return result
    for t in upcoming:
        if t.get("days_left", 99) <= 2:
            _add(t)
            if len(result) >= max_count:
                return result
    return result


def _esc(s):
    if not s:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_stats_strip(metrics, n_overdue, n_today):
    """Light stats in a single line."""
    streak_emoji = "🔥" if metrics["streak"] >= 3 else "⚡" if metrics["streak"] >= 1 else "·"
    return (
        '<section class="aw-stats">'
        '<a class="stat stat-link" href="plan_today.html"><span class="stat-num">{open_n}</span><span class="stat-lbl">' + t('Open items') + '</span></a>'
        '<div class="stat stat-red"><span class="stat-num">{ov}</span><span class="stat-lbl">' + t('Overdue') + '</span></div>'
        '<div class="stat stat-amber"><span class="stat-num">{td}</span><span class="stat-lbl">' + t('Due today') + '</span></div>'
        '<div class="stat stat-green"><span class="stat-num">{ct}</span><span class="stat-lbl">' + t('Closed today') + '</span></div>'
        '<div class="stat"><span class="stat-num">{streak_e} {streak}</span><span class="stat-lbl">' + t('Day streak') + '</span></div>'
        '</section>'
    ).format(
        open_n=metrics["open"], ov=n_overdue, td=n_today, ct=metrics["closed_today"],
        streak_e=streak_emoji, streak=metrics["streak"],
    )


def _tg_for_client_cached(client_id):
    """Returns the client's Telegram username by client_id."""
    try:
        import generate
        for c in generate.clients:
            if c.get("id") == client_id:
                msg = c.get("messengers") or {}
                return msg.get("telegram") or ""
    except Exception:
        pass
    return ""


def _esca(s):
    """HTML-escape for attributes: amp, quotes, < >."""
    if s is None:
        return ""
    return (str(s)
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", " "))


def _translate(s):
    """If _helpers._translate_tech_terms exists, try to translate; otherwise return as-is."""
    try:
        from _helpers import _translate_tech_terms
        return _translate_tech_terms(s or "")
    except Exception:
        return s or ""


def _track_data_attrs(t):
    """data-* attributes for the track modal — the SINGLE builder (canonical from state: assist, stale, context, history)."""
    from _track_attrs import build_track_data_attrs
    import generate, re as _re_an
    a = build_track_data_attrs(t, _esca, today=getattr(generate, 'TODAY', None),
                               tg_for=_tg_for_client_cached, track_type_for=None,
                               translate_fn=_translate)
    # drop data-track-type: overview widgets (Top-5 / deadlines / activity) are curated,
    # not filtered by the Team/Direct toggle
    return _re_an.sub(r'\s*data-track-type="[^"]*"', '', a)


def render_focus_top5_widget(focus, plan_today_url="plan_today.html", embedded=False):
    """Top-5 for today. Button -> Plan.Today."""
    if not focus:
        body = '<div class="aw-empty">' + t('Nothing urgent for today') + '</div>'
    else:
        rows = []
        for tk in focus:
            client = tk.get("client_name") or ""
            title = (tk.get("title") or "")[:100]
            if tk.get("days_overdue") is not None:
                badge_cls = "dl-overdue"
                badge_txt = t("overdue {}d").format(tk["days_overdue"])
            elif tk.get("days_left") == 0:
                badge_cls = "dl-today"; badge_txt = t("today")
            elif tk.get("days_left", 99) <= 2:
                badge_cls = "dl-soon"; badge_txt = t("in {}d").format(tk["days_left"])
            else:
                badge_cls = "dl-plan"; badge_txt = t("{}d").format(tk.get("days_left", "?"))
            attrs = _track_data_attrs(tk)
            rows.append(
                '<div class="aw-row aw-focus-row track-card-clickable"{a}>'
                '<span class="aw-dl-badge {bc}">{bt}</span>'
                '<span class="aw-text">{title}</span>'
                ' <span class="aw-client">— {client}</span>'
                '</div>'.format(a=attrs, bc=badge_cls, bt=_esc(badge_txt), title=_esc(title), client=_esc(client)))
        body = "".join(rows)
    if embedded:
        return (
            '<div class="brief-top5">'
            '<div class="brief-top5-head">' + tp('Top-5 today', 'Топ-5 на сегодня') + ' '
            '<a class="aw-link" href="{url}">' + t('→ full plan') + '</a></div>'
            '<div class="aw-body">{body}</div></div>'
        ).format(url=_esc(plan_today_url), body=body)
    return (
        '<div class="aw-widget aw-focus">'
        '<div class="aw-head">' + t('🎯 Top-5 for today') + ' '
        '<a class="aw-link" href="{url}">' + t('→ full plan') + '</a></div>'
        '<div class="aw-body">{body}</div></div>'
    ).format(url=_esc(plan_today_url), body=body)


def render_deadlines_widget(upcoming, overdue):
    """All deadlines: overdue + upcoming 30 days."""
    rows = []
    for tk in overdue:
        days = tk.get("days_overdue", 0)
        title = (tk.get("title") or "")[:100]
        client = tk.get("client_name") or ""
        attrs = _track_data_attrs(tk)
        rows.append(
            '<div class="aw-row track-card-clickable"{a}>'
            '<span class="aw-dl-badge dl-overdue">{badge}</span>'
            '<span class="aw-text">{t}</span>'
            ' <span class="aw-client">— {c}</span></div>'.format(a=attrs, badge=_esc(t("overdue {}d").format(days)), t=_esc(title), c=_esc(client)))
    for tk in upcoming:
        days = tk.get("days_left", 0)
        title = (tk.get("title") or "")[:100]
        client = tk.get("client_name") or ""
        if days == 0: cls, badge = "dl-today", t("today")
        elif days <= 3: cls, badge = "dl-soon", t("in {}d").format(days)
        elif days <= 7: cls, badge = "dl-week", t("in {}d").format(days)
        else: cls, badge = "dl-plan", t("{}d").format(days)
        attrs = _track_data_attrs(tk)
        rows.append(
            '<div class="aw-row track-card-clickable"{a}>'
            '<span class="aw-dl-badge {cls}">{b}</span>'
            '<span class="aw-text">{t}</span>'
            ' <span class="aw-client">— {c}</span></div>'.format(a=attrs, cls=cls, b=_esc(badge), t=_esc(title), c=_esc(client)))
    body = "".join(rows) if rows else '<div class="aw-empty">' + t('No deadlines') + '</div>'
    return (
        '<div class="aw-widget aw-deadlines">'
        '<div class="aw-head">' + t('📅 All deadlines') + ' <span class="aw-count">{ov} ' + t('overdue') + ' · {up} ' + t('ahead') + '</span></div>'
        '<div class="aw-body">{b}</div></div>'
    ).format(ov=len(overdue), up=len(upcoming), b=body)


# Legacy stubs
def render_health_widget(*a, **kw): return ""
def render_pending_widget(*a, **kw): return ""
def render_suspicious_widget(*a, **kw): return ""
def render_focus_widget(*a, **kw): return ""
def render_progress_widget(*a, **kw): return ""
def render_stale_widget(*a, **kw): return ""
def compute_focus_tracks(*a, **kw): return []


ANALYTICS_CSS = """
.mode-switch{display:inline-flex;gap:2px;padding:3px;background:var(--bg-page);
  border:1px solid var(--border);border-radius:8px;margin:0 0 var(--space-md);
  font-size:0}
.mode-btn{padding:5px 12px;font-size:15px;border:0;background:transparent;
  color:var(--text-secondary);cursor:pointer;border-radius:6px;
  font-family:inherit;font-weight:500;transition:all 120ms;
  display:inline-flex;align-items:center;gap:6px}
.mode-btn:hover{color:var(--text-primary)}
.mode-btn.active{background:var(--bg-card);color:var(--text-primary);
  box-shadow:0 1px 2px rgba(0,0,0,0.06),0 0 0 0.5px rgba(0,0,0,0.04)}
.mode-count{font-size:14px;color:var(--text-muted);font-weight:400;
  padding:1px 5px;background:var(--bg-page);border-radius:6px;line-height:1.4}
.mode-btn.active .mode-count{background:var(--bg-page);color:var(--text-secondary)}
body.mode-team [data-track-type="direct"]{display:none !important}
body.mode-direct [data-track-type="team"]{display:none !important}

/* === Light stats in a single line === */
.aw-stats{display:flex;gap:32px;padding:16px 20px;background:var(--bg-card);
  border:1px solid var(--border);border-radius:var(--radius-card);
  margin:0 0 14px;flex-wrap:wrap;align-items:flex-end}
.aw-stats .stat{display:flex;flex-direction:column;gap:3px;padding:0;
  border-right:none;min-width:0}
.aw-stats .stat-num{font-size:22px;font-weight:500;color:var(--text-primary);line-height:1}
.aw-stats a.stat-link{text-decoration:none;color:inherit;cursor:pointer}
.brief-top5{margin-top:14px;padding-top:12px;border-top:1px solid var(--border)}
.brief-top5-head{font-size:15px;font-weight:600;color:var(--text-secondary);margin-bottom:8px;display:flex;justify-content:space-between;align-items:baseline}
.aw-stats a.stat-link:hover .stat-num{color:var(--accent-blue)}
.aw-stats .stat-lbl{font-size:11.5px;color:var(--text-muted);text-transform:uppercase;
  letter-spacing:0.05em}
.aw-stats .stat-red .stat-num{color:var(--accent-red)}
.aw-stats .stat-amber .stat-num{color:var(--accent-yellow)}
.aw-stats .stat-green .stat-num{color:var(--accent-green)}

/* === Top-5 and Deadlines widgets === */
.aw-widget{background:var(--bg-card);border:1px solid var(--border);
  border-radius:var(--radius-card);box-shadow:none;padding:16px 20px;
  margin-bottom:14px}
.aw-head{font-size:var(--fs-h2,18px);font-weight:600;margin:0 0 12px;color:var(--text-primary);
  text-transform:none;letter-spacing:0;padding-bottom:var(--space-sm,8px);
  border-bottom:2px solid var(--border);
  display:flex;justify-content:space-between;align-items:baseline}
.aw-count{font-size:var(--fs-meta,13px);font-weight:500;color:var(--text-muted);text-transform:none;letter-spacing:0}
.aw-link{font-size:13px;font-weight:500;color:var(--accent-blue);text-decoration:none;
  text-transform:none;letter-spacing:0;padding:2px 6px;border-radius:6px;transition:all 120ms}
.aw-link:hover{color:var(--text-primary)}
.aw-body{font-size:14px;line-height:1.5}
.aw-empty{padding:10px 0;color:var(--text-muted);font-size:14px}
.aw-row{display:flex;align-items:flex-start;gap:8px;
  border-bottom:1px solid var(--border);cursor:pointer;transition:background 120ms;
  padding:9px 8px;margin:0 -8px;border-radius:6px}
.aw-row:last-child{border-bottom:none}
.aw-row:hover{background:var(--bg-page)}
.aw-text{color:var(--text-primary);flex:1;min-width:0}
.aw-client{color:var(--text-muted);font-size:15px;white-space:nowrap}
.aw-dl-badge{font-size:13px;padding:2px 9px;border-radius:6px;font-weight:600;
  white-space:nowrap;flex-shrink:0;min-width:84px;text-align:center}
.dl-overdue{background:var(--red-bg);color:var(--accent-red)}
.dl-today{background:var(--red-bg);color:var(--accent-red)}
.dl-soon{background:var(--yellow-bg);color:#8A6730}
.dl-week{background:var(--yellow-bg);color:#8A6730}
.dl-plan{background:var(--blue-bg);color:var(--accent-blue)}
  border-bottom:1px solid var(--border);font-size:15px;line-height:1.4;
  border-radius:4px;transition:background 120ms;margin:0 -8px}

"""



# Actions shown in the feed — icon + human-readable label.
# Keys are canonical English `kind` codes read straight from history[].kind.
from _icons import icon as _icon
_ACTION_LABELS = {
    "payment": ("service_payment", "Payment"),
    "filing": ("declaration", "Filed"),
    "reply": ("email_action_required", "Client replied"),
    "document": ("declaration", "Document"),
    "status_change": ("finkoper_recurring", "Status changed"),
    "note": ("pencil", "Note"),
    "decision": ("analysis", "Decision recorded"),
}


def _classify_event(ev):
    """Read the structured `kind` field of a history entry. JSON-first: no text
    classification. An event is meaningful iff it carries a non-null `kind`
    (a canonical English code, e.g. payment / filing / reply / document /
    status_change / note). Absent/None = noise — skip it."""
    kind = (ev or {}).get("kind")
    if not kind:
        return None
    return str(kind)


def recent_activity(all_tracks, journal_path, limit=15, decisions_only=False, window_days=14):
    """Feed of meaningful events: what was done/updated in client work.
    Uses the track title, not the raw event_text. Technical events are hidden."""
    items = []
    today = _today()
    horizon = today - timedelta(days=window_days)

    # 1) By tracks — the latest meaningful event
    #    (skipped when decisions_only: the new 'updated/closed tracks' zones own this)
    for t in (all_tracks if not decisions_only else []):
        history = t.get("history") or []
        cid = t.get("client_id") or ""
        cname = t.get("client_name") or ""
        title = (t.get("title") or "").strip()
        if not title:
            continue
        evs_dated = []
        for ev in history:
            d = _parse_date(ev.get("date"))
            if d and d >= horizon:
                evs_dated.append((d, ev))
        evs_dated.sort(key=lambda x: x[0], reverse=True)
        # First look for a real (non-auto) event, then auto as a fallback
        chosen_d, chosen_ev, chosen_kind = None, None, None
        for d, ev in evs_dated:
            kind = _classify_event(ev)
            if kind is None:
                continue
            if not ev.get("auto", False):
                # Real user action — take it immediately
                chosen_d, chosen_ev, chosen_kind = d, ev, kind
                break
            elif chosen_d is None:
                # Auto event as fallback — remember it but keep looking for a real one
                chosen_d, chosen_ev, chosen_kind = d, ev, kind
        if chosen_kind is not None:
            # Try to pull the real date out of the event text
            # (the updater often writes "21.05.2026: ..." or "2026-05-21 ..." but sets date=today)
            ev_text = chosen_ev.get("event", "") if chosen_ev else ""
            if chosen_ev:
                # Look for a full date YYYY-MM-DD or DD.MM.YYYY
                for m_date in _re.finditer(r"(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})", ev_text):
                    real_d = _parse_date(m_date.group(1))
                    if real_d and real_d < chosen_d:
                        chosen_d = real_d
                        break
                else:
                    # Look for DD.MM without a year — substitute the year from chosen_d
                    m2 = _re.search(r"(?<![\d.])((0?[1-9]|[12]\d|3[01])\.(0?[1-9]|1[0-2]))(?![\.\d])", ev_text)
                    if m2:
                        try:
                            real_d = date(chosen_d.year, int(m2.group(3)), int(m2.group(2)))
                            if real_d < chosen_d:
                                chosen_d = real_d
                        except Exception:
                            pass
            ic_name, action = _ACTION_LABELS.get(chosen_kind, ("finkoper_recurring", "Updated"))
            items.append({
                "date": chosen_d, "icon": _icon(ic_name), "kind": chosen_kind,
                "action": action, "title": title[:90],
                "client_id": cid, "client_name": cname,
                "track": t, "source": "track",
            })

    # 2) Decisions from per-client history.jsonl (kind=decision/significant) — REPLACES
    #    parsing of the decisions journal (retired 2026-06-07). journal_path is no longer read.
    try:
        import os as _os, json as _json, state_ops as _so
        cmap = {}
        for t in all_tracks:
            cid = t.get("client_id")
            if cid and cid not in cmap:
                cmap[cid] = t.get("client_name") or ""
        for cid, cname in cmap.items():
            folder = _so.CLIENT_FOLDERS.get(cid)
            if not folder:
                continue
            hp = _os.path.join(_so._PLAN_DIR, folder, "history.jsonl")
            if not _os.path.exists(hp):
                continue
            try:
                for line in open(hp, encoding="utf-8"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = _json.loads(line)
                    except Exception:
                        continue
                    d = _parse_date((rec.get("ts") or "")[:10])
                    if not d or d < horizon:
                        continue
                    summ = (rec.get("summary") or "").strip()
                    # JSON-first: surface only records explicitly typed as a
                    # human-facing decision (kind field) — no text blacklisting.
                    if not summ or rec.get("kind") not in ("decision", "significant"):
                        continue
                    items.append({
                        "date": d, "ts": rec.get("ts"), "icon": _icon('analysis'),
                        "kind": "decision", "action": "Decision recorded",
                        "title": summ[:90],
                        "client_id": cid, "client_name": cname or cid,
                        "track": None, "source": "history",
                    })
            except Exception:
                continue
    except Exception:
        pass

    items.sort(key=lambda x: x["date"], reverse=True)
    return items[:limit]


def _humanize_date(d, today):
    delta = (today - d).days
    if delta == 0: return t("today")
    if delta == 1: return t("yesterday")
    if delta < 7: return t("{}d ago").format(delta)
    if delta < 30: return t("{}w ago").format(delta // 7)
    return d.strftime("%d.%m")


def render_activity_widget(activity, max_show=10, show=5):
    """Latest decisions — rendered with the SAME shared event component as the
    recently-updated / recently-closed track lists (avatar + headline, right
    column: relative date). One component, one style."""
    today = _today()
    from _helpers import relative_when
    from _components import event_row, render_event_section
    # Dedup by (action, title, client, date)
    seen, order = {}, []
    for it in activity:
        key = (it.get("action", ""), it.get("title", ""), it["client_name"], it["date"].isoformat())
        if key in seen:
            seen[key]["count"] = seen[key].get("count", 1) + 1
        else:
            seen[key] = {**it, "count": 1}
            order.append(key)
    activity = [seen[k] for k in order][:max_show]
    if not activity:
        return ''
    rows = []
    for it in activity:
        when = relative_when(it.get("ts") or (it["date"].isoformat() if it.get("date") else ""), today)
        head = _esc(it.get("title", ""))
        cnt = it.get("count", 1)
        if cnt > 1:
            head += ' <span class="ev-when">×%d</span>' % cnt
        rows.append(event_row(it.get("client_name") or "", head, '', when, None, ''))
    return render_event_section(tp('📋 Latest decisions', '📋 Последние решения'),
                                rows, count=len(activity), show=show)


def render_widgets_split(clients_data_path, journal_path, calculate_health_func, clients,
                         calendar_rows=None, ukep_rows=None, requests_rows=None,
                         daemon_finkoper=None, daemon_anomalies=None):
    """Like render_all_widgets, but the three parts separately — for a custom ordering
    of home-page blocks (Stats / Top-5 / Recent updates placed around the brief)."""
    from _tracks import load_all_tracks
    all_tracks = load_all_tracks()
    metrics = compute_progress_to_zero(all_tracks, window_days=7)
    # "В работе" must match the plan: count the SAME action set the plan shows
    # (aggregate_tasks routes open-questions / waiting / risks out of the plan).
    try:
        import generate as _gen
        from _aggregator import aggregate_tasks as _agg
        metrics["open"] = len((_agg(_gen.TODAY) or {}).get("all", []))
    except Exception:
        pass
    upcoming = upcoming_deadlines(all_tracks, window_days=30)
    overdue = overdue_tracks(all_tracks)
    n_today = sum(1 for t in upcoming if t.get("days_left") == 0)
    focus = compute_focus_top5(all_tracks, overdue, upcoming, max_count=5)
    activity = recent_activity(all_tracks, journal_path, limit=40, decisions_only=True, window_days=30)
    return {
        "stats": render_stats_strip(metrics, len(overdue), n_today),
        "top5": render_focus_top5_widget(focus, embedded=True),
        "activity": render_activity_widget(activity),
    }


def render_all_widgets(clients_data_path, journal_path, calculate_health_func, clients,
                       calendar_rows=None, ukep_rows=None, requests_rows=None,
                       daemon_finkoper=None, daemon_anomalies=None):
    """Home v3: stats-strip + top-5 + full deadlines."""
    from _tracks import load_all_tracks
    all_tracks = load_all_tracks()
    metrics = compute_progress_to_zero(all_tracks, window_days=7)
    upcoming = upcoming_deadlines(all_tracks, window_days=30)
    overdue = overdue_tracks(all_tracks)
    # how many are due today (days_left==0)
    n_today = sum(1 for t in upcoming if t.get("days_left") == 0)
    focus = compute_focus_top5(all_tracks, overdue, upcoming, max_count=5)
    activity = recent_activity(all_tracks, journal_path, limit=40)
    return (
        render_stats_strip(metrics, len(overdue), n_today)
        + render_focus_top5_widget(focus)
        + render_activity_widget(activity)
    )
