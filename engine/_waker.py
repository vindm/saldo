# -*- coding: utf-8 -*-
"""_waker.py — auto-wake deferred tracks.

A track with status 'deferred' and type_specific.wake_date <= today is moved
to status type_specific.wake_to (defaults to 'awaiting'). Idempotent.
Writes via state_ops (backup + atomic + UTF-8) and logs to history.jsonl.

Purpose: avoid piling up far-horizon tasks in the calendar. Future quarterly
tracks (service-payment checks) sit as 'deferred' and surface on their own
near the right date (Q3 — Oct 1, Q4 — Feb 1, etc.).

Returns the number of woken tracks.
"""
import datetime
import state_ops


def _today_iso(today=None):
    if today is None:
        return datetime.date.today().isoformat()
    if hasattr(today, 'isoformat'):
        return today.isoformat()
    return str(today)


def wake_deferred_tracks(today=None, verbose=False):
    today = _today_iso(today)
    woken = 0
    for cid in state_ops.CLIENT_FOLDERS:
        try:
            data = state_ops.state_read(cid, 'tasks.json')
        except Exception:
            continue
        changed = False
        for t in data.get('tasks', []) or []:
            if t.get('status') != 'deferred':
                continue
            ts = t.get('type_specific') or {}
            wd = ts.get('wake_date')
            # wake_date in YYYY-MM-DD format -> correct string comparison
            if not wd or str(wd) > today:
                continue
            wake_to = ts.get('wake_to') or 'awaiting'
            t['status'] = wake_to
            t.setdefault('history', []).append({
                'date': today,
                'event': 'Auto-wake: track woken by wake_date %s -> %s.' % (wd, wake_to),
                'auto': True,
                'source': 'waker',
            })
            changed = True
            woken += 1
            if verbose:
                print('[waker] %s: %s -> %s' % (cid, t.get('id'), wake_to))
            state_ops.history_append(cid, {
                'date': today, 'ctx': 'waker', 'action': 'wake',
                'track': t.get('id'),
                'event': 'Track %s woken (wake_date %s).' % (t.get('id'), wd),
                'source': 'waker',
            })
        if changed:
            data['last_updated'] = today
            state_ops.state_write(cid, 'tasks.json', data, ctx='waker_wake')
    return woken


if __name__ == '__main__':
    import sys
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    n = wake_deferred_tracks(today=arg, verbose=True)
    print('Woken tracks: %d' % n)
