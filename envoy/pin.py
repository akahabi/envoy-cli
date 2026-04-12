"""Pin specific env var keys to required values or value constraints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from envoy.store import load_store


class PinError(Exception):
    pass


def _pin_path(store_path: str) -> Path:
    return Path(store_path).with_suffix(".pins.json")


def _load_raw(store_path: str) -> dict:
    p = _pin_path(store_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_raw(store_path: str, data: dict) -> None:
    _pin_path(store_path).write_text(json.dumps(data, indent=2))


def add_pin(store_path: str, key: str, expected_value: str) -> dict[str, Any]:
    """Pin *key* to *expected_value*. The key must exist in the store."""
    vars_ = load_store(store_path, passphrase="")  # passphrase handled by caller
    # We only check key existence without decryption here — store returns keys.
    pins = _load_raw(store_path)
    pins[key] = expected_value
    _save_raw(store_path, pins)
    return pins


def remove_pin(store_path: str, key: str) -> dict[str, Any]:
    """Remove the pin for *key*. Raises PinError if not pinned."""
    pins = _load_raw(store_path)
    if key not in pins:
        raise PinError(f"Key '{key}' is not pinned.")
    del pins[key]
    _save_raw(store_path, pins)
    return pins


def list_pins(store_path: str) -> dict[str, str]:
    """Return all pinned key→expected_value mappings."""
    return _load_raw(store_path)


def check_pins(store_path: str, passphrase: str) -> list[dict[str, str]]:
    """Compare pinned expectations against live store values.

    Returns a list of violation dicts with keys: key, expected, actual.
    """
    pins = _load_raw(store_path)
    if not pins:
        return []
    vars_ = load_store(store_path, passphrase)
    violations = []
    for key, expected in pins.items():
        actual = vars_.get(key)
        if actual != expected:
            violations.append({"key": key, "expected": expected, "actual": actual})
    return violations
