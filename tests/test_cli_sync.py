"""Tests for CLI sync commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from envoy.cli_sync import sync


@pytest.fixture()
def runner():
    return CliRunner()


def test_push_success(runner):
    with patch("envoy.cli_sync.push_profile") as mock_push:
        result = runner.invoke(
            sync, ["push", "staging", "--store", "my.store", "--passphrase", "secret"]
        )
        mock_push.assert_called_once_with("my.store", "staging", "secret")
        assert "Pushed store to profile 'staging'" in result.output
        assert result.exit_code == 0


def test_push_failure(runner):
    with patch("envoy.cli_sync.push_profile", side_effect=Exception("disk error")):
        result = runner.invoke(
            sync, ["push", "staging", "--store", "my.store", "--passphrase", "secret"]
        )
        assert result.exit_code == 1
        assert "disk error" in result.output


def test_pull_success(runner):
    with patch("envoy.cli_sync.pull_profile") as mock_pull:
        result = runner.invoke(
            sync, ["pull", "staging", "--store", "my.store", "--passphrase", "secret"]
        )
        mock_pull.assert_called_once_with("my.store", "staging", "secret")
        assert "Pulled profile 'staging'" in result.output
        assert result.exit_code == 0


def test_pull_not_found(runner):
    with patch("envoy.cli_sync.pull_profile", side_effect=FileNotFoundError("Profile 'x' not found")):
        result = runner.invoke(
            sync, ["pull", "x", "--store", "my.store", "--passphrase", "secret"]
        )
        assert result.exit_code == 1
        assert "not found" in result.output


def test_list_no_profiles(runner):
    with patch("envoy.cli_sync.list_profiles", return_value=[]):
        result = runner.invoke(sync, ["list"])
        assert "No profiles found" in result.output
        assert result.exit_code == 0


def test_list_with_profiles(runner):
    with patch("envoy.cli_sync.list_profiles", return_value=["staging", "production"]):
        result = runner.invoke(sync, ["list"])
        assert "staging" in result.output
        assert "production" in result.output


def test_delete_success(runner):
    with patch("envoy.cli_sync.delete_profile") as mock_del:
        result = runner.invoke(sync, ["delete", "staging"])
        mock_del.assert_called_once_with("staging")
        assert "Deleted profile 'staging'" in result.output
        assert result.exit_code == 0


def test_delete_not_found(runner):
    with patch("envoy.cli_sync.delete_profile", side_effect=FileNotFoundError("Profile 'x' not found")):
        result = runner.invoke(sync, ["delete", "x"])
        assert result.exit_code == 1
