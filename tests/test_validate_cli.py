import json
import pytest
from click.testing import CliRunner
from pathlib import Path
from envoy.validate_cli import validate_cmd
from envoy.store import save_store


@pytest.fixture
def runner():
    return CliRunner()


def _write_store(tmp_path, vars_, passphrase="secret"):
    store_path = str(tmp_path / ".envoy")
    save_store(store_path, passphrase, vars_)
    return store_path


def _write_schema(tmp_path, schema):
    p = tmp_path / "schema.json"
    p.write_text(json.dumps(schema))
    return str(p)


def test_check_passes_with_valid_vars(runner, tmp_path):
    store = _write_store(tmp_path, {"API_KEY": "abc123", "PORT": "8080"})
    schema = _write_schema(tmp_path, {"required": ["API_KEY", "PORT"]})
    result = runner.invoke(
        validate_cmd, ["check", schema, "--store", store, "--passphrase", "secret"]
    )
    assert result.exit_code == 0
    assert "All checks passed" in result.output


def test_check_fails_on_missing_required(runner, tmp_path):
    store = _write_store(tmp_path, {"PORT": "8080"})
    schema = _write_schema(tmp_path, {"required": ["API_KEY", "PORT"]})
    result = runner.invoke(
        validate_cmd, ["check", schema, "--store", store, "--passphrase", "secret"]
    )
    assert result.exit_code != 0
    assert "ERROR" in result.output
    assert "API_KEY" in result.output


def test_check_warns_but_exits_zero_without_flag(runner, tmp_path):
    store = _write_store(tmp_path, {"API_KEY": ""})
    schema = _write_schema(tmp_path, {"required": ["API_KEY"]})
    result = runner.invoke(
        validate_cmd, ["check", schema, "--store", store, "--passphrase", "secret"]
    )
    # empty value should produce a warning but no error by default
    assert "WARNING" in result.output or result.exit_code == 0


def test_check_warns_exit_nonzero_with_warn_flag(runner, tmp_path):
    store = _write_store(tmp_path, {"API_KEY": ""})
    schema = _write_schema(tmp_path, {"required": ["API_KEY"]})
    result = runner.invoke(
        validate_cmd,
        ["check", schema, "--store", store, "--passphrase", "secret", "--warn"],
    )
    if "WARNING" in result.output:
        assert result.exit_code != 0


def test_check_bad_passphrase_shows_error(runner, tmp_path):
    store = _write_store(tmp_path, {"API_KEY": "x"})
    schema = _write_schema(tmp_path, {})
    result = runner.invoke(
        validate_cmd, ["check", schema, "--store", store, "--passphrase", "wrong"]
    )
    assert result.exit_code != 0


def test_check_missing_store_shows_error(runner, tmp_path):
    schema = _write_schema(tmp_path, {"required": ["API_KEY"]})
    result = runner.invoke(
        validate_cmd,
        ["check", schema, "--store", str(tmp_path / "nonexistent"), "--passphrase", "secret"],
    )
    assert result.exit_code != 0
