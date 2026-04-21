"""Quota management: enforce max number of vars per store or namespace."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

DEFAULT_QUOTA = 100


class QuotaError(Exception):
    """Raised when a quota rule is violated or configuration is invalid."""


def _quota_path(store_path: Path) -> Path:
    return store_path.parent / (store_path.stem + ".quota.json")


def _load_raw(store_path: Path) -> Dict:
    p = _quota_path(store_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_raw(store_path: Path, data: Dict) -> None:
    _quota_path(store_path).write_text(json.dumps(data, indent=2))


def set_quota(store_path: Path, limit: int, namespace: Optional[str] = None) -> Dict:
    """Set a quota limit for the whole store or a specific namespace."""
    if limit < 1:
        raise QuotaError(f"Quota limit must be at least 1, got {limit}")
    data = _load_raw(store_path)
    key = namespace if namespace else "__global__"
    data[key] = limit
    _save_raw(store_path, data)
    return dict(data)


def get_quota(store_path: Path, namespace: Optional[str] = None) -> int:
    """Return the configured limit for the store or namespace (default 100)."""
    data = _load_raw(store_path)
    key = namespace if namespace else "__global__"
    return data.get(key, DEFAULT_QUOTA)


def remove_quota(store_path: Path, namespace: Optional[str] = None) -> None:
    """Remove a quota rule, falling back to the default."""
    data = _load_raw(store_path)
    key = namespace if namespace else "__global__"
    data.pop(key, None)
    _save_raw(store_path, data)


def check_quota(store_path: Path, vars_: Dict, namespace: Optional[str] = None) -> None:
    """Raise QuotaError if *vars_* exceeds the configured limit."""
    if namespace:
        prefix = namespace + ":"
        count = sum(1 for k in vars_ if k.startswith(prefix))
    else:
        count = len(vars_)
    limit = get_quota(store_path, namespace)
    if count > limit:
        scope = f"namespace '{namespace}'" if namespace else "store"
        raise QuotaError(
            f"Quota exceeded for {scope}: {count} vars present, limit is {limit}"
        )
