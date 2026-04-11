import click
from envoy.lint import lint_vars, LintResult
from envoy.store import load_store


@click.group("lint")
def lint_cmd():
    """Lint environment variable keys and values for common issues."""
    pass


@lint_cmd.command("check")
@click.option("--store", "store_path", required=True, help="Path to the encrypted store file.")
@click.option("--passphrase", prompt=True, hide_input=True, help="Passphrase to decrypt the store.")
@click.option("--warn", is_flag=True, default=False, help="Exit with non-zero code if warnings are found.")
def check_cmd(store_path: str, passphrase: str, warn: bool):
    """Check a store file for lint issues."""
    try:
        vars_ = load_store(store_path, passphrase)
    except Exception as exc:
        raise click.ClickException(str(exc))

    result: LintResult = lint_vars(vars_)

    if not result.issues:
        click.echo("No lint issues found.")
        return

    error_count = len(result.errors())
    warning_count = len(result.warnings())

    for issue in result.issues:
        prefix = click.style("ERROR", fg="red") if issue.severity == "error" else click.style("WARN", fg="yellow")
        click.echo(f"[{prefix}] {issue}")

    click.echo(f"\n{error_count} error(s), {warning_count} warning(s).")

    if error_count > 0 or (warn and warning_count > 0):
        raise SystemExit(1)
