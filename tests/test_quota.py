"""Tests for envoy.quota."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.quota import (
    DEFAULT_QUOTA,
    QuotaError,
    check_quota,
    get_quota,
    remove_quota,
    set_quota,
)


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.env.json"
    p.write_text(json.dumps({"vars": {}}))
    return p


def test_set_quota_returns_mapping(store_file: Path) -> None:
    rules = set_quota(store_file, 50)
    assert rules["__global__"] == 50


def test_set_quota_persists_file(store_file: Path) -> None:
    set_quota(store_file, 25)
    quota_path = store_file.parent / (store_file.stem + ".quota.json")
    data = json.loads(quota_path.read_text())
    assert data["__global__"] == 25


def test_set_quota_namespace(store_file: Path) -> None:
    rules = set_quota(store_file, 10, namespace="prod")
    assert rules["prod"] == 10


def test_set_quota_zero_raises(store_file: Path) -> None:
    with pytest.raises(QuotaError):
        set_quota(store_file, 0)


def test_set_quota_negative_raises(store_file: Path) -> None:
    with pytest.raises(QuotaError):
        set_quota(store_file, -5)


def test_get_quota_default_when_no_file(store_file: Path) -> None:
    assert get_quota(store_file) == DEFAULT_QUOTA


def test_get_quota_returns_set_value(store_file: Path) -> None:
    set_quota(store_file, 42)
    assert get_quota(store_file) == 42


def test_get_quota_namespace_falls_back_to_default(store_file: Path) -> None:
    assert get_quota(store_file, namespace="staging") == DEFAULT_QUOTA


def test_remove_quota_clears_rule(store_file: Path) -> None:
    set_quota(store_file, 10)
    remove_quota(store_file)
    assert get_quota(store_file) == DEFAULT_QUOTA


def test_remove_quota_idempotent(store_file: Path) -> None:
    # Should not raise even when no rule exists
    remove_quota(store_file)
    remove_quota(store_file)


def test_check_quota_within_limit(store_file: Path) -> None:
    set_quota(store_file, 5)
    vars_ = {f"KEY_{i}": str(i) for i in range(3)}
    check_quota(store_file, vars_)  # should not raise


def test_check_quota_at_limit(store_file: Path) -> None:
    set_quota(store_file, 3)
    vars_ = {f"KEY_{i}": str(i) for i in range(3)}
    check_quota(store_file, vars_)  # exactly at limit — OK


def test_check_quota_exceeds_limit_raises(store_file: Path) -> None:
    set_quota(store_file, 2)
    vars_ = {f"KEY_{i}": str(i) for i in range(5)}
    with pytest.raises(QuotaError, match="Quota exceeded"):
        check_quota(store_file, vars_)


def test_check_quota_namespace_counts_only_prefixed_keys(store_file: Path) -> None:
    set_quota(store_file, 2, namespace="ns")
    vars_ = {"ns:A": "1", "ns:B": "2", "OTHER": "x", "ANOTHER": "y"}
    check_quota(store_file, vars_, namespace="ns")  # 2 ns keys — OK


def test_check_quota_namespace_raises_when_exceeded(store_file: Path) -> None:
    set_quota(store_file, 1, namespace="ns")
    vars_ = {"ns:A": "1", "ns:B": "2"}
    with pytest.raises(QuotaError, match="namespace 'ns'"):
        check_quota(store_file, vars_, namespace="ns")
