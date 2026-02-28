"""Focal mechanism beachball plotting.

Uses ObsPy's beachball rendering (install via ``pip install opencoulomb[network]``).
Falls back to a simple circle representation if ObsPy is not available.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib.patches as mpatches
import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from opencoulomb.types.catalog import EarthquakeCatalog
    from opencoulomb.types.model import CoulombModel
    from opencoulomb.types.result import CoulombResult


def _get_beach() -> Any:
    """Import ObsPy beach function."""
    try:
        from obspy.imaging.beachball import beach  # type: ignore[import-not-found]
        return beach
    except ImportError:
        return None


def plot_beachball(
    strike: float,
    dip: float,
    rake: float,
    xy: tuple[float, float],
    ax: Axes,
    size: float = 20.0,
    facecolor: str | tuple[float, ...] = "red",
    bgcolor: str = "white",
    linewidth: float = 1.0,
) -> None:
    """Plot a single focal mechanism beachball.

    Parameters
    ----------
    strike, dip, rake : float
        Focal mechanism (degrees).
    xy : tuple[float, float]
        Position on axes.
    ax : Axes
        Matplotlib axes.
    size : float
        Beachball size in points.
    facecolor : str or tuple of float
        Compressional quadrant color (name or RGBA tuple).
    bgcolor : str
        Dilatational quadrant color.
    linewidth : float
        Circle outline width.
    """
    beach_fn = _get_beach()
    if beach_fn is not None:
        b = beach_fn(
            [strike, dip, rake],
            xy=xy,
            width=size,
            facecolor=facecolor,
            bgcolor=bgcolor,
            linewidth=linewidth,
        )
        ax.add_collection(b)
    else:
        # Fallback: simple colored circle
        circle = mpatches.Circle(xy, size / 2, color=facecolor, alpha=0.7)
        ax.add_patch(circle)


def plot_beachballs_on_map(
    result: CoulombResult,
    model: CoulombModel,
    catalog: EarthquakeCatalog | None = None,
    ax: Axes | None = None,
    color_by_cfs: bool = True,
    size_by_magnitude: bool = True,
    cmap: Any | None = None,
) -> tuple[Figure, Axes]:
    """Plot focal mechanism beachballs on a CFS map.

    If catalog is provided, plots catalog events with focal mechanisms
    colored by interpolated CFS. Otherwise, plots receiver fault
    orientations as beachballs.

    Parameters
    ----------
    result : CoulombResult
        CFS computation result.
    model : CoulombModel
        Input model.
    catalog : EarthquakeCatalog or None
        Optional earthquake catalog with events.
    ax : Axes or None
        Existing axes. Creates new figure if None.
    color_by_cfs : bool
        Color beachballs by CFS value (red=+, blue=-).
    size_by_magnitude : bool
        Scale beachball size by magnitude.
    cmap : colormap or None
        Custom colormap. Defaults to RdBu_r.

    Returns
    -------
    tuple[Figure, Axes]
    """
    from opencoulomb.viz.colormaps import coulomb_cmap, symmetric_norm
    from opencoulomb.viz.maps import plot_cfs_map

    if ax is None:
        fig, ax = plot_cfs_map(result, model, show_faults=True)
    else:
        fig = ax.figure  # type: ignore[assignment]

    if cmap is None:
        cmap = coulomb_cmap()

    cfs_grid = result.cfs_grid()
    vmax = float(np.max(np.abs(cfs_grid)))
    norm = symmetric_norm(vmax)

    if catalog is not None and catalog.events:
        # Interpolate CFS at catalog event locations
        from scipy.interpolate import RegularGridInterpolator  # type: ignore[import-untyped]

        n_y, n_x = result.grid_shape
        x_1d = result.stress.x.reshape(n_y, n_x)[0, :]
        y_1d = result.stress.y.reshape(n_y, n_x)[:, 0]

        interp = RegularGridInterpolator(
            (y_1d, x_1d), cfs_grid,
            method="linear", bounds_error=False, fill_value=0.0,
        )

        for ev in catalog.events:
            # Catalog coords need to be in model km coordinates
            cfs_val = float(interp((ev.latitude, ev.longitude)))

            if color_by_cfs:
                rgba = cmap(norm(cfs_val))
                color = rgba[:3] if hasattr(rgba, '__len__') else "gray"
            else:
                color = "red" if cfs_val > 0 else "blue"

            size = 15.0
            if size_by_magnitude:
                size = max(5.0, ev.magnitude * 5.0)

            # Use receiver orientation as default focal mechanism
            plot_beachball(
                result.receiver_strike, result.receiver_dip, result.receiver_rake,
                xy=(ev.longitude, ev.latitude),
                ax=ax, size=size, facecolor=color,
            )
    else:
        # Plot receiver fault orientations
        for recv in model.receiver_faults:
            plot_beachball(
                recv.strike_deg, recv.dip, recv.rake_deg,
                xy=(recv.center_x, recv.center_y),
                ax=ax, size=15.0, facecolor="gray",
            )

    return fig, ax
