"""CLI commands for scanning env vars for accidental secrets."""

from __future__ import annotations

import sys

import click

from envoy.secret_scan import scan_vars
from envoy.store import load_store


@click.group(name="scan")
def scan_cmd() -> None:
    """Scan env vars for accidental secrets or sensitive patterns."""


@scan_cmd.command(name="check")
@click.option("--store", "store_path", required=True, help="Path to the encrypted store file.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Passphrase to decrypt the store.")
@click.option("--no-key-names", is_flag=True, default=False, help="Skip checking key names for sensitive patterns.")
@click.option("--strict", is_flag=True, default=False, help="Exit non-zero even for warnings (any hit).")
def check_cmd(store_path: str, passphrase: str, no_key_names: bool, strict: bool) -> None:
    """Check the store for suspicious secret values."""
    try:
        vars_ = load_store(store_path, passphrase)
    except Exception as exc:
        click.echo(f"Error loading store: {exc}", err=True)
        sys.exit(1)

    result = scan_vars(vars_, key_patterns=not no_key_names)
    click.echo(result.summary())

    if strict and not result.clean:
        sys.exit(1)
    elif not result.clean:
        # Non-strict: still exit 1 so CI pipelines can act on it
        sys.exit(1)


@scan_cmd.command(name="list-patterns")
def list_patterns_cmd() -> None:
    """List the built-in patterns used for secret detection."""
    from envoy.secret_scan import _PATTERNS

    click.echo("Built-in detection patterns:")
    for i, (pattern, reason) in enumerate(_PATTERNS, 1):
        click.echo(f"  {i:2d}. [{reason}]")
        click.echo(f"      {pattern}")
