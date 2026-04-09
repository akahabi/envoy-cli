"""Template rendering for .env files with variable substitution."""

import re
from typing import Dict, Optional


class TemplateError(Exception):
    """Raised when template rendering fails."""


_VAR_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}")


def render_template(template: str, variables: Dict[str, str]) -> str:
    """Render a template string, substituting ${VAR} or ${VAR:default} placeholders.

    Args:
        template: Template string with ${VAR} or ${VAR:default} placeholders.
        variables: Dictionary of variable names to values.

    Returns:
        Rendered string with all placeholders substituted.

    Raises:
        TemplateError: If a variable is missing and no default is provided.
    """
    missing = []

    def replace(match: re.Match) -> str:
        name = match.group(1)
        default: Optional[str] = match.group(2)
        if name in variables:
            return variables[name]
        if default is not None:
            return default
        missing.append(name)
        return match.group(0)

    result = _VAR_PATTERN.sub(replace, template)

    if missing:
        raise TemplateError(
            f"Template references undefined variable(s) with no default: {', '.join(missing)}"
        )

    return result


def extract_placeholders(template: str) -> Dict[str, Optional[str]]:
    """Return all placeholder names and their defaults found in a template.

    Args:
        template: Template string to scan.

    Returns:
        Dict mapping variable name -> default value (or None if no default).
    """
    result: Dict[str, Optional[str]] = {}
    for match in _VAR_PATTERN.finditer(template):
        name = match.group(1)
        default: Optional[str] = match.group(2)
        if name not in result:
            result[name] = default
    return result
