"""Info CLI command."""
from __future__ import annotations

from pathlib import Path

import click


@click.command("info")
@click.argument("inp_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def info_cmd(inp_file: Path) -> None:
    """Display model information from an .inp file."""
    from opencoulomb.io import read_inp
    model = read_inp(inp_file)

    click.echo(f"Model: {model.title}")
    click.echo(f"Material: Poisson={model.material.poisson:.4f}, Young={model.material.young:.0f} bar, friction={model.material.friction:.4f}")
    click.echo(f"Grid: X=[{model.grid.start_x:.2f}, {model.grid.finish_x:.2f}], Y=[{model.grid.start_y:.2f}, {model.grid.finish_y:.2f}]")
    click.echo(f"  Spacing: {model.grid.x_inc:.4f} x {model.grid.y_inc:.4f} km, Depth: {model.grid.depth:.2f} km")
    click.echo(f"  Points: {model.grid.n_x} x {model.grid.n_y} = {model.grid.n_points}")
    click.echo(f"Faults: {model.n_sources} source(s), {model.n_receivers} receiver(s)")

    for i, f in enumerate(model.source_faults):
        label = f.label or f"Source {i + 1}"
        click.echo(f"  [{i}] {label}: strike={f.strike_deg:.1f}, dip={f.dip:.1f}, slip=({f.slip_1:.3f}, {f.slip_2:.3f}) m")

    for i, f in enumerate(model.receiver_faults):
        label = f.label or f"Receiver {i + 1}"
        click.echo(f"  [{i}] {label}: strike={f.strike_deg:.1f}, dip={f.dip:.1f}")

    if model.regional_stress is not None:
        click.echo("Regional stress: defined")

    if model.cross_section is not None:
        cs = model.cross_section
        click.echo(f"Cross-section: ({cs.start_x:.1f}, {cs.start_y:.1f}) to ({cs.finish_x:.1f}, {cs.finish_y:.1f}), depth {cs.depth_min:.1f}-{cs.depth_max:.1f} km")
