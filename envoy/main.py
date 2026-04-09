"""Main entry point combining all CLI command groups."""

import click
from envoy.cli import cli
from envoy.cli_sync import sync
from envoy.cli_audit import audit


@click.group()
@click.version_option(version="0.1.0", prog_name="envoy")
def main():
    """envoy — Manage and sync .env files across environments."""
    pass


main.add_command(cli, name="env")
main.add_command(sync, name="sync")
main.add_command(audit, name="audit")


if __name__ == "__main__":
    main()
