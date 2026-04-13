"""Tests for envoy/ttl.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envoy.store import save_store
from envoy.ttl import (
    TTLError,
    _ttl_path,
    expired_keys,
    list_ttls,
    remove_ttl,
    set_ttl,
)

PASSPHRASE = "test-secret"


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    p = tmp_path / ".envoy"
    save_store(p, PASSPHRASE, {"API_KEY": "abc123", "DB_PASS": "hunter2"})
    return p


def test_set_ttl_returns_entry(store_file: Path):
    entry = set_ttl(store_file, PASSPHRASE, "API_KEY", 3600)
    assert "expires_at" in entry


def test_set_ttl_persists_file(store_file: Path):
    set_ttl(store_file, PASSPHRASE, "API_KEY", 60)
    data = json.loads(_ttl_path(store_file).read_text())
    assert "API_KEY" in data


def test_set_ttl_unknown_key_raises(store_file: Path):
    with pytest.raises(TTLError, match="not found"):
        set_ttl(store_file, PASSPHRASE, "MISSING_KEY", 60)


def test_set_ttl_zero_seconds_raises(store_file: Path):
    with pytest.raises(TTLError, match="positive"):
        set_ttl(store_file, PASSPHRASE, "API_KEY", 0)


def test_remove_ttl_clears_entry(store_file: Path):
    set_ttl(store_file, PASSPHRASE, "API_KEY", 60)
    remove_ttl(store_file, "API_KEY")
    data = list_ttls(store_file)
    assert "API_KEY" not in data


def test_remove_ttl_nonexistent_is_noop(store_file: Path):
    remove_ttl(store_file, "DOES_NOT_EXIST")  # should not raise


def test_list_ttls_empty_when_no_file(store_file: Path):
    assert list_ttls(store_file) == {}


def test_list_ttls_returns_all_entries(store_file: Path):
    set_ttl(store_file, PASSPHRASE, "API_KEY", 60)
    set_ttl(store_file, PASSPHRASE, "DB_PASS", 120)
    entries = list_ttls(store_file)
    assert set(entries.keys()) == {"API_KEY", "DB_PASS"}


def test_expired_keys_detects_past_expiry(store_file: Path):
    set_ttl(store_file, PASSPHRASE, "API_KEY", 60)
    # Manually backdate the expiry
    ttl_file = _ttl_path(store_file)
    data = json.loads(ttl_file.read_text())
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    data["API_KEY"]["expires_at"] = past
    ttl_file.write_text(json.dumps(data))
    assert "API_KEY" in expired_keys(store_file)


def test_expired_keys_ignores_future_expiry(store_file: Path):
    set_ttl(store_file, PASSPHRASE, "API_KEY", 3600)
    assert expired_keys(store_file) == []
