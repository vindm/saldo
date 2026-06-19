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
from _helpers import track_stale_days  # R8
import _vocab

REPLACEMENT = '�'
# NOTE: these markers are LOGIC KEYS — they are matched against data values in
# _is_filled() to detect "not yet answered" fields. Locale-driven (see _vocab).
_UNKNOWN_MARKERS = _vocab.get('unknown_markers')

from datetime import date as _date
TODAY = _date.today()

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
        for a in accts:
            ac = a.get('account')
            if ac is not None and not (str(ac).startswith('...') or '*' in str(ac)) \
               and not re.fullmatch(r'\d{20}', str(ac)):
                _v(viols, 'warn', cid, 'acct_fmt', f'accounts: account {a.get("id")} is not 20 digits: {ac}')
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

    # F. RISKS -> linked_tasks point to existing tasks
    risks = (states.get('risks') or {}).get('risks', [])
    for r in risks:
        for lt in (r.get('linked_tasks') or []):
            if lt not in ids:
                _v(viols, 'warn', cid, 'risk_link', f'risk {r.get("id")}: linked_task not found: {lt}')

    # H. REGIME: USN/AUSN rate + AUSN invariants
    reg = states.get('regime') or {}
    prim = reg.get('primary') or {}
    rtype, robj, rrate = prim.get('type'), prim.get('object'), prim.get('rate')
    if rtype == 'USN' and robj == 'income' and rrate not in (6, None):
        _v(viols, 'warn', cid, 'usn_rate', f'regime: USN "Income", rate {rrate} (expected 6 — no regional rates)')
    if rtype == 'AUSN':
        if rrate not in (8, 20, None):
            _v(viols, 'warn', cid, 'ausn_rate', f'regime: AUSN rate {rrate} (expected 8 or 20)')
        ba = (states.get('accounts') or {}).get('bank_access') or {}
        if ba.get('is_ausn_partner') is False:
            _v(viols, 'warn', cid, 'ausn_partner', 'regime=AUSN, but accounts.bank_access.is_ausn_partner=False')
        act = [a for a in accts if a.get('closed_at') is None and str(a.get('purpose', '')).startswith(_vocab.get('purpose_primary_prefix'))]
        banks = {a.get('bank_name') for a in act if a.get('bank_name')}
        if len(banks) > 1:
            _v(viols, 'error', cid, 'ausn_one_bank', f'AUSN requires ONE bank, active current accounts in: {sorted(banks)}')

    # I. INN — checksum
    if inn and _inn_valid(inn) is False:
        _v(viols, 'error', cid, 'inn_csum', f'identity: INN fails its checksum: {inn}')
    for cp in (states.get('counterparties') or {}).get('counterparties', []):
        ci = cp.get('inn')
        if ci and str(ci).isdigit() and _inn_valid(ci) is False:
            _v(viols, 'warn', cid, 'cp_inn_csum', f'counterparty {cp.get("id")}: INN fails its checksum: {ci}')

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
