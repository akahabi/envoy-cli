"""Backup and restore the local .env store to/from a timestamped archive."""

from __future__ import annotations

import json
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path


class BackupError(Exception):
    """Raised when a backup or restore operation fails."""


def _backups_dir(store_path: Path) -> Path:
    return store_path.parent / ".envoy_backups"


def _backup_name(label: str | None) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{label}__{ts}" if label else ts


def create_backup(store_path: Path, label: str | None = None) -> str:
    """Archive *store_path* into a compressed tarball and return the backup name."""
    if not store_path.exists():
        raise BackupError(f"Store not found: {store_path}")

    backups = _backups_dir(store_path)
    backups.mkdir(parents=True, exist_ok=True)

    name = _backup_name(label)
    archive = backups / f"{name}.tar.gz"

    with tarfile.open(archive, "w:gz") as tar:
        tar.add(store_path, arcname=store_path.name)

    return name


def restore_backup(store_path: Path, name: str) -> None:
    """Restore *store_path* from a previously created backup named *name*."""
    backups = _backups_dir(store_path)
    archive = backups / f"{name}.tar.gz"

    if not archive.exists():
        raise BackupError(f"Backup not found: {name}")

    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(path=store_path.parent)


def list_backups(store_path: Path) -> list[str]:
    """Return backup names sorted newest-first."""
    backups = _backups_dir(store_path)
    if not backups.exists():
        return []
    names = sorted(
        (p.stem for p in backups.glob("*.tar.gz")),
        reverse=True,
    )
    return names


def delete_backup(store_path: Path, name: str) -> None:
    """Delete a single backup archive by name."""
    backups = _backups_dir(store_path)
    archive = backups / f"{name}.tar.gz"
    if not archive.exists():
        raise BackupError(f"Backup not found: {name}")
    archive.unlink()
