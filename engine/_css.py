"""_css.py — all CSS constants and JS fragments for overview/dashboard.

Extracted from generate.py as part of the decomposition refactor.
Imported by generate.py, _client_dashboard_v2.py, _overview_v2.py.
"""

from _strings import t

DESIGN_TOKENS_CSS = (
    ":root{"
    "--bg-page:#FBFBFA;--bg-card:#FFFFFF;--bg-canvas:#F2F0EA;--border:#EAE8E2;"
    "--text-primary:#171717;--text-secondary:#2E2E2E;--text-muted:#474744;"
    "--accent-red:#C0392B;--accent-yellow:#D98324;--accent-green:#5E8B49;--accent-blue:#3A6CA8;"
    "--red-bg:#FBE6E0;--yellow-bg:#FBEFD4;--green-bg:#EAF3DE;--blue-bg:#E6F0FB;"
    "--font:-apple-system,\"Segoe UI\",\"Helvetica Neue\",system-ui,sans-serif;"
    "--fs-base:15px;--fs-meta:13px;--fs-h2:22px;--fs-h1:28px;--fs-number:28px;--fs-number-large:40px;"
    "--space-xs:4px;--space-sm:8px;--space-md:16px;--space-lg:24px;--space-xl:32px;"
    "--radius-card:8px;--radius-btn:4px;--radius-badge:2px;"
    "--shadow-card:0 1px 2px rgba(17,17,17,0.03);--transition:150ms ease;}"
    "*{box-sizing:border-box}"
    "body{margin:0;padding:var(--space-lg);background:var(--bg-canvas);color:var(--text-primary);"
    "font-family:var(--font);font-size:var(--fs-base);line-height:1.6}"
    "a{color:inherit;text-decoration:none}a:hover{color:var(--accent-blue)}"
    ".card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-card);"
    "padding:var(--space-md);box-shadow:var(--shadow-card)}"
    ".muted{color:var(--text-muted)}.secondary{color:var(--text-secondary)}"
    ".meta{font-size:var(--fs-meta);color:var(--text-muted)}"

    # === Rich-badges and Risks ===
    ".rich-badges{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 4px}"
    ".rich-badge{font-size:15px;padding:2px 8px;border-radius:10px;"
    "background:#F0EBE3;color:var(--text-secondary);font-weight:500;letter-spacing:.02em}"
    ".rich-badge.prio-high{background:#FCE4DE;color:var(--accent-red);font-weight:600}"
    ".rich-badge.prio-low{background:#EEEEEC;color:var(--text-muted)}"
    ".rich-badge.blocked-by{background:#FBF1DC;color:#8A6730}"
    ".rich-badge.comments{background:#E8EEEA;color:var(--accent-green)}"
    # .track-prio-high: overrides the existing ::before (no double border)
    # risks
    ".risks-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));"
    "gap:var(--space-md);margin-bottom:var(--space-lg)}"
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
    ".risk-next{font-size:15px;color:var(--text-primary);background:#F8F5EF;"
    "padding:6px 10px;border-radius:6px;margin-top:8px}"
    ".risk-next::before{content:''}"
    ".risk-linked-tasks{font-size:15px;color:var(--text-muted);margin-top:6px;font-family:var(--font-mono,monospace)}"
    ".risk-law{font-size:15px;color:var(--accent-blue);margin-top:4px;font-style:italic}"
    ".risk-summary{cursor:pointer;list-style:none;display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 10px;flex:1 0 auto;align-content:flex-start}"
    ".risk-summary::-webkit-details-marker{display:none}"
    ".risk-summary::before{content:'▸';color:var(--text-muted);font-size:11px}"
    "details.risk-card[open]>.risk-summary::before{content:'▾'}"
    ".risk-next-inline{font-size:14px;color:var(--text-secondary);font-weight:400}"
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

    # === Financials + Counterparties ===
    ".fin-section{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);padding:16px 20px;margin-bottom:14px}"
    ".fin-pace{font-size:15px;color:var(--text-primary);background:#F8F5EF;"
    "padding:8px 12px;border-radius:6px;margin-bottom:var(--space-md)}"
    ".fin-subtitle{font-size:15px;text-transform:uppercase;letter-spacing:.04em;"
    "color:var(--text-muted);font-weight:500;margin:var(--space-md) 0 6px}"
    ".fin-table{width:100%;border-collapse:collapse;background:var(--bg-card);"
    "border:1px solid var(--border);border-radius:var(--radius-card);overflow:hidden;font-size:15px}"
    ".fin-table th{text-align:left;padding:8px 12px;background:#F0EBE3;"
    "font-weight:500;font-size:15px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.04em}"
    ".fin-table td{padding:8px 12px;border-top:1px solid var(--border);color:var(--text-secondary)}"
    ".fin-table .fin-period{font-weight:600;color:var(--text-primary)}"
    ".fin-table .fin-income{color:var(--text-primary);font-family:var(--font-mono,monospace);font-size:15px}"
    ".fin-table .cal-amt{font-family:var(--font-mono,monospace);font-size:15px;color:var(--text-primary)}"
    ".fin-cal-table tr.cal-st-past{opacity:.5}"
    ".fin-cal-table tr.cal-st-future td.cal-date{color:var(--accent-blue);font-weight:500}"
    ".cal-task code{font-size:15px;background:#F0EBE3;padding:2px 6px;border-radius:4px}"
    "details.cal-past{margin-top:6px}"
    "details.cal-past>summary{cursor:pointer;list-style:none;font-size:15px;color:var(--text-muted);font-weight:500;padding:4px 0}"
    "details.cal-past>summary::-webkit-details-marker{display:none}"
    "details.cal-past>summary::before{content:'\\25B8 ';color:var(--text-muted);font-size:11px}"
    "details.cal-past[open]>summary::before{content:'\\25BE '}"
    "details.cal-past>.fin-cal-table{margin-top:6px}"
    # Counterparties
    ".cp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));"
    "gap:var(--space-md);margin-bottom:var(--space-lg)}"
    ".cp-card{background:var(--bg-card);border:1px solid var(--border);"
    "border-radius:var(--radius-card);padding:var(--space-md)}"
    ".cp-name{font-weight:600;font-size:14px;color:var(--text-primary);margin-bottom:4px}"
    ".cp-meta{font-size:15px;color:var(--text-muted);text-transform:uppercase;"
    "letter-spacing:.04em;margin-bottom:8px}"
    ".cp-inn{font-size:15px;color:var(--text-secondary);margin-bottom:6px}"
    ".cp-inn code{font-family:var(--font-mono,monospace);background:#F0EBE3;padding:2px 6px;border-radius:4px;font-size:15px}"
    ".cp-req{font-size:15px;color:var(--text-secondary);margin:6px 0;padding:6px 10px;"
    "background:#F8F5EF;border-radius:6px}"
    ".cp-tags{display:flex;gap:4px;flex-wrap:wrap;margin:6px 0}"
    ".cp-tag{font-size:15px;padding:2px 8px;border-radius:10px;background:#E8EEEA;"
    "color:var(--accent-green);font-weight:500}"
    ".cp-notes{font-size:15px;color:var(--text-secondary);line-height:1.5;margin-top:8px;"
    "padding-top:8px;border-top:1px dashed var(--border)}"
    ".cp-linked{font-size:15px;color:var(--text-muted);margin-top:6px;font-family:var(--font-mono,monospace)}"
    ".cp-linked code{background:#F0EBE3;padding:1px 5px;border-radius:3px}"

    # === UX fix #1: Focus-band (what matters today) ===
    ".focus-band{background:linear-gradient(135deg,#FBF1DC,#F8E5C8);"
    "border:1px solid #E8C99E;border-radius:var(--radius-card);"
    "padding:var(--space-md);margin:0 0 var(--space-lg)}"
    ".focus-band-label{font-size:15px;text-transform:uppercase;letter-spacing:.06em;"
    "color:#8A6730;font-weight:600;margin-bottom:8px}"
    ".focus-band-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px}"
    ".focus-card{background:rgba(255,255,255,.7);border-radius:8px;padding:8px 10px;"
    "border:1px solid rgba(232,201,158,.5)}"
    ".focus-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px}"
    ".focus-icon{font-size:14px}"
    ".focus-tag{font-size:15px;text-transform:uppercase;letter-spacing:.04em;"
    "color:#8A6730;font-weight:600;background:rgba(232,201,158,.4);"
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
    "background:#F0EBE3;padding:2px 6px;border-radius:4px}"
    ".acc-bik{font-family:var(--font-mono,monospace);font-size:15px;color:var(--text-muted)}"
    ".acc-purpose{font-size:15px;color:var(--text-muted)}"
    ".acc-status{font-size:15px;text-transform:uppercase;color:var(--accent-yellow);font-weight:500}"
    ".acc-note{font-size:15px;color:var(--text-secondary);background:#F8F5EF;"
    "padding:6px 10px;border-radius:6px;margin-top:4px;width:100%;font-style:italic}"
    # Behavior
    ".beh-section{margin-bottom:var(--space-lg);background:var(--bg-card);"
    "border:1px solid var(--border);border-radius:var(--radius-card);padding:var(--space-md)}"
    ".beh-block{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}"
    ".beh-ch-primary{font-size:15px;font-weight:600;background:#FBF1DC;"
    "padding:4px 10px;border-radius:14px;color:#8A6730}"
    ".beh-ch-secondary{font-size:15px;background:#F0EBE3;padding:3px 8px;"
    "border-radius:12px;color:var(--text-secondary)}"
    ".beh-tz{font-size:15px;color:var(--text-muted);padding:3px 8px}"
    ".beh-style{font-size:15px;color:var(--text-secondary);margin-bottom:8px}"
    ".beh-style b{color:var(--text-primary)}"
    ".beh-note{font-size:15px;color:var(--text-secondary);font-style:italic;line-height:1.5;margin-bottom:8px}"
    ".beh-prefs{display:flex;flex-direction:column;gap:4px;font-size:15px}"
    ".beh-likes{color:var(--accent-green)}"
    ".beh-dislikes{color:#8B4F3C}"
    ".beh-asks{color:var(--text-secondary);background:#F8F5EF;padding:6px 10px;border-radius:6px;margin-top:4px}"

    # === UX-fix #7: client-actions row (Discuss + Dictate) ===
    # Buttons use the shared .btn-mini class (as on track cards and in modals)
    ".client-actions{display:flex;gap:6px;margin-top:10px}"

    # === UX-fix #8: unified button design system (tm-btn-*) ===
    # Used everywhere: client header, track modal, any future action zone.
    # Sizes chosen for accessibility (15px font, 12+22 padding — older users).
    ".tm-btn{padding:12px 22px;font-size:15px;border:1px solid var(--border);"
    "background:var(--bg-card);color:var(--text-primary);border-radius:var(--radius-btn);"
    "cursor:pointer;font-weight:500;font-family:inherit;"
    "transition:background var(--transition,.15s),border-color var(--transition,.15s),color var(--transition,.15s);"
    "display:inline-flex;align-items:center;gap:6px}"
    ".tm-btn:hover{border-color:var(--accent-blue);background:var(--blue-bg);color:var(--accent-blue)}"
    ".tm-btn-primary{background:var(--accent-blue);color:#fff;border-color:var(--accent-blue)}"
    ".tm-btn-primary:hover{background:#3a5c8f;color:#fff;border-color:#3a5c8f}"
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
    ".prompt-modal-box{background:var(--bg-card);border-radius:var(--radius-card);"
    "padding:var(--space-lg);max-width:600px;width:100%;border:1px solid var(--border);"
    "box-shadow:0 4px 16px rgba(0,0,0,0.1)}"
    ".prompt-modal-title{font-size:var(--fs-h2);font-weight:500;margin-bottom:var(--space-sm)}"
    ".prompt-modal textarea{width:100%;min-height:140px;padding:var(--space-sm) var(--space-md);"
    "border:1px solid var(--border);border-radius:var(--radius-btn);font-family:inherit;"
    "font-size:var(--fs-base);resize:vertical;background:var(--bg-page);line-height:1.6}"
    ".prompt-modal-status{font-size:var(--fs-meta);margin-top:var(--space-sm);font-weight:500}"
    ".prompt-modal-status.ok{color:var(--accent-green)}"
    ".prompt-modal-status.warn{color:var(--accent-yellow)}"
    ".prompt-modal-actions{display:flex;gap:var(--space-sm);justify-content:flex-end;"
    "margin-top:var(--space-md)}"
    ".prompt-modal-actions button{font-size:var(--fs-meta);padding:var(--space-xs) var(--space-md);"
    "border:1px solid var(--border);background:var(--bg-page);color:var(--text-primary);"
    "border-radius:var(--radius-btn);cursor:pointer;font-family:inherit}"
    ".prompt-modal-actions button:hover{border-color:var(--accent-blue);color:var(--accent-blue)}"
)

PROMPT_MODAL_HTML = (
    '<div id="prompt-modal" class="prompt-modal">'
    '<div class="prompt-modal-box">'
    '<div class="prompt-modal-title">Prompt ready</div>'
    '<textarea id="prompt-text" readonly></textarea>'
    '<div id="prompt-status" class="prompt-modal-status">—</div>'
    '<div class="prompt-modal-actions">'
    '<button id="prompt-copy-btn">Copy again</button>'
    '<button id="prompt-close-btn">Close</button>'
    '</div>'
    '</div>'
    '</div>'
)

PROMPT_MODAL_JS = (
    '<script>'
    '(function(){'
    'var modal=document.getElementById("prompt-modal");'
    'var ta=document.getElementById("prompt-text");'
    'var status=document.getElementById("prompt-status");'
    'function openPrompt(txt){'
    'ta.value=txt;modal.classList.add("open");'
    'setTimeout(function(){ta.focus();ta.select();'
    'try{var ok=document.execCommand("copy");'
    'status.className="prompt-modal-status "+(ok?"ok":"warn");'
    'status.textContent=ok?"✓ Copied — paste into Cowork (Ctrl+V)":'
    '"Failed — select and press Ctrl+C, then Ctrl+V in Cowork";'
    '}catch(e){status.className="prompt-modal-status warn";'
    'status.textContent="Select the text and press Ctrl+C, then Ctrl+V in Cowork";}'
    '},20);}'
    'function closeModal(){modal.classList.remove("open");}'
    'document.addEventListener("click",function(e){'
    'var btn=e.target.closest("button[data-prompt]");'
    'if(btn){e.preventDefault();openPrompt(btn.dataset.prompt);return;}'
    'if(e.target===modal){closeModal();}});'
    'document.getElementById("prompt-close-btn").addEventListener("click",closeModal);'
    'document.getElementById("prompt-copy-btn").addEventListener("click",function(){'
    'ta.focus();ta.select();'
    'try{var ok=document.execCommand("copy");'
    'status.className="prompt-modal-status "+(ok?"ok":"warn");'
    'status.textContent=ok?"✓ Copied":"Ctrl+C to copy";'
    '}catch(e){status.textContent="Ctrl+C to copy";}});'
    'document.addEventListener("keydown",function(e){'
    'if(e.key==="Escape")closeModal();});})();'
    '</script>'
)

# Localize the prompt-copy modal chrome through the locale layer (en = no-op).
PROMPT_MODAL_HTML = (
    PROMPT_MODAL_HTML
    .replace('>Prompt ready</div>', '>' + t('Prompt ready') + '</div>')
    .replace('>Copy again</button>', '>' + t('Copy again') + '</button>')
    .replace('>Close</button>', '>' + t('Close') + '</button>')
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
)
