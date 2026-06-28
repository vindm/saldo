"""Backfill a `source` channel on history/task events that have NONE.

0021–0024 brought every event's `source` VALUE into the closed channel vocabulary
— but they only touched events that already carried a source (or a stray `by`).
About half of the historical events carry no `source` key at all (migration-seed
events, dedup/merge notes, monitor/priority notes, operator notes, and the
status/close events `update_status` used to write without a source). With no
source there is nothing to canonicalize, so the event renders a BLANK chip on
«Недавно обновили / закрыли». This migration fills that gap so every event has a
channel, completing the «source = connector | operator | system» model.

Split along the canonical dividing rule (`migrations/RUNTIME_PASS_SPEC.md`):

- **Structure → deterministic `up()`.** The unambiguous, name-free machine shapes
  of a SOURCELESS event: the exact engine-written migration-onboarding strings
  («Задача заведена при переходе на новую систему», «Конвертирован в
  state/tasks.json v2.0») → `migration`; a `Status:`/`Статус:` head (the mechanical
  status/close line, an operator decision per mm_update §D) → `cowork`.

- **Meaning → `RUNTIME_PASS`.** Every other sourceless event is classified by what
  it MEANS, per `policies/event-sources.md`: an engine structural note (extracted /
  created / added / merged-deduped / dropped / dismissed / priority / deadline-moved
  / cycle-opened / onboarding) → `system`; an operator decision / manual entry /
  correction / note — including an operator-name prefix, read from the operator's
  OWN data (never hardcoded here, per 0022) → `cowork`; a source document / evidence
  → `document`; the news feed («News-демон …») → `news`. Conservative: when meaning
  is unclear, `system` rather than guess an actor.

The original (absent) is recorded as `source_legacy` (null = "had no source,
backfilled"), mirroring 0021–0024. Idempotent: an event that now has a source is
skipped, so a re-run — and `preflight`'s residue scan — drop to 0.

Only events with an EMPTY source are touched; events 0021–0024 already canonicalized
are left exactly as they are.

    sourceless event (exact migration seed / Status: head) -> channel   [up(), +legacy]
    sourceless event (extracted/merged/priority/operator note/…) -> channel [RUNTIME_PASS, +legacy]
"""

ID = "0025"
DESCRIPTION = ("tasks: backfill a source channel on events that have none "
               "(exact migration-seed / Status: head deterministically; the rest by meaning via runtime pass)")

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
try:
    from _helpers import _CANON_CHANNELS
except Exception:                       # defensive: engine path not importable
    _CANON_CHANNELS = frozenset({
        "cowork", "tg", "whatsapp", "max", "email", "finkoper", "bank",
        "ofd", "1c", "news", "document", "system", "migration", "session",
        "resolution_sweep", "deadline_monitor", "threshold_monitor",
        "staleness_monitor", "mm_update", "dashboards"})

# Exact engine-written onboarding/schema strings — generic system phrases, zero
# client data. These are the migration's own seed events.
_MIGRATION_SEEDS = {
    "Задача заведена при переходе на новую систему",
    "Конвертирован в state/tasks.json v2.0",
}


def _has_source(obj):
    return bool(str(obj.get("source") or "").strip())


def _det_source_for_empty(obj):
    """Deterministic, name-free channel for an event that has NO source.
    Returns a canonical channel, or None when no confident shape applies
    (left for the runtime pass). Never fires on an event that already has one."""
    if not isinstance(obj, dict) or _has_source(obj):
        return None
    ev = str(obj.get("event") or "").strip()
    if not ev:
        return None
    if ev in _MIGRATION_SEEDS:
        return "migration"
    if ev.startswith("Status:") or ev.startswith("Статус:"):
        return "cowork"
    return None


def _iter_sources(tk):
    if isinstance(tk, dict):
        yield tk
        for ev in tk.get("history") or []:
            if isinstance(ev, dict):
                yield ev


def up(api):
    """Deterministic half: fill the unambiguous, name-free sourceless shapes."""
    def fix(client_id, data):
        tasks = data.get("tasks")
        if not isinstance(tasks, list):
            return False, ""
        changed = 0
        for tk in tasks:
            for obj in _iter_sources(tk):
                new = _det_source_for_empty(obj)
                if new is not None:
                    obj.setdefault("source_legacy", obj.get("source"))
                    obj["source"] = new
                    changed += 1
        if not changed:
            return False, ""
        return True, "missing source backfilled (deterministic): %d" % changed

    api.for_each_client("tasks.json", fix)


# ---------------------------------------------------------------------------
# AI-side surface (RUNTIME_PASS spec). up() does the confident shapes; the rest is
# classified by MEANING per policies/event-sources.md. See RUNTIME_PASS_SPEC.md.
# ---------------------------------------------------------------------------

def _shape_sig(ev):
    """Coarse shape signature for a sourceless event — the leading token, so the
    runtime sees the residue grouped by kind without any client data leaking."""
    import re
    ev = str(ev or "").strip()
    if not ev:
        return "(empty)"
    return re.split(r"[\s=:—-]", ev, 1)[0][:24]


def preflight(api):
    """READ step. Per DISTINCT shape signature of a still-sourceless event that
    up() did NOT fill — the residue the runtime must classify by meaning."""
    seen = {}
    for cid in api.clients():
        data = api.read(cid, "tasks.json")
        if not isinstance(data, dict):
            continue
        for tk in data.get("tasks") or []:
            for obj in _iter_sources(tk):
                if _has_source(obj) or _det_source_for_empty(obj):
                    continue
                ev = str(obj.get("event") or "").strip()
                sig = _shape_sig(ev)
                e = seen.setdefault(sig, {"shape": sig, "occurrences": 0,
                                          "clients": set(), "auto_seen": set(),
                                          "kind": "needs_source_classification",
                                          "sample": ev[:60]})
                e["occurrences"] += 1
                e["clients"].add(cid)
                e["auto_seen"].add(bool(obj.get("auto")))
    flags = []
    for e in seen.values():
        e["clients"] = sorted(e["clients"])
        e["auto_seen"] = sorted(e["auto_seen"])
        flags.append(e)
    return flags


RUNTIME_PASS = {
    "intent": (
        "For each still-sourceless event preflight flagged, set `source` to the "
        "closed vocabulary in policies/event-sources.md by what the event MEANS, "
        "recording the absent original as source_legacy=null: an engine structural "
        "note (Извлечён/Создан/Добавлен/Объединён-dedup/Dropped/DISMISSED/Снято, "
        "priority=*, a deadline move, a cycle opener «Открыт … цикл», onboarding "
        "«Создана при заведении клиента») -> `system`; an operator decision / manual "
        "entry / correction / note — incl. an operator-name prefix read from the "
        "operator's OWN data (never hardcoded here) — (Закрыто/Закрыт … решением …, "
        "Корректировка …, <operator>: …) -> `cowork`; a source document / evidence "
        "-> `document`; the news feed («News-демон …») -> `news`. Conservative: when "
        "a head's meaning is unclear, use `system` rather than guess an actor. Never "
        "invent a channel outside the closed set."
    ),
    "scope": "tasks[].source, tasks[].history[].source (events with no source)",
    "escalate": "on_anomaly",
    "guardrails": [
        "only fill an event preflight flagged (one with no source); never overwrite a present source",
        "the new channel head MUST be in _CANON_CHANNELS (closed set)",
        "record the absent original as source_legacy=null",
        "never touch identifiers, amounts, or event text",
        "operator name/initials -> cowork; never a client/external party",
    ],
}

EXPECT = {
    "preflight_max": 80,                 # distinct prose-leading-token shapes; more = anomaly
    "change_kinds": ["needs_source_classification"],
}

SCENARIO = [
    "Open the overview «Недавно обновили / Недавно закрыли» and a track modal event "
    "history for an affected client. Confirm EVERY event now shows a source chip — "
    "no blank — and each reads a canonical label («Ирина»/«система»/«импорт»/"
    "«документ»/«новости»/…), with source_legacy recording the originally-absent source.",
]
