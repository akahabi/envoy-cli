"""CLI commands for profile sync operations."""

import click

from envoy.sync import push_profile, pull_profile, list_profiles, delete_profile


@click.group()
def sync():
    """Manage environment profile snapshots."""
    pass


@sync.command("push")
@click.argument("profile")
@click.option("--store", default=".envoy_store", show_default=True, help="Path to local store file.")
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def push_cmd(profile: str, store: str, passphrase: str) -> None:
    """Push current env vars to a named profile snapshot."""
    try:
        push_profile(store, profile, passphrase)
        click.echo(f"✓ Pushed store to profile '{profile}'.")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@sync.command("pull")
@click.argument("profile")
@click.option("--store", default=".envoy_store", show_default=True, help="Path to local store file.")
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def pull_cmd(profile: str, store: str, passphrase: str) -> None:
    """Pull a named profile snapshot and merge into local store."""
    try:
        pull_profile(store, profile, passphrase)
        click.echo(f"✓ Pulled profile '{profile}' into local store.")
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@sync.command("list")
def list_cmd() -> None:
    """List all saved profile snapshots."""
    profiles = list_profiles()
    if not profiles:
        click.echo("No profiles found.")
    else:
        for name in sorted(profiles):
            click.echo(f"  - {name}")


@sync.command("delete")
@click.argument("profile")
def delete_cmd(profile: str) -> None:
    """Delete a named profile snapshot."""
    try:
        delete_profile(profile)
        click.echo(f"✓ Deleted profile '{profile}'.")
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
