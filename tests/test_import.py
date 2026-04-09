"""Tests for envoy/import_.py and the import CLI command."""

import json
import pytest
from click.testing import CliRunner
from pathlib import Path

from envoy.import_ import from_dotenv, from_json, from_shell, load, ImportError as EnvoyImportError
from envoy.cli_import import file_cmd
from envoy.store import get_env_vars, load_store


# ---------------------------------------------------------------------------
# Unit tests for parsers
# ---------------------------------------------------------------------------

def test_from_dotenv_simple():
    result = from_dotenv("FOO=bar\nBAZ=qux\n")
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_from_dotenv_strips_quotes():
    result = from_dotenv('KEY="hello world"\nOTHER=\'value\'')
    assert result["KEY"] == "hello world"
    assert result["OTHER"] == "value"


def test_from_dotenv_ignores_comments_and_blanks():
    result = from_dotenv("# comment\n\nFOO=1\n")
    assert result == {"FOO": "1"}


def test_from_dotenv_invalid_key_raises():
    with pytest.raises(EnvoyImportError, match="invalid key name"):
        from_dotenv("123BAD=value")


def test_from_dotenv_missing_equals_raises():
    with pytest.raises(EnvoyImportError, match="no '=' found"):
        from_dotenv("NOEQUALS")


def test_from_json_simple():
    text = json.dumps({"A": "1", "B": "two"})
    assert from_json(text) == {"A": "1", "B": "two"}


def test_from_json_non_string_value_raises():
    with pytest.raises(EnvoyImportError, match="must be a string"):
        from_json(json.dumps({"KEY": 42}))


def test_from_json_non_object_raises():
    with pytest.raises(EnvoyImportError, match="root must be an object"):
        from_json(json.dumps(["not", "an", "object"]))


def test_from_shell_export_prefix():
    result = from_shell("export FOO=bar\nexport BAZ='hello world'")
    assert result["FOO"] == "bar"
    assert result["BAZ"] == "hello world"


def test_from_shell_without_export():
    result = from_shell("KEY=value")
    assert result == {"KEY": "value"}


def test_load_auto_detects_dotenv(tmp_path: Path):
    f = tmp_path / "vars.env"
    f.write_text("HELLO=world\n")
    assert load(str(f)) == {"HELLO": "world"}


def test_load_auto_detects_json(tmp_path: Path):
    f = tmp_path / "vars.json"
    f.write_text(json.dumps({"X": "1"}))
    assert load(str(f)) == {"X": "1"}


def test_load_missing_file_raises():
    with pytest.raises(EnvoyImportError, match="not found"):
        load("/nonexistent/path/vars.env")


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_import_adds_vars(tmp_path: Path, runner: CliRunner, monkeypatch):
    monkeypatch.setenv("ENVOY_STORE_DIR", str(tmp_path))
    env_file = tmp_path / "sample.env"
    env_file.write_text("NEW_KEY=hello\n")

    result = runner.invoke(
        file_cmd,
        [str(env_file), "--env", "local", "--passphrase", "secret"],
    )
    assert result.exit_code == 0, result.output
    assert "Added:   1" in result.output


def test_cli_import_dry_run_does_not_write(tmp_path: Path, runner: CliRunner, monkeypatch):
    monkeypatch.setenv("ENVOY_STORE_DIR", str(tmp_path))
    env_file = tmp_path / "sample.env"
    env_file.write_text("DRY_KEY=dryval\n")

    result = runner.invoke(
        file_cmd,
        [str(env_file), "--env", "local", "--passphrase", "secret", "--dry-run"],
    )
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    # Store file should not exist
    assert not (tmp_path / "local.env").exists()


def test_cli_import_skips_without_overwrite(tmp_path: Path, runner: CliRunner, monkeypatch):
    monkeypatch.setenv("ENVOY_STORE_DIR", str(tmp_path))
    env_file = tmp_path / "sample.env"
    env_file.write_text("EXISTING=new_value\n")

    # First import to seed the store
    runner.invoke(file_cmd, [str(env_file), "--env", "local", "--passphrase", "secret"])
    # Second import without --overwrite
    result = runner.invoke(
        file_cmd,
        [str(env_file), "--env", "local", "--passphrase", "secret"],
    )
    assert result.exit_code == 0
    assert "Skipped: 1" in result.output
