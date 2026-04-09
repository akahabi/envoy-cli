"""Unit tests for envoy.rotate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.store import save_store, load_store
from envoy.rotate import RotationError, rotate_store, rotate_profile


SAMPLE_VARS = {"KEY_A": "alpha", "KEY_B": "beta"}
OLD_PASS = "old-secret"
NEW_PASS = "new-secret"


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.enc"
    save_store(path, SAMPLE_VARS, OLD_PASS)
    return path


@pytest.fixture()
def profiles_dir(tmp_path: Path) -> Path:
    pdir = tmp_path / "profiles"
    pdir.mkdir()
    save_store(pdir / "staging.enc", SAMPLE_VARS, OLD_PASS)
    return pdir


# ---------------------------------------------------------------------------
# rotate_store
# ---------------------------------------------------------------------------

def test_rotate_store_returns_vars(store_file: Path) -> None:
    result = rotate_store(store_file, OLD_PASS, NEW_PASS)
    assert result == SAMPLE_VARS


def test_rotate_store_new_passphrase_works(store_file: Path) -> None:
    rotate_store(store_file, OLD_PASS, NEW_PASS)
    loaded = load_store(store_file, NEW_PASS)
    assert loaded == SAMPLE_VARS


def test_rotate_store_old_passphrase_fails_after_rotation(store_file: Path) -> None:
    rotate_store(store_file, OLD_PASS, NEW_PASS)
    with pytest.raises(Exception):
        load_store(store_file, OLD_PASS)


def test_rotate_store_wrong_old_passphrase_raises(store_file: Path) -> None:
    with pytest.raises(RotationError, match="Could not decrypt"):
        rotate_store(store_file, "wrong", NEW_PASS)


def test_rotate_store_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "ghost.enc"
    with pytest.raises(RotationError):
        rotate_store(missing, OLD_PASS, NEW_PASS)


# ---------------------------------------------------------------------------
# rotate_profile
# ---------------------------------------------------------------------------

def test_rotate_profile_success(profiles_dir: Path) -> None:
    result = rotate_profile(profiles_dir, "staging", OLD_PASS, NEW_PASS)
    assert result == SAMPLE_VARS


def test_rotate_profile_unknown_raises(profiles_dir: Path) -> None:
    with pytest.raises(RotationError, match="not found"):
        rotate_profile(profiles_dir, "production", OLD_PASS, NEW_PASS)


def test_rotate_profile_wrong_passphrase_raises(profiles_dir: Path) -> None:
    with pytest.raises(RotationError):
        rotate_profile(profiles_dir, "staging", "bad-pass", NEW_PASS)
