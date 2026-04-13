"""Unit tests for envoy.watch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pytest

from envoy.store import save_store, set_env_var
from envoy.watch import WatchError, diff_snapshots, watch

PASS = "hunter2"


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.env.enc"
    save_store(path, PASS, {"ALPHA": "1", "BETA": "2"})
    return path


# ---------------------------------------------------------------------------
# diff_snapshots
# ---------------------------------------------------------------------------

def test_diff_detects_added_key():
    before = {"A": "1"}
    after = {"A": "1", "B": "2"}
    diff = diff_snapshots(before, after)
    assert diff["added"] == [("B", None, "2")]
    assert diff["removed"] == []
    assert diff["changed"] == []


def test_diff_detects_removed_key():
    before = {"A": "1", "B": "2"}
    after = {"A": "1"}
    diff = diff_snapshots(before, after)
    assert diff["removed"] == [("B", "2", None)]


def test_diff_detects_changed_value():
    before = {"A": "old"}
    after = {"A": "new"}
    diff = diff_snapshots(before, after)
    assert diff["changed"] == [("A", "old", "new")]


def test_diff_identical_dicts_returns_empty():
    d = {"A": "1", "B": "2"}
    diff = diff_snapshots(d, d.copy())
    assert not any(diff.values())


# ---------------------------------------------------------------------------
# watch()
# ---------------------------------------------------------------------------

def test_watch_raises_if_store_missing(tmp_path: Path):
    with pytest.raises(WatchError):
        watch(tmp_path / "missing.enc", PASS, on_change=lambda d: None, max_iterations=0)


def test_watch_calls_on_change_when_file_changes(store_file: Path):
    received: list[dict] = []

    def _write_new_var():
        set_env_var(store_file, PASS, "GAMMA", "3")

    call_count = 0

    def on_change(diff: dict) -> None:
        received.append(diff)

    # Patch time.sleep to avoid real delays and mutate the file mid-loop
    import envoy.watch as wmod
    original_sleep = wmod.time.sleep

    iteration = 0

    def fake_sleep(_interval):
        nonlocal iteration
        if iteration == 0:
            _write_new_var()
        iteration += 1

    wmod.time.sleep = fake_sleep
    try:
        watch(store_file, PASS, on_change=on_change, interval=0, max_iterations=2)
    finally:
        wmod.time.sleep = original_sleep

    assert len(received) == 1
    assert received[0]["added"] == [("GAMMA", None, "3")]


def test_watch_no_callback_when_file_unchanged(store_file: Path):
    received: list[dict] = []

    import envoy.watch as wmod
    original_sleep = wmod.time.sleep
    wmod.time.sleep = lambda _: None
    try:
        watch(store_file, PASS, on_change=received.append, interval=0, max_iterations=3)
    finally:
        wmod.time.sleep = original_sleep

    assert received == []
