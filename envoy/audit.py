"""Audit log for tracking env var changes across environments."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_AUDIT_PATH = Path.home() / ".envoy" / "audit.log"


def _get_audit_path(audit_path: Optional[Path] = None) -> Path:
    path = audit_path or DEFAULT_AUDIT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def record_event(
    action: str,
    key: str,
    environment: str,
    profile: Optional[str] = None,
    audit_path: Optional[Path] = None,
) -> dict:
    """Record an audit event and append it to the audit log."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "key": key,
        "environment": environment,
        "profile": profile,
    }
    path = _get_audit_path(audit_path)
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")
    return event


def read_events(
    audit_path: Optional[Path] = None,
    environment: Optional[str] = None,
    action: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[dict]:
    """Read and optionally filter audit events from the log."""
    path = _get_audit_path(audit_path)
    if not path.exists():
        return []
    events = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if environment and event.get("environment") != environment:
                continue
            if action and event.get("action") != action:
                continue
            events.append(event)
    if limit:
        events = events[-limit:]
    return events


def clear_events(audit_path: Optional[Path] = None) -> None:
    """Clear all audit events from the log."""
    path = _get_audit_path(audit_path)
    if path.exists():
        path.unlink()
