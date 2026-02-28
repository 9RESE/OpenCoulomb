"""Plot CLI command."""
from __future__ import annotations

import logging
from pathlib import Path

import click

logger = logging.getLogger("opencoulomb")


@click.command("plot")
@click.argument("inp_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None, help="Output image path (default: {stem}_cfs.png)")
@click.option("--type", "-t", "plot_type", type=click.Choice(["cfs", "displacement", "section", "beachball", "volume-slices", "volume-3d", "volume-gif"]), default="cfs", help="Plot type")
@click.option("--vmax", type=float, default=None, help="Symmetric color scale maximum")
@click.option("--dpi", type=int, default=300, help="Output DPI")
@click.option("--no-faults", is_flag=True, help="Hide fault traces")
@click.option("--receiver", type=int, default=None, help="Receiver fault index (0-based)")
@click.option("--catalog", "catalog_path", type=click.Path(exists=True, path_type=Path), default=None, help="Catalog CSV for beachball overlay")
@click.option("--gps", "gps_path", type=click.Path(exists=True, path_type=Path), default=None, help="GPS CSV for displacement comparison")
@click.option("--depth-min", type=float, default=0.0, help="Volume: min depth (km)")
@click.option("--depth-max", type=float, default=20.0, help="Volume: max depth (km)")
@click.option("--depth-inc", type=float, default=2.0, help="Volume: depth increment (km)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def plot_cmd(
    inp_file: Path,
    output: Path | None,
    plot_type: str,
    vmax: float | None,
    dpi: int,
    no_faults: bool,
    receiver: int | None,
    catalog_path: Path | None,
    gps_path: Path | None,
    depth_min: float,
    depth_max: float,
    depth_inc: float,
    verbose: bool,
) -> None:
    """Generate plots from an .inp file."""
    from opencoulomb.cli._logging import setup_logging
    setup_logging(verbose)

    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend

    from opencoulomb.io import read_inp
    logger.info("Parsing %s", inp_file.name)
    model = read_inp(inp_file)

    from opencoulomb.core import compute_grid
    logger.info("Computing...")
    result = compute_grid(model, receiver_index=receiver)

    if output is None:
        output = inp_file.with_name(f"{inp_file.stem}_{plot_type}.png")

    from opencoulomb.viz import plot_cfs_map, plot_displacement, save_figure
    from opencoulomb.viz import plot_cross_section as plot_xsec

    fig = None

    if plot_type == "cfs":
        fig, _ = plot_cfs_map(result, model, vmax=vmax, show_faults=not no_faults)
    elif plot_type == "displacement":
        fig, _ = plot_displacement(result, model, show_faults=not no_faults)
    elif plot_type == "section":
        from opencoulomb.core import compute_cross_section
        if model.cross_section is None:
            raise click.ClickException("No cross-section defined in input file")
        section = compute_cross_section(model, receiver_index=receiver)
        fig, _ = plot_xsec(section, vmax=vmax)
    elif plot_type == "beachball":
        from opencoulomb.viz.beachball import plot_beachballs_on_map
        catalog = None
        if catalog_path:
            from opencoulomb.io.catalog_io import read_catalog_csv
            catalog = read_catalog_csv(catalog_path)
        fig, _ = plot_beachballs_on_map(result, model, catalog=catalog)
    elif plot_type in ("volume-slices", "volume-3d", "volume-gif"):
        from opencoulomb.core.pipeline import compute_volume
        from opencoulomb.types.grid import VolumeGridSpec
        vol_spec = VolumeGridSpec(
            start_x=model.grid.start_x, start_y=model.grid.start_y,
            finish_x=model.grid.finish_x, finish_y=model.grid.finish_y,
            x_inc=model.grid.x_inc, y_inc=model.grid.y_inc,
            depth_min=depth_min, depth_max=depth_max, depth_inc=depth_inc,
        )
        vol = compute_volume(model, vol_spec, receiver_index=receiver)

        if plot_type == "volume-slices":
            from opencoulomb.viz.volume import plot_volume_slices
            fig, _ = plot_volume_slices(vol, model, vmax=vmax)
        elif plot_type == "volume-3d":
            from opencoulomb.viz.volume import plot_volume_3d
            fig, _ = plot_volume_3d(vol, model)
        else:  # volume-gif
            from opencoulomb.viz.volume import export_volume_gif
            gif_path = output if output and str(output).endswith(".gif") else inp_file.with_suffix(".gif")
            export_volume_gif(vol, model, gif_path)
            click.echo(f"Saved: {gif_path}")
            return
    else:
        raise click.ClickException(f"Unknown plot type: {plot_type}")

    # GPS overlay (works with any horizontal plot)
    if gps_path and fig is not None:
        from opencoulomb.io.gps_reader import read_gps_csv
        from opencoulomb.viz.gps import plot_gps_comparison
        gps_data = read_gps_csv(gps_path)
        ax = fig.get_axes()[0] if fig.get_axes() else None
        if ax:
            plot_gps_comparison(result, model, gps_data, ax=ax)

    if fig is not None:
        save_figure(fig, output, dpi=dpi)
        import matplotlib.pyplot as plt
        plt.close(fig)
        click.echo(f"Saved: {output}")
