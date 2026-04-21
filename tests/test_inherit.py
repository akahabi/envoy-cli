"""Tests for envoy.inherit."""
from __future__ import annotations

from pathlib import Path

import pytest

from envoy.sync import push_profile
from envoy.inherit import InheritError, resolve


PASS = "test-passphrase"


@pytest.fixture()
def profiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "profiles"
    d.mkdir()
    return d


def _seed(name: str, vars_: dict, profiles_dir: Path) -> None:
    push_profile(name, vars_, PASS, profiles_dir)


def test_resolve_single_profile(profiles_dir: Path) -> None:
    _seed("base", {"A": "1", "B": "2"}, profiles_dir)
    result = resolve(["base"], PASS, profiles_dir)
    assert result.vars == {"A": "1", "B": "2"}
    assert result.chain == ["base"]


def test_resolve_later_profile_overrides(profiles_dir: Path) -> None:
    _seed("base", {"A": "base", "B": "base"}, profiles_dir)
    _seed("prod", {"B": "prod", "C": "prod"}, profiles_dir)
    result = resolve(["base", "prod"], PASS, profiles_dir)
    assert result.vars["A"] == "base"   # only in base
    assert result.vars["B"] == "prod"   # overridden by prod
    assert result.vars["C"] == "prod"   # only in prod


def test_resolve_three_level_chain(profiles_dir: Path) -> None:
    _seed("base", {"X": "base", "Y": "base"}, profiles_dir)
    _seed("staging", {"Y": "staging", "Z": "staging"}, profiles_dir)
    _seed("prod", {"Z": "prod"}, profiles_dir)
    result = resolve(["base", "staging", "prod"], PASS, profiles_dir)
    assert result.vars["X"] == "base"
    assert result.vars["Y"] == "staging"
    assert result.vars["Z"] == "prod"
    assert result.chain == ["base", "staging", "prod"]


def test_origin_tracks_source_profile(profiles_dir: Path) -> None:
    _seed("base", {"KEY": "old"}, profiles_dir)
    _seed("override", {"KEY": "new"}, profiles_dir)
    result = resolve(["base", "override"], PASS, profiles_dir)
    assert result.origin("KEY") == "override"


def test_origin_returns_none_for_unknown_key(profiles_dir: Path) -> None:
    _seed("base", {"A": "1"}, profiles_dir)
    result = resolve(["base"], PASS, profiles_dir)
    assert result.origin("MISSING") is None


def test_missing_profile_raises(profiles_dir: Path) -> None:
    _seed("base", {"A": "1"}, profiles_dir)
    with pytest.raises(InheritError, match="ghost"):
        resolve(["base", "ghost"], PASS, profiles_dir)


def test_empty_profile_list_raises(profiles_dir: Path) -> None:
    with pytest.raises(InheritError):
        resolve([], PASS, profiles_dir)


def test_summary_contains_chain(profiles_dir: Path) -> None:
    _seed("a", {"K": "v"}, profiles_dir)
    result = resolve(["a"], PASS, profiles_dir)
    summary = result.summary()
    assert "a" in summary
    assert "K=v" in summary
