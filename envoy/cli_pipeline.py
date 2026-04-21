"""CLI commands for running and inspecting envoy pipelines."""

import json
import sys
from pathlib import Path

import click

from envoy.pipeline import (
    PipelineError,
    PipelineResult,
    build_pipeline,
    run_pipeline,
)


@click.group("pipeline")
def pipeline_cmd():
    """Define and run multi-step env transformation pipelines."""


@pipeline_cmd.command("run")
@click.argument("store", type=click.Path(exists=True, dir_okay=False))
@click.argument("pipeline_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--passphrase", envvar="ENVOY_PASSPHRASE", prompt=True, hide_input=True,
              help="Passphrase for the store.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Print steps without applying changes.")
@click.option("--output", type=click.Choice(["text", "json"]), default="text",
              help="Output format for the result summary.")
def run_cmd(store: str, pipeline_file: str, passphrase: str, dry_run: bool, output: str):
    """Run a pipeline definition against a store.

    STORE is the path to the encrypted .env store.
    PIPELINE_FILE is a JSON file describing the pipeline steps.
    """
    try:
        raw = Path(pipeline_file).read_text(encoding="utf-8")
        definition = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        click.echo(f"Error reading pipeline file: {exc}", err=True)
        sys.exit(1)

    try:
        pipeline = build_pipeline(definition)
    except PipelineError as exc:
        click.echo(f"Pipeline build error: {exc}", err=True)
        sys.exit(1)

    if dry_run:
        click.echo(f"Dry run — {len(pipeline)} step(s) defined:")
        for i, step in enumerate(pipeline, 1):
            click.echo(f"  {i}. {step}")
        return

    try:
        result: PipelineResult = run_pipeline(store, passphrase, pipeline)
    except PipelineError as exc:
        click.echo(f"Pipeline failed: {exc}", err=True)
        sys.exit(1)

    if output == "json":
        click.echo(json.dumps(result.summary(), indent=2))
    else:
        status = "OK" if result.ok else "FAILED"
        click.echo(f"Pipeline {status} — {len(result.steps)} step(s) executed.")
        for step in result.steps:
            icon = "✓" if step.get("ok") else "✗"
            click.echo(f"  {icon} {step.get('name', 'unknown')}: {step.get('message', '')}")

    if not result.ok:
        sys.exit(1)


@pipeline_cmd.command("validate")
@click.argument("pipeline_file", type=click.Path(exists=True, dir_okay=False))
def validate_cmd(pipeline_file: str):
    """Validate a pipeline definition file without running it.

    PIPELINE_FILE is a JSON file describing the pipeline steps.
    """
    try:
        raw = Path(pipeline_file).read_text(encoding="utf-8")
        definition = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        click.echo(f"Error reading pipeline file: {exc}", err=True)
        sys.exit(1)

    try:
        pipeline = build_pipeline(definition)
        click.echo(f"Pipeline is valid — {len(pipeline)} step(s) defined.")
        for i, step in enumerate(pipeline, 1):
            click.echo(f"  {i}. {step}")
    except PipelineError as exc:
        click.echo(f"Invalid pipeline: {exc}", err=True)
        sys.exit(1)
