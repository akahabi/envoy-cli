"""Tests for envoy.cli_copy CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_copy import copy_cmd
from envoy.store import load_store, save_store

PASS_A = "src-pass"
PASS_B = "dst-pass"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


@pytest.fixture()
def src_store(tmp_path: Path) -> Path:
    p = tmp_path / "src.env"
    save_store(p, PASS_A, {"ALPHA": "1", "BETA": "2"})
    return p


def _invoke(runner: CliRunner, *args: str):
    return runner.invoke(copy_cmd, args, catch_exceptions=False)


def test_vars_copies_all(runner: CliRunner, src_store: Path, tmp_path: Path) -> None:
    dst = tmp_path / "dst.env"
    result = _invoke(
        runner, "vars", str(src_store), str(dst),
        "--src-pass", PASS_A, "--dst-pass", PASS_B,
    )
    assert result.exit_code == 0
    assert "2 variable(s)" in result.output
    loaded = load_store(dst, PASS_B)
    assert loaded["ALPHA"] == "1"
    assert loaded["BETA"] == "2"


def test_vars_specific_key(runner: CliRunner, src_store: Path, tmp_path: Path) -> None:
    dst = tmp_path / "dst.env"
    result = _invoke(
        runner, "vars", str(src_store), str(dst),
        "--src-pass", PASS_A, "--dst-pass", PASS_B,
        "--key", "ALPHA",
    )
    assert result.exit_code == 0
    loaded = load_store(dst, PASS_B)
    assert "ALPHA" in loaded
    assert "BETA" not in loaded


def test_vars_missing_key_exits_nonzero(runner: CliRunner, src_store: Path, tmp_path: Path) -> None:
    dst = tmp_path / "dst.env"
    result = runner.invoke(
        copy_cmd,
        ["vars", str(src_store), str(dst), "--src-pass", PASS_A, "--dst-pass", PASS_B, "--key", "NOPE"],
    )
    assert result.exit_code != 0


def test_key_copies_single(runner: CliRunner, src_store: Path, tmp_path: Path) -> None:
    dst = tmp_path / "dst.env"
    result = _invoke(
        runner, "key", str(src_store), str(dst), "ALPHA",
        "--src-pass", PASS_A, "--dst-pass", PASS_B,
    )
    assert result.exit_code == 0
    assert "'ALPHA'" in result.output
    loaded = load_store(dst, PASS_B)
    assert loaded["ALPHA"] == "1"


def test_key_with_rename(runner: CliRunner, src_store: Path, tmp_path: Path) -> None:
    dst = tmp_path / "dst.env"
    result = _invoke(
        runner, "key", str(src_store), str(dst), "ALPHA",
        "--src-pass", PASS_A, "--dst-pass", PASS_B,
        "--rename", "NEW_ALPHA",
    )
    assert result.exit_code == 0
    assert "NEW_ALPHA" in result.output
    loaded = load_store(dst, PASS_B)
    assert "NEW_ALPHA" in loaded
    assert "ALPHA" not in loaded


def test_key_missing_exits_nonzero(runner: CliRunner, src_store: Path, tmp_path: Path) -> None:
    dst = tmp_path / "dst.env"
    result = runner.invoke(
        copy_cmd,
        ["key", str(src_store), str(dst), "GHOST", "--src-pass", PASS_A, "--dst-pass", PASS_B],
    )
    assert result.exit_code != 0
