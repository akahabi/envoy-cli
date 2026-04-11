"""Tag management for env vars — assign, remove, and filter by tags."""

from __future__ import annotations

from typing import Dict, List, Set

from envoy.store import load_store, save_store


class TagError(Exception):
    """Raised when a tag operation fails."""


_TAGS_KEY = "__tags__"


def _get_tags(store: dict) -> Dict[str, List[str]]:
    """Return the tags mapping {var_name: [tag, ...]} from the store."""
    return store.get(_TAGS_KEY, {})


def add_tag(store_path: str, passphrase: str, var_name: str, tag: str) -> List[str]:
    """Add *tag* to *var_name*.  Returns the updated tag list for that var."""
    store = load_store(store_path, passphrase)
    env_vars: dict = store.get("vars", {})
    if var_name not in env_vars:
        raise TagError(f"Variable '{var_name}' not found in store.")
    tags: Dict[str, List[str]] = _get_tags(store)
    current: List[str] = tags.get(var_name, [])
    if tag not in current:
        current.append(tag)
    tags[var_name] = current
    store[_TAGS_KEY] = tags
    save_store(store_path, passphrase, store)
    return current


def remove_tag(store_path: str, passphrase: str, var_name: str, tag: str) -> List[str]:
    """Remove *tag* from *var_name*.  Returns the updated tag list."""
    store = load_store(store_path, passphrase)
    tags: Dict[str, List[str]] = _get_tags(store)
    current: List[str] = tags.get(var_name, [])
    if tag not in current:
        raise TagError(f"Tag '{tag}' not found on variable '{var_name}'.")
    current.remove(tag)
    tags[var_name] = current
    store[_TAGS_KEY] = tags
    save_store(store_path, passphrase, store)
    return current


def list_tags(store_path: str, passphrase: str, var_name: str | None = None) -> Dict[str, List[str]]:
    """Return tag mapping.  If *var_name* given, return only that var's tags."""
    store = load_store(store_path, passphrase)
    tags = _get_tags(store)
    if var_name is not None:
        return {var_name: tags.get(var_name, [])}
    return {k: v for k, v in tags.items() if v}


def filter_by_tag(store_path: str, passphrase: str, tag: str) -> Dict[str, str]:
    """Return all env vars that have *tag* assigned."""
    store = load_store(store_path, passphrase)
    env_vars: dict = store.get("vars", {})
    tags = _get_tags(store)
    return {k: v for k, v in env_vars.items() if tag in tags.get(k, [])}
