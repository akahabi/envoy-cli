"""Tests for envoy.search."""

from __future__ import annotations

import pytest

from envoy.store import save_store, set_env_var
from envoy.tag import add_tag
from envoy.search import SearchError, SearchResult, search_vars

PASS = "hunter2"


@pytest.fixture()
def store_file(tmp_path):
    p = tmp_path / "store.env"
    save_store(str(p), PASS, {})
    set_env_var(str(p), PASS, "DB_HOST", "localhost")
    set_env_var(str(p), PASS, "DB_PORT", "5432")
    set_env_var(str(p), PASS, "API_KEY", "abc123secret")
    set_env_var(str(p), PASS, "LOG_LEVEL", "debug")
    return str(p)


def test_key_glob_matches_prefix(store_file):
    result = search_vars(store_file, PASS, key_pattern="DB_*")
    assert set(result.matches.keys()) == {"DB_HOST", "DB_PORT"}


def test_key_glob_no_match(store_file):
    result = search_vars(store_file, PASS, key_pattern="MISSING_*")
    assert result.is_empty()


def test_value_pattern_matches(store_file):
    result = search_vars(store_file, PASS, value_pattern=r"\d+")
    assert "DB_PORT" in result.matches
    assert "API_KEY" in result.matches


def test_value_pattern_case_insensitive_by_default(store_file):
    result = search_vars(store_file, PASS, value_pattern="DEBUG")
    assert "LOG_LEVEL" in result.matches


def test_value_pattern_case_sensitive(store_file):
    result = search_vars(store_file, PASS, value_pattern="DEBUG", case_sensitive=True)
    assert result.is_empty()


def test_invalid_value_pattern_raises(store_file):
    with pytest.raises(SearchError, match="Invalid value pattern"):
        search_vars(store_file, PASS, value_pattern="[unclosed")


def test_tag_filter(store_file):
    add_tag(store_file, PASS, "DB_HOST", "infra")
    result = search_vars(store_file, PASS, tag="infra")
    assert set(result.matches.keys()) == {"DB_HOST"}


def test_tag_and_key_combined(store_file):
    add_tag(store_file, PASS, "DB_HOST", "infra")
    add_tag(store_file, PASS, "DB_PORT", "infra")
    result = search_vars(store_file, PASS, key_pattern="DB_H*", tag="infra")
    assert set(result.matches.keys()) == {"DB_HOST"}


def test_summary_with_matches(store_file):
    result = search_vars(store_file, PASS, key_pattern="DB_*")
    assert "2 matches" in result.summary()


def test_summary_no_matches(store_file):
    result = search_vars(store_file, PASS, key_pattern="NOPE_*")
    assert "No matches" in result.summary()


def test_result_count(store_file):
    result = search_vars(store_file, PASS, key_pattern="*")
    assert result.count == 4
