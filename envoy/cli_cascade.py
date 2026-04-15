"""CLI commands for cascade resolution of env vars."""

from __future__ import annotations

import click

from envoy.cascade import CascadeError, cascade
from envoy.export import render


@click.group("cascade")
def cascade_cmd() -> None:
    """Merge variables from multiple profiles in priority order."""


@cascade_cmd.command("resolve")
@click.argument("profiles", nargs=-1, required=True)
@click.option("--store", default=".envoy", show_default=True, help="Path to local store.")
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--profiles-dir", default=".envoy_profiles", show_default=True)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["dotenv", "json", "shell"]),
    default="dotenv",
    show_default=True,
    help="Output format.",
)
@click.option("--no-base", is_flag=True, default=False, help="Skip local store as base layer.")
@click.option("--show-origins", is_flag=True, default=False, help="Print origin summary to stderr.")
def resolve_cmd(
    profiles: tuple,
    store: str,
    passphrase: str,
    profiles_dir: str,
    fmt: str,
    no_base: bool,
    show_origins: bool,
) -> None:
    """Resolve and print merged variables from PROFILES in priority order."""
    try:
        result = cascade(
            store_path=store,
            passphrase=passphrase,
            profiles=list(profiles),
            profiles_dir=profiles_dir,
            base_store=not no_base,
        )
    except CascadeError as exc:
        raise click.ClickException(str(exc)) from exc

    if show_origins:
        click.echo(result.summary(), err=True)

    click.echo(render(result.merged, fmt))


@cascade_cmd.command("origins")
@click.argument("profiles", nargs=-1, required=True)
@click.option("--store", default=".envoy", show_default=True)
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--profiles-dir", default=".envoy_profiles", show_default=True)
@click.option("--no-base", is_flag=True, default=False)
def origins_cmd(
    profiles: tuple,
    store: str,
    passphrase: str,
    profiles_dir: str,
    no_base: bool,
) -> None:
    """Show which profile each variable originates from."""
    try:
        result = cascade(
            store_path=store,
            passphrase=passphrase,
            profiles=list(profiles),
            profiles_dir=profiles_dir,
            base_store=not no_base,
        )
    except CascadeError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(result.summary())
