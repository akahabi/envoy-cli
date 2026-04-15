"""CLI commands for renaming environment variable keys."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from envoy.rename import RenameError, rename_var


@click.group("rename")
def rename_cmd() -> None:
    """Rename variable keys inside a store."""


@rename_cmd.command("key")
@click.argument("old_key")
@click.argument("new_key")
@click.option(
    "--store",
    "store_path",
    default=".envoy_store",
    show_default=True,
    help="Path to the encrypted store file.",
)
@click.option(
    "--passphrase",
    envvar="ENVOY_PASSPHRASE",
    prompt=True,
    hide_input=True,
    help="Passphrase used to decrypt/encrypt the store.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite new_key if it already exists.",
)
def key_cmd(
    old_key: str,
    new_key: str,
    store_path: str,
    passphrase: str,
    overwrite: bool,
) -> None:
    """Rename OLD_KEY to NEW_KEY in the store."""
    path = Path(store_path)
    if not path.exists():
        click.echo(f"Store not found: {store_path}", err=True)
        sys.exit(1)

    try:
        vars_ = rename_var(path, passphrase, old_key, new_key, overwrite=overwrite)
    except RenameError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Renamed '{old_key}' -> '{new_key}'. Store now has {len(vars_)} key(s).")
