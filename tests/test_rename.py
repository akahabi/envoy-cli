"""Tests for envoy.rename."""

from __future__ import annotations

import pytest
from pathlib import Path

from envoy.store import save_store, load_store
from envoy.rename import RenameError, rename_var, bulk_rename


PASS = "test-passphrase"


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    path = tmp_path / "store.bin"
    save_store(path, PASS, {"FOO": "foo_val", "BAR": "bar_val", "BAZ": "baz_val"})
    return path


def test_rename_var_returns_updated_dict(store_file: Path) -> None:
    result = rename_var(store_file, PASS, "FOO", "FOO_RENAMED")
    assert "FOO_RENAMED" in result
    assert "FOO" not in result
    assert result["FOO_RENAMED"] == "foo_val"


def test_rename_var_persists_to_store(store_file: Path) -> None:
    rename_var(store_file, PASS, "FOO", "FOO_NEW")
    reloaded = load_store(store_file, PASS)
    assert "FOO_NEW" in reloaded
    assert "FOO" not in reloaded


def test_rename_preserves_other_keys(store_file: Path) -> None:
    rename_var(store_file, PASS, "FOO", "FOO_X")
    reloaded = load_store(store_file, PASS)
    assert reloaded["BAR"] == "bar_val"
    assert reloaded["BAZ"] == "baz_val"


def test_rename_missing_key_raises(store_file: Path) -> None:
    with pytest.raises(RenameError, match="Key not found"):
        rename_var(store_file, PASS, "MISSING", "NEW_KEY")


def test_rename_identical_keys_raises(store_file: Path) -> None:
    with pytest.raises(RenameError, match="identical"):
        rename_var(store_file, PASS, "FOO", "FOO")


def test_rename_existing_key_without_overwrite_raises(store_file: Path) -> None:
    with pytest.raises(RenameError, match="already exists"):
        rename_var(store_file, PASS, "FOO", "BAR")


def test_rename_existing_key_with_overwrite_succeeds(store_file: Path) -> None:
    result = rename_var(store_file, PASS, "FOO", "BAR", overwrite=True)
    assert result["BAR"] == "foo_val"
    assert "FOO" not in result


def test_bulk_rename_multiple_keys(store_file: Path) -> None:
    result = bulk_rename(store_file, PASS, {"FOO": "FOO2", "BAR": "BAR2"})
    assert "FOO2" in result and "BAR2" in result
    assert "FOO" not in result and "BAR" not in result


def test_bulk_rename_rolls_back_on_validation_failure(store_file: Path) -> None:
    with pytest.raises(RenameError):
        bulk_rename(store_file, PASS, {"FOO": "FOO_OK", "MISSING": "X"})
    # Store should be unchanged
    reloaded = load_store(store_file, PASS)
    assert "FOO" in reloaded
    assert "FOO_OK" not in reloaded
