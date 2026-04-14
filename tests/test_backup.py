"""Tests for envoy.backup."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.backup import (
    BackupError,
    create_backup,
    delete_backup,
    list_backups,
    restore_backup,
)


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    p = tmp_path / "store.env.enc"
    p.write_text(json.dumps({"vars": {"KEY": "value"}}))
    return p


def test_create_backup_returns_name(store_file: Path) -> None:
    name = create_backup(store_file)
    assert isinstance(name, str)
    assert len(name) > 0


def test_create_backup_with_label_includes_label(store_file: Path) -> None:
    name = create_backup(store_file, label="pre-deploy")
    assert name.startswith("pre-deploy__")


def test_create_backup_persists_archive(store_file: Path) -> None:
    name = create_backup(store_file)
    backups_dir = store_file.parent / ".envoy_backups"
    assert (backups_dir / f"{name}.tar.gz").exists()


def test_create_backup_missing_store_raises(tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="Store not found"):
        create_backup(tmp_path / "missing.enc")


def test_list_backups_empty_when_no_dir(store_file: Path) -> None:
    assert list_backups(store_file) == []


def test_list_backups_returns_names(store_file: Path) -> None:
    create_backup(store_file, label="a")
    create_backup(store_file, label="b")
    names = list_backups(store_file)
    assert len(names) == 2
    assert all(isinstance(n, str) for n in names)


def test_list_backups_sorted_newest_first(store_file: Path) -> None:
    n1 = create_backup(store_file, label="first")
    n2 = create_backup(store_file, label="second")
    names = list_backups(store_file)
    assert names[0] >= names[1]  # lexicographic desc == timestamp desc


def test_restore_backup_overwrites_store(store_file: Path) -> None:
    name = create_backup(store_file)
    store_file.write_text(json.dumps({"vars": {"KEY": "changed"}}))
    restore_backup(store_file, name)
    data = json.loads(store_file.read_text())
    assert data["vars"]["KEY"] == "value"


def test_restore_backup_missing_name_raises(store_file: Path) -> None:
    with pytest.raises(BackupError, match="Backup not found"):
        restore_backup(store_file, "nonexistent")


def test_delete_backup_removes_archive(store_file: Path) -> None:
    name = create_backup(store_file)
    delete_backup(store_file, name)
    assert name not in list_backups(store_file)


def test_delete_backup_missing_raises(store_file: Path) -> None:
    with pytest.raises(BackupError, match="Backup not found"):
        delete_backup(store_file, "ghost")
