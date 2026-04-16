"""Tests for envoy.namespace."""
from __future__ import annotations

from pathlib import Path

import pytest

from envoy.namespace import NamespaceError, delete_namespace, get_namespace, list_namespaces, set_namespace_var
from envoy.store import save_store

PASS = "test-pass"


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    p = tmp_path / "store.env"
    save_store(p, {"DB__HOST": "localhost", "DB__PORT": "5432", "APP__DEBUG": "true", "PLAIN": "value"}, PASS)
    return p


def test_list_namespaces(store_file: Path) -> None:
    ns = list_namespaces(store_file)
    assert ns == ["APP", "DB"]


def test_list_namespaces_ignores_plain_keys(store_file: Path) -> None:
    ns = list_namespaces(store_file)
    assert "PLAIN" not in ns


def test_list_namespaces_empty_store(tmp_path: Path) -> None:
    p = tmp_path / "store.env"
    save_store(p, {}, PASS)
    assert list_namespaces(p) == []


def test_get_namespace_strips_prefix(store_file: Path) -> None:
    vars_ = get_namespace(store_file, "DB")
    assert vars_ == {"HOST": "localhost", "PORT": "5432"}


def test_get_namespace_returns_empty_for_unknown(store_file: Path) -> None:
    vars_ = get_namespace(store_file, "UNKNOWN")
    assert vars_ == {}


def test_set_namespace_var_returns_full_key(store_file: Path) -> None:
    full_key = set_namespace_var(store_file, "DB", "NAME", "mydb", PASS)
    assert full_key == "DB__NAME"


def test_set_namespace_var_persists(store_file: Path) -> None:
    set_namespace_var(store_file, "DB", "NAME", "mydb", PASS)
    vars_ = get_namespace(store_file, "DB")
    assert vars_["NAME"] == "mydb"


def test_set_namespace_var_invalid_namespace(store_file: Path) -> None:
    with pytest.raises(NamespaceError, match="namespace"):
        set_namespace_var(store_file, "bad-ns", "KEY", "val", PASS)


def test_set_namespace_var_invalid_key(store_file: Path) -> None:
    with pytest.raises(NamespaceError, match="key"):
        set_namespace_var(store_file, "DB", "bad-key", "val", PASS)


def test_delete_namespace_removes_all_vars(store_file: Path) -> None:
    deleted = delete_namespace(store_file, "DB", PASS)
    assert set(deleted) == {"DB__HOST", "DB__PORT"}
    assert get_namespace(store_file, "DB") == {}


def test_delete_namespace_leaves_other_namespaces(store_file: Path) -> None:
    delete_namespace(store_file, "DB", PASS)
    assert get_namespace(store_file, "APP") == {"DEBUG": "true"}


def test_delete_namespace_unknown_raises(store_file: Path) -> None:
    with pytest.raises(NamespaceError, match="not found"):
        delete_namespace(store_file, "GHOST", PASS)
