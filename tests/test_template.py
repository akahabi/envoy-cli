"""Tests for envoy.template module."""

import pytest
from click.testing import CliRunner

from envoy.cli_template import template_cmd
from envoy.template import TemplateError, extract_placeholders, render_template


# --- render_template ---

def test_render_simple_substitution():
    result = render_template("Hello, ${NAME}!", {"NAME": "World"})
    assert result == "Hello, World!"


def test_render_multiple_vars():
    result = render_template("${A} + ${B}", {"A": "foo", "B": "bar"})
    assert result == "foo + bar"


def test_render_uses_default_when_missing():
    result = render_template("${PORT:8080}", {})
    assert result == "8080"


def test_render_var_overrides_default():
    result = render_template("${PORT:8080}", {"PORT": "9090"})
    assert result == "9090"


def test_render_empty_default_allowed():
    result = render_template("${OPTIONAL:}", {})
    assert result == ""


def test_render_missing_no_default_raises():
    with pytest.raises(TemplateError, match="MISSING"):
        render_template("${MISSING}", {})


def test_render_multiple_missing_reported():
    with pytest.raises(TemplateError) as exc_info:
        render_template("${A} ${B}", {})
    msg = str(exc_info.value)
    assert "A" in msg
    assert "B" in msg


def test_render_no_placeholders_returns_unchanged():
    text = "plain text without variables"
    assert render_template(text, {}) == text


# --- extract_placeholders ---

def test_extract_returns_names_and_defaults():
    result = extract_placeholders("${FOO} ${BAR:baz}")
    assert result == {"FOO": None, "BAR": "baz"}


def test_extract_deduplicates():
    result = extract_placeholders("${X} ${X:fallback}")
    assert list(result.keys()) == ["X"]
    assert result["X"] is None  # first occurrence wins


def test_extract_empty_template():
    assert extract_placeholders("") == {}


# --- CLI ---

@pytest.fixture()
def runner():
    return CliRunner()


def test_inspect_lists_placeholders(runner, tmp_path):
    tmpl = tmp_path / "app.env.tmpl"
    tmpl.write_text("DB_HOST=${DB_HOST:localhost}\nDB_PORT=${DB_PORT}\n")
    result = runner.invoke(template_cmd, ["inspect", str(tmpl)])
    assert result.exit_code == 0
    assert "DB_HOST" in result.output
    assert "DB_PORT" in result.output
    assert "localhost" in result.output


def test_inspect_no_placeholders(runner, tmp_path):
    tmpl = tmp_path / "plain.txt"
    tmpl.write_text("nothing special here")
    result = runner.invoke(template_cmd, ["inspect", str(tmpl)])
    assert result.exit_code == 0
    assert "No placeholders" in result.output
