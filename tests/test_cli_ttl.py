"""Tests for envoy/cli_ttl.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_ttl import ttl_cmd
from envoy.store import save_store
from envoy.ttl import _ttl_path

PASSPHRASE = "test-secret"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    p = tmp_path / ".envoy"
    save_store(p, PASSPHRASE, {"API_KEY": "abc", "DB_PASS": "xyz"})
    return p


def _invoke(runner, store_file, *args):
    return runner.invoke(
        ttl_cmd,
        ["--store", str(store_file)] + list(args),
        input=f"{PASSPHRASE}\n",
        catch_exceptions=False,
    )


def test_set_success(runner, store_file):
    result = runner.invoke(
        ttl_cmd,
        ["set", "API_KEY", "3600", "--store", str(store_file), "--passphrase", PASSPHRASE],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "expires at" in result.output


def test_set_unknown_key_exits_nonzero(runner, store_file):
    result = runner.invoke(
        ttl_cmd,
        ["set", "GHOST", "60", "--store", str(store_file), "--passphrase", PASSPHRASE],
    )
    assert result.exit_code != 0
    assert "Error" in result.output


def test_list_empty(runner, store_file):
    result = _invoke(runner, store_file, "list")
    assert "No TTL" in result.output


def test_list_shows_entries(runner, store_file):
    runner.invoke(
        ttl_cmd,
        ["set", "API_KEY", "60", "--store", str(store_file), "--passphrase", PASSPHRASE],
    )
    result = _invoke(runner, store_file, "list")
    assert "API_KEY" in result.output


def test_remove_clears_entry(runner, store_file):
    runner.invoke(
        ttl_cmd,
        ["set", "API_KEY", "60", "--store", str(store_file), "--passphrase", PASSPHRASE],
    )
    result = _invoke(runner, store_file, "remove", "API_KEY")
    assert result.exit_code == 0
    data = json.loads(_ttl_path(store_file).read_text())
    assert "API_KEY" not in data


def test_expired_shows_expired_keys(runner, store_file):
    runner.invoke(
        ttl_cmd,
        ["set", "DB_PASS", "60", "--store", str(store_file), "--passphrase", PASSPHRASE],
    )
    ttl_file = _ttl_path(store_file)
    data = json.loads(ttl_file.read_text())
    data["DB_PASS"]["expires_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    ttl_file.write_text(json.dumps(data))
    result = _invoke(runner, store_file, "expired")
    assert "DB_PASS" in result.output
    assert "EXPIRED" in result.output
