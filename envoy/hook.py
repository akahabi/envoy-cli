"""Hook system for triggering shell commands on store events."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional

HOOK_EVENTS = ("pre-set", "post-set", "pre-export", "post-export", "pre-push", "post-push")


class HookError(Exception):
    """Raised when a hook operation fails."""


def _hook_path(store_path: Path) -> Path:
    return store_path.parent / (store_path.stem + ".hooks.json")


def _load_raw(store_path: Path) -> dict:
    p = _hook_path(store_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_raw(store_path: Path, data: dict) -> None:
    _hook_path(store_path).write_text(json.dumps(data, indent=2))


def add_hook(store_path: Path, event: str, command: str) -> List[str]:
    """Register *command* to run on *event*. Returns updated command list."""
    if event not in HOOK_EVENTS:
        raise HookError(f"Unknown event '{event}'. Valid events: {', '.join(HOOK_EVENTS)}")
    data = _load_raw(store_path)
    hooks = data.get(event, [])
    if command not in hooks:
        hooks.append(command)
    data[event] = hooks
    _save_raw(store_path, data)
    return hooks


def remove_hook(store_path: Path, event: str, command: str) -> List[str]:
    """Remove *command* from *event* hooks. Returns updated command list."""
    data = _load_raw(store_path)
    hooks = data.get(event, [])
    if command not in hooks:
        raise HookError(f"Command not registered for event '{event}'.")
    hooks.remove(command)
    data[event] = hooks
    _save_raw(store_path, data)
    return hooks


def list_hooks(store_path: Path, event: Optional[str] = None) -> dict:
    """Return all hooks, or hooks for a specific event."""
    data = _load_raw(store_path)
    if event is not None:
        if event not in HOOK_EVENTS:
            raise HookError(f"Unknown event '{event}'.")
        return {event: data.get(event, [])}
    return {ev: data.get(ev, []) for ev in HOOK_EVENTS}


def fire_hooks(store_path: Path, event: str, env: Optional[dict] = None) -> List[str]:
    """Run all commands registered for *event*. Returns list of outputs."""
    data = _load_raw(store_path)
    commands = data.get(event, [])
    outputs = []
    for cmd in commands:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            raise HookError(f"Hook command failed: {cmd!r}\n{result.stderr.strip()}")
        outputs.append(result.stdout.strip())
    return outputs
