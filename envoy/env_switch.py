"""Switch the active environment by loading a named profile into the local store."""

from pathlib import Path
from typing import Optional

from envoy.store import load_store, save_store
from envoy.sync import _profile_path, pull_profile
from envoy.audit import record_event


class SwitchError(Exception):
    """Raised when an environment switch fails."""


def switch_env(
    profile: str,
    store_path: Path,
    profiles_dir: Path,
    passphrase: str,
    *,
    dry_run: bool = False,
) -> dict:
    """Load *profile* from *profiles_dir* into *store_path*.

    Returns the dict of variables that were written.

    Raises
    ------
    SwitchError
        If the profile file does not exist.
    """
    path = _profile_path(profiles_dir, profile)
    if not path.exists():
        raise SwitchError(f"Profile '{profile}' not found at {path}")

    vars_ = pull_profile(profile, store_path, profiles_dir, passphrase)

    if not dry_run:
        record_event(
            action="switch",
            profile=profile,
            detail=f"switched to profile '{profile}'; {len(vars_)} vars loaded",
        )

    return vars_


def current_env(
    store_path: Path,
    passphrase: str,
    profiles_dir: Path,
) -> Optional[str]:
    """Return the name of the profile whose contents match the current store,
    or *None* if no profile matches exactly."""
    if not store_path.exists():
        return None

    store_vars = load_store(store_path, passphrase)

    for profile_file in sorted(profiles_dir.glob("*.env.enc")):
        profile_name = profile_file.stem.replace(".env", "")
        try:
            profile_vars = pull_profile(
                profile_name,
                store_path,  # we need a temp read — pull_profile overwrites store
                profiles_dir,
                passphrase,
            )
        except Exception:
            continue
        if profile_vars == store_vars:
            # Restore original store before returning
            save_store(store_path, passphrase, store_vars)
            return profile_name

    # Restore original store (pull_profile may have overwritten it)
    save_store(store_path, passphrase, store_vars)
    return None
