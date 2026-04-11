"""CLI commands for tag management."""

from __future__ import annotations

import click

from envoy.tag import TagError, add_tag, filter_by_tag, list_tags, remove_tag


@click.group("tag")
def tag_cmd() -> None:
    """Manage tags on environment variables."""


@tag_cmd.command("add")
@click.argument("var_name")
@click.argument("tag")
@click.option("--store", default=".envoy", show_default=True, help="Path to the store file.")
@click.password_option("--passphrase", prompt="Passphrase", confirmation_prompt=False)
def add_cmd(var_name: str, tag: str, store: str, passphrase: str) -> None:
    """Add TAG to VAR_NAME."""
    try:
        tags = add_tag(store, passphrase, var_name, tag)
        click.echo(f"Tags for '{var_name}': {', '.join(tags)}")
    except TagError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@tag_cmd.command("remove")
@click.argument("var_name")
@click.argument("tag")
@click.option("--store", default=".envoy", show_default=True)
@click.password_option("--passphrase", prompt="Passphrase", confirmation_prompt=False)
def remove_cmd(var_name: str, tag: str, store: str, passphrase: str) -> None:
    """Remove TAG from VAR_NAME."""
    try:
        tags = remove_tag(store, passphrase, var_name, tag)
        remaining = ", ".join(tags) if tags else "(none)"
        click.echo(f"Tags for '{var_name}': {remaining}")
    except TagError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@tag_cmd.command("list")
@click.argument("var_name", required=False, default=None)
@click.option("--store", default=".envoy", show_default=True)
@click.password_option("--passphrase", prompt="Passphrase", confirmation_prompt=False)
def list_cmd(var_name: str | None, store: str, passphrase: str) -> None:
    """List tags, optionally filtered to VAR_NAME."""
    mapping = list_tags(store, passphrase, var_name)
    if not mapping:
        click.echo("No tags found.")
        return
    for var, tags in sorted(mapping.items()):
        click.echo(f"{var}: {', '.join(tags)}")


@tag_cmd.command("filter")
@click.argument("tag")
@click.option("--store", default=".envoy", show_default=True)
@click.password_option("--passphrase", prompt="Passphrase", confirmation_prompt=False)
def filter_cmd(tag: str, store: str, passphrase: str) -> None:
    """Show all variables that have TAG assigned."""
    vars_ = filter_by_tag(store, passphrase, tag)
    if not vars_:
        click.echo(f"No variables tagged '{tag}'.")
        return
    for k, v in sorted(vars_.items()):
        click.echo(f"{k}={v}")
