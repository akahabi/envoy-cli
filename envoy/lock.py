"""Lock file management for envoy stores.

Provides a simple advisory lock mechanism to prevent concurrent writes
to the same store or profile file.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

DEFAULT_TIMEOUT = 10.0  # seconds
DEFAULT_POLL = 0.05     # seconds
LOCK_SUFFIX = ".lock"


class LockError(Exception):
    """Raised when a lock cannot be acquired within the timeout."""


def _lock_path(target: Path) -> Path:
    return target.with_suffix(target.suffix + LOCK_SUFFIX)


def acquire(target: Path, timeout: float = DEFAULT_TIMEOUT) -> Path:
    """Acquire an advisory lock for *target*.

    Creates a sibling ``<target>.lock`` file.  Polls until the lock is
    free or *timeout* seconds have elapsed.

    Returns the path to the lock file.
    Raises :class:`LockError` on timeout.
    """
    lock = _lock_path(target)
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return lock
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise LockError(
                    f"Could not acquire lock for '{target}' within {timeout}s. "
                    f"If no other process is running, delete '{lock}' manually."
                )
            time.sleep(DEFAULT_POLL)


def release(lock: Path) -> None:
    """Release a previously acquired lock file.

    Safe to call even if the lock file no longer exists.
    """
    try:
        lock.unlink()
    except FileNotFoundError:
        pass


class locked:
    """Context manager that acquires and releases a lock around *target*.

    Example::

        with locked(store_path):
            save_store(store_path, passphrase, vars)
    """

    def __init__(self, target: Path, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._target = target
        self._timeout = timeout
        self._lock: Path | None = None

    def __enter__(self) -> "locked":
        self._lock = acquire(self._target, self._timeout)
        return self

    def __exit__(self, *_: object) -> None:
        if self._lock is not None:
            release(self._lock)
            self._lock = None
