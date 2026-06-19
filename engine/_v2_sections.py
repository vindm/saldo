"""_v2_sections.py — renders v2 mental_model sections into HTML widgets for the client dashboard.

Added to extend the dashboard with blocks:
  Financial model, Tax calendar, Forward plan, Red flags,
  Behavior pattern, Links between sources, Counterparty dossiers.
"""
import re as _re
from _helpers import _esc
from _strings import t


def _md_to_html(md_text):
    """Minimal markdown -> HTML converter for mental_model sections.
    Supports: H3 (###), bold (**), tables (|), ul (-), blockquote (>),
    paragraphs. NO markdown lib so it works on any machine.
    """
    if not md_text or not md_text.strip():
        return ''

    lines = md_text.split('\n')
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.rstrip()

        # Empty line
        if not s.strip():
            i += 1
            continue

        # H3
        if s.startswith('### '):
            out.append('<h4 class="v2-h4">' + _esc(s[4:].strip()) + '</h4>')
            i += 1
            continue

        # H2 (should not appear inside a section, but just in case)
        if s.startswith('## '):
            i += 1
            continue

        # Table
        if s.startswith('|'):
            tbl_lines = []
            while i < len(lines) and lines[i].rstrip().startswith('|'):
                tbl_lines.append(lines[i].rstrip())
                i += 1
            if tbl_lines:
                out.append(_render_table(tbl_lines))
            continue

        # List
        if s.startswith('- '):
            ul = ['<ul class="v2-ul">']
            while i < len(lines) and lines[i].rstrip().startswith('- '):
                item = lines[i].rstrip()[2:].strip()
                ul.append('<li>' + _md_inline(item) + '</li>')
                i += 1
            ul.append('</ul>')
            out.append('\n'.join(ul))
            continue

        # Blockquote (>)
        if s.startswith('> ') or s.startswith('>'):
            quote_lines = []
            while i < len(lines) and (lines[i].lstrip().startswith('>') or not lines[i].strip()):
                if lines[i].strip():
                    quote_lines.append(lines[i].lstrip().lstrip('>').strip())
                i += 1
            if quote_lines:
                out.append('<blockquote class="v2-quote">' + _md_inline(' / '.join(quote_lines)) + '</blockquote>')
            continue

        # Bold-only line like **Header**:
        out.append('<p class="v2-p">' + _md_inline(s) + '</p>')
        i += 1

    return '\n'.join(out)


def _md_inline(text):
    """Inline markdown: bold, code, italics."""
    # Escape HTML first
    t = _esc(text)
    # **bold** → <strong>
    t = _re.sub(r'\*\*([^*\n]+?)\*\*', r'<strong>\1</strong>', t)
    # `code` → <code>
    t = _re.sub(r'`([^`\n]+?)`', r'<code>\1</code>', t)
    return t


def _render_table(lines):
    """Simple markdown table -> HTML."""
    if not lines:
        return ''
    rows = []
    for ln in lines:
        # Strip leading/trailing |, then split
        ln = ln.strip()
        if ln.startswith('|'): ln = ln[1:]
        if ln.endswith('|'): ln = ln[:-1]
        cells = [c.strip() for c in ln.split('|')]
        rows.append(cells)

    # Skip divider (---)
    data_rows = [r for r in rows if not _re.match(r'^[-:|\s]+$', '|'.join(r))]
    if not data_rows:
        return ''

    out = ['<table class="v2-table"><thead><tr>']
    for cell in data_rows[0]:
        out.append('<th>' + _md_inline(cell) + '</th>')
    out.append('</tr></thead><tbody>')
    for row in data_rows[1:]:
        out.append('<tr>')
        for cell in row:
            out.append('<td>' + _md_inline(cell) + '</td>')
        out.append('</tr>')
    out.append('</tbody></table>')
    return ''.join(out)


# CSS for v2 sections
V2_SECTIONS_CSS = """
.v2-section{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-card);
  padding:var(--space-md);margin:0 0 var(--space-md);box-shadow:var(--shadow-card)}
.v2-section > summary{cursor:pointer;font-size:var(--fs-h2);font-weight:500;list-style:none;
  display:flex;align-items:center;gap:var(--space-sm);padding:0;margin:0}
.v2-section > summary::-webkit-details-marker{display:none}
.v2-section > summary::before{content:"▸";display:inline-block;transition:transform 150ms;color:var(--text-muted)}
.v2-section[open] > summary::before{transform:rotate(90deg)}
.v2-section[open] > summary{margin-bottom:var(--space-md);padding-bottom:var(--space-sm);
  border-bottom:1px solid var(--border)}
.v2-content{font-size:var(--fs-base);line-height:1.6;color:var(--text-primary)}
.v2-content .v2-h4{font-size:var(--fs-base);font-weight:600;margin:var(--space-md) 0 var(--space-xs);color:var(--text-primary)}
.v2-content .v2-h4:first-child{margin-top:0}
.v2-content .v2-p{margin:var(--space-xs) 0}
.v2-content .v2-ul{margin:var(--space-xs) 0 var(--space-sm);padding-left:var(--space-md)}
.v2-content .v2-ul li{margin:var(--space-xs) 0}
.v2-content .v2-quote{margin:var(--space-sm) 0;padding:var(--space-sm) var(--space-md);
  background:var(--blue-bg);border-left:3px solid var(--accent-blue);border-radius:0 var(--radius-btn) var(--radius-btn) 0;
  font-style:normal;color:var(--text-primary)}
.v2-content .v2-table{width:100%;border-collapse:collapse;margin:var(--space-sm) 0;font-size:var(--fs-meta)}
.v2-content .v2-table th{text-align:left;padding:var(--space-xs) var(--space-sm);background:var(--bg-page);
  border-bottom:2px solid var(--border);font-weight:500}
.v2-content .v2-table td{padding:var(--space-xs) var(--space-sm);border-bottom:1px solid var(--border);vertical-align:top}
.v2-content code{background:var(--bg-page);padding:1px 4px;border-radius:3px;font-size:15px}
.v2-content strong{font-weight:600}
.v2-empty{color:var(--text-muted);font-size:var(--fs-meta);font-style:italic}
"""


def render_v2_section(title, icon, md_content, open_by_default=False):
    """Render a single v2 section as <details>."""
    if not md_content or not md_content.strip():
        body = '<div class="v2-empty">' + t('(empty for now)') + '</div>'
    else:
        body = _md_to_html(md_content)
    open_attr = ' open' if open_by_default else ''
    return (
        '<details class="v2-section"' + open_attr + '>'
        '<summary>' + icon + ' ' + _esc(title) + '</summary>'
        '<div class="v2-content">' + body + '</div>'
        '</details>'
    )


def render_v2_block(by_client):
    """Render the v2 sections for the client.

    JSON-first (2026-06-19): only sections with non-empty, state-derived content
    are shown. In the current dashboard that is the "Work plan" (forward_plan from
    state/tasks.json). Financial model / tax calendar / risks / behavior /
    counterparties are rendered by their own dedicated state-driven sections, so
    their v2 counterparts are intentionally left blank upstream and skipped here
    (no duplicate tables).
    """
    if not by_client:
        return ''
    sections = [
        (t('Financial model & trends'), '📊', by_client.get('finmodel', ''), True),
        (t('Tax calendar 2026'), '📅', by_client.get('tax_calendar', ''), True),
        (t('Work plan (2-3 months ahead)'), '🗓️', by_client.get('forward_plan', ''), True),
        (t('Red flags & risks'), '🚩', by_client.get('red_flags', ''), True),
        (t('Client behavior pattern'), '🧠', by_client.get('behavior_pattern', ''), True),
        (t('Links between sources'), '🔗', by_client.get('source_links', ''), False),
        (t('Key counterparty dossiers'), '🤝', by_client.get('counterparties', ''), True),
    ]
    parts = [render_v2_section(t, i, c, o) for t, i, c, o in sections
             if c and c.strip()]
    if not parts:
        return ''
    return '<section class="v2-block">' + ''.join(parts) + '</section>'
