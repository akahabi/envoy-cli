"""Track and retrieve the history of changes to env vars in a store."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class HistoryError(Exception):
    pass


def _history_path(store_path: str) -> Path:
    p = Path(store_path)
    return p.parent / (p.stem + ".history.json")


def record_change(
    store_path: str,
    action: str,
    key: str,
    old_value: str | None = None,
    new_value: str | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    """Append a change record to the history file for the given store."""
    entry: dict[str, Any] = {
        "timestamp": time.time(),
        "action": action,
        "key": key,
        "old_value": old_value,
        "new_value": new_value,
    }
    if profile is not None:
        entry["profile"] = profile

    path = _history_path(store_path)
    records: list[dict[str, Any]] = []
    if path.exists():
        try:
            records = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise HistoryError(f"Corrupt history file: {path}") from exc

    records.append(entry)
    path.write_text(json.dumps(records, indent=2))
    return entry


def read_history(
    store_path: str,
    key: str | None = None,
    action: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Return history entries, optionally filtered by key and/or action."""
    path = _history_path(store_path)
    if not path.exists():
        return []

    try:
        records: list[dict[str, Any]] = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise HistoryError(f"Corrupt history file: {path}") from exc

    if key is not None:
        records = [r for r in records if r.get("key") == key]
    if action is not None:
        records = [r for r in records if r.get("action") == action]
    if limit is not None:
        records = records[-limit:]
    return records


def clear_history(store_path: str) -> None:
    """Remove the history file for the given store."""
    path = _history_path(store_path)
    if path.exists():
        path.unlink()
