"""Entry-point that assembles all CLI command groups."""

from __future__ import annotations

import click

from envoy.cli import cli
from envoy.cli_sync import sync
from envoy.cli_audit import audit
from envoy.cli_import import import_cmd
from envoy.cli_rotate import rotate


@click.group()
def main() -> None:
    """envoy — manage and sync .env files with encrypted storage."""


main.add_command(cli, name="env")
main.add_command(sync)
main.add_command(audit)
main.add_command(import_cmd, name="import")
main.add_command(rotate)


if __name__ == "__main__":
    main()
