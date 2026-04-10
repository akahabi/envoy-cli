"""CLI commands for snapshot management."""

from __future__ import annotations

import click
from datetime import datetime

from envoy.snapshot import SnapshotError, create_snapshot, delete_snapshot, list_snapshots, restore_snapshot


@click.group("snapshot")
def snapshot_cmd() -> None:
    """Manage point-in-time snapshots of env vars."""


@snapshot_cmd.command("create")
@click.option("--store", default=".envoy_store", show_default=True, help="Path to the encrypted store.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Decryption passphrase.")
@click.option("--name", default=None, help="Optional snapshot name (auto-generated if omitted).")
def create_cmd(store: str, passphrase: str, name: str) -> None:
    """Create a snapshot of the current env vars."""
    try:
        snap_name = create_snapshot(store, passphrase, name)
        click.echo(f"Snapshot '{snap_name}' created.")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@snapshot_cmd.command("restore")
@click.argument("name")
@click.option("--store", default=".envoy_store", show_default=True, help="Path to the encrypted store.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Encryption passphrase.")
def restore_cmd(name: str, store: str, passphrase: str) -> None:
    """Restore env vars from a snapshot."""
    try:
        vars_ = restore_snapshot(store, passphrase, name)
        click.echo(f"Restored {len(vars_)} variable(s) from snapshot '{name}'.")
    except SnapshotError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@snapshot_cmd.command("list")
@click.option("--store", default=".envoy_store", show_default=True, help="Path to the encrypted store.")
def list_cmd(store: str) -> None:
    """List all available snapshots."""
    snaps = list_snapshots(store)
    if not snaps:
        click.echo("No snapshots found.")
        return
    for s in snaps:
        ts = datetime.fromtimestamp(s["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"{s['name']:30s}  {ts}  ({s['var_count']} vars)")


@snapshot_cmd.command("delete")
@click.argument("name")
@click.option("--store", default=".envoy_store", show_default=True, help="Path to the encrypted store.")
def delete_cmd(name: str, store: str) -> None:
    """Delete a named snapshot."""
    try:
        delete_snapshot(store, name)
        click.echo(f"Snapshot '{name}' deleted.")
    except SnapshotError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
