"""Tests for envoy.cli_rename CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_rename import rename_cmd
from envoy.store import save_store, load_store


PASS = "test-passphrase"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    path = tmp_path / "store.bin"
    save_store(path, PASS, {"ALPHA": "a", "BETA": "b"})
    return path


def _invoke(runner: CliRunner, store_file: Path, *args: str):
    return runner.invoke(
        rename_cmd,
        ["key", *args, "--store", str(store_file), "--passphrase", PASS],
        catch_exceptions=False,
    )


def test_rename_key_success(runner: CliRunner, store_file: Path) -> None:
    result = _invoke(runner, store_file, "ALPHA", "ALPHA_RENAMED")
    assert result.exit_code == 0
    assert "ALPHA" in result.output and "ALPHA_RENAMED" in result.output


def test_rename_key_persists(runner: CliRunner, store_file: Path) -> None:
    _invoke(runner, store_file, "ALPHA", "ALPHA_NEW")
    reloaded = load_store(store_file, PASS)
    assert "ALPHA_NEW" in reloaded
    assert "ALPHA" not in reloaded


def test_rename_missing_key_exits_nonzero(runner: CliRunner, store_file: Path) -> None:
    result = _invoke(runner, store_file, "NOPE", "WHATEVER")
    assert result.exit_code != 0


def test_rename_conflict_without_overwrite_exits_nonzero(
    runner: CliRunner, store_file: Path
) -> None:
    result = _invoke(runner, store_file, "ALPHA", "BETA")
    assert result.exit_code != 0


def test_rename_conflict_with_overwrite_succeeds(
    runner: CliRunner, store_file: Path
) -> None:
    result = runner.invoke(
        rename_cmd,
        ["key", "ALPHA", "BETA", "--overwrite", "--store", str(store_file), "--passphrase", PASS],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    reloaded = load_store(store_file, PASS)
    assert reloaded["BETA"] == "a"


def test_rename_missing_store_exits_nonzero(
    runner: CliRunner, tmp_path: Path
) -> None:
    missing = tmp_path / "no_such_store.bin"
    result = runner.invoke(
        rename_cmd,
        ["key", "FOO", "BAR", "--store", str(missing), "--passphrase", PASS],
        catch_exceptions=False,
    )
    assert result.exit_code != 0
