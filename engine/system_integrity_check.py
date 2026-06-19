#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""system_integrity_check.py — machine watchdog for "docs vs. reality".

Read-only audit of the system: changes NOTHING, only reports discrepancies.
Run it at the start of work and after any structural changes.

    python3 _data/system_integrity_check.py

Categories:
  [ERROR]  — integrity/breakage (NUL, broken JSON, missing state dir, live
              reading of an archived file, a revived deprecation). Exit != 0.
  [WARN]   — doc drift, orphan modules, a missing core state file.
  [OK]     — section is clean.

These checks were derived from the audit of 2026-06-07 (see decisions_log.md).
"""
import os, sys, re, glob, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PLAN = os.path.dirname(HERE)  # project root
import state_ops

errors, warns = [], []
def err(cat, msg):  errors.append((cat, msg))
def warn(cat, msg): warns.append((cat, msg))

CORE_STATE = ['identity','regime','accounts','financials','counterparties','risks','behavior','tasks']
clients = list(state_ops.CLIENT_FOLDERS.items())
n_clients = len(clients)

# --- 1. Clients: CLIENT_FOLDERS vs. real state/ + core files ---
for cid, folder in clients:
    sd = os.path.join(PLAN, folder, 'state')
    if not os.path.isdir(sd):
        err('Clients', f'{cid}: no state/ folder ({folder})')
        continue
    for core in CORE_STATE:
        if not os.path.exists(os.path.join(sd, core + '.json')):
            warn('Clients', f'{cid}: missing core file state/{core}.json')

# --- 2. Data integrity: JSON validity, UTF-8, NUL ---
for cid, folder in clients:
    for jf in glob.glob(os.path.join(PLAN, folder, 'state', '*.json')):
        raw = open(jf, 'rb').read()
        rel = os.path.relpath(jf, PLAN)
        if b'\x00' in raw:
            err('Integrity', f'NUL bytes in {rel}')
        try:
            json.loads(raw.decode('utf-8'))
        except Exception as e:
            err('Integrity', f'broken JSON/UTF-8: {rel} — {str(e)[:50]}')
    mm = os.path.join(PLAN, folder, 'mental_model.md')
    if os.path.exists(mm):
        raw = open(mm, 'rb').read()
        rel = os.path.relpath(mm, PLAN)
        if b'\x00' in raw:
            err('Integrity', f'NUL bytes in {rel}')
        try:
            raw.decode('utf-8')
        except Exception:
            err('Integrity', f'non-UTF-8: {rel}')

# --- 3. Dangling pointers: live reading of archived files ---
ARCHIVED = ['clients_data.json']
for pf in sorted(glob.glob(os.path.join(HERE, '*.py'))):
    name = os.path.basename(pf)
    src = open(pf, encoding='utf-8').read()
    for arch in ARCHIVED:
        a = re.escape(arch)
        # live read: open(...arch...).read / read_text on arch / json.load(open(...arch
        if re.search(r'open\([^\n)]*' + a + r'[^\n)]*\)\s*\.\s*read', src) or \
           re.search(a + r'[\'"]\s*\)\s*\.\s*read_text', src) or \
           re.search(r'json\.load\(\s*open\([^\n)]*' + a, src):
            err('Pointers', f'{name}: live reading of archived {arch}')
for arch in ARCHIVED:
    if os.path.exists(os.path.join(HERE, arch)):
        warn('Pointers', f'{arch} reappeared in _data/ (should be archived)')

# --- 4. Orphan _data modules ---
ENTRYPOINTS = {'generate','state_lint','snapshot','safe_edit','system_integrity_check','rotate_baks'}
mods = [os.path.basename(f)[:-3] for f in glob.glob(os.path.join(HERE, '*.py'))]
srcs = {m: open(os.path.join(HERE, m + '.py'), encoding='utf-8').read() for m in mods}
for m in mods:
    if m in ENTRYPOINTS:
        continue
    pat = re.compile(r'(?:^|\n)\s*(?:import ' + re.escape(m) + r'\b|from ' + re.escape(m) + r' import)')
    if not any(pat.search(srcs[o]) for o in mods if o != m):
        warn('Orphans', f'module {m}.py is imported by no one (Archive candidate)')

# --- 5. Skill domains + revived deprecation ---
SKILLS = os.path.join(PLAN, 'connectors')
DEPRECATED_DIRS = ['updater', 'analytic']
real_domains = sorted(
    d for d in os.listdir(SKILLS)
    if os.path.isdir(os.path.join(SKILLS, d)) and not d.startswith('.') and d != '__pycache__'
) if os.path.isdir(SKILLS) else []
for dep in DEPRECATED_DIRS:
    if os.path.isdir(os.path.join(SKILLS, dep)):
        err('Skills', f'deprecated skill domain exists again: {dep}/')

# --- 6. Drift of client count in forward docs ---
DOCS = ['policies/system-map.md', 'policies/INSTRUCTIONS.md', 'connectors/mm_update/SKILL.md']
for rel in DOCS:
    fp = os.path.join(PLAN, rel)
    if not os.path.exists(fp):
        warn('Drift', f'doc missing: {rel}')
        continue
    txt = open(fp, encoding='utf-8').read()
    # Historical lines (about a past migration) are not counted as drift — only forward instructions.
    HIST = re.compile(r'migrat|complet|director|pilot|accumulat|\bwas\b|in 2026-0[1-5]', re.IGNORECASE)
    for line in txt.split('\n'):
        if HIST.search(line):
            continue
        for m in re.finditer(r'(?:all|across|for)\s+(\d{1,2})\s+client', line, re.IGNORECASE):
            n = int(m.group(1))
            if n != n_clients:
                warn('Drift', f'{rel}: "{m.group(0).strip()}" — but CLIENT_FOLDERS has {n_clients} clients')

# --- 7. state_lint (informational; gating is done by generate.py) ---
lint_info = ''
try:
    import state_lint
    v = state_lint.lint_all()
    le = sum(1 for x in v if isinstance(x, dict) and x.get('severity') == 'error')
    lint_info = f'state_lint: {len(v)} violations, {le} error'
    if le:
        err('Lint', f'state_lint returned {le} error (see python3 _data/state_lint.py)')
except Exception as e:
    lint_info = f'state_lint did not run: {str(e)[:50]}'

# ===== Report =====
print('=' * 64)
print(f'SYSTEM INTEGRITY CHECK')
print(f'clients (CLIENT_FOLDERS): {n_clients} | _data modules: {len(mods)} | skill domains: {len(real_domains)}')
print(f'domains: {", ".join(real_domains)}')
print(f'{lint_info}')
print('=' * 64)

def dump(title, items, mark):
    if not items:
        return
    print(f'\n{mark} {title} ({len(items)}):')
    cats = {}
    for cat, msg in items:
        cats.setdefault(cat, []).append(msg)
    for cat in sorted(cats):
        print(f'  [{cat}]')
        for msg in cats[cat]:
            print(f'    - {msg}')

dump('ERROR — need fixing', errors, '[ERROR]')
dump('WARN — drift / orphans', warns, '[WARN]')

if not errors and not warns:
    print('\n[OK] ALL CLEAN — no docs-vs-reality discrepancies found.')
elif not errors:
    print(f'\n[OK] No blocking errors. [WARN] {len(warns)} warnings (drift/orphans).')
else:
    print(f'\n[ERROR] {len(errors)} errors, [WARN] {len(warns)} warnings.')

sys.exit(len(errors))
