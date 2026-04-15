"""Tests for envoy.archive."""

from __future__ import annotations

import pytest
from pathlib import Path

from envoy.archive import ArchiveError, pack, unpack
from envoy.sync import push_profile


PASS = "hunter2"


@pytest.fixture()
def profiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "profiles"
    d.mkdir()
    return d


def _seed(profiles_dir: Path, name: str, vars_: dict) -> None:
    store_file = profiles_dir.parent / "store.enc"
    from envoy.store import save_store

    save_store(store_file, vars_, PASS)
    push_profile(store_file, profiles_dir, name, PASS)


def test_pack_produces_bytes(profiles_dir: Path, tmp_path: Path) -> None:
    _seed(profiles_dir, "staging", {"A": "1"})
    data = pack(["staging"], profiles_dir, PASS)
    assert isinstance(data, bytes)
    assert len(data) > 0


def test_pack_missing_profile_raises(profiles_dir: Path) -> None:
    with pytest.raises(ArchiveError, match="not found"):
        pack(["ghost"], profiles_dir, PASS)


def test_unpack_restores_profiles(profiles_dir: Path, tmp_path: Path) -> None:
    _seed(profiles_dir, "prod", {"DB": "postgres"})
    data = pack(["prod"], profiles_dir, PASS)

    dest = tmp_path / "restored"
    names = unpack(data, dest, PASS)
    assert names == ["prod"]
    assert (dest / "prod.enc").exists()


def test_unpack_multiple_profiles(profiles_dir: Path, tmp_path: Path) -> None:
    _seed(profiles_dir, "staging", {"X": "1"})
    _seed(profiles_dir, "prod", {"X": "2"})
    data = pack(["staging", "prod"], profiles_dir, PASS)

    dest = tmp_path / "out"
    names = unpack(data, dest, PASS)
    assert set(names) == {"staging", "prod"}


def test_unpack_raises_on_existing_without_overwrite(profiles_dir: Path, tmp_path: Path) -> None:
    _seed(profiles_dir, "staging", {"K": "v"})
    data = pack(["staging"], profiles_dir, PASS)

    dest = tmp_path / "out"
    unpack(data, dest, PASS)  # first unpack succeeds
    with pytest.raises(ArchiveError, match="already exists"):
        unpack(data, dest, PASS)  # second should fail


def test_unpack_overwrite_flag_replaces(profiles_dir: Path, tmp_path: Path) -> None:
    _seed(profiles_dir, "staging", {"K": "v"})
    data = pack(["staging"], profiles_dir, PASS)

    dest = tmp_path / "out"
    unpack(data, dest, PASS)
    names = unpack(data, dest, PASS, overwrite=True)  # should not raise
    assert "staging" in names


def test_unpack_bad_bytes_raises(tmp_path: Path) -> None:
    with pytest.raises(Exception):
        unpack(b"not a zip", tmp_path / "out", PASS)
