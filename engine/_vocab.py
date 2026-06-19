# -*- coding: utf-8 -*-
"""_vocab.py — locale-specific DATA tokens (the "locale layer").

The engine's internal comparisons are written against canonical ENGLISH values.
But a real practice accumulates its data in its own language: request statuses,
calendar prep/exec statuses, bank-name tokens, the account-purpose prefix,
"unknown" markers, the urgency marker, and a few aggregator markdown labels.

This module exposes those tokens for the ACTIVE locale (``_config.LOCALE``), so:

  (A) the loaders can NORMALIZE incoming discrete statuses to canonical English
      enums (then every downstream comparison + CSS selector stays
      locale-independent), and
  (B) the remaining value matchers (bank-name check, purpose prefix, unknown
      markers, urgency marker, aggregator labels) can match against the active
      locale's data.

NOTE: analytics event classification and wave operation taxonomy used to live
here as keyword/regex tables; they are now JSON-first (history[].kind and
task_type respectively) and the tables were removed.

The 'ru' values are copied faithfully from the ORIGINAL engine
(``accountant/_Планирование/_data/*.py``) — they are GROUND TRUTH. The 'en'
values reproduce the current English demo behavior.

NOTE: every Russian string below is a generic accounting term (statuses,
section headings, keywords) — never a client name.
"""

import _config

# ── canonical English enums (the engine's internal vocabulary; never localized) ──
CANON_REQUEST_WAITING = 'waiting'
CANON_REQUEST_OVERDUE = 'overdue'
CANON_PREP_DONE = 'Done'        # one representative canonical "prep done" value
CANON_PREP_SUBMITTED = 'Submitted'
CANON_EXEC_OVERDUE = 'Overdue'
CANON_EXEC_COMPLETED = 'Completed'
CANON_EXEC_CANCELLED = 'Cancelled'


# ── per-locale DATA-token tables ──────────────────────────────────────────────
_VOCAB = {
    'en': {
        # request statuses (load_requests / load_client_pending)
        'request_waiting': {'waiting'},
        'request_overdue': 'overdue',

        # calendar prep "done" set + exec statuses (load_calendar -> _health)
        'prep_done': ('Done', 'Submitted'),
        'exec_overdue': 'Overdue',
        'exec_done': ('Completed', 'Cancelled'),

        # urgency marker (mental_model derive)
        'urgent_marker': 'URGENT',

        # bank-name tokens for the BIK check (state_lint)
        'bank_name_tokens': ('TBank', 'Tinkoff'),

        # account purpose prefix (state_lint AUSN one-bank check)
        'purpose_primary_prefix': 'primary',

        # state_lint "unknown / not answered" markers
        'unknown_markers': ['❓', 'unknown', 'Unknown', 'UNKNOWN',
                            'not established', 'tbd'],

        # aggregator markdown labels (TG morning-scan parsing)
        'agg': {
            'sp_prefix': 'SP ',                  # name_short prefix to strip / match
            'new_word': 'new',                   # "— N new"
            'needs_reply': 'needs reply',        # marker line + "needs reply:"
        },
    },

    'ru': {
        # request statuses — ORIGINAL _health.py:60,94,96
        'request_waiting': {'ждём', 'ждем'},
        'request_overdue': 'просрочено',

        # calendar prep/exec — ORIGINAL _health.py:48,53,82
        'prep_done': ('Готово', 'Передано'),
        'exec_overdue': 'Просрочено',
        'exec_done': ('Выполнено', 'Отменено'),

        # urgency marker — ORIGINAL _mental_model.py:127,154
        'urgent_marker': 'ГОРИТ',

        # bank-name tokens — ORIGINAL state_lint.py:285
        'bank_name_tokens': ('ТБанк', 'Тинько'),

        # account purpose prefix — ORIGINAL state_lint.py:205
        'purpose_primary_prefix': 'расчётный',

        # unknown markers — ORIGINAL state_lint.py:25
        'unknown_markers': ['❓', 'не выяснено', 'НЕ ВЫЯСНЕНО', 'unknown',
                            'не известно', 'неизвестн'],

        # aggregator markdown labels — ORIGINAL _aggregator.py:106,447,458,467
        'agg': {
            'sp_prefix': 'ИП ',
            'new_word': 'новых',
            'needs_reply': 'требует ответа',
        },
    },
}


def _table():
    return _VOCAB.get(_config.LOCALE, _VOCAB['en'])


def get(key):
    """Top-level locale token by key (falls back to the 'en' table)."""
    t = _table()
    if key in t:
        return t[key]
    return _VOCAB['en'][key]



def agg(key):
    """aggregator sub-table token."""
    t = _table().get('agg', {})
    if key in t:
        return t[key]
    return _VOCAB['en']['agg'][key]


# ── normalization helpers (loader boundary) ───────────────────────────────────
def normalize_request_status(raw):
    """Map a raw (locale) request status -> canonical 'waiting'/'overdue'/raw.

    Case-insensitive against the active locale's tokens. Unknown values pass
    through lower-cased unchanged (so the en demo, which already uses canonical
    values, is a no-op)."""
    s = (raw or '').strip().lower()
    if not s:
        return s
    waiting = {w.lower() for w in get('request_waiting')}
    overdue = get('request_overdue').lower()
    if s in waiting:
        return CANON_REQUEST_WAITING
    if s == overdue:
        return CANON_REQUEST_OVERDUE
    return s


def normalize_prep_status(raw):
    """Map a raw (locale) calendar prep status -> canonical 'Done'/'Submitted'.

    The prep-done set is locale-specific; the first element maps to 'Done', the
    second (if present) to 'Submitted'. Unknown values pass through unchanged."""
    s = (raw or '').strip()
    if not s:
        return s
    done_set = get('prep_done')
    # order-preserving: element 0 -> Done, element 1 -> Submitted
    canon = (CANON_PREP_DONE, CANON_PREP_SUBMITTED)
    for i, tok in enumerate(done_set):
        if s == tok:
            return canon[i] if i < len(canon) else CANON_PREP_DONE
    return s


def normalize_exec_status(raw):
    """Map a raw (locale) calendar exec status -> canonical
    'Overdue'/'Completed'/'Cancelled'. Unknown values pass through unchanged."""
    s = (raw or '').strip()
    if not s:
        return s
    if s == get('exec_overdue'):
        return CANON_EXEC_OVERDUE
    done_set = get('exec_done')
    canon = (CANON_EXEC_COMPLETED, CANON_EXEC_CANCELLED)
    for i, tok in enumerate(done_set):
        if s == tok:
            return canon[i] if i < len(canon) else CANON_EXEC_COMPLETED
    return s
