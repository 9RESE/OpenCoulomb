"""Stress tensor computation from Okada displacement gradients.

Converts the 9 displacement gradient components returned by DC3D
into a 6-component stress tensor via Hooke's law for an isotropic
elastic medium.

Coordinate convention: x=East, y=North, z=Up (geographic).
Stress sign: compression positive (geophysics convention).
Units: bar.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

# Factor to convert Okada gradients (du(m)/dx(km)) to dimensionless strain.
# strain = du(m) / dx(m) = du(m) / (dx(km) * 1000) = okada_gradient * 0.001
_KM_TO_M = 0.001


def gradients_to_stress(
    uxx: NDArray[np.float64],
    uyx: NDArray[np.float64],
    uzx: NDArray[np.float64],
    uxy: NDArray[np.float64],
    uyy: NDArray[np.float64],
    uzy: NDArray[np.float64],
    uxz: NDArray[np.float64],
    uyz: NDArray[np.float64],
    uzz: NDArray[np.float64],
    young: float,
    poisson: float,
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    """Convert displacement gradients to stress tensor via Hooke's law.

    Parameters
    ----------
    uxx .. uzz : ndarray of shape (N,)
        Displacement gradient components du_i/dx_j from Okada DC3D.
        Units: m/km (Okada convention).
    young : float
        Young's modulus in bar.
    poisson : float
        Poisson's ratio (0 < nu < 0.5).

    Returns
    -------
    sxx, syy, szz, syz, sxz, sxy : ndarray of shape (N,)
        Stress tensor components in bar (Voigt notation).
    """
    # Lame parameters
    mu = young / (2.0 * (1.0 + poisson))  # shear modulus
    lam = young * poisson / ((1.0 + poisson) * (1.0 - 2.0 * poisson))

    # Strain tensor (symmetric) with km→m conversion
    exx = uxx * _KM_TO_M
    eyy = uyy * _KM_TO_M
    ezz = uzz * _KM_TO_M
    exy = 0.5 * (uxy + uyx) * _KM_TO_M
    exz = 0.5 * (uxz + uzx) * _KM_TO_M
    eyz = 0.5 * (uyz + uzy) * _KM_TO_M

    # Volumetric strain
    vol = exx + eyy + ezz

    # Hooke's law: sigma_ij = lambda * delta_ij * e_kk + 2*mu * e_ij
    sxx = lam * vol + 2.0 * mu * exx
    syy = lam * vol + 2.0 * mu * eyy
    szz = lam * vol + 2.0 * mu * ezz
    syz = 2.0 * mu * eyz
    sxz = 2.0 * mu * exz
    sxy = 2.0 * mu * exy

    return sxx, syy, szz, syz, sxz, sxy


def rotate_stress_tensor(
    sxx: NDArray[np.float64],
    syy: NDArray[np.float64],
    szz: NDArray[np.float64],
    syz: NDArray[np.float64],
    sxz: NDArray[np.float64],
    sxy: NDArray[np.float64],
    strike_rad: float,
    dip_rad: float,
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    """Rotate a stress tensor from fault-local to geographic coordinates.

    Uses the Bond transformation matrix for Voigt notation.

    Parameters
    ----------
    sxx .. sxy : ndarray of shape (N,)
        Stress components in fault-local coordinates (bar).
    strike_rad, dip_rad : float
        Fault orientation (radians).

    Returns
    -------
    sxx_g .. sxy_g : ndarray of shape (N,)
        Stress components in geographic coordinates (bar).
    """
    # Build rotation matrix (fault-local → geographic = R^T)
    ss = np.sin(strike_rad)
    cs = np.cos(strike_rad)
    sd = np.sin(dip_rad)
    cd = np.cos(dip_rad)

    # Direction cosines (rows of R: geographic → fault-local)
    # l_strike = [ss, cs, 0]
    # l_updip  = [-cs*cd, ss*cd, sd]
    # l_normal = [cs*sd, -ss*sd, cd]

    # We need R^T (fault-local → geographic)
    # R^T columns are the direction cosine vectors
    a11, a12, a13 = ss, -cs * cd, cs * sd
    a21, a22, a23 = cs, ss * cd, -ss * sd
    a31, a32, a33 = 0.0, sd, cd

    # Apply tensor rotation: sigma_geo = R^T @ sigma_local @ R
    # For Voigt notation, use the expanded formula directly.
    # sigma'_ij = sum_k sum_l a_ik * a_jl * sigma_kl
    # where a is the rotation matrix R^T

    # Build the 3x3 stress tensor for vectorized rotation
    # sigma_local = [[sxx, sxy, sxz], [sxy, syy, syz], [sxz, syz, szz]]
    # We compute each component of the rotated tensor

    sxx_g = (
        a11 * a11 * sxx + a12 * a12 * syy + a13 * a13 * szz
        + 2.0 * a11 * a12 * sxy + 2.0 * a11 * a13 * sxz + 2.0 * a12 * a13 * syz
    )
    syy_g = (
        a21 * a21 * sxx + a22 * a22 * syy + a23 * a23 * szz
        + 2.0 * a21 * a22 * sxy + 2.0 * a21 * a23 * sxz + 2.0 * a22 * a23 * syz
    )
    szz_g = (
        a31 * a31 * sxx + a32 * a32 * syy + a33 * a33 * szz
        + 2.0 * a31 * a32 * sxy + 2.0 * a31 * a33 * sxz + 2.0 * a32 * a33 * syz
    )
    syz_g = (
        a21 * a31 * sxx + a22 * a32 * syy + a23 * a33 * szz
        + (a21 * a32 + a22 * a31) * sxy
        + (a21 * a33 + a23 * a31) * sxz
        + (a22 * a33 + a23 * a32) * syz
    )
    sxz_g = (
        a11 * a31 * sxx + a12 * a32 * syy + a13 * a33 * szz
        + (a11 * a32 + a12 * a31) * sxy
        + (a11 * a33 + a13 * a31) * sxz
        + (a12 * a33 + a13 * a32) * syz
    )
    sxy_g = (
        a11 * a21 * sxx + a12 * a22 * syy + a13 * a23 * szz
        + (a11 * a22 + a12 * a21) * sxy
        + (a11 * a23 + a13 * a21) * sxz
        + (a12 * a23 + a13 * a22) * syz
    )

    return sxx_g, syy_g, szz_g, syz_g, sxz_g, sxy_g
