"""_mode_switch.py — All/Team/Direct mode toggle, iOS segmented-control style.

Used in overview and in the plans (today/week/month).
State is persisted in localStorage.
"""
from _strings import t

MODE_SWITCH_HTML = (
    '<div class="mode-switch">'
    '<button class="mode-btn active" data-mode="all">' + t('All') + ' <span class="mode-count">15</span></button>'
    '<button class="mode-btn" data-mode="team">' + t('Team') + ' <span class="mode-count">6</span></button>'
    '<button class="mode-btn" data-mode="direct">' + t('Direct') + ' <span class="mode-count">9</span></button>'
    '</div>'
)

MODE_SWITCH_CSS = """
.mode-switch{display:inline-flex;gap:2px;padding:3px;background:var(--bg-page);
  border:1px solid var(--border);border-radius:8px;margin:0 0 var(--space-md);
  font-size:0;vertical-align:middle}
.mode-btn{padding:8px 16px;font-size:15px;border:0;background:transparent;
  color:var(--text-primary);cursor:pointer;border-radius:6px;
  font-family:inherit;font-weight:500;transition:all 120ms;
  display:inline-flex;align-items:center;gap:6px;line-height:1.4}
.mode-btn:hover{color:var(--text-primary)}
.mode-btn.active{background:var(--bg-card);color:var(--text-primary);font-weight:600;
  box-shadow:0 1px 2px rgba(0,0,0,0.06),0 0 0 0.5px rgba(0,0,0,0.04)}
.mode-count{font-size:15px;color:var(--text-secondary);font-weight:500;
  padding:2px 8px;background:var(--bg-page);border-radius:8px;line-height:1.4}
.mode-btn.active .mode-count{background:var(--bg-page);color:var(--text-secondary)}
body.mode-team [data-track-type="direct"]{display:none !important}
body.mode-direct [data-track-type="team"]{display:none !important}
"""

MODE_SWITCH_JS = (
    "<script>(function(){"
    "var saved=(function(){try{return localStorage.getItem('cowork_mode')||'all'}catch(e){return 'all'}})();"
    "function applyMode(m){"
    "document.body.classList.remove('mode-all','mode-team','mode-direct');"
    "document.body.classList.add('mode-'+m);"
    "document.querySelectorAll('.mode-btn').forEach(function(b){"
    "b.classList.toggle('active',b.getAttribute('data-mode')===m)});"
    "try{localStorage.setItem('cowork_mode',m)}catch(e){}}"
    "document.addEventListener('click',function(e){"
    "var b=e.target.closest('.mode-btn');if(b)applyMode(b.getAttribute('data-mode'))});"
    "if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',function(){applyMode(saved)})}"
    "else{applyMode(saved)}"
    "})();</script>"
)
