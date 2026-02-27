"""Computation result data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


@dataclass(slots=True)
class StressResult:
    """Raw stress tensor and displacement at observation points.

    All arrays have shape (N,) where N is the number of observation points.

    Attributes
    ----------
    x, y, z : ndarray of shape (N,)
        Observation point coordinates (km). z negative = below surface.
    ux, uy, uz : ndarray of shape (N,)
        Displacement components (m). East, North, Up.
    sxx, syy, szz, syz, sxz, sxy : ndarray of shape (N,)
        Stress tensor components (bar).
    """

    x: NDArray[np.float64]
    y: NDArray[np.float64]
    z: NDArray[np.float64]
    ux: NDArray[np.float64]
    uy: NDArray[np.float64]
    uz: NDArray[np.float64]
    sxx: NDArray[np.float64]
    syy: NDArray[np.float64]
    szz: NDArray[np.float64]
    syz: NDArray[np.float64]
    sxz: NDArray[np.float64]
    sxy: NDArray[np.float64]

    @property
    def n_points(self) -> int:
        return len(self.x)


@dataclass(slots=True)
class CoulombResult:
    """Complete computation result including CFS.

    Attributes
    ----------
    stress : StressResult
        Raw stress tensor and displacement field.
    cfs : ndarray of shape (N,)
        Coulomb failure stress change (bar).
    shear : ndarray of shape (N,)
        Resolved shear stress change (bar).
    normal : ndarray of shape (N,)
        Resolved normal stress change (bar).
    receiver_strike : float
        Receiver fault strike used for CFS calculation (degrees).
    receiver_dip : float
        Receiver fault dip (degrees).
    receiver_rake : float
        Receiver fault rake (degrees).
    grid_shape : tuple[int, int]
        (n_y, n_x) shape for reshaping flat arrays to 2D grids.
    oops_strike : ndarray or None
        Optimal fault strike at each point (degrees).
    oops_dip : ndarray or None
        Optimal fault dip at each point (degrees).
    oops_rake : ndarray or None
        Optimal fault rake (degrees).
    """

    stress: StressResult
    cfs: NDArray[np.float64]
    shear: NDArray[np.float64]
    normal: NDArray[np.float64]
    receiver_strike: float
    receiver_dip: float
    receiver_rake: float
    grid_shape: tuple[int, int]
    oops_strike: NDArray[np.float64] | None = None
    oops_dip: NDArray[np.float64] | None = None
    oops_rake: NDArray[np.float64] | None = None

    def cfs_grid(self) -> NDArray[np.float64]:
        """Reshape CFS to 2D grid: shape (n_y, n_x)."""
        return self.cfs.reshape(self.grid_shape)

    def displacement_grid(
        self,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
        """Reshape displacements to 2D grids."""
        s = self.grid_shape
        return (
            self.stress.ux.reshape(s),
            self.stress.uy.reshape(s),
            self.stress.uz.reshape(s),
        )


@dataclass(slots=True)
class ElementResult:
    """CFS results on individual receiver fault elements.

    Attributes
    ----------
    elements : list
        Receiver fault elements (list[FaultElement]).
    cfs : ndarray of shape (M,)
        CFS at each receiver element center (bar).
    shear : ndarray of shape (M,)
        Shear stress at each receiver (bar).
    normal : ndarray of shape (M,)
        Normal stress at each receiver (bar).
    """

    elements: list  # list[FaultElement], avoid circular import at class level
    cfs: NDArray[np.float64]
    shear: NDArray[np.float64]
    normal: NDArray[np.float64]
