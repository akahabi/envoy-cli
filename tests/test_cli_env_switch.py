import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from envoy.env_switch_cli import env_switch_cmd
from envoy.env_switch import SwitchError


@pytest.fixture
def runner():
    return CliRunner()


def _invoke(runner, *args, passphrase="secret"):
    return runner.invoke(
        env_switch_cmd,
        list(args) + ["--passphrase", passphrase],
        catch_exceptions=False,
    )


def test_switch_success(runner):
    with patch("envoy.env_switch_cli.switch_env", return_value={"A": "1", "B": "2"}) as mock_sw:
        result = _invoke(runner, "to", "staging", "--store", ".envoy", "--profiles-dir", ".profiles")
    assert result.exit_code == 0
    assert "Switched to profile 'staging'" in result.output
    assert "2 variable(s) loaded" in result.output
    mock_sw.assert_called_once_with(
        store_path=".envoy",
        profiles_dir=".profiles",
        profile_name="staging",
        passphrase="secret",
    )


def test_switch_failure_exits_nonzero(runner):
    with patch("envoy.env_switch_cli.switch_env", side_effect=SwitchError("profile not found")):
        result = runner.invoke(
            env_switch_cmd,
            ["to", "missing", "--passphrase", "secret"],
            catch_exceptions=False,
        )
    assert result.exit_code == 1
    assert "profile not found" in result.output


def test_current_shows_name(runner):
    with patch("envoy.env_switch_cli.current_env", return_value="production"):
        result = _invoke(runner, "current", "--store", ".envoy")
    assert result.exit_code == 0
    assert "production" in result.output


def test_current_no_env_set(runner):
    with patch("envoy.env_switch_cli.current_env", return_value=None):
        result = _invoke(runner, "current", "--store", ".envoy")
    assert result.exit_code == 0
    assert "No active environment" in result.output


def test_current_switch_error_exits_nonzero(runner):
    with patch("envoy.env_switch_cli.current_env", side_effect=SwitchError("bad passphrase")):
        result = runner.invoke(
            env_switch_cmd,
            ["current", "--passphrase", "wrong"],
            catch_exceptions=False,
        )
    assert result.exit_code == 1
    assert "bad passphrase" in result.output
