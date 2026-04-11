"""Lint .env variable names and values for common issues."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

_KEY_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')
_LEADING_WHITESPACE_RE = re.compile(r'^\s+')
_TRAILING_WHITESPACE_RE = re.compile(r'\s+$')


@dataclass
class LintIssue:
    key: str
    severity: str  # 'error' | 'warning'
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == 'error']

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == 'warning']

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def lint_vars(vars: Dict[str, str]) -> LintResult:
    """Run all lint checks against a dict of env vars."""
    result = LintResult()

    for key, value in vars.items():
        # Key naming convention
        if not _KEY_RE.match(key):
            result.issues.append(LintIssue(
                key=key,
                severity='error',
                message="Key must be uppercase letters, digits, or underscores, starting with a letter.",
            ))

        # Empty value
        if value == '':
            result.issues.append(LintIssue(
                key=key,
                severity='warning',
                message="Value is empty.",
            ))

        # Leading/trailing whitespace in value
        if _LEADING_WHITESPACE_RE.match(value) or _TRAILING_WHITESPACE_RE.search(value):
            result.issues.append(LintIssue(
                key=key,
                severity='warning',
                message="Value has leading or trailing whitespace.",
            ))

        # Possible unquoted URL or multiline content
        if '\n' in value:
            result.issues.append(LintIssue(
                key=key,
                severity='error',
                message="Value contains a newline character.",
            ))

    return result
