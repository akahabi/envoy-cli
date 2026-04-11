import pytest
from click.testing import CliRunner
from unittest.mock import patch
from envoy.lint_cli import lint_cmd


@pytest.fixture
def runner():
    return CliRunner()


CLEAN_VARS = {"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "abc123"}
DIRTY_VARS = {"bad_key": "value", "EMPTY_VAL": "", "DATABASE_URL": "postgres://localhost/db"}


def test_check_no_issues(runner):
    with patch("envoy.lint_cli.load_store", return_value=CLEAN_VARS):
        result = runner.invoke(lint_cmd, ["check", "--store", "fake.store", "--passphrase", "pass"])
    assert result.exit_code == 0
    assert "No lint issues found" in result.output


def test_check_shows_errors(runner):
    with patch("envoy.lint_cli.load_store", return_value=DIRTY_VARS):
        result = runner.invoke(lint_cmd, ["check", "--store", "fake.store", "--passphrase", "pass"])
    assert "ERROR" in result.output or "WARN" in result.output
    assert result.exit_code == 1


def test_check_warnings_only_exit_zero_without_flag(runner):
    warn_only_vars = {"EMPTY_VAL": ""}
    with patch("envoy.lint_cli.load_store", return_value=warn_only_vars):
        result = runner.invoke(lint_cmd, ["check", "--store", "fake.store", "--passphrase", "pass"])
    assert "WARN" in result.output
    assert result.exit_code == 0


def test_check_warnings_exit_nonzero_with_warn_flag(runner):
    warn_only_vars = {"EMPTY_VAL": ""}
    with patch("envoy.lint_cli.load_store", return_value=warn_only_vars):
        result = runner.invoke(lint_cmd, ["check", "--store", "fake.store", "--passphrase", "pass", "--warn"])
    assert result.exit_code == 1


def test_check_load_failure(runner):
    with patch("envoy.lint_cli.load_store", side_effect=ValueError("bad passphrase")):
        result = runner.invoke(lint_cmd, ["check", "--store", "fake.store", "--passphrase", "wrong"])
    assert result.exit_code != 0
    assert "bad passphrase" in result.output


def test_check_summary_line(runner):
    with patch("envoy.lint_cli.load_store", return_value=DIRTY_VARS):
        result = runner.invoke(lint_cmd, ["check", "--store", "fake.store", "--passphrase", "pass"])
    assert "error(s)" in result.output
    assert "warning(s)" in result.output
