"""Mark env vars as deprecated with optional replacement and sunset date."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from envoy.store import load_store


class DeprecateError(Exception):
    pass


def _deprecate_path(store_path: str) -> Path:
    return Path(store_path).with_suffix(".deprecations.json")


def _load_raw(store_path: str) -> dict:
    p = _deprecate_path(store_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_raw(store_path: str, data: dict) -> None:
    _deprecate_path(store_path).write_text(json.dumps(data, indent=2))


def deprecate_var(
    store_path: str,
    passphrase: str,
    key: str,
    reason: str,
    replacement: Optional[str] = None,
    sunset: Optional[str] = None,
) -> dict:
    """Mark *key* as deprecated. Returns the deprecation entry."""
    vars_ = load_store(store_path, passphrase)
    if key not in vars_:
        raise DeprecateError(f"Key '{key}' not found in store.")
    if sunset:
        try:
            datetime.strptime(sunset, "%Y-%m-%d")
        except ValueError:
            raise DeprecateError("sunset must be YYYY-MM-DD format.")
    data = _load_raw(store_path)
    entry = {
        "reason": reason,
        "deprecated_on": date.today().isoformat(),
    }
    if replacement:
        entry["replacement"] = replacement
    if sunset:
        entry["sunset"] = sunset
    data[key] = entry
    _save_raw(store_path, data)
    return entry


def undeprecate_var(store_path: str, key: str) -> None:
    """Remove deprecation marker for *key*."""
    data = _load_raw(store_path)
    if key not in data:
        raise DeprecateError(f"Key '{key}' has no deprecation entry.")
    del data[key]
    _save_raw(store_path, data)


def list_deprecated(store_path: str) -> dict:
    """Return all deprecation entries keyed by var name."""
    return _load_raw(store_path)


def check_sunset(store_path: str) -> list[dict]:
    """Return entries whose sunset date has passed."""
    today = date.today().isoformat()
    return [
        {"key": k, **v}
        for k, v in _load_raw(store_path).items()
        if v.get("sunset") and v["sunset"] <= today
    ]
