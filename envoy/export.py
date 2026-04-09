"""Export environment variables to various formats."""

from __future__ import annotations

from typing import Dict


SUPPORTED_FORMATS = ("dotenv", "json", "shell")


def to_dotenv(vars: Dict[str, str]) -> str:
    """Render vars as a .env file (KEY=VALUE per line)."""
    lines = []
    for key, value in sorted(vars.items()):
        # Quote values that contain spaces or special characters
        if any(c in value for c in (" ", "\t", "\n", "'", '"', "$", "`")):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def to_json(vars: Dict[str, str]) -> str:
    """Render vars as a pretty-printed JSON object."""
    import json

    return json.dumps(dict(sorted(vars.items())), indent=2) + "\n"


def to_shell(vars: Dict[str, str]) -> str:
    """Render vars as export statements for use in a shell script."""
    lines = []
    for key, value in sorted(vars.items()):
        escaped = value.replace("\\", "\\\\").replace("'", "'\\''")
        lines.append(f"export {key}='{escaped}'")
    return "\n".join(lines) + ("\n" if lines else "")


def render(vars: Dict[str, str], fmt: str) -> str:
    """Dispatch to the correct renderer based on *fmt*.

    Parameters
    ----------
    vars:
        Mapping of environment variable names to their values.
    fmt:
        One of ``'dotenv'``, ``'json'``, or ``'shell'``.

    Raises
    ------
    ValueError
        If *fmt* is not a supported format.
    """
    fmt = fmt.lower()
    if fmt == "dotenv":
        return to_dotenv(vars)
    if fmt == "json":
        return to_json(vars)
    if fmt == "shell":
        return to_shell(vars)
    raise ValueError(
        f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
    )
