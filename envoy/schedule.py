"""Schedule-based auto-rotation of env vars."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

SCHEDULE_FILE = ".envoy_schedule.json"


class ScheduleError(Exception):
    """Raised on schedule-related failures."""


def _schedule_path(store_path: str) -> Path:
    return Path(store_path).parent / SCHEDULE_FILE


def _load_raw(store_path: str) -> dict:
    p = _schedule_path(store_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_raw(store_path: str, data: dict) -> None:
    _schedule_path(store_path).write_text(json.dumps(data, indent=2))


def set_schedule(store_path: str, key: str, interval_days: int) -> dict[str, Any]:
    """Schedule *key* for rotation every *interval_days* days."""
    if interval_days <= 0:
        raise ScheduleError("interval_days must be a positive integer")
    data = _load_raw(store_path)
    now = datetime.utcnow().isoformat()
    due = (datetime.utcnow() + timedelta(days=interval_days)).isoformat()
    data[key] = {"interval_days": interval_days, "created_at": now, "due_at": due}
    _save_raw(store_path, data)
    return data[key]


def remove_schedule(store_path: str, key: str) -> None:
    """Remove the rotation schedule for *key*."""
    data = _load_raw(store_path)
    if key not in data:
        raise ScheduleError(f"No schedule found for key '{key}'")
    del data[key]
    _save_raw(store_path, data)


def list_schedules(store_path: str) -> dict[str, Any]:
    """Return all scheduled keys."""
    return _load_raw(store_path)


def due_schedules(store_path: str) -> dict[str, Any]:
    """Return schedules whose due_at is in the past."""
    now = datetime.utcnow()
    return {
        k: v
        for k, v in _load_raw(store_path).items()
        if datetime.fromisoformat(v["due_at"]) <= now
    }
