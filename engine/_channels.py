"""_channels.py — "channels in use" derived from client state.

The connector list an instance needs is not really a free choice — it is a
function of which channels its CURRENT clients actually use. This module reads
client state (read-only) and reports the channels in use, then reconciles them
against the declared connectors (`config/instance.yaml → connectors`, via
`_config.CONNECTOR_CHANNELS`).

It is the evidence layer for "assemble the daemons from the clients' real
channels": today it surfaces the picture (used / declared-but-unused /
used-but-undeclared); the scheduler can later consume `channels_in_use()` to run
exactly the relevant collectors. Read-only — writes nothing, decides nothing.

Channel signals in state:
  - behavior.json → channels.primary / .secondary  (type: telegram/whatsapp/…)
  - accounts.json → bank_accounts (→ bank), ofd (→ ofd)
  - accounts.json → quick_access[].service (finkoper / onec→1c / rosstat→websbor /
    gdrive→document / tg / email / ofd / bank)
"""
import state_ops
from _config import CONNECTOR_CHANNELS

# communication-channel `type` (behavior.channels) → connector channel
_COMM_TYPE_TO_CHANNEL = {
    'telegram': 'tg', 'tg': 'tg',
    'whatsapp': 'whatsapp', 'max': 'max',
    'email': 'email', 'mail': 'email',
    'finkoper': 'finkoper',
    'team_via_finkoper': 'finkoper', 'team_via_anastasia': 'finkoper',
    'team_via_anastasia_and_representative': 'finkoper',
    'edo': 'document',
    # 'phone' → not an ingest connector (no channel)
}

# accounts.quick_access[].service → connector channel (None / absent = not an
# ingest connector: fns/coretax/acquiring portals are operator-driven, skipped)
_QA_SERVICE_TO_CHANNEL = {
    'bank': 'bank', 'finkoper': 'finkoper', 'onec': '1c', '1c': '1c',
    'ofd': 'ofd', 'tg': 'tg', 'email': 'email', 'rosstat': 'websbor',
    'gdrive': 'document', 'yandexdisk': 'document', 'documents': 'document',
}

# connectors that are operator-/instance-level, NOT client-driven — always
# relevant regardless of any single client (so "declared but unused" should not
# flag them as removable).
_OPERATOR_LEVEL = frozenset({'news', 'egrul', 'cowork', 'system', 'migration'})

# valid source channels that have NO ingest daemon (manual data sources / the
# operator) — using one is normal and needs no connector, so it must not be
# flagged as "undeclared, must enable".
_NO_DAEMON_SOURCES = frozenset({'1c', 'cowork', 'system', 'migration'})


def _comm_channels(behavior):
    out = set()
    ch = (behavior or {}).get('channels') or {}
    items = []
    p = ch.get('primary')
    if isinstance(p, dict):
        items.append(p)
    elif isinstance(p, list):
        items += [x for x in p if isinstance(x, dict)]
    s = ch.get('secondary')
    if isinstance(s, list):
        items += [x for x in s if isinstance(x, dict)]
    elif isinstance(s, dict):
        items.append(s)
    for it in items:
        c = _COMM_TYPE_TO_CHANNEL.get(str(it.get('type') or '').strip().lower())
        if c:
            out.add(c)
    return out


def _account_channels(accounts):
    out = set()
    a = accounts or {}
    if a.get('bank_accounts'):
        out.add('bank')
    o = a.get('ofd')
    if o not in (None, '', [], {}):
        out.add('ofd')
    for q in (a.get('quick_access') or []):
        svc = str((q.get('service') or q.get('type') or '')).strip().lower()
        c = _QA_SERVICE_TO_CHANNEL.get(svc)
        if c:
            out.add(c)
    return out


def channels_in_use():
    """{channel: sorted[client_id]} — the connector channels each current client
    actually uses, by evidence in their state. Read-only."""
    by_channel = {}
    for cid in state_ops.CLIENT_FOLDERS:
        try:
            beh = state_ops.state_read(cid, 'behavior.json')
            acc = state_ops.state_read(cid, 'accounts.json')
        except Exception:
            continue
        chans = set()
        if isinstance(beh, dict):
            chans |= _comm_channels(beh)
        if isinstance(acc, dict):
            chans |= _account_channels(acc)
        for c in chans:
            by_channel.setdefault(c, set()).add(cid)
    return {c: sorted(v) for c, v in sorted(by_channel.items())}


def reconcile_channels():
    """Compare channels in use against the declared connectors.

    Returns dict with:
      used            : {channel: [clients]} in use (client-driven)
      declared        : sorted declared connector channels (config)
      used_undeclared : in use but NOT declared (must enable)
      declared_unused : declared, client-driven, but no client uses it (candidate
                        to disable). Operator-level connectors (news/egrul) excluded.
    """
    used = channels_in_use()
    declared = set(CONNECTOR_CHANNELS)
    used_set = set(used)
    used_undeclared = sorted(used_set - declared - _NO_DAEMON_SOURCES)
    declared_unused = sorted((declared - used_set) - _OPERATOR_LEVEL)
    return {
        'used': used,
        'declared': sorted(declared),
        'used_undeclared': used_undeclared,
        'declared_unused': declared_unused,
    }


if __name__ == '__main__':
    import json
    r = reconcile_channels()
    print("CHANNELS IN USE (by clients' state):")
    for c, clients in r['used'].items():
        print(f"  {c:10} {len(clients):2}  {', '.join(clients)}")
    print("\nDECLARED connectors (config):", ', '.join(r['declared']))
    print("USED but NOT declared (enable):", r['used_undeclared'] or '—')
    print("DECLARED but unused (client-driven; candidate to disable):",
          r['declared_unused'] or '—')
