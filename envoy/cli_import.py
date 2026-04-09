"""CLI commands for importing environment variables from external files."""

import click

from envoy.import_ import ImportError as EnvoyImportError
from envoy.import_ import load
from envoy.store import get_env_vars, save_store, set_env_var, load_store
from envoy.audit import record_event


@click.group("import")
def import_cmd() -> None:
    """Import environment variables from external files."""


@import_cmd.command("file")
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["env", "json", "sh"]), default=None,
              help="Force a specific format (auto-detected from extension by default).")
@click.option("--env", "environment", default="local", show_default=True,
              help="Target environment (local, staging, production).")
@click.option("--passphrase", prompt=True, hide_input=True,
              help="Passphrase used to encrypt the store.")
@click.option("--overwrite/--no-overwrite", default=False, show_default=True,
              help="Overwrite existing keys.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Preview changes without writing to the store.")
def file_cmd(
    filepath: str,
    fmt: str,
    environment: str,
    passphrase: str,
    overwrite: bool,
    dry_run: bool,
) -> None:
    """Import variables from FILEPATH into the specified environment."""
    try:
        incoming = load(filepath, fmt=fmt)
    except EnvoyImportError as exc:
        raise click.ClickException(str(exc))

    if not incoming:
        click.echo("No variables found in the file.")
        return

    store = load_store(environment, passphrase)
    existing_keys = set(get_env_vars(store).keys())

    skipped, added, updated = [], [], []
    for key, value in incoming.items():
        if key in existing_keys and not overwrite:
            skipped.append(key)
        elif key in existing_keys:
            updated.append(key)
        else:
            added.append(key)

    if dry_run:
        click.echo(f"[dry-run] Would add:    {added or '(none)'}")
        click.echo(f"[dry-run] Would update: {updated or '(none)'}")
        click.echo(f"[dry-run] Would skip:   {skipped or '(none)'}")
        return

    for key in added + updated:
        store = set_env_var(store, key, incoming[key])

    save_store(store, environment, passphrase)

    record_event(
        action="import",
        environment=environment,
        detail={
            "source": filepath,
            "added": len(added),
            "updated": len(updated),
            "skipped": len(skipped),
        },
    )

    click.echo(f"Imported from {filepath}:")
    click.echo(f"  Added:   {len(added)}")
    click.echo(f"  Updated: {len(updated)}")
    click.echo(f"  Skipped: {len(skipped)} (use --overwrite to replace existing keys)")
