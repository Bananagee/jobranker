import os
import json
import hashlib
from datetime import datetime

# directory to hold our single cache of uploads
CACHE_DIR = "cache"
FIRST_DIR = os.path.join(CACHE_DIR, "firstcache")
INDEX_PATH = os.path.join(FIRST_DIR, "index.json")

os.makedirs(FIRST_DIR, exist_ok=True)

def _load_index() -> dict:
    if not os.path.exists(INDEX_PATH):
        return {}
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def _save_index(idx: dict) -> None:
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(idx, f, indent=2)

def get_index_entry(hash_str: str) -> dict | None:
    """
    Return the index entry for this hash, or None if it's not there.
    """
    return _load_index().get(hash_str)

def update_first_index(
    hash_str: str,
    *,
    broken: bool,
    filename: str,
    ip: str
) -> None:
    """
    Record or update metadata for every upload.
    - broken: did parsing fail?
    - filename: original filename
    - ip: uploader's IP
    """
    idx = _load_index()
    now = datetime.utcnow().isoformat()
    entry = idx.get(hash_str, {
        "broken": False,
        "first_seen": now,
        "last_seen": now,
        "count": 0,
        "events": [],       # list of {time, filename, ip}
        "notes": ""
    })
    entry["count"] += 1
    entry["last_seen"] = now
    entry["broken"] = entry["broken"] or broken

    # record this specific event
    entry.setdefault("events", []).append({
        "time": now,
        "filename": filename,
        "ip": ip
    })

    idx[hash_str] = entry
    _save_index(idx)

def file_hash(data: bytes) -> str:
    """
    Compute a SHA256 hash for the given bytes.
    """
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()