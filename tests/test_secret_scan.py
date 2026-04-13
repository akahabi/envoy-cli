"""Tests for envoy.secret_scan."""

from __future__ import annotations

import pytest

from envoy.secret_scan import ScanHit, ScanResult, scan_vars, value_preview


# ---------------------------------------------------------------------------
# value_preview
# ---------------------------------------------------------------------------

def test_value_preview_short_value_is_all_stars():
    assert value_preview("abc") == "***"


def test_value_preview_long_value_shows_prefix_and_stars():
    preview = value_preview("supersecretvalue")
    assert preview.startswith("sup")
    assert "***" in preview


# ---------------------------------------------------------------------------
# scan_vars — clean inputs
# ---------------------------------------------------------------------------

def test_clean_vars_returns_no_hits():
    vars_ = {"APP_NAME": "myapp", "PORT": "8080", "DEBUG": "true"}
    result = scan_vars(vars_)
    assert result.clean
    assert result.hits == []


def test_clean_result_summary_says_no_issues():
    result = ScanResult(hits=[])
    assert "No suspicious" in result.summary()


# ---------------------------------------------------------------------------
# scan_vars — key-name patterns
# ---------------------------------------------------------------------------

def test_key_named_password_triggers_hit():
    vars_ = {"DB_PASSWORD": "hunter2"}
    result = scan_vars(vars_, key_patterns=True)
    assert not result.clean
    assert result.hits[0].key == "DB_PASSWORD"


def test_key_named_secret_triggers_hit():
    vars_ = {"APP_SECRET": "abc123"}
    result = scan_vars(vars_, key_patterns=True)
    assert not result.clean


def test_key_name_patterns_disabled_skips_name_check():
    vars_ = {"DB_PASSWORD": "hunter2"}
    result = scan_vars(vars_, key_patterns=False)
    # Value "hunter2" doesn't match hex/base64/specific token patterns
    assert result.clean


# ---------------------------------------------------------------------------
# scan_vars — value patterns
# ---------------------------------------------------------------------------

def test_aws_access_key_pattern_detected():
    vars_ = {"CLOUD_KEY": "AKIAIOSFODNN7EXAMPLE"}
    result = scan_vars(vars_)
    assert not result.clean
    assert "AWS" in result.hits[0].reason


def test_stripe_live_key_detected():
    vars_ = {"PAYMENT_KEY": "sk_live_AbCdEfGhIjKlMnOpQrStUv"}
    result = scan_vars(vars_)
    assert not result.clean
    assert "Stripe" in result.hits[0].reason


def test_github_pat_detected():
    vars_ = {"GH_TOKEN": "ghp_" + "A" * 36}
    result = scan_vars(vars_)
    assert not result.clean
    assert "GitHub" in result.hits[0].reason


def test_hex_hash_value_detected():
    vars_ = {"CHECKSUM": "a" * 40}
    result = scan_vars(vars_)
    assert not result.clean


# ---------------------------------------------------------------------------
# ScanResult.summary
# ---------------------------------------------------------------------------

def test_summary_lists_all_hits():
    hits = [
        ScanHit(key="A", value="val1", reason="reason one"),
        ScanHit(key="B", value="val2", reason="reason two"),
    ]
    result = ScanResult(hits=hits)
    summary = result.summary()
    assert "2 suspicious" in summary
    assert "A" in summary
    assert "B" in summary


def test_scan_hit_str_masks_value():
    hit = ScanHit(key="SECRET", value="supersensitive", reason="test")
    text = str(hit)
    assert "supersensitive" not in text
    assert "SECRET" in text
