"""Coulomb-style colormaps and normalization."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib
import matplotlib.colors as mcolors

if TYPE_CHECKING:
    import numpy as np
    from matplotlib.colors import Colormap, Normalize
    from numpy.typing import NDArray


def coulomb_cmap() -> Colormap:
    """Coulomb-style diverging colormap (blue-white-red).

    Blue = stress decrease (destabilizing removed).
    Red = stress increase (brought closer to failure).
    """
    return matplotlib.colormaps.get_cmap("RdBu_r")


def displacement_cmap() -> Colormap:
    """Sequential colormap for displacement magnitude."""
    return matplotlib.colormaps.get_cmap("viridis")


def stress_cmap() -> Colormap:
    """Diverging colormap for individual stress components.

    Currently identical to coulomb_cmap(); may diverge in future versions.
    """
    return matplotlib.colormaps.get_cmap("RdBu_r")


def symmetric_norm(
    data: NDArray[np.float64],
    vmax: float | None = None,
) -> Normalize:
    """Create a symmetric normalization centered on zero.

    Parameters
    ----------
    data : ndarray
        Data array to determine limits from.
    vmax : float or None
        Maximum absolute value. If None, uses max(|data|).

    Returns
    -------
    Normalize
        Matplotlib normalization with symmetric limits [-vmax, +vmax].
    """
    import numpy as np

    if vmax is None:
        vmax = float(np.nanmax(np.abs(data)))
    if vmax == 0:
        vmax = 1.0
    return mcolors.Normalize(vmin=-vmax, vmax=vmax)
