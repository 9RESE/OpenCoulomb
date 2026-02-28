"""Visualization (Matplotlib-based)."""

from opencoulomb.viz._base import add_colorbar, create_figure, finalize_figure, set_axis_labels
from opencoulomb.viz.beachball import plot_beachball, plot_beachballs_on_map
from opencoulomb.viz.colormaps import coulomb_cmap, displacement_cmap, stress_cmap, symmetric_norm
from opencoulomb.viz.displacement import plot_displacement
from opencoulomb.viz.export import save_figure
from opencoulomb.viz.faults import plot_fault_traces
from opencoulomb.viz.gps import compute_misfit, plot_gps_comparison
from opencoulomb.viz.maps import plot_cfs_map
from opencoulomb.viz.sections import plot_cross_section
from opencoulomb.viz.styles import (
    PUBLICATION_RCPARAMS,
    SCREEN_RCPARAMS,
    publication_style,
    screen_style,
)
from opencoulomb.viz.volume import (
    export_volume_gif,
    plot_catalog_on_volume,
    plot_volume_3d,
    plot_volume_cross_sections,
    plot_volume_slices,
)

__all__ = [
    "PUBLICATION_RCPARAMS",
    "SCREEN_RCPARAMS",
    "add_colorbar",
    "compute_misfit",
    "coulomb_cmap",
    "create_figure",
    "displacement_cmap",
    "export_volume_gif",
    "finalize_figure",
    "plot_beachball",
    "plot_beachballs_on_map",
    "plot_catalog_on_volume",
    "plot_cfs_map",
    "plot_cross_section",
    "plot_displacement",
    "plot_fault_traces",
    "plot_gps_comparison",
    "plot_volume_3d",
    "plot_volume_cross_sections",
    "plot_volume_slices",
    "publication_style",
    "save_figure",
    "screen_style",
    "set_axis_labels",
    "stress_cmap",
    "symmetric_norm",
]
