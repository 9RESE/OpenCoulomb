"""Visualization (Matplotlib-based)."""

from opencoulomb.viz._base import add_colorbar, create_figure, finalize_figure, set_axis_labels
from opencoulomb.viz.colormaps import coulomb_cmap, displacement_cmap, stress_cmap, symmetric_norm
from opencoulomb.viz.displacement import plot_displacement
from opencoulomb.viz.export import save_figure
from opencoulomb.viz.faults import plot_fault_traces
from opencoulomb.viz.maps import plot_cfs_map
from opencoulomb.viz.sections import plot_cross_section
from opencoulomb.viz.styles import (
    PUBLICATION_RCPARAMS,
    SCREEN_RCPARAMS,
    publication_style,
    screen_style,
)

__all__ = [
    "PUBLICATION_RCPARAMS",
    "SCREEN_RCPARAMS",
    "add_colorbar",
    "coulomb_cmap",
    "create_figure",
    "displacement_cmap",
    "finalize_figure",
    "plot_cfs_map",
    "plot_cross_section",
    "plot_displacement",
    "plot_fault_traces",
    "publication_style",
    "save_figure",
    "screen_style",
    "set_axis_labels",
    "stress_cmap",
    "symmetric_norm",
]
