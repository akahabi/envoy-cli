"""Merge vars from one store or profile into another, with conflict resolution."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, NamedTuple

from envoy.store import load_store, save_store
from envoy.sync import pull_profile


class MergeStrategy(str, Enum):
    KEEP_TARGET = "keep-target"   # on conflict, keep target value
    KEEP_SOURCE = "keep-source"   # on conflict, overwrite with source value
    RAISE = "raise"               # on conflict, raise MergeError


class MergeError(Exception):
    """Raised when a merge conflict is encountered with RAISE strategy."""


class MergeConflict(NamedTuple):
    key: str
    source_value: str
    target_value: str


class MergeResult(NamedTuple):
    merged: Dict[str, str]
    conflicts: List[MergeConflict]
    added: List[str]


def merge_dicts(
    source: Dict[str, str],
    target: Dict[str, str],
    strategy: MergeStrategy = MergeStrategy.KEEP_TARGET,
) -> MergeResult:
    """Merge *source* into *target* and return a MergeResult."""
    merged = dict(target)
    conflicts: List[MergeConflict] = []
    added: List[str] = []

    for key, src_val in source.items():
        if key not in target:
            merged[key] = src_val
            added.append(key)
        elif target[key] != src_val:
            conflict = MergeConflict(key=key, source_value=src_val, target_value=target[key])
            conflicts.append(conflict)
            if strategy == MergeStrategy.RAISE:
                raise MergeError(
                    f"Conflict on key '{key}': "
                    f"source={src_val!r}, target={target[key]!r}"
                )
            elif strategy == MergeStrategy.KEEP_SOURCE:
                merged[key] = src_val
            # KEEP_TARGET: already in merged from dict(target)

    return MergeResult(merged=merged, conflicts=conflicts, added=added)


def merge_store_from_profile(
    store_path: str,
    passphrase: str,
    profile_name: str,
    profiles_dir: str,
    strategy: MergeStrategy = MergeStrategy.KEEP_TARGET,
) -> MergeResult:
    """Pull a profile and merge its vars into the local store."""
    source_vars = pull_profile(store_path, passphrase, profile_name, profiles_dir)
    target_vars = get_env_vars_from_store(store_path, passphrase)
    result = merge_dicts(source_vars, target_vars, strategy)
    save_store(store_path, passphrase, result.merged)
    return result


def get_env_vars_from_store(store_path: str, passphrase: str) -> Dict[str, str]:
    """Load vars from store, returning empty dict if store does not exist."""
    from envoy.store import get_env_vars
    try:
        return get_env_vars(store_path, passphrase)
    except FileNotFoundError:
        return {}
