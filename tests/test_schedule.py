"""Tests for envoy.schedule."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from envoy.schedule import (
    ScheduleError,
    _schedule_path,
    due_schedules,
    list_schedules,
    remove_schedule,
    set_schedule,
)


@pytest.fixture()
def store_file(tmp_path: Path) -> str:
    p = tmp_path / ".envoy_store"
    p.write_text(json.dumps({"vars": {"MY_KEY": "val"}}))
    return str(p)


def test_set_schedule_returns_entry(store_file: str) -> None:
    entry = set_schedule(store_file, "MY_KEY", 7)
    assert entry["interval_days"] == 7
    assert "due_at" in entry
    assert "created_at" in entry


def test_set_schedule_persists_file(store_file: str) -> None:
    set_schedule(store_file, "MY_KEY", 30)
    data = json.loads(_schedule_path(store_file).read_text())
    assert "MY_KEY" in data
    assert data["MY_KEY"]["interval_days"] == 30


def test_set_schedule_zero_days_raises(store_file: str) -> None:
    with pytest.raises(ScheduleError, match="positive"):
        set_schedule(store_file, "MY_KEY", 0)


def test_set_schedule_negative_days_raises(store_file: str) -> None:
    with pytest.raises(ScheduleError):
        set_schedule(store_file, "MY_KEY", -5)


def test_remove_schedule_deletes_entry(store_file: str) -> None:
    set_schedule(store_file, "MY_KEY", 7)
    remove_schedule(store_file, "MY_KEY")
    assert "MY_KEY" not in list_schedules(store_file)


def test_remove_schedule_missing_key_raises(store_file: str) -> None:
    with pytest.raises(ScheduleError, match="No schedule"):
        remove_schedule(store_file, "GHOST")


def test_list_schedules_empty_when_no_file(store_file: str) -> None:
    assert list_schedules(store_file) == {}


def test_list_schedules_returns_all(store_file: str) -> None:
    set_schedule(store_file, "MY_KEY", 7)
    set_schedule(store_file, "OTHER", 14)
    result = list_schedules(store_file)
    assert set(result.keys()) == {"MY_KEY", "OTHER"}


def test_due_schedules_returns_overdue(store_file: str) -> None:
    set_schedule(store_file, "MY_KEY", 7)
    # Manually backdate due_at
    p = _schedule_path(store_file)
    data = json.loads(p.read_text())
    data["MY_KEY"]["due_at"] = (datetime.utcnow() - timedelta(days=1)).isoformat()
    p.write_text(json.dumps(data))
    overdue = due_schedules(store_file)
    assert "MY_KEY" in overdue


def test_due_schedules_excludes_future(store_file: str) -> None:
    set_schedule(store_file, "MY_KEY", 7)
    assert due_schedules(store_file) == {}
