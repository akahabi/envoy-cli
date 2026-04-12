"""Tests for envoy.history and envoy.cli_history."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.history import HistoryError, clear_history, read_history, record_change
from envoy.cli_history import history_cmd


@pytest.fixture()
def store_file(tmp_path: Path) -> str:
    return str(tmp_path / "test.envoy.enc")


# ---------------------------------------------------------------------------
# Unit tests for history.py
# ---------------------------------------------------------------------------

def test_record_change_returns_entry(store_file: str) -> None:
    entry = record_change(store_file, "set", "API_KEY", new_value="abc")
    assert entry["action"] == "set"
    assert entry["key"] == "API_KEY"
    assert entry["new_value"] == "abc"
    assert "timestamp" in entry


def test_record_change_persists_file(store_file: str) -> None:
    record_change(store_file, "set", "FOO", new_value="bar")
    history_path = Path(store_file).parent / "test.history.json"
    assert history_path.exists()
    data = json.loads(history_path.read_text())
    assert len(data) == 1


def test_multiple_records_accumulate(store_file: str) -> None:
    record_change(store_file, "set", "A", new_value="1")
    record_change(store_file, "set", "B", new_value="2")
    entries = read_history(store_file)
    assert len(entries) == 2


def test_read_history_empty_when_no_file(store_file: str) -> None:
    assert read_history(store_file) == []


def test_read_history_filter_by_key(store_file: str) -> None:
    record_change(store_file, "set", "FOO", new_value="1")
    record_change(store_file, "set", "BAR", new_value="2")
    entries = read_history(store_file, key="FOO")
    assert len(entries) == 1
    assert entries[0]["key"] == "FOO"


def test_read_history_filter_by_action(store_file: str) -> None:
    record_change(store_file, "set", "FOO", new_value="1")
    record_change(store_file, "delete", "FOO")
    entries = read_history(store_file, action="delete")
    assert len(entries) == 1
    assert entries[0]["action"] == "delete"


def test_read_history_limit(store_file: str) -> None:
    for i in range(10):
        record_change(store_file, "set", f"K{i}", new_value=str(i))
    entries = read_history(store_file, limit=3)
    assert len(entries) == 3
    # limit returns the most recent entries
    assert entries[-1]["key"] == "K9"


def test_clear_history_removes_file(store_file: str) -> None:
    record_change(store_file, "set", "X", new_value="y")
    clear_history(store_file)
    assert read_history(store_file) == []


def test_corrupt_history_raises(store_file: str, tmp_path: Path) -> None:
    history_path = tmp_path / "test.history.json"
    history_path.write_text("not valid json")
    with pytest.raises(HistoryError):
        read_history(store_file)


# ---------------------------------------------------------------------------
# CLI tests for cli_history.py
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_log_no_entries(runner: CliRunner, store_file: str) -> None:
    result = runner.invoke(history_cmd, ["log", "--store", store_file])
    assert result.exit_code == 0
    assert "No history" in result.output


def test_log_shows_entries(runner: CliRunner, store_file: str) -> None:
    record_change(store_file, "set", "MY_VAR", old_value=None, new_value="hello")
    result = runner.invoke(history_cmd, ["log", "--store", store_file])
    assert result.exit_code == 0
    assert "MY_VAR" in result.output
    assert "SET" in result.output


def test_log_with_key_filter(runner: CliRunner, store_file: str) -> None:
    record_change(store_file, "set", "A", new_value="1")
    record_change(store_file, "set", "B", new_value="2")
    result = runner.invoke(history_cmd, ["log", "--store", store_file, "--key", "A"])
    assert result.exit_code == 0
    assert "A" in result.output
    assert "B" not in result.output
