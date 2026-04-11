"""Entry-point that assembles all CLI command groups."""

from __future__ import annotations

import click

from envoy.cli import cli
from envoy.cli_audit import audit
from envoy.cli_compare import compare_cmd
from envoy.cli_env_check import env_check_cmd
from envoy.cli_import import import_cmd
from envoy.cli_rotate import rotate
from envoy.cli_snapshot import snapshot_cmd
from envoy.cli_sync import sync
from envoy.cli_tag import tag_cmd
from envoy.cli_template import template_cmd
from envoy.lint_cli import lint_cmd
from envoy.validate_cli import validate_cmd


def main() -> None:
    """Register all sub-commands and invoke the root CLI."""
    cli.add_command(sync)
    cli.add_command(audit)
    cli.add_command(import_cmd)
    cli.add_command(rotate)
    cli.add_command(template_cmd)
    cli.add_command(snapshot_cmd)
    cli.add_command(compare_cmd)
    cli.add_command(lint_cmd)
    cli.add_command(validate_cmd)
    cli.add_command(env_check_cmd)
    cli.add_command(tag_cmd)
    cli()


if __name__ == "__main__":
    main()
