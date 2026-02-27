"""Shared visualization utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.cm import ScalarMappable
    from matplotlib.colorbar import Colorbar
    from matplotlib.figure import Figure


def create_figure(
    figsize: tuple[float, float] = (10, 8),
    dpi: int = 150,
) -> tuple[Figure, Axes]:
    """Create a figure with a single axes."""
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    return fig, ax


def add_colorbar(
    mappable: ScalarMappable,
    ax: Axes,
    label: str = "",
    **kwargs: Any,
) -> Colorbar:
    """Add a consistently formatted colorbar."""
    fig = ax.get_figure()
    if fig is None:
        msg = "Axes has no parent figure"
        raise ValueError(msg)
    cbar = fig.colorbar(mappable, ax=ax, shrink=0.8, pad=0.02, **kwargs)
    if label:
        cbar.set_label(label, fontsize=10)
    cbar.ax.tick_params(labelsize=9)
    return cbar


def set_axis_labels(
    ax: Axes,
    xlabel: str = "East (km)",
    ylabel: str = "North (km)",
) -> None:
    """Apply standard axis labels."""
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.tick_params(labelsize=9)


def finalize_figure(
    fig: Figure,
    title: str = "",
    tight: bool = True,
) -> Figure:
    """Final formatting for a figure."""
    if title:
        fig.suptitle(title, fontsize=12, y=0.98)
    if tight:
        fig.tight_layout()
    return fig
