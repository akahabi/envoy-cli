"""CLI commands for quota management."""

from __future__ import annotations

from pathlib import Path

import click

from envoy.quota import QuotaError, check_quota, get_quota, remove_quota, set_quota
from envoy.store import load_store


@click.group("quota")
def quota_cmd() -> None:
    """Manage variable count quotas for stores and namespaces."""


@quota_cmd.command("set")
@click.argument("store", type=click.Path())
@click.argument("limit", type=int)
@click.option("--namespace", "-n", default=None, help="Restrict quota to a namespace prefix.")
@click.option("--passphrase", "-p", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def set_cmd(store: str, limit: int, namespace: str | None, passphrase: str) -> None:
    """Set a quota LIMIT on STORE (optionally scoped to a NAMESPACE)."""
    store_path = Path(store)
    try:
        rules = set_quota(store_path, limit, namespace)
        scope = f"namespace '{namespace}'" if namespace else "global"
        click.echo(f"Quota set: {scope} → {limit} vars")
        click.echo(f"All rules: {rules}")
    except QuotaError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@quota_cmd.command("get")
@click.argument("store", type=click.Path())
@click.option("--namespace", "-n", default=None)
def get_cmd(store: str, namespace: str | None) -> None:
    """Show the current quota limit for STORE or a NAMESPACE."""
    store_path = Path(store)
    limit = get_quota(store_path, namespace)
    scope = f"namespace '{namespace}'" if namespace else "global"
    click.echo(f"Quota ({scope}): {limit}")


@quota_cmd.command("remove")
@click.argument("store", type=click.Path())
@click.option("--namespace", "-n", default=None)
def remove_cmd(store: str, namespace: str | None) -> None:
    """Remove a quota rule, reverting to the default limit."""
    remove_quota(Path(store), namespace)
    scope = f"namespace '{namespace}'" if namespace else "global"
    click.echo(f"Quota rule removed for {scope}.")


@quota_cmd.command("check")
@click.argument("store", type=click.Path(exists=True))
@click.option("--namespace", "-n", default=None)
@click.option("--passphrase", "-p", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def check_cmd(store: str, namespace: str | None, passphrase: str) -> None:
    """Check whether STORE currently exceeds its quota."""
    store_path = Path(store)
    vars_ = load_store(store_path, passphrase)
    try:
        check_quota(store_path, vars_, namespace)
        scope = f"namespace '{namespace}'" if namespace else "store"
        click.echo(f"OK — {scope} is within quota.")
    except QuotaError as exc:
        click.echo(f"Quota violation: {exc}", err=True)
        raise SystemExit(1)
