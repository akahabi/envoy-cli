"""Tests for envoy.cli_schedule."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_schedule import schedule_cmd
from envoy.schedule import _schedule_path, set_schedule


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def store_file(tmp_path: Path) -> str:
    p = tmp_path / ".envoy_store"
    p.write_text(json.dumps({"vars": {"API_KEY": "secret"}}))
    return str(p)


def _invoke(runner: CliRunner, store: str, *args: str):
    return runner.invoke(schedule_cmd, [*args, "--store", store])


def test_set_success(runner: CliRunner, store_file: str) -> None:
    result = _invoke(runner, store_file, "set", "API_KEY", "7")
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "7 day(s)" in result.output


def test_set_invalid_interval_exits_nonzero(runner: CliRunner, store_file: str) -> None:
    result = _invoke(runner, store_file, "set", "API_KEY", "0")
    assert result.exit_code != 0
    assert "Error" in result.output


def test_remove_success(runner: CliRunner, store_file: str) -> None:
    set_schedule(store_file, "API_KEY", 7)
    result = _invoke(runner, store_file, "remove", "API_KEY")
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_remove_missing_key_exits_nonzero(runner: CliRunner, store_file: str) -> None:
    result = _invoke(runner, store_file, "remove", "GHOST")
    assert result.exit_code != 0


def test_list_empty(runner: CliRunner, store_file: str) -> None:
    result = _invoke(runner, store_file, "list")
    assert result.exit_code == 0
    assert "No schedules" in result.output


def test_list_shows_entries(runner: CliRunner, store_file: str) -> None:
    set_schedule(store_file, "API_KEY", 14)
    result = _invoke(runner, store_file, "list")
    assert "API_KEY" in result.output
    assert "14" in result.output


def test_due_no_overdue(runner: CliRunner, store_file: str) -> None:
    set_schedule(store_file, "API_KEY", 7)
    result = _invoke(runner, store_file, "due")
    assert result.exit_code == 0
    assert "No keys" in result.output


def test_due_shows_overdue(runner: CliRunner, store_file: str) -> None:
    set_schedule(store_file, "API_KEY", 7)
    p = _schedule_path(store_file)
    data = json.loads(p.read_text())
    data["API_KEY"]["due_at"] = (datetime.utcnow() - timedelta(days=1)).isoformat()
    p.write_text(json.dumps(data))
    result = _invoke(runner, store_file, "due")
    assert "API_KEY" in result.output
    assert "overdue" in result.output.lower() or "due" in result.output.lower()
