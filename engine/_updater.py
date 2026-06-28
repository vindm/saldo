# -*- coding: utf-8 -*-
"""_updater.py — the in-dashboard "Update Saldo" affordance.

The version check runs INLINE in the engine: when `generate.py` renders, it asks
this module whether `origin` has commits the local checkout is missing (one
`git fetch` + a rev-list, run once per generate via the module cache below). If
so, a gold "Доступно обновление" item is emitted in the sidebar and the
`update.html` page shows what's new; otherwise nothing shows and the operator is
never nagged. No separate daemon, no status file — the dashboard reflects what
generate saw at render time.

The check is best-effort: any failure (offline, no SSH key, slow remote, not a
git checkout) degrades silently to "no update". Set ABA_SKIP_UPDATE_CHECK=1 to
skip the network entirely (useful for fast offline dev/CI runs).

The button itself does not update anything — it copies a fixed trigger prompt to
the clipboard for the operator to paste into the Cowork chat; the runtime then
runs the guarded, pause-for-OK upgrade (`connectors/update/SKILL.md`).
"""
import os
import subprocess

from _strings import t

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)               # the saldo/ engine checkout (git lives here)
_FETCH_TIMEOUT = 8                            # seconds; never hang a render on the network

# The fixed trigger phrase the button copies. Stable so it reliably matches the
# update workflow. Russian — the operator-facing surface is RU (locale boundary).
UPDATE_PROMPT_RU = (
    "Проверь обновления Saldo по workflow connectors/update/SKILL.md. "
    "Если есть новая версия — сделай резервную копию, скачай её, "
    "затем покажи мне, что именно изменится (новые версии, миграции данных), "
    "и ТОЛЬКО после моего «да» применяй обновление и миграции, пересобери "
    "дашборд, проверь, что всё работает, и отчитайся. Если миграция требует "
    "пошагового применения — веди её по одной."
)

# Computed once per process (generate renders ~20 pages → one git check, not 20).
_STATUS_CACHE = None


def _git(*args, capture=True, timeout=None):
    """Run a git command in the repo. Returns stdout (stripped) or None on any error."""
    try:
        r = subprocess.run(
            ["git", "-C", _REPO, *args],
            capture_output=capture, text=True, timeout=timeout,
            stdin=subprocess.DEVNULL,
            env=dict(os.environ, GIT_TERMINAL_PROMPT="0"),
        )
        if r.returncode != 0:
            return None
        return (r.stdout or "").strip() if capture else ""
    except Exception:
        return None


def _compute_status():
    """Do the actual git check. Returns the status dict (always a dict)."""
    status = {"available": False, "behind": 0, "current": None,
              "latest": None, "headline": ""}

    if os.environ.get("ABA_SKIP_UPDATE_CHECK"):
        return status
    if _git("rev-parse", "--is-inside-work-tree") != "true":
        return status

    # Fetch objects from origin (no working-tree change), bounded by a timeout.
    # capture=True keeps a failed fetch (offline, no key) quiet — it must not
    # pollute generate's output; we only care about the rev-list comparison.
    _git("fetch", "--quiet", "origin", timeout=_FETCH_TIMEOUT)

    branch = _git("rev-parse", "--abbrev-ref", "HEAD") or "HEAD"
    upstream = _git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if not upstream:
        upstream = "origin/" + branch

    behind_raw = _git("rev-list", "--count", "HEAD.." + upstream)
    try:
        behind = int(behind_raw)
    except (TypeError, ValueError):
        return status

    status["current"] = _git("rev-parse", "--short", "HEAD")
    status["latest"] = _git("rev-parse", "--short", upstream)
    status["behind"] = behind
    status["available"] = behind > 0
    if behind > 0:
        # Newest pending commit subject as a hint of what's coming.
        status["headline"] = _git("log", "-1", "--format=%s", upstream) or ""
    return status


def get_update_status():
    """Cached per-process update status. Computes the git check at most once."""
    global _STATUS_CACHE
    if _STATUS_CACHE is None:
        _STATUS_CACHE = _compute_status()
    return _STATUS_CACHE


def update_available():
    return bool(get_update_status().get("available"))


def render_update_sidebar_item(active=""):
    """Sidebar entry for the update page.

    Returns '' when no update is available (menu stays clean). When an update IS
    available, returns a gold call-to-action item with a "!" badge.
    """
    if not update_available():
        return ""
    cls = "sb-item sb-update" + (" active" if active == "update" else "")
    return (
        '<a class="' + cls + '" href="update.html">'
        '<span class="ico"></span>' + t("Update available") +
        '<span class="count">!</span></a>'
    )


def _whatsnew_html(status):
    bits = []
    headline = status.get("headline") or ""
    if headline:
        bits.append("<strong>" + t("What's new") + ":</strong> " + headline)
    meta = []
    if status.get("behind"):
        meta.append(t("commits behind") + ": " + str(status["behind"]))
    if status.get("latest"):
        meta.append(t("latest") + " " + str(status["latest"]))
    if meta:
        bits.append('<div style="margin-top:8px;color:#7a5e2a;font-size:14px">'
                    + " · ".join(meta) + "</div>")
    if not bits:
        return ""
    return '<div class="upd-whatsnew">' + "".join(bits) + "</div>"


def _js_str(s):
    return (s.replace("\\", "\\\\").replace('"', '\\"')
             .replace("\n", "\\n").replace("\r", ""))


# ── CSS for the sidebar entry + the update page ────────────────────────────
UPDATER_CSS = (
    ".sb-item.sb-update{border-left:3px solid #B79257;background:#FBF4E6;"
    "color:#6B4F1C;font-weight:600}"
    ".sb-item.sb-update:hover{background:#F4E8CC;color:#5A3F12}"
    ".sb-item.sb-update .count{background:#B79257;color:#fff;font-weight:700}"
    ".upd-wrap{max-width:720px}"
    ".upd-hero{background:#FBF4E6;border:1px solid #E7D3A6;border-radius:10px;"
    "padding:20px 22px;margin:4px 0 20px}"
    ".upd-hero h1{margin:0 0 6px;font-size:22px;color:#6B4F1C}"
    ".upd-hero .upd-sub{color:#7a5e2a;font-size:15px;margin:0}"
    ".upd-whatsnew{background:#fff;border:1px solid var(--border);"
    "border-radius:8px;padding:14px 18px;margin:0 0 18px;font-size:15px;"
    "line-height:1.5}"
    ".upd-whatsnew strong{color:#1F4E79}"
    ".upd-steps{font-size:15px;line-height:1.7;color:var(--text-secondary)}"
    ".upd-steps li{margin-bottom:4px}"
    ".upd-cta{display:flex;gap:10px;flex-wrap:wrap;align-items:center;"
    "margin:18px 0 10px}"
    ".upd-btn{padding:11px 20px;border:1px solid #B79257;background:#B79257;"
    "color:#fff;border-radius:6px;cursor:pointer;font-size:16px;font-weight:600;"
    "font-family:inherit;transition:background .15s}"
    ".upd-btn:hover{background:#9d7c45}"
    ".upd-ok{display:none;padding:11px 14px;background:#e8f3ec;color:#356544;"
    "border-radius:6px;margin-top:10px;font-size:15px;line-height:1.45}"
    ".upd-ok.active{display:block}"
    ".upd-ok strong{display:block;margin-bottom:3px}"
    ".upd-fallback{font-size:14px;color:var(--text-muted);margin-top:18px;"
    "padding-top:14px;border-top:1px solid var(--border);line-height:1.6}"
    ".upd-uptodate{background:#fff;border:1px solid var(--border);"
    "border-radius:8px;padding:22px;font-size:16px;color:var(--text-secondary)}"
)


def render_update_page():
    """Standalone 'Update Saldo' page. Mirrors the guide.html shell."""
    from generate import _esc, DESIGN_TOKENS_CSS, OVERVIEW_SPECIFIC_CSS
    from _overview_shared import render_header
    from _overview_v2 import OVERVIEW_V2_CSS
    from _sidebar import render_sidebar, SIDEBAR_CSS
    from _css import PROMPT_MODAL_CSS, PROMPT_MODAL_HTML, PROMPT_MODAL_JS

    status = get_update_status()
    head = render_header()
    title = t("Update Saldo")

    if status.get("available"):
        body = (
            '<div class="upd-hero">'
            '<h1>' + t("A new version of Saldo is available") + '</h1>'
            '<p class="upd-sub">'
            + t("Press the button below, then paste into the chat with the assistant. "
                "Nothing is changed until you confirm.") +
            '</p></div>'
            + _whatsnew_html(status) +
            '<p class="upd-steps">' + t("When you press the button, the assistant will:") + '</p>'
            '<ol class="upd-steps">'
            '<li>' + t("make a backup of your data") + '</li>'
            '<li>' + t("download the new engine version") + '</li>'
            '<li>' + t("show you exactly what will change and wait for your «yes»") + '</li>'
            '<li>' + t("apply the update, migrate your data, and rebuild the dashboard") + '</li>'
            '<li>' + t("check that everything works and report back") + '</li>'
            '</ol>'
            '<div class="upd-cta">'
            '<button id="upd-copy" class="upd-btn" type="button">'
            + t("Copy the update command") + '</button>'
            '</div>'
            '<div id="upd-ok" class="upd-ok">'
            '<strong>' + t("Copied.") + '</strong>'
            + t("Switch to the chat with the assistant, paste, and send.") +
            '</div>'
            '<div class="upd-fallback">'
            + t("If the button does not work, just write to the assistant: "
                "«обнови систему Saldo» — it knows what to do.") +
            '</div>'
        )
    else:
        body = (
            '<h1 class="page-title">' + t("Update Saldo") + '</h1>'
            '<div class="upd-uptodate">'
            + t("You are on the latest version. There is nothing to update right now. "
                "When a new version appears, an «Update available» item will "
                "show up in the menu on the left.") +
            '</div>'
        )

    script = (
        '<script>(function(){'
        'var btn=document.getElementById("upd-copy");'
        'if(!btn)return;'
        'var ok=document.getElementById("upd-ok");'
        'var PROMPT="' + _js_str(UPDATE_PROMPT_RU) + '";'
        'btn.addEventListener("click",function(){'
        'var tmp=document.createElement("textarea");tmp.value=PROMPT;'
        'tmp.style.position="fixed";tmp.style.left="-9999px";tmp.style.opacity="0";'
        'document.body.appendChild(tmp);tmp.focus();tmp.select();'
        'var done=false;try{done=document.execCommand("copy");}catch(e){done=false;}'
        'document.body.removeChild(tmp);'
        'if(done){ok.classList.add("active");}else{alert(PROMPT);}'
        '});'
        '})();</script>'
    )

    return (
        '<!DOCTYPE html>\n<html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>' + _esc(title) + '</title>'
        '<style>' + DESIGN_TOKENS_CSS + OVERVIEW_SPECIFIC_CSS + OVERVIEW_V2_CSS
        + SIDEBAR_CSS + PROMPT_MODAL_CSS + UPDATER_CSS + '</style>'
        '</head><body>'
        '<div class="layout-shell">'
        + render_sidebar(active='update')
        + '<main class="main-content"><div class="upd-wrap">'
        + head + body + script
        + '</div></main></div>'
        + PROMPT_MODAL_HTML + PROMPT_MODAL_JS
        + '</body></html>'
    )
