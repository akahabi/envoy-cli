"""CLI commands for promoting variables between profiles."""

from __future__ import annotations

from pathlib import Path

import click

from envoy.promote import promote_profile, PromoteError
from envoy.merge import MergeStrategy


@click.group("promote")
def promote_cmd() -> None:
    """Promote variables from one profile to another."""


@promote_cmd.command("run")
@click.argument("src")
@click.argument("dst")
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", required=True, help="Encryption passphrase.")
@click.option("--store", "store_path", default=".envoy/store.enc", show_default=True, help="Path to local store file.")
@click.option("--profiles-dir", default=".envoy/profiles", show_default=True, help="Directory for profile files.")
@click.option(
    "--strategy",
    type=click.Choice([s.value for s in MergeStrategy], case_sensitive=False),
    default=MergeStrategy.KEEP_TARGET.value,
    show_default=True,
    help="Conflict resolution strategy.",
)
@click.option("--key", "keys", multiple=True, metavar="KEY", help="Specific key(s) to promote (repeatable).")
def run_cmd(
    src: str,
    dst: str,
    passphrase: str,
    store_path: str,
    profiles_dir: str,
    strategy: str,
    keys: tuple[str, ...],
) -> None:
    """Promote variables from SRC profile into DST profile."""
    try:
        merged = promote_profile(
            src_profile=src,
            dst_profile=dst,
            passphrase=passphrase,
            store_path=Path(store_path),
            profiles_dir=Path(profiles_dir),
            strategy=MergeStrategy(strategy),
            keys=list(keys) if keys else None,
        )
    except PromoteError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(
        f"Promoted {len(merged)} variable(s) from '{src}' \u2192 '{dst}' "
        f"using strategy '{strategy}'."
    )
    for key in sorted(merged):
        click.echo(f"  {key}")
