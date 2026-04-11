"""CLI tests for tag commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envoy.cli_tag import tag_cmd
from envoy.store import save_store, set_env_var
from envoy.tag import add_tag

_PASS = "secret"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def store_file(tmp_path):
    path = str(tmp_path / "test.envoy")
    store = {"vars": {}}
    save_store(path, _PASS, store)
    set_env_var(path, _PASS, "API_KEY", "abc123")
    set_env_var(path, _PASS, "DB_URL", "postgres://localhost")
    return path


def _invoke(runner, args, store, passphrase=_PASS):
    return runner.invoke(tag_cmd, [*args, "--store", store, "--passphrase", passphrase])


def test_add_success(runner, store_file):
    result = _invoke(runner, ["add", "API_KEY", "sensitive"], store_file)
    assert result.exit_code == 0
    assert "sensitive" in result.output


def test_add_unknown_var_exits_nonzero(runner, store_file):
    result = _invoke(runner, ["add", "MISSING", "tag"], store_file)
    assert result.exit_code != 0
    assert "Error" in result.output


def test_remove_success(runner, store_file):
    add_tag(store_file, _PASS, "API_KEY", "sensitive")
    result = _invoke(runner, ["remove", "API_KEY", "sensitive"], store_file)
    assert result.exit_code == 0


def test_remove_missing_tag_exits_nonzero(runner, store_file):
    result = _invoke(runner, ["remove", "API_KEY", "ghost"], store_file)
    assert result.exit_code != 0


def test_list_shows_tags(runner, store_file):
    add_tag(store_file, _PASS, "API_KEY", "prod")
    result = _invoke(runner, ["list"], store_file)
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "prod" in result.output


def test_list_no_tags_message(runner, store_file):
    result = _invoke(runner, ["list"], store_file)
    assert result.exit_code == 0
    assert "No tags" in result.output


def test_filter_returns_tagged_vars(runner, store_file):
    add_tag(store_file, _PASS, "API_KEY", "sensitive")
    result = _invoke(runner, ["filter", "sensitive"], store_file)
    assert result.exit_code == 0
    assert "API_KEY" in result.output


def test_filter_no_match_message(runner, store_file):
    result = _invoke(runner, ["filter", "nonexistent"], store_file)
    assert result.exit_code == 0
    assert "No variables" in result.output
