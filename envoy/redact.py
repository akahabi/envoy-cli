"""Redaction helpers — mask sensitive env var values for safe display."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Keys whose values should always be fully redacted
_SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(SECRET|PASSWORD|PASSWD|TOKEN|API_?KEY|PRIVATE|CREDENTIAL|AUTH)", re.I),
]

_DEFAULT_MASK = "***"
_DEFAULT_VISIBLE_CHARS = 4


class RedactError(Exception):
    """Raised when redaction configuration is invalid."""


@dataclass
class RedactResult:
    original: Dict[str, str]
    redacted: Dict[str, str]
    masked_keys: List[str] = field(default_factory=list)

    @property
    def redaction_count(self) -> int:
        return len(self.masked_keys)

    def summary(self) -> str:
        if not self.masked_keys:
            return "No values redacted."
        keys = ", ".join(sorted(self.masked_keys))
        return f"{self.redaction_count} value(s) redacted: {keys}"


def _is_sensitive(key: str) -> bool:
    return any(p.search(key) for p in _SENSITIVE_PATTERNS)


def _mask_value(value: str, visible_chars: int = _DEFAULT_VISIBLE_CHARS) -> str:
    if len(value) <= visible_chars:
        return _DEFAULT_MASK
    return value[:visible_chars] + _DEFAULT_MASK


def redact_vars(
    vars_: Dict[str, str],
    extra_keys: Optional[List[str]] = None,
    visible_chars: int = _DEFAULT_VISIBLE_CHARS,
) -> RedactResult:
    """Return a RedactResult with sensitive values masked.

    Args:
        vars_: The env vars dict to redact.
        extra_keys: Additional key names to treat as sensitive.
        visible_chars: How many leading characters to keep visible.
    """
    if visible_chars < 0:
        raise RedactError("visible_chars must be >= 0")

    sensitive_extra = set(k.upper() for k in (extra_keys or []))
    redacted: Dict[str, str] = {}
    masked_keys: List[str] = []

    for key, value in vars_.items():
        if _is_sensitive(key) or key.upper() in sensitive_extra:
            redacted[key] = _mask_value(value, visible_chars)
            masked_keys.append(key)
        else:
            redacted[key] = value

    return RedactResult(original=vars_, redacted=redacted, masked_keys=masked_keys)
