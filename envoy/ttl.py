"""TTL (time-to-live) support for env vars — auto-expire keys after a set duration."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from envoy.store import load_store


class TTLError(Exception):
    pass


def _ttl_path(store_path: Path) -> Path:
    return store_path.with_suffix(".ttl.json")


def _load_raw(store_path: Path) -> dict:
    p = _ttl_path(store_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_raw(store_path: Path, data: dict) -> None:
    _ttl_path(store_path).write_text(json.dumps(data, indent=2))


def set_ttl(store_path: Path, passphrase: str, key: str, seconds: int) -> dict:
    """Attach a TTL (in seconds from now) to an existing env var."""
    vars_ = load_store(store_path, passphrase)
    if key not in vars_:
        raise TTLError(f"Key '{key}' not found in store.")
    if seconds <= 0:
        raise TTLError("TTL must be a positive number of seconds.")
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()
    data = _load_raw(store_path)
    data[key] = {"expires_at": expires_at}
    _save_raw(store_path, data)
    return data[key]


def remove_ttl(store_path: Path, key: str) -> None:
    """Remove the TTL entry for a key."""
    data = _load_raw(store_path)
    data.pop(key, None)
    _save_raw(store_path, data)


def list_ttls(store_path: Path) -> dict:
    """Return all TTL entries with their expiry timestamps."""
    return _load_raw(store_path)


def expired_keys(store_path: Path) -> list[str]:
    """Return keys whose TTL has elapsed."""
    now = datetime.now(timezone.utc)
    data = _load_raw(store_path)
    result = []
    for key, meta in data.items():
        expires_at = datetime.fromisoformat(meta["expires_at"])
        if now >= expires_at:
            result.append(key)
    return result
