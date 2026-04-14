"""Clone an existing profile into a new profile, optionally overriding vars."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from envoy.sync import _profile_path, pull_profile, push_profile


class CloneError(Exception):
    """Raised when a clone operation fails."""


def clone_profile(
    profiles_dir: Path,
    src_name: str,
    dst_name: str,
    passphrase: str,
    overrides: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Clone *src_name* into *dst_name*, applying optional *overrides*.

    Parameters
    ----------
    profiles_dir:
        Directory that holds encrypted profile files.
    src_name:
        Name of the profile to copy from.
    dst_name:
        Name of the new profile to create.
    passphrase:
        Encryption passphrase used for both reading and writing.
    overrides:
        Key/value pairs that should be set (or replaced) in the clone.

    Returns
    -------
    Dict[str, str]
        The final set of variables stored in the new profile.
    """
    src_path = _profile_path(profiles_dir, src_name)
    if not src_path.exists():
        raise CloneError(f"Source profile '{src_name}' does not exist.")

    dst_path = _profile_path(profiles_dir, dst_name)
    if dst_path.exists():
        raise CloneError(f"Destination profile '{dst_name}' already exists.")

    vars_: Dict[str, str] = pull_profile(profiles_dir, src_name, passphrase)

    if overrides:
        vars_.update(overrides)

    push_profile(profiles_dir, dst_name, vars_, passphrase)
    return vars_
