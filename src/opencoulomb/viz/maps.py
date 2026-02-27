"""CFS contour map visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from opencoulomb.types.model import CoulombModel
    from opencoulomb.types.result import CoulombResult


def plot_cfs_map(
    result: CoulombResult,
    model: CoulombModel,
    ax: Axes | None = None,
    vmax: float | None = None,
    contour_levels: int = 20,
    show_faults: bool = True,
) -> tuple[Figure, Axes]:
    """Plot CFS as a filled contour map.

    Parameters
    ----------
    result : CoulombResult
    model : CoulombModel
    ax : Axes or None — if None, creates new figure
    vmax : float or None — symmetric color limits
    contour_levels : int — number of contour levels
    show_faults : bool — overlay fault traces
    """
    from opencoulomb.viz._base import add_colorbar, create_figure, finalize_figure, set_axis_labels
    from opencoulomb.viz.colormaps import coulomb_cmap, symmetric_norm

    if ax is None:
        fig, ax = create_figure()
    else:
        fig = ax.get_figure()

    grid = model.grid
    n_y, n_x = result.grid_shape
    cfs_2d = result.cfs_grid()

    x = np.linspace(grid.start_x, grid.finish_x, n_x)
    y = np.linspace(grid.start_y, grid.finish_y, n_y)

    norm = symmetric_norm(cfs_2d, vmax=vmax)
    cf = ax.contourf(x, y, cfs_2d, levels=contour_levels, cmap=coulomb_cmap(), norm=norm)
    add_colorbar(cf, ax, label="CFS (bar)")

    if show_faults:
        from opencoulomb.viz.faults import plot_fault_traces

        plot_fault_traces(model, ax=ax)

    set_axis_labels(ax)
    ax.set_aspect("equal")
    finalize_figure(fig, title=f"Coulomb Stress Change — {model.title}")
    return fig, ax
