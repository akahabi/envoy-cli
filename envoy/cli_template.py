"""CLI commands for template rendering."""

import sys
from pathlib import Path

import click

from envoy.store import load_store
from envoy.template import TemplateError, extract_placeholders, render_template


@click.group("template")
def template_cmd() -> None:
    """Render templates using stored environment variables."""


@template_cmd.command("render")
@click.argument("template_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--store", "store_path", default=".envoy", show_default=True, help="Path to the envoy store file.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Passphrase for the store.")
@click.option("--output", "-o", default=None, help="Output file path (default: stdout).")
def render_cmd(template_file: str, store_path: str, passphrase: str, output: str) -> None:
    """Render TEMPLATE_FILE substituting variables from the store."""
    try:
        variables = load_store(store_path, passphrase)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error loading store: {exc}", err=True)
        sys.exit(1)

    source = Path(template_file).read_text(encoding="utf-8")

    try:
        rendered = render_template(source, variables)
    except TemplateError as exc:
        click.echo(f"Template error: {exc}", err=True)
        sys.exit(1)

    if output:
        Path(output).write_text(rendered, encoding="utf-8")
        click.echo(f"Rendered template written to {output}")
    else:
        click.echo(rendered, nl=False)


@template_cmd.command("inspect")
@click.argument("template_file", type=click.Path(exists=True, dir_okay=False))
def inspect_cmd(template_file: str) -> None:
    """List all variable placeholders found in TEMPLATE_FILE."""
    source = Path(template_file).read_text(encoding="utf-8")
    placeholders = extract_placeholders(source)

    if not placeholders:
        click.echo("No placeholders found.")
        return

    click.echo(f"Found {len(placeholders)} placeholder(s):")
    for name, default in sorted(placeholders.items()):
        default_str = f"  (default: {default!r})" if default is not None else ""
        click.echo(f"  {name}{default_str}")
