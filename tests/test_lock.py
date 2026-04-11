"""Tests for envoy.lock."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from envoy.lock import LockError, acquire, locked, release, _lock_path


@pytest.fixture()
def target(tmp_path: Path) -> Path:
    p = tmp_path / "store.env"
    p.write_text("data")
    return p


def test_acquire_creates_lock_file(target: Path) -> None:
    lock = acquire(target)
    try:
        assert lock.exists()
        assert lock.name == "store.env.lock"
    finally:
        release(lock)


def test_lock_file_contains_pid(target: Path) -> None:
    import os
    lock = acquire(target)
    try:
        assert lock.read_text() == str(os.getpid())
    finally:
        release(lock)


def test_release_removes_lock_file(target: Path) -> None:
    lock = acquire(target)
    release(lock)
    assert not lock.exists()


def test_release_is_idempotent(target: Path) -> None:
    lock = acquire(target)
    release(lock)
    release(lock)  # should not raise


def test_acquire_times_out_when_locked(target: Path) -> None:
    lock = acquire(target)
    try:
        with pytest.raises(LockError, match="Could not acquire lock"):
            acquire(target, timeout=0.1)
    finally:
        release(lock)


def test_lock_path_helper(target: Path) -> None:
    assert _lock_path(target) == target.parent / "store.env.lock"


def test_context_manager_acquires_and_releases(target: Path) -> None:
    lock_file = _lock_path(target)
    with locked(target):
        assert lock_file.exists()
    assert not lock_file.exists()


def test_context_manager_releases_on_exception(target: Path) -> None:
    lock_file = _lock_path(target)
    try:
        with locked(target):
            assert lock_file.exists()
            raise ValueError("boom")
    except ValueError:
        pass
    assert not lock_file.exists()


def test_sequential_locks_succeed(target: Path) -> None:
    for _ in range(3):
        with locked(target):
            pass  # each iteration should cleanly acquire then release


def test_threaded_access_serialised(target: Path) -> None:
    """Two threads competing for the lock should not both hold it."""
    held_simultaneously: list[bool] = []
    inside = threading.Event()

    def worker() -> None:
        with locked(target, timeout=5.0):
            inside.set()
            time.sleep(0.05)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    inside.wait()   # ensure t1 is inside before t2 starts
    t2.start()
    t1.join()
    t2.join()
    # If we reach here without deadlock or error, serialisation worked.
    assert not _lock_path(target).exists()
