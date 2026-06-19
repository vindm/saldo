"""
state_ops.py — atomic operations for working with per-client state/.

Architecture (Karpathy-style memory hierarchy):
- mental_model.md — narrative/analytical slice, human-readable
- state/*.json — structured facts, machine-readable
- history.jsonl — append-only log of signals

This module provides 5 low-level primitives. The logic of "what exactly to
update on which signal" lives in the AI agent (Claude), not in code. Here we
only do atomic writes with backup and validation.

Usage pattern:
    from state_ops import state_read, state_write, history_append
    tasks = state_read('client_a', 'tasks.json')
    tasks['tasks'].append({...})
    state_write('client_a', 'tasks.json', tasks, ctx='add_pp_task')
    history_append('client_a', {
        'summary': 'Added a filing task for 30.06',
        'fields_changed': ['tasks[].add'],
        'source': 'manual'
    })

Backup policy: when overwriting an existing file, a .bak_<TS>_<ctx> is created
next to the file. Rotation follows the existing rule (see docs).
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

# DATA_DIR — root of the data tree (config-driven). It used to hold a hardcoded
# dict of client surnames; now the id->folder mapping is built at runtime from
# <DATA_DIR>/clients_index.json (each entry has id and folder).
from _config import DATA_DIR

_PLAN_DIR = Path(DATA_DIR)


def _load_client_folders():
    """Build a mapping client_id -> relative path to the client's folder by
    reading <DATA_DIR>/clients_index.json. Cached at module level.

    Each index entry must contain 'id' and 'folder'. If the index is missing
    or broken, return an empty dict (graceful degradation)."""
    index_path = _PLAN_DIR / "clients_index.json"
    if not index_path.exists():
        return {}
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    except (ValueError, OSError):
        return {}
    mapping = {}
    for entry in index:
        cid = entry.get("id")
        folder = entry.get("folder")
        if cid and folder:
            mapping[cid] = folder
    return mapping


_CLIENT_FOLDERS = None


def _client_folders():
    """Lazy initialization of the id->folder mapping (read once)."""
    global _CLIENT_FOLDERS
    if _CLIENT_FOLDERS is None:
        _CLIENT_FOLDERS = _load_client_folders()
    return _CLIENT_FOLDERS


def __getattr__(name):
    """Backward-compat shim: legacy callers reference module-level CLIENT_FOLDERS
    (which used to be a hardcoded dict of surnames). It is now a runtime
    id->folder mapping from clients_index.json. PEP 562 module __getattr__."""
    if name == "CLIENT_FOLDERS":
        return _client_folders()
    raise AttributeError(
        "module {!r} has no attribute {!r}".format(__name__, name)
    )


def _client_dir(client_id):
    """Absolute path to the client's folder. Raises KeyError if client_id is unknown."""
    folders = _client_folders()
    if client_id not in folders:
        raise KeyError(
            "Unknown client_id '{}'. Known: {}".format(
                client_id, sorted(folders.keys())
            )
        )
    return _PLAN_DIR / folders[client_id]


def _state_dir(client_id):
    """The client's state/ folder (created on first access)."""
    d = _client_dir(client_id) / 'state'
    d.mkdir(parents=True, exist_ok=True)
    return d


def _backup(path, ctx):
    """Create a .bak next to the file, if the file exists."""
    if not path.exists():
        return None
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = path.with_name(path.name + '.bak_{}_{}'.format(ts, ctx))
    shutil.copy2(path, bak)
    return bak


# ---------- state/*.json ----------

def state_read(client_id, file_name):
    """Read state/<file_name>. If the file is missing, return {}.

    Guarantee: the returned dict can be safely mutated; to persist it back
    you must call state_write explicitly.
    """
    p = _state_dir(client_id) / file_name
    if not p.exists():
        return {}
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def state_write(client_id, file_name, data, ctx='manual'):
    """Atomically write state/<file_name>.

    Sequence:
    1. Backup (if the file exists)
    2. Serialize -> parse back -> validate correctness
    3. Atomic write via .tmp + rename
    4. UTF-8 validation on write

    Returns: Path to written file.
    Raises: ValueError on invalid JSON or UTF-8 problems.
    """
    p = _state_dir(client_id) / file_name
    _backup(p, ctx)

    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
    # roundtrip validation: what we write is valid JSON
    json.loads(text)
    # UTF-8 validation (raises UnicodeEncodeError if something is off)
    payload = text.encode('utf-8')

    tmp = p.with_name(p.name + '.tmp')
    with open(tmp, 'wb') as f:
        f.write(payload)
    os.replace(str(tmp), str(p))
    return p


# ---------- mental_model.md ----------

def mental_model_read(client_id):
    """Read the client's mental_model.md. If missing, return empty string."""
    p = _client_dir(client_id) / 'mental_model.md'
    if not p.exists():
        return ''
    return p.read_text(encoding='utf-8')


def mental_model_write(client_id, new_content, ctx='manual'):
    """Atomically overwrite mental_model.md.

    Backup + UTF-8 validation + atomic write.
    """
    p = _client_dir(client_id) / 'mental_model.md'
    _backup(p, ctx)

    payload = new_content.encode('utf-8')
    tmp = p.with_name(p.name + '.tmp')
    with open(tmp, 'wb') as f:
        f.write(payload)
    os.replace(str(tmp), str(p))
    return p


# ---------- history.jsonl ----------

def history_append(client_id, entry):
    """Append-only log in history.jsonl.

    entry — dict. If there is no 'ts' key, the current date+time is added.
    Each record is one line of JSON + \\n (jsonl format).

    NEVER rewrites existing records. Append only.
    """
    p = _client_dir(client_id) / 'history.jsonl'
    if 'ts' not in entry:
        entry = dict(entry)  # do not mutate the input dict
        entry['ts'] = datetime.now().astimezone().isoformat(timespec='seconds')
    line = json.dumps(entry, ensure_ascii=False) + '\n'
    with open(p, 'a', encoding='utf-8') as f:
        f.write(line)
    return p


def history_read(client_id):
    """Read history.jsonl into a list of dicts (one per line).

    Returns []: if the file is missing, empty, or every line is malformed.
    Malformed lines are skipped silently (never raises). Order preserved
    (chronological, as written — newest last).
    """
    try:
        p = _client_dir(client_id) / 'history.jsonl'
    except KeyError:
        return []
    if not p.exists():
        return []
    out = []
    try:
        text = p.read_text(encoding='utf-8')
    except OSError:
        return []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
        except ValueError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


# ---------- helpers for the generator ----------

def state_exists(client_id, file_name):
    """True if state/<file_name> exists. Cheap check without reading."""
    try:
        d = _client_dir(client_id) / 'state'
    except KeyError:
        return False
    return (d / file_name).exists()


def list_state_files(client_id):
    """List of *.json in the client's state/. Useful for debug/inventory."""
    try:
        d = _client_dir(client_id) / 'state'
    except KeyError:
        return []
    if not d.exists():
        return []
    return sorted([p.name for p in d.glob('*.json')])
