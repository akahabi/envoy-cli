"""CLI commands for managing env-var pins."""

import click

from envoy.pin import PinError, add_pin, check_pins, list_pins, remove_pin


@click.group("pin")
def pin_cmd():
    """Pin env vars to expected values and verify them."""


@pin_cmd.command("add")
@click.argument("key")
@click.argument("expected_value")
@click.option("--store", default=".envoy", show_default=True, help="Path to store file.")
def add_cmd(key: str, expected_value: str, store: str):
    """Pin KEY to EXPECTED_VALUE."""
    try:
        pins = add_pin(store, key, expected_value)
        click.echo(f"Pinned '{key}' = '{expected_value}'. Total pins: {len(pins)}.")
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@pin_cmd.command("remove")
@click.argument("key")
@click.option("--store", default=".envoy", show_default=True)
def remove_cmd(key: str, store: str):
    """Remove the pin for KEY."""
    try:
        remove_pin(store, key)
        click.echo(f"Removed pin for '{key}'.")
    except PinError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@pin_cmd.command("list")
@click.option("--store", default=".envoy", show_default=True)
def list_cmd(store: str):
    """List all pinned keys and their expected values."""
    pins = list_pins(store)
    if not pins:
        click.echo("No pins defined.")
        return
    for key, val in sorted(pins.items()):
        click.echo(f"  {key} = {val}")


@pin_cmd.command("check")
@click.option("--store", default=".envoy", show_default=True)
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def check_cmd(store: str, passphrase: str):
    """Verify all pinned keys match their expected values."""
    violations = check_pins(store, passphrase)
    if not violations:
        click.echo("All pins OK.")
        return
    click.echo(f"{len(violations)} pin violation(s):")
    for v in violations:
        actual_display = v["actual"] if v["actual"] is not None else "<missing>"
        click.echo(f"  {v['key']}: expected '{v['expected']}', got '{actual_display}'")
    raise SystemExit(1)
