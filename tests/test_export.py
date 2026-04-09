"""Tests for envoy.export rendering helpers."""

import json

import pytest

from envoy.export import render, to_dotenv, to_json, to_shell, SUPPORTED_FORMATS


SAMPLE = {
    "DATABASE_URL": "postgres://localhost/db",
    "SECRET_KEY": "s3cr3t",
    "APP_NAME": "my app",
}


# ---------------------------------------------------------------------------
# to_dotenv
# ---------------------------------------------------------------------------

def test_dotenv_simple_values():
    result = to_dotenv({"FOO": "bar", "BAZ": "qux"})
    assert "FOO=bar" in result
    assert "BAZ=qux" in result


def test_dotenv_quotes_values_with_spaces():
    result = to_dotenv({"KEY": "hello world"})
    assert 'KEY="hello world"' in result


def test_dotenv_quotes_values_with_dollar():
    result = to_dotenv({"KEY": "$HOME"})
    assert 'KEY="$HOME"' in result


def test_dotenv_sorted_output():
    result = to_dotenv({"Z_VAR": "z", "A_VAR": "a"})
    lines = [l for l in result.splitlines() if l]
    assert lines[0].startswith("A_VAR")
    assert lines[1].startswith("Z_VAR")


def test_dotenv_empty_vars():
    assert to_dotenv({}) == ""


# ---------------------------------------------------------------------------
# to_json
# ---------------------------------------------------------------------------

def test_json_is_valid_json():
    result = to_json(SAMPLE)
    parsed = json.loads(result)
    assert parsed["SECRET_KEY"] == "s3cr3t"


def test_json_sorted_keys():
    result = to_json({"Z": "1", "A": "2"})
    parsed = json.loads(result)
    assert list(parsed.keys()) == ["A", "Z"]


# ---------------------------------------------------------------------------
# to_shell
# ---------------------------------------------------------------------------

def test_shell_export_prefix():
    result = to_shell({"FOO": "bar"})
    assert result.strip() == "export FOO='bar'"


def test_shell_escapes_single_quotes():
    result = to_shell({"MSG": "it's alive"})
    assert "export MSG='it'\\''s alive'" in result


def test_shell_empty_vars():
    assert to_shell({}) == ""


# ---------------------------------------------------------------------------
# render dispatcher
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fmt", ["dotenv", "json", "shell"])
def test_render_accepts_all_supported_formats(fmt):
    result = render({"KEY": "value"}, fmt)
    assert isinstance(result, str)
    assert len(result) > 0


def test_render_case_insensitive():
    assert render({"K": "v"}, "JSON") == render({"K": "v"}, "json")


def test_render_raises_on_unknown_format():
    with pytest.raises(ValueError, match="Unsupported format"):
        render({"K": "v"}, "yaml")


def test_supported_formats_constant():
    assert "dotenv" in SUPPORTED_FORMATS
    assert "json" in SUPPORTED_FORMATS
    assert "shell" in SUPPORTED_FORMATS
