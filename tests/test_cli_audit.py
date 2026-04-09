"""Tests for envoy.cli_audit CLI commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envoy.cli_audit import audit


@pytest.fixture
def runner():
    return CliRunner()


def test_log_no_events(runner):
    with patch("envoy.cli_audit.read_events", return_value=[]):
        result = runner.invoke(audit, ["log"])
    assert result.exit_code == 0
    assert "No audit events found" in result.output


def test_log_shows_events(runner):
    events = [
        {
            "timestamp": "2024-01-01T00:00:00+00:00",
            "action": "set",
            "environment": "local",
            "key": "API_KEY",
            "profile": None,
        }
    ]
    with patch("envoy.cli_audit.read_events", return_value=events):
        result = runner.invoke(audit, ["log"])
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "set" in result.output
    assert "local" in result.output


def test_log_with_profile_shown(runner):
    events = [
        {
            "timestamp": "2024-01-01T00:00:00+00:00",
            "action": "push",
            "environment": "staging",
            "key": "DB_URL",
            "profile": "myapp",
        }
    ]
    with patch("envoy.cli_audit.read_events", return_value=events):
        result = runner.invoke(audit, ["log"])
    assert "[myapp]" in result.output


def test_log_passes_filters(runner):
    with patch("envoy.cli_audit.read_events", return_value=[]) as mock_read:
        runner.invoke(audit, ["log", "--env", "staging", "--action", "push", "--limit", "5"])
    mock_read.assert_called_once_with(environment="staging", action="push", limit=5)


def test_clear_with_confirmation(runner):
    with patch("envoy.cli_audit.clear_events") as mock_clear:
        result = runner.invoke(audit, ["clear"], input="y\n")
    assert result.exit_code == 0
    assert "cleared" in result.output
    mock_clear.assert_called_once()


def test_clear_aborted(runner):
    with patch("envoy.cli_audit.clear_events") as mock_clear:
        result = runner.invoke(audit, ["clear"], input="n\n")
    assert result.exit_code != 0 or "Aborted" in result.output
    mock_clear.assert_not_called()
