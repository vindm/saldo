#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backup rotator: keeps N most recent .bak files per source file, and
MOVES (does not delete) the rest into Archive/bak_history/<YYYY-MM>/, preserving the relative path.
Testing phase: move only. Running without --apply = dry-run.
Usage:
  python3 rotate_baks.py            # dry-run, show what would move
  python3 rotate_baks.py --apply    # perform the move
  python3 rotate_baks.py --keep 3   # how many recent ones to keep (default 3)
"""
import os, re, sys, shutil, datetime, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # project root
ARCH = os.path.join(ROOT, "Archive", "bak_history")
BAK_RE = re.compile(r"^(?P<base>.+)\.bak_(?P<ts>\d{8}_\d{6})(?:_.*)?$")

def collect():
    groups = collections.defaultdict(list)  # base_path -> [(ts, fullpath)]
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if "Archive" in dirpath.split(os.sep):  # never touch ANY archive (ROOT or nested)
            continue
        for fn in filenames:
            m = BAK_RE.match(fn)
            if not m:
                continue
            full = os.path.join(dirpath, fn)
            base = os.path.join(dirpath, m.group("base"))
            groups[base].append((m.group("ts"), full))
    return groups

def main():
    apply = "--apply" in sys.argv
    keep = 3
    if "--keep" in sys.argv:
        keep = int(sys.argv[sys.argv.index("--keep")+1])
    groups = collect()
    total_files = sum(len(v) for v in groups.values())
    to_move = []
    for base, items in groups.items():
        items.sort(key=lambda x: x[0])  # by timestamp in name, oldest first
        if len(items) > keep:
            for ts, full in items[:-keep]:  # all but the N most recent
                to_move.append(full)
    moved_bytes = sum(os.path.getsize(f) for f in to_move)
    print(f"Groups (source files with backups): {len(groups)}")
    print(f"Total .bak: {total_files} | keeping {keep} recent each | moving: {len(to_move)} ({moved_bytes/1048576:.1f} MB)")
    if not apply:
        print("\n[DRY-RUN] nothing moved. Add --apply to perform it")
        # top-5 groups by backup count
        top = sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True)[:5]
        print("Top-5 by backup count:")
        for base, items in top:
            print(f"  {len(items):>4}  {os.path.relpath(base, ROOT)}")
        return
    month = datetime.datetime.now().strftime("%Y-%m")
    moved = 0
    for full in to_move:
        rel = os.path.relpath(full, ROOT)
        dest = os.path.join(ARCH, month, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(full, dest)
        moved += 1
    print(f"\n[APPLY] moved {moved} files into Archive/bak_history/{month}/")

if __name__ == "__main__":
    main()
