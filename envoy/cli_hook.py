"""CLI commands for managing store event hooks."""
import click
from pathlib import Path
from envoy.hook import add_hook, remove_hook, list_hooks, fire_hooks, HOOK_EVENTS, HookError


@click.group("hook")
def hook_cmd():
    """Manage shell hooks triggered on store events."""


@hook_cmd.command("add")
@click.argument("event")
@click.argument("command")
@click.option("--store", default=".envoy/store.enc", show_default=True)
def add_cmd(event: str, command: str, store: str) -> None:
    """Register COMMAND to run on EVENT."""
    try:
        hooks = add_hook(Path(store), event, command)
        click.echo(f"Hook added for '{event}'. Total: {len(hooks)} command(s).")
    except HookError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@hook_cmd.command("remove")
@click.argument("event")
@click.argument("command")
@click.option("--store", default=".envoy/store.enc", show_default=True)
def remove_cmd(event: str, command: str, store: str) -> None:
    """Remove COMMAND from EVENT hooks."""
    try:
        hooks = remove_hook(Path(store), event, command)
        click.echo(f"Hook removed. Remaining: {len(hooks)} command(s).")
    except HookError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@hook_cmd.command("list")
@click.option("--event", default=None, help="Filter by event name.")
@click.option("--store", default=".envoy/store.enc", show_default=True)
def list_cmd(event: str, store: str) -> None:
    """List registered hooks."""
    try:
        hooks = list_hooks(Path(store), event)
    except HookError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    any_found = False
    for ev, cmds in hooks.items():
        if cmds:
            any_found = True
            click.echo(f"[{ev}]")
            for cmd in cmds:
                click.echo(f"  {cmd}")
    if not any_found:
        click.echo("No hooks registered.")


@hook_cmd.command("fire")
@click.argument("event")
@click.option("--store", default=".envoy/store.enc", show_default=True)
def fire_cmd(event: str, store: str) -> None:
    """Manually fire all hooks for EVENT."""
    try:
        outputs = fire_hooks(Path(store), event)
        click.echo(f"Fired {len(outputs)} hook(s) for '{event}'.")
        for out in outputs:
            if out:
                click.echo(out)
    except HookError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
