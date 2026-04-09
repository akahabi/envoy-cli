"""Key rotation: re-encrypt a store with a new passphrase."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envoy.store import load_store, save_store
from envoy.audit import record_event


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate_store(
    store_path: Path,
    old_passphrase: str,
    new_passphrase: str,
    profile: Optional[str] = None,
) -> dict:
    """Re-encrypt *store_path* with *new_passphrase*.

    Loads the store using *old_passphrase*, then saves it again using
    *new_passphrase*.  Returns the decrypted variable mapping so callers
    can verify the result.

    Raises ``RotationError`` if the store cannot be decrypted with the
    supplied old passphrase.
    """
    try:
        vars_ = load_store(store_path, old_passphrase)
    except Exception as exc:  # covers wrong passphrase / corrupt file
        raise RotationError(f"Could not decrypt store: {exc}") from exc

    try:
        save_store(store_path, vars_, new_passphrase)
    except Exception as exc:
        raise RotationError(f"Could not save re-encrypted store: {exc}") from exc

    record_event(
        action="rotate",
        key="*",
        profile=profile,
        detail={"store": str(store_path)},
    )

    return vars_


def rotate_profile(
    profiles_dir: Path,
    profile: str,
    old_passphrase: str,
    new_passphrase: str,
) -> dict:
    """Rotate the passphrase for a named sync profile."""
    profile_path = profiles_dir / f"{profile}.enc"
    if not profile_path.exists():
        raise RotationError(f"Profile '{profile}' not found.")
    return rotate_store(profile_path, old_passphrase, new_passphrase, profile=profile)
