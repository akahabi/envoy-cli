"""CLI commands for viewing the envoy audit log."""

import click
from envoy.audit import read_events, clear_events


@click.group("audit")
def audit():
    """View and manage the audit log."""
    pass


@audit.command("log")
@click.option("--env", "environment", default=None, help="Filter by environment.")
@click.option("--action", default=None, help="Filter by action (set, push, pull, delete).")
@click.option("--limit", default=20, show_default=True, help="Number of recent events to show.")
def log_cmd(environment, action, limit):
    """Display recent audit log entries."""
    events = read_events(environment=environment, action=action, limit=limit)
    if not events:
        click.echo("No audit events found.")
        return
    for event in events:
        profile_part = f" [{event['profile']}]" if event.get("profile") else ""
        click.echo(
            f"{event['timestamp']}  {event['action']:8s}  "
            f"{event['environment']:12s}  {event['key']}{profile_part}"
        )


@audit.command("clear")
@click.confirmation_option(prompt="Are you sure you want to clear the audit log?")
def clear_cmd():
    """Clear all audit log entries."""
    clear_events()
    click.echo("Audit log cleared.")
