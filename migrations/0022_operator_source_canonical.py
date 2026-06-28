"""Collapse the "operator acting directly" source channel into one token `cowork`.

A history event's (and a task's) `source` channel spelled the operator several
ways — `cowork`, `owner`, `operator` (engine vocabulary) and the operator's own
NAME (e.g. a Cyrillic first name) — all meaning the same actor: the operator
herself made the change. They already render identically (`_helpers._SRC_LABELS`
maps `cowork`/`owner`/`operator` → «Ирина»), so this is state hygiene, not a
visible bug, but leaving the variants lets them keep multiplying.

This migration is SPLIT along the canonical dividing rule
(`migrations/RUNTIME_PASS_SPEC.md`):

- **Structure → deterministic `up()`.** The operator-self tokens that are fixed
  ENGINE VOCABULARY — `owner`, `operator` — are renamed to `cowork` by shape.
  These are not names; they are safe to list in the public repo.

- **Meaning → `RUNTIME_PASS`.** The operator's NAME (and any unforeseen
  operator-self spelling) cannot be hardcoded here — a migration ships public and
  must carry ZERO real data, and we will not enumerate the operator's name in the
  engine. So `preflight` SURFACES the residue (a non-canonical, non-machine,
  human/name-like channel that isn't a recognized external/system token), and the
  runtime JUDGES each one against the operator's own data: if it denotes the
  operator acting directly → `cowork`; otherwise it is left untouched. The name
  lives only in the operator's local data, never in this file.

Canonical token chosen by the operator: `cowork` (displayed as «Ирина»).

Both halves preserve the original in `source_legacy` (lossless, mirroring
0005/0009/0010/0021) and are idempotent — a channel already `cowork` is skipped,
and `preflight` only re-surfaces residue that is still non-canonical, so a
re-run after the pass is a no-op.

    history[].source / tasks[].source  (owner|operator) -> cowork   [up(), +legacy]
    history[].source / tasks[].source  (operator name)  -> cowork   [RUNTIME_PASS, +legacy]
"""

ID = "0022"
DESCRIPTION = ("tasks: collapse operator-self source channel into `cowork` "
               "(owner/operator deterministically; operator-name via runtime pass)")

# Canonical token for "the operator acted directly".
_CANON = "cowork"

# Operator-self tokens that are fixed ENGINE VOCABULARY (not names) — renamed by
# the deterministic up(). `cowork` is already canonical (no-op).
_OPERATOR_LATIN = {"owner", "operator"}

# Recognized NON-operator channels — external parties, banks, system markers.
# preflight skips these so only genuine operator-self CANDIDATES surface for
# judgment. Names of the operator are deliberately absent (discovered, not listed).
_EXTERNAL = {
    "tg", "telegram", "email", "mail", "finkoper", "news", "tbank", "alfa",
    "alfabank", "vtb", "bank", "ofd", "1c", "1с", "joint", "session", "chat",
    # Cyrillic display forms that appear literally in real data:
    "тбанк", "альфа", "втб", "офд", "финкопер", "новости", "почта", "сессия", "чат",
}
_SYSTEM = {"migration", "миграция"}   # the migrate API's own history source + RU variant

_KNOWN = _OPERATOR_LATIN | _EXTERNAL | _SYSTEM | {_CANON}
_CYRILLIC = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")


def _channel(val):
    """The channel head of a `channel:detail` source, lower-cased; '' if empty."""
    if not isinstance(val, str) or not val.strip():
        return ""
    return val.partition(":")[0].strip().lower()


def _recanon(val, target_channels):
    """Return `val` with its channel rewritten to `_CANON` when its channel is in
    `target_channels`, preserving the `:detail` suffix; else None (no change)."""
    if not isinstance(val, str) or not val.strip():
        return None
    head, sep, tail = val.partition(":")
    if head.strip().lower() not in target_channels:
        return None
    return _CANON + (sep + tail if sep else "")


def _is_operator_candidate(channel):
    """A non-canonical, human/name-like channel that the deterministic pass did
    NOT handle and that is not a recognized external/system token — i.e. a
    candidate the runtime should judge (typically the operator's name)."""
    if not channel or channel in _KNOWN:
        return False
    if "_" in channel or any(c.isdigit() for c in channel):
        return False  # machine / daemon / migration tag — not the operator
    return any(c in _CYRILLIC for c in channel)  # human/name-like (Cyrillic word)


def _iter_sources(tk):
    """Yield ('task'|'event', container) for each source-bearing object on a task."""
    if isinstance(tk, dict):
        yield "task", tk
        for ev in tk.get("history") or []:
            if isinstance(ev, dict):
                yield "event", ev


def up(api):
    """Deterministic half: owner/operator -> cowork (engine vocabulary, name-free)."""
    def fix(client_id, data):
        tasks = data.get("tasks")
        if not isinstance(tasks, list):
            return False, ""
        changed = 0
        for tk in tasks:
            for _, obj in _iter_sources(tk):
                new = _recanon(obj.get("source"), _OPERATOR_LATIN)
                if new is not None:
                    obj.setdefault("source_legacy", obj["source"])
                    obj["source"] = new
                    changed += 1
        if not changed:
            return False, ""
        return True, "operator-self source owner/operator -> cowork: %d" % changed

    api.for_each_client("tasks.json", fix)


# ---------------------------------------------------------------------------
# AI-side surface (RUNTIME_PASS spec). The deterministic up() handles the engine
# vocabulary; the operator's NAME (and any unforeseen operator-self spelling)
# cannot be hardcoded in the public repo, so preflight surfaces it as residue and
# the runtime judges it against the operator's own data. See RUNTIME_PASS_SPEC.md.
# ---------------------------------------------------------------------------

def preflight(api):
    """READ step for `migrate.py next`. Read-only. Surfaces, per DISTINCT channel,
    the operator-self candidates (human/name-like, non-canonical, non-machine,
    non-external) for the runtime to judge — typically the operator's name."""
    seen = {}
    for cid in api.clients():
        data = api.read(cid, "tasks.json")
        if not isinstance(data, dict):
            continue
        tasks = data.get("tasks")
        if not isinstance(tasks, list):
            continue
        for tk in tasks:
            for _, obj in _iter_sources(tk):
                ch = _channel(obj.get("source"))
                if _is_operator_candidate(ch):
                    e = seen.setdefault(ch, {"channel": ch, "occurrences": 0,
                                             "clients": set(), "kind": "operator_self_candidate"})
                    e["occurrences"] += 1
                    e["clients"].add(cid)
    flags = []
    for e in seen.values():
        e["clients"] = sorted(e["clients"])
        flags.append(e)
    return flags


RUNTIME_PASS = {
    "intent": (
        "For each DISTINCT channel preflight flagged (a human/name-like source "
        "token that is not a recognized external/system channel), decide from the "
        "operator's own data whether it denotes THE OPERATOR acting directly — the "
        "operator's own name or initials, or any operator-self spelling. If yes, "
        "rewrite that channel to `cowork` on every task/event source where it "
        "appears (preserve the `:detail` suffix, original in `source_legacy`). If "
        "it denotes a client, an external party/bank, or a system/daemon, LEAVE it "
        "untouched. Conservative: when unsure, leave it."
    ),
    "scope": "tasks[].source, tasks[].history[].source",
    "escalate": "on_anomaly",
    "guardrails": [
        "only rewrite a channel preflight flagged as a candidate",
        "rewrite ONLY when the token clearly denotes the operator acting directly",
        "never touch a client / external party / bank / system / daemon channel",
        "preserve the `:detail` suffix and the original in source_legacy",
        "never touch identifiers, amounts, or event text",
    ],
}

EXPECT = {
    "preflight_max": 12,                 # distinct candidate channels; more = anomaly
    "change_kinds": ["operator_self_candidate"],
}

SCENARIO = [
    "Open the overview «Недавно обновили / закрыли» and a track modal's event "
    "history for an affected client. Confirm operator-made events read «Ирина» "
    "(channel now `cowork`), no operator-name token remains as a raw source, "
    "client/external/bank/system sources are unchanged, and source_legacy kept "
    "the original.",
]
