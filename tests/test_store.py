"""Tests for envoy.store encrypted key/value storage."""

import pytest
from pathlib import Path

from envoy.store import load_store, save_store, set_env_var, get_env_vars


PASSPHRASE = "test-passphrase-123"


@pytest.fixture()
def tmp_store(tmp_path: Path) -> Path:
    return tmp_path / "store.enc"


def test_load_empty_store(tmp_store):
    result = load_store(PASSPHRASE, tmp_store)
    assert result == {}


def test_save_and_load_roundtrip(tmp_store):
    data = {"local": {"KEY": "value"}, "staging": {"API_URL": "https://staging.example.com"}}
    save_store(data, PASSPHRASE, tmp_store)
    loaded = load_store(PASSPHRASE, tmp_store)
    assert loaded == data


def test_set_env_var_creates_key(tmp_store):
    set_env_var("local", "DB_HOST", "localhost", PASSPHRASE, tmp_store)
    vars_ = get_env_vars("local", PASSPHRASE, tmp_store)
    assert vars_["DB_HOST"] == "localhost"


def test_set_env_var_overwrites_existing(tmp_store):
    set_env_var("local", "DB_HOST", "localhost", PASSPHRASE, tmp_store)
    set_env_var("local", "DB_HOST", "remotehost", PASSPHRASE, tmp_store)
    vars_ = get_env_vars("local", PASSPHRASE, tmp_store)
    assert vars_["DB_HOST"] == "remotehost"


def test_get_env_vars_unknown_env_returns_empty(tmp_store):
    result = get_env_vars("production", PASSPHRASE, tmp_store)
    assert result == {}


def test_wrong_passphrase_on_load_raises(tmp_store):
    save_store({"local": {"X": "1"}}, PASSPHRASE, tmp_store)
    with pytest.raises(Exception):
        load_store("wrong-passphrase", tmp_store)
