"""_css.py — all CSS constants and JS fragments for overview/dashboard.

Extracted from generate.py as part of the decomposition refactor.
Imported by generate.py, _client_dashboard_v2.py, _overview_v2.py.
"""

from _strings import t

DESIGN_TOKENS_CSS = (
    ":root{"
    # Cool, neutral surfaces (Linear-grade).
    "--bg-page:#F6F7F9;--bg-card:#FFFFFF;--bg-canvas:#F6F7F9;--bg-subtle:#EEF1F4;"
    "--border:#E8EAEE;--border-strong:#D8DCE2;"
    "--text-primary:#15171C;--text-secondary:#565B66;--text-muted:#8A909C;"
    # Brand-navy accent system (S-tier v2). ONE accent = brand navy; gold is a
    # thin secondary; semantics muted. --accent-blue is repointed to navy so every
    # existing interactive use (buttons, links, focus, hovers) follows it.
    "--accent:#1F4E79;--accent-hover:#19405F;--accent-active:#143049;"
    "--accent-soft:#EAF1F7;--accent-soft-border:#CBDBEA;--accent-text:#1F4E79;"
    "--accent-blue:#1F4E79;--blue-bg:#EAF1F7;"
    "--gold:#B79257;--gold-soft:#F7F1E6;"
    # Semantic colours — muted/modern (health / severity / readiness / due).
    "--accent-red:#C24A3D;--accent-yellow:#A8782B;--accent-green:#3E8E5E;"
    "--red-bg:#FBEEEC;--yellow-bg:#F7F0E1;--green-bg:#E9F4ED;"
    "--font:'Inter','SF Pro Text',-apple-system,\"Segoe UI\",system-ui,sans-serif;"
    "--fs-base:15px;--fs-meta:13px;--fs-h2:22px;--fs-h1:28px;--fs-number:28px;--fs-number-large:40px;"
    "--space-xs:4px;--space-sm:8px;--space-md:16px;--space-lg:24px;--space-xl:32px;"
    "--radius-card:12px;--radius-btn:8px;--radius-badge:4px;"
    "--shadow-card:0 1px 2px rgba(16,16,26,0.04);"
    "--shadow-pop:0 6px 20px rgba(31,78,121,0.16);--transition:150ms ease;}"
    "*{box-sizing:border-box}"
    "@media(prefers-reduced-motion:reduce){*,*::before,*::after{transition-duration:0.01ms!important;animation-duration:0.01ms!important}}"
    "body{margin:0;padding:0;background:var(--bg-canvas);color:var(--text-primary);"
    "font-family:var(--font);font-size:var(--fs-base);line-height:1.6}"
    "a{color:inherit;text-decoration:none}a:hover{color:var(--accent-blue)}"
    "button:focus-visible,a:focus-visible,summary:focus-visible,.wave-toggle:focus-visible{"
    "outline:2px solid var(--accent);outline-offset:2px;border-radius:var(--radius-btn)}"
    ".card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-card);"
    "padding:var(--space-md);box-shadow:var(--shadow-card)}"
    ".muted{color:var(--text-muted)}.secondary{color:var(--text-secondary)}"
    ".meta{font-size:var(--fs-meta);color:var(--text-muted)}"
    # THE shared due-date badge (engine/_components.due_badge) — one definition,
    # used by the client hero and the plan rows. Relative + urgency-coloured.
    ".due-badge{flex-shrink:0;display:inline-block;font-size:12.5px;font-weight:600;"
    "border-radius:6px;padding:3px 9px;white-space:nowrap;font-variant-numeric:tabular-nums}"
    ".due-badge-overdue,.due-badge-today{background:var(--red-bg);color:var(--accent-red)}"
    ".due-badge-soon{background:var(--yellow-bg);color:var(--accent-yellow)}"
    ".due-badge-far{background:var(--bg-subtle);color:var(--text-secondary)}"
    # no deadline — clearly de-emphasised (muted, lighter weight)
    ".due-badge-none{background:var(--bg-subtle);color:var(--text-muted);font-weight:500}"

    # === Rich-badges and Risks ===
    ".rich-badges{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 4px}"
    ".rich-badge{font-size:15px;padding:2px 8px;border-radius:10px;"
    "background:var(--bg-subtle);color:var(--text-secondary);font-weight:500;letter-spacing:.02em}"
    ".rich-badge.prio-high{background:var(--red-bg);color:var(--accent-red);font-weight:600}"
    ".rich-badge.prio-low{background:var(--bg-subtle);color:var(--text-muted)}"
    ".rich-badge.blocked-by{background:var(--yellow-bg);color:var(--accent-yellow)}"
    ".rich-badge.comments{background:var(--green-bg);color:var(--accent-green)}"
    # .track-prio-high: overrides the existing ::before (no double border)
    # risks
    # Cap at 3 cards per row (wider = more informative): each column is at least
    # one-third of the row, so auto-fill never packs more than 3; on narrow
    # screens it falls back to fewer (min 340px).
    ".risks-grid{display:grid;grid-template-columns:repeat(auto-fill,"
    "minmax(max(340px,calc((100% - 2*var(--space-md)) / 3)),1fr));"
    "gap:var(--space-md);margin-bottom:var(--space-lg);align-items:start}"
    ".risk-card{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);padding:var(--space-md);border-left:4px solid var(--border);"
    "display:flex;flex-direction:column}"
    ".risk-card:hover{background:var(--bg-page)}"
    ".risk-card.risk-sev-red{border-left-color:var(--accent-red)}"
    ".risk-card.risk-sev-yellow{border-left-color:var(--accent-yellow)}"
    ".risk-card.risk-sev-green{border-left-color:var(--accent-green)}"
    ".risk-card.risk-sev-grey{border-left-color:var(--border)}"
    ".risk-head{display:flex;align-items:center;gap:8px;margin-bottom:4px}"
    ".risk-icon{font-size:16px}"
    ".risk-title{font-weight:600;font-size:14px;color:var(--text-primary)}"
    ".risk-meta{font-size:15px;color:var(--text-muted);text-transform:uppercase;"
    "letter-spacing:.04em;margin-bottom:6px}"
    ".risk-desc{font-size:15px;color:var(--text-secondary);line-height:1.5;margin:6px 0}"
    ".risk-next{font-size:15px;color:var(--text-primary);background:var(--accent-soft);"
    "padding:6px 10px;border-radius:6px;margin-top:8px}"
    ".risk-next::before{content:''}"
    # holds the shared clickable reference chips (.an-dep) — a calm flex row, not the
    # old monospace text. The chip's own -10px margin pulls the first one to the edge.
    ".risk-linked-tasks{margin-top:6px;display:flex;flex-wrap:wrap;align-items:center;gap:2px 4px}"
    ".risk-linked-label{font-size:13px;color:var(--text-muted);font-weight:500;margin-right:2px}"
    ".risk-linked-more{color:var(--text-muted);font-size:15px}"
    ".risk-law{font-size:15px;color:var(--accent-blue);margin-top:4px;font-style:italic}"
    ".risk-summary{cursor:pointer;list-style:none;display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 10px;flex:1 0 auto;align-content:flex-start}"
    ".risk-summary::-webkit-details-marker{display:none}"
    ".risk-summary::before{content:'▸';color:var(--text-muted);font-size:11px}"
    "details.risk-card[open]>.risk-summary::before{content:'▾'}"
    ".risk-next-inline{font-size:14px;color:var(--text-secondary);font-weight:400;flex:1 1 100%;min-width:0}"
    "details.risk-card:not([open])>.risk-summary>.risk-next-inline{display:-webkit-box;"
    "-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}"
    ".risk-body{margin-top:8px}"
    ".risks-derived{font-size:14px;color:var(--text-muted);background:var(--bg-card);"
    "border:1px dashed var(--border);border-radius:var(--radius-card);padding:8px 12px;margin-bottom:var(--space-lg)}"
    ".risks-resolved{margin:var(--space-md) 0 var(--space-lg);background:var(--bg-card);"
    "border:1px solid var(--border);border-radius:var(--radius-card);padding:var(--space-sm) var(--space-md)}"
    ".risks-resolved summary{cursor:pointer;font-size:15px;color:var(--text-muted);"
    "font-weight:500;padding:4px 0}"
    ".risk-resolved-item{font-size:15px;color:var(--text-secondary);padding:6px 0;"
    "border-bottom:1px dashed var(--border)}"
    ".risk-resolved-item:last-child{border-bottom:none}"
    ".risk-resolved-icon{color:var(--accent-green)}"
    ".risk-resolved-date{color:var(--text-muted)}"
    ".risk-resolved-by{font-size:15px;color:var(--text-muted);margin-top:2px}"

    # === Financials — Periods + Tax calendar (card/row language, matches roster) ===
    ".fin2-card{display:flex;flex-direction:column;background:var(--bg-card);"
    "border:1px solid var(--border);border-radius:var(--radius-card);overflow:hidden;margin-bottom:var(--space-lg)}"
    ".fin2-row{display:flex;align-items:center;gap:14px;padding:10px 16px;border-top:1px solid var(--border)}"
    ".fin2-row:first-child{border-top:none}"
    ".fin2-per{flex:0 0 128px;font-weight:600;color:var(--text-primary);font-size:14px;white-space:nowrap}"
    ".fin2-turn{flex:0 0 auto;min-width:150px;font-family:var(--font-mono,monospace);font-size:14px;color:var(--text-primary)}"
    ".fin2-tax{flex:1;min-width:0;color:var(--text-secondary);font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
    ".fin2-st{flex:0 0 auto;display:flex;align-items:center;gap:6px;margin-left:auto}"
    ".fin2-chip{font-size:12px;font-weight:500;padding:2px 9px;border-radius:var(--radius-badge);white-space:nowrap}"
    ".fin2-chip-neutral{background:var(--bg-subtle);color:var(--text-muted)}"
    ".fin2-chip-info{background:var(--blue-bg);color:var(--accent-blue)}"
    ".fin2-chip-ok{background:#E8F1EC;color:#2A6444}"
    ".fin2-chip-warn{background:#F6EEDD;color:#7A5A1F}"
    ".fin2-chip-bad{background:#F7ECEA;color:#97362B}"
    ".fin2-pace{font-size:13px;color:var(--text-muted);font-weight:500}"
    ".fin2-empty{color:var(--text-muted);font-size:14px;padding:12px 16px}"
    ".fin2-cal .cal2-row{padding:11px 16px}"
    ".fin2-cal details.cal2-more{margin-top:0;border-top:1px solid var(--border)}"
    ".fin2-cal details.cal2-more>summary{padding:9px 16px}"
    ".fin2-head{padding-top:8px;padding-bottom:8px;background:var(--bg-subtle)}"
    ".fin2-head span{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--text-muted);font-weight:500}"
    ".fin2-muted{color:var(--text-muted)}"
    ".fin2-note{font-size:12.5px;color:var(--text-muted);line-height:1.5;margin:7px 2px 0}"
    # Compact tax calendar — grouped by date, near-deadlines only (later/past collapse)
    ".cal2{display:flex;flex-direction:column}"
    ".cal2-row{display:flex;gap:18px;padding:9px 2px;border-top:1px solid var(--border)}"
    ".cal2-row:first-child{border-top:none}"
    ".cal2-date{flex:0 0 96px;color:var(--accent-blue);font-weight:500;font-size:14px}"
    ".cal2-date.cal2-soon{color:var(--accent-red,#C24A3D)}"
    ".cal2-items{flex:1;display:flex;flex-direction:column;gap:6px;min-width:0}"
    ".cal2-item{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}"
    ".cal2-what{color:var(--text-primary);font-size:14px}"
    ".cal2-amt{font-family:var(--font-mono,monospace);font-size:13px;color:var(--text-secondary)}"
    ".cal2-task{color:var(--text-muted);font-size:13px;margin-left:auto;white-space:nowrap}"
    "details.cal2-more{margin-top:8px}"
    "details.cal2-more>summary{cursor:pointer;list-style:none;font-size:14px;color:var(--text-muted);font-weight:500;padding:4px 0}"
    "details.cal2-more>summary::-webkit-details-marker{display:none}"
    "details.cal2-more>summary::before{content:'\\25B8 ';color:var(--text-muted);font-size:11px}"
    "details.cal2-more[open]>summary::before{content:'\\25BE '}"
    # Counterparties
    ".cp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));"
    "gap:var(--space-md);margin-bottom:var(--space-lg)}"
    ".cp-card{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);padding:var(--space-md)}"
    ".cp-name{font-weight:600;font-size:14px;color:var(--text-primary);margin-bottom:4px}"
    ".cp-meta{font-size:15px;color:var(--text-muted);text-transform:uppercase;"
    "letter-spacing:.04em;margin-bottom:8px}"
    ".cp-inn{font-size:15px;color:var(--text-secondary);margin-bottom:6px}"
    ".cp-inn code{font-family:var(--font-mono,monospace);background:var(--bg-subtle);padding:2px 6px;border-radius:4px;font-size:15px}"
    ".cp-req{font-size:15px;color:var(--text-secondary);margin:6px 0;padding:6px 10px;"
    "background:var(--bg-subtle);border-radius:6px}"
    ".cp-tags{display:flex;gap:4px;flex-wrap:wrap;margin:6px 0}"
    ".cp-tag{font-size:15px;padding:2px 8px;border-radius:10px;background:var(--green-bg);"
    "color:var(--accent-green);font-weight:500}"
    ".cp-notes{font-size:15px;color:var(--text-secondary);line-height:1.5;margin-top:8px;"
    "padding-top:8px;border-top:1px dashed var(--border)}"
    ".cp-linked{font-size:15px;color:var(--text-muted);margin-top:6px;font-family:var(--font-mono,monospace)}"
    ".cp-linked code{background:var(--bg-subtle);padding:1px 5px;border-radius:3px}"
    # the linked-TASKS line holds shared clickable chips (.an-dep) — drop the
    # monospace and lay the «tasks:» label + chips out as a calm flex row.
    ".cp-linked-tasks{font-family:inherit;display:flex;flex-wrap:wrap;align-items:center;gap:2px 6px}"

    # === UX fix #1: Focus-band (what matters today) ===
    ".focus-band{background:linear-gradient(135deg,var(--yellow-bg),#F8E5C8);"
    "border:1px solid #E8C99E;border-radius:var(--radius-card);"
    "padding:var(--space-md);margin:0 0 var(--space-lg)}"
    ".focus-band-label{font-size:15px;text-transform:uppercase;letter-spacing:.06em;"
    "color:var(--accent-yellow);font-weight:600;margin-bottom:8px}"
    ".focus-band-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px}"
    ".focus-card{background:rgba(255,255,255,.7);border-radius:8px;padding:8px 10px;"
    "border:1px solid rgba(232,201,158,.5)}"
    ".focus-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px}"
    ".focus-icon{font-size:14px}"
    ".focus-tag{font-size:15px;text-transform:uppercase;letter-spacing:.04em;"
    "color:var(--accent-yellow);font-weight:600;background:rgba(232,201,158,.4);"
    "padding:2px 6px;border-radius:8px}"
    ".focus-title{font-size:15px;font-weight:600;color:var(--text-primary);line-height:1.3;margin-bottom:2px}"
    ".focus-sub{font-size:15px;color:var(--text-secondary);line-height:1.4}"
    # === UX fix #2: track-card border color by priority/status ===
    # Priority/status override via ::before (no double border with severity)
    ".track-card.track-prio-high::before{background:var(--accent-red)!important;width:4px}"
    ".track-card[data-track-status*=\"WAITING\"]::before{background:var(--accent-blue)!important;width:4px}"
    # snapshot-list: support for <b> from _md_bold
    ".snapshot-list .row b{color:var(--text-primary);font-weight:600}"

    # === client-tagline (UX-fix: business description under the name) ===
    ".client-tagline{font-size:15px;color:var(--text-secondary);"
    "margin-top:6px;font-style:italic;line-height:1.4;max-width:680px}"
    ".meta-label{color:var(--text-muted);font-size:15px;text-transform:uppercase;letter-spacing:.04em;font-weight:500}"

    # === UX-fix #6: Accounts + Behavior ===
    ".acc-section{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);padding:16px 20px;margin-bottom:14px}"
    ".acc-block-title{font-size:15px;text-transform:uppercase;letter-spacing:.04em;"
    "color:var(--text-muted);font-weight:500;margin:var(--space-md) 0 6px}"
    ".acc-section > .acc-block-title:first-child{margin-top:0}"
    ".acc-row{background:transparent;border:none;border-bottom:1px solid var(--border);"
    "border-radius:0;padding:9px 2px;margin-bottom:0;font-size:15px;"
    "color:var(--text-secondary);display:flex;align-items:center;gap:8px;flex-wrap:wrap}"
    ".acc-row:last-child{border-bottom:none}"
    ".acc-row.acc-st-closed{opacity:.5}"
    ".acc-bank{font-weight:500;color:var(--text-primary)}"
    ".acc-num{font-family:var(--font-mono,monospace);font-size:15px;color:var(--text-primary);"
    "background:var(--bg-subtle);padding:2px 6px;border-radius:4px}"
    ".acc-bik{font-family:var(--font-mono,monospace);font-size:15px;color:var(--text-muted)}"
    ".acc-purpose{font-size:15px;color:var(--text-muted)}"
    ".acc-status{font-size:15px;text-transform:uppercase;color:var(--accent-yellow);font-weight:500}"
    ".acc-note{font-size:15px;color:var(--text-secondary);background:var(--bg-subtle);"
    "padding:6px 10px;border-radius:6px;margin-top:4px;width:100%;font-style:italic}"
    # Behavior
    ".beh-section{margin-bottom:var(--space-lg);background:var(--bg-card);"
    "border:1px solid var(--border);border-radius:var(--radius-card);padding:var(--space-md)}"
    ".beh-block{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}"
    ".beh-ch-primary{font-size:15px;font-weight:600;background:var(--yellow-bg);"
    "padding:4px 10px;border-radius:14px;color:var(--accent-yellow)}"
    ".beh-ch-secondary{font-size:15px;background:var(--bg-subtle);padding:3px 8px;"
    "border-radius:12px;color:var(--text-secondary)}"
    ".beh-tz{font-size:15px;color:var(--text-muted);padding:3px 8px}"
    ".beh-style{font-size:15px;color:var(--text-secondary);margin-bottom:8px}"
    ".beh-style b{color:var(--text-primary)}"
    ".beh-note{font-size:15px;color:var(--text-secondary);font-style:italic;line-height:1.5;margin-bottom:8px}"
    ".beh-prefs{display:flex;flex-direction:column;gap:4px;font-size:15px}"
    ".beh-likes{color:var(--accent-green)}"
    ".beh-dislikes{color:#8B4F3C}"
    ".beh-asks{color:var(--text-secondary);background:var(--bg-subtle);padding:6px 10px;border-radius:6px;margin-top:4px}"

    # === client-actions row: one "Разобрать" (tm-btn-outline) + the report link ===
    # The separate Dictate button was dropped (dictation lives in the shared modal).
    ".client-actions{display:flex;gap:10px;margin-top:20px}"

    # === UX-fix #8: unified button design system (tm-btn-*) ===
    # Used everywhere: client header, track modal, any future action zone.
    # Sizes chosen for accessibility (15px font, 12+22 padding — older users).
    ".tm-btn{padding:12px 22px;font-size:15px;border:1px solid var(--border);"
    "background:var(--bg-card);color:var(--text-primary);border-radius:var(--radius-btn);"
    "cursor:pointer;font-weight:500;font-family:inherit;"
    "transition:background var(--transition,.15s),border-color var(--transition,.15s),color var(--transition,.15s);"
    # line-height + text-decoration normalised so the class renders IDENTICALLY on
    # <button> and <a> (a <button> defaults to line-height:normal, an <a> inherits
    # the body's 1.6 — without this they'd be different heights).
    "display:inline-flex;align-items:center;justify-content:center;gap:6px;"
    "line-height:1.2;text-decoration:none;vertical-align:middle}"
    # SIZE modifiers — size is a modifier on the one base, never a per-instance
    # override. Default (no class) = medium. Color modifiers below change only
    # colour, never size; the two axes compose (e.g. tm-btn tm-btn-outline tm-btn-sm).
    ".tm-btn-sm{padding:8px 14px;font-size:13px}"
    ".tm-btn-lg{padding:14px 26px;font-size:16px}"
    ".tm-btn:hover{border-color:var(--accent-blue);background:var(--blue-bg);color:var(--accent-blue)}"
    # primary-outline: accent border + accent text, light fill — highlighted but
    # not heavy. The shared look for every "Разобрать" action across the app.
    # Compound selector (.tm-btn.tm-btn-outline) so it outranks any later plain
    # .tm-btn{border:…} rule that would otherwise reset the accent border.
    ".tm-btn.tm-btn-outline{border-color:var(--accent);color:var(--accent)}"
    ".tm-btn.tm-btn-outline:hover{border-color:var(--accent);background:var(--accent-soft);color:var(--accent-text)}"
    ".tm-btn-primary{background:var(--accent);color:#fff;border-color:var(--accent)}"
    ".tm-btn-primary:hover{background:var(--accent-hover);color:#fff;border-color:var(--accent-hover)}"
    ".tm-btn-success{background:var(--accent-green);color:#fff;border-color:var(--accent-green)}"
    ".tm-btn-success:hover{background:#557546;color:#fff;border-color:#557546}"
    ".tm-btn-warn{background:var(--accent-yellow);color:#fff;border-color:var(--accent-yellow)}"
    ".tm-btn-warn:hover{background:#b8893a;color:#fff;border-color:#b8893a}"
    ".tm-btn-tg{background:#2AABEE;color:#fff;border-color:#2AABEE}"
    ".tm-btn-tg:hover{background:#1a8fc7;color:#fff;border-color:#1a8fc7}"

    # === UX-fix #9: req-section consistent with the other sections ===
    ".req-section{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);padding:16px 20px;margin-bottom:14px}"
    ".cal-task-title{font-size:15px;color:var(--accent-blue)}"
)

OVERVIEW_SPECIFIC_CSS = (
    ".page-header{display:flex;justify-content:space-between;align-items:baseline;"
    "margin-bottom:var(--space-lg);padding-bottom:var(--space-md);border-bottom:1px solid var(--border)}"
    ".page-header h1{font-size:var(--fs-h1);font-weight:500;margin:0}"
    ".page-header .status-line{font-size:var(--fs-meta);color:var(--text-secondary);"
    "display:flex;gap:var(--space-md);align-items:center}"
    ".source-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin:0 1px}"
    ".source-dot.ok{background:var(--accent-green)}"
    ".source-dot.empty{background:var(--accent-yellow)}"
    ".source-dot.missing{background:var(--accent-red)}"
    ".source-dot[title]:hover{cursor:help}"
    ".priorities{display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--space-md);margin-bottom:var(--space-lg)}"
    ".priority-column{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);padding:var(--space-md);min-height:200px}"
    ".priority-column.urgent{border-top:3px solid var(--accent-red)}"
    ".priority-column.week{border-top:3px solid var(--accent-yellow)}"
    ".priority-column.replies{border-top:3px solid var(--accent-blue)}"
    ".priority-column h2{font-size:var(--fs-h2);font-weight:500;margin:0 0 var(--space-md);"
    "display:flex;justify-content:space-between;align-items:baseline}"
    ".priority-column h2 .count{font-size:var(--fs-meta);color:var(--text-muted);font-weight:400}"
    ".priority-item{padding:var(--space-sm) 0;border-bottom:1px solid var(--border);"
    "display:flex;justify-content:space-between;gap:var(--space-sm);align-items:flex-start}"
    ".priority-item:last-child{border-bottom:none}"
    ".priority-item .text{flex:1;cursor:pointer}"
    ".priority-item .text:hover{color:var(--accent-blue)}"
    ".priority-item .text strong{font-weight:500}"
    ".priority-item .meta-row{font-size:var(--fs-meta);color:var(--text-muted);margin-top:2px}"
    ".priority-item .external-link{flex-shrink:0;color:var(--text-muted);font-size:14px;"
    "padding:2px 4px;border-radius:var(--radius-btn)}"
    ".priority-item .external-link:hover{background:var(--bg-page);color:var(--accent-blue)}"
    ".empty-state{color:var(--text-muted);font-size:var(--fs-meta);font-style:normal;"
    "padding:var(--space-md) 0;text-align:center}"
    ".empty-state.success{color:var(--accent-green)}"
    ".clients-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--space-md);margin-bottom:var(--space-lg)}"
    "@media(max-width:1000px){.clients-grid{grid-template-columns:repeat(2,1fr)}}"
    ".client-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-card);"
    "padding:var(--space-md);position:relative;overflow:hidden;"
    "transition:transform var(--transition),box-shadow var(--transition)}"
    ".client-card:hover{transform:translateY(-2px);box-shadow:0 2px 8px rgba(0,0,0,0.06)}"
    ".client-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:4px}"
    ".client-card.health-red::before{background:var(--accent-red)}"
    ".client-card.health-yellow::before{background:var(--accent-yellow)}"
    ".client-card.health-green::before{background:var(--accent-green)}"
    ".client-card.health-grey::before{background:var(--border)}"
    ".client-card h3{font-size:var(--fs-base);font-weight:500;margin:0 0 var(--space-md);padding-left:var(--space-sm)}"
    ".client-counters{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-xs) var(--space-md);"
    "margin-bottom:var(--space-md);font-size:var(--fs-meta);color:var(--text-secondary);padding-left:var(--space-sm)}"
    ".client-counter{display:flex;align-items:center;gap:var(--space-xs)}"
    ".client-counter strong{color:var(--text-primary);font-weight:500}"
    ".client-deadline{font-size:var(--fs-meta);color:var(--text-secondary);"
    "padding-top:var(--space-sm);border-top:1px solid var(--border);margin-bottom:var(--space-md);"
    "padding-left:var(--space-sm)}"
    ".client-deadline .date{color:var(--accent-red);font-weight:500}"
    ".client-card a.open-dashboard{display:inline-block;font-size:var(--fs-meta);color:var(--accent-blue);"
    "padding:var(--space-xs) var(--space-sm);border:1px solid var(--border);border-radius:var(--radius-btn);"
    "transition:background var(--transition);margin-left:var(--space-sm)}"
    ".client-card a.open-dashboard:hover{background:var(--bg-page)}"
    ".digest{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-card)}"
    ".digest summary{padding:var(--space-md);cursor:pointer;font-size:var(--fs-h2);font-weight:500;list-style:none}"
    ".digest summary::-webkit-details-marker{display:none}"
    ".digest summary::after{content:' \\25BC';color:var(--text-muted);font-size:var(--fs-meta)}"
    ".digest[open] summary::after{content:' \\25B2'}"
    ".digest-content{padding:0 var(--space-md) var(--space-md);"
    "display:grid;grid-template-columns:1fr 1fr 1fr;gap:var(--space-lg)}"
    "@media(max-width:1000px){.digest-content{grid-template-columns:1fr}}"
    ".digest-block h4{font-size:var(--fs-meta);text-transform:uppercase;letter-spacing:0.5px;"
    "color:var(--text-muted);margin:0 0 var(--space-sm);font-weight:500}"
    ".digest-item{padding:var(--space-xs) 0;font-size:var(--fs-meta);color:var(--text-secondary);"
    "border-bottom:1px solid var(--border)}"
    ".digest-item:last-child{border-bottom:none}"
)

CLIENT_DASHBOARD_CSS = (
    ".client-header{display:flex;justify-content:space-between;align-items:flex-start;"
    "margin-bottom:var(--space-lg);padding-bottom:var(--space-md);border-bottom:1px solid var(--border)}"
    ".client-header .breadcrumb{font-size:var(--fs-meta);color:var(--text-muted);margin-bottom:var(--space-xs)}"
    ".client-header .breadcrumb a:hover{color:var(--accent-blue)}"
    ".client-header h1{font-size:var(--fs-h1);font-weight:500;margin:0}"
    ".client-header .health-indicator{display:inline-block;width:12px;height:12px;border-radius:50%;"
    "margin-right:var(--space-sm);vertical-align:middle}"
    ".client-header .health-red{background:var(--accent-red)}"
    ".client-header .health-yellow{background:var(--accent-yellow)}"
    ".client-header .health-green{background:var(--accent-green)}"
    ".client-header .health-grey{background:var(--border)}"
    ".client-header .meta-info{font-size:var(--fs-meta);color:var(--text-secondary);text-align:right}"
    ".client-content{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-md);align-items:start}"
    "@media(max-width:1100px){.client-content{grid-template-columns:1fr}}"
    ".block{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-card);"
    "padding:var(--space-md);box-shadow:var(--shadow-card)}"
    ".block h2{font-size:var(--fs-h2);font-weight:500;margin:0 0 var(--space-md);"
    "display:flex;justify-content:space-between;align-items:baseline}"
    ".block h2 .count{font-size:var(--fs-meta);color:var(--text-muted);font-weight:400}"
    ".block.full-width{grid-column:1/-1}"
    ".btn{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;font-size:var(--fs-meta);"
    "border:1px solid var(--border);border-radius:var(--radius-btn);background:var(--bg-page);"
    "color:var(--text-primary);cursor:pointer;font-family:inherit;transition:all var(--transition);"
    "text-decoration:none}"
    ".btn:hover{border-color:var(--accent-blue);color:var(--accent-blue)}"
    ".btn-icon{padding:4px 8px}"
    ".task-item{padding:var(--space-md);border:1px solid var(--border);border-radius:var(--radius-btn);"
    "margin-bottom:var(--space-sm);background:var(--bg-card)}"
    ".task-item.status-overdue{border-left:3px solid var(--accent-red)}"
    ".task-item.status-soon{border-left:3px solid var(--accent-yellow)}"
    ".task-item.status-unread{background:var(--blue-bg)}"
    ".task-item:last-child{margin-bottom:0}"
    ".task-header{display:flex;justify-content:space-between;gap:var(--space-sm);"
    "align-items:baseline;margin-bottom:var(--space-xs)}"
    ".task-id{font-family:ui-monospace,monospace;color:var(--text-muted);font-size:var(--fs-meta)}"
    ".task-title{font-weight:500;flex:1}"
    ".task-badges{display:flex;gap:var(--space-xs)}"
    ".task-badge{display:inline-block;padding:2px 6px;border-radius:var(--radius-badge);"
    "font-size:var(--fs-meta);font-weight:500}"
    ".badge-overdue{background:var(--red-bg);color:var(--accent-red)}"
    ".badge-soon{background:var(--yellow-bg);color:var(--accent-yellow)}"
    ".badge-unread{background:var(--blue-bg);color:var(--accent-blue)}"
    ".task-meta{font-size:var(--fs-meta);color:var(--text-muted);margin-bottom:var(--space-sm)}"
    ".task-actions{display:flex;gap:var(--space-xs)}"
    ".pending-item{padding:var(--space-sm) 0;border-bottom:1px solid var(--border)}"
    ".pending-item:last-child{border-bottom:none}"
    ".pending-item.status-overdue .pending-dot{color:var(--accent-red)}"
    ".pending-item.status-waiting .pending-dot{color:var(--accent-yellow)}"
    ".pending-text{margin-bottom:var(--space-xs)}"
    ".pending-meta{font-size:var(--fs-meta);color:var(--text-muted);margin-bottom:var(--space-sm)}"
    ".timeline-item{display:flex;gap:var(--space-sm);padding:var(--space-sm) 0;"
    "border-bottom:1px solid var(--border);align-items:flex-start}"
    ".timeline-item:last-child{border-bottom:none}"
    ".timeline-time{flex-shrink:0;width:80px;font-family:ui-monospace,monospace;"
    "font-size:var(--fs-meta);color:var(--text-muted)}"
    ".timeline-icon{flex-shrink:0;width:24px;font-size:14px}"
    ".timeline-body{flex:1}"
    ".timeline-title{font-weight:400}"
    ".timeline-detail{font-size:var(--fs-meta);color:var(--text-secondary);margin-top:2px}"
    ".timeline-item.severity-high{background:var(--red-bg);"
    "margin:0 calc(-1 * var(--space-md));padding-left:var(--space-md);padding-right:var(--space-md)}"
    ".timeline-item.severity-medium{background:var(--yellow-bg);"
    "margin:0 calc(-1 * var(--space-md));padding-left:var(--space-md);padding-right:var(--space-md)}"
    ".anomaly-item{padding:var(--space-sm) 0;border-bottom:1px solid var(--border)}"
    ".anomaly-item:last-child{border-bottom:none}"
    ".anomaly-header{font-weight:500;margin-bottom:var(--space-xs)}"
    ".anomaly-description{font-size:var(--fs-meta);color:var(--text-secondary);margin-bottom:var(--space-sm)}"
    ".anomaly-item.severity-high .anomaly-header{color:var(--accent-red)}"
    ".anomaly-item.severity-medium .anomaly-header{color:var(--accent-yellow)}"
    ".anomaly-item details{font-size:var(--fs-meta);margin-bottom:var(--space-sm)}"
    ".anomaly-item details summary{cursor:pointer;color:var(--text-muted)}"
    ".anomaly-item details p{margin:var(--space-xs) 0;color:var(--text-secondary)}"
    ".history-item{border-bottom:1px solid var(--border);padding:var(--space-sm) 0}"
    ".history-item:last-child{border-bottom:none}"
    ".history-item summary{cursor:pointer;list-style:none;display:flex;gap:var(--space-sm);align-items:baseline}"
    ".history-item summary::-webkit-details-marker{display:none}"
    ".history-date{font-family:ui-monospace,monospace;font-size:var(--fs-meta);"
    "color:var(--text-muted);width:90px;flex-shrink:0}"
    ".history-type{font-size:var(--fs-meta);padding:2px 6px;background:var(--bg-page);"
    "border-radius:var(--radius-badge);color:var(--text-secondary);flex-shrink:0}"
    ".history-title{font-weight:400}"
    ".history-content{padding:var(--space-sm) 0 var(--space-sm) 100px;"
    "font-size:var(--fs-meta);color:var(--text-secondary)}"
    ".history-content pre{background:var(--bg-page);padding:var(--space-sm);"
    "border-radius:var(--radius-btn);font-family:ui-monospace,monospace;font-size:15px;"
    "white-space:pre-wrap;margin:var(--space-sm) 0 0}"
    ".block .empty-state{color:var(--text-muted);font-size:var(--fs-meta);"
    "padding:var(--space-md) 0;text-align:center}"
    ".block .empty-state.success{color:var(--accent-green)}"
    ".copy-tooltip{position:absolute;background:var(--accent-green);color:white;"
    "padding:6px 12px;border-radius:var(--radius-btn);font-size:var(--fs-meta);"
    "z-index:1000;pointer-events:none;box-shadow:0 2px 8px rgba(0,0,0,0.15);"
    "animation:fadeInOut 3s ease-in-out;white-space:nowrap}"
    "@keyframes fadeInOut{0%,100%{opacity:0}10%,90%{opacity:1}}"
)

NEW_JS_FRAGMENT = (
    "<script>function copyPrompt(event,btn){event.preventDefault();const p=btn.dataset.prompt;"
    "navigator.clipboard.writeText(p).then(()=>showTooltip(btn,'✅ Prompt copied, paste it into Cowork'))"
    ".catch(err=>showTooltip(btn,'❌ '+err.message));}"
    "function showTooltip(btn,msg){const t=document.createElement('div');t.className='copy-tooltip';t.textContent=msg;"
    "document.body.appendChild(t);const r=btn.getBoundingClientRect();"
    "t.style.top=(r.top-40+window.scrollY)+'px';t.style.left=r.left+'px';setTimeout(()=>t.remove(),3000);}</script>"
    # Live relative-time ticker — mirrors engine/_helpers.relative_when EXACTLY
    # (same thresholds, same RU plural rules) so .reltime[data-ts] spans stay true
    # to the wall clock on a dashboard left open. Server still renders the right
    # label, so this is a progressive enhancement (correct with JS off).
    "<script>(function(){"
    "function pl(n,a,b,c){n=Math.abs(n)%100;var k=n%10;"
    "if(n>10&&n<20)return c;if(k>1&&k<5)return b;if(k===1)return a;return c;}"
    "function rel(s){if(!s||s.length<10)return null;var now=new Date();"
    "if(s.indexOf('T')>-1){var dt=new Date(s);if(!isNaN(dt.getTime())){var secs=(now-dt)/1000;"
    "if(secs>=0){if(secs<60)return '\\u0442\\u043e\\u043b\\u044c\\u043a\\u043e \\u0447\\u0442\\u043e';"
    "var m=Math.floor(secs/60);"
    "if(m<60)return m+' '+pl(m,'\\u043c\\u0438\\u043d\\u0443\\u0442\\u0443','\\u043c\\u0438\\u043d\\u0443\\u0442\\u044b','\\u043c\\u0438\\u043d\\u0443\\u0442')+' \\u043d\\u0430\\u0437\\u0430\\u0434';"
    "var h=Math.floor(secs/3600);"
    "if(h<24)return h+' '+pl(h,'\\u0447\\u0430\\u0441','\\u0447\\u0430\\u0441\\u0430','\\u0447\\u0430\\u0441\\u043e\\u0432')+' \\u043d\\u0430\\u0437\\u0430\\u0434';}}}"
    "var y=+s.slice(0,4),mo=+s.slice(5,7),da=+s.slice(8,10);if(!y||!mo||!da)return null;"
    "var d=new Date(y,mo-1,da),t0=new Date(now.getFullYear(),now.getMonth(),now.getDate());"
    "var delta=Math.round((t0-d)/86400000);"
    "if(delta<=0)return '\\u0441\\u0435\\u0433\\u043e\\u0434\\u043d\\u044f';"
    "if(delta===1)return '\\u0432\\u0447\\u0435\\u0440\\u0430';"
    "if(delta<7)return delta+' '+pl(delta,'\\u0434\\u0435\\u043d\\u044c','\\u0434\\u043d\\u044f','\\u0434\\u043d\\u0435\\u0439')+' \\u043d\\u0430\\u0437\\u0430\\u0434';"
    # >=7d: the label is a server-rendered absolute date that never changes with
    # the clock, so the ticker returns null and leaves the server text untouched.
    "return null;}"
    "function tick(){var els=document.querySelectorAll('.reltime[data-ts]');"
    "for(var i=0;i<els.length;i++){var v=rel(els[i].getAttribute('data-ts'));if(v)els[i].textContent=v;}}"
    "tick();setInterval(tick,60000);})();</script>"
)

# Live due-badge ticker — mirrors _components.due_label + due_class EXACTLY, so a
# .due-badge[data-due] recomputes its wording AND urgency colour against the wall
# clock (a tab open across midnight: «через 2 дня» -> «завтра» -> «сегодня» ->
# «просрочено», colour shifting with it). Localised words injected from t() so it
# tracks the operator locale instead of hardcoding RU. Server still renders the
# correct value (progressive enhancement, correct with JS off).
import json as _json
_DUE_LABELS_JSON = _json.dumps(
    {'over': t('overdue'), 'today': t('today'), 'tom': t('tomorrow'), 'inn': t('in {} d.')},
    ensure_ascii=True,
)
NEW_JS_FRAGMENT += (
    "<script>(function(){var L=" + _DUE_LABELS_JSON + ";"
    "function dtext(n){if(n<0)return L.over;if(n===0)return L.today;if(n===1)return L.tom;return L.inn.replace('{}',n);}"
    "function dcls(n){if(n<0)return 'overdue';if(n===0)return 'today';if(n<=7)return 'soon';return 'far';}"
    "function dtick(){var els=document.querySelectorAll('.due-badge[data-due]');"
    "var now=new Date();var t0=new Date(now.getFullYear(),now.getMonth(),now.getDate());"
    "for(var i=0;i<els.length;i++){var s=els[i].getAttribute('data-due');if(!s||s.length<10)continue;"
    "var y=+s.slice(0,4),mo=+s.slice(5,7),da=+s.slice(8,10);if(!y||!mo||!da)continue;"
    "var d=new Date(y,mo-1,da);var n=Math.round((d-t0)/86400000);"
    "els[i].textContent=dtext(n);els[i].className='due-badge due-badge-'+dcls(n);}}"
    "dtick();setInterval(dtick,60000);})();</script>"
)



# Shared copy-to-clipboard modal for the overview + client_v2 dashboards.
# Replaces the old COPY_PROMPT_JS (via navigator.clipboard, which breaks in a sandbox).
# Uses document.execCommand('copy'), which works both in plain HTML and in an iframe.

PROMPT_MODAL_CSS = (
    ".card-actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:var(--space-xs)}"
    ".btn-mini{font-size:15px;padding:3px 9px;border:1px solid var(--border);"
    "background:var(--bg-page);color:var(--text-primary);border-radius:var(--radius-btn);"
    "cursor:pointer;font-family:inherit;transition:all var(--transition)}"
    ".btn-mini:hover{border-color:var(--accent-blue);color:var(--accent-blue);"
    "background:var(--bg-card)}"
    ".prompt-modal{position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10001;"
    "display:none;align-items:center;justify-content:center;padding:var(--space-md)}"
    ".prompt-modal.open{display:flex}"
    ".prompt-modal-box{background:var(--bg-card);border-radius:14px;"
    "padding:28px 30px;max-width:620px;width:100%;border:1px solid var(--border);"
    "box-shadow:0 24px 64px -16px rgba(16,16,26,0.30),0 4px 12px rgba(16,16,26,0.06)}"
    ".prompt-modal-title{font-size:18px;font-weight:600;margin-bottom:4px;letter-spacing:-0.01em}"
    ".prompt-modal-sub{font-size:14px;color:var(--text-muted);margin-bottom:14px;line-height:1.5}"
    ".prompt-modal-ctx{display:none;background:var(--bg-subtle);border:1px solid var(--border);"
    "border-left:3px solid var(--accent);border-radius:8px;padding:9px 13px;margin-bottom:10px}"
    ".prompt-modal-ctx.show{display:block}"
    ".prompt-modal-ctx-h{font-size:11px;text-transform:uppercase;letter-spacing:.06em;"
    "color:var(--text-muted);font-weight:600;margin-bottom:5px}"
    ".prompt-modal-ctx-body{white-space:pre-wrap;font-size:13px;color:var(--text-secondary);"
    "line-height:1.5;max-height:150px;overflow-y:auto}"
    ".prompt-modal textarea{width:100%;min-height:150px;padding:12px 14px;"
    "border:1px solid var(--border);border-radius:8px;font-family:inherit;box-sizing:border-box;"
    "font-size:var(--fs-base);resize:vertical;background:var(--bg-page);line-height:1.6}"
    ".prompt-modal textarea:focus{outline:none;border-color:var(--accent);background:var(--bg-card)}"
    ".prompt-modal-hint{font-size:13px;color:var(--text-muted);margin-top:12px;padding-top:11px;"
    "border-top:1px solid var(--border);line-height:1.55}"
    ".prompt-modal-hint kbd{background:var(--bg-page);border:1px solid var(--border-strong);"
    "border-radius:4px;padding:1px 6px;font-family:var(--font-mono,ui-monospace,monospace);font-size:12px}"
    ".prompt-modal-status{font-size:var(--fs-meta);margin-top:var(--space-sm);font-weight:500}"
    ".prompt-modal-status.ok{color:var(--accent-green)}"
    ".prompt-modal-status.warn{color:var(--accent-yellow)}"
    ".prompt-modal-actions{display:flex;gap:var(--space-sm);justify-content:flex-end;"
    "margin-top:var(--space-md)}"
    ".prompt-modal-actions button{font-size:var(--fs-meta);padding:var(--space-xs) var(--space-md);"
    "border:1px solid var(--border);background:var(--bg-page);color:var(--text-primary);"
    "border-radius:var(--radius-btn);cursor:pointer;font-family:inherit}"
    ".prompt-modal-actions button:hover{border-color:var(--accent-blue);color:var(--accent-blue)}"
    "#prompt-copy-btn{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:500}"
    "#prompt-copy-btn:hover{background:var(--accent-hover);color:#fff;border-color:var(--accent-hover)}"
)

PROMPT_MODAL_HTML = (
    '<div id="prompt-modal" class="prompt-modal">'
    '<div class="prompt-modal-box" onclick="event.stopPropagation()">'
    '<div class="prompt-modal-title">Prompt ready</div>'
    '<div class="prompt-modal-sub">Edit or dictate (Win+H) below, then paste into Cowork.</div>'
    '<div id="prompt-ctx" class="prompt-modal-ctx">'
    '<div class="prompt-modal-ctx-h">Task context · always included</div>'
    '<div id="prompt-ctx-body" class="prompt-modal-ctx-body"></div>'
    '</div>'
    '<textarea id="prompt-text" placeholder="Write your own prompt or dictate (Win+H)…"></textarea>'
    '<div id="prompt-status" class="prompt-modal-status">—</div>'
    '<div class="prompt-modal-actions">'
    '<button id="prompt-copy-btn">Copy again</button>'
    '<button id="prompt-close-btn">Close</button>'
    '</div>'
    '<div class="prompt-modal-hint">Tip: <kbd>Win</kbd>+<kbd>H</kbd> is the built-in Windows dictation — it works in any text field, including this one.</div>'
    '</div>'
    '</div>'
)

PROMPT_MODAL_JS = (
    '<script>'
    '(function(){'
    'var modal=document.getElementById("prompt-modal");'
    'var ta=document.getElementById("prompt-text");'
    'var status=document.getElementById("prompt-status");'
    'var ctxBox=document.getElementById("prompt-ctx");'
    'var ctxBody=document.getElementById("prompt-ctx-body");'
    'var ctxStore="";'
    # the copied prompt = immutable context + whatever is in the editable field
    'function fullText(){var b=ta.value.trim();return ctxStore?(b?ctxStore+"\\n\\n"+b:ctxStore):b;}'
    'function copyText(str){var tmp=document.createElement("textarea");tmp.value=str;'
    'tmp.style.position="fixed";tmp.style.left="-9999px";tmp.style.opacity="0";'
    'document.body.appendChild(tmp);tmp.focus();tmp.select();'
    'var ok=false;try{ok=document.execCommand("copy");}catch(e){ok=false;}'
    'document.body.removeChild(tmp);return ok;}'
    'function doCopy(){var ok=copyText(fullText());'
    'status.className="prompt-modal-status "+(ok?"ok":"warn");'
    'status.textContent=ok?"✓ Copied — paste into Cowork (Ctrl+V)":'
    '"Failed — select and press Ctrl+C, then Ctrl+V in Cowork";ta.focus();}'
    'function openPrompt(txt,opts){'
    'opts=opts||{};'
    'ctxStore=opts.ctx||"";'
    'ta.value=txt||"";'
    'if(ctxBox&&ctxBody){if(ctxStore){ctxBody.textContent=ctxStore;ctxBox.classList.add("show");}'
    'else{ctxBox.classList.remove("show");ctxBody.textContent="";}}'
    'modal.classList.add("open");'
    'setTimeout(function(){ta.focus();'
    'if(opts.dictate){var L=ta.value.length;try{ta.setSelectionRange(L,L);}catch(e){}'
    'status.className="prompt-modal-status";status.textContent="Press Win+H to dictate, then Copy";}'
    'else{ta.select();doCopy();}'
    '},20);}'
    'window.openPromptModal=openPrompt;'
    'function closeModal(){modal.classList.remove("open");}'
    'document.addEventListener("click",function(e){'
    'var btn=e.target.closest("button[data-prompt]");'
    'if(btn){e.preventDefault();openPrompt(btn.dataset.prompt,{ctx:btn.getAttribute("data-prompt-ctx")||""});return;}'
    'if(e.target===modal){closeModal();}});'
    'document.getElementById("prompt-close-btn").addEventListener("click",closeModal);'
    'document.getElementById("prompt-copy-btn").addEventListener("click",doCopy);'
    'document.addEventListener("keydown",function(e){'
    'if(e.key==="Escape"&&modal.classList.contains("open"))closeModal();});})();'
    '</script>'
)

# Localize the prompt-copy modal chrome through the locale layer (en = no-op).
PROMPT_MODAL_HTML = (
    PROMPT_MODAL_HTML
    .replace('>Prompt ready</div>', '>' + t('Prompt ready') + '</div>')
    .replace('>Copy again</button>', '>' + t('Copy again') + '</button>')
    .replace('>Close</button>', '>' + t('Close') + '</button>')
    .replace('Edit or dictate (Win+H) below, then paste into Cowork.',
             t('Edit or dictate (Win+H) below, then paste into Cowork.'))
    .replace('>Task context · always included</div>',
             '>' + t('Task context · always included') + '</div>')
    .replace('placeholder="Write your own prompt or dictate (Win+H)…"',
             'placeholder="' + t('Write your own prompt or dictate (Win+H)…') + '"')
    .replace('Tip: <kbd>Win</kbd>+<kbd>H</kbd> is the built-in Windows dictation — it works in any text field, including this one.',
             t('Tip: <kbd>Win</kbd>+<kbd>H</kbd> is the built-in Windows dictation — it works in any text field, including this one.'))
)
PROMPT_MODAL_JS = (
    PROMPT_MODAL_JS
    .replace('"✓ Copied — paste into Cowork (Ctrl+V)"',
             '"' + t('✓ Copied — paste into Cowork (Ctrl+V)') + '"')
    .replace('"Failed — select and press Ctrl+C, then Ctrl+V in Cowork"',
             '"' + t('Failed — select and press Ctrl+C, then Ctrl+V in Cowork') + '"')
    .replace('"Select the text and press Ctrl+C, then Ctrl+V in Cowork"',
             '"' + t('Select the text and press Ctrl+C, then Ctrl+V in Cowork') + '"')
    .replace('"✓ Copied"', '"' + t('✓ Copied') + '"')
    .replace('"Ctrl+C to copy"', '"' + t('Ctrl+C to copy') + '"')
    .replace('"Press Win+H to dictate, then Copy"', '"' + t('Press Win+H to dictate, then Copy') + '"')
)
