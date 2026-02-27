"""Cross-section visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from opencoulomb.types.section import CrossSectionResult


def plot_cross_section(
    section: CrossSectionResult,
    field: str = "cfs",
    ax: Axes | None = None,
    vmax: float | None = None,
    contour_levels: int = 20,
) -> tuple[Figure, Axes]:
    """Plot a cross-section as filled contours.

    Parameters
    ----------
    section : CrossSectionResult
    field : str — 'cfs', 'shear', 'normal'
    ax : Axes or None
    vmax : float or None
    contour_levels : int
    """
    from opencoulomb.viz._base import add_colorbar, create_figure, finalize_figure
    from opencoulomb.viz.colormaps import coulomb_cmap, symmetric_norm

    if ax is None:
        fig, ax = create_figure(figsize=(12, 6))
    else:
        fig = ax.get_figure()
        if fig is None:
            msg = "Axes has no parent figure"
            raise ValueError(msg)

    field_map = {"cfs": section.cfs, "shear": section.shear, "normal": section.normal}
    if field not in field_map:
        raise ValueError(
            f"Unknown field '{field}'. Must be one of: {sorted(field_map.keys())}"
        )
    data = field_map[field]

    norm = symmetric_norm(data, vmax=vmax)
    cf = ax.contourf(
        section.distance,
        section.depth,
        data,
        levels=contour_levels,
        cmap=coulomb_cmap(),
        norm=norm,
    )
    add_colorbar(cf, ax, label=f"{field.upper()} (bar)")

    ax.set_xlabel("Distance along profile (km)", fontsize=10)
    ax.set_ylabel("Depth (km)", fontsize=10)
    ax.invert_yaxis()  # depth increases downward
    ax.tick_params(labelsize=9)

    spec = section.spec
    title = (
        f"Cross Section: ({spec.start_x:.1f}, {spec.start_y:.1f}) to "
        f"({spec.finish_x:.1f}, {spec.finish_y:.1f})"
    )
    finalize_figure(fig, title=title)
    return fig, ax
