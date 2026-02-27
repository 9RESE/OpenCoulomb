"""Plot CLI command."""
from __future__ import annotations

import logging
from pathlib import Path

import click

logger = logging.getLogger("opencoulomb")


@click.command("plot")
@click.argument("inp_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None, help="Output image path (default: {stem}_cfs.png)")
@click.option("--type", "-t", "plot_type", type=click.Choice(["cfs", "displacement", "section"]), default="cfs", help="Plot type")
@click.option("--vmax", type=float, default=None, help="Symmetric color scale maximum")
@click.option("--dpi", type=int, default=300, help="Output DPI")
@click.option("--no-faults", is_flag=True, help="Hide fault traces")
@click.option("--receiver", type=int, default=None, help="Receiver fault index (0-based)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def plot_cmd(
    inp_file: Path,
    output: Path | None,
    plot_type: str,
    vmax: float | None,
    dpi: int,
    no_faults: bool,
    receiver: int | None,
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
    else:
        raise click.ClickException(f"Unknown plot type: {plot_type}")

    save_figure(fig, output, dpi=dpi)
    import matplotlib.pyplot as plt
    plt.close(fig)
    click.echo(f"Saved: {output}")
