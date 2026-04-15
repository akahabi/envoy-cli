"""CLI commands for copying environment variables between stores."""

from __future__ import annotations

from pathlib import Path

import click

from envoy.copy import CopyError, copy_key, copy_vars


@click.group("copy")
def copy_cmd() -> None:
    """Copy variables between env stores."""


@copy_cmd.command("vars")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("dst", type=click.Path(path_type=Path))
@click.option("--src-pass", envvar="ENVOY_SRC_PASSPHRASE", prompt="Source passphrase", hide_input=True)
@click.option("--dst-pass", envvar="ENVOY_DST_PASSPHRASE", prompt="Destination passphrase", hide_input=True)
@click.option("--key", "keys", multiple=True, help="Specific key(s) to copy. Repeatable.")
@click.option("--no-overwrite", is_flag=True, default=False, help="Skip keys already in destination.")
def vars_cmd(
    src: Path,
    dst: Path,
    src_pass: str,
    dst_pass: str,
    keys: tuple[str, ...],
    no_overwrite: bool,
) -> None:
    """Copy variables from SRC store to DST store."""
    try:
        copied = copy_vars(
            src_path=src,
            dst_path=dst,
            src_passphrase=src_pass,
            dst_passphrase=dst_pass,
            keys=list(keys) if keys else None,
            overwrite=not no_overwrite,
        )
    except CopyError as exc:
        raise click.ClickException(str(exc)) from exc

    if not copied:
        click.echo("Nothing copied.")
    else:
        click.echo(f"Copied {len(copied)} variable(s) to {dst}:")
        for k in sorted(copied):
            click.echo(f"  {k}")


@copy_cmd.command("key")
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("dst", type=click.Path(path_type=Path))
@click.argument("key")
@click.option("--src-pass", envvar="ENVOY_SRC_PASSPHRASE", prompt="Source passphrase", hide_input=True)
@click.option("--dst-pass", envvar="ENVOY_DST_PASSPHRASE", prompt="Destination passphrase", hide_input=True)
@click.option("--rename", "new_key", default=None, help="Name for the key in the destination store.")
def key_cmd(
    src: Path,
    dst: Path,
    key: str,
    src_pass: str,
    dst_pass: str,
    new_key: str | None,
) -> None:
    """Copy a single KEY from SRC store to DST store."""
    try:
        dest_key, _ = copy_key(
            src_path=src,
            dst_path=dst,
            key=key,
            src_passphrase=src_pass,
            dst_passphrase=dst_pass,
            new_key=new_key,
        )
    except CopyError as exc:
        raise click.ClickException(str(exc)) from exc

    label = f"'{key}' -> '{dest_key}'" if new_key else f"'{key}'"
    click.echo(f"Copied {label} to {dst}")
