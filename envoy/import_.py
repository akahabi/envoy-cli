"""Import environment variables from external formats (.env, JSON, shell exports)."""

import json
import re
import shlex
from pathlib import Path
from typing import Dict, Optional


class ImportError(Exception):
    """Raised when an import operation fails."""


def from_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env file into a dict of key-value pairs."""
    result: Dict[str, str] = {}
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ImportError(f"Line {lineno}: no '=' found: {raw_line!r}")
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            raise ImportError(f"Line {lineno}: invalid key name: {key!r}")
        # Strip optional surrounding quotes
        for quote in ('"', "'"):
            if value.startswith(quote) and value.endswith(quote) and len(value) >= 2:
                value = value[1:-1]
                break
        result[key] = value
    return result


def from_json(text: str) -> Dict[str, str]:
    """Parse a JSON object into a dict of key-value pairs."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object.")
    result: Dict[str, str] = {}
    for k, v in data.items():
        if not isinstance(k, str) or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", k):
            raise ImportError(f"Invalid key name: {k!r}")
        if not isinstance(v, str):
            raise ImportError(f"Value for key {k!r} must be a string, got {type(v).__name__}.")
        result[k] = v
    return result


def from_shell(text: str) -> Dict[str, str]:
    """Parse 'export KEY=VALUE' shell statements into a dict."""
    result: Dict[str, str] = {}
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            raise ImportError(f"Line {lineno}: no '=' found: {raw_line!r}")
        key, _, value = line.partition("=")
        key = key.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            raise ImportError(f"Line {lineno}: invalid key name: {key!r}")
        try:
            tokens = shlex.split(value)
        except ValueError as exc:
            raise ImportError(f"Line {lineno}: {exc}") from exc
        result[key] = tokens[0] if tokens else ""
    return result


def load(path: str, fmt: Optional[str] = None) -> Dict[str, str]:
    """Load vars from a file, auto-detecting format from extension if fmt is None."""
    p = Path(path)
    if not p.exists():
        raise ImportError(f"File not found: {path}")
    text = p.read_text(encoding="utf-8")
    detected = fmt or p.suffix.lower().lstrip(".")
    parsers = {"env": from_dotenv, "json": from_json, "sh": from_shell}
    parser = parsers.get(detected)
    if parser is None:
        raise ImportError(f"Unknown format: {detected!r}. Use one of: {list(parsers)}.")
    return parser(text)
