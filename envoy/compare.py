"""Compare two environments (local store vs profile) and report differences."""

from pathlib import Path
from typing import Optional

from envoy.store import load_store
from envoy.sync import _profile_path
from envoy.diff import diff_vars, summary, has_differences, DiffResult


class CompareError(Exception):
    pass


def compare_store_to_profile(
    store_path: Path,
    profile: str,
    store_passphrase: str,
    profile_passphrase: str,
    profiles_dir: Optional[Path] = None,
) -> DiffResult:
    """Load local store and a named profile, return diff results."""
    if not store_path.exists():
        raise CompareError(f"Store file not found: {store_path}")

    source_vars = load_store(store_path, store_passphrase)

    prof_path = _profile_path(profile, profiles_dir)
    if not prof_path.exists():
        raise CompareError(f"Profile '{profile}' not found.")

    target_vars = load_store(prof_path, profile_passphrase)

    return diff_vars(source_vars, target_vars)


def compare_profiles(
    profile_a: str,
    profile_b: str,
    passphrase_a: str,
    passphrase_b: str,
    profiles_dir: Optional[Path] = None,
) -> DiffResult:
    """Compare two named profiles and return diff results."""
    path_a = _profile_path(profile_a, profiles_dir)
    path_b = _profile_path(profile_b, profiles_dir)

    if not path_a.exists():
        raise CompareError(f"Profile '{profile_a}' not found.")
    if not path_b.exists():
        raise CompareError(f"Profile '{profile_b}' not found.")

    vars_a = load_store(path_a, passphrase_a)
    vars_b = load_store(path_b, passphrase_b)

    return diff_vars(vars_a, vars_b)
