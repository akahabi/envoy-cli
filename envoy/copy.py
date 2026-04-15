"""Copy environment variables between stores and profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envoy.store import load_store, save_store, set_env_var
from envoy.sync import push_profile, pull_profile


class CopyError(Exception):
    """Raised when a copy operation fails."""


def copy_vars(
    src_path: Path,
    dst_path: Path,
    src_passphrase: str,
    dst_passphrase: str,
    keys: Optional[list[str]] = None,
    overwrite: bool = True,
) -> dict[str, str]:
    """Copy variables from one store file to another.

    Args:
        src_path: Path to the source encrypted store.
        dst_path: Path to the destination encrypted store.
        src_passphrase: Passphrase for the source store.
        dst_passphrase: Passphrase for the destination store.
        keys: Optional list of specific keys to copy. Copies all if None.
        overwrite: If False, skip keys that already exist in destination.

    Returns:
        Dict of key/value pairs that were copied.

    Raises:
        CopyError: If source store is missing or a key is not found.
    """
    if not src_path.exists():
        raise CopyError(f"Source store not found: {src_path}")

    src_vars = load_store(src_path, src_passphrase)

    if keys is not None:
        missing = [k for k in keys if k not in src_vars]
        if missing:
            raise CopyError(f"Keys not found in source: {', '.join(missing)}")
        to_copy = {k: src_vars[k] for k in keys}
    else:
        to_copy = dict(src_vars)

    dst_vars = load_store(dst_path, dst_passphrase) if dst_path.exists() else {}

    copied: dict[str, str] = {}
    for key, value in to_copy.items():
        if not overwrite and key in dst_vars:
            continue
        dst_vars[key] = value
        copied[key] = value

    save_store(dst_path, dst_passphrase, dst_vars)
    return copied


def copy_key(
    src_path: Path,
    dst_path: Path,
    key: str,
    src_passphrase: str,
    dst_passphrase: str,
    new_key: Optional[str] = None,
) -> tuple[str, str]:
    """Copy a single key, optionally renaming it in the destination.

    Returns:
        Tuple of (destination_key, value) that was written.

    Raises:
        CopyError: If the key does not exist in the source.
    """
    if not src_path.exists():
        raise CopyError(f"Source store not found: {src_path}")

    src_vars = load_store(src_path, src_passphrase)
    if key not in src_vars:
        raise CopyError(f"Key '{key}' not found in source store")

    value = src_vars[key]
    dest_key = new_key or key

    dst_vars = load_store(dst_path, dst_passphrase) if dst_path.exists() else {}
    dst_vars[dest_key] = value
    save_store(dst_path, dst_passphrase, dst_vars)

    return dest_key, value
