"""Tests for envoy.compare module."""

import pytest
from pathlib import Path

from envoy.store import save_store
from envoy.compare import compare_store_to_profile, compare_profiles, CompareError
from envoy.diff import has_differences


PASS_A = "passA"
PASS_B = "passB"


@pytest.fixture()
def store_file(tmp_path):
    path = tmp_path / ".envoy"
    save_store(path, {"KEY1": "val1", "KEY2": "val2"}, PASS_A)
    return path


@pytest.fixture()
def profiles_dir(tmp_path):
    d = tmp_path / "profiles"
    d.mkdir()
    return d


def _make_profile(profiles_dir, name, vars_, passphrase):
    path = profiles_dir / f"{name}.envoy"
    save_store(path, vars_, passphrase)
    return path


def test_compare_store_to_profile_no_diff(store_file, profiles_dir):
    _make_profile(profiles_dir, "staging", {"KEY1": "val1", "KEY2": "val2"}, PASS_B)
    result = compare_store_to_profile(store_file, "staging", PASS_A, PASS_B, profiles_dir)
    assert not has_differences(result)


def test_compare_store_to_profile_detects_changes(store_file, profiles_dir):
    _make_profile(profiles_dir, "staging", {"KEY1": "different", "KEY2": "val2"}, PASS_B)
    result = compare_store_to_profile(store_file, "staging", PASS_A, PASS_B, profiles_dir)
    assert has_differences(result)
    statuses = {r.key: r.status for r in result}
    assert statuses["KEY1"] == "changed"
    assert statuses["KEY2"] == "unchanged"


def test_compare_store_missing_raises(tmp_path, profiles_dir):
    _make_profile(profiles_dir, "staging", {}, PASS_B)
    with pytest.raises(CompareError, match="Store file not found"):
        compare_store_to_profile(tmp_path / "missing", "staging", PASS_A, PASS_B, profiles_dir)


def test_compare_store_to_missing_profile_raises(store_file, profiles_dir):
    with pytest.raises(CompareError, match="not found"):
        compare_store_to_profile(store_file, "ghost", PASS_A, PASS_B, profiles_dir)


def test_compare_profiles_identical(profiles_dir):
    _make_profile(profiles_dir, "staging", {"A": "1"}, PASS_A)
    _make_profile(profiles_dir, "prod", {"A": "1"}, PASS_B)
    result = compare_profiles("staging", "prod", PASS_A, PASS_B, profiles_dir)
    assert not has_differences(result)


def test_compare_profiles_detects_added_key(profiles_dir):
    _make_profile(profiles_dir, "staging", {"A": "1"}, PASS_A)
    _make_profile(profiles_dir, "prod", {"A": "1", "B": "2"}, PASS_B)
    result = compare_profiles("staging", "prod", PASS_A, PASS_B, profiles_dir)
    statuses = {r.key: r.status for r in result}
    assert statuses["B"] == "added"


def test_compare_profiles_missing_raises(profiles_dir):
    _make_profile(profiles_dir, "staging", {}, PASS_A)
    with pytest.raises(CompareError, match="not found"):
        compare_profiles("staging", "ghost", PASS_A, PASS_B, profiles_dir)
