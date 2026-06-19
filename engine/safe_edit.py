#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""safe_edit.py — safe editing of UTF-8 text files.

Why: some Edit/Write tools running over a network mount can corrupt
multi-byte (e.g. Cyrillic) text. This script: backup -> replace/append ->
UTF-8 validation -> atomic write.

Usage:
  # replace a unique fragment (old/new are paths to files holding the text):
  python3 safe_edit.py --file "<path>" --old /tmp/old.txt --new /tmp/new.txt [--ctx label]
  # append to end:
  python3 safe_edit.py --file "<path>" --append /tmp/add.txt [--ctx label]

Guarantee: on any error the source file is left untouched (atomic .tmp + os.replace).
"""
import argparse, os, shutil, sys
from datetime import datetime

def _read(p): return open(p, encoding='utf-8').read()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', required=True)
    ap.add_argument('--old'); ap.add_argument('--new')
    ap.add_argument('--append')
    ap.add_argument('--ctx', default='safe_edit')
    a = ap.parse_args()
    f = a.file
    if not os.path.exists(f):
        if a.append is not None and not (a.old or a.new):
            open(f, 'w', encoding='utf-8').close()  # create empty for append
        elif a.new and not a.old:
            pass  # creating a new file from --new below
        else:
            sys.exit(f'NO SUCH FILE: {f}')

    if os.path.exists(f) and os.path.getsize(f) > 0:
        bak = f + '.bak_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + a.ctx
        shutil.copy2(f, bak)
        print('backup:', os.path.basename(bak))

    text = _read(f) if os.path.exists(f) else ''

    if a.append is not None:
        text = text + _read(a.append)
    elif a.old and a.new:
        old, new = _read(a.old), _read(a.new)
        n = text.count(old)
        if n == 0: sys.exit('OLD not found - edit aborted')
        if n > 1: sys.exit(f'OLD occurs {n} times (not unique) - edit aborted')
        text = text.replace(old, new, 1)
    elif a.new and not a.old:
        text = _read(a.new)  # create/overwrite whole file
    else:
        sys.exit('need: --append FILE  OR  --old FILE --new FILE  OR  --new FILE (overwrite)')

    tmp = f + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as w: w.write(text)
    _read(tmp)  # UTF-8 validation before swap
    os.replace(tmp, f)
    assert '�' not in _read(f), 'corrupt char U+FFFD in result!'
    print('OK:', f, '|', len(_read(f)), 'chars | UTF-8 valid')

if __name__ == '__main__':
    main()
