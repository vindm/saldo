# Brand and tone — client documents and communications

> Goal: every artifact a client sees looks like the service of a serious professional practice and speaks in one voice. ALWAYS apply when creating client documents and messages.

## When to apply
- Any document for a client: explanatory/analytical note, letter, instruction, reply in a Finkoper task chat, reminder, invoice/act.
- Any message sent externally on behalf of the operator (Telegram, email, messengers).
- Do NOT apply to internal files (state, dashboards, logs, checklists) — those use their own technical format.

## Where the assets live (brand kit folder)
- `Letterhead_template.docx` — empty branded letterhead: copy it, then fill in (the header, footers, and signature are inserted automatically).
- `Brand_guide.docx` — full guidelines (logo, palette, typography, structure, tone of voice).
- `Logos/` — color/white monogram, horizontal color/white logo (PNG, transparent background).
- `_generator/brand_kit.js` (+ `brand_monogram_color.png`) — a docx-js module for programmatically assembling branded documents (Node + the `docx` package). Exports letterhead/runHeader/footer/styles/title/metaBand/callout/signature and the palette. Use it when a document is assembled in code.

## Identity (in brief)
- Brand: **"[Operator] · bookkeeping support"**. The mark is a monogram of the operator's initials.
- Palette: dark blue `#1F4E79` (primary), blue `#2E5A88` (H2), gold `#B79257` (rules/accent/emblem frame), light-blue background `#EEF3F9` (callouts, the "To/date" band), gray `#595959`, graphite `#333333` (body text).
- Font — **Arial**. Headings dark-blue bold. In-text emphasis — bold, not color or underline.
- Document structure: letterhead header (page 1) + gold rule → title → "To / date" band (light-blue background) → sections, tables with dark-blue headers, "IMPORTANT" callouts (blue bar on the left) → signature block → footer "page N of M".

## Tone of voice
1. **Plain and to the point** — no officialese or bureaucracy; explain complex things in ordinary words.
2. **Specifics** — numbers, deadlines, examples; where appropriate, references to articles of the law.
3. **Always a "what to do"** — end with clear steps.
4. **Respectful and calm** — professional care, no pressure or alarmism.
5. **Client's zone only** — do not surface internal matters (bookkeeping, the manager, pricing) (memory `letter_to_client_scope_principle`). A specific client's tone comes from their `state/behavior.json`.

## Before sending
- Any client document is a **draft**. Sending it externally requires the operator's approval (Rule #3 / `safety-rules.md` §1, §3, §4).

_Related: memory `brand_identity_and_tone`, `letter_to_client_scope_principle`. Full version — `Brand_guide.docx`._
