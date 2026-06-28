"""Fold the operator's `chat` / `session` source channels into `cowork`.

The source-channel model is three buckets (policies/event-sources.md): a
CONNECTOR brought the signal, OR the operator herself (`cowork`), OR the engine
(`system`). `chat` (the operator's working chat with the assistant) and `session`
(a joint working session) are both the OPERATOR acting — not a separate connector
— so they belong in `cowork`. They already render «Ирина», so this is state
hygiene that makes the closed vocabulary match the model (`_CANON_CHANNELS` no
longer lists `chat`/`session`).

Deterministic and name-free: the channel head `chat` or `session` → `cowork`,
preserving the `:detail` suffix, original in `source_legacy` (lossless, mirroring
0021–0023). Idempotent — a channel already `cowork` is skipped. (`chat` came from
0021's canonicalization of `чат`/`chat_irina`; `session` from `joint`/`session`.)

    history[].source / tasks[].source  (chat|session) -> cowork   (+ source_legacy)
"""

ID = "0024"
DESCRIPTION = "tasks: fold operator source channels chat/session into cowork (connector|operator|system model)"

_OPERATOR_FOLD = {"chat", "session"}
_CANON = "cowork"


def _iter_sources(tk):
    if isinstance(tk, dict):
        yield tk
        for ev in tk.get("history") or []:
            if isinstance(ev, dict):
                yield ev


def up(api):
    def fix(client_id, data):
        tasks = data.get("tasks")
        if not isinstance(tasks, list):
            return False, ""
        changed = 0
        for tk in tasks:
            for obj in _iter_sources(tk):
                val = obj.get("source")
                if not isinstance(val, str) or not val.strip():
                    continue
                head, sep, tail = val.partition(":")
                if head.strip().lower() in _OPERATOR_FOLD:
                    obj.setdefault("source_legacy", val)
                    obj["source"] = _CANON + (sep + tail if sep else "")
                    changed += 1
        if not changed:
            return False, ""
        return True, "operator source chat/session -> cowork: %d" % changed

    api.for_each_client("tasks.json", fix)
