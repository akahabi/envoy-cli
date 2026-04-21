"""Group env vars under named logical groups for easier management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envoy.store import load_store


class GroupError(Exception):
    pass


def _group_path(store_path: str) -> Path:
    p = Path(store_path)
    return p.parent / (p.stem + ".groups.json")


def _load_raw(store_path: str) -> Dict[str, List[str]]:
    path = _group_path(store_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_raw(store_path: str, data: Dict[str, List[str]]) -> None:
    _group_path(store_path).write_text(json.dumps(data, indent=2))


def add_group(store_path: str, group: str, keys: List[str], passphrase: str) -> Dict[str, List[str]]:
    """Create or extend a group with the given keys (must exist in store)."""
    existing = load_store(store_path, passphrase)
    for key in keys:
        if key not in existing:
            raise GroupError(f"Key '{key}' not found in store")
    data = _load_raw(store_path)
    current = data.get(group, [])
    merged = list(dict.fromkeys(current + keys))  # deduplicate, preserve order
    data[group] = merged
    _save_raw(store_path, data)
    return data


def remove_group(store_path: str, group: str) -> Dict[str, List[str]]:
    """Delete a group entirely."""
    data = _load_raw(store_path)
    if group not in data:
        raise GroupError(f"Group '{group}' does not exist")
    del data[group]
    _save_raw(store_path, data)
    return data


def remove_keys_from_group(store_path: str, group: str, keys: List[str]) -> Dict[str, List[str]]:
    """Remove specific keys from a group without deleting the group itself.

    Raises GroupError if the group does not exist or if any key is not
    currently a member of the group.
    """
    data = _load_raw(store_path)
    if group not in data:
        raise GroupError(f"Group '{group}' does not exist")
    current = data[group]
    missing = [k for k in keys if k not in current]
    if missing:
        raise GroupError(f"Keys not in group '{group}': {', '.join(missing)}")
    data[group] = [k for k in current if k not in keys]
    _save_raw(store_path, data)
    return data


def list_groups(store_path: str) -> Dict[str, List[str]]:
    """Return all groups and their key lists."""
    return _load_raw(store_path)


def get_group_vars(store_path: str, group: str, passphrase: str) -> Dict[str, str]:
    """Return the key/value pairs for all keys belonging to the group."""
    data = _load_raw(store_path)
    if group not in data:
        raise GroupError(f"Group '{group}' does not exist")
    all_vars = load_store(store_path, passphrase)
    return {k: all_vars[k] for k in data[group] if k in all_vars}
