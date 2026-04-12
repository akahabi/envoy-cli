import click
from envoy.env_switch import switch_env, current_env, SwitchError


@click.group("switch")
def env_switch_cmd():
    """Switch between named environments (profiles)."""


@env_switch_cmd.command("to")
@click.argument("profile")
@click.option(
    "--store",
    default=".envoy",
    show_default=True,
    help="Path to the encrypted store file.",
)
@click.option(
    "--profiles-dir",
    default=".envoy_profiles",
    show_default=True,
    help="Directory where profile files are stored.",
)
@click.option("--passphrase", prompt=True, hide_input=True, help="Store passphrase.")
def switch_cmd(profile: str, store: str, profiles_dir: str, passphrase: str):
    """Switch the active environment to PROFILE."""
    try:
        vars_loaded = switch_env(
            store_path=store,
            profiles_dir=profiles_dir,
            profile_name=profile,
            passphrase=passphrase,
        )
        click.echo(f"Switched to profile '{profile}'. {len(vars_loaded)} variable(s) loaded.")
    except SwitchError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@env_switch_cmd.command("current")
@click.option(
    "--store",
    default=".envoy",
    show_default=True,
    help="Path to the encrypted store file.",
)
@click.option("--passphrase", prompt=True, hide_input=True, help="Store passphrase.")
def current_cmd(store: str, passphrase: str):
    """Show the currently active environment name."""
    try:
        name = current_env(store_path=store, passphrase=passphrase)
        if name:
            click.echo(f"Current environment: {name}")
        else:
            click.echo("No active environment set.")
    except SwitchError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
