"""CLI entry point for envoy."""

import click
from pathlib import Path
from typing import Optional

from envoy.store import set_env_var, get_env_vars, load_store, save_store


@click.group()
@click.version_option("0.1.0", prog_name="envoy")
def cli() -> None:
    """envoy — manage and sync .env files with encrypted storage."""


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--env", default="local", show_default=True, help="Target environment.")
@click.password_option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True)
def set_var(key: str, value: str, env: str, passphrase: str) -> None:
    """Set KEY=VALUE in the specified environment."""
    set_env_var(env, key, value, passphrase)
    click.echo(f"✔ Set {key} in [{env}]")


@cli.command("get")
@click.argument("key")
@click.option("--env", default="local", show_default=True, help="Target environment.")
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def get_var(key: str, env: str, passphrase: str) -> None:
    """Print the value of KEY from the specified environment."""
    vars_ = get_env_vars(env, passphrase)
    if key not in vars_:
        raise click.ClickException(f"Key '{key}' not found in [{env}]")
    click.echo(vars_[key])


@cli.command("list")
@click.option("--env", default="local", show_default=True, help="Target environment.")
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def list_vars(env: str, passphrase: str) -> None:
    """List all variables for the specified environment."""
    vars_ = get_env_vars(env, passphrase)
    if not vars_:
        click.echo(f"No variables stored for [{env}]")
        return
    for k, v in sorted(vars_.items()):
        click.echo(f"{k}={v}")


@cli.command("export")
@click.option("--env", default="local", show_default=True, help="Target environment.")
@click.option("--output", "-o", type=click.Path(), default=".env", show_default=True)
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def export_vars(env: str, output: str, passphrase: str) -> None:
    """Export variables to a .env file."""
    vars_ = get_env_vars(env, passphrase)
    lines = [f"{k}={v}\n" for k, v in sorted(vars_.items())]
    Path(output).write_text("".join(lines), encoding="utf-8")
    click.echo(f"✔ Exported {len(lines)} variable(s) to {output}")
