"""Tests for envoy.hook."""
import pytest
from pathlib import Path
from envoy.hook import add_hook, remove_hook, list_hooks, fire_hooks, HookError
from envoy.store import save_store


@pytest.fixture()
def store_file(tmp_path):
    p = tmp_path / "store.enc"
    save_store(p, "pass", {})
    return p


def test_add_hook_returns_command_list(store_file):
    cmds = add_hook(store_file, "post-set", "echo hello")
    assert cmds == ["echo hello"]


def test_add_hook_persists_file(store_file):
    add_hook(store_file, "post-set", "echo hello")
    hooks = list_hooks(store_file, "post-set")
    assert "echo hello" in hooks["post-set"]


def test_add_hook_idempotent(store_file):
    add_hook(store_file, "post-set", "echo hi")
    cmds = add_hook(store_file, "post-set", "echo hi")
    assert cmds.count("echo hi") == 1


def test_add_hook_unknown_event_raises(store_file):
    with pytest.raises(HookError, match="Unknown event"):
        add_hook(store_file, "on-magic", "echo nope")


def test_add_multiple_hooks_same_event(store_file):
    add_hook(store_file, "pre-push", "echo a")
    cmds = add_hook(store_file, "pre-push", "echo b")
    assert len(cmds) == 2


def test_remove_hook_reduces_list(store_file):
    add_hook(store_file, "post-export", "echo x")
    cmds = remove_hook(store_file, "post-export", "echo x")
    assert cmds == []


def test_remove_hook_not_registered_raises(store_file):
    with pytest.raises(HookError, match="not registered"):
        remove_hook(store_file, "post-set", "echo missing")


def test_list_hooks_all_events(store_file):
    add_hook(store_file, "pre-set", "echo pre")
    hooks = list_hooks(store_file)
    assert "pre-set" in hooks
    assert "echo pre" in hooks["pre-set"]
    # other events are empty lists
    assert hooks["post-push"] == []


def test_list_hooks_unknown_event_raises(store_file):
    with pytest.raises(HookError, match="Unknown event"):
        list_hooks(store_file, "bad-event")


def test_fire_hooks_runs_command(store_file):
    add_hook(store_file, "post-set", "echo fired")
    outputs = fire_hooks(store_file, "post-set")
    assert outputs == ["fired"]


def test_fire_hooks_empty_event_returns_empty(store_file):
    outputs = fire_hooks(store_file, "pre-push")
    assert outputs == []


def test_fire_hooks_failing_command_raises(store_file):
    add_hook(store_file, "pre-export", "exit 1")
    with pytest.raises(HookError, match="Hook command failed"):
        fire_hooks(store_file, "pre-export")
