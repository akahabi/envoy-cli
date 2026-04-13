"""Tests for envoy.cli_secret_scan."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from envoy.cli_secret_scan import scan_cmd
from envoy.store import save_store


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def store_file(tmp_path):
    path = tmp_path / "test.env"
    return str(path)


def _invoke(runner, store_path, passphrase="pass", extra_args=None):
    args = ["check", "--store", store_path, "--passphrase", passphrase]
    if extra_args:
        args.extend(extra_args)
    return runner.invoke(scan_cmd, args)


def test_check_clean_store_exits_zero(runner, store_file):
    save_store(store_file, "pass", {"APP_NAME": "myapp", "PORT": "8080"})
    result = _invoke(runner, store_file)
    assert result.exit_code == 0
    assert "No suspicious" in result.output


def test_check_detects_aws_key(runner, store_file):
    save_store(store_file, "pass", {"CLOUD": "AKIAIOSFODNN7EXAMPLE"})
    result = _invoke(runner, store_file)
    assert result.exit_code == 1
    assert "suspicious" in result.output


def test_check_detects_sensitive_key_name(runner, store_file):
    save_store(store_file, "pass", {"DB_PASSWORD": "hunter2"})
    result = _invoke(runner, store_file)
    assert result.exit_code == 1


def test_check_no_key_names_flag_skips_name_check(runner, store_file):
    save_store(store_file, "pass", {"DB_PASSWORD": "hunter2"})
    result = _invoke(runner, store_file, extra_args=["--no-key-names"])
    # hunter2 doesn't match value-only patterns
    assert result.exit_code == 0


def test_check_wrong_passphrase_exits_nonzero(runner, store_file):
    save_store(store_file, "correct", {"X": "1"})
    result = _invoke(runner, store_file, passphrase="wrong")
    assert result.exit_code == 1
    assert "Error" in result.output


def test_check_missing_store_exits_nonzero(runner, tmp_path):
    missing = str(tmp_path / "nope.env")
    result = _invoke(runner, missing)
    assert result.exit_code == 1


def test_list_patterns_shows_output(runner):
    result = runner.invoke(scan_cmd, ["list-patterns"])
    assert result.exit_code == 0
    assert "AWS" in result.output
    assert "GitHub" in result.output
    assert "Stripe" in result.output
