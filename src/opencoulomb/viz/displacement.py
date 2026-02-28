"""Displacement field visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from opencoulomb.types.model import CoulombModel
    from opencoulomb.types.result import CoulombResult


def plot_displacement(
    result: CoulombResult,
    model: CoulombModel,
    ax: Axes | None = None,
    component: str = "horizontal",
    scale: float | None = None,
    show_faults: bool = True,
) -> tuple[Figure, Axes]:
    """Plot displacement as quiver arrows (horizontal) or filled contour (vertical).

    Parameters
    ----------
    result : CoulombResult
    model : CoulombModel
    ax : Axes or None
    component : str — 'horizontal' for quiver, 'vertical' for uz contour
    scale : float or None — quiver arrow scale
    show_faults : bool
    """
    from opencoulomb.viz._base import add_colorbar, create_figure, finalize_figure, set_axis_labels
    from opencoulomb.viz.colormaps import displacement_cmap

    if ax is None:
        fig, ax = create_figure()
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
        if fig is None:
            msg = "Axes has no parent figure"
            raise ValueError(msg)

    grid = model.grid
    n_y, n_x = result.grid_shape
    ux_2d, uy_2d, uz_2d = result.displacement_grid()

    x = np.linspace(grid.start_x, grid.finish_x, n_x)
    y = np.linspace(grid.start_y, grid.finish_y, n_y)

    if component == "horizontal":
        mag = np.sqrt(ux_2d**2 + uy_2d**2)
        q = ax.quiver(x, y, ux_2d, uy_2d, mag, cmap=displacement_cmap(), scale=scale)
        add_colorbar(q, ax, label="|Displacement| (m)")
        title = "Horizontal Displacement"
    else:  # vertical
        cf = ax.contourf(x, y, uz_2d, levels=20, cmap=displacement_cmap())
        add_colorbar(cf, ax, label="Vertical Displacement (m)")
        title = "Vertical Displacement"

    if show_faults:
        from opencoulomb.viz.faults import plot_fault_traces

        plot_fault_traces(model, ax=ax, show_labels=False)

    set_axis_labels(ax)
    ax.set_aspect("equal")
    finalize_figure(fig, title=f"{title} — {model.title}")
    return fig, ax
