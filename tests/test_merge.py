"""Tests for envoy.merge."""

import json
import os
import pytest

from envoy.merge import (
    MergeConflict,
    MergeError,
    MergeStrategy,
    merge_dicts,
    merge_store_from_profile,
)
from envoy.store import save_store
from envoy.sync import push_profile


# ---------------------------------------------------------------------------
# merge_dicts
# ---------------------------------------------------------------------------

def test_merge_adds_new_keys_from_source():
    result = merge_dicts({"A": "1", "B": "2"}, {"A": "1"})
    assert result.merged["B"] == "2"
    assert "B" in result.added


def test_merge_keep_target_on_conflict():
    result = merge_dicts(
        {"KEY": "source_val"},
        {"KEY": "target_val"},
        strategy=MergeStrategy.KEEP_TARGET,
    )
    assert result.merged["KEY"] == "target_val"
    assert len(result.conflicts) == 1
    assert result.conflicts[0] == MergeConflict("KEY", "source_val", "target_val")


def test_merge_keep_source_on_conflict():
    result = merge_dicts(
        {"KEY": "source_val"},
        {"KEY": "target_val"},
        strategy=MergeStrategy.KEEP_SOURCE,
    )
    assert result.merged["KEY"] == "source_val"


def test_merge_raise_strategy_raises_on_conflict():
    with pytest.raises(MergeError, match="KEY"):
        merge_dicts(
            {"KEY": "source_val"},
            {"KEY": "target_val"},
            strategy=MergeStrategy.RAISE,
        )


def test_merge_no_conflict_identical_values():
    result = merge_dicts({"KEY": "same"}, {"KEY": "same"})
    assert result.conflicts == []
    assert result.added == []
    assert result.merged["KEY"] == "same"


def test_merge_empty_source():
    result = merge_dicts({}, {"A": "1"})
    assert result.merged == {"A": "1"}
    assert result.added == []
    assert result.conflicts == []


def test_merge_empty_target():
    result = merge_dicts({"A": "1"}, {})
    assert result.merged == {"A": "1"}
    assert result.added == ["A"]


# ---------------------------------------------------------------------------
# merge_store_from_profile  (integration)
# ---------------------------------------------------------------------------

@pytest.fixture()
def store_file(tmp_path):
    return str(tmp_path / "store.enc")


@pytest.fixture()
def profiles_dir(tmp_path):
    d = tmp_path / "profiles"
    d.mkdir()
    return str(d)


def test_merge_store_from_profile_adds_missing_keys(store_file, profiles_dir):
    passphrase = "secret"
    save_store(store_file, passphrase, {"EXISTING": "yes"})
    push_profile(store_file, passphrase, "staging", profiles_dir)
    # modify store so profile has an extra key the store lacks
    save_store(store_file, passphrase, {"EXISTING": "yes", "EXTRA": "from_profile"})
    push_profile(store_file, passphrase, "staging", profiles_dir)
    # reset store to not have EXTRA
    save_store(store_file, passphrase, {"EXISTING": "yes"})

    result = merge_store_from_profile(
        store_file, passphrase, "staging", profiles_dir,
        strategy=MergeStrategy.KEEP_TARGET,
    )
    assert "EXTRA" in result.merged
    assert "EXTRA" in result.added


def test_merge_store_from_profile_respects_keep_source(store_file, profiles_dir):
    passphrase = "secret"
    save_store(store_file, passphrase, {"KEY": "profile_value"})
    push_profile(store_file, passphrase, "prod", profiles_dir)
    save_store(store_file, passphrase, {"KEY": "local_value"})

    result = merge_store_from_profile(
        store_file, passphrase, "prod", profiles_dir,
        strategy=MergeStrategy.KEEP_SOURCE,
    )
    assert result.merged["KEY"] == "profile_value"
