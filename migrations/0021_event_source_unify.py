"""Unify a history event's channel into a single key `source`.

Two inconsistencies had crept into `state/tasks.json` history events and the
task-level `source`, both purely about HOW the channel was written (never WHAT
it was), so they are mechanical, shape-level normalizations:

1. **`by` → `source` (key rename).** The canonical event writer
   (`_tracks.add_history_event`) always writes `source`, but a few events were
   hand/runtime-written with `by` instead (e.g. `by: resolution_sweep:pilot`).
   The renderer only read `source`, so those events showed NO source chip even
   though the channel was known. In the data no event carries BOTH keys, so the
   rename is lossless. (The `assist.by` hypothesis-attribution field is a
   DIFFERENT slot and is left untouched — this migration only walks `history[]`
   events and the task-level `source`.)

2. **Channel-synonym canonicalization.** One channel was spelled several ways —
   `chat` / `чат` / `chat_irina` for the operator chat, `finkoper_chat` for
   Finkoper. They render identically today (the display map collapses them), but
   leaving three spellings in state lets the variants keep multiplying. Matched
   by SHAPE, never a literal name: a `chat…`/Cyrillic `чат` channel → `chat`,
   a `finkoper…` channel → `finkoper`; the `:detail` suffix is preserved and the
   original kept in `source_legacy` (lossless, mirroring 0005/0009/0010).

Idempotent: a value already in canonical form is skipped, so re-running changes
nothing. Schema-level — keyed on field names and channel SHAPE, no client or
operator names, no per-client logic → zero real data, safe in the public repo.

Pairs with: the render-side `source`-or-`by` fallback (`_overview_v2.py`,
`_track_modal.py`), the `source_label` channel map + machine-id fallback
(`_helpers.py`), the `event_by_key` lint check (`state_lint.py`), and the
disambiguating note added to `connectors/mm_update/SKILL.md` (event channel is
always `source`, never `by`).

    history[].by            -> history[].source            (rename, no legacy)
    history[].source (chat… / чат / finkoper…) -> canonical (+ source_legacy)
    tasks[].source   (chat… / чат / finkoper…) -> canonical (+ source_legacy)
"""

ID = "0021"
DESCRIPTION = ("tasks: unify history-event channel into `source` "
               "(rename `by`→`source`; canonicalize chat/finkoper channel synonyms)")


def _canon_channel(ch):
    """Canonical channel token for a synonym, or None if no change is needed.

    Shape-based (no names): a `chat…` or Cyrillic `чат` channel collapses to
    `chat`; a `finkoper…` channel collapses to `finkoper`. A channel already in
    canonical form returns None so the caller skips it (idempotent).
    """
    c = (ch or "").strip().lower()
    if c == "чат" or c.startswith("chat"):
        return "chat" if c != "chat" else None
    if c.startswith("finkoper"):
        return "finkoper" if c != "finkoper" else None
    return None


def _canon_source(val):
    """Canonicalized `channel:detail` string, or None if unchanged.

    Splits on the first ':', canonicalizes only the channel head, preserves the
    detail tail verbatim.
    """
    if not isinstance(val, str) or not val.strip():
        return None
    head, sep, tail = val.partition(":")
    canon = _canon_channel(head)
    if canon is None:
        return None
    return canon + (sep + tail if sep else "")


def up(api):
    def fix(client_id, data):
        tasks = data.get("tasks")
        if not isinstance(tasks, list):
            return False, ""
        renamed = 0
        canon = 0
        for tk in tasks:
            if not isinstance(tk, dict):
                continue
            # task-level source: canonicalize channel synonyms (preserve original)
            new_ts = _canon_source(tk.get("source"))
            if new_ts is not None:
                tk.setdefault("source_legacy", tk["source"])
                tk["source"] = new_ts
                canon += 1
            for ev in tk.get("history") or []:
                if not isinstance(ev, dict):
                    continue
                # 1) rename `by` -> `source` (the event channel's one true key)
                if "by" in ev:
                    if not str(ev.get("source") or "").strip():
                        ev["source"] = ev.pop("by")
                        renamed += 1
                    else:
                        ev.pop("by", None)  # source already set wins; drop redundant by
                # 2) canonicalize channel synonyms in the event source
                new_es = _canon_source(ev.get("source"))
                if new_es is not None:
                    ev.setdefault("source_legacy", ev["source"])
                    ev["source"] = new_es
                    canon += 1
        if not (renamed or canon):
            return False, ""
        return True, "history source unified: %d by→source, %d channel canon" % (renamed, canon)

    api.for_each_client("tasks.json", fix)
