#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""state_lint.py — machine checker of state invariants across all clients.

Why: the confidence that a new fact closed ALL the links should come from a
checker that passed, not from the agent's memory. Every future bug -> a new
invariant here (the system gets monotonically stronger).

Levels: 'error' (blocks dashboard publication), 'warn' (banner).

Usage:
  python3 state_lint.py            # report on all; exit=1 if any error
  python3 state_lint.py <client>   # one client
  import state_lint; v = state_lint.lint_all()
"""
import json, os, re, sys
from datetime import datetime, date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from state_ops import CLIENT_FOLDERS, _client_dir  # single source of the client list
from _helpers import track_stale_days, _CANON_CHANNELS  # R8 + closed source vocab
import _vocab
from _status import CANON_LABEL, normalize_status  # canonical track-status vocabulary
from _track_modal import _TS_RU_LOC, INTERNAL_TS_KEYS  # type_specific label coverage
from _track_attrs import _TASK_TYPE_LABEL  # task_type label coverage
from _client_dashboard_v2 import _CP_RELATION_LABEL, _CP_CATEGORY_LABEL  # counterparty enum label coverage

REPLACEMENT = '�'
# NOTE: these markers are LOGIC KEYS — they are matched against data values in
# _is_filled() to detect "not yet answered" fields. Locale-driven (see _vocab).
_UNKNOWN_MARKERS = _vocab.get('unknown_markers')

from datetime import date as _date
TODAY = _date.today()

# Strong, unambiguous operation phrases in a task TITLE -> the task_type they imply.
# Used by the op_type_mismatch check (R9). CURATED on purpose — NOT every keyword
# from _plan_waves._OP_KEYWORDS — because an incidental token in a title (e.g. «ЛК
# АУСН» inside an access request) must NOT be read as that operation. Add a row only
# when the phrase reliably names the operation regardless of context.
_OP_TITLE_SIGNALS = [
    (re.compile(r'оплат\w*\s+услуг', re.I), 'service_payment', 'service-fee control (оплата услуг)'),
]

def _inn_valid(s):
    """Checksum of a Russian INN (10 or 12 digits). None if not all digits."""
    s = str(s)
    if not s.isdigit():
        return None
    def cc(digs, coefs):
        return (sum(d * c for d, c in zip(digs, coefs)) % 11) % 10
    d = [int(x) for x in s]
    if len(s) == 10:
        return cc(d[:9], [2, 4, 10, 3, 5, 9, 4, 6, 8]) == d[9]
    if len(s) == 12:
        c11 = cc(d[:10], [7, 2, 4, 10, 3, 5, 9, 4, 6, 8])
        c12 = cc(d[:11], [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8])
        return c11 == d[10] and c12 == d[11]
    return False

def _parse_d(s):
    try:
        return datetime.strptime(str(s)[:10], '%Y-%m-%d').date()
    except Exception:
        return None

def _v(viols, sev, client, code, msg):
    viols.append({'severity': sev, 'client': client, 'code': code, 'msg': msg})

def _state_files(cid):
    d = _client_dir(cid) / 'state'
    if not d.exists():
        return {}
    out = {}
    for p in d.glob('*.json'):
        out[p.stem] = p
    return out

def _is_filled(val):
    if val is None:
        return False
    if isinstance(val, bool):
        return False  # a boolean flag (confirmed=false etc.) is not an "answer", don't auto-resolve
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return False
        if any(m in val for m in _UNKNOWN_MARKERS):
            return False
        return True
    if isinstance(val, (list, dict)):
        return len(val) > 0  # empty list/dict = no answer yet
    return True

def _resolve_path(states_data, spec):
    """spec: 'accounts:bank_accounts[id=tbank_main].account' -> value or a KeyError marker."""
    if ':' not in spec:
        return ('ERR', f'bad resolves_when (no ":"): {spec}')
    fkey, path = spec.split(':', 1)
    if fkey not in states_data:
        return ('ERR', f'resolves_when: no file {fkey}.json')
    cur = states_data[fkey]
    for tok in re.split(r'\.(?![^\[]*\])', path):  # split on '.', not inside [...]
        m = re.match(r'^([^\[]+)(\[(.+?)=(.+?)\])?$', tok)
        if not m:
            return ('ERR', f'resolves_when: bad token {tok}')
        key, _, fk, fv = m.group(1), m.group(2), m.group(3), m.group(4)
        if isinstance(cur, dict):
            if key not in cur:
                return ('MISS', None)
            cur = cur[key]
        else:
            return ('MISS', None)
        if fk:  # filter over a list
            if not isinstance(cur, list):
                return ('MISS', None)
            found = [x for x in cur if str(x.get(fk)) == fv]
            if not found:
                return ('MISS', None)
            cur = found[0]
    return ('OK', cur)

def lint_client(cid, _xclient=None):
    viols = []
    files = _state_files(cid)
    states = {}
    # A. FILE HEALTH
    for stem, p in files.items():
        raw = p.read_bytes()
        try:
            txt = raw.decode('utf-8')
        except UnicodeDecodeError as e:
            _v(viols, 'error', cid, 'utf8', f'{stem}.json: invalid UTF-8 ({e})'); continue
        if REPLACEMENT in txt:
            _v(viols, 'error', cid, 'fffd', f'{stem}.json: contains corrupt char U+FFFD')
        try:
            states[stem] = json.loads(txt)
        except Exception as e:
            _v(viols, 'error', cid, 'json', f'{stem}.json: invalid JSON ({e})')
    mm = _client_dir(cid) / 'mental_model.md'
    if mm.exists():
        if REPLACEMENT in mm.read_text(encoding='utf-8', errors='replace'):
            _v(viols, 'error', cid, 'fffd', 'mental_model.md: corrupt char U+FFFD')
    else:
        _v(viols, 'warn', cid, 'no_mm', 'no mental_model.md')

    tasks = (states.get('tasks') or {}).get('tasks', [])

    # B. RESOLVES_WHEN — an open question whose answer is already in state
    for t in tasks:
        rw = t.get('resolves_when')
        if rw and t.get('status') == 'active':
            specs = rw if isinstance(rw, list) else [rw]
            for spec in specs:
                kind, val = _resolve_path(states, spec)
                if kind == 'ERR':
                    _v(viols, 'warn', cid, 'rw_bad', f'{t.get("id")}: {val}')
                elif kind == 'OK' and _is_filled(val):
                    _v(viols, 'error', cid, 'orphan_q',
                       f'{t.get("id")} "{t.get("title","")[:50]}" active, but the answer is already in state ({spec}={str(val)[:40]}) -> close the track')

    # C. BANK ACCOUNTS
    accts = (states.get('accounts') or {}).get('bank_accounts', [])
    if accts:
        prim = [a for a in accts if a.get('is_primary')]
        if len(prim) != 1:
            _v(viols, 'error', cid, 'primary', f'accounts: is_primary must be exactly 1, found {len(prim)}')
        try:
            import _jurisdiction as _J
            _af = (_J.load_jurisdiction((states.get('regime') or {}).get('jurisdiction')).lint or {}).get('account_format')
        except Exception:
            _af = None
        _aflen = int(_af.get('length', 20)) if _af else 20
        for a in accts:
            ac = a.get('account')
            if _af and ac is not None and not (str(ac).startswith('...') or '*' in str(ac)) \
               and not re.fullmatch(r'\d{%d}' % _aflen, str(ac)):
                _v(viols, 'warn', cid, 'acct_fmt', f'accounts: account {a.get("id")} is not {_aflen} digits: {ac}')
            bik = a.get('bik')
            if bik and not re.fullmatch(r'\d{9}', str(bik)):
                _v(viols, 'warn', cid, 'bik_fmt', f'accounts: BIK {a.get("id")} is not 9 digits: {bik}')

    # D. IDENTITY
    ident = states.get('identity') or {}
    inn = ident.get('inn')
    if inn and not re.fullmatch(r'\d{12}', str(inn)):
        _v(viols, 'warn', cid, 'inn', f'identity: sole-proprietor INN is not 12 digits: {inn}')
    ogrn = ident.get('ogrnip')
    if ogrn and not re.fullmatch(r'\d{15}', str(ogrn)):
        _v(viols, 'warn', cid, 'ogrnip', f'identity: OGRNIP is not 15 digits: {ogrn}')

    # E. TASKS
    ids = {}
    for t in tasks:
        tid = t.get('id')
        ids[tid] = ids.get(tid, 0) + 1
        if t.get('status') == 'completed' and not t.get('completed_at'):
            _v(viols, 'warn', cid, 'no_completed_at', f'{tid}: completed without completed_at')
        dd = t.get('due_date')
        if dd:
            try: datetime.strptime(dd, '%Y-%m-%d')
            except Exception: _v(viols, 'warn', cid, 'due_fmt', f'{tid}: due_date not YYYY-MM-DD: {dd}')
    for tid, c in ids.items():
        if c > 1:
            _v(viols, 'error', cid, 'dup_id', f'duplicated task id: {tid} x{c}')

    # E2. STATUS VOCABULARY — flag non-canonical task statuses (info). The
    # dashboard normalizes for display, but stored statuses should be canonical
    # (run tools/migrate_normalize_statuses.py). Once the data is migrated this
    # list is empty and the level can be raised to 'warn' to prevent creep.
    for t in tasks:
        st = t.get('status')
        if st and st not in CANON_LABEL:
            _v(viols, 'info', cid, 'status_noncanon',
               f'{t.get("id")}: non-canonical status "{st}" -> normalize to canonical (run: python3 engine/migrate.py up --apply)')

    # E3. i18n COVERAGE — every operator-facing label must be localizable, so a
    # missing translation surfaces here at build time instead of on screen. Flags
    # task_type values and type_specific keys that have no label (and aren't
    # internal plumbing). Info-level: free-form/bespoke keys (dates/ids baked into
    # the key) show up here as a nudge to normalize the data, not as a hard fail.
    _ts_known, _ts_internal = set(_TS_RU_LOC), set(INTERNAL_TS_KEYS)
    for t in tasks:
        tt = t.get('task_type')
        if tt and tt not in _TASK_TYPE_LABEL:
            _v(viols, 'info', cid, 'i18n_task_type',
               f'{t.get("id")}: task_type "{tt}" has no label (add to _TASK_TYPE_LABEL)')
        # A closed/terminal task must not carry a stale next_action (would show an
        # outdated next step on a done task). Migration 0007 clears it; flag drift.
        if normalize_status(t.get('status') or '') in ('done', 'archived', 'cancelled') \
                and (t.get('next_action') or t.get('next_action_full')):
            _v(viols, 'info', cid, 'stale_next_action',
               f'{t.get("id")}: terminal task still has next_action (clear it on close)')
        for k in (t.get('type_specific') or {}):
            if k not in _ts_known and k not in _ts_internal:
                _v(viols, 'info', cid, 'i18n_ts_key',
                   f'{t.get("id")}: type_specific key "{k}" has no label (add to _TS_RU_LOC or INTERNAL_TS_KEYS)')

    # E4. EVENT SOURCE KEY — a history event's channel lives in `source` (the key
    # add_history_event writes). A stray `by` is a runtime slip that hides the
    # source chip at render time (the renderer falls back to it, but state should
    # be single-key). `event_source_noncanon` (warn) flags any channel head not in
    # the closed vocabulary `_CANON_CHANNELS` (policies/event-sources.md).
    # Migrations 0021/0022/0023 cleaned the historical data into that set; this
    # flags drift. (NB: `assist.by` is a different, legitimate field and is NOT
    # checked here — only history[] events and the task-level source.)
    def _noncanon_channel(val):
        # The channel head (before ':') must be in the closed vocabulary
        # (policies/event-sources.md). Empty source is not flagged here.
        c = str(val or '').split(':', 1)[0].strip().lower()
        return bool(c) and c not in _CANON_CHANNELS
    for t in tasks:
        for ev in (t.get('history') or []):
            if not isinstance(ev, dict):
                continue
            if 'by' in ev:
                _v(viols, 'info', cid, 'event_by_key',
                   f'{t.get("id")}: history event uses `by` for its channel (canonical is `source`; run: python3 engine/migrate.py up --apply)')
            if _noncanon_channel(ev.get('source')):
                _v(viols, 'warn', cid, 'event_source_noncanon',
                   f'{t.get("id")}: source channel "{ev.get("source")}" not in the closed vocabulary (see policies/event-sources.md; run: python3 engine/migrate.py up --apply)')
            # E4b. MISSING SOURCE — every history event must carry a channel (the
            # invariant add_history_event / update_status enforce). A sourceless
            # event rendered a blank chip on «Недавно обновили / закрыли». Migration
            # 0025 backfills the historical ones; this flags any new drift. (warn.)
            if not (str(ev.get('source') or '').strip() or str(ev.get('by') or '').strip()):
                _v(viols, 'warn', cid, 'event_missing_source',
                   f'{t.get("id")}: history event has no source channel (run: python3 engine/migrate.py up --apply)')
        if _noncanon_channel(t.get('source')):
            _v(viols, 'warn', cid, 'event_source_noncanon',
               f'{t.get("id")}: task source channel "{t.get("source")}" not in the closed vocabulary (see policies/event-sources.md)')

    # F. RISKS -> linked_tasks point to existing tasks
    risks = (states.get('risks') or {}).get('risks', [])
    for r in risks:
        for lt in (r.get('linked_tasks') or []):
            if lt not in ids:
                _v(viols, 'warn', cid, 'risk_link', f'risk {r.get("id")}: linked_task not found: {lt}')

    # H. REGIME invariants — thresholds come from the client's jurisdiction pack
    # (jurisdictions/<code>/lint.yaml). Runs a rule only if the pack defines it,
    # so a non-RU client never gets USN/AUSN warnings. (Phase 2 / D3.)
    reg = states.get('regime') or {}
    prim = reg.get('primary') or {}
    rtype, robj, rrate = prim.get('type'), prim.get('object'), prim.get('rate')
    try:
        import _jurisdiction as _J
        _regime_rules = (_J.load_jurisdiction(reg.get('jurisdiction')).lint or {}).get('regime_rules') or {}
    except Exception:
        _regime_rules = {}
    _rule = _regime_rules.get(rtype) or {}
    if rtype == 'USN' and robj == 'income':
        _exp = _rule.get('income_rate_expected')
        if _exp and rrate not in (tuple(_exp) + (None,)):
            _v(viols, 'warn', cid, 'usn_rate', f'regime: USN "Income", rate {rrate} (expected {" or ".join(map(str, _exp))} — no regional rates)')
    if rtype == 'AUSN':
        _exp = _rule.get('rate_expected')
        if _exp and rrate not in (tuple(_exp) + (None,)):
            _v(viols, 'warn', cid, 'ausn_rate', f'regime: AUSN rate {rrate} (expected {" or ".join(map(str, _exp))})')
        if _rule.get('require_partner_flag'):
            ba = (states.get('accounts') or {}).get('bank_access') or {}
            if ba.get('is_ausn_partner') is False:
                _v(viols, 'warn', cid, 'ausn_partner', 'regime=AUSN, but accounts.bank_access.is_ausn_partner=False')
        if _rule.get('require_one_bank'):
            act = [a for a in accts if a.get('closed_at') is None and str(a.get('purpose', '')).startswith(_vocab.get('purpose_primary_prefix'))]
            banks = {a.get('bank_name') for a in act if a.get('bank_name')}
            if len(banks) > 1:
                _v(viols, 'error', cid, 'ausn_one_bank', f'AUSN requires ONE bank, active current accounts in: {sorted(banks)}')

    # H2. Cash-reconciliation gate — pack-declared, jurisdiction-agnostic
    # (`cash_reconciled` / `turnover_source` slots from migration 0017).
    # A turnover-based tax's base must be COMPLETE before the period is settled: where
    # the month's turnover includes cash takings, that cash must be reconciled to the
    # recorded turnover (POS/Moka vs the cash report, or OFD kassa vs declared). The
    # regime OPTS IN via its pack (`require_cash_reconciliation`, same mechanism as
    # `require_one_bank`), so RU USN(income)/AUSN and ID UMKM-final share ONE gate while
    # a non-turnover or no-cash client is never touched. Fires only when: (a) the regime
    # opts in, (b) the period is OPEN (archived history is settled, not re-litigated),
    # (c) turnover is recorded, (d) cash is actually in play — the period's
    # turnover_source names it OR the client has a kassa/OFD/acquiring channel, and
    # (e) cash_reconciled is not true. The staleness_monitor pushes the same flag.
    if _rule.get('require_cash_reconciliation'):
        _acc = states.get('accounts') or {}
        _has_cash_channel = bool(_acc.get('kassas') or _acc.get('kkt_mode')
                                 or _acc.get('acquiring_channels'))
        _TERMINAL_PERIOD = {'archive', 'archived', 'closed', 'paid', 'done'}
        for p in ((states.get('financials') or {}).get('periods') or []):
            if p.get('period_type') != 'month':
                continue
            if str(p.get('status', '')).strip().lower() in _TERMINAL_PERIOD:
                continue
            _tov = next((p.get(k) for k in
                         ('income_usn', 'turnover_idr', 'income_ausn', 'turnover')
                         if p.get(k) is not None), None)
            if _tov is None:
                continue
            _src = str(p.get('turnover_source') or '').lower()
            _src_cash = ('cash' in _src) or ('касса' in _src) or ('moka' in _src)
            if (_src_cash or _has_cash_channel) and p.get('cash_reconciled') is not True:
                _v(viols, 'warn', cid, 'cash_unreconciled',
                   f'period {p.get("period")}: turnover-tax base not confirmed complete — cash '
                   f'takings not reconciled (cash_reconciled={p.get("cash_reconciled")!r}). '
                   f'Reconcile takings to recorded turnover before settling the period.')

    # H3. PAYROLL ROSTER + BPJS COVERAGE — pack-declared (jurisdictions/<code>/lint.yaml →
    # payroll), jurisdiction-agnostic engine. Fires only where the pack opts in AND the client
    # runs payroll (regime.has_employees). Reads the per-employee roster (state/payroll.json,
    # slot from migration 0019). Makes first-class what an aggregate payroll cannot see — a
    # worker missing from a BPJS billing (a UU 24/2011 violation), and a foreign worker whose
    # residency / PPh method / permit are unverified.
    try:
        import _jurisdiction as _J
        _pay_rule = (_J.load_jurisdiction(reg.get('jurisdiction')).lint or {}).get('payroll') or {}
    except Exception:
        _pay_rule = {}
    if _pay_rule and reg.get('has_employees') is True:
        _roster = (states.get('payroll') or {}).get('employees')
        _kasses = _pay_rule.get('bpjs_kasses') or []
        _fw = _pay_rule.get('foreign_worker') or {}
        _warn_days = _fw.get('permit_expiry_warn_days')
        if _pay_rule.get('require_employee_roster') and not _roster:
            _v(viols, 'info', cid, 'payroll_roster_empty',
               'regime.has_employees=true but no employee roster yet (state/payroll.json '
               'employees[] empty) — populate it so BPJS / permit coverage can be checked.')
        for emp in (_roster or []):
            if not isinstance(emp, dict):
                continue
            _eid = emp.get('id') or emp.get('name') or '?'
            _bpjs = emp.get('bpjs') or {}
            # An explicit "missing" on any mandatory kas IS the live risk — surface it.
            for k in _kasses:
                if str(_bpjs.get(k)).lower() == 'missing':
                    _v(viols, 'warn', cid, 'bpjs_coverage_gap',
                       f'employee {_eid}: BPJS {k}=missing — register before billing '
                       f'(an uncovered worker is a UU 24/2011 violation).')
            if emp.get('foreign_national') is True:
                # A KITAS-holder must be in BOTH kasses; an unrecorded status is unverified.
                if _fw.get('require_both_kasses'):
                    for k in _kasses:
                        if _bpjs.get(k) in (None, ''):
                            _v(viols, 'warn', cid, 'tka_bpjs_unverified',
                               f'employee {_eid}: foreign worker, BPJS {k} status not recorded '
                               f'— a KITAS-holder must be in both kasses; verify coverage.')
                # A non-ID-resident is taxed PPh 26 (20% flat), not PPh 21.
                if emp.get('tax_residency') == 'non_id' and emp.get('pph_method') not in ('pph26', None):
                    _v(viols, 'warn', cid, 'pph_method_residency',
                       f'employee {_eid}: tax_residency=non_id but pph_method='
                       f'{emp.get("pph_method")!r} — a non-resident is taxed PPh 26 (20% flat), '
                       f'not PPh 21.')
                # Permit (RPTKA/KITAS) expiry window — plan the renewal before it lapses.
                _permit = emp.get('permit') or {}
                if _warn_days:
                    for pk in ('kitas_expires', 'rptka_expires'):
                        _pd = _parse_d(_permit.get(pk))
                        if _pd is None:
                            continue
                        _days = (_pd - TODAY).days
                        if _days < 0:
                            _v(viols, 'error', cid, 'permit_expired',
                               f'employee {_eid}: {pk} EXPIRED ({_permit.get(pk)}).')
                        elif _days <= _warn_days:
                            _v(viols, 'warn', cid, 'permit_expiring',
                               f'employee {_eid}: {pk} in {_days}d ({_permit.get(pk)}) — plan '
                               f'RPTKA/KITAS renewal; close any BPJS gap before it.')

    # H4. OBLIGATION CADENCE — pack-declared recurring obligations (jurisdictions/<code>/
    # obligations.yaml). Where an obligation's cadence depends on business scale (LKPM: an
    # Usaha Kecil files per SEMESTER, medium/large per QUARTER — BKPM 5/2025 §285), check that
    # the client's calendar entries fall in the scale-correct months. Catches the exact drift
    # that put a quarterly LKPM (a phantom Q3) on an Usaha Kecil. Pack-declared + jurisdiction-
    # agnostic: runs only where the pack declares an applicable, scale-driven obligation.
    try:
        import _jurisdiction as _Jb
        _obls = _Jb.load_jurisdiction(reg.get('jurisdiction')).obligations
    except Exception:
        _obls = {}
    if _obls:
        _TERM_CAL = {'paid', 'done', 'submitted', 'completed', 'cancelled'}
        _ident = states.get('identity') or {}
        _scale_raw = str(_ident.get('skala_usaha') or '').lower()
        _scale = ('kecil' if 'kecil' in _scale_raw else
                  'menengah' if 'menengah' in _scale_raw else
                  'besar' if 'besar' in _scale_raw else None)
        _fin = states.get('financials') or {}
        _entries = [e for k, v in _fin.items()
                    if isinstance(v, list) and re.fullmatch(r'tax_calendar_\d{4}', k)
                    for e in v if isinstance(e, dict)]
        for _code, _obl in _obls.items():
            _cbs = (_obl or {}).get('cadence_by_scale')
            if not _cbs:
                continue  # fixed-cadence (annual etc.) obligations aren't scale-checked here
            if _obl.get('applies_when') == 'penanaman_modal_registered' \
                    and not _ident.get('penanaman_modal'):
                continue
            if _scale is None or _scale not in _cbs:
                continue  # scale unknown / not covered -> can't judge, stay silent
            _months = set((_cbs[_scale] or {}).get('deadline_months') or [])
            if not _months:
                continue
            _tok = str(_obl.get('match') or _code).upper()
            _every = (_cbs[_scale] or {}).get('every')
            for e in _entries:
                if _tok not in str(e.get('what') or '').upper():
                    continue
                if str(e.get('status', '')).strip().lower() in _TERM_CAL:
                    continue  # a filed past entry is history — don't relitigate its cadence
                _ed = _parse_d(e.get('date'))
                if _ed and _ed.month not in _months:
                    _v(viols, 'warn', cid, 'obligation_cadence_mismatch',
                       f'{_code.upper()} entry {e.get("date")} falls in month {_ed.month}, but a '
                       f'{_scale} client files {_every} (deadline months {sorted(_months)}) — '
                       f'wrong cadence? (scale-driven obligation, jurisdictions/<code>/obligations.yaml)')

    # H5. DELIVERY vs DERIVED CADENCE — the bookkeeping cadence the regime REQUIRES is derived
    # (engine/_cadence.py, docs/CADENCE.md); the rate at which the client actually delivers source
    # documents (behavior.json -> bank_statement_frequency) must not be LOOSER than it, or the
    # period cannot be posted in time. Flags e.g. a payroll (monthly-floor) client who only sends
    # statements quarterly. Silent when either side is unknown (on_request / undetermined regime).
    if _obls:
        try:
            import _cadence as _Cad
            _deliv = _Cad.delivery_cadence((states.get('behavior') or {}).get('bank_statement_frequency'))
            if _deliv:
                _cad_state = {'regime': reg,
                              'payroll': states.get('payroll') or {},
                              'financials': states.get('financials') or {}}
                _req = _Cad.resolve_bookkeeping_cadence(_obls, _cad_state, TODAY.strftime('%Y-%m'))
                if _Cad.is_delivery_looser(_deliv, _req):
                    _v(viols, 'warn', cid, 'delivery_looser_than_cadence',
                       f'source docs arrive {_deliv} but the regime requires {_req} bookkeeping — '
                       f'cannot post {_req} on {_deliv} statements '
                       f'(behavior.json bank_statement_frequency; see docs/CADENCE.md)')
        except Exception:
            pass

    # H4. PAYROLL RUN — per-employee lines carried on a payroll task (type_specific.payroll_lines,
    # see docs/PAYROLL-CALCULATION-REVIEW-PROPOSAL.md). The engine checks CONSISTENCY, not the math:
    # the breakdown must reconcile to the period aggregate the rest of the engine renders, every
    # line must point at a real roster employee, and the line must agree with that employee's
    # coverage/residency (mirrors H3). Correctness of each figure is the parity review's job.
    _emp_by_id = {e.get('id'): e for e in ((states.get('payroll') or {}).get('employees') or [])
                  if isinstance(e, dict)}
    _periods_by_id = {p.get('period'): p for p in ((states.get('financials') or {}).get('periods') or [])
                      if isinstance(p, dict)}
    for _t in tasks:
        _ts = _t.get('type_specific') or {}
        _lines = _ts.get('payroll_lines')
        if not isinstance(_lines, list) or not _lines:
            continue
        _tid = _t.get('id')
        _sum_pph = 0
        for _ln in _lines:
            if not isinstance(_ln, dict):
                continue
            _sum_pph += (_ln.get('pph') or 0)
            _eid = _ln.get('employee_id')
            _emp = _emp_by_id.get(_eid)
            if _emp is None:
                _v(viols, 'warn', cid, 'payroll_line_emp',
                   f'{_tid}: payroll line references unknown employee_id {_eid!r}')
                continue
            # coverage tie-in: a kas marked "missing" must carry no posted contribution
            _lb = _ln.get('bpjs') or {}
            _eb = _emp.get('bpjs') or {}
            for _k in ('kesehatan', 'ketenagakerjaan'):
                if str(_eb.get(_k)).lower() == 'missing':
                    _kc = _lb.get(_k) or {}
                    if (_kc.get('employee') or 0) or (_kc.get('employer') or 0):
                        _v(viols, 'warn', cid, 'payroll_coverage',
                           f'{_tid}: {_eid} BPJS {_k}=missing on roster but a contribution is posted '
                           f'in the run — register the worker or drop the line.')
            # method tie-in: a non-resident must be PPh 26, not TER/annualisasi
            if _emp.get('tax_residency') == 'non_id' and _ln.get('method') not in (None, 'pph26'):
                _v(viols, 'warn', cid, 'payroll_method',
                   f'{_tid}: {_eid} is non-resident but line method={_ln.get("method")!r} — '
                   f'a non-resident is taxed PPh 26 (20% flat).')
        # totals self-consistency
        _tot = _ts.get('totals') or {}
        if _tot.get('pph') is not None and _tot.get('pph') != _sum_pph:
            _v(viols, 'warn', cid, 'payroll_totals',
               f'{_tid}: totals.pph={_tot.get("pph")} != sum(lines.pph)={_sum_pph}')
        # reconciliation to the period aggregate the engine renders
        _masa = _ts.get('period')
        _per = _periods_by_id.get(_masa)
        if _per is not None:
            _agg = (_per.get('taxes') or {}).get('pph21')
            if _agg is not None and _agg != _sum_pph:
                _v(viols, 'warn', cid, 'payroll_reconcile',
                   f'{_tid}: payroll PPh sum {_sum_pph} != financials period {_masa} taxes.pph21 '
                   f'{_agg} — the per-employee breakdown must reconcile to the period total.')

    # I. INN — checksum
    if inn and _inn_valid(inn) is False:
        _v(viols, 'error', cid, 'inn_csum', f'identity: INN fails its checksum: {inn}')
    for cp in (states.get('counterparties') or {}).get('counterparties', []):
        ci = cp.get('inn')
        if ci and str(ci).isdigit() and _inn_valid(ci) is False:
            _v(viols, 'warn', cid, 'cp_inn_csum', f'counterparty {cp.get("id")}: INN fails its checksum: {ci}')
        # i18n coverage: relation_type/category are operator-facing enums; an
        # unmapped value renders the raw code (uppercased by .cp-meta). Mirror
        # i18n_task_type so a new value can't ship without a localized label.
        rel = cp.get('relation_type')
        if rel and rel not in _CP_RELATION_LABEL:
            _v(viols, 'info', cid, 'i18n_cp_label',
               f'counterparty {cp.get("id")}: relation_type "{rel}" has no label (add to _CP_RELATION_LABEL)')
        ccat = cp.get('category')
        if ccat and ccat not in _CP_CATEGORY_LABEL:
            _v(viols, 'info', cid, 'i18n_cp_label',
               f'counterparty {cp.get("id")}: category "{ccat}" has no label (add to _CP_CATEGORY_LABEL)')

    # J. Tracks: overdue, open_question without resolves_when, stale
    for t2 in tasks:
        if t2.get('status') == 'active':
            dd = _parse_d(t2.get('due_date')) if t2.get('due_date') else None
            if dd and dd < TODAY:
                days = (TODAY - dd).days
                # grace: month-close is routinely shifted (internal deadline ~20th).
                # >14 days overdue = warn, 1-14 = info.
                sev = 'warn' if days > 14 else 'info'
                _v(viols, sev, cid, 'overdue', f'{t2.get("id")} active, due {t2.get("due_date")} has passed ({days} days)')
            if t2.get('task_type') == 'open_question':
                if not t2.get('resolves_when') and not t2.get('no_auto_resolve'):
                    _v(viols, 'info', cid, 'no_resolves_when', f'{t2.get("id")} open_question without resolves_when (add a watcher path)')
                cr = _parse_d(t2.get('created_at')) if t2.get('created_at') else None
                if cr and (TODAY - cr).days > 120:
                    _v(viols, 'info', cid, 'stale_q', f'{t2.get("id")} open_question has hung for {(TODAY-cr).days} days — revisit')
            # assist coverage: a priority/question without a fresh system hypothesis+actions
            if t2.get('priority') == 'high' or t2.get('task_type') == 'open_question':
                _a = t2.get('assist') or {}
                if not _a.get('actions'):
                    _v(viols, 'info', cid, 'assist_gap', f'{t2.get("id")} without assist (no system hypothesis/actions)')
                else:
                    _ua = _parse_d(_a.get('updated_at')) if _a.get('updated_at') else None
                    if _ua and (TODAY - _ua).days > 30:
                        _v(viols, 'info', cid, 'assist_stale', f'{t2.get("id")} assist is stale ({(TODAY-_ua).days} days)')

    # R8: stale active tracks (no movement past the priority threshold)
    for t2 in tasks:
        _sd = track_stale_days(t2, TODAY)
        if _sd is not None:
            _v(viols, 'info', cid, 'stale_track', f'{t2.get("id")} no movement for {_sd} days ({t2.get("priority","normal")}) — nudge or postpone')

    # R9: type<->title mismatch (classification drift guard). The title is human
    # prose, NOT the classifier — task_type is the source of truth. But when a title
    # reliably names an operation (see _OP_TITLE_SIGNALS) while task_type says
    # something else, the type is probably wrong: flag it (INFO) so the operator /
    # runtime re-types it. Curated signals only, so an incidental title token can't
    # raise a false positive. Terminal tasks are skipped.
    # Inquiry/annotation types are NOT operations — a question whose text mentions an
    # operation («из какой выручки оплатить услуги») is still a question, not that
    # operation. Skip them (mirrors migration 0014's type gate) so they don't false-flag.
    _NOT_AN_OPERATION = ('open_question', 'regime_question', 'note')
    for t2 in tasks:
        if normalize_status(t2.get('status') or '') in ('done', 'archived', 'cancelled'):
            continue
        _tt = (t2.get('task_type') or '').strip()
        if _tt in _NOT_AN_OPERATION:
            continue
        _ttl = (t2.get('title') or t2.get('what') or '')
        for _rx, _exp, _lbl in _OP_TITLE_SIGNALS:
            if _rx.search(_ttl) and _tt != _exp:
                _v(viols, 'info', cid, 'op_type_mismatch',
                   f'{t2.get("id")}: title reads as {_lbl} but task_type is "{_tt or "—"}" (expected "{_exp}")')

    # NOTE (JSON-first, 2026-06-19): the old "Analysis & recommendations narrative
    # freshness" lint used to PARSE the ```analysis JSON block out of mental_model.md.
    # That block is gone — the dashboard's analysis zone is now derived from
    # state/tasks.json (see _brief.build_client_analysis_from_state). The engine no
    # longer parses mental_model.md for any rendered content, so this check was removed.

    # K. blocked_by -> existing tasks
    for t2 in tasks:
        for b in (t2.get('blocked_by') or []):
            if b not in ids:
                _v(viols, 'warn', cid, 'blocked_ref', f'{t2.get("id")}: blocked_by on a non-existent task {b}')

    # K2. ref_resolves — every task type_specific.refs[].id must resolve to an existing entity of
    # its type (docs/ENTITY-LINKING-ARCHITECTURE.md). One generic check covers every entity type;
    # a type we don't resolve yet is skipped (never a false error). Generalizes risk_link.
    _entity_ids = {
        'employee':     {e.get('id') for e in ((states.get('payroll') or {}).get('employees') or []) if isinstance(e, dict)},
        'period':       {p.get('period') for p in ((states.get('financials') or {}).get('periods') or []) if isinstance(p, dict)},
        'counterparty': {c.get('id') for c in ((states.get('counterparties') or {}).get('counterparties') or []) if isinstance(c, dict)},
        'risk':         {r.get('id') for r in risks if isinstance(r, dict)},
        'account':      {a.get('id') for a in accts if isinstance(a, dict)},
        'task':         set(ids.keys()),
    }
    for t2 in tasks:
        for _ref in ((t2.get('type_specific') or {}).get('refs') or []):
            if not isinstance(_ref, dict):
                continue
            _rt, _ri = _ref.get('type'), _ref.get('id')
            if _rt in _entity_ids and _ri not in _entity_ids[_rt]:
                _v(viols, 'warn', cid, 'ref_resolves',
                   f'{t2.get("id")}: ref {{type:{_rt}, id:{_ri}}} does not resolve to an existing {_rt}')

    # L. risk severity
    for r in risks:
        if r.get('severity') not in ('green', 'yellow', 'red'):
            _v(viols, 'warn', cid, 'risk_sev', f'risk {r.get("id")}: severity "{r.get("severity")}" outside {{green,yellow,red}}')
    # L2. risk kind (kind-split, 2026-06-13): risk/question/blocker or absent are allowed
    for r in risks:
        k = r.get('kind')
        if k is not None and k not in ('risk', 'question', 'blocker'):
            _v(viols, 'warn', cid, 'risk_kind', f'risk {r.get("id")}: kind "{k}" outside {{risk,question,blocker}}')

    # M. TBank -> BIK 044525974; duplicate account numbers within a client
    seen_acc = {}
    for a in accts:
        bn = str(a.get('bank_name') or '')
        # NOTE: bank-name tokens are LOGIC KEYS matched against bank_name data
        # values; locale-driven (see _vocab).
        if any(_tok in bn for _tok in _vocab.get('bank_name_tokens')) and a.get('bik') and str(a.get('bik')) != '044525974':
            _v(viols, 'warn', cid, 'tbank_bik', f'accounts {a.get("id")}: TBank, but BIK {a.get("bik")} (expected 044525974)')
        if a.get('account'):
            seen_acc.setdefault(str(a.get('account')), []).append(a.get('id'))
    for ac, lst in seen_acc.items():
        if len(lst) > 1:
            _v(viols, 'error', cid, 'dup_acct', f'duplicated account number {ac} in {lst}')

    # N. last_updated not in the future
    for stem, data in states.items():
        if isinstance(data, dict) and data.get('last_updated'):
            lu = _parse_d(data.get('last_updated'))
            if lu and lu > TODAY:
                _v(viols, 'error', cid, 'lu_future', f'{stem}.json: last_updated in the future: {data.get("last_updated")}')

    # O. TG channel resolvability (rotation-drift guard)
    # The TG daemon derives its rotation set from behavior.channels (every client
    # with a telegram channel), NOT from a hand-kept list — so a client can no
    # longer be silently dropped. But a telegram channel is only USEFUL if the
    # daemon can resolve the chat: it needs a @username, OR a phone to resolve by,
    # OR a cached peer_id. A telegram channel recorded only as a display name with
    # none of those is unreachable (Telethon get_entity cannot resolve a display
    # name) and would fall out of every sync — surface it instead of dropping it.
    beh = states.get('behavior') or {}
    bch = beh.get('channels') or {}
    _all_ch = []
    _p = bch.get('primary')
    if isinstance(_p, dict):
        _all_ch.append(_p)
    _all_ch += [c for c in (bch.get('secondary') or []) if isinstance(c, dict)]
    # The daemon syncs the FIRST telegram channel (primary, then secondary order) —
    # mirror tg_sync.tg_resolver exactly so the lint judges the channel actually
    # synced, not auxiliary ones (e.g. a client's assistant TG channel).
    _tg = next((c for c in _all_ch if c.get('type') == 'telegram'), None)
    if _tg is not None:
        _has_phone = any(c.get('type') == 'phone' and str(c.get('id') or '').strip()
                         for c in _all_ch)
        _cid_val = str(_tg.get('id') or '').strip()
        _resolvable = (
            _cid_val.startswith('@')
            or bool(str(_tg.get('username') or '').strip())
            or _tg.get('peer_id') not in (None, '')
            or _has_phone
        )
        if not _resolvable:
            _v(viols, 'warn', cid, 'tg_unresolvable',
               f'behavior: telegram channel "{_cid_val[:40]}" has no @username, no phone, '
               f'and no cached peer_id — the TG daemon cannot resolve it (chat falls out of sync)')
    # O2. TG handle canon (migration 0027): a handle channel must carry username WITHOUT '@'
    # and id == '@'+username. Display-name-only channels (no username) are exempt.
    for c in _all_ch:
        if c.get('type') != 'telegram':
            continue
        _u = str(c.get('username') or '').strip()
        if not _u:
            continue  # no handle → nothing to canonicalize
        _idv = str(c.get('id') or '').strip()
        if _u.startswith('@') or _idv != '@' + _u.lstrip('@'):
            _v(viols, 'warn', cid, 'tg_channel_noncanon',
               f'behavior: telegram handle not canon (want username="<handle>" no @, '
               f'id="@<handle>"): username={_u!r} id={_idv!r}')
    # O3. Communication-graph coverage (migration 0028): every telegram endpoint flagged
    # sync:true must carry a resolver (peer_id or @username), else the daemon can't read it.
    for ep in (bch.get('endpoints') or []):
        if not isinstance(ep, dict) or ep.get('transport') != 'telegram' or not ep.get('sync'):
            continue
        if ep.get('peer_id') in (None, '') and not str(ep.get('username') or '').strip():
            _v(viols, 'warn', cid, 'endpoint_unsynced',
               f'behavior: telegram endpoint "{str(ep.get("id"))[:40]}" (role {ep.get("role")}) '
               f'is sync:true but has no peer_id and no @username — the daemon cannot read it')

    # collect for cross-client reconciliation
    if _xclient is not None:
        for cp in (states.get('counterparties') or {}).get('counterparties', []):
            nm, cinn = (cp.get('name') or '').strip().lower(), cp.get('inn')
            if nm and cinn_ok(cinn):
                _xclient['cp'].setdefault(nm, {}).setdefault(str(cinn), set()).add(cid)
        for a in accts:
            if a.get('account'):
                _xclient['acc'].setdefault(str(a.get('account')), set()).add(cid)
    return viols

def cinn_ok(v):
    return v is not None and re.fullmatch(r'\d{10,12}', str(v))

def lint_all():
    viols = []
    xclient = {'cp': {}, 'acc': {}}
    for cid in CLIENT_FOLDERS:
        try:
            viols += lint_client(cid, _xclient=xclient)
        except Exception as e:
            _v(viols, 'error', cid, 'lint_crash', f'linter crashed: {e}')
    # G1. the same counterparty with different INNs across clients
    for nm, inns in xclient['cp'].items():
        if len(inns) > 1:
            detail = '; '.join(f'{i}: {sorted(cl)}' for i, cl in inns.items())
            _v(viols, 'warn', '(cross)', 'cp_inn', f'counterparty "{nm}" with different INNs — {detail}')
    # G2. the same account number across multiple clients = a data error
    for ac, cls in xclient['acc'].items():
        if len(cls) > 1:
            _v(viols, 'error', '(cross)', 'acct_multi', f'account {ac} is listed under multiple clients: {sorted(cls)}')
    return viols

def report(viols, show_info=False):
    errs = [v for v in viols if v['severity'] == 'error']
    warns = [v for v in viols if v['severity'] == 'warn']
    infos = [v for v in viols if v['severity'] == 'info']
    for v in errs:
        print(f"  [ERROR] [{v['client']}] {v['code']}: {v['msg']}")
    for v in warns:
        print(f"  [WARN]  [{v['client']}] {v['code']}: {v['msg']}")
    if show_info:
        for v in infos:
            print(f"  [INFO]  [{v['client']}] {v['code']}: {v['msg']}")
    tail = f", {len(infos)} info" + ("" if show_info else " (run state_lint.py for details)")
    print(f"\nTotal: {len(errs)} error, {len(warns)} warn{tail}")
    return len(errs)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in CLIENT_FOLDERS:
        v = lint_client(sys.argv[1])
    else:
        v = lint_all()
    n_err = report(v, show_info=True)
    sys.exit(1 if n_err else 0)
