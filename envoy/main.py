"""Entry point for the envoy CLI."""

import click

from envoy.cli import cli
from envoy.cli_sync import sync
from envoy.cli_audit import audit
from envoy.cli_import import import_cmd
from envoy.cli_rotate import rotate
from envoy.cli_template import template_cmd
from envoy.cli_snapshot import snapshot_cmd
from envoy.cli_compare import compare_cmd


@click.group()
@click.version_option()
def main():
    """envoy — manage and sync .env files securely."""


main.add_command(cli, name="env")
main.add_command(sync)
main.add_command(audit)
main.add_command(import_cmd, name="import")
main.add_command(rotate)
main.add_command(template_cmd, name="template")
main.add_command(snapshot_cmd, name="snapshot")
main.add_command(compare_cmd, name="compare")


if __name__ == "__main__":
    main()
