"""CLI commands for managing TTL (time-to-live) on env vars."""

from pathlib import Path

import click

from envoy.ttl import TTLError, expired_keys, list_ttls, remove_ttl, set_ttl


@click.group("ttl")
def ttl_cmd():
    """Manage key expiry (TTL) for env vars."""


@ttl_cmd.command("set")
@click.argument("key")
@click.argument("seconds", type=int)
@click.option("--store", default=".envoy", show_default=True, help="Path to the store file.")
@click.password_option("--passphrase", prompt="Passphrase", confirmation_prompt=False)
def set_cmd(key: str, seconds: int, store: str, passphrase: str):
    """Set a TTL of SECONDS on KEY."""
    try:
        entry = set_ttl(Path(store), passphrase, key, seconds)
        click.echo(f"TTL set: {key} expires at {entry['expires_at']}")
    except TTLError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@ttl_cmd.command("remove")
@click.argument("key")
@click.option("--store", default=".envoy", show_default=True)
def remove_cmd(key: str, store: str):
    """Remove the TTL from KEY."""
    remove_ttl(Path(store), key)
    click.echo(f"TTL removed for '{key}'.")


@ttl_cmd.command("list")
@click.option("--store", default=".envoy", show_default=True)
def list_cmd(store: str):
    """List all keys with an active TTL."""
    entries = list_ttls(Path(store))
    if not entries:
        click.echo("No TTL entries found.")
        return
    for key, meta in entries.items():
        click.echo(f"  {key}: expires at {meta['expires_at']}")


@ttl_cmd.command("expired")
@click.option("--store", default=".envoy", show_default=True)
def expired_cmd(store: str):
    """List keys whose TTL has elapsed."""
    keys = expired_keys(Path(store))
    if not keys:
        click.echo("No expired keys.")
        return
    for key in keys:
        click.echo(f"  {key} [EXPIRED]")
