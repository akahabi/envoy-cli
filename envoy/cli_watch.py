"""CLI commands for watching a store file for live changes."""

from __future__ import annotations

import click
from pathlib import Path

from envoy.watch import watch, WatchError


@click.group("watch")
def watch_cmd() -> None:
    """Watch a store file and report changes in real time."""


def _format_diff(diff: dict) -> None:
    """Pretty-print a diff dict to stdout."""
    for key, old, new in diff.get("added", []):
        click.echo(click.style(f"  + {key}={new}", fg="green"))
    for key, old, new in diff.get("removed", []):
        click.echo(click.style(f"  - {key} (was {old})", fg="red"))
    for key, old, new in diff.get("changed", []):
        click.echo(click.style(f"  ~ {key}: {old} -> {new}", fg="yellow"))


@watch_cmd.command("run")
@click.argument("store", type=click.Path(dir_okay=False))
@click.option("--passphrase", prompt=True, hide_input=True, help="Store passphrase.")
@click.option(
    "--interval",
    default=1.0,
    show_default=True,
    type=float,
    help="Poll interval in seconds.",
)
def run_cmd(store: str, passphrase: str, interval: float) -> None:
    """Watch STORE for changes and print a live diff."""
    store_path = Path(store)
    click.echo(f"Watching {store_path} (Ctrl-C to stop)…")

    def on_change(diff: dict) -> None:
        click.echo(click.style("[change detected]", bold=True))
        _format_diff(diff)

    try:
        watch(store_path, passphrase, on_change=on_change, interval=interval)
    except WatchError as exc:
        raise click.ClickException(str(exc)) from exc
    except KeyboardInterrupt:
        click.echo("\nStopped watching.")
