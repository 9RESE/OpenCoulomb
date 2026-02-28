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
@click.option("--strain", is_flag=True, help="Also compute strain tensor")
@click.option("--volume", is_flag=True, help="Compute 3D volume grid")
@click.option("--depth-min", type=float, default=0.0, help="Volume: minimum depth (km)")
@click.option("--depth-max", type=float, default=20.0, help="Volume: maximum depth (km)")
@click.option("--depth-inc", type=float, default=2.0, help="Volume: depth increment (km)")
@click.option("--taper", type=click.Choice(["cosine", "linear", "elliptical"]), default=None, help="Slip taper profile")
@click.option("--taper-nx", type=int, default=5, help="Taper: subdivisions along strike")
@click.option("--taper-ny", type=int, default=3, help="Taper: subdivisions down-dip")
@click.option("--taper-width", type=float, default=0.2, help="Taper: width fraction (0-0.5)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def compute_cmd(
    inp_file: Path,
    output_dir: Path | None,
    formats: tuple[str, ...],
    field: str,
    receiver: int | None,
    cross_section: bool,
    strain: bool,
    volume: bool,
    depth_min: float,
    depth_max: float,
    depth_inc: float,
    taper: str | None,
    taper_nx: int,
    taper_ny: int,
    taper_width: float,
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
    try:
        model = read_inp(inp_file)
    except Exception as exc:
        raise click.ClickException(f"Parse error: {exc}") from exc
    logger.info("Model: %s (%d sources, %d receivers)", model.title, model.n_sources, model.n_receivers)

    # Build taper spec if requested
    taper_spec = None
    if taper is not None:
        from opencoulomb.core.tapering import TaperProfile, TaperSpec
        taper_spec = TaperSpec(
            profile=TaperProfile(taper),
            n_along_strike=taper_nx,
            n_down_dip=taper_ny,
            taper_width_fraction=taper_width,
        )

    # Compute volume or grid
    if volume:
        from opencoulomb.core.pipeline import compute_volume
        from opencoulomb.types.grid import VolumeGridSpec
        vol_spec = VolumeGridSpec(
            start_x=model.grid.start_x, start_y=model.grid.start_y,
            finish_x=model.grid.finish_x, finish_y=model.grid.finish_y,
            x_inc=model.grid.x_inc, y_inc=model.grid.y_inc,
            depth_min=depth_min, depth_max=depth_max, depth_inc=depth_inc,
        )
        logger.info("Computing 3D volume CFS (%d points)...", vol_spec.n_points)
        try:
            vol_result = compute_volume(
                model, vol_spec, receiver_index=receiver,
                compute_strain=strain, taper=taper_spec,
            )
        except Exception as exc:
            raise click.ClickException(f"Computation error: {exc}") from exc
        logger.info("Volume: %d x %d x %d", *vol_result.volume_shape)

        from opencoulomb.io.volume_writer import write_volume_csv, write_volume_slices
        vol_csv = output_dir / f"{stem}_volume.csv"
        write_volume_csv(vol_result, vol_csv)
        logger.info("Wrote %s", vol_csv.name)

        slice_dir = output_dir / f"{stem}_slices"
        paths = write_volume_slices(vol_result, slice_dir, field=field)
        logger.info("Wrote %d slice files to %s", len(paths), slice_dir)

        click.echo(f"Done. Volume output in {output_dir}")
        return

    from opencoulomb.core import compute_grid
    logger.info("Computing grid CFS...")
    try:
        result = compute_grid(
            model, receiver_index=receiver,
            compute_strain=strain, taper=taper_spec,
        )
    except Exception as exc:
        raise click.ClickException(f"Computation error: {exc}") from exc
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
