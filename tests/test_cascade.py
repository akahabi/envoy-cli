"""Tests for envoy.cascade."""

from __future__ import annotations

import pytest

from envoy.cascade import CascadeError, cascade
from envoy.store import save_store
from envoy.sync import push_profile


@pytest.fixture()
def store_file(tmp_path):
    return str(tmp_path / ".envoy")


@pytest.fixture()
def profiles_dir(tmp_path):
    d = tmp_path / "profiles"
    d.mkdir()
    return str(d)


PASS = "secret"


def _seed_store(path, vars_):
    save_store(path, PASS, vars_)


def _seed_profile(profiles_dir, name, vars_, store_file):
    save_store(store_file, PASS, vars_)
    push_profile(profiles_dir, name, store_file, PASS)


def test_cascade_single_profile(store_file, profiles_dir):
    _seed_profile(profiles_dir, "staging", {"A": "1", "B": "2"}, store_file)
    result = cascade(store_file, PASS, ["staging"], profiles_dir, base_store=False)
    assert result.merged == {"A": "1", "B": "2"}
    assert result.layers == ["staging"]


def test_cascade_later_profile_wins(store_file, profiles_dir):
    _seed_profile(profiles_dir, "base", {"A": "base", "B": "base"}, store_file)
    _seed_profile(profiles_dir, "prod", {"B": "prod", "C": "prod"}, store_file)
    result = cascade(store_file, PASS, ["base", "prod"], profiles_dir, base_store=False)
    assert result.merged["A"] == "base"
    assert result.merged["B"] == "prod"
    assert result.merged["C"] == "prod"


def test_cascade_base_store_is_lowest_priority(store_file, profiles_dir):
    _seed_store(store_file, {"X": "local"})
    _seed_profile(profiles_dir, "override", {"X": "remote"}, store_file)
    # restore local store after profile seed
    _seed_store(store_file, {"X": "local"})
    result = cascade(store_file, PASS, ["override"], profiles_dir, base_store=True)
    assert result.merged["X"] == "remote"
    assert result.origin("X") == "override"


def test_cascade_base_store_provides_keys_not_in_profiles(store_file, profiles_dir):
    _seed_store(store_file, {"LOCAL_ONLY": "yes", "SHARED": "local"})
    _seed_profile(profiles_dir, "p", {"SHARED": "profile"}, store_file)
    _seed_store(store_file, {"LOCAL_ONLY": "yes", "SHARED": "local"})
    result = cascade(store_file, PASS, ["p"], profiles_dir, base_store=True)
    assert result.merged["LOCAL_ONLY"] == "yes"
    assert result.origin("LOCAL_ONLY") == "__local__"


def test_cascade_missing_profile_raises(store_file, profiles_dir):
    with pytest.raises(CascadeError, match="not found"):
        cascade(store_file, PASS, ["nonexistent"], profiles_dir, base_store=False)


def test_cascade_no_profiles_raises(store_file, profiles_dir):
    with pytest.raises(CascadeError):
        cascade(store_file, PASS, [], profiles_dir)


def test_cascade_layers_order_recorded(store_file, profiles_dir):
    _seed_profile(profiles_dir, "a", {"K": "a"}, store_file)
    _seed_profile(profiles_dir, "b", {"K": "b"}, store_file)
    result = cascade(store_file, PASS, ["a", "b"], profiles_dir, base_store=False)
    assert result.layers == ["a", "b"]


def test_cascade_summary_contains_layer_info(store_file, profiles_dir):
    _seed_profile(profiles_dir, "staging", {"PORT": "8080"}, store_file)
    result = cascade(store_file, PASS, ["staging"], profiles_dir, base_store=False)
    summary = result.summary()
    assert "staging" in summary
    assert "PORT" in summary
