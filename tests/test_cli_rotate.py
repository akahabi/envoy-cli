"""CLI integration tests for the rotate commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envoy.cli_rotate import rotate
from envoy.rotate import RotationError


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# ---------------------------------------------------------------------------
# rotate store
# ---------------------------------------------------------------------------

def test_rotate_store_success(runner: CliRunner, tmp_path: Path) -> None:
    store = str(tmp_path / "test.enc")
    store_path = Path(store)
    store_path.write_bytes(b"placeholder")  # file must exist

    with patch("envoy.cli_rotate.rotate_store", return_value={"A": "1", "B": "2"}) as mock:
        result = runner.invoke(
            rotate,
            ["store", "--store", store,
             "--old-passphrase", "old", "--new-passphrase", "new"],
        )
    assert result.exit_code == 0
    assert "2 variable(s)" in result.output
    mock.assert_called_once()


def test_rotate_store_missing_file(runner: CliRunner, tmp_path: Path) -> None:
    missing = str(tmp_path / "ghost.enc")
    result = runner.invoke(
        rotate,
        ["store", "--store", missing,
         "--old-passphrase", "old", "--new-passphrase", "new"],
    )
    assert result.exit_code != 0
    assert "not found" in result.output


def test_rotate_store_rotation_error(runner: CliRunner, tmp_path: Path) -> None:
    store = str(tmp_path / "test.enc")
    Path(store).write_bytes(b"x")
    with patch("envoy.cli_rotate.rotate_store", side_effect=RotationError("bad pass")):
        result = runner.invoke(
            rotate,
            ["store", "--store", store,
             "--old-passphrase", "old", "--new-passphrase", "new"],
        )
    assert result.exit_code != 0
    assert "bad pass" in result.output


# ---------------------------------------------------------------------------
# rotate profile
# ---------------------------------------------------------------------------

def test_rotate_profile_success(runner: CliRunner, tmp_path: Path) -> None:
    pdir = str(tmp_path / "profiles")
    with patch("envoy.cli_rotate.rotate_profile", return_value={"X": "1"}) as mock:
        result = runner.invoke(
            rotate,
            ["profile", "staging", "--profiles-dir", pdir,
             "--old-passphrase", "old", "--new-passphrase", "new"],
        )
    assert result.exit_code == 0
    assert "staging" in result.output
    assert "1 variable(s)" in result.output
    mock.assert_called_once()


def test_rotate_profile_not_found(runner: CliRunner, tmp_path: Path) -> None:
    pdir = str(tmp_path / "profiles")
    with patch("envoy.cli_rotate.rotate_profile",
               side_effect=RotationError("Profile 'prod' not found.")):
        result = runner.invoke(
            rotate,
            ["profile", "prod", "--profiles-dir", pdir,
             "--old-passphrase", "old", "--new-passphrase", "new"],
        )
    assert result.exit_code != 0
    assert "not found" in result.output
