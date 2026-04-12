"""Unit tests for envoy.alias."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.alias import (
    AliasError,
    _alias_path,
    add_alias,
    list_aliases,
    remove_alias,
    resolve_alias,
)

KNOWN = ["DATABASE_URL", "SECRET_KEY", "DEBUG"]


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    p = tmp_path / ".envoy"
    p.write_text("{}")
    return p


def test_add_alias_returns_mapping(store_file: Path) -> None:
    result = add_alias(store_file, "db", "DATABASE_URL", KNOWN)
    assert result["db"] == "DATABASE_URL"


def test_add_alias_persists_file(store_file: Path) -> None:
    add_alias(store_file, "db", "DATABASE_URL", KNOWN)
    raw = json.loads(_alias_path(store_file).read_text())
    assert raw["db"] == "DATABASE_URL"


def test_add_alias_multiple(store_file: Path) -> None:
    add_alias(store_file, "db", "DATABASE_URL", KNOWN)
    add_alias(store_file, "sk", "SECRET_KEY", KNOWN)
    aliases = list_aliases(store_file)
    assert len(aliases) == 2


def test_add_alias_unknown_key_raises(store_file: Path) -> None:
    with pytest.raises(AliasError, match="not found in store"):
        add_alias(store_file, "x", "NONEXISTENT", KNOWN)


def test_add_alias_invalid_identifier_raises(store_file: Path) -> None:
    with pytest.raises(AliasError, match="not a valid identifier"):
        add_alias(store_file, "my-alias", "DATABASE_URL", KNOWN)


def test_remove_alias_deletes_entry(store_file: Path) -> None:
    add_alias(store_file, "db", "DATABASE_URL", KNOWN)
    remove_alias(store_file, "db")
    assert "db" not in list_aliases(store_file)


def test_remove_alias_missing_raises(store_file: Path) -> None:
    with pytest.raises(AliasError, match="not found"):
        remove_alias(store_file, "ghost")


def test_list_aliases_empty_when_no_file(store_file: Path) -> None:
    assert list_aliases(store_file) == {}


def test_resolve_alias_returns_key(store_file: Path) -> None:
    add_alias(store_file, "sk", "SECRET_KEY", KNOWN)
    assert resolve_alias(store_file, "sk") == "SECRET_KEY"


def test_resolve_alias_missing_returns_none(store_file: Path) -> None:
    assert resolve_alias(store_file, "nope") is None
