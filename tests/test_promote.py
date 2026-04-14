"""Tests for envoy.promote."""

from __future__ import annotations

from pathlib import Path

import pytest

from envoy.store import save_store, load_store, set_env_var
from envoy.sync import push_profile
from envoy.promote import promote_profile, PromoteError
from envoy.merge import MergeStrategy

PASS = "test-passphrase"


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    return tmp_path / "store.enc"


@pytest.fixture()
def profiles_dir(tmp_path: Path) -> Path:
    d = tmp_path / "profiles"
    d.mkdir()
    return d


def _seed_profile(name: str, vars_: dict, store_file: Path, profiles_dir: Path) -> None:
    store = {"vars": vars_}
    save_store(store, PASS, store_file)
    push_profile(name, PASS, store_file, profiles_dir)


def test_promote_copies_all_vars(store_file, profiles_dir):
    _seed_profile("staging", {"DB_URL": "postgres://staging", "DEBUG": "true"}, store_file, profiles_dir)
    merged = promote_profile(
        src_profile="staging",
        dst_profile="production",
        passphrase=PASS,
        store_path=store_file,
        profiles_dir=profiles_dir,
    )
    assert merged["DB_URL"] == "postgres://staging"
    assert merged["DEBUG"] == "true"


def test_promote_creates_dst_profile(store_file, profiles_dir):
    _seed_profile("staging", {"KEY": "val"}, store_file, profiles_dir)
    promote_profile(
        src_profile="staging",
        dst_profile="production",
        passphrase=PASS,
        store_path=store_file,
        profiles_dir=profiles_dir,
    )
    assert (profiles_dir / "production.enc").exists()


def test_promote_key_filter(store_file, profiles_dir):
    _seed_profile("staging", {"A": "1", "B": "2", "C": "3"}, store_file, profiles_dir)
    merged = promote_profile(
        src_profile="staging",
        dst_profile="production",
        passphrase=PASS,
        store_path=store_file,
        profiles_dir=profiles_dir,
        keys=["A", "C"],
    )
    assert set(merged.keys()) == {"A", "C"}


def test_promote_keep_target_strategy(store_file, profiles_dir):
    _seed_profile("staging", {"X": "from-staging"}, store_file, profiles_dir)
    _seed_profile("production", {"X": "from-production"}, store_file, profiles_dir)
    merged = promote_profile(
        src_profile="staging",
        dst_profile="production",
        passphrase=PASS,
        store_path=store_file,
        profiles_dir=profiles_dir,
        strategy=MergeStrategy.KEEP_TARGET,
    )
    assert merged["X"] == "from-production"


def test_promote_keep_source_strategy(store_file, profiles_dir):
    _seed_profile("staging", {"X": "from-staging"}, store_file, profiles_dir)
    _seed_profile("production", {"X": "from-production"}, store_file, profiles_dir)
    merged = promote_profile(
        src_profile="staging",
        dst_profile="production",
        passphrase=PASS,
        store_path=store_file,
        profiles_dir=profiles_dir,
        strategy=MergeStrategy.KEEP_SOURCE,
    )
    assert merged["X"] == "from-staging"


def test_promote_missing_src_raises(store_file, profiles_dir):
    with pytest.raises(PromoteError, match="Source profile"):
        promote_profile(
            src_profile="nonexistent",
            dst_profile="production",
            passphrase=PASS,
            store_path=store_file,
            profiles_dir=profiles_dir,
        )


def test_promote_missing_key_raises(store_file, profiles_dir):
    _seed_profile("staging", {"A": "1"}, store_file, profiles_dir)
    with pytest.raises(PromoteError, match="Keys not found"):
        promote_profile(
            src_profile="staging",
            dst_profile="production",
            passphrase=PASS,
            store_path=store_file,
            profiles_dir=profiles_dir,
            keys=["MISSING_KEY"],
        )
