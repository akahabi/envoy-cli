"""Tests for envoy.cli_pin."""

import pytest
from click.testing import CliRunner

from envoy.cli_pin import pin_cmd
from envoy.store import save_store


PASS = "hunter2"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def store_file(tmp_path):
    p = tmp_path / "test.envoy"
    save_store(str(p), {"API_KEY": "secret", "PORT": "8080"}, PASS)
    return str(p)


def _invoke(runner, store_file, *args):
    return runner.invoke(pin_cmd, ["--store", store_file, *args])


def test_add_success(runner, store_file):
    result = _invoke(runner, store_file, "add", "PORT", "8080")
    assert result.exit_code == 0
    assert "Pinned" in result.output


def test_list_empty(runner, store_file):
    result = _invoke(runner, store_file, "list")
    assert result.exit_code == 0
    assert "No pins" in result.output


def test_list_shows_pins(runner, store_file):
    _invoke(runner, store_file, "add", "PORT", "8080")
    result = _invoke(runner, store_file, "list")
    assert "PORT" in result.output
    assert "8080" in result.output


def test_remove_success(runner, store_file):
    _invoke(runner, store_file, "add", "PORT", "8080")
    result = _invoke(runner, store_file, "remove", "PORT")
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_remove_unknown_key_exits_nonzero(runner, store_file):
    result = _invoke(runner, store_file, "remove", "GHOST")
    assert result.exit_code != 0


def test_check_all_ok(runner, store_file):
    _invoke(runner, store_file, "add", "PORT", "8080")
    result = runner.invoke(
        pin_cmd,
        ["--store", store_file, "check", "--passphrase", PASS],
    )
    assert result.exit_code == 0
    assert "OK" in result.output


def test_check_violation_exits_nonzero(runner, store_file):
    _invoke(runner, store_file, "add", "PORT", "9999")
    result = runner.invoke(
        pin_cmd,
        ["--store", store_file, "check", "--passphrase", PASS],
    )
    assert result.exit_code != 0
    assert "PORT" in result.output
