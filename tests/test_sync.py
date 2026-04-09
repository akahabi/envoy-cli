"""Tests for envoy.sync profile push/pull functionality."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from envoy.sync import push_profile, pull_profile, list_profiles, delete_profile
from envoy.store import save_store, load_store

PASSPHRASE = "test-secret-passphrase"


@pytest.fixture()
def tmp_store(tmp_path):
    store_path = str(tmp_path / "store.enc")
    data = {"APP_ENV": "test", "DB_URL": "sqlite:///:memory:"}
    save_store(store_path, data, PASSPHRASE)
    return store_path


@pytest.fixture()
def profiles_dir(tmp_path, monkeypatch):
    profiles = tmp_path / "profiles"
    monkeypatch.setattr("envoy.sync.PROFILES_DIR", profiles)
    return profiles


def test_push_creates_profile_file(tmp_store, profiles_dir):
    push_profile(tmp_store, "staging", PASSPHRASE)
    assert (profiles_dir / "staging.enc").exists()


def test_pull_restores_vars(tmp_store, profiles_dir, tmp_path):
    push_profile(tmp_store, "staging", PASSPHRASE)
    new_store = str(tmp_path / "new_store.enc")
    save_store(new_store, {}, PASSPHRASE)
    pull_profile(new_store, "staging", PASSPHRASE)
    result = load_store(new_store, PASSPHRASE)
    assert result["APP_ENV"] == "test"
    assert result["DB_URL"] == "sqlite:///:memory:"


def test_pull_merges_with_existing(tmp_store, profiles_dir, tmp_path):
    push_profile(tmp_store, "staging", PASSPHRASE)
    new_store = str(tmp_path / "new_store.enc")
    save_store(new_store, {"LOCAL_ONLY": "yes"}, PASSPHRASE)
    pull_profile(new_store, "staging", PASSPHRASE)
    result = load_store(new_store, PASSPHRASE)
    assert result["LOCAL_ONLY"] == "yes"
    assert result["APP_ENV"] == "test"


def test_pull_nonexistent_profile_raises(tmp_store, profiles_dir):
    with pytest.raises(FileNotFoundError, match="Profile 'ghost' not found"):
        pull_profile(tmp_store, "ghost", PASSPHRASE)


def test_list_profiles_empty(profiles_dir):
    assert list_profiles() == []


def test_list_profiles_returns_names(tmp_store, profiles_dir):
    push_profile(tmp_store, "staging", PASSPHRASE)
    push_profile(tmp_store, "production", PASSPHRASE)
    names = list_profiles()
    assert set(names) == {"staging", "production"}


def test_delete_profile(tmp_store, profiles_dir):
    push_profile(tmp_store, "staging", PASSPHRASE)
    delete_profile("staging")
    assert "staging" not in list_profiles()


def test_delete_nonexistent_profile_raises(profiles_dir):
    with pytest.raises(FileNotFoundError):
        delete_profile("nope")
