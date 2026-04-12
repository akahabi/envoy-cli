"""Alias management: map short names to env var keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class AliasError(Exception):
    """Raised on alias operation failures."""


def _alias_path(store_path: Path) -> Path:
    return store_path.parent / (store_path.stem + ".aliases.json")


def _load_raw(store_path: Path) -> Dict[str, str]:
    path = _alias_path(store_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_raw(store_path: Path, data: Dict[str, str]) -> None:
    _alias_path(store_path).write_text(json.dumps(data, indent=2))


def add_alias(store_path: Path, alias: str, key: str, known_keys: List[str]) -> Dict[str, str]:
    """Register *alias* as a shorthand for *key*. *key* must exist in *known_keys*."""
    if key not in known_keys:
        raise AliasError(f"Key '{key}' not found in store.")
    if not alias.isidentifier():
        raise AliasError(f"Alias '{alias}' is not a valid identifier.")
    data = _load_raw(store_path)
    data[alias] = key
    _save_raw(store_path, data)
    return data


def remove_alias(store_path: Path, alias: str) -> Dict[str, str]:
    """Remove *alias*. Raises AliasError if it does not exist."""
    data = _load_raw(store_path)
    if alias not in data:
        raise AliasError(f"Alias '{alias}' not found.")
    del data[alias]
    _save_raw(store_path, data)
    return data


def list_aliases(store_path: Path) -> Dict[str, str]:
    """Return all aliases as {alias: key}."""
    return _load_raw(store_path)


def resolve_alias(store_path: Path, alias: str) -> Optional[str]:
    """Return the key for *alias*, or None if not registered."""
    return _load_raw(store_path).get(alias)
