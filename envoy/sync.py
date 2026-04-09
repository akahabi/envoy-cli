"""Sync module for pushing/pulling .env files to/from remote profiles."""

import json
import os
from pathlib import Path
from typing import Optional

from envoy.crypto import encrypt, decrypt
from envoy.store import load_store, save_store

PROFILES_DIR = Path.home() / ".envoy" / "profiles"


def _profile_path(profile: str) -> Path:
    """Return the file path for a named profile."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    return PROFILES_DIR / f"{profile}.enc"


def push_profile(store_path: str, profile: str, passphrase: str) -> None:
    """Encrypt the current store and save it as a named profile snapshot."""
    store = load_store(store_path, passphrase)
    plaintext = json.dumps(store)
    blob = encrypt(plaintext, passphrase)
    dest = _profile_path(profile)
    dest.write_text(blob)


def pull_profile(store_path: str, profile: str, passphrase: str) -> None:
    """Load a named profile snapshot and merge it into the current store."""
    src = _profile_path(profile)
    if not src.exists():
        raise FileNotFoundError(f"Profile '{profile}' not found at {src}")
    blob = src.read_text()
    plaintext = decrypt(blob, passphrase)
    remote_store = json.loads(plaintext)
    local_store = load_store(store_path, passphrase)
    # Remote values take precedence
    local_store.update(remote_store)
    save_store(store_path, local_store, passphrase)


def list_profiles() -> list[str]:
    """Return names of all saved profiles."""
    if not PROFILES_DIR.exists():
        return []
    return [p.stem for p in PROFILES_DIR.glob("*.enc")]


def delete_profile(profile: str) -> None:
    """Delete a named profile snapshot."""
    path = _profile_path(profile)
    if not path.exists():
        raise FileNotFoundError(f"Profile '{profile}' not found")
    path.unlink()
