"""Reminders: flag env vars as expiring or needing rotation by a deadline."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from envoy.store import load_store


class RemindError(Exception):
    pass


def _remind_path(store_path: Path) -> Path:
    return store_path.with_suffix(".reminders.json")


def _load_raw(store_path: Path) -> dict:
    p = _remind_path(store_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_raw(store_path: Path, data: dict) -> None:
    _remind_path(store_path).write_text(json.dumps(data, indent=2))


def set_reminder(store_path: Path, passphrase: str, key: str, deadline: str, note: str = "") -> dict:
    """Attach a deadline (YYYY-MM-DD) reminder to *key*."""
    vars_ = load_store(store_path, passphrase)
    if key not in vars_:
        raise RemindError(f"Key '{key}' not found in store.")
    try:
        date.fromisoformat(deadline)
    except ValueError:
        raise RemindError(f"Invalid date format '{deadline}'. Use YYYY-MM-DD.")
    data = _load_raw(store_path)
    data[key] = {"deadline": deadline, "note": note}
    _save_raw(store_path, data)
    return data[key]


def remove_reminder(store_path: Path, key: str) -> bool:
    """Remove reminder for *key*. Returns True if one existed."""
    data = _load_raw(store_path)
    if key in data:
        del data[key]
        _save_raw(store_path, data)
        return True
    return False


def list_reminders(store_path: Path) -> dict:
    """Return all reminders keyed by var name."""
    return _load_raw(store_path)


def due_reminders(store_path: Path, as_of: Optional[date] = None) -> list[dict]:
    """Return reminders whose deadline <= *as_of* (default: today)."""
    today = as_of or date.today()
    data = _load_raw(store_path)
    due = []
    for key, info in data.items():
        if date.fromisoformat(info["deadline"]) <= today:
            due.append({"key": key, **info})
    due.sort(key=lambda x: x["deadline"])
    return due
