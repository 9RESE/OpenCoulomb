"""Cross-section data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from opencoulomb.exceptions import ValidationError

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class CrossSectionSpec:
    """Cross-section profile specification.

    Attributes
    ----------
    start_x, start_y : float
        Profile start point (km).
    finish_x, finish_y : float
        Profile end point (km).
    depth_min : float
        Minimum depth (km, >= 0). Typically 0 (surface).
    depth_max : float
        Maximum depth (km, > depth_min).
    z_inc : float
        Vertical spacing (km, > 0).
    """

    start_x: float
    start_y: float
    finish_x: float
    finish_y: float
    depth_min: float
    depth_max: float
    z_inc: float

    def __post_init__(self) -> None:
        if self.depth_min < 0:
            raise ValidationError(f"depth_min must be >= 0, got {self.depth_min}")
        if self.depth_max <= self.depth_min:
            raise ValidationError(
                f"depth_max ({self.depth_max}) must exceed depth_min ({self.depth_min})"
            )
        if self.z_inc <= 0:
            raise ValidationError(f"z_inc must be positive, got {self.z_inc}")


@dataclass(slots=True)
class CrossSectionResult:
    """Computation results on a cross-section grid.

    Attributes
    ----------
    distance : ndarray of shape (N_horiz,)
        Horizontal distance along the profile (km).
    depth : ndarray of shape (N_vert,)
        Depth values (km, positive downward).
    cfs : ndarray of shape (N_vert, N_horiz)
        CFS on the cross-section grid (bar).
    shear : ndarray of shape (N_vert, N_horiz)
        Shear stress (bar).
    normal : ndarray of shape (N_vert, N_horiz)
        Normal stress (bar).
    ux, uy, uz : ndarray of shape (N_vert, N_horiz)
        Displacement components (m).
    sxx, syy, szz, syz, sxz, sxy : ndarray of shape (N_vert, N_horiz)
        Full stress tensor on the section (bar).
    spec : CrossSectionSpec
        The specification that produced this result.
    """

    distance: NDArray[np.float64]
    depth: NDArray[np.float64]
    cfs: NDArray[np.float64]
    shear: NDArray[np.float64]
    normal: NDArray[np.float64]
    ux: NDArray[np.float64]
    uy: NDArray[np.float64]
    uz: NDArray[np.float64]
    sxx: NDArray[np.float64]
    syy: NDArray[np.float64]
    szz: NDArray[np.float64]
    syz: NDArray[np.float64]
    sxz: NDArray[np.float64]
    sxy: NDArray[np.float64]
    spec: CrossSectionSpec
