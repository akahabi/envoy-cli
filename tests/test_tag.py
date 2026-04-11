"""Unit tests for envoy.tag."""

from __future__ import annotations

import pytest

from envoy.store import save_store, set_env_var
from envoy.tag import TagError, add_tag, filter_by_tag, list_tags, remove_tag

_PASS = "secret"


@pytest.fixture()
def store_file(tmp_path):
    path = str(tmp_path / "test.envoy")
    store = {"vars": {}}
    save_store(path, _PASS, store)
    set_env_var(path, _PASS, "API_KEY", "abc123")
    set_env_var(path, _PASS, "DB_URL", "postgres://localhost/db")
    set_env_var(path, _PASS, "DEBUG", "true")
    return path


def test_add_tag_returns_tag_list(store_file):
    result = add_tag(store_file, _PASS, "API_KEY", "sensitive")
    assert result == ["sensitive"]


def test_add_tag_multiple_tags(store_file):
    add_tag(store_file, _PASS, "API_KEY", "sensitive")
    result = add_tag(store_file, _PASS, "API_KEY", "prod")
    assert "sensitive" in result
    assert "prod" in result


def test_add_tag_idempotent(store_file):
    add_tag(store_file, _PASS, "API_KEY", "sensitive")
    result = add_tag(store_file, _PASS, "API_KEY", "sensitive")
    assert result.count("sensitive") == 1


def test_add_tag_unknown_var_raises(store_file):
    with pytest.raises(TagError, match="MISSING"):
        add_tag(store_file, _PASS, "MISSING", "tag")


def test_remove_tag_succeeds(store_file):
    add_tag(store_file, _PASS, "DB_URL", "infra")
    result = remove_tag(store_file, _PASS, "DB_URL", "infra")
    assert "infra" not in result


def test_remove_tag_not_present_raises(store_file):
    with pytest.raises(TagError, match="not found"):
        remove_tag(store_file, _PASS, "DB_URL", "nonexistent")


def test_list_tags_all(store_file):
    add_tag(store_file, _PASS, "API_KEY", "sensitive")
    add_tag(store_file, _PASS, "DB_URL", "infra")
    result = list_tags(store_file, _PASS)
    assert "API_KEY" in result
    assert "DB_URL" in result


def test_list_tags_for_single_var(store_file):
    add_tag(store_file, _PASS, "API_KEY", "sensitive")
    result = list_tags(store_file, _PASS, var_name="API_KEY")
    assert list(result.keys()) == ["API_KEY"]
    assert "sensitive" in result["API_KEY"]


def test_filter_by_tag_returns_matching_vars(store_file):
    add_tag(store_file, _PASS, "API_KEY", "sensitive")
    add_tag(store_file, _PASS, "DB_URL", "sensitive")
    result = filter_by_tag(store_file, _PASS, "sensitive")
    assert "API_KEY" in result
    assert "DB_URL" in result
    assert "DEBUG" not in result


def test_filter_by_tag_no_matches(store_file):
    result = filter_by_tag(store_file, _PASS, "nonexistent")
    assert result == {}
