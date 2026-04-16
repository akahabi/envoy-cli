"""Namespace support: group vars under a prefix for scoped access."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from envoy.store import load_store, save_store


class NamespaceError(Exception):
    pass


def list_namespaces(store_path: Path) -> List[str]:
    """Return sorted unique namespace prefixes found in the store."""
    vars_ = load_store(store_path)
    seen: set[str] = set()
    for key in vars_:
        if "__" in key:
            ns, _, _ = key.partition("__")
            seen.add(ns)
    return sorted(seen)


def get_namespace(store_path: Path, namespace: str) -> Dict[str, str]:
    """Return vars belonging to *namespace* with the prefix stripped."""
    prefix = f"{namespace}__"
    vars_ = load_store(store_path)
    return {k[len(prefix):]: v for k, v in vars_.items() if k.startswith(prefix)}


def set_namespace_var(store_path: Path, namespace: str, key: str, value: str, passphrase: str) -> str:
    """Set a namespaced var, returning the full key written."""
    if not namespace.isidentifier():
        raise NamespaceError(f"Invalid namespace: {namespace!r}")
    if not key.isidentifier():
        raise NamespaceError(f"Invalid key: {key!r}")
    full_key = f"{namespace}__{key}"
    vars_ = load_store(store_path)
    vars_[full_key] = value
    save_store(store_path, vars_, passphrase)
    return full_key


def delete_namespace(store_path: Path, namespace: str, passphrase: str) -> List[str]:
    """Delete all vars in *namespace*, returning deleted keys."""
    prefix = f"{namespace}__"
    vars_ = load_store(store_path)
    to_delete = [k for k in vars_ if k.startswith(prefix)]
    if not to_delete:
        raise NamespaceError(f"Namespace not found: {namespace!r}")
    for k in to_delete:
        del vars_[k]
    save_store(store_path, vars_, passphrase)
    return to_delete
