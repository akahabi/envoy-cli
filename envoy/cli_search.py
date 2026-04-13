"""CLI commands for searching env vars."""

from __future__ import annotations

import click

from envoy.search import SearchError, search_vars


@click.group("search")
def search_cmd() -> None:
    """Search and filter environment variables."""


@search_cmd.command("run")
@click.option("--store", required=True, envvar="ENVOY_STORE", help="Path to the store file.")
@click.option("--passphrase", required=True, envvar="ENVOY_PASSPHRASE", hide_input=True, help="Decryption passphrase.")
@click.option("--key", "key_pattern", default=None, help="Glob pattern to match against keys (e.g. 'DB_*').")
@click.option("--value", "value_pattern", default=None, help="Regex pattern to match against values.")
@click.option("--tag", default=None, help="Filter by tag name.")
@click.option("--case-sensitive", is_flag=True, default=False, help="Enable case-sensitive matching.")
@click.option("--show-values", is_flag=True, default=False, help="Print values alongside keys.")
def run_cmd(
    store: str,
    passphrase: str,
    key_pattern: str | None,
    value_pattern: str | None,
    tag: str | None,
    case_sensitive: bool,
    show_values: bool,
) -> None:
    """Search env vars with optional key, value, and tag filters."""
    if key_pattern is None and value_pattern is None and tag is None:
        raise click.UsageError("Provide at least one of --key, --value, or --tag.")

    try:
        result = search_vars(
            store,
            passphrase,
            key_pattern=key_pattern,
            value_pattern=value_pattern,
            tag=tag,
            case_sensitive=case_sensitive,
        )
    except SearchError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.is_empty():
        click.echo("No matches found.")
        return

    for key, value in sorted(result.matches.items()):
        if show_values:
            click.echo(f"{key}={value}")
        else:
            click.echo(key)

    click.echo(f"\n{result.summary()}")
