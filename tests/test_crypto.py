"""Tests for envoy.crypto encryption/decryption utilities."""

import pytest
from envoy.crypto import encrypt, decrypt


PASSPHRASE = "super-secret-passphrase"
PLAINTEXT = "DATABASE_URL=postgres://user:pass@localhost/db"


def test_encrypt_returns_string():
    result = encrypt(PLAINTEXT, PASSPHRASE)
    assert isinstance(result, str)
    assert result != PLAINTEXT


def test_decrypt_roundtrip():
    blob = encrypt(PLAINTEXT, PASSPHRASE)
    recovered = decrypt(blob, PASSPHRASE)
    assert recovered == PLAINTEXT


def test_different_passphrases_produce_different_blobs():
    blob1 = encrypt(PLAINTEXT, "passphrase-one")
    blob2 = encrypt(PLAINTEXT, "passphrase-two")
    assert blob1 != blob2


def test_same_plaintext_produces_different_blobs():
    """Each call should use a fresh random salt and nonce."""
    blob1 = encrypt(PLAINTEXT, PASSPHRASE)
    blob2 = encrypt(PLAINTEXT, PASSPHRASE)
    assert blob1 != blob2


def test_wrong_passphrase_raises():
    blob = encrypt(PLAINTEXT, PASSPHRASE)
    with pytest.raises(Exception):
        decrypt(blob, "wrong-passphrase")


def test_tampered_blob_raises():
    blob = encrypt(PLAINTEXT, PASSPHRASE)
    tampered = blob[:-4] + "AAAA"
    with pytest.raises(Exception):
        decrypt(tampered, PASSPHRASE)
