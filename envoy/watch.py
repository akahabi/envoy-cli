"""Watch a store file for changes and emit events when vars are added/modified/removed."""

from __future__ import annotations

import time
import hashlib
import json
from pathlib import Path
from typing import Callable, Optional

from envoy.store import load_store


class WatchError(Exception):
    """Raised when the watch cannot be initialised."""


def _file_hash(path: Path) -> str:
    """Return a stable hex digest for the file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot(store_path: Path, passphrase: str) -> dict[str, str]:
    """Return the current vars from *store_path* as a plain dict."""
    return load_store(store_path, passphrase)


def diff_snapshots(
    before: dict[str, str], after: dict[str, str]
) -> dict[str, list[tuple[str, Optional[str], Optional[str]]]]:
    """Return a structured diff between two snapshots.

    Returns a dict with keys ``added``, ``removed``, ``changed``.
    Each value is a list of ``(key, old_value, new_value)`` tuples.
    """
    added = [(k, None, after[k]) for k in after if k not in before]
    removed = [(k, before[k], None) for k in before if k not in after]
    changed = [
        (k, before[k], after[k])
        for k in before
        if k in after and before[k] != after[k]
    ]
    return {"added": added, "removed": removed, "changed": changed}


def watch(
    store_path: Path,
    passphrase: str,
    on_change: Callable[[dict[str, list]], None],
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *store_path* every *interval* seconds and call *on_change* with diffs.

    Raises ``WatchError`` if the store file does not exist at startup.
    Set *max_iterations* to a positive integer to stop after N polls (useful in tests).
    """
    if not store_path.exists():
        raise WatchError(f"Store file not found: {store_path}")

    current_vars = _snapshot(store_path, passphrase)
    current_hash = _file_hash(store_path)
    iterations = 0

    while True:
        if max_iterations is not None and iterations >= max_iterations:
            break
        time.sleep(interval)
        iterations += 1
        if not store_path.exists():
            continue
        new_hash = _file_hash(store_path)
        if new_hash == current_hash:
            continue
        new_vars = _snapshot(store_path, passphrase)
        diff = diff_snapshots(current_vars, new_vars)
        if any(diff.values()):
            on_change(diff)
        current_vars = new_vars
        current_hash = new_hash
