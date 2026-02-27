"""Convert CLI command."""

from __future__ import annotations

import logging
from pathlib import Path

import click

logger = logging.getLogger("opencoulomb")

_FORMATS = ["cou", "csv", "dat", "summary"]


@click.command("convert")
@click.argument("inp_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--format", "-f", "fmt",
    type=click.Choice(_FORMATS),
    required=True,
    help="Output format",
)
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None, help="Output file path")
@click.option("--field", type=click.Choice(["cfs", "shear", "normal"]), default="cfs", help="Field for .dat output")
@click.option("--receiver", type=int, default=None, help="Receiver fault index (0-based)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def convert_cmd(
    inp_file: Path,
    fmt: str,
    output: Path | None,
    field: str,
    receiver: int | None,
    verbose: bool,
) -> None:
    """Convert an .inp file to a specific output format.

    Computes CFS and writes results in the chosen format.
    """
    from opencoulomb.cli._logging import setup_logging

    setup_logging(verbose)

    from opencoulomb.core import compute_grid
    from opencoulomb.io import read_inp

    logger.info("Parsing %s", inp_file.name)
    model = read_inp(inp_file)

    logger.info("Computing grid CFS...")
    result = compute_grid(model, receiver_index=receiver)

    stem = inp_file.stem
    if output is None:
        ext_map = {"cou": "_dcff.cou", "csv": ".csv", "dat": f"_{field}.dat", "summary": "_summary.txt"}
        output = inp_file.parent / f"{stem}{ext_map[fmt]}"

    if fmt == "cou":
        from opencoulomb.io import write_dcff_cou

        write_dcff_cou(result, model, output)
    elif fmt == "csv":
        from opencoulomb.io import write_csv

        write_csv(result, output)
    elif fmt == "dat":
        from opencoulomb.io import write_coulomb_dat

        write_coulomb_dat(result, output, field=field)
    elif fmt == "summary":
        from opencoulomb.io import write_summary

        write_summary(result, model, output)

    click.echo(f"Wrote: {output}")
