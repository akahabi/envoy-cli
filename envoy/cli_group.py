"""CLI commands for managing env-var groups."""

from __future__ import annotations

import click

from envoy.group import GroupError, add_group, remove_group, list_groups, get_group_vars


@click.group("group")
def group_cmd():
    """Organise env vars into named groups."""


@group_cmd.command("add")
@click.argument("group")
@click.argument("keys", nargs=-1, required=True)
@click.option("--store", default=".envoy", show_default=True, help="Path to store file")
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def add_cmd(group: str, keys: tuple, store: str, passphrase: str):
    """Add KEYS to GROUP (creating it if necessary)."""
    try:
        result = add_group(store, group, list(keys), passphrase)
        click.echo(f"Group '{group}' now contains: {', '.join(result[group])}")
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@group_cmd.command("remove")
@click.argument("group")
@click.option("--store", default=".envoy", show_default=True)
def remove_cmd(group: str, store: str):
    """Delete GROUP."""
    try:
        remove_group(store, group)
        click.echo(f"Group '{group}' removed.")
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@group_cmd.command("list")
@click.option("--store", default=".envoy", show_default=True)
def list_cmd(store: str):
    """List all groups and their keys."""
    groups = list_groups(store)
    if not groups:
        click.echo("No groups defined.")
        return
    for name, keys in sorted(groups.items()):
        click.echo(f"{name}: {', '.join(keys)}")


@group_cmd.command("show")
@click.argument("group")
@click.option("--store", default=".envoy", show_default=True)
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def show_cmd(group: str, store: str, passphrase: str):
    """Show key=value pairs for all vars in GROUP."""
    try:
        vars_ = get_group_vars(store, group, passphrase)
        for k, v in sorted(vars_.items()):
            click.echo(f"{k}={v}")
    except GroupError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
