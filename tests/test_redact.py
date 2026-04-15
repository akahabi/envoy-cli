"""Tests for envoy.redact."""

import pytest

from envoy.redact import RedactError, RedactResult, _is_sensitive, _mask_value, redact_vars


# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------

def test_is_sensitive_password():
    assert _is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_token():
    assert _is_sensitive("GITHUB_TOKEN") is True


def test_is_sensitive_api_key():
    assert _is_sensitive("STRIPE_API_KEY") is True


def test_is_sensitive_plain_key_is_false():
    assert _is_sensitive("APP_NAME") is False


# ---------------------------------------------------------------------------
# _mask_value
# ---------------------------------------------------------------------------

def test_mask_value_short_value_returns_stars():
    assert _mask_value("abc", visible_chars=4) == "***"


def test_mask_value_long_value_shows_prefix():
    result = _mask_value("supersecret", visible_chars=4)
    assert result.startswith("supe")
    assert result.endswith("***")


def test_mask_value_zero_visible_chars():
    result = _mask_value("hello", visible_chars=0)
    assert result == "***"


# ---------------------------------------------------------------------------
# redact_vars
# ---------------------------------------------------------------------------

def test_redact_vars_masks_sensitive_keys():
    vars_ = {"DB_PASSWORD": "hunter2", "APP_NAME": "myapp"}
    result = redact_vars(vars_)
    assert result.redacted["APP_NAME"] == "myapp"
    assert result.redacted["DB_PASSWORD"] != "hunter2"
    assert "DB_PASSWORD" in result.masked_keys


def test_redact_vars_extra_keys_are_masked():
    vars_ = {"MY_CUSTOM": "topsecret", "OTHER": "visible"}
    result = redact_vars(vars_, extra_keys=["MY_CUSTOM"])
    assert result.redacted["MY_CUSTOM"] != "topsecret"
    assert result.redacted["OTHER"] == "visible"


def test_redact_vars_original_unchanged():
    vars_ = {"SECRET_KEY": "abc123"}
    result = redact_vars(vars_)
    assert result.original["SECRET_KEY"] == "abc123"


def test_redact_vars_no_sensitive_keys():
    vars_ = {"HOST": "localhost", "PORT": "5432"}
    result = redact_vars(vars_)
    assert result.redaction_count == 0
    assert result.redacted == vars_


def test_redact_result_summary_with_masked_keys():
    vars_ = {"API_KEY": "sk-1234567890"}
    result = redact_vars(vars_)
    assert "API_KEY" in result.summary()
    assert "1" in result.summary() or "redacted" in result.summary()


def test_redact_result_summary_no_masked_keys():
    vars_ = {"REGION": "us-east-1"}
    result = redact_vars(vars_)
    assert result.summary() == "No values redacted."


def test_redact_vars_negative_visible_chars_raises():
    with pytest.raises(RedactError):
        redact_vars({"KEY": "value"}, visible_chars=-1)


def test_redact_vars_empty_store():
    result = redact_vars({})
    assert result.redacted == {}
    assert result.masked_keys == []
