"""CLI commands for profile inheritance resolution."""
from __future__ import annotations

from pathlib import Path

import click

from envoy.inherit import InheritError, resolve


@click.group("inherit")
def inherit_cmd() -> None:
    """Resolve variables through a chain of inherited profiles."""


@inherit_cmd.command("resolve")
@click.argument("profiles", nargs=-1, required=True)
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
@click.option(
    "--profiles-dir",
    default=".envoy/profiles",
    show_default=True,
    help="Directory containing profile files.",
)
@click.option("--show-origins", is_flag=True, default=False, help="Show which profile each var comes from.")
def resolve_cmd(profiles: tuple, passphrase: str, profiles_dir: str, show_origins: bool) -> None:
    """Merge PROFILES left-to-right and print the resolved variables.

    Later profiles override earlier ones (like CSS specificity).
    """
    try:
        result = resolve(list(profiles), passphrase, Path(profiles_dir))
    except InheritError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Chain: {' -> '.join(result.chain)}")
    click.echo(f"Resolved {len(result.vars)} variable(s):")
    for key in sorted(result.vars):
        val = result.vars[key]
        if show_origins:
            src = result.origin(key) or "?"
            click.echo(f"  {key}={val}  [{src}]")
        else:
            click.echo(f"  {key}={val}")


@inherit_cmd.command("origins")
@click.argument("profiles", nargs=-1, required=True)
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
@click.option(
    "--profiles-dir",
    default=".envoy/profiles",
    show_default=True,
)
def origins_cmd(profiles: tuple, passphrase: str, profiles_dir: str) -> None:
    """Show the origin profile for every resolved variable."""
    try:
        result = resolve(list(profiles), passphrase, Path(profiles_dir))
    except InheritError as exc:
        raise click.ClickException(str(exc)) from exc

    for key in sorted(result.vars):
        src = result.origin(key) or "?"
        click.echo(f"{key}  <-  {src}")
