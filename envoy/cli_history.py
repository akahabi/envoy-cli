"""CLI commands for inspecting env-var change history."""

from __future__ import annotations

import time
from datetime import datetime

import click

from envoy.history import HistoryError, clear_history, read_history


@click.group("history")
def history_cmd() -> None:
    """View and manage the change history of a store."""


@history_cmd.command("log")
@click.option("--store", default=".envoy.enc", show_default=True, help="Path to the store file.")
@click.option("--key", default=None, help="Filter by variable name.")
@click.option("--action", default=None, help="Filter by action type (set, delete, …).")
@click.option("--limit", default=20, show_default=True, help="Maximum number of entries to show.")
def log_cmd(store: str, key: str | None, action: str | None, limit: int) -> None:
    """Display recent change history for a store."""
    try:
        entries = read_history(store, key=key, action=action, limit=limit)
    except HistoryError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if not entries:
        click.echo("No history entries found.")
        return

    for entry in entries:
        ts = datetime.fromtimestamp(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        act = entry.get("action", "?")
        k = entry.get("key", "?")
        old = entry.get("old_value")
        new = entry.get("new_value")
        profile = entry.get("profile")
        line = f"[{ts}] {act.upper():8s} {k}"
        if old is not None or new is not None:
            line += f"  {old!r} -> {new!r}"
        if profile:
            line += f"  (profile: {profile})"
        click.echo(line)


@history_cmd.command("clear")
@click.option("--store", default=".envoy.enc", show_default=True, help="Path to the store file.")
@click.confirmation_option(prompt="Clear all history for this store?")
def clear_cmd(store: str) -> None:
    """Delete all history records for a store."""
    try:
        clear_history(store)
    except HistoryError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    click.echo("History cleared.")
