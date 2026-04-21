"""CLI commands for managing deprecated env vars."""
import click

from envoy.deprecate import (
    DeprecateError,
    check_sunset,
    deprecate_var,
    list_deprecated,
    undeprecate_var,
)


@click.group("deprecate")
def deprecate_cmd():
    """Manage deprecated environment variables."""


@deprecate_cmd.command("mark")
@click.argument("key")
@click.option("--reason", required=True, help="Why this var is deprecated.")
@click.option("--replacement", default=None, help="Suggested replacement key.")
@click.option("--sunset", default=None, help="Sunset date (YYYY-MM-DD).")
@click.option("--store", default="envoy.store", show_default=True)
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def mark_cmd(key, reason, replacement, sunset, store, passphrase):
    """Mark KEY as deprecated."""
    try:
        entry = deprecate_var(store, passphrase, key, reason, replacement, sunset)
    except DeprecateError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Marked '{key}' as deprecated on {entry['deprecated_on']}.")
    if replacement:
        click.echo(f"  Replacement: {replacement}")
    if sunset:
        click.echo(f"  Sunset: {sunset}")


@deprecate_cmd.command("unmark")
@click.argument("key")
@click.option("--store", default="envoy.store", show_default=True)
def unmark_cmd(key, store):
    """Remove deprecation marker from KEY."""
    try:
        undeprecate_var(store, key)
    except DeprecateError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Removed deprecation marker for '{key}'.")


@deprecate_cmd.command("list")
@click.option("--store", default="envoy.store", show_default=True)
def list_cmd(store):
    """List all deprecated variables."""
    entries = list_deprecated(store)
    if not entries:
        click.echo("No deprecated variables.")
        return
    for key, info in sorted(entries.items()):
        repl = f" -> {info['replacement']}" if "replacement" in info else ""
        sunset = f" (sunset: {info['sunset']})" if "sunset" in info else ""
        click.echo(f"  {key}{repl}{sunset}  # {info['reason']}")


@deprecate_cmd.command("sunset")
@click.option("--store", default="envoy.store", show_default=True)
def sunset_cmd(store):
    """Show variables whose sunset date has passed."""
    expired = check_sunset(store)
    if not expired:
        click.echo("No variables past their sunset date.")
        return
    for item in expired:
        click.echo(f"  {item['key']} (sunset: {item['sunset']})  # {item['reason']}")
