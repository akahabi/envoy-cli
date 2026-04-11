"""CLI commands for checking env vars against a .env.example reference file."""

from __future__ import annotations

from pathlib import Path

import click

from envoy.env_check import EnvCheckError, check_against_example


@click.group("check")
def env_check_cmd() -> None:
    """Check store vars against a reference .env.example."""


@env_check_cmd.command("run")
@click.option("--store", default=".envoy", show_default=True, help="Path to the encrypted store file.")
@click.option("--example", default=".env.example", show_default=True, help="Path to the .env.example reference file.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Passphrase to decrypt the store.")
@click.option("--ignore-extra", is_flag=True, default=False, help="Do not report keys present in store but absent from example.")
@click.option("--show-present", is_flag=True, default=False, help="Also list keys that are correctly present.")
def run_cmd(
    store: str,
    example: str,
    passphrase: str,
    ignore_extra: bool,
    show_present: bool,
) -> None:
    """Run the env-check and report missing / extra keys."""
    try:
        result = check_against_example(
            Path(store),
            passphrase,
            Path(example),
            ignore_extra=ignore_extra,
        )
    except EnvCheckError as exc:
        raise click.ClickException(str(exc)) from exc

    if result.missing:
        click.echo(click.style("Missing keys:", fg="red", bold=True))
        for key in result.missing:
            click.echo(f"  - {key}")

    if result.extra:
        click.echo(click.style("Extra keys:", fg="yellow", bold=True))
        for key in result.extra:
            click.echo(f"  + {key}")

    if show_present and result.present:
        click.echo(click.style("Present keys:", fg="green", bold=True))
        for key in result.present:
            click.echo(f"  ✓ {key}")

    if result.ok:
        click.echo(click.style("All required vars are present.", fg="green"))
    else:
        raise SystemExit(1)
