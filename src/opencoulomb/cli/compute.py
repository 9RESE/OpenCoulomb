"""Compute CLI command."""
from __future__ import annotations

import logging
from pathlib import Path

import click

logger = logging.getLogger("opencoulomb")


@click.command("compute")
@click.argument("inp_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--output-dir", "-o", type=click.Path(path_type=Path), default=None, help="Output directory (default: same as input)")
@click.option("--format", "-f", "formats", type=click.Choice(["cou", "csv", "dat", "all"]), multiple=True, default=["all"], help="Output formats")
@click.option("--field", type=click.Choice(["cfs", "shear", "normal"]), default="cfs", help="Field for .dat output")
@click.option("--receiver", type=int, default=None, help="Receiver fault index (0-based)")
@click.option("--cross-section/--no-cross-section", default=True, help="Compute cross-section if available")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def compute_cmd(
    inp_file: Path,
    output_dir: Path | None,
    formats: tuple[str, ...],
    field: str,
    receiver: int | None,
    cross_section: bool,
    verbose: bool,
) -> None:
    """Compute Coulomb failure stress from an .inp file."""
    from opencoulomb.cli._logging import setup_logging
    setup_logging(verbose)

    if output_dir is None:
        output_dir = inp_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = inp_file.stem

    # Parse
    from opencoulomb.io import read_inp
    logger.info("Parsing %s", inp_file.name)
    model = read_inp(inp_file)
    logger.info("Model: %s (%d sources, %d receivers)", model.title, model.n_sources, model.n_receivers)

    # Compute grid
    from opencoulomb.core import compute_grid
    logger.info("Computing grid CFS...")
    result = compute_grid(model, receiver_index=receiver)
    logger.info("Grid: %d x %d points", result.grid_shape[1], result.grid_shape[0])

    # Determine output formats
    write_all = "all" in formats

    # Write outputs
    from opencoulomb.io import write_coulomb_dat, write_csv, write_dcff_cou, write_summary

    if write_all or "cou" in formats:
        path = output_dir / f"{stem}_dcff.cou"
        write_dcff_cou(result, model, path)
        logger.info("Wrote %s", path.name)

    if write_all or "csv" in formats:
        path = output_dir / f"{stem}.csv"
        write_csv(result, path)
        logger.info("Wrote %s", path.name)

    if write_all or "dat" in formats:
        path = output_dir / f"{stem}_{field}.dat"
        write_coulomb_dat(result, path, field=field)
        logger.info("Wrote %s", path.name)

    # Summary (always)
    if write_all:
        path = output_dir / f"{stem}_summary.txt"
        write_summary(result, model, path)
        logger.info("Wrote %s", path.name)

    # Cross-section
    if cross_section and model.cross_section is not None:
        from opencoulomb.core import compute_cross_section
        from opencoulomb.io import write_section_cou
        logger.info("Computing cross-section...")
        section = compute_cross_section(model, receiver_index=receiver)
        path = output_dir / f"{stem}_section.cou"
        write_section_cou(section, model, path)
        logger.info("Wrote %s", path.name)

    click.echo(f"Done. Output in {output_dir}")
