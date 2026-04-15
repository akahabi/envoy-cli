"""CLI commands for packing and unpacking profile archives."""

from __future__ import annotations

from pathlib import Path

import click

from envoy.archive import ArchiveError, pack, unpack


@click.group("archive")
def archive_cmd() -> None:
    """Pack and unpack profile bundles."""


@archive_cmd.command("pack")
@click.argument("profiles", nargs=-1, required=True)
@click.option("--profiles-dir", default=".envoy/profiles", show_default=True)
@click.option("--output", "-o", required=True, help="Destination .zip path")
@click.option("--passphrase", "-p", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def pack_cmd(
    profiles: tuple[str, ...],
    profiles_dir: str,
    output: str,
    passphrase: str,
) -> None:
    """Pack PROFILES into a zip archive at OUTPUT."""
    try:
        data = pack(list(profiles), Path(profiles_dir), passphrase)
    except ArchiveError as exc:
        raise click.ClickException(str(exc)) from exc

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    click.echo(f"Packed {len(profiles)} profile(s) → {out_path}")


@archive_cmd.command("unpack")
@click.argument("archive")
@click.option("--profiles-dir", default=".envoy/profiles", show_default=True)
@click.option("--passphrase", "-p", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing profiles")
def unpack_cmd(
    archive: str,
    profiles_dir: str,
    passphrase: str,
    overwrite: bool,
) -> None:
    """Unpack profiles from ARCHIVE into --profiles-dir."""
    data = Path(archive).read_bytes()
    try:
        restored = unpack(data, Path(profiles_dir), passphrase, overwrite=overwrite)
    except ArchiveError as exc:
        raise click.ClickException(str(exc)) from exc

    for name in restored:
        click.echo(f"  restored: {name}")
    click.echo(f"Unpacked {len(restored)} profile(s) from {archive}")
