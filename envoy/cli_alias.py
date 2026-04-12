"""CLI commands for alias management."""

from __future__ import annotations

from pathlib import Path

import click

from envoy.alias import AliasError, add_alias, list_aliases, remove_alias, resolve_alias
from envoy.store import get_env_vars


@click.group("alias")
def alias_cmd() -> None:
    """Manage short aliases for env var keys."""


@alias_cmd.command("add")
@click.argument("alias")
@click.argument("key")
@click.option("--store", default=".envoy", show_default=True, help="Path to the store file.")
@click.option("--passphrase", prompt=True, hide_input=True)
def add_cmd(alias: str, key: str, store: str, passphrase: str) -> None:
    """Add ALIAS as a shorthand for KEY."""
    store_path = Path(store)
    try:
        known = list(get_env_vars(store_path, passphrase).keys())
        add_alias(store_path, alias, key, known)
        click.echo(f"Alias '{alias}' -> '{key}' added.")
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc


@alias_cmd.command("remove")
@click.argument("alias")
@click.option("--store", default=".envoy", show_default=True)
def remove_cmd(alias: str, store: str) -> None:
    """Remove ALIAS."""
    try:
        remove_alias(Path(store), alias)
        click.echo(f"Alias '{alias}' removed.")
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc


@alias_cmd.command("list")
@click.option("--store", default=".envoy", show_default=True)
def list_cmd(store: str) -> None:
    """List all registered aliases."""
    aliases = list_aliases(Path(store))
    if not aliases:
        click.echo("No aliases defined.")
        return
    for alias, key in sorted(aliases.items()):
        click.echo(f"{alias}  ->  {key}")


@alias_cmd.command("resolve")
@click.argument("alias")
@click.option("--store", default=".envoy", show_default=True)
def resolve_cmd(alias: str, store: str) -> None:
    """Print the key that ALIAS maps to."""
    key = resolve_alias(Path(store), alias)
    if key is None:
        raise click.ClickException(f"Alias '{alias}' not found.")
    click.echo(key)
