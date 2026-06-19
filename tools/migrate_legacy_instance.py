#!/usr/bin/env python3
"""Migrate a legacy bookkeeping-assistant data tree into the product's data layout.

Usage:
    python tools/migrate_legacy_instance.py <OLD_PLAN_DIR> <OUT_DATA_DIR>

OLD_PLAN_DIR  legacy planning dir; contains `_data/clients_index.json` and the
              per-client folders referenced by each entry's `folder`.
OUT_DATA_DIR  destination data dir for the product engine. Point ABA_DATA_DIR here.

What it does (core, lossless for the parts the engine reads):
  - reads the legacy roster (`_data/clients_index.json`)
  - writes a new `<OUT>/clients_index.json` with `group` (from legacy `track`)
    and `folder` = `clients/<id>`
  - copies each client's `state/*.json` (skips *.bak*), `mental_model.md`,
    `history.jsonl` into `<OUT>/clients/<id>/`

Registry/daemon conversion (calendar/request_log/ukep, journal inbox) is NOT
done here yet — the engine degrades gracefully without them. The finkoper JSON
snapshot, if present, is copied as-is.

No data is mutated; this only reshapes a COPY. Run it against a copy of real data.
"""
import json, os, shutil, sys


def _copy_state(src_client_dir, dst_client_dir):
    os.makedirs(dst_client_dir, exist_ok=True)
    # state/*.json (skip backups)
    src_state = os.path.join(src_client_dir, "state")
    if os.path.isdir(src_state):
        dst_state = os.path.join(dst_client_dir, "state")
        os.makedirs(dst_state, exist_ok=True)
        for name in os.listdir(src_state):
            if name.endswith(".json") and ".bak" not in name:
                shutil.copy2(os.path.join(src_state, name), os.path.join(dst_state, name))
    # narrative + log (prose; engine no longer parses mental_model.md)
    for name in ("mental_model.md", "history.jsonl"):
        sp = os.path.join(src_client_dir, name)
        if os.path.isfile(sp):
            shutil.copy2(sp, os.path.join(dst_client_dir, name))


def migrate(old_plan_dir, out_dir):
    idx_path = os.path.join(old_plan_dir, "_data", "clients_index.json")
    with open(idx_path, encoding="utf-8") as f:
        roster = json.load(f)

    os.makedirs(out_dir, exist_ok=True)
    new_roster = []
    copied = 0
    for entry in roster:
        cid = entry["id"]
        legacy_folder = entry.get("folder") or ""
        # Resolve the client folder. The legacy roster's `folder` is sometimes
        # bare (direct-book clients lived under a `Прямые/` subdir in the old
        # state_ops map). Try the bare path, then common legacy subdirs.
        candidates = [
            os.path.join(old_plan_dir, legacy_folder),
            os.path.join(old_plan_dir, "Прямые", legacy_folder),
            os.path.join(old_plan_dir, "direct", legacy_folder),
        ]
        src_client_dir = next((p for p in candidates if os.path.isdir(p)), None)
        dst_client_dir = os.path.join(out_dir, "clients", cid)
        if src_client_dir is None:
            print(f"  ! skip {cid}: legacy folder not found ({legacy_folder})")
            continue
        _copy_state(src_client_dir, dst_client_dir)
        new_roster.append({
            "id": cid,
            "name_short": entry.get("name_short", cid),
            "name_full": entry.get("name_full", ""),
            "folder": f"clients/{cid}",
            "group": entry.get("group") or entry.get("track") or "default",
        })
        copied += 1

    with open(os.path.join(out_dir, "clients_index.json"), "w", encoding="utf-8") as f:
        json.dump(new_roster, f, ensure_ascii=False, indent=2)

    # NOTE: we intentionally do NOT migrate daemon snapshots (finkoper_state,
    # journal/inbox). Those are point-in-time collector outputs that the live
    # instance regenerates every morning. A migrated snapshot is stale relative to
    # state/*.json (the source of truth) and would override authoritative, more
    # recent facts — e.g. a deadline that state has deferred. State wins; the
    # daemons repopulate on the first scheduled run.

    groups = sorted({c["group"] for c in new_roster})
    print(f"Migrated {copied}/{len(roster)} clients into {out_dir}")
    print(f"Groups: {', '.join(groups)}")
    return copied, groups


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    migrate(sys.argv[1], sys.argv[2])
