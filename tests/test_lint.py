"""Tests for envoy.lint."""

import pytest
from envoy.lint import lint_vars, LintIssue, LintResult


def test_lint_clean_vars_returns_no_issues():
    result = lint_vars({"DATABASE_URL": "postgres://localhost/db", "PORT": "5432"})
    assert result.issues == []
    assert result.ok is True


def test_lint_lowercase_key_is_error():
    result = lint_vars({"database_url": "value"})
    errors = result.errors
    assert len(errors) == 1
    assert "database_url" == errors[0].key
    assert errors[0].severity == 'error'


def test_lint_key_starting_with_digit_is_error():
    result = lint_vars({"1_BAD": "value"})
    assert any(i.key == "1_BAD" and i.severity == 'error' for i in result.issues)


def test_lint_empty_value_is_warning():
    result = lint_vars({"SECRET_KEY": ""})
    warnings = result.warnings
    assert len(warnings) == 1
    assert warnings[0].key == "SECRET_KEY"
    assert warnings[0].severity == 'warning'


def test_lint_leading_whitespace_is_warning():
    result = lint_vars({"API_KEY": "  abc"})
    assert any(i.severity == 'warning' and 'whitespace' in i.message for i in result.issues)


def test_lint_trailing_whitespace_is_warning():
    result = lint_vars({"API_KEY": "abc  "})
    assert any(i.severity == 'warning' and 'whitespace' in i.message for i in result.issues)


def test_lint_newline_in_value_is_error():
    result = lint_vars({"PRIVATE_KEY": "line1\nline2"})
    errors = result.errors
    assert any(i.key == "PRIVATE_KEY" and 'newline' in i.message for i in errors)


def test_lint_multiple_issues_accumulated():
    result = lint_vars({
        "good_key": "",       # bad key (error) + empty value (warning)
        "GOOD_KEY": "value",  # clean
    })
    assert len(result.errors) >= 1
    assert len(result.warnings) >= 1


def test_lint_ok_false_when_errors_present():
    result = lint_vars({"bad-key": "value"})
    assert result.ok is False


def test_lint_issue_str_format():
    issue = LintIssue(key="FOO", severity="error", message="Something wrong.")
    assert str(issue) == "[ERROR] FOO: Something wrong."


def test_lint_empty_dict_returns_ok():
    result = lint_vars({})
    assert result.ok is True
    assert result.issues == []
