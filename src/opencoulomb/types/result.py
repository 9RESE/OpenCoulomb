"""Computation result data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

    from opencoulomb.types.fault import FaultElement


@dataclass(slots=True)
class StrainResult:
    """Strain tensor at observation points.

    All arrays have shape (N,) where N is the number of observation points.

    Attributes
    ----------
    exx, eyy, ezz, eyz, exz, exy : ndarray of shape (N,)
        Strain tensor components (dimensionless, Voigt notation).
    volumetric : ndarray of shape (N,)
        Volumetric strain / dilatation (exx + eyy + ezz).
    """

    exx: NDArray[np.float64]
    eyy: NDArray[np.float64]
    ezz: NDArray[np.float64]
    eyz: NDArray[np.float64]
    exz: NDArray[np.float64]
    exy: NDArray[np.float64]
    volumetric: NDArray[np.float64]


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
    strain: StrainResult | None = None

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

    elements: list[FaultElement]
    cfs: NDArray[np.float64]
    shear: NDArray[np.float64]
    normal: NDArray[np.float64]


@dataclass(slots=True)
class VolumeResult:
    """3D volume computation result.

    All flat arrays have shape (N,) where N = n_z * n_y * n_x.

    Attributes
    ----------
    stress : StressResult
        Raw stress tensor and displacement (flat arrays).
    cfs, shear, normal : ndarray of shape (N,)
        CFS components (bar).
    receiver_strike, receiver_dip, receiver_rake : float
        Receiver orientation (degrees).
    volume_shape : tuple[int, int, int]
        (n_z, n_y, n_x) for reshaping flat arrays to 3D.
    depths : ndarray of shape (n_z,)
        Depth values for each layer (km).
    strain : StrainResult or None
        Strain tensor if computed.
    """

    stress: StressResult
    cfs: NDArray[np.float64]
    shear: NDArray[np.float64]
    normal: NDArray[np.float64]
    receiver_strike: float
    receiver_dip: float
    receiver_rake: float
    volume_shape: tuple[int, int, int]
    depths: NDArray[np.float64]
    strain: StrainResult | None = None

    def cfs_volume(self) -> NDArray[np.float64]:
        """Reshape CFS to 3D volume: shape (n_z, n_y, n_x)."""
        return self.cfs.reshape(self.volume_shape)

    def slice_at_depth(self, depth_index: int) -> CoulombResult:
        """Extract a 2D horizontal slice at a given depth index.

        Returns a standard CoulombResult compatible with existing writers/viz.
        """
        _n_z, n_y, n_x = self.volume_shape
        n_2d = n_y * n_x
        start = depth_index * n_2d
        end = start + n_2d
        s = slice(start, end)

        stress_2d = StressResult(
            x=self.stress.x[s], y=self.stress.y[s], z=self.stress.z[s],
            ux=self.stress.ux[s], uy=self.stress.uy[s], uz=self.stress.uz[s],
            sxx=self.stress.sxx[s], syy=self.stress.syy[s], szz=self.stress.szz[s],
            syz=self.stress.syz[s], sxz=self.stress.sxz[s], sxy=self.stress.sxy[s],
        )

        strain_2d: StrainResult | None = None
        if self.strain is not None:
            strain_2d = StrainResult(
                exx=self.strain.exx[s], eyy=self.strain.eyy[s], ezz=self.strain.ezz[s],
                eyz=self.strain.eyz[s], exz=self.strain.exz[s], exy=self.strain.exy[s],
                volumetric=self.strain.volumetric[s],
            )

        return CoulombResult(
            stress=stress_2d,
            cfs=self.cfs[s],
            shear=self.shear[s],
            normal=self.normal[s],
            receiver_strike=self.receiver_strike,
            receiver_dip=self.receiver_dip,
            receiver_rake=self.receiver_rake,
            grid_shape=(n_y, n_x),
            strain=strain_2d,
        )
