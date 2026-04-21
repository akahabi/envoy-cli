"""Profile inheritance: resolve vars by merging a chain of profiles."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from envoy.sync import pull_profile, list_profiles


class InheritError(Exception):
    """Raised when inheritance resolution fails."""


class InheritResult:
    def __init__(self, vars: Dict[str, str], chain: List[str]) -> None:
        self.vars = vars
        self.chain = chain

    def origin(self, key: str) -> Optional[str]:
        """Return the name of the first profile in the chain that defines *key*."""
        return self._origins.get(key)

    # populated by resolve()
    _origins: Dict[str, str] = {}

    def summary(self) -> str:
        lines = [f"Resolved {len(self.vars)} var(s) via chain: {' -> '.join(self.chain)}"]
        for k, v in sorted(self.vars.items()):
            src = self._origins.get(k, "?")
            lines.append(f"  {k}={v}  (from {src})")
        return "\n".join(lines)


def resolve(
    profile_names: List[str],
    passphrase: str,
    profiles_dir: Path,
) -> InheritResult:
    """Merge profiles left-to-right; later profiles override earlier ones.

    Args:
        profile_names: Ordered list of profile names (base first, most-specific last).
        passphrase: Decryption passphrase shared across all profiles.
        profiles_dir: Directory where profile files are stored.

    Returns:
        InheritResult with merged vars and the resolved chain.

    Raises:
        InheritError: If any profile in the chain does not exist.
    """
    if not profile_names:
        raise InheritError("profile_names must not be empty")

    available = list_profiles(profiles_dir)
    merged: Dict[str, str] = {}
    origins: Dict[str, str] = {}

    for name in profile_names:
        if name not in available:
            raise InheritError(f"Profile '{name}' not found in {profiles_dir}")
        vars_ = pull_profile(name, passphrase, profiles_dir)
        for k, v in vars_.items():
            merged[k] = v
            origins[k] = name

    result = InheritResult(vars=merged, chain=list(profile_names))
    result._origins = origins
    return result
