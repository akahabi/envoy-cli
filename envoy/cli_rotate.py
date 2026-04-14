"""CLI commands for key rotation."""

from __future__ import annotations

from pathlib import Path

import click

from envoy.rotate import RotationError, rotate_store, rotate_profile


@click.group()
def rotate() -> None:
    """Rotate encryption passphrases."""


@rotate.command("store")
@click.option("--store", "store_path", default=".envoy", show_default=True,
              help="Path to the encrypted store file.")
@click.password_option("--old-passphrase", prompt="Old passphrase",
                       confirmation_prompt=False, help="Current passphrase.")
@click.password_option("--new-passphrase", prompt="New passphrase",
                       help="Replacement passphrase.")
def rotate_store_cmd(store_path: str, old_passphrase: str, new_passphrase: str) -> None:
    """Re-encrypt the local store with a new passphrase."""
    path = Path(store_path)
    if not path.exists():
        raise click.ClickException(f"Store file not found: {store_path}")
    if old_passphrase == new_passphrase:
        raise click.ClickException("New passphrase must differ from the old passphrase.")
    try:
        vars_ = rotate_store(path, old_passphrase, new_passphrase)
    except RotationError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Rotated {len(vars_)} variable(s) in '{store_path}'.")


@rotate.command("profile")
@click.argument("profile")
@click.option("--profiles-dir", default=".envoy_profiles", show_default=True,
              help="Directory containing sync profiles.")
@click.password_option("--old-passphrase", prompt="Old passphrase",
                       confirmation_prompt=False, help="Current passphrase.")
@click.password_option("--new-passphrase", prompt="New passphrase",
                       help="Replacement passphrase.")
def rotate_profile_cmd(
    profile: str,
    profiles_dir: str,
    old_passphrase: str,
    new_passphrase: str,
) -> None:
    """Re-encrypt a sync profile with a new passphrase."""
    if old_passphrase == new_passphrase:
        raise click.ClickException("New passphrase must differ from the old passphrase.")
    pdir = Path(profiles_dir)
    try:
        vars_ = rotate_profile(pdir, profile, old_passphrase, new_passphrase)
    except RotationError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Rotated profile '{profile}' ({len(vars_)} variable(s)).")
