"""Tests for envoy.remind."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from envoy.remind import RemindError, due_reminders, list_reminders, remove_reminder, set_reminder
from envoy.store import save_store

PASSPHRASE = "test-pass"


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    p = tmp_path / ".envoy"
    save_store(p, PASSPHRASE, {"API_KEY": "abc", "DB_URL": "postgres://"})
    return p


def test_set_reminder_returns_entry(store_file):
    entry = set_reminder(store_file, PASSPHRASE, "API_KEY", "2099-01-01", note="rotate soon")
    assert entry["deadline"] == "2099-01-01"
    assert entry["note"] == "rotate soon"


def test_set_reminder_persists(store_file):
    set_reminder(store_file, PASSPHRASE, "API_KEY", "2099-06-15")
    data = list_reminders(store_file)
    assert "API_KEY" in data
    assert data["API_KEY"]["deadline"] == "2099-06-15"


def test_set_reminder_unknown_key_raises(store_file):
    with pytest.raises(RemindError, match="not found"):
        set_reminder(store_file, PASSPHRASE, "MISSING_KEY", "2099-01-01")


def test_set_reminder_bad_date_raises(store_file):
    with pytest.raises(RemindError, match="Invalid date"):
        set_reminder(store_file, PASSPHRASE, "API_KEY", "not-a-date")


def test_remove_reminder_returns_true(store_file):
    set_reminder(store_file, PASSPHRASE, "API_KEY", "2099-01-01")
    result = remove_reminder(store_file, "API_KEY")
    assert result is True


def test_remove_reminder_absent_returns_false(store_file):
    result = remove_reminder(store_file, "API_KEY")
    assert result is False


def test_list_reminders_empty_when_no_file(store_file):
    assert list_reminders(store_file) == {}


def test_list_reminders_returns_all(store_file):
    set_reminder(store_file, PASSPHRASE, "API_KEY", "2099-01-01")
    set_reminder(store_file, PASSPHRASE, "DB_URL", "2099-03-01")
    data = list_reminders(store_file)
    assert set(data.keys()) == {"API_KEY", "DB_URL"}


def test_due_reminders_past_deadline(store_file):
    set_reminder(store_file, PASSPHRASE, "API_KEY", "2000-01-01")
    due = due_reminders(store_file, as_of=date(2025, 1, 1))
    assert any(d["key"] == "API_KEY" for d in due)


def test_due_reminders_future_deadline_excluded(store_file):
    set_reminder(store_file, PASSPHRASE, "API_KEY", "2099-12-31")
    due = due_reminders(store_file, as_of=date(2025, 1, 1))
    assert due == []


def test_due_reminders_sorted_by_deadline(store_file):
    set_reminder(store_file, PASSPHRASE, "DB_URL", "2000-06-01")
    set_reminder(store_file, PASSPHRASE, "API_KEY", "2000-01-01")
    due = due_reminders(store_file, as_of=date(2025, 1, 1))
    deadlines = [d["deadline"] for d in due]
    assert deadlines == sorted(deadlines)
