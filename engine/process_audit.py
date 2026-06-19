#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""process_audit.py — self-audit of the PROCESS (read-only).

A third axis of control alongside state_lint (data invariants) and
system_integrity_check (docs vs. reality). It reconciles "my hands vs. the
pipeline": from the traces (history.jsonl, snapshots, tasks.json, file
contents) — were the working rules followed? It fixes and blocks nothing,
only reports.

Principle after the v1 shake-out: trust LOGICAL labels inside the data (ts in
history, event dates, snapshot names, actual file contents). Checks based on
filesystem mtime are unreliable on a cloud-sync mount (they catch re-syncs) ->
INFO only.

Core checks (v2):
  1. snapshot        — how many significant events accumulated since the last
                       brain_*.tar.gz and how many days old it is (logical
                       labels -> WARN is reliable).
  2. source          — a track event (history, auto=false) more RECENT than the
                       window, with no source (source attribution is mandatory;
                       the historical backlog is left untouched).
  3. integrity       — the real guardian of the UTF-8 rule: UTF-8 / truncation /
                       broken JSON / broken .py in text sources (the reason the
                       rule exists).
  4. state<->history — INFO: state/*.json with mtime much later than the last
                       history record (a soft signal, mtime is noisy on a
                       cloud-sync mount).

Run:  python3 _data/process_audit.py [client-substr] [--days N]
"""
import os, sys, glob, json, re
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN = os.path.normpath(os.path.join(HERE, '..'))        # project root
SNAP_DIR = os.path.join(PLAN, 'Archive', 'snapshots')

SOURCE_WINDOW_DAYS = 14       # check source only on recent events (the rule is new)
SNAP_EVENT_CAP     = 15       # this many significant events since a snapshot = time for a snapshot
SNAP_AGE_WARN      = 7        # days since the last snapshot for INFO
STATE_HIST_TOL_H   = 24       # h: state<->history gap for INFO (mtime noise)

CORE_STATE = ['identity', 'regime', 'accounts', 'financials',
              'counterparties', 'risks', 'behavior', 'tasks', 'real_estate']

WARN, INFO = [], []
def warn(m): WARN.append(m)
def info(m): INFO.append(m)

def parse_iso(s):
    if not s: return None
    s = str(s).strip().replace('Z', '+00:00')
    try: dt = datetime.fromisoformat(s)
    except ValueError:
        m = re.match(r'(\d{4}-\d{2}-\d{2})', s)
        if not m: return None
        dt = datetime.fromisoformat(m.group(1))
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()

def now_epoch(): return datetime.now(timezone.utc).timestamp()
def short(s, n=80):
    s = ' '.join(str(s).split()); return s if len(s) <= n else s[:n-1] + '…'

def client_dirs(flt=None):
    out = []
    for f in sorted(glob.glob(os.path.join(PLAN, '**', 'state', 'tasks.json'), recursive=True)):
        cdir = os.path.dirname(os.path.dirname(f))
        name = os.path.basename(cdir)
        if flt and flt.lower() not in name.lower(): continue
        out.append((name, cdir))
    return out

def last_history_ts(cdir):
    hp = os.path.join(cdir, 'history.jsonl')
    if not os.path.exists(hp): return None
    last = None
    with open(hp, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: t = parse_iso(json.loads(line).get('ts'))
            except Exception: continue
            if t and (last is None or t > last): last = t
    return last

# ---------- 1. snapshot freshness (reliable: logical labels) ----------
def check_snapshot(clients):
    snaps = glob.glob(os.path.join(SNAP_DIR, 'brain_*.tar.gz'))
    if not snaps:
        warn("[snapshot] no brain_*.tar.gz at all — pipeline has no rollback points"); return
    def sts(p):
        m = re.search(r'brain_(\d{8})_(\d{6})', os.path.basename(p))
        if not m: return os.path.getmtime(p)
        g = m.groups()
        return parse_iso(f"{g[0][:4]}-{g[0][4:6]}-{g[0][6:8]}T{g[1][:2]}:{g[1][2:4]}:{g[1][4:6]}") or os.path.getmtime(p)
    newest = max(snaps, key=sts); nts = sts(newest)
    after = 0
    for _, cdir in client_dirs():
        hp = os.path.join(cdir, 'history.jsonl')
        if not os.path.exists(hp): continue
        with open(hp, encoding='utf-8', errors='replace') as fh:
            for line in fh:
                line = line.strip()
                if not line: continue
                try: t = parse_iso(json.loads(line).get('ts'))
                except Exception: continue
                if t and t > nts: after += 1
    age = (now_epoch() - nts) / 86400
    if after > SNAP_EVENT_CAP:
        warn(f"[snapshot] {after} events since the last snapshot ({os.path.basename(newest)}) — time to make a snapshot")
    elif age > SNAP_AGE_WARN:
        info(f"[snapshot] last snapshot is {age:.0f} days old, events since: {after}")
    else:
        info(f"[snapshot] fresh ({age:.1f} days), events since: {after}")

# ---------- 2. source on recent events (logical dates) ----------
def check_source(clients, window_days):
    cutoff = now_epoch() - window_days * 86400
    miss, samples = 0, []
    for name, cdir in clients:
        try: d = json.load(open(os.path.join(cdir, 'state', 'tasks.json'), encoding='utf-8'))
        except Exception: continue
        for tr in d.get('tasks', []):
            for ev in tr.get('history', []):
                if ev.get('auto'): continue
                t = parse_iso(ev.get('date'))
                if t is None or t < cutoff: continue          # only recent events
                if not ev.get('source'):
                    miss += 1
                    if len(samples) < 8:
                        samples.append(f"{name}/{tr.get('id')} ({ev.get('date')}): {short(ev.get('event'),60)}")
    if miss:
        warn(f"[source] recent events (<={window_days} days) without source: {miss}")
        for s in samples: info(f"    · {s}")
    else:
        info(f"[source] no recent events without source (window {window_days} days)")

# ---------- 3. text-file integrity — the real guardian of the UTF-8 rule ----------
def check_integrity(clients):
    files = []
    files += glob.glob(os.path.join(HERE, '*.py'))
    files += glob.glob(os.path.join(PLAN, 'policies', '**', '*.md'), recursive=True)
    j = os.path.join(PLAN, 'policies', 'decisions_log.md')
    if os.path.exists(j): files.append(j)
    for _, cdir in clients:
        files += glob.glob(os.path.join(cdir, 'state', '*.json'))
        for nm in ('mental_model.md', 'history.jsonl'):
            p = os.path.join(cdir, nm)
            if os.path.exists(p): files.append(p)
    bad = 0
    for f in files:
        if f.endswith('.bak') or '.bak_' in os.path.basename(f): continue
        rel = os.path.relpath(f, PLAN)
        try:
            raw = open(f, 'rb').read()
        except Exception as e:
            warn(f"[integrity] {rel}: cannot read ({e})"); bad += 1; continue
        if b'\x00' in raw:
            warn(f"[integrity] {rel}: NUL byte in file"); bad += 1; continue
        try:
            txt = raw.decode('utf-8')
        except UnicodeDecodeError as e:
            warn(f"[integrity] {rel}: UTF-8 truncation (pos {e.start}) — multi-byte text torn"); bad += 1; continue
        if f.endswith('.json'):
            try: json.loads(txt)
            except Exception as e:
                warn(f"[integrity] {rel}: broken JSON ({short(e,50)})"); bad += 1
        elif f.endswith('.jsonl'):
            for i, ln in enumerate(txt.splitlines(), 1):
                if ln.strip():
                    try: json.loads(ln)
                    except Exception:
                        warn(f"[integrity] {rel}: broken JSONL line #{i}"); bad += 1; break
        elif f.endswith('.py'):
            try: compile(txt, f, 'exec')
            except SyntaxError as e:
                warn(f"[integrity] {rel}: .py syntax ({short(e,50)})"); bad += 1
    if not bad:
        info(f"[integrity] {len(files)} text sources — UTF-8/JSON/.py are clean")

# ---------- 4. state<->history (INFO: mtime is noisy) ----------
def check_state_history(clients):
    for name, cdir in clients:
        last_ts = last_history_ts(cdir)
        sdir = os.path.join(cdir, 'state')
        present = [os.path.join(sdir, c + '.json') for c in CORE_STATE
                   if os.path.exists(os.path.join(sdir, c + '.json'))]
        if last_ts is None:
            if present: info(f"[state<->history] {name}: has state/, but history.jsonl is empty — writes bypassing state_ops?")
            continue
        flagged = [os.path.basename(f) for f in present
                   if (os.path.getmtime(f) - last_ts) > STATE_HIST_TOL_H * 3600]
        if flagged:
            info(f"[state<->history] {name}: {', '.join(flagged)} with mtime >{STATE_HIST_TOL_H}h after history (likely a cloud-sync re-sync; verify if the edit is real)")

def main():
    flt, window = None, SOURCE_WINDOW_DAYS
    args = sys.argv[1:]
    if '--days' in args:
        i = args.index('--days'); window = int(args[i+1]); del args[i:i+2]
    if args: flt = args[0]
    clients = client_dirs(flt)
    print(f"=== PROCESS SELF-AUDIT · {datetime.now().strftime('%Y-%m-%d %H:%M')} · clients: {len(clients)} ===")
    check_snapshot(clients)
    check_source(clients, window)
    check_integrity(clients)
    check_state_history(clients)
    print()
    if WARN:
        print(f"WARN ({len(WARN)}):")
        for w in WARN: print("  •", w)
    else:
        print("WARN: none — process followed as far as the available traces show")
    if INFO:
        print(f"\nINFO ({len(INFO)}):")
        for i in INFO: print("  ", i)
    print(f"\nResult: WARN={len(WARN)}, INFO={len(INFO)}  (read-only, nothing changed)")
    return 0

if __name__ == '__main__':
    sys.exit(main())
