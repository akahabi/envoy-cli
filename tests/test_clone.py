"""Tests for envoy.clone."""

from __future__ import annotations

import pytest
from pathlib import Path

from envoy.clone import CloneError, clone_profile
from envoy.sync import push_profile, pull_profile


PASSPHRASE = "test-secret"


@pytest.fixture()
def profiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "profiles"
    d.mkdir()
    return d


def _seed(profiles_dir: Path, name: str, vars_: dict) -> None:
    push_profile(profiles_dir, name, vars_, PASSPHRASE)


def test_clone_copies_all_vars(profiles_dir: Path) -> None:
    _seed(profiles_dir, "staging", {"KEY": "value", "DB": "postgres"})
    result = clone_profile(profiles_dir, "staging", "production", PASSPHRASE)
    assert result == {"KEY": "value", "DB": "postgres"}


def test_clone_creates_dst_profile(profiles_dir: Path) -> None:
    _seed(profiles_dir, "staging", {"A": "1"})
    clone_profile(profiles_dir, "staging", "production", PASSPHRASE)
    recovered = pull_profile(profiles_dir, "production", PASSPHRASE)
    assert recovered == {"A": "1"}


def test_clone_applies_overrides(profiles_dir: Path) -> None:
    _seed(profiles_dir, "staging", {"KEY": "old", "OTHER": "x"})
    result = clone_profile(
        profiles_dir, "staging", "production", PASSPHRASE, overrides={"KEY": "new"}
    )
    assert result["KEY"] == "new"
    assert result["OTHER"] == "x"


def test_clone_overrides_add_new_keys(profiles_dir: Path) -> None:
    _seed(profiles_dir, "staging", {"EXISTING": "yes"})
    result = clone_profile(
        profiles_dir, "staging", "production", PASSPHRASE, overrides={"FRESH": "new"}
    )
    assert result["FRESH"] == "new"
    assert result["EXISTING"] == "yes"


def test_clone_missing_source_raises(profiles_dir: Path) -> None:
    with pytest.raises(CloneError, match="Source profile 'ghost' does not exist"):
        clone_profile(profiles_dir, "ghost", "production", PASSPHRASE)


def test_clone_existing_destination_raises(profiles_dir: Path) -> None:
    _seed(profiles_dir, "staging", {"A": "1"})
    _seed(profiles_dir, "production", {"B": "2"})
    with pytest.raises(CloneError, match="Destination profile 'production' already exists"):
        clone_profile(profiles_dir, "staging", "production", PASSPHRASE)


def test_clone_no_overrides_leaves_source_unchanged(profiles_dir: Path) -> None:
    original = {"X": "10", "Y": "20"}
    _seed(profiles_dir, "staging", original)
    clone_profile(profiles_dir, "staging", "copy", PASSPHRASE)
    assert pull_profile(profiles_dir, "staging", PASSPHRASE) == original
