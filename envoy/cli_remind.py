"""CLI commands for managing env-var reminders."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import click

from envoy.remind import RemindError, due_reminders, list_reminders, remove_reminder, set_reminder


@click.group("remind")
def remind_cmd():
    """Manage expiry reminders for env vars."""


@remind_cmd.command("set")
@click.argument("key")
@click.argument("deadline")  # YYYY-MM-DD
@click.option("--note", default="", help="Optional note about why rotation is needed.")
@click.option("--store", default=".envoy", show_default=True)
@click.password_option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt="Passphrase")
def set_cmd(key: str, deadline: str, note: str, store: str, passphrase: str):
    """Set a rotation reminder for KEY with DEADLINE (YYYY-MM-DD)."""
    try:
        set_reminder(Path(store), passphrase, key, deadline, note)
        click.echo(f"Reminder set for '{key}' — due {deadline}.")
    except RemindError as exc:
        click.echo(f"Error: {exc}aise SystemExit(1)


@remind_cmd.command("remove")
@click.argument("key")
@click.option("--store", default=".envoy", show_default=True)
def remove_cmd(key: str, store: str):
    """Remove the reminder for KEY."""
    removed = remove_reminder(Path(store), key)
    if removed:
        click.echo(f"Reminder for '{key}' removed.")
    else:
        click.echo(f"No reminder found for '{key}'.")


@remind_cmd.command("list")
@click.option("--store", default=".envoy", show_default=True)
def list_cmd(store: str):
    """List all reminders."""
    data = list_reminders(Path(store))
    if not data:
        click.echo("No reminders set.")
        return
    for key, info in sorted(data.items()):
        note_part = f" — {info['note']}" if info.get("note") else ""
        click.echo(f"  {key}: {info['deadline']}{note_part}")


@remind_cmd.command("due")
@click.option("--store", default=".envoy", show_default=True)
@click.option("--as-of", default=None, help="Check as of YYYY-MM-DD (default: today).")
def due_cmd(store: str, as_of: str | None):
    """Show reminders that are due (deadline <= today)."""
    as_of_date = date.fromisoformat(as_of) if as_of else None
    due = due_reminders(Path(store), as_of_date)
    if not due:
        click.echo("No reminders due.")
        return
    click.echo(f"{len(due)} reminder(s) due:")
    for item in due:
        note_part = f" — {item['note']}" if item.get("note") else ""
        click.echo(f"  {item['key']}: {item['deadline']}{note_part}")
