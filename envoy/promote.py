"""Promote environment variables from one profile to another with optional filtering."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envoy.sync import pull_profile, push_profile, list_profiles
from envoy.store import load_store, save_store, get_env_vars
from envoy.merge import merge_dicts, MergeStrategy


class PromoteError(Exception):
    """Raised when a promotion operation fails."""


def promote_profile(
    src_profile: str,
    dst_profile: str,
    passphrase: str,
    store_path: Path,
    profiles_dir: Path,
    strategy: MergeStrategy = MergeStrategy.KEEP_TARGET,
    keys: Optional[list[str]] = None,
) -> dict[str, str]:
    """Promote variables from *src_profile* into *dst_profile*.

    Args:
        src_profile: Name of the source profile to read from.
        dst_profile: Name of the destination profile to merge into.
        passphrase: Encryption passphrase shared across profiles.
        store_path: Path to the local store file (used as scratch space).
        profiles_dir: Directory where profiles are persisted.
        strategy: Conflict resolution strategy when a key exists in both profiles.
        keys: Optional allowlist of variable keys to promote. Promotes all if None.

    Returns:
        The merged variable mapping written to *dst_profile*.

    Raises:
        PromoteError: If either profile does not exist or promotion fails.
    """
    available = list_profiles(profiles_dir)
    if src_profile not in available:
        raise PromoteError(f"Source profile '{src_profile}' not found.")

    # Load source vars
    pull_profile(src_profile, passphrase, store_path, profiles_dir)
    src_vars = get_env_vars(passphrase, store_path)

    if keys is not None:
        missing = [k for k in keys if k not in src_vars]
        if missing:
            raise PromoteError(
                f"Keys not found in source profile: {', '.join(missing)}"
            )
        src_vars = {k: src_vars[k] for k in keys}

    # Load destination vars (may not exist yet)
    dst_vars: dict[str, str] = {}
    if dst_profile in available:
        pull_profile(dst_profile, passphrase, store_path, profiles_dir)
        dst_vars = get_env_vars(passphrase, store_path)

    merged = merge_dicts(src_vars, dst_vars, strategy=strategy)

    # Persist merged result as dst_profile
    store = load_store(passphrase, store_path)
    store["vars"] = merged
    save_store(store, passphrase, store_path)
    push_profile(dst_profile, passphrase, store_path, profiles_dir)

    return merged
