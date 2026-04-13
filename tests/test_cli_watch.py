"""Tests for envoy.cli_watch CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from envoy.cli_watch import watch_cmd
from envoy.store import save_store
from envoy.watch import WatchError

PASS = "secret"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def store_file(tmp_path: Path) -> Path:
    path = tmp_path / "e.enc"
    save_store(path, PASS, {"FOO": "bar"})
    return path


def _invoke(runner, store_file, extra=None):
    args = ["run", str(store_file), "--passphrase", PASS, "--interval", "0"]
    if extra:
        args.extend(extra)
    return runner.invoke(watch_cmd, args)


def test_run_missing_store_exits_nonzero(runner, tmp_path):
    result = runner.invoke(
        watch_cmd, ["run", str(tmp_path / "missing.enc"), "--passphrase", PASS, "--interval", "0"]
    )
    assert result.exit_code != 0
    assert "Error" in result.output


def test_run_outputs_watching_message(runner, store_file):
    with patch("envoy.cli_watch.watch", side_effect=KeyboardInterrupt):
        result = runner.invoke(
            watch_cmd,
            ["run", str(store_file), "--passphrase", PASS, "--interval", "0"],
        )
    assert "Watching" in result.output
    assert result.exit_code == 0


def test_run_stopped_message_on_keyboard_interrupt(runner, store_file):
    with patch("envoy.cli_watch.watch", side_effect=KeyboardInterrupt):
        result = runner.invoke(
            watch_cmd,
            ["run", str(store_file), "--passphrase", PASS, "--interval", "0"],
        )
    assert "Stopped" in result.output


def test_run_watch_error_shown_as_click_exception(runner, store_file):
    with patch("envoy.cli_watch.watch", side_effect=WatchError("boom")):
        result = runner.invoke(
            watch_cmd,
            ["run", str(store_file), "--passphrase", PASS, "--interval", "0"],
        )
    assert result.exit_code != 0
    assert "boom" in result.output


def test_run_on_change_callback_prints_diff(runner, store_file):
    """Verify that the on_change callback passed to watch produces coloured output."""
    captured_callback = {}

    def fake_watch(path, passphrase, on_change, interval, **kw):
        captured_callback["fn"] = on_change

    with patch("envoy.cli_watch.watch", side_effect=fake_watch):
        runner.invoke(
            watch_cmd,
            ["run", str(store_file), "--passphrase", PASS, "--interval", "0"],
        )

    # Now invoke the captured callback manually
    from io import StringIO
    import click

    output_lines = []
    diff = {
        "added": [("NEW_KEY", None, "val")],
        "removed": [],
        "changed": [],
    }
    with patch("click.echo", side_effect=lambda msg, **kw: output_lines.append(str(msg))):
        captured_callback["fn"](diff)

    joined = "\n".join(output_lines)
    assert "NEW_KEY" in joined
