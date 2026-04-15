"""Tests for envoy.copy module."""

from __future__ import annotations

from pathlib import Path

import pytest

from envoy.copy import CopyError, copy_key, copy_vars
from envoy.store import load_store, save_store

PASS_A = "passphrase-a"
PASS_B = "passphrase-b"


@pytest.fixture()
def src_store(tmp_path: Path) -> Path:
    p = tmp_path / "src.env"
    save_store(p, PASS_A, {"FOO": "foo_val", "BAR": "bar_val", "BAZ": "baz_val"})
    return p


@pytest.fixture()
def dst_store(tmp_path: Path) -> Path:
    p = tmp_path / "dst.env"
    save_store(p, PASS_B, {"EXISTING": "keep_me"})
    return p


def test_copy_vars_all_keys(src_store: Path, tmp_path: Path) -> None:
    dst = tmp_path / "new.env"
    copied = copy_vars(src_store, dst, PASS_A, PASS_B)
    assert set(copied.keys()) == {"FOO", "BAR", "BAZ"}
    result = load_store(dst, PASS_B)
    assert result["FOO"] == "foo_val"
    assert result["BAR"] == "bar_val"


def test_copy_vars_specific_keys(src_store: Path, tmp_path: Path) -> None:
    dst = tmp_path / "partial.env"
    copied = copy_vars(src_store, dst, PASS_A, PASS_B, keys=["FOO"])
    assert list(copied.keys()) == ["FOO"]
    result = load_store(dst, PASS_B)
    assert "FOO" in result
    assert "BAR" not in result


def test_copy_vars_missing_key_raises(src_store: Path, tmp_path: Path) -> None:
    dst = tmp_path / "x.env"
    with pytest.raises(CopyError, match="NOPE"):
        copy_vars(src_store, dst, PASS_A, PASS_B, keys=["NOPE"])


def test_copy_vars_no_overwrite_skips_existing(src_store: Path, dst_store: Path) -> None:
    save_store(dst_store, PASS_B, {"FOO": "original", "EXISTING": "keep_me"})
    copied = copy_vars(src_store, dst_store, PASS_A, PASS_B, keys=["FOO", "BAR"], overwrite=False)
    assert "FOO" not in copied
    assert "BAR" in copied
    result = load_store(dst_store, PASS_B)
    assert result["FOO"] == "original"


def test_copy_vars_missing_src_raises(tmp_path: Path) -> None:
    with pytest.raises(CopyError, match="Source store not found"):
        copy_vars(tmp_path / "ghost.env", tmp_path / "dst.env", PASS_A, PASS_B)


def test_copy_key_single(src_store: Path, tmp_path: Path) -> None:
    dst = tmp_path / "single.env"
    dest_key, value = copy_key(src_store, dst, "FOO", PASS_A, PASS_B)
    assert dest_key == "FOO"
    assert value == "foo_val"
    result = load_store(dst, PASS_B)
    assert result["FOO"] == "foo_val"


def test_copy_key_with_rename(src_store: Path, tmp_path: Path) -> None:
    dst = tmp_path / "renamed.env"
    dest_key, value = copy_key(src_store, dst, "FOO", PASS_A, PASS_B, new_key="RENAMED_FOO")
    assert dest_key == "RENAMED_FOO"
    result = load_store(dst, PASS_B)
    assert "RENAMED_FOO" in result
    assert "FOO" not in result


def test_copy_key_missing_raises(src_store: Path, tmp_path: Path) -> None:
    dst = tmp_path / "x.env"
    with pytest.raises(CopyError, match="MISSING"):
        copy_key(src_store, dst, "MISSING", PASS_A, PASS_B)


def test_copy_vars_preserves_existing_dst_keys(src_store: Path, dst_store: Path) -> None:
    copy_vars(src_store, dst_store, PASS_A, PASS_B, keys=["FOO"])
    result = load_store(dst_store, PASS_B)
    assert result["EXISTING"] == "keep_me"
    assert result["FOO"] == "foo_val"
