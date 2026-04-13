"""Tests for envoy.env_check module."""

from __future__ import annotations

from pathlib import Path

import pytest

from envoy.env_check import EnvCheckError, check_against_example
from envoy.store import save_store


PASSPHRASE = "test-passphrase"


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    path = tmp_path / ".envoy"
    save_store(path, PASSPHRASE, {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret"})
    return path


@pytest.fixture()
def example_file(tmp_path: Path) -> Path:
    path = tmp_path / ".env.example"
    path.write_text("DB_HOST=\nDB_PORT=\nAPI_KEY=\n", encoding="utf-8")
    return path


def test_check_all_present(store_file: Path, example_file: Path) -> None:
    result = check_against_example(store_file, PASSPHRASE, example_file)
    assert result.ok
    assert result.missing == []
    assert result.extra == []
    assert sorted(result.present) == ["API_KEY", "DB_HOST", "DB_PORT"]


def test_check_detects_missing_key(store_file: Path, tmp_path: Path) -> None:
    example = tmp_path / ".env.example"
    example.write_text("DB_HOST=\nDB_PORT=\nAPI_KEY=\nSECRET_KEY=\n", encoding="utf-8")
    result = check_against_example(store_file, PASSPHRASE, example)
    assert not result.ok
    assert "SECRET_KEY" in result.missing


def test_check_detects_extra_key(store_file: Path, tmp_path: Path) -> None:
    example = tmp_path / ".env.example"
    example.write_text("DB_HOST=\nDB_PORT=\n", encoding="utf-8")
    result = check_against_example(store_file, PASSPHRASE, example)
    assert not result.ok
    assert "API_KEY" in result.extra


def test_ignore_extra_flag(store_file: Path, tmp_path: Path) -> None:
    example = tmp_path / ".env.example"
    example.write_text("DB_HOST=\nDB_PORT=\n", encoding="utf-8")
    result = check_against_example(store_file, PASSPHRASE, example, ignore_extra=True)
    assert result.ok
    assert result.extra == []


def test_missing_example_file_raises(store_file: Path, tmp_path: Path) -> None:
    with pytest.raises(EnvCheckError, match="Example file not found"):
        check_against_example(store_file, PASSPHRASE, tmp_path / "nonexistent.example")


def test_missing_store_file_raises(tmp_path: Path, example_file: Path) -> None:
    with pytest.raises(EnvCheckError, match="Store file not found"):
        check_against_example(tmp_path / "no_store", PASSPHRASE, example_file)


def test_summary_all_match(store_file: Path, example_file: Path) -> None:
    result = check_against_example(store_file, PASSPHRASE, example_file)
    assert "All vars match." in result.summary()


def test_summary_shows_missing(store_file: Path, tmp_path: Path) -> None:
    example = tmp_path / ".env.example"
    example.write_text("DB_HOST=\nMISSING_VAR=\n", encoding="utf-8")
    result = check_against_example(store_file, PASSPHRASE, example, ignore_extra=True)
    assert "MISSING_VAR" in result.summary()


def test_summary_shows_extra(store_file: Path, tmp_path: Path) -> None:
    """Verify that the summary includes extra keys when they are present."""
    example = tmp_path / ".env.example"
    example.write_text("DB_HOST=\nDB_PORT=\n", encoding="utf-8")
    result = check_against_example(store_file, PASSPHRASE, example)
    assert "API_KEY" in result.summary()
