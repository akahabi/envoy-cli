"""Snapshot management: capture and restore point-in-time copies of env vars."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

from envoy.store import load_store, save_store


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshots_dir(store_path: str) -> Path:
    base = Path(store_path).parent
    return base / ".snapshots"


def _snapshot_path(store_path: str, name: str) -> Path:
    return _snapshots_dir(store_path) / f"{name}.json"


def create_snapshot(store_path: str, passphrase: str, name: Optional[str] = None) -> str:
    """Capture current env vars and save as a named snapshot. Returns the snapshot name."""
    vars_ = load_store(store_path, passphrase)
    if name is None:
        name = f"snap_{int(time.time())}"
    snap_dir = _snapshots_dir(store_path)
    snap_dir.mkdir(parents=True, exist_ok=True)
    payload = {"name": name, "created_at": time.time(), "vars": vars_}
    _snapshot_path(store_path, name).write_text(json.dumps(payload, indent=2))
    return name


def restore_snapshot(store_path: str, passphrase: str, name: str) -> Dict[str, str]:
    """Overwrite the current store with vars from the named snapshot."""
    path = _snapshot_path(store_path, name)
    if not path.exists():
        raise SnapshotError(f"Snapshot '{name}' not found.")
    payload = json.loads(path.read_text())
    vars_: Dict[str, str] = payload["vars"]
    save_store(store_path, passphrase, vars_)
    return vars_


def list_snapshots(store_path: str) -> List[Dict]:
    """Return metadata for all snapshots, sorted by creation time (newest first)."""
    snap_dir = _snapshots_dir(store_path)
    if not snap_dir.exists():
        return []
    results = []
    for f in snap_dir.glob("*.json"):
        try:
            payload = json.loads(f.read_text())
            results.append({"name": payload["name"], "created_at": payload["created_at"], "var_count": len(payload["vars"])})
        except (json.JSONDecodeError, KeyError):
            continue
    return sorted(results, key=lambda x: x["created_at"], reverse=True)


def delete_snapshot(store_path: str, name: str) -> None:
    """Delete a named snapshot."""
    path = _snapshot_path(store_path, name)
    if not path.exists():
        raise SnapshotError(f"Snapshot '{name}' not found.")
    path.unlink()
