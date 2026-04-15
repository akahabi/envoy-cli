"""Tests for envoy.group and envoy.cli_group."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from envoy.store import save_store
from envoy.group import GroupError, add_group, remove_group, list_groups, get_group_vars
from envoy.cli_group import group_cmd

PASS = "testpass"


@pytest.fixture()
def store_file(tmp_path: Path) -> str:
    path = str(tmp_path / "store.envoy")
    save_store(path, PASS, {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret"})
    return path


def test_add_group_returns_mapping(store_file):
    result = add_group(store_file, "database", ["DB_HOST", "DB_PORT"], PASS)
    assert result["database"] == ["DB_HOST", "DB_PORT"]


def test_add_group_persists_file(store_file):
    add_group(store_file, "database", ["DB_HOST"], PASS)
    assert "database" in list_groups(store_file)


def test_add_group_is_idempotent(store_file):
    add_group(store_file, "database", ["DB_HOST"], PASS)
    result = add_group(store_file, "database", ["DB_HOST"], PASS)
    assert result["database"].count("DB_HOST") == 1


def test_add_group_unknown_key_raises(store_file):
    with pytest.raises(GroupError, match="MISSING"):
        add_group(store_file, "bad", ["MISSING"], PASS)


def test_remove_group(store_file):
    add_group(store_file, "database", ["DB_HOST"], PASS)
    remove_group(store_file, "database")
    assert "database" not in list_groups(store_file)


def test_remove_group_missing_raises(store_file):
    with pytest.raises(GroupError, match="does not exist"):
        remove_group(store_file, "nonexistent")


def test_list_groups_empty_when_no_file(store_file):
    assert list_groups(store_file) == {}


def test_get_group_vars_returns_values(store_file):
    add_group(store_file, "database", ["DB_HOST", "DB_PORT"], PASS)
    vars_ = get_group_vars(store_file, "database", PASS)
    assert vars_ == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_get_group_vars_missing_group_raises(store_file):
    with pytest.raises(GroupError, match="does not exist"):
        get_group_vars(store_file, "nope", PASS)


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, store_file, *args):
    return runner.invoke(group_cmd, list(args) + ["--store", store_file, "--passphrase", PASS])


def test_cli_add_success(runner, store_file):
    result = runner.invoke(group_cmd, ["add", "db", "DB_HOST", "--store", store_file, "--passphrase", PASS])
    assert result.exit_code == 0
    assert "db" in result.output


def test_cli_add_unknown_key_exits_nonzero(runner, store_file):
    result = runner.invoke(group_cmd, ["add", "db", "NOPE", "--store", store_file, "--passphrase", PASS])
    assert result.exit_code != 0


def test_cli_list_shows_groups(runner, store_file):
    add_group(store_file, "db", ["DB_HOST"], PASS)
    result = runner.invoke(group_cmd, ["list", "--store", store_file])
    assert "db" in result.output


def test_cli_list_empty_message(runner, store_file):
    result = runner.invoke(group_cmd, ["list", "--store", store_file])
    assert "No groups" in result.output


def test_cli_remove_success(runner, store_file):
    add_group(store_file, "db", ["DB_HOST"], PASS)
    result = runner.invoke(group_cmd, ["remove", "db", "--store", store_file])
    assert result.exit_code == 0
    assert "removed" in result.output
