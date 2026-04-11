import click
from pathlib import Path
from envoy.store import load_store
from envoy.validate import validate


@click.group("validate")
def validate_cmd():
    """Validate env vars against a schema."""


@validate_cmd.command("check")
@click.argument("schema_file", type=click.Path(exists=True))
@click.option("--store", "store_path", default=".envoy", show_default=True, help="Path to the encrypted store.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Passphrase to decrypt the store.")
@click.option("--profile", default=None, help="Profile name to load vars from instead of local store.")
@click.option("--warn", "warn_as_error", is_flag=True, default=False, help="Treat warnings as errors.")
def check_cmd(schema_file, store_path, passphrase, profile, warn_as_error):
    """Check env vars against a JSON schema file."""
    import json

    try:
        schema = json.loads(Path(schema_file).read_text())
    except Exception as exc:
        raise click.ClickException(f"Failed to read schema: {exc}")

    try:
        if profile:
            from envoy.sync import pull_profile
            from pathlib import Path as _Path
            profiles_dir = _Path(store_path).parent / ".envoy_profiles"
            vars_ = pull_profile(profiles_dir, profile, passphrase)
        else:
            vars_ = load_store(store_path, passphrase)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc))
    except Exception as exc:
        raise click.ClickException(f"Could not load vars: {exc}")

    result = validate(vars_, schema)

    if not result.errors and not result.warnings:
        click.echo(click.style("✔ All checks passed.", fg="green"))
        return

    for issue in result.errors:
        click.echo(click.style(f"ERROR   {issue}", fg="red"))

    for issue in result.warnings:
        click.echo(click.style(f"WARNING {issue}", fg="yellow"))

    has_fatal = bool(result.errors) or (warn_as_error and bool(result.warnings))
    if has_fatal:
        raise click.ClickException("Validation failed.")
