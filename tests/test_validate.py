"""Tests for envoy.validate."""
import pytest
from envoy.validate import validate_vars, ValidationIssue


SCHEMA = {
    "DATABASE_URL": {"required": True, "min_length": 10},
    "PORT": {"required": True, "pattern": r"\d+"},
    "SECRET_KEY": {"required": True, "min_length": 16},
    "LOG_LEVEL": {"required": False, "pattern": r"DEBUG|INFO|WARNING|ERROR"},
    "OPTIONAL_BLANK": {"required": False, "warn_empty": True},
}


def _vars(**kwargs):
    base = {
        "DATABASE_URL": "postgres://localhost/db",
        "PORT": "5432",
        "SECRET_KEY": "supersecretkey1234",
    }
    base.update(kwargs)
    return base


def test_valid_vars_returns_ok():
    result = validate_vars(_vars(), SCHEMA)
    assert result.ok
    assert result.issues == []


def test_missing_required_key_is_error():
    vars_ = _vars()
    del vars_["DATABASE_URL"]
    result = validate_vars(vars_, SCHEMA)
    assert not result.ok
    keys = [i.key for i in result.errors]
    assert "DATABASE_URL" in keys


def test_pattern_mismatch_is_error():
    result = validate_vars(_vars(PORT="not-a-number"), SCHEMA)
    assert not result.ok
    assert any(i.key == "PORT" and "pattern" in i.message for i in result.errors)


def test_min_length_violation_is_error():
    result = validate_vars(_vars(SECRET_KEY="short"), SCHEMA)
    assert not result.ok
    assert any(i.key == "SECRET_KEY" and "minimum length" in i.message for i in result.errors)


def test_optional_key_absent_is_ok():
    result = validate_vars(_vars(), SCHEMA)
    assert result.ok


def test_optional_key_with_invalid_pattern_is_error():
    result = validate_vars(_vars(LOG_LEVEL="VERBOSE"), SCHEMA)
    assert not result.ok
    assert any(i.key == "LOG_LEVEL" for i in result.errors)


def test_warn_empty_produces_warning_not_error():
    result = validate_vars(_vars(OPTIONAL_BLANK="   "), SCHEMA)
    assert result.ok  # no errors
    assert any(i.key == "OPTIONAL_BLANK" and i.severity == "warning" for i in result.warnings)


def test_issue_str_format():
    issue = ValidationIssue("MY_KEY", "some problem", "error")
    assert str(issue) == "[ERROR] MY_KEY: some problem"


def test_multiple_errors_accumulated():
    vars_ = {"PORT": "bad"}  # missing DATABASE_URL and SECRET_KEY too
    result = validate_vars(vars_, SCHEMA)
    assert len(result.errors) >= 3
