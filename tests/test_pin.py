"""Tests for envoy.pin."""

import json
import pytest

from envoy.pin import PinError, add_pin, check_pins, list_pins, remove_pin
from envoy.store import save_store


PASS = "hunter2"


@pytest.fixture()
def store_file(tmp_path):
    p = tmp_path / "test.envoy"
    save_store(str(p), {"DB_URL": "postgres://localhost", "SECRET": "abc123"}, PASS)
    return str(p)


def test_list_pins_empty_when_no_file(store_file):
    assert list_pins(store_file) == {}


def test_add_pin_returns_mapping(store_file):
    result = add_pin(store_file, "DB_URL", "postgres://localhost")
    assert result == {"DB_URL": "postgres://localhost"}


def test_add_pin_persists_to_file(store_file, tmp_path):
    add_pin(store_file, "SECRET", "abc123")
    pin_path = tmp_path / "test.pins.json"
    data = json.loads(pin_path.read_text())
    assert data["SECRET"] == "abc123"


def test_add_pin_multiple(store_file):
    add_pin(store_file, "DB_URL", "postgres://localhost")
    result = add_pin(store_file, "SECRET", "abc123")
    assert len(result) == 2


def test_list_pins_returns_all(store_file):
    add_pin(store_file, "DB_URL", "postgres://localhost")
    add_pin(store_file, "SECRET", "abc123")
    pins = list_pins(store_file)
    assert "DB_URL" in pins
    assert "SECRET" in pins


def test_remove_pin_removes_key(store_file):
    add_pin(store_file, "DB_URL", "postgres://localhost")
    remaining = remove_pin(store_file, "DB_URL")
    assert "DB_URL" not in remaining


def test_remove_pin_unknown_key_raises(store_file):
    with pytest.raises(PinError):
        remove_pin(store_file, "NONEXISTENT")


def test_check_pins_no_violations(store_file):
    add_pin(store_file, "DB_URL", "postgres://localhost")
    add_pin(store_file, "SECRET", "abc123")
    violations = check_pins(store_file, PASS)
    assert violations == []


def test_check_pins_detects_mismatch(store_file):
    add_pin(store_file, "SECRET", "wrong_value")
    violations = check_pins(store_file, PASS)
    assert len(violations) == 1
    assert violations[0]["key"] == "SECRET"
    assert violations[0]["expected"] == "wrong_value"
    assert violations[0]["actual"] == "abc123"


def test_check_pins_missing_key_is_violation(store_file):
    add_pin(store_file, "MISSING_KEY", "some_val")
    violations = check_pins(store_file, PASS)
    assert any(v["key"] == "MISSING_KEY" for v in violations)


def test_check_pins_empty_pins_returns_empty(store_file):
    assert check_pins(store_file, PASS) == []
