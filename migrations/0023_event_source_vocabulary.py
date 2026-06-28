"""Bring every history/task `source` into the CLOSED channel vocabulary.

`source` used to be free form and three different things got dumped into it: the
**channel** (who brought the update), the **reason** (`decision_…`, `*_unclear`),
and the **document** behind it (`contract_…`, «налоговое уведомление …»). The
channel is only the first of those. This migration normalizes the channel head to
the closed set (`engine/_helpers._CANON_CHANNELS`, human reference
`policies/event-sources.md`); the specific ref moves into the free `:detail`.

Split along the canonical dividing rule (`migrations/RUNTIME_PASS_SPEC.md`):

- **Structure → deterministic `up()`.** The confident, name-free shape cases:
  `migrated_from_*` → `migration:<rest>`; bare `migration`/`миграция` → `migration`;
  known BANK names (public institutions, not personal data) → `bank:<Name>`;
  daemon `*_unclear` flags → `system:<token>`; trivial aliases
  (`1с`→`1c`, `telegram`→`tg`, `mail`→`email`, `joint`→`session`).

- **Meaning → `RUNTIME_PASS`.** Everything else non-canonical is classified by
  what it MEANS, per `policies/event-sources.md`: an operator action / decision /
  manual entry / reconciliation → `cowork`; a source document / evidence →
  `document`; an automated pass / analysis / monitor → `system` (or `news` for the
  news feed). `preflight` surfaces the residue (the non-canonical heads `up()`
  leaves); the runtime reads the operator's OWN data and rewrites. The shipped
  file lists NO client/operator names — names live only in the operator's data.

Both halves preserve the original in `source_legacy` (lossless, mirroring
0021/0022) and are idempotent: a channel already canonical is skipped, and
`preflight` only re-surfaces still-non-canonical heads, so a re-run is a no-op.

    source head (migrated_from_*/bank/*_unclear/alias) -> canonical   [up(), +legacy]
    source head (decision/document/analysis/manual/…)  -> canonical   [RUNTIME_PASS, +legacy]
"""

ID = "0023"
DESCRIPTION = ("tasks: normalize source channel into the closed vocabulary "
               "(migrated_from/bank/*_unclear/aliases deterministically; the rest via runtime pass)")

# Imported so the migration and the engine share ONE definition of "canonical".
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
try:
    from _helpers import _CANON_CHANNELS
except Exception:                       # defensive: engine path not importable
    _CANON_CHANNELS = frozenset({
        "cowork", "chat", "tg", "whatsapp", "max", "email", "finkoper", "bank",
        "ofd", "1c", "news", "document", "system", "migration", "session",
        "resolution_sweep", "deadline_monitor", "threshold_monitor",
        "staleness_monitor", "mm_update", "dashboards"})

# Bank NAMES are public institutions (not client/personal data) — safe to list.
_BANKS = {
    "тбанк": "Т-Банк", "tbank": "Т-Банк", "t-bank": "Т-Банк",
    "альфа": "Альфа", "alfa": "Альфа", "alfabank": "Альфа",
    "втб": "ВТБ", "vtb": "ВТБ", "сбер": "Сбер", "sber": "Сбер",
    "mandiri": "Mandiri",
}
_ALIASES = {"1с": "1c", "telegram": "tg", "mail": "email", "joint": "session", "чат": "chat"}


def _channel(val):
    return str(val or "").partition(":")[0].strip().lower() if isinstance(val, str) else ""


def _det_map(val):
    """Deterministic, name-free channel normalization. Returns a new source string
    or None when no confident shape rule applies (left for the runtime pass)."""
    if not isinstance(val, str) or not val.strip():
        return None
    head, sep, tail = val.partition(":")
    ch = head.strip().lower()
    if ch in _CANON_CHANNELS:
        return None                                   # already canonical
    if ch.startswith("migrated_from_"):
        rest = head.strip()[len("migrated_from_"):]
        return "migration" + (":" + rest if rest else "")
    if ch in ("migration", "миграция"):
        return "migration" + (sep + tail if sep else "")
    if ch in _BANKS:
        return "bank:" + _BANKS[ch]                   # bare bank token -> name in detail
    if ch.endswith("_unclear"):
        return "system:" + ch
    if ch in _ALIASES:
        return _ALIASES[ch] + (sep + tail if sep else "")
    return None


def _iter_sources(tk):
    if isinstance(tk, dict):
        yield tk
        for ev in tk.get("history") or []:
            if isinstance(ev, dict):
                yield ev


def up(api):
    """Deterministic half: the confident, name-free shape cases."""
    def fix(client_id, data):
        tasks = data.get("tasks")
        if not isinstance(tasks, list):
            return False, ""
        changed = 0
        for tk in tasks:
            for obj in _iter_sources(tk):
                new = _det_map(obj.get("source"))
                if new is not None:
                    obj.setdefault("source_legacy", obj["source"])
                    obj["source"] = new
                    changed += 1
        if not changed:
            return False, ""
        return True, "source channel normalized (deterministic): %d" % changed

    api.for_each_client("tasks.json", fix)


# ---------------------------------------------------------------------------
# AI-side surface (RUNTIME_PASS spec). up() does the confident shapes; the rest is
# classified by MEANING per policies/event-sources.md. See RUNTIME_PASS_SPEC.md.
# ---------------------------------------------------------------------------

def preflight(api):
    """READ step. Per DISTINCT residue channel head that is still non-canonical
    AFTER simulating the deterministic map — the cases the runtime must classify."""
    seen = {}
    for cid in api.clients():
        data = api.read(cid, "tasks.json")
        if not isinstance(data, dict):
            continue
        for tk in data.get("tasks") or []:
            for obj in _iter_sources(tk):
                s = obj.get("source")
                if not isinstance(s, str) or not s.strip():
                    continue
                mapped = _det_map(s) or s
                ch = _channel(mapped)
                if ch and ch not in _CANON_CHANNELS:
                    e = seen.setdefault(ch, {"channel": ch, "occurrences": 0,
                                             "clients": set(), "kind": "needs_channel_classification"})
                    e["occurrences"] += 1
                    e["clients"].add(cid)
    flags = []
    for e in seen.values():
        e["clients"] = sorted(e["clients"])
        flags.append(e)
    return flags


RUNTIME_PASS = {
    "intent": (
        "For each non-canonical source head preflight flagged, set the channel to "
        "the closed vocabulary in policies/event-sources.md by what it MEANS, "
        "keeping the original ref in the `:detail` and the whole original in "
        "source_legacy: an operator action / decision / manual entry / "
        "reconciliation (decision_*, ira_correction_*, manual, сверка) -> `cowork`; "
        "a source document / evidence (contract_*, a tax-notice / statement / KUDIR "
        "prose) -> `document`; an automated pass / analysis / monitor "
        "(*_analysis, *_calendar, cognitive_update_*, team_*, departure_tracking, "
        "onboarding*, data_quality) -> `system`; the news feed (news_daemon_*) -> "
        "`news`. Conservative: when a head's meaning is unclear, use `system` rather "
        "than guess an actor. Never invent a channel outside the closed set."
    ),
    "scope": "tasks[].source, tasks[].history[].source",
    "escalate": "on_anomaly",
    "guardrails": [
        "only rewrite a head preflight flagged",
        "the new channel head MUST be in _CANON_CHANNELS (closed set)",
        "keep the original ref in :detail and the whole original in source_legacy",
        "never touch identifiers, amounts, or event text",
        "operator name/initials -> cowork; never a client/external party",
    ],
}

EXPECT = {
    "preflight_max": 60,                 # distinct residue heads; more = anomaly
    "change_kinds": ["needs_channel_classification"],
}

SCENARIO = [
    "Open the overview «Недавно обновили / закрыли» and a track modal event "
    "history for an affected client. Confirm every source chip reads a canonical "
    "label («Ирина»/«документ»/«система»/«импорт»/«банк · <name>»/…), no raw "
    "free-form token (decision_…, contract_…, migrated_from_…) remains visible, "
    "and source_legacy kept the original.",
]
