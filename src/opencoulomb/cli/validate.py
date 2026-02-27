"""Validate CLI command."""

from __future__ import annotations

import logging
from pathlib import Path

import click

logger = logging.getLogger("opencoulomb")


@click.command("validate")
@click.argument("inp_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def validate_cmd(inp_file: Path, verbose: bool) -> None:
    """Validate an .inp file and report any issues."""
    from opencoulomb.cli._logging import setup_logging

    setup_logging(verbose)

    from opencoulomb.io import read_inp

    try:
        model = read_inp(inp_file)
    except Exception as exc:
        raise click.ClickException(f"Parse error: {exc}") from exc

    click.echo(f"File: {inp_file.name}")
    click.echo(f"Model: {model.title}")

    issues: list[str] = []

    # Check faults
    if model.n_sources == 0:
        issues.append("No source faults (all faults have zero slip)")
    if model.n_receivers == 0:
        issues.append("No receiver faults (CFS will use source orientation)")

    # Check grid sanity
    grid = model.grid
    if grid.n_points > 1_000_000:
        issues.append(f"Very large grid: {grid.n_points:,} points (may be slow)")
    if grid.depth < 0:
        issues.append(f"Negative grid depth: {grid.depth} km")

    # Check fault geometry
    for i, fault in enumerate(model.faults):
        if fault.length < 1e-6:
            issues.append(f"Fault {i}: zero-length trace")
        if fault.bottom_depth > 100:
            issues.append(f"Fault {i}: very deep ({fault.bottom_depth} km)")

    # Check cross-section
    if model.cross_section is not None:
        cs = model.cross_section
        if cs.depth_max > 100:
            issues.append(f"Cross-section depth_max very large: {cs.depth_max} km")

    if issues:
        click.echo(f"\nWarnings ({len(issues)}):")
        for issue in issues:
            click.echo(f"  - {issue}")
    else:
        click.echo("\nNo issues found.")

    click.echo(
        f"\nSummary: {model.n_sources} source(s), {model.n_receivers} receiver(s), "
        f"{grid.n_points} grid points"
    )
