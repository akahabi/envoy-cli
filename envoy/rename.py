"""Rename a variable key within a store, preserving its value and metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from envoy.store import load_store, save_store


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


def rename_var(
    store_path: Path,
    passphrase: str,
    old_key: str,
    new_key: str,
    *,
    overwrite: bool = False,
) -> Dict[str, str]:
    """Rename *old_key* to *new_key* in the store at *store_path*.

    Returns the full vars dict after renaming.

    Raises:
        RenameError: if old_key does not exist, new_key already exists
            (unless *overwrite* is True), or the keys are identical.
    """
    if old_key == new_key:
        raise RenameError(f"Old and new key are identical: '{old_key}'")

    vars_: Dict[str, str] = load_store(store_path, passphrase)

    if old_key not in vars_:
        raise RenameError(f"Key not found: '{old_key}'")

    if new_key in vars_ and not overwrite:
        raise RenameError(
            f"Key '{new_key}' already exists. Use --overwrite to replace it."
        )

    value = vars_.pop(old_key)
    vars_[new_key] = value

    save_store(store_path, passphrase, vars_)
    return vars_


def bulk_rename(
    store_path: Path,
    passphrase: str,
    mapping: Dict[str, str],
    *,
    overwrite: bool = False,
) -> Dict[str, str]:
    """Rename multiple keys at once using *mapping* {old: new}.

    All renames are validated before any mutation is applied.
    """
    vars_: Dict[str, str] = load_store(store_path, passphrase)

    # Validate first
    for old_key, new_key in mapping.items():
        if old_key == new_key:
            raise RenameError(f"Old and new key are identical: '{old_key}'")
        if old_key not in vars_:
            raise RenameError(f"Key not found: '{old_key}'")
        if new_key in vars_ and new_key not in mapping and not overwrite:
            raise RenameError(
                f"Key '{new_key}' already exists. Use --overwrite to replace it."
            )

    # Apply
    for old_key, new_key in mapping.items():
        vars_[new_key] = vars_.pop(old_key)

    save_store(store_path, passphrase, vars_)
    return vars_
