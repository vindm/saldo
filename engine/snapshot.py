#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""snapshot.py — snapshot of the system "brain" into tar.gz (a stand-in for git on mounts where unlink is blocked).

Includes only text/code/state: .md .py .json .jsonl
Excludes: secrets, backups (.bak/.tmp/.corrupted/.broken/.before_rerun), __pycache__, _tmp_html, binaries.
Writes to <root>/Archive/snapshots/brain_<ts>.tar.gz

Usage:
  python3 snapshot.py [label]      # create a snapshot
  python3 snapshot.py --list       # list existing snapshots
Restore (manually): tar -xzf <snapshot> -C <target>
"""
import os, sys, tarfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))          # project root
SNAP_DIR = os.path.join(HERE, '..', 'Archive', 'snapshots')
INCLUDE_EXT = {'.md', '.py', '.json', '.jsonl', '.txt'}
EXCLUDE_SUBSTR = ['/secrets/', '.bak_', '.bak', '.tmp', '_tmp_html/',
                  '__pycache__/', '.corrupted_', '.broken_', '.before_rerun',
                  '_BROKEN_git', '/Archive/snapshots/']

def _included(rel):
    if any(s in rel for s in EXCLUDE_SUBSTR):
        return False
    return os.path.splitext(rel)[1].lower() in INCLUDE_EXT

def make(label='snapshot'):
    os.makedirs(SNAP_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    name = f'brain_{ts}_{label}.tar.gz'
    out = os.path.join(SNAP_DIR, name)
    tmp = out + '.building'   # write to a temp file, then rename (no unlink needed)
    n = 0; total = 0
    with tarfile.open(tmp, 'w:gz') as tar:
        for dirpath, dirs, files in os.walk(ROOT):
            for fn in files:
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, ROOT)
                if _included(rel.replace('\\', '/')):
                    tar.add(full, arcname=rel)
                    n += 1; total += os.path.getsize(full)
    os.replace(tmp, out)   # rename is allowed on the mount
    print(f'snapshot: {name}')
    print(f'files: {n} | source size: {total//1024} KB | archive: {os.path.getsize(out)//1024} KB')
    return out

def lst():
    if not os.path.isdir(SNAP_DIR):
        print('no snapshots'); return
    for f in sorted(os.listdir(SNAP_DIR)):
        if f.endswith('.tar.gz'):
            print(f, '—', os.path.getsize(os.path.join(SNAP_DIR, f))//1024, 'KB')

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        lst()
    else:
        make(sys.argv[1] if len(sys.argv) > 1 else 'snapshot')
