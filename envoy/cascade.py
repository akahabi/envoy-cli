"""Cascade resolution: merge vars from multiple profiles in priority order."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.sync import pull_profile
from envoy.store import load_store


class CascadeError(Exception):
    """Raised when cascade resolution fails."""


@dataclass
class CascadeResult:
    merged: Dict[str, str]
    sources: Dict[str, str]  # key -> profile name that provided it
    layers: List[str]        # ordered list of profiles used (lowest to highest priority)

    def origin(self, key: str) -> Optional[str]:
        """Return the profile name that provided *key*, or None."""
        return self.sources.get(key)

    def summary(self) -> str:
        lines = [f"Cascade layers (lowest → highest): {' → '.join(self.layers)}"]
        for key, src in sorted(self.sources.items()):
            lines.append(f"  {key}  (from {src})")
        return "\n".join(lines)


def cascade(
    store_path: str,
    passphrase: str,
    profiles: List[str],
    profiles_dir: str,
    base_store: bool = True,
) -> CascadeResult:
    """Merge variables from *profiles* in order (last profile wins).

    If *base_store* is True the local store is loaded first as the
    lowest-priority layer before any profiles are applied.
    """
    if not profiles:
        raise CascadeError("At least one profile must be specified.")

    merged: Dict[str, str] = {}
    sources: Dict[str, str] = {}
    layers: List[str] = []

    if base_store:
        try:
            base_vars = load_store(store_path, passphrase)
        except FileNotFoundError:
            base_vars = {}
        layer_name = "__local__"
        layers.append(layer_name)
        for k, v in base_vars.items():
            merged[k] = v
            sources[k] = layer_name

    for profile in profiles:
        try:
            profile_vars = pull_profile(profiles_dir, profile, passphrase)
        except FileNotFoundError:
            raise CascadeError(f"Profile '{profile}' not found in '{profiles_dir}'.")
        layers.append(profile)
        for k, v in profile_vars.items():
            merged[k] = v
            sources[k] = profile

    return CascadeResult(merged=merged, sources=sources, layers=layers)
