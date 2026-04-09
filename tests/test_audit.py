"""Tests for envoy.audit module."""

import json
import pytest
from pathlib import Path
from envoy.audit import record_event, read_events, clear_events


@pytest.fixture
def audit_file(tmp_path):
    return tmp_path / "audit.log"


def test_record_event_creates_file(audit_file):
    record_event("set", "API_KEY", "local", audit_path=audit_file)
    assert audit_file.exists()


def test_record_event_returns_dict(audit_file):
    event = record_event("set", "API_KEY", "local", audit_path=audit_file)
    assert event["action"] == "set"
    assert event["key"] == "API_KEY"
    assert event["environment"] == "local"
    assert "timestamp" in event


def test_record_event_with_profile(audit_file):
    event = record_event("push", "DB_URL", "staging", profile="myapp", audit_path=audit_file)
    assert event["profile"] == "myapp"


def test_read_events_empty_when_no_file(audit_file):
    events = read_events(audit_path=audit_file)
    assert events == []


def test_read_events_returns_all(audit_file):
    record_event("set", "KEY1", "local", audit_path=audit_file)
    record_event("set", "KEY2", "staging", audit_path=audit_file)
    events = read_events(audit_path=audit_file)
    assert len(events) == 2


def test_read_events_filter_by_environment(audit_file):
    record_event("set", "KEY1", "local", audit_path=audit_file)
    record_event("set", "KEY2", "staging", audit_path=audit_file)
    events = read_events(environment="local", audit_path=audit_file)
    assert len(events) == 1
    assert events[0]["key"] == "KEY1"


def test_read_events_filter_by_action(audit_file):
    record_event("set", "KEY1", "local", audit_path=audit_file)
    record_event("push", "KEY1", "local", audit_path=audit_file)
    events = read_events(action="push", audit_path=audit_file)
    assert len(events) == 1
    assert events[0]["action"] == "push"


def test_read_events_limit(audit_file):
    for i in range(10):
        record_event("set", f"KEY{i}", "local", audit_path=audit_file)
    events = read_events(limit=3, audit_path=audit_file)
    assert len(events) == 3
    assert events[-1]["key"] == "KEY9"


def test_clear_events(audit_file):
    record_event("set", "KEY1", "local", audit_path=audit_file)
    clear_events(audit_path=audit_file)
    assert not audit_file.exists()
