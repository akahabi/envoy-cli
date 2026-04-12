"""CLI commands for comparing environments."""

import sys
from pathlib import Path

import click

from envoy.compare import compare_store_to_profile, compare_profiles, CompareError
from envoy.diff import summary, has_differences


@click.group()
def compare_cmd():
    """Compare variables between environments."""


@compare_cmd.command("store-profile")
@click.argument("profile")
@click.option("--store", default=".envoy", show_default=True, help="Path to local store.")
@click.option("--store-pass", prompt=True, hide_input=True, help="Local store passphrase.")
@click.option("--profile-pass", prompt=True, hide_input=True, help="Profile passphrase.")
@click.option("--show-unchanged", is_flag=True, default=False, help="Also list unchanged keys.")
def store_profile_cmd(profile, store, store_pass, profile_pass, show_unchanged):
    """Compare local store to a remote profile."""
    try:
        result = compare_store_to_profile(
            Path(store), profile, store_pass, profile_pass
        )
    except CompareError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    _print_diff(result, show_unchanged)


@compare_cmd.command("profiles")
@click.argument("profile_a")
@click.argument("profile_b")
@click.option("--pass-a", prompt="Passphrase for first profile", hide_input=True)
@click.option("--pass-b", prompt="Passphrase for second profile", hide_input=True)
@click.option("--show-unchanged", is_flag=True, default=False)
def profiles_cmd(profile_a, profile_b, pass_a, pass_b, show_unchanged):
    """Compare two named profiles."""
    try:
        result = compare_profiles(profile_a, profile_b, pass_a, pass_b)
    except CompareError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    _print_diff(result, show_unchanged)


def _print_diff(result, show_unchanged: bool):
    """Print a colour-coded diff of the comparison result.

    Exits with a non-zero status code when differences are found, so the
    command can be used reliably in scripts and CI pipelines.
    """
    for item in result:
        if item.status == "added":
            click.echo(click.style(f"+ {item.key} = {item.target_value}", fg="green"))
        elif item.status == "removed":
            click.echo(click.style(f"- {item.key} = {item.source_value}", fg="red"))
        elif item.status == "changed":
            click.echo(click.style(f"~ {item.key}: {item.source_value!r} -> {item.target_value!r}", fg="yellow"))
        elif show_unchanged:
            click.echo(f"  {item.key} = {item.source_value}")

    click.echo()
    click.echo(summary(result))
    if not has_differences(result):
        click.echo("Environments are in sync.")
    else:
        sys.exit(1)
