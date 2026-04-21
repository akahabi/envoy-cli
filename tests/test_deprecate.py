"""Tests for envoy.deprecate."""
import json
from datetime import date, timedelta

import pytest

from envoy.deprecate import (
    DeprecateError,
    check_sunset,
    deprecate_var,
    list_deprecated,
    undeprecate_var,
)
from envoy.store import save_store


@pytest.fixture()
def store_file(tmp_path):
    p = tmp_path / "test.store"
    save_store(str(p), "secret", {"OLD_KEY": "foo", "KEEP": "bar"})
    return str(p)


def test_deprecate_var_returns_entry(store_file):
    entry = deprecate_var(store_file, "secret", "OLD_KEY", reason="use NEW_KEY")
    assert entry["reason"] == "use NEW_KEY"
    assert entry["deprecated_on"] == date.today().isoformat()


def test_deprecate_var_persists_file(store_file):
    deprecate_var(store_file, "secret", "OLD_KEY", reason="obsolete")
    data = list_deprecated(store_file)
    assert "OLD_KEY" in data


def test_deprecate_var_with_replacement(store_file):
    entry = deprecate_var(
        store_file, "secret", "OLD_KEY", reason="use NEW_KEY", replacement="NEW_KEY"
    )
    assert entry["replacement"] == "NEW_KEY"


def test_deprecate_var_with_sunset(store_file):
    entry = deprecate_var(
        store_file, "secret", "OLD_KEY", reason="going away", sunset="2099-01-01"
    )
    assert entry["sunset"] == "2099-01-01"


def test_deprecate_var_invalid_sunset_raises(store_file):
    with pytest.raises(DeprecateError, match="YYYY-MM-DD"):
        deprecate_var(store_file, "secret", "OLD_KEY", reason="x", sunset="01-01-2099")


def test_deprecate_var_unknown_key_raises(store_file):
    with pytest.raises(DeprecateError, match="MISSING"):
        deprecate_var(store_file, "secret", "MISSING", reason="nope")


def test_undeprecate_var_removes_entry(store_file):
    deprecate_var(store_file, "secret", "OLD_KEY", reason="old")
    undeprecate_var(store_file, "OLD_KEY")
    assert "OLD_KEY" not in list_deprecated(store_file)


def test_undeprecate_var_missing_raises(store_file):
    with pytest.raises(DeprecateError):
        undeprecate_var(store_file, "OLD_KEY")


def test_list_deprecated_empty_when_no_file(store_file):
    assert list_deprecated(store_file) == {}


def test_list_deprecated_returns_all(store_file):
    deprecate_var(store_file, "secret", "OLD_KEY", reason="r1")
    deprecate_var(store_file, "secret", "KEEP", reason="r2")
    data = list_deprecated(store_file)
    assert set(data.keys()) == {"OLD_KEY", "KEEP"}


def test_check_sunset_returns_expired(store_file):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    deprecate_var(store_file, "secret", "OLD_KEY", reason="old", sunset=yesterday)
    expired = check_sunset(store_file)
    assert any(e["key"] == "OLD_KEY" for e in expired)


def test_check_sunset_excludes_future(store_file):
    deprecate_var(
        store_file, "secret", "OLD_KEY", reason="old", sunset="2099-12-31"
    )
    assert check_sunset(store_file) == []
