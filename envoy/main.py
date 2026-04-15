"""Entry-point that registers all CLI command groups."""

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
from envoy.cli_secret_scan import scan_cmd
from envoy.cli_ttl import ttl_cmd
from envoy.cli_search import search_cmd
from envoy.cli_promote import promote_cmd
from envoy.cli_rename import rename_cmd


@click.group()
def main() -> None:
    """envoy — manage and sync .env files with encrypted storage."""


main.add_command(cli)
main.add_command(sync)
main.add_command(audit)
main.add_command(import_cmd)
main.add_command(rotate)
main.add_command(template_cmd)
main.add_command(snapshot_cmd)
main.add_command(compare_cmd)
main.add_command(lint_cmd)
main.add_command(validate_cmd)
main.add_command(env_check_cmd)
main.add_command(tag_cmd)
main.add_command(env_switch_cmd)
main.add_command(history_cmd)
main.add_command(remind_cmd)
main.add_command(alias_cmd)
main.add_command(pin_cmd)
main.add_command(watch_cmd)
main.add_command(scan_cmd)
main.add_command(ttl_cmd)
main.add_command(search_cmd)
main.add_command(promote_cmd)
main.add_command(rename_cmd)


if __name__ == "__main__":
    main()
