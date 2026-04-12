"""Tests for envoy.env_switch."""

import pytest
from pathlib import Path

from envoy.store import save_store, load_store
from envoy.sync import push_profile
from envoy.env_switch import SwitchError, switch_env, current_env


PASSPHRASE = "hunter2"


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    p = tmp_path / "store.env.enc"
    save_store(p, PASSPHRASE, {"APP": "original", "DEBUG": "false"})
    return p


@pytest.fixture()
def profiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "profiles"
    d.mkdir()
    return d


def _push(name: str, vars_: dict, store_file: Path, profiles_dir: Path) -> None:
    save_store(store_file, PASSPHRASE, vars_)
    push_profile(name, store_file, profiles_dir, PASSPHRASE)


# ---------------------------------------------------------------------------
# switch_env
# ---------------------------------------------------------------------------

def test_switch_env_loads_profile_vars(store_file, profiles_dir):
    _push("staging", {"APP": "staging-app", "DEBUG": "true"}, store_file, profiles_dir)
    # Reset store to something different
    save_store(store_file, PASSPHRASE, {"APP": "local"})

    result = switch_env("staging", store_file, profiles_dir, PASSPHRASE)

    assert result["APP"] == "staging-app"
    assert result["DEBUG"] == "true"


def test_switch_env_persists_to_store(store_file, profiles_dir):
    _push("prod", {"APP": "prod-app"}, store_file, profiles_dir)
    save_store(store_file, PASSPHRASE, {"APP": "local"})

    switch_env("prod", store_file, profiles_dir, PASSPHRASE)

    loaded = load_store(store_file, PASSPHRASE)
    assert loaded["APP"] == "prod-app"


def test_switch_env_raises_for_missing_profile(store_file, profiles_dir):
    with pytest.raises(SwitchError, match="nonexistent"):
        switch_env("nonexistent", store_file, profiles_dir, PASSPHRASE)


def test_switch_env_dry_run_does_not_raise(store_file, profiles_dir):
    _push("dev", {"APP": "dev"}, store_file, profiles_dir)
    # dry_run=True should still return vars without error
    result = switch_env("dev", store_file, profiles_dir, PASSPHRASE, dry_run=True)
    assert result["APP"] == "dev"


# ---------------------------------------------------------------------------
# current_env
# ---------------------------------------------------------------------------

def test_current_env_returns_matching_profile(store_file, profiles_dir):
    vars_ = {"APP": "match", "PORT": "8080"}
    _push("match-profile", vars_, store_file, profiles_dir)
    save_store(store_file, PASSPHRASE, vars_)

    result = current_env(store_file, PASSPHRASE, profiles_dir)
    assert result == "match-profile"


def test_current_env_returns_none_when_no_match(store_file, profiles_dir):
    _push("other", {"APP": "other"}, store_file, profiles_dir)
    save_store(store_file, PASSPHRASE, {"APP": "completely-different"})

    result = current_env(store_file, PASSPHRASE, profiles_dir)
    assert result is None


def test_current_env_returns_none_when_no_store(tmp_path, profiles_dir):
    missing = tmp_path / "no_store.enc"
    result = current_env(missing, PASSPHRASE, profiles_dir)
    assert result is None
