"""Local encrypted storage for .env files."""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from envoy.crypto import encrypt, decrypt


DEFAULT_STORE_PATH = Path.home() / ".envoy" / "store.enc"


def _load_raw(store_path: Path) -> str:
    if not store_path.exists():
        return ""
    return store_path.read_text(encoding="utf-8")


def load_store(passphrase: str, store_path: Optional[Path] = None) -> Dict[str, Dict[str, str]]:
    """Load and decrypt the env store. Returns a dict keyed by environment name."""
    path = store_path or DEFAULT_STORE_PATH
    raw = _load_raw(path)
    if not raw:
        return {}
    plaintext = decrypt(raw, passphrase)
    return json.loads(plaintext)


def save_store(
    data: Dict[str, Dict[str, str]],
    passphrase: str,
    store_path: Optional[Path] = None,
) -> None:
    """Encrypt and persist the env store to disk."""
    path = store_path or DEFAULT_STORE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    plaintext = json.dumps(data, indent=2)
    encoded = encrypt(plaintext, passphrase)
    path.write_text(encoded, encoding="utf-8")


def set_env_var(
    environment: str,
    key: str,
    value: str,
    passphrase: str,
    store_path: Optional[Path] = None,
) -> None:
    """Set a single variable in the given environment."""
    store = load_store(passphrase, store_path)
    store.setdefault(environment, {})[key] = value
    save_store(store, passphrase, store_path)


def get_env_vars(
    environment: str,
    passphrase: str,
    store_path: Optional[Path] = None,
) -> Dict[str, str]:
    """Retrieve all variables for the given environment."""
    store = load_store(passphrase, store_path)
    return store.get(environment, {})
