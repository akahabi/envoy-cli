"""Tests for envoy.snapshot and envoy.cli_snapshot."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.snapshot import SnapshotError, create_snapshot, delete_snapshot, list_snapshots, restore_snapshot
from envoy.store import save_store
from envoy.cli_snapshot import snapshot_cmd

PASS = "test-passphrase"


@pytest.fixture()
def store_file(tmp_path: Path) -> str:
    path = str(tmp_path / "store.env")
    save_store(path, PASS, {"KEY1": "val1", "KEY2": "val2"})
    return path


def test_create_snapshot_returns_name(store_file: str) -> None:
    name = create_snapshot(store_file, PASS, name="v1")
    assert name == "v1"


def test_create_snapshot_auto_name(store_file: str) -> None:
    name = create_snapshot(store_file, PASS)
    assert name.startswith("snap_")


def test_create_snapshot_persists_file(store_file: str) -> None:
    create_snapshot(store_file, PASS, name="mycheckpoint")
    snap_path = Path(store_file).parent / ".snapshots" / "mycheckpoint.json"
    assert snap_path.exists()
    data = json.loads(snap_path.read_text())
    assert data["vars"] == {"KEY1": "val1", "KEY2": "val2"}


def test_restore_snapshot_overwrites_store(store_file: str) -> None:
    create_snapshot(store_file, PASS, name="before")
    save_store(store_file, PASS, {"KEY1": "changed", "KEY3": "new"})
    vars_ = restore_snapshot(store_file, PASS, "before")
    assert vars_ == {"KEY1": "val1", "KEY2": "val2"}


def test_restore_missing_snapshot_raises(store_file: str) -> None:
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot(store_file, PASS, "ghost")


def test_list_snapshots_empty(store_file: str) -> None:
    assert list_snapshots(store_file) == []


def test_list_snapshots_sorted_newest_first(store_file: str) -> None:
    create_snapshot(store_file, PASS, name="first")
    time.sleep(0.01)
    create_snapshot(store_file, PASS, name="second")
    snaps = list_snapshots(store_file)
    assert [s["name"] for s in snaps] == ["second", "first"]


def test_delete_snapshot_removes_file(store_file: str) -> None:
    create_snapshot(store_file, PASS, name="to_delete")
    delete_snapshot(store_file, "to_delete")
    assert list_snapshots(store_file) == []


def test_delete_missing_snapshot_raises(store_file: str) -> None:
    with pytest.raises(SnapshotError):
        delete_snapshot(store_file, "nope")


# --- CLI tests ---

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def test_cli_create_success(runner: CliRunner, store_file: str) -> None:
    result = runner.invoke(snapshot_cmd, ["create", "--store", store_file, "--passphrase", PASS, "--name", "cli_snap"])
    assert result.exit_code == 0
    assert "cli_snap" in result.output


def test_cli_list_shows_snapshot(runner: CliRunner, store_file: str) -> None:
    create_snapshot(store_file, PASS, name="listed")
    result = runner.invoke(snapshot_cmd, ["list", "--store", store_file])
    assert result.exit_code == 0
    assert "listed" in result.output


def test_cli_restore_success(runner: CliRunner, store_file: str) -> None:
    create_snapshot(store_file, PASS, name="snap_r")
    result = runner.invoke(snapshot_cmd, ["restore", "snap_r", "--store", store_file, "--passphrase", PASS])
    assert result.exit_code == 0
    assert "2 variable(s)" in result.output


def test_cli_delete_success(runner: CliRunner, store_file: str) -> None:
    create_snapshot(store_file, PASS, name="del_me")
    result = runner.invoke(snapshot_cmd, ["delete", "del_me", "--store", store_file])
    assert result.exit_code == 0
    assert "deleted" in result.output
