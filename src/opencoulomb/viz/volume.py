"""3D volume visualization for depth-loop results."""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from opencoulomb.types.catalog import EarthquakeCatalog
    from opencoulomb.types.model import CoulombModel
    from opencoulomb.types.result import VolumeResult


def plot_volume_slices(
    volume: VolumeResult,
    _model: CoulombModel,
    depth_indices: list[int] | None = None,
    field: str = "cfs",
    n_cols: int = 3,
    vmax: float | None = None,
) -> tuple[Figure, list[Axes]]:
    """Plot a grid of 2D horizontal slices through a volume.

    Parameters
    ----------
    volume : VolumeResult
        3D computation result.
    model : CoulombModel
        Input model (for fault overlay).
    depth_indices : list[int] or None
        Which depth indices to plot. None = all.
    field : str
        Field to plot: "cfs", "shear", "normal".
    n_cols : int
        Number of subplot columns.
    vmax : float or None
        Symmetric color scale maximum. None = auto.

    Returns
    -------
    tuple[Figure, list[Axes]]
    """
    from opencoulomb.viz.colormaps import coulomb_cmap, symmetric_norm

    n_z, n_y, n_x = volume.volume_shape

    if depth_indices is None:
        depth_indices = list(range(n_z))

    n_plots = len(depth_indices)
    n_rows = math.ceil(n_plots / n_cols)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 3.5 * n_rows))
    if n_rows == 1 and n_cols == 1:
        axes_flat: list[Any] = [axes]
    else:
        axes_flat = list(np.array(axes).ravel())

    if field == "cfs":
        data_3d = volume.cfs.reshape(volume.volume_shape)
    elif field == "shear":
        data_3d = volume.shear.reshape(volume.volume_shape)
    elif field == "normal":
        data_3d = volume.normal.reshape(volume.volume_shape)
    else:
        msg = f"Unknown field: {field!r}"
        raise ValueError(msg)

    if vmax is None:
        vmax = float(np.max(np.abs(data_3d)))
    if vmax == 0:
        vmax = 1.0

    cmap = coulomb_cmap()
    norm = symmetric_norm(vmax)

    # Get x, y coordinates for contouring
    slice0 = volume.slice_at_depth(0)
    x_2d = slice0.stress.x.reshape(n_y, n_x)
    y_2d = slice0.stress.y.reshape(n_y, n_x)

    used_axes: list[Axes] = []
    for i, di in enumerate(depth_indices):
        ax = axes_flat[i]
        data_2d = data_3d[di]
        ax.contourf(x_2d, y_2d, data_2d, levels=21, cmap=cmap, norm=norm)
        ax.set_title(f"Depth = {volume.depths[di]:.1f} km")
        ax.set_aspect("equal")
        if i % n_cols == 0:
            ax.set_ylabel("North (km)")
        if i >= n_plots - n_cols:
            ax.set_xlabel("East (km)")
        used_axes.append(ax)

    # Hide unused axes
    for j in range(n_plots, len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.tight_layout()
    return fig, used_axes


def plot_volume_cross_sections(
    volume: VolumeResult,
    _model: CoulombModel,
    y_indices: list[int] | None = None,
    field: str = "cfs",
    vmax: float | None = None,
) -> tuple[Figure, list[Axes]]:
    """Plot vertical E-W cross-sections through a volume.

    Parameters
    ----------
    volume : VolumeResult
        3D computation result.
    model : CoulombModel
        Input model.
    y_indices : list[int] or None
        Which Y-indices to slice. None = [0, mid, end].
    field : str
        Field to plot.
    vmax : float or None
        Symmetric color scale maximum.

    Returns
    -------
    tuple[Figure, list[Axes]]
    """
    from opencoulomb.viz.colormaps import coulomb_cmap, symmetric_norm

    _n_z, n_y, n_x = volume.volume_shape

    if y_indices is None:
        y_indices = [0, n_y // 2, n_y - 1]
        y_indices = [yi for yi in y_indices if 0 <= yi < n_y]

    if field == "cfs":
        data_3d = volume.cfs.reshape(volume.volume_shape)
    elif field == "shear":
        data_3d = volume.shear.reshape(volume.volume_shape)
    else:
        data_3d = volume.normal.reshape(volume.volume_shape)

    if vmax is None:
        vmax = float(np.max(np.abs(data_3d)))
    if vmax == 0:
        vmax = 1.0

    n_plots = len(y_indices)
    fig, axes = plt.subplots(n_plots, 1, figsize=(10, 3 * n_plots))
    if n_plots == 1:
        axes = [axes]

    cmap = coulomb_cmap()
    norm = symmetric_norm(vmax)

    # X coordinates (1D)
    slice0 = volume.slice_at_depth(0)
    x_1d = slice0.stress.x.reshape(n_y, n_x)[0, :]
    y_1d = slice0.stress.y.reshape(n_y, n_x)[:, 0]

    used_axes: list[Axes] = []
    for i, yi in enumerate(y_indices):
        ax = axes[i]
        # data_3d[z, y, x] → slice at fixed y → (z, x)
        section = data_3d[:, yi, :]
        ax.contourf(x_1d, volume.depths, section, levels=21, cmap=cmap, norm=norm)
        ax.invert_yaxis()
        ax.set_title(f"Y = {y_1d[yi]:.1f} km")
        ax.set_ylabel("Depth (km)")
        if i == n_plots - 1:
            ax.set_xlabel("East (km)")
        used_axes.append(ax)

    fig.tight_layout()
    return fig, used_axes


def plot_volume_3d(
    volume: VolumeResult,
    _model: CoulombModel,
    field: str = "cfs",
    threshold: float | None = None,
    alpha: float = 0.3,
) -> tuple[Figure, Any]:
    """3D scatter plot of volume stress field.

    Uses mpl_toolkits.mplot3d to show points above a CFS threshold.

    Parameters
    ----------
    volume : VolumeResult
        3D computation result.
    model : CoulombModel
        Input model.
    field : str
        Field to plot.
    threshold : float or None
        Only show points with |field| > threshold. None = auto (10% of max).
    alpha : float
        Point transparency.

    Returns
    -------
    tuple[Figure, Axes3D]
    """
    from opencoulomb.viz.colormaps import coulomb_cmap, symmetric_norm

    if field == "cfs":
        data = volume.cfs
    elif field == "shear":
        data = volume.shear
    else:
        data = volume.normal

    if threshold is None:
        threshold = float(np.max(np.abs(data))) * 0.1

    mask = np.abs(data) > threshold
    x = volume.stress.x[mask]
    y = volume.stress.y[mask]
    z = -volume.stress.z[mask]  # positive depth
    vals = data[mask]

    vmax = float(np.max(np.abs(data)))
    if vmax == 0:
        vmax = 1.0

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    cmap = coulomb_cmap()
    norm = symmetric_norm(vmax)

    scatter = ax.scatter(x, y, z, c=vals, cmap=cmap, norm=norm, alpha=alpha, s=5)
    ax.set_xlabel("East (km)")
    ax.set_ylabel("North (km)")
    ax.set_zlabel("Depth (km)")
    ax.invert_zaxis()
    fig.colorbar(scatter, ax=ax, label=f"{field.upper()} (bar)", shrink=0.6)

    return fig, ax


def export_volume_gif(
    volume: VolumeResult,
    _model: CoulombModel,
    output_path: str | Path,
    field: str = "cfs",
    _axis: str = "depth",
    fps: int = 5,
    vmax: float | None = None,
) -> Path:
    """Export animated GIF cycling through volume slices.

    Parameters
    ----------
    volume : VolumeResult
        3D computation result.
    model : CoulombModel
        Input model.
    output_path : str or Path
        Output GIF file path.
    field : str
        Field to animate.
    axis : str
        Axis to animate along: "depth".
    fps : int
        Frames per second.
    vmax : float or None
        Symmetric color scale maximum.

    Returns
    -------
    Path
        Path to the written GIF file.
    """
    from matplotlib.animation import FuncAnimation, PillowWriter

    from opencoulomb.viz.colormaps import coulomb_cmap, symmetric_norm

    output_path = Path(output_path)
    n_z, n_y, n_x = volume.volume_shape

    if field == "cfs":
        data_3d = volume.cfs.reshape(volume.volume_shape)
    elif field == "shear":
        data_3d = volume.shear.reshape(volume.volume_shape)
    else:
        data_3d = volume.normal.reshape(volume.volume_shape)

    if vmax is None:
        vmax = float(np.max(np.abs(data_3d)))
    if vmax == 0:
        vmax = 1.0

    cmap = coulomb_cmap()
    norm = symmetric_norm(vmax)

    slice0 = volume.slice_at_depth(0)
    x_2d = slice0.stress.x.reshape(n_y, n_x)
    y_2d = slice0.stress.y.reshape(n_y, n_x)

    fig, ax = plt.subplots(figsize=(8, 6))

    def update(frame: int) -> list[Any]:
        ax.clear()
        ax.contourf(x_2d, y_2d, data_3d[frame], levels=21, cmap=cmap, norm=norm)
        ax.set_title(f"{field.upper()} at depth = {volume.depths[frame]:.1f} km")
        ax.set_xlabel("East (km)")
        ax.set_ylabel("North (km)")
        ax.set_aspect("equal")
        return []

    anim = FuncAnimation(fig, update, frames=n_z, interval=1000 // fps, blit=False)
    writer = PillowWriter(fps=fps)
    anim.save(str(output_path), writer=writer)
    plt.close(fig)

    return output_path


def plot_catalog_on_volume(
    volume: VolumeResult,
    _model: CoulombModel,
    catalog: EarthquakeCatalog,
    field: str = "cfs",
    depth_index: int | None = None,
) -> tuple[Figure, Axes]:
    """Overlay earthquake catalog on a volume depth slice.

    Parameters
    ----------
    volume : VolumeResult
        3D computation result.
    model : CoulombModel
        Input model.
    catalog : EarthquakeCatalog
        Earthquake events to overlay.
    field : str
        Background field.
    depth_index : int or None
        Depth index for the slice. None = middle.

    Returns
    -------
    tuple[Figure, Axes]
    """
    from opencoulomb.viz.colormaps import coulomb_cmap, symmetric_norm

    n_z, n_y, n_x = volume.volume_shape

    if depth_index is None:
        depth_index = n_z // 2

    if field == "cfs":
        data_3d = volume.cfs.reshape(volume.volume_shape)
    elif field == "shear":
        data_3d = volume.shear.reshape(volume.volume_shape)
    else:
        data_3d = volume.normal.reshape(volume.volume_shape)

    vmax = float(np.max(np.abs(data_3d)))
    if vmax == 0:
        vmax = 1.0

    cmap = coulomb_cmap()
    norm = symmetric_norm(vmax)

    slice_result = volume.slice_at_depth(depth_index)
    x_2d = slice_result.stress.x.reshape(n_y, n_x)
    y_2d = slice_result.stress.y.reshape(n_y, n_x)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.contourf(x_2d, y_2d, data_3d[depth_index], levels=21, cmap=cmap, norm=norm)

    # Plot catalog events
    slice_depth = volume.depths[depth_index]
    arrays = catalog.to_arrays()
    if len(arrays["latitude"]) > 0:
        # Scale size by magnitude, color by depth proximity
        sizes = (arrays["magnitude"] ** 2) * 5
        depth_diff = np.abs(arrays["depth_km"] - slice_depth)
        alphas = np.clip(1.0 - depth_diff / 20.0, 0.1, 1.0)

        for i in range(len(catalog)):
            ax.scatter(
                arrays["longitude"][i], arrays["latitude"][i],
                s=sizes[i], c="white", edgecolors="black",
                alpha=float(alphas[i]), zorder=5,
            )

    ax.set_title(f"{field.upper()} at depth = {slice_depth:.1f} km + catalog")
    ax.set_xlabel("East (km)")
    ax.set_ylabel("North (km)")
    ax.set_aspect("equal")

    return fig, ax
