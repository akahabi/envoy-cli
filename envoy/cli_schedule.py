"""CLI commands for managing rotation schedules."""

from __future__ import annotations

import click

from envoy.schedule import (
    ScheduleError,
    due_schedules,
    list_schedules,
    remove_schedule,
    set_schedule,
)


@click.group("schedule")
def schedule_cmd() -> None:
    """Manage automatic rotation schedules for env vars."""


@schedule_cmd.command("set")
@click.argument("key")
@click.argument("interval_days", type=int)
@click.option("--store", default=".envoy_store", show_default=True)
def set_cmd(key: str, interval_days: int, store: str) -> None:
    """Schedule KEY for rotation every INTERVAL_DAYS days."""
    try:
        entry = set_schedule(store, key, interval_days)
        click.echo(f"Scheduled '{key}' every {interval_days} day(s). Due at: {entry['due_at']}")
    except ScheduleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@schedule_cmd.command("remove")
@click.argument("key")
@click.option("--store", default=".envoy_store", show_default=True)
def remove_cmd(key: str, store: str) -> None:
    """Remove the rotation schedule for KEY."""
    try:
        remove_schedule(store, key)
        click.echo(f"Removed schedule for '{key}'.")
    except ScheduleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@schedule_cmd.command("list")
@click.option("--store", default=".envoy_store", show_default=True)
def list_cmd(store: str) -> None:
    """List all scheduled keys."""
    schedules = list_schedules(store)
    if not schedules:
        click.echo("No schedules configured.")
        return
    for key, info in sorted(schedules.items()):
        click.echo(f"{key}: every {info['interval_days']}d, due {info['due_at']}")


@schedule_cmd.command("due")
@click.option("--store", default=".envoy_store", show_default=True)
def due_cmd(store: str) -> None:
    """List keys whose rotation is overdue."""
    overdue = due_schedules(store)
    if not overdue:
        click.echo("No keys are overdue for rotation.")
        return
    click.echo(f"{len(overdue)} key(s) overdue:")
    for key, info in sorted(overdue.items()):
        click.echo(f"  {key}  (was due {info['due_at']})")
