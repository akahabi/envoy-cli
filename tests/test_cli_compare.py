"""Tests for envoy.cli_compare CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch

from envoy.cli_compare import compare_cmd
from envoy.diff import DiffResult


SAMPLE_RESULT = [
    DiffResult(key="KEY1", status="unchanged", source_value="v1", target_value="v1"),
    DiffResult(key="KEY2", status="changed", source_value="old", target_value="new"),
    DiffResult(key="KEY3", status="added", source_value=None, target_value="x"),
]


@pytest.fixture()
def runner():
    return CliRunner()


def test_store_profile_success(runner):
    with patch("envoy.cli_compare.compare_store_to_profile", return_value=SAMPLE_RESULT):
        result = runner.invoke(
            compare_cmd,
            ["store-profile", "staging", "--store-pass", "p1", "--profile-pass", "p2"],
        )
    assert result.exit_code == 0
    assert "KEY2" in result.output
    assert "KEY3" in result.output


def test_store_profile_shows_unchanged_when_flag_set(runner):
    with patch("envoy.cli_compare.compare_store_to_profile", return_value=SAMPLE_RESULT):
        result = runner.invoke(
            compare_cmd,
            ["store-profile", "staging", "--store-pass", "p", "--profile-pass", "p", "--show-unchanged"],
        )
    assert "KEY1" in result.output


def test_store_profile_failure(runner):
    from envoy.compare import CompareError
    with patch("envoy.cli_compare.compare_store_to_profile", side_effect=CompareError("boom")):
        result = runner.invoke(
            compare_cmd,
            ["store-profile", "staging", "--store-pass", "p", "--profile-pass", "p"],
        )
    assert result.exit_code == 1
    assert "boom" in result.output


def test_profiles_success(runner):
    with patch("envoy.cli_compare.compare_profiles", return_value=SAMPLE_RESULT):
        result = runner.invoke(
            compare_cmd,
            ["profiles", "staging", "prod", "--pass-a", "p1", "--pass-b", "p2"],
        )
    assert result.exit_code == 0
    assert "KEY2" in result.output


def test_profiles_failure(runner):
    from envoy.compare import CompareError
    with patch("envoy.cli_compare.compare_profiles", side_effect=CompareError("not found")):
        result = runner.invoke(
            compare_cmd,
            ["profiles", "a", "b", "--pass-a", "p", "--pass-b", "p"],
        )
    assert result.exit_code == 1
    assert "not found" in result.output


def test_in_sync_message_shown(runner):
    no_diff = [
        DiffResult(key="K", status="unchanged", source_value="v", target_value="v")
    ]
    with patch("envoy.cli_compare.compare_profiles", return_value=no_diff):
        result = runner.invoke(
            compare_cmd,
            ["profiles", "a", "b", "--pass-a", "p", "--pass-b", "p"],
        )
    assert "in sync" in result.output
