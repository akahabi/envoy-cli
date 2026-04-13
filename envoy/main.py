"""Entry point that assembles all CLI command groups."""

from __future__ import annotations

import click

from envoy.cli import cli
from envoy.cli_sync import sync
from envoy.cli_audit import audit
from envoy.cli_import import import_cmd
from envoy.cli_rotate import rotate
from envoy.cli_template import template_cmd
from envoy.cli_snapshot import snapshot_cmd
from envoy.cli_compare import compare_cmd
from envoy.lint_cli import lint_cmd
from envoy.validate_cli import validate_cmd
from envoy.cli_env_check import env_check_cmd
from envoy.cli_tag import tag_cmd
from envoy.env_switch_cli import env_switch_cmd
from envoy.cli_history import history_cmd
from envoy.cli_remind import remind_cmd
from envoy.cli_alias import alias_cmd
from envoy.cli_pin import pin_cmd
from envoy.cli_watch import watch_cmd


@click.group()
@click.version_option()
def main() -> None:
    """envoy — manage and sync .env files with encrypted storage."""


main.add_command(cli, name="env")
main.add_command(sync)
main.add_command(audit)
main.add_command(import_cmd, name="import")
main.add_command(rotate)
main.add_command(template_cmd, name="template")
main.add_command(snapshot_cmd, name="snapshot")
main.add_command(compare_cmd, name="compare")
main.add_command(lint_cmd, name="lint")
main.add_command(validate_cmd, name="validate")
main.add_command(env_check_cmd, name="env-check")
main.add_command(tag_cmd, name="tag")
main.add_command(env_switch_cmd, name="switch")
main.add_command(history_cmd, name="history")
main.add_command(remind_cmd, name="remind")
main.add_command(alias_cmd, name="alias")
main.add_command(pin_cmd, name="pin")
main.add_command(watch_cmd, name="watch")


if __name__ == "__main__":
    main()
