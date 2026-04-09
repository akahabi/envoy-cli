"""Tests for envoy.diff module."""

import pytest
from envoy.diff import diff_vars, DiffResult


SOURCE = {"KEY_A": "alpha", "KEY_B": "beta", "KEY_C": "shared"}
TARGET = {"KEY_B": "bravo", "KEY_C": "shared", "KEY_D": "delta"}


def test_diff_only_in_source():
    result = diff_vars(SOURCE, TARGET)
    assert "KEY_A" in result.only_in_source
    assert result.only_in_source["KEY_A"] == "alpha"


def test_diff_only_in_target():
    result = diff_vars(SOURCE, TARGET)
    assert "KEY_D" in result.only_in_target
    assert result.only_in_target["KEY_D"] == "delta"


def test_diff_changed_values():
    result = diff_vars(SOURCE, TARGET)
    assert "KEY_B" in result.changed
    src_val, tgt_val = result.changed["KEY_B"]
    assert src_val == "beta"
    assert tgt_val == "bravo"


def test_diff_unchanged_keys():
    result = diff_vars(SOURCE, TARGET)
    assert "KEY_C" in result.unchanged


def test_diff_identical_dicts():
    data = {"X": "1", "Y": "2"}
    result = diff_vars(data, data.copy())
    assert not result.has_differences
    assert result.unchanged == sorted(["X", "Y"]) or set(result.unchanged) == {"X", "Y"}


def test_diff_empty_source():
    result = diff_vars({}, {"A": "1"})
    assert "A" in result.only_in_target
    assert not result.only_in_source
    assert not result.changed


def test_diff_empty_target():
    result = diff_vars({"A": "1"}, {})
    assert "A" in result.only_in_source
    assert not result.only_in_target


def test_has_differences_true():
    result = diff_vars(SOURCE, TARGET)
    assert result.has_differences is True


def test_has_differences_false():
    data = {"K": "v"}
    result = diff_vars(data, data.copy())
    assert result.has_differences is False


def test_summary_contains_markers():
    result = diff_vars(SOURCE, TARGET)
    summary = result.summary()
    assert "+" in summary   # only_in_source
    assert "-" in summary   # only_in_target
    assert "~" in summary   # changed


def test_summary_no_differences():
    data = {"K": "v"}
    result = diff_vars(data, data.copy())
    assert "(no differences)" in result.summary()
