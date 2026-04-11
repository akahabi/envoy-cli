"""Validate env var keys and values against a schema definition."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ValidationIssue:
    key: str
    message: str
    severity: str  # 'error' | 'warning'

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


# Schema: dict mapping key -> {"required": bool, "pattern": str, "min_length": int}
Schema = Dict[str, Dict]


def validate_vars(vars_: Dict[str, str], schema: Schema) -> ValidationResult:
    """Validate *vars_* against *schema*, returning a ValidationResult."""
    result = ValidationResult()

    for key, rules in schema.items():
        required = rules.get("required", False)
        if key not in vars_:
            if required:
                result.issues.append(
                    ValidationIssue(key, "required key is missing", "error")
                )
            continue

        value = vars_[key]

        pattern: Optional[str] = rules.get("pattern")
        if pattern and not re.fullmatch(pattern, value):
            result.issues.append(
                ValidationIssue(
                    key,
                    f"value does not match pattern '{pattern}'",
                    "error",
                )
            )

        min_length: Optional[int] = rules.get("min_length")
        if min_length is not None and len(value) < min_length:
            result.issues.append(
                ValidationIssue(
                    key,
                    f"value is shorter than minimum length {min_length}",
                    "error",
                )
            )

        if rules.get("warn_empty", False) and value.strip() == "":
            result.issues.append(
                ValidationIssue(key, "value is blank", "warning")
            )

    return result
