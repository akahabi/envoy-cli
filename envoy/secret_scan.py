"""Scan env var values for accidental secrets or sensitive patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Patterns that suggest a value might be a plaintext secret
_PATTERNS: List[tuple[str, str]] = [
    (r"(?i)^[A-Za-z0-9+/]{40,}={0,2}$", "possible base64-encoded secret"),
    (r"(?i)^[0-9a-f]{32,64}$", "possible hex-encoded secret or hash"),
    (r"(?i)(password|passwd|secret|token|api[_-]?key|private[_-]?key)", "key name suggests secret"),
    (r"^sk_live_[A-Za-z0-9]+", "Stripe live secret key pattern"),
    (r"^ghp_[A-Za-z0-9]{36}", "GitHub personal access token pattern"),
    (r"^AKIA[0-9A-Z]{16}$", "AWS access key ID pattern"),
]


@dataclass
class ScanHit:
    key: str
    value: str
    reason: str

    def __str__(self) -> str:
        masked = value_preview(self.value)
        return f"{self.key}={masked!r}  [{self.reason}]"


@dataclass
class ScanResult:
    hits: List[ScanHit] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return len(self.hits) == 0

    def summary(self) -> str:
        if self.clean:
            return "No suspicious values detected."
        lines = [f"{len(self.hits)} suspicious value(s) found:"]
        for hit in self.hits:
            lines.append(f"  {hit}")
        return "\n".join(lines)


def value_preview(value: str, max_len: int = 6) -> str:
    """Return a masked preview of a value."""
    if len(value) <= max_len:
        return "*" * len(value)
    return value[:3] + "***"


def scan_vars(vars_: Dict[str, str], key_patterns: bool = True) -> ScanResult:
    """Scan a dict of env vars for suspicious values.

    Args:
        vars_: Mapping of key -> value.
        key_patterns: Also check key names against sensitive-name patterns.

    Returns:
        A ScanResult with any hits found.
    """
    hits: List[ScanHit] = []
    for key, value in vars_.items():
        for pattern, reason in _PATTERNS:
            # Key-name pattern only applied when key_patterns is True
            if "key name" in reason and not key_patterns:
                continue
            target = key if "key name" in reason else value
            if re.search(pattern, target):
                hits.append(ScanHit(key=key, value=value, reason=reason))
                break  # one hit per key is enough
    return ScanResult(hits=hits)
