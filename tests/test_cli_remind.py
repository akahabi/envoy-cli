"""Tests for envoy.cli_remind."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_remind import remind_cmd
from envoy.store import save_store

PASSPHRASE = "test-pass"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    p = tmp_path / ".envoy"
    save_store(p, PASSPHRASE, {"SECRET": "val", "TOKEN": "tok"})
    return p


def _invoke(runner, store_file, *args):
    return runner.invoke(remind_cmd, ["--store", str(store_file)] + list(args))


def test_set_success(runner, store_file):
    result = runner.invoke(
        remind_cmd,
        ["set", "SECRET", "2099-01-01", "--store", str(store_file), "--passphrase", PASSPHRASE],
    )
    assert result.exit_code == 0
    assert "2099-01-01" in result.output


def test_set_unknown_key_exits_nonzero(runner, store_file):
    result = runner.invoke(
        remind_cmd,
        ["set", "NOPE", "2099-01-01", "--store", str(store_file), "--passphrase", PASSPHRASE],
    )
    assert result.exit_code != 0
    assert "Error" in result.output


def test_set_bad_date_exits_nonzero(runner, store_file):
    result = runner.invoke(
        remind_cmd,
        ["set", "SECRET", "bad-date", "--store", str(store_file), "--passphrase", PASSPHRASE],
    )
    assert result.exit_code != 0


def test_list_empty(runner, store_file):
    result = _invoke(runner, store_file, "list")
    assert result.exit_code == 0
    assert "No reminders" in result.output


def test_list_shows_entries(runner, store_file):
    runner.invoke(
        remind_cmd,
        ["set", "TOKEN", "2099-05-01", "--note", "quarterly", "--store", str(store_file), "--passphrase", PASSPHRASE],
    )
    result = _invoke(runner, store_file, "list")
    assert "TOKEN" in result.output
    assert "2099-05-01" in result.output
    assert "quarterly" in result.output


def test_remove_existing(runner, store_file):
    runner.invoke(
        remind_cmd,
        ["set", "SECRET", "2099-01-01", "--store", str(store_file), "--passphrase", PASSPHRASE],
    )
    result = _invoke(runner, store_file, "remove", "SECRET")
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_absent(runner, store_file):
    result = _invoke(runner, store_file, "remove", "SECRET")
    assert result.exit_code == 0
    assert "No reminder" in result.output


def test_due_shows_overdue(runner, store_file):
    runner.invoke(
        remind_cmd,
        ["set", "SECRET", "2000-01-01", "--store", str(store_file), "--passphrase", PASSPHRASE],
    )
    result = runner.invoke(
        remind_cmd,
        ["due", "--store", str(store_file), "--as-of", "2025-06-01"],
    )
    assert result.exit_code == 0
    assert "SECRET" in result.output
