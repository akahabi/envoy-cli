"""Search and filter env vars by key pattern, value pattern, or tags."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.store import get_env_vars
from envoy.tag import _get_tags


class SearchError(Exception):
    """Raised when a search operation fails."""


@dataclass
class SearchResult:
    matches: Dict[str, str] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.matches)

    def is_empty(self) -> bool:
        return self.count == 0

    def summary(self) -> str:
        if self.is_empty():
            return "No matches found."
        return f"{self.count} match{'es' if self.count != 1 else ''} found."


def search_vars(
    store_path: str,
    passphrase: str,
    *,
    key_pattern: Optional[str] = None,
    value_pattern: Optional[str] = None,
    tag: Optional[str] = None,
    case_sensitive: bool = False,
) -> SearchResult:
    """Search env vars by key glob, value regex, and/or tag."""
    vars_ = get_env_vars(store_path, passphrase)

    if not vars_:
        return SearchResult()

    matches: Dict[str, str] = {}

    flags = 0 if case_sensitive else re.IGNORECASE

    tagged_keys: Optional[set] = None
    if tag is not None:
        try:
            tags_map = _get_tags(store_path)
        except Exception as exc:
            raise SearchError(f"Failed to read tags: {exc}") from exc
        tagged_keys = {
            k for k, t_list in tags_map.items() if tag in t_list
        }

    for key, value in vars_.items():
        if key_pattern is not None:
            pat = key_pattern if case_sensitive else key_pattern.upper()
            candidate = key if case_sensitive else key.upper()
            if not fnmatch.fnmatch(candidate, pat):
                continue

        if value_pattern is not None:
            try:
                if not re.search(value_pattern, value, flags):
                    continue
            except re.error as exc:
                raise SearchError(f"Invalid value pattern: {exc}") from exc

        if tagged_keys is not None and key not in tagged_keys:
            continue

        matches[key] = value

    return SearchResult(matches=matches)
