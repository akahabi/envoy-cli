"""Diff utilities for comparing .env variable sets across environments."""

from typing import Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class DiffResult:
    only_in_source: Dict[str, str] = field(default_factory=dict)
    only_in_target: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.only_in_source or self.only_in_target or self.changed)

    def summary(self) -> str:
        lines = []
        for key, val in sorted(self.only_in_source.items()):
            lines.append(f"  + {key}={val}")
        for key, val in sorted(self.only_in_target.items()):
            lines.append(f"  - {key}={val}")
        for key, (src, tgt) in sorted(self.changed.items()):
            lines.append(f"  ~ {key}: {tgt!r} -> {src!r}")
        if not lines:
            lines.append("  (no differences)")
        return "\n".join(lines)


def diff_vars(
    source: Dict[str, str],
    target: Dict[str, str],
) -> DiffResult:
    """Compare two variable dicts and return a DiffResult.

    Args:
        source: The reference set of variables (e.g. local).
        target: The set to compare against (e.g. a profile).

    Returns:
        A DiffResult describing additions, removals, and changes.
    """
    result = DiffResult()
    all_keys = set(source) | set(target)

    for key in all_keys:
        in_source = key in source
        in_target = key in target

        if in_source and not in_target:
            result.only_in_source[key] = source[key]
        elif in_target and not in_source:
            result.only_in_target[key] = target[key]
        elif source[key] != target[key]:
            result.changed[key] = (source[key], target[key])
        else:
            result.unchanged.append(key)

    return result
