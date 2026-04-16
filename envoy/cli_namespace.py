"""CLI commands for namespace management."""
from __future__ import annotations

from pathlib import Path

import click

from envoy.namespace import NamespaceError, delete_namespace, get_namespace, list_namespaces, set_namespace_var


@click.group("namespace")
def namespace_cmd() -> None:
    """Manage namespaced environment variables."""


@namespace_cmd.command("list")
@click.option("--store", default=".envoy", show_default=True)
def list_cmd(store: str) -> None:
    """List all namespaces present in the store."""
    namespaces = list_namespaces(Path(store))
    if not namespaces:
        click.echo("No namespaces found.")
        return
    for ns in namespaces:
        click.echo(ns)


@namespace_cmd.command("show")
@click.argument("namespace")
@click.option("--store", default=".envoy", show_default=True)
def show_cmd(namespace: str, store: str) -> None:
    """Show vars inside NAMESPACE (prefix stripped)."""
    vars_ = get_namespace(Path(store), namespace)
    if not vars_:
        click.echo(f"No vars found in namespace '{namespace}'.")
        return
    for k, v in sorted(vars_.items()):
        click.echo(f"{k}={v}")


@namespace_cmd.command("set")
@click.argument("namespace")
@click.argument("key")
@click.argument("value")
@click.option("--store", default=".envoy", show_default=True)
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def set_cmd(namespace: str, key: str, value: str, store: str, passphrase: str) -> None:
    """Set KEY=VALUE inside NAMESPACE."""
    try:
        full_key = set_namespace_var(Path(store), namespace, key, value, passphrase)
        click.echo(f"Set {full_key}")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@namespace_cmd.command("delete")
@click.argument("namespace")
@click.option("--store", default=".envoy", show_default=True)
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True)
def delete_cmd(namespace: str, store: str, passphrase: str) -> None:
    """Delete all vars in NAMESPACE."""
    try:
        deleted = delete_namespace(Path(store), namespace, passphrase)
        click.echo(f"Deleted {len(deleted)} key(s): {', '.join(deleted)}")
    except NamespaceError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
