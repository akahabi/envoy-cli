"""Tests for envoy.cli_archive."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_archive import archive_cmd
from envoy.sync import push_profile
from envoy.store import save_store


PASS = "hunter2"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def profiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "profiles"
    d.mkdir()
    return d


def _seed(profiles_dir: Path, name: str, vars_: dict) -> None:
    store_file = profiles_dir.parent / "store.enc"
    save_store(store_file, vars_, PASS)
    push_profile(store_file, profiles_dir, name, PASS)


def _invoke(runner: CliRunner, *args: str):
    return runner.invoke(archive_cmd, list(args), catch_exceptions=False)


def test_pack_success(runner: CliRunner, profiles_dir: Path, tmp_path: Path) -> None:
    _seed(profiles_dir, "staging", {"A": "1"})
    out = tmp_path / "bundle.zip"
    result = _invoke(
        runner,
        "pack", "staging",
        "--profiles-dir", str(profiles_dir),
        "--output", str(out),
        "--passphrase", PASS,
    )
    assert result.exit_code == 0
    assert out.exists()
    assert "1 profile" in result.output


def test_pack_missing_profile_exits_nonzero(runner: CliRunner, profiles_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.zip"
    result = runner.invoke(
        archive_cmd,
        ["pack", "ghost", "--profiles-dir", str(profiles_dir), "--output", str(out), "--passphrase", PASS],
    )
    assert result.exit_code != 0


def test_unpack_success(runner: CliRunner, profiles_dir: Path, tmp_path: Path) -> None:
    _seed(profiles_dir, "prod", {"DB": "pg"})
    out = tmp_path / "bundle.zip"
    _invoke(runner, "pack", "prod", "--profiles-dir", str(profiles_dir), "--output", str(out), "--passphrase", PASS)

    dest = tmp_path / "restored"
    result = _invoke(runner, "unpack", str(out), "--profiles-dir", str(dest), "--passphrase", PASS)
    assert result.exit_code == 0
    assert "prod" in result.output


def test_unpack_overwrite_flag(runner: CliRunner, profiles_dir: Path, tmp_path: Path) -> None:
    _seed(profiles_dir, "staging", {"X": "1"})
    out = tmp_path / "bundle.zip"
    _invoke(runner, "pack", "staging", "--profiles-dir", str(profiles_dir), "--output", str(out), "--passphrase", PASS)

    dest = tmp_path / "out"
    _invoke(runner, "unpack", str(out), "--profiles-dir", str(dest), "--passphrase", PASS)
    result = _invoke(runner, "unpack", str(out), "--profiles-dir", str(dest), "--passphrase", PASS, "--overwrite")
    assert result.exit_code == 0
