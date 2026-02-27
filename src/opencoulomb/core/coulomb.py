"""Coulomb failure stress (CFS) computation.

Resolves the total stress tensor onto receiver fault planes and
computes Coulomb failure stress change.

CFS = delta_tau + mu' * delta_sigma_n

Sign convention:
    positive shear  = promotes slip in rake direction
    positive normal = unclamping (tensile, promotes failure)
    positive CFS    = fault brought closer to failure
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def resolve_stress_on_fault(
    sxx: NDArray[np.float64],
    syy: NDArray[np.float64],
    szz: NDArray[np.float64],
    syz: NDArray[np.float64],
    sxz: NDArray[np.float64],
    sxy: NDArray[np.float64],
    strike_rad: float,
    dip_rad: float,
    rake_rad: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Resolve stress tensor onto a receiver fault plane.

    Parameters
    ----------
    sxx .. sxy : ndarray of shape (N,)
        Stress tensor in geographic coordinates (bar).
    strike_rad, dip_rad, rake_rad : float
        Receiver fault orientation (radians).

    Returns
    -------
    shear, normal : ndarray of shape (N,)
        Resolved shear stress (in rake direction) and normal stress (bar).
        Positive shear = promotes slip. Positive normal = unclamping.
    """
    ss = np.sin(strike_rad)
    cs = np.cos(strike_rad)
    sd = np.sin(dip_rad)
    cd = np.cos(dip_rad)
    sr = np.sin(rake_rad)
    cr = np.cos(rake_rad)

    # Fault normal vector (East, North, Up)
    nx = cs * sd
    ny = -ss * sd
    nz = cd

    # Normal stress: sigma_n = n . sigma . n
    normal = (
        sxx * nx * nx + syy * ny * ny + szz * nz * nz
        + 2.0 * sxy * nx * ny
        + 2.0 * sxz * nx * nz
        + 2.0 * syz * ny * nz
    )

    # Traction vector: t_i = sigma_ij * n_j
    tx = sxx * nx + sxy * ny + sxz * nz
    ty = sxy * nx + syy * ny + syz * nz
    tz = sxz * nx + syz * ny + szz * nz

    # Rake direction vector (in plane of fault)
    # d_rake = cos(rake) * l_strike + sin(rake) * l_updip
    dx = cr * ss + sr * (-cs * cd)
    dy = cr * cs + sr * (ss * cd)
    dz = sr * sd

    # Shear stress in rake direction: tau = t . d_rake
    shear = tx * dx + ty * dy + tz * dz

    return shear, normal


def compute_cfs(
    shear: NDArray[np.float64],
    normal: NDArray[np.float64],
    friction: float,
) -> NDArray[np.float64]:
    """Compute Coulomb failure stress change.

    Parameters
    ----------
    shear : ndarray of shape (N,)
        Resolved shear stress change (bar).
    normal : ndarray of shape (N,)
        Resolved normal stress change (bar). Positive = unclamping.
    friction : float
        Effective friction coefficient (mu').

    Returns
    -------
    cfs : ndarray of shape (N,)
        Coulomb failure stress change (bar).
        Positive = fault brought closer to failure.
    """
    return shear + friction * normal


def compute_cfs_on_receiver(
    sxx: NDArray[np.float64],
    syy: NDArray[np.float64],
    szz: NDArray[np.float64],
    syz: NDArray[np.float64],
    sxz: NDArray[np.float64],
    sxy: NDArray[np.float64],
    strike_rad: float,
    dip_rad: float,
    rake_rad: float,
    friction: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Compute CFS for a specific receiver fault orientation.

    Convenience function combining stress resolution and CFS computation.

    Parameters
    ----------
    sxx .. sxy : ndarray of shape (N,)
        Total stress tensor in geographic coordinates (bar).
    strike_rad, dip_rad, rake_rad : float
        Receiver fault orientation (radians).
    friction : float
        Effective friction coefficient.

    Returns
    -------
    cfs, shear, normal : ndarray of shape (N,)
        Coulomb failure stress, shear stress, and normal stress (bar).
    """
    shear, normal = resolve_stress_on_fault(
        sxx, syy, szz, syz, sxz, sxy,
        strike_rad, dip_rad, rake_rad,
    )
    cfs = compute_cfs(shear, normal, friction)
    return cfs, shear, normal
