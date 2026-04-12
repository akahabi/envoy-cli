"""Integration tests for the alias CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envoy.cli_alias import alias_cmd


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    p = tmp_path / ".envoy"
    p.write_text("{}")
    return p


def _invoke(runner: CliRunner, store: Path, args: list) -> object:
    return runner.invoke(alias_cmd, ["--store", str(store)] + args, catch_exceptions=False)


def test_add_success(runner: CliRunner, store_file: Path) -> None:
    with patch("envoy.cli_alias.get_env_vars", return_value={"DATABASE_URL": "postgres://"}), \
         patch("envoy.cli_alias.add_alias", return_value={"db": "DATABASE_URL"}) as mock_add:
        result = runner.invoke(
            alias_cmd,
            ["add", "db", "DATABASE_URL", "--store", str(store_file), "--passphrase", "s3cr3t"],
            catch_exceptions=False,
        )
    assert result.exit_code == 0
    assert "added" in result.output
    mock_add.assert_called_once()


def test_add_unknown_key_exits_nonzero(runner: CliRunner, store_file: Path) -> None:
    with patch("envoy.cli_alias.get_env_vars", return_value={}):
        result = runner.invoke(
            alias_cmd,
            ["add", "db", "DATABASE_URL", "--store", str(store_file), "--passphrase", "s3cr3t"],
        )
    assert result.exit_code != 0


def test_remove_success(runner: CliRunner, store_file: Path) -> None:
    with patch("envoy.cli_alias.remove_alias", return_value={}) as mock_rm:
        result = _invoke(runner, store_file, ["remove", "db"])
    assert result.exit_code == 0
    assert "removed" in result.output
    mock_rm.assert_called_once()


def test_remove_missing_exits_nonzero(runner: CliRunner, store_file: Path) -> None:
    result = _invoke(runner, store_file, ["remove", "ghost"])
    assert result.exit_code != 0


def test_list_empty(runner: CliRunner, store_file: Path) -> None:
    result = _invoke(runner, store_file, ["list"])
    assert result.exit_code == 0
    assert "No aliases" in result.output


def test_resolve_missing_exits_nonzero(runner: CliRunner, store_file: Path) -> None:
    result = _invoke(runner, store_file, ["resolve", "nope"])
    assert result.exit_code != 0
