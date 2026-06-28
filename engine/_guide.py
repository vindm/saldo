"""_guide.py — the "How to use" page.

Dashboard documentation: IA, user flows, data sources, legend, roadmap.
This is both a manual for the accountant and a formalization of the spec
for further redesign iterations.
"""
from generate import (
    clients, TODAY,
    _esc,
    DESIGN_TOKENS_CSS, OVERVIEW_SPECIFIC_CSS,
)
from _helpers import _format_date_ru
from _overview_v2 import OVERVIEW_V2_CSS
from _overview_shared import render_header
from _sidebar import render_sidebar, SIDEBAR_CSS
from _css import PROMPT_MODAL_CSS, PROMPT_MODAL_HTML, PROMPT_MODAL_JS


def render_guide():
    head = render_header()
    title = 'How to use'

    content = '''
<h1 class="page-title">How to use the dashboard</h1>
<p class="g-lead">This dashboard is a single entry point into the day's work. The one rule that shapes everything: <b>the Plan contains actions only</b>. Anything that is not an action lives somewhere else — open questions and clarifications go to the Dashboard; passive "we're just waiting / watching" items go to a collapsed Waiting lane. So when you open the Plan, every row is something you can actually do right now.</p>

<nav class="g-toc">
  <a href="#views">The views</a>
  <a href="#modal">Track modal</a>
  <a href="#flows">User flows: 3 rituals</a>
  <a href="#nottask">What is NOT a task</a>
  <a href="#sources">Task sources &amp; classification</a>
  <a href="#legend">Legend</a>
</nav>

<section id="views" class="g-sect">
  <h2>The views</h2>
  <p>The left menu lists: Dashboard · Plan · Calendar · Periods · one entry per client group (e.g. Team, Direct) · How to use. Each view answers its own question.</p>

  <div class="g-card">
    <h3>🏠 Dashboard</h3>
    <p><b>Question:</b> what is in the system right now?</p>
    <ul>
      <li><b>One-line stats strip</b> — the quick numbers.</li>
      <li><b>🧭 Brief for today</b> — a short framing of the day.</li>
      <li><b>❓ Open questions (N)</b> — one expandable block. It shows 2 by default, sorted by priority and then by staleness/age; among equals a daily rotation surfaces different questions over time. Each has action buttons (Close / Ask the client / Defer). The rest open under "Show the rest (N)", grouped by client. These are clarifications — they were deliberately moved <i>off</i> the Plan to here.</li>
      <li><b>🧠 Analysis and recommendations</b>.</li>
      <li><b>Top-5 most urgent</b>, the activity / morning digest, and a dictate mic.</li>
    </ul>
    <p>Open it first in the morning to see "what's going on at all".</p>
  </div>

  <div class="g-card">
    <h3>✅ Plan</h3>
    <p><b>Question:</b> what do I DO right now?</p>
    <p>One urgency-sorted, colour-coded list — no Urgent/Plan/Backlog horizon buckets. It is split into blocks:</p>
    <ul>
      <li><b>Operations — can be batched</b> — collapsible operation bars. An operation groups ≥2 tasks that share the same operation + reporting period + client-group, <i>regardless of how many clients are in it</i> (we model the operation, not the current client roster). Examples: "Month close · April 2026", "Calc + notice + payment order · June 2026", "Client service payment". Click a bar to expand the per-client task rows; each bar has <b>Process wave</b> / <b>Dictate</b> actions.</li>
      <li><b>Individual tasks</b> — single rows for one-offs that don't group.</li>
      <li><b>⏳ Waiting — on the client / bank side</b> — a de-emphasised, <b>collapsed</b> lane at the bottom for passive items: monitoring / risk-watches and "awaiting the client" items with no deadline (nothing to do but wait). Dated "awaiting the client" items that <i>do</i> have a deadline + a chase action (sign a payment order, payment control, first-docs) stay as real tasks above.</li>
    </ul>
    <p>The left border colour = urgency: red overdue, amber ≤7 days, blue ≤30 days, grey later / no date. Every row and bar shows days-to-nearest-deadline. Clicking a row or bar opens the track modal.</p>
  </div>

  <div class="g-card">
    <h3>📅 Calendar</h3>
    <p><b>Question:</b> how does the month lay out / what tax dates are coming?</p>
    <p>A navigable multi-month grid with ‹ › to switch months, clickable task chips, and tax dates framed. Useful at the start of a month and around the unified-tax-account due dates.</p>
  </div>

  <div class="g-card">
    <h3>🗂 Periods</h3>
    <p><b>Question:</b> where does each reporting period stand?</p>
    <p>For each open period it shows the recurring cycles as a progress stepper — done ✓ / N tasks in progress / overdue (counted by task). The main <b>monthly close</b> runs in order:</p>
    <ul>
      <li>Collect source docs → Post to 1C → Month close → Month audit → Calc + notice + payment order → Sign / pay.</li>
    </ul>
    <p>Clients with payroll, quarterly tax, or AUSN also get their own cycle bands below. Clicking a stage jumps straight to that operation on the Plan.</p>
  </div>

  <div class="g-card">
    <h3>👥 Clients (one entry per group)</h3>
    <p><b>Question:</b> what's the picture for a client?</p>
    <p>The menu shows one item per client group (e.g. Team, Direct), built dynamically from each client's <code>group</code> field. Clicking a client opens its dashboard — the <b>same plan renderer scoped to that client</b>, so the client card shows that client's Operations / Individual / Waiting lane — plus risks, quick-access links, financials, counterparties, behavior, and history.</p>
  </div>
</section>

<section id="modal" class="g-sect">
  <h2>Track modal</h2>
  <p>Clicking any task row or operation bar (on the Dashboard, the Plan, or a client card) opens a modal with the full task map.</p>

  <div class="g-card">
    <h3>What's inside</h3>
    <ul>
      <li><b>Title</b> of the track.</li>
      <li><b>Breadcrumb</b> — clicks lead to the matching pages.</li>
      <li><b>Deadline badge</b> (overdue / today / N days).</li>
      <li><b>📋 Context</b> — what the task is about.</li>
      <li><b>History of events</b>.</li>
      <li><b>💡 System hypothesis</b> — what the system thinks the next step is.</li>
      <li><b>Details</b>.</li>
    </ul>
  </div>

  <div class="g-card">
    <h3>Actions</h3>
    <ul>
      <li><b>Remind</b> / <b>Defer</b>.</li>
      <li><b>🔍 Break it down</b> — copies a prompt to paste into the assistant chat; the assistant opens the model, checks related items, and proposes a step.</li>
      <li><b>🎤 Dictate</b> — capture a thought to hand to the assistant.</li>
    </ul>
    <p class="g-note">There are deliberately <b>no</b> "Done" / "Snooze" buttons. Closing or snoozing goes through a conversation with the assistant — so it can verify what was actually done, update related items, and log the history. Say "close" or "defer 3 days" to the assistant instead of clicking.</p>
  </div>
</section>

<section id="flows" class="g-sect">
  <h2>User flows: 3 rituals</h2>

  <div class="g-flow">
    <div class="g-flow-title">Morning</div>
    <ol>
      <li>Open the <b>Dashboard</b> → glance at stats, open questions, top-5, and the digest</li>
      <li>Open the <b>Plan</b> → work the top operations (batch a whole operation at once with <b>Process wave</b>)</li>
      <li>Say "close / defer / do this" to the assistant, and it updates the model</li>
    </ol>
  </div>

  <div class="g-flow">
    <div class="g-flow-title">Start of month / month-end</div>
    <ol>
      <li>Open <b>Periods</b> → see where each cycle stands, stage by stage</li>
      <li>Click a lagging stage → jump to that operation on the <b>Plan</b></li>
      <li>Use the <b>Calendar</b> for the tax dates</li>
    </ol>
  </div>

  <div class="g-flow">
    <div class="g-flow-title">During the day</div>
    <ol>
      <li>A signal arrives (TG / email) → it shows up in the digest</li>
      <li>A thought about a client comes up → the <b>🎤 Dictate</b> button → paste to the assistant</li>
    </ol>
  </div>
</section>

<section id="nottask" class="g-sect">
  <h2>What is NOT a task</h2>
  <p>This is the key mental model. The Plan holds actions only — three kinds of things deliberately live elsewhere:</p>
  <ul>
    <li><b>Open questions / clarifications</b> → the Dashboard's "❓ Open questions" block. They need an answer, not an action, so they never clutter the Plan.</li>
    <li><b>Passive waits &amp; monitoring</b> → the Plan's collapsed <b>⏳ Waiting</b> lane. Nothing for you to do but watch — risk-watches and deadline-less "awaiting the client" items.</li>
    <li><b>Risks</b> → on the client card. They are context about a client, not a to-do.</li>
  </ul>
  <p class="g-note">If a row is sitting on the Plan, it's because there is an action to take. If there's nothing to do yet, it has already been routed to one of the three buckets above.</p>
</section>

<section id="sources" class="g-sect">
  <h2>Task sources &amp; classification</h2>
  <p>The <b>source of truth</b> is each client's <code>state/tasks.json</code> (active tracks). Optional morning collectors / daemons add signals as JSON into <code>journal/inbox/</code>:</p>
  <table class="g-table">
    <thead><tr><th>Source</th><th>What it provides</th></tr></thead>
    <tbody>
      <tr><td><code>state/tasks.json</code></td><td>Active client tracks — the source of truth the plan is built from</td></tr>
      <tr><td><code>journal/inbox/</code> (practice-management / finkoper)</td><td>Optional signals from practice-management chats</td></tr>
      <tr><td><code>journal/inbox/</code> (email)</td><td>Optional email signals</td></tr>
      <tr><td><code>journal/inbox/</code> (telegram)</td><td>Optional Telegram signals</td></tr>
      <tr><td><code>journal/inbox/</code> (news)</td><td>Optional news signals</td></tr>
    </tbody>
  </table>
  <p>If a collector is absent, its panels just stay empty — graceful degradation, nothing breaks.</p>
  <p><b>Grouping</b> is by semantic task <b>type</b> + period + group — never by the task's <i>source</i> (a "finkoper" task is grouped by what it's <i>about</i>, e.g. "acquiring", not by "it came from finkoper") and never by raw title wording.</p>

  <h3>How tasks are classified</h3>
  <ul>
    <li><code>open_question</code> type → the Dashboard "Open questions" block; excluded from the Plan.</li>
    <li><code>monitoring</code> type, or <code>awaiting_external</code> with <b>no</b> due date → the Plan's <b>Waiting</b> lane.</li>
    <li>everything else that has an action → the Plan's <b>Operations</b> / <b>Individual</b> blocks.</li>
  </ul>
</section>

<section id="legend" class="g-sect">
  <h2>Legend</h2>

  <h3>Task urgency colours</h3>
  <div class="g-legend">
    <div class="g-leg-item"><span class="g-sw g-red"></span><b>Red</b> — overdue or due within 3 days</div>
    <div class="g-leg-item"><span class="g-sw g-amber"></span><b>Amber</b> — due within 7 days</div>
    <div class="g-leg-item"><span class="g-sw g-blue"></span><b>Blue</b> — planned, due within 30 days</div>
    <div class="g-leg-item"><span class="g-sw g-grey"></span><b>Grey</b> — no hard date, or later</div>
  </div>

  <h3>Client health</h3>
  <div class="g-legend">
    <div class="g-leg-item"><span class="g-dot g-red"></span><b>RED</b> — a blocker or something overdue</div>
    <div class="g-leg-item"><span class="g-dot g-amber"></span><b>YELLOW</b> — due soon, or minor gaps</div>
    <div class="g-leg-item"><span class="g-dot g-green"></span><b>GREEN</b> — clear</div>
    <div class="g-leg-item"><span class="g-dot g-grey"></span><b>GREY</b> — too little data</div>
  </div>
</section>
'''

    extra_css = (
        '.page-title{font-size:22px;font-weight:500;margin:0 0 var(--space-md)}'
        '.g-lead{font-size:14px;line-height:1.6;color:var(--text-secondary);'
        'margin:0 0 var(--space-lg);max-width:760px}'
        '.g-toc{background:var(--bg-card);border:1px solid var(--border);'
        'border-radius:var(--radius-card);padding:var(--space-md);margin-bottom:var(--space-lg);'
        'display:flex;flex-wrap:wrap;gap:var(--space-md)}'
        '.g-toc a{font-size:15px;color:var(--accent-blue);text-decoration:none}'
        '.g-toc a:hover{text-decoration:underline}'
        '.g-sect{margin-bottom:var(--space-xl)}'
        '.g-sect h2{font-size:18px;font-weight:500;margin:0 0 var(--space-md);'
        'padding-bottom:var(--space-xs);border-bottom:1px solid var(--border)}'
        '.g-sect h3{font-size:14px;font-weight:500;margin:var(--space-md) 0 var(--space-xs)}'
        '.g-sect p{font-size:15px;line-height:1.6;color:var(--text-primary);margin:0 0 var(--space-sm);'
        'max-width:760px}'
        '.g-sect ul,.g-sect ol{font-size:15px;line-height:1.7;color:var(--text-primary);'
        'padding-left:var(--space-lg);margin:0 0 var(--space-md);max-width:760px}'
        '.g-sect li{margin-bottom:4px}'
        '.g-card{background:var(--bg-card);border:1px solid var(--border);'
        'border-radius:var(--radius-card);padding:var(--space-md);margin-bottom:var(--space-md)}'
        '.g-card h3{margin-top:0}'
        '.g-flow{background:var(--bg-card);border:1px solid var(--border);'
        'border-left-width:3px;border-left-color:var(--accent-blue);'
        'border-radius:0 var(--radius-card) var(--radius-card) 0;'
        'padding:var(--space-md);margin-bottom:var(--space-md)}'
        '.g-flow-title{font-size:15px;font-weight:500;color:var(--accent-blue);'
        'margin-bottom:var(--space-xs)}'
        '.g-table{width:100%;border-collapse:collapse;background:var(--bg-card);'
        'border:1px solid var(--border);border-radius:var(--radius-card);overflow:hidden;'
        'font-size:15px;margin:var(--space-md) 0;max-width:760px}'
        '.g-table th{font-size:14px;text-transform:uppercase;letter-spacing:0.04em;'
        'color:var(--text-muted);font-weight:500;padding:8px var(--space-sm);text-align:left;'
        'border-bottom:1px solid var(--border);background:var(--bg-page)}'
        '.g-table td{padding:8px var(--space-sm);border-bottom:1px solid var(--border);'
        'vertical-align:top}'
        '.g-table tr:last-child td{border-bottom:none}'
        '.g-note{background:var(--bg-page);border-left:3px solid var(--accent-yellow);'
        'padding:8px var(--space-md);border-radius:0 var(--radius-card) var(--radius-card) 0;'
        'font-size:15px;color:var(--text-secondary);max-width:760px}'
        '.g-legend{display:flex;flex-direction:column;gap:6px;margin:var(--space-sm) 0;'
        'font-size:15px}'
        '.g-leg-item{display:flex;align-items:center;gap:var(--space-sm)}'
        '.g-sw{width:14px;height:14px;border-radius:3px;display:inline-block;flex-shrink:0}'
        '.g-dot{width:10px;height:10px;border-radius:50%;display:inline-block;flex-shrink:0}'
        '.g-red{background:#FCEBEB;border:0.5px solid #F09595}'
        '.g-amber{background:#FAEEDA;border:0.5px solid #FAC775}'
        '.g-blue{background:#E6F1FB;border:0.5px solid #B5D4F4}'
        '.g-green{background:#EAF3DE;border:0.5px solid #C0DD97}'
        '.g-grey{background:var(--bg-page);border:0.5px solid var(--border)}'
        '.g-dot.g-red{background:var(--accent-red);border:none}'
        '.g-dot.g-amber{background:var(--accent-yellow);border:none}'
        '.g-dot.g-green{background:var(--accent-green);border:none}'
        '.g-dot.g-grey{background:var(--border);border:none}'
        '.g-pill{font-size:14px;padding:1px 8px;border-radius:8px;font-weight:500;'
        'display:inline-block;margin-right:4px;flex-shrink:0;border:1px solid transparent}'
        '.g-pteam{background:var(--bg-page);color:var(--text-secondary);'
        'border-color:var(--border)}'
        '.g-pdirect{background:#E6F1FB;color:#0C447C;border-color:#B5D4F4}'
        '.g-pausn{background:#FAEEDA;color:#633806;border-color:#FAC775}'
        '.g-todo{font-size:15px;line-height:1.7}'
        'code{font-family:monospace;background:var(--bg-page);padding:1px 4px;'
        'border-radius:3px;font-size:14px}'
        '.g-sect{scroll-margin-top:var(--space-md)}'
    )

    return (
        '<!DOCTYPE html>\n<html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMiAzMiI+PGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTUuNSIgZmlsbD0iIzFGNEU3OSIvPjxjaXJjbGUgY3g9IjE2IiBjeT0iMTYiIHI9IjEyLjciIGZpbGw9Im5vbmUiIHN0cm9rZT0iI0I3OTI1NyIgc3Ryb2tlLXdpZHRoPSIxLjMiLz48dGV4dCB4PSIxNiIgeT0iMTciIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJjZW50cmFsIiBmb250LWZhbWlseT0iQXJpYWwsSGVsdmV0aWNhLHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTQiIGZvbnQtd2VpZ2h0PSI3MDAiIGZpbGw9IiNmZmZmZmYiPtCY0JI8L3RleHQ+PC9zdmc+">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<title>' + _esc(title) + '</title>'
        '<style>' + DESIGN_TOKENS_CSS + OVERVIEW_SPECIFIC_CSS + OVERVIEW_V2_CSS
        + SIDEBAR_CSS + PROMPT_MODAL_CSS + extra_css + '</style>'
        '</head><body>'
        '<div class="layout-shell">'
        + render_sidebar(active='guide')
        + '<main class="main-content">'
        + head
        + content
        + '</main></div>'
        + PROMPT_MODAL_HTML + PROMPT_MODAL_JS
        + '</body></html>'
    )
