"""Optimally Oriented Planes (OOPs) computation.

Finds fault orientations that maximize Coulomb failure stress (CFS)
given a total stress field (earthquake-induced + regional background).

Algorithm:
1. Build regional stress tensor from principal stress specification
2. Add regional stress to earthquake-induced stress (superposition)
3. Eigendecompose total stress tensor at each grid point
4. Apply Mohr-Coulomb criterion to find optimal failure plane angle
5. Convert optimal plane normal to geographic (strike, dip)
6. Compute CFS on the optimal plane

References:
    King, G.C.P., Stein, R.S., and Lin, J. (1994). Static stress changes
    and the triggering of earthquakes. Bulletin of the Seismological
    Society of America, 84(3), 935-953.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from opencoulomb.types.stress import RegionalStress


def compute_regional_stress_tensor(
    regional: RegionalStress,
    depth: NDArray[np.float64],
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    """Build the 6-component regional stress tensor at given depths.

    Each principal stress axis is specified by direction (azimuth), dip,
    base intensity, and depth gradient. The stress magnitude at depth *d*
    is ``intensity + gradient * d``.

    Parameters
    ----------
    regional : RegionalStress
        Three principal stress axes with orientations and depth gradients.
    depth : ndarray of shape (N,)
        Depth values (km, positive downward).

    Returns
    -------
    sxx, syy, szz, syz, sxz, sxy : ndarray of shape (N,)
        Regional stress tensor in geographic coordinates (bar).
        x=East, y=North, z=Up.
    """
    n = len(depth)
    sxx = np.zeros(n)
    syy = np.zeros(n)
    szz = np.zeros(n)
    syz = np.zeros(n)
    sxz = np.zeros(n)
    sxy = np.zeros(n)

    for ps in (regional.s1, regional.s2, regional.s3):
        # Principal stress magnitude at depth
        sigma = ps.intensity + ps.gradient * depth

        # Unit vector for this principal axis (geographic: E, N, Up)
        az_rad = math.radians(ps.direction)
        dip_rad = math.radians(ps.dip)
        cos_dip = math.cos(dip_rad)
        sin_dip = math.sin(dip_rad)

        # Azimuth is clockwise from North: East = sin(az), North = cos(az)
        vx = math.sin(az_rad) * cos_dip  # East component
        vy = math.cos(az_rad) * cos_dip  # North component
        vz = -sin_dip                     # Up component (dip positive = downward)

        # Outer product contribution: sigma * v_i * v_j
        sxx += sigma * vx * vx
        syy += sigma * vy * vy
        szz += sigma * vz * vz
        syz += sigma * vy * vz
        sxz += sigma * vx * vz
        sxy += sigma * vx * vy

    return sxx, syy, szz, syz, sxz, sxy


def _build_stress_matrices(
    sxx: NDArray[np.float64],
    syy: NDArray[np.float64],
    szz: NDArray[np.float64],
    syz: NDArray[np.float64],
    sxz: NDArray[np.float64],
    sxy: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Build (N, 3, 3) symmetric stress tensor matrices from Voigt components.

    Parameters
    ----------
    sxx .. sxy : ndarray of shape (N,)
        Voigt stress components.

    Returns
    -------
    matrices : ndarray of shape (N, 3, 3)
        Symmetric stress matrices.
    """
    n = len(sxx)
    S = np.empty((n, 3, 3))
    S[:, 0, 0] = sxx
    S[:, 1, 1] = syy
    S[:, 2, 2] = szz
    S[:, 0, 1] = sxy
    S[:, 1, 0] = sxy
    S[:, 0, 2] = sxz
    S[:, 2, 0] = sxz
    S[:, 1, 2] = syz
    S[:, 2, 1] = syz
    return S


def mohr_coulomb_angle(friction: float) -> float:
    """Compute the Mohr-Coulomb optimal failure plane angle.

    The optimal angle is between the fault normal and sigma1
    (most compressive principal stress).

    Parameters
    ----------
    friction : float
        Effective friction coefficient (mu').

    Returns
    -------
    beta : float
        Optimal angle in radians. The fault plane normal makes this
        angle with sigma1 in the sigma1-sigma3 plane.
    """
    if friction <= 0.0:
        return math.pi / 4.0
    return 0.5 * math.atan(1.0 / friction)


def find_optimal_planes(
    sxx: NDArray[np.float64],
    syy: NDArray[np.float64],
    szz: NDArray[np.float64],
    syz: NDArray[np.float64],
    sxz: NDArray[np.float64],
    sxy: NDArray[np.float64],
    friction: float,
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    """Find optimally oriented fault planes that maximize CFS.

    At each point, eigendecomposes the total stress tensor, applies the
    Mohr-Coulomb criterion to find two conjugate failure planes, and
    returns the one with higher CFS.

    Parameters
    ----------
    sxx .. sxy : ndarray of shape (N,)
        Total stress tensor in geographic coordinates (bar).
    friction : float
        Effective friction coefficient.

    Returns
    -------
    strike_opt : ndarray of shape (N,)
        Optimal fault strike (degrees, 0-360).
    dip_opt : ndarray of shape (N,)
        Optimal fault dip (degrees, 0-90).
    rake_opt : ndarray of shape (N,)
        Rake on the optimal plane (degrees).
    cfs_opt : ndarray of shape (N,)
        CFS on the optimal plane (bar).
    """
    n = len(sxx)

    # Build symmetric 3x3 matrices for batch eigendecomposition
    S = _build_stress_matrices(sxx, syy, szz, syz, sxz, sxy)

    # Eigendecompose: eigh returns eigenvalues in ascending order
    _, eigenvectors = np.linalg.eigh(S)

    # eigh returns ascending: eigenvalues[:, 0] <= [:, 1] <= [:, 2]
    # Convention: s1 (most compressive) >= s2 >= s3 (least compressive)
    # In compression-positive convention, s1 is the largest eigenvalue.
    # eigh ascending: col 0 = smallest, col 2 = largest
    s3_vec = eigenvectors[:, :, 0]  # sigma3 direction (least compressive)
    s1_vec = eigenvectors[:, :, 2]  # sigma1 direction (most compressive)

    # Mohr-Coulomb optimal angle
    beta = mohr_coulomb_angle(friction)

    # Two conjugate plane normals in the sigma1-sigma3 plane
    # Normal = cos(beta) * s1_hat + sin(beta) * s3_hat  (and the conjugate)
    cb = math.cos(beta)
    sb = math.sin(beta)

    normal_a = cb * s1_vec + sb * s3_vec  # (N, 3)
    normal_b = cb * s1_vec - sb * s3_vec  # (N, 3)

    # Normalize (should be unit already, but ensure)
    normal_a /= np.linalg.norm(normal_a, axis=1, keepdims=True)
    normal_b /= np.linalg.norm(normal_b, axis=1, keepdims=True)

    # Compute CFS on each conjugate plane
    cfs_a, _, _ = _compute_cfs_on_normals(S, normal_a, friction)
    cfs_b, _, _ = _compute_cfs_on_normals(S, normal_b, friction)

    # Select the plane with higher |CFS|
    use_a = np.abs(cfs_a) >= np.abs(cfs_b)
    cfs_opt = np.where(use_a, cfs_a, cfs_b)
    normals_opt = np.where(use_a[:, np.newaxis], normal_a, normal_b)

    # Convert normals to strike/dip
    strike_opt = np.empty(n)
    dip_opt = np.empty(n)
    rake_opt = np.empty(n)

    # Per-point loop: the conditional logic in _normal_to_strike_dip_rake
    # (atan2, nz sign flip, dip~0 branch) resists simple vectorization.
    for i in range(n):
        s, d, r = _normal_to_strike_dip_rake(
            normals_opt[i],
            S[i],
        )
        strike_opt[i] = s
        dip_opt[i] = d
        rake_opt[i] = r

    return strike_opt, dip_opt, rake_opt, cfs_opt


def _compute_cfs_on_normals(
    S: NDArray[np.float64],
    normals: NDArray[np.float64],
    friction: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Compute CFS on planes with given normals.

    Parameters
    ----------
    S : ndarray of shape (N, 3, 3)
        Stress tensor matrices.
    normals : ndarray of shape (N, 3)
        Unit normal vectors to the fault planes.
    friction : float
        Effective friction coefficient.

    Returns
    -------
    cfs, shear, normal_stress : ndarray of shape (N,)
    """
    # Traction vector: t_i = S_ij * n_j
    # Using einsum for batch matrix-vector multiply
    traction = np.einsum("nij,nj->ni", S, normals)

    # Normal stress: sigma_n = t . n
    normal_stress = np.einsum("ni,ni->n", traction, normals)

    # Shear traction: t_shear = t - sigma_n * n
    t_shear = traction - normal_stress[:, np.newaxis] * normals

    # Shear stress magnitude
    shear = np.linalg.norm(t_shear, axis=1)

    # CFS = |tau| + mu * sigma_n  (positive normal = unclamping = tensile)
    cfs = shear + friction * normal_stress

    return cfs, shear, normal_stress


def _normal_to_strike_dip_rake(
    normal: NDArray[np.float64],
    stress_matrix: NDArray[np.float64],
) -> tuple[float, float, float]:
    """Convert a fault plane normal to strike, dip, and rake.

    Parameters
    ----------
    normal : ndarray of shape (3,)
        Unit normal to the fault plane in geographic (E, N, Up).
    stress_matrix : ndarray of shape (3, 3)
        Stress tensor at this point.

    Returns
    -------
    strike, dip, rake : float
        In degrees. Strike 0-360, dip 0-90, rake -180 to 180.
    """
    nx, ny, nz = float(normal[0]), float(normal[1]), float(normal[2])

    # Ensure normal points upward (nz >= 0) for consistent dip convention
    if nz < 0:
        nx, ny, nz = -nx, -ny, -nz

    # Dip: angle from horizontal
    horiz_mag = math.sqrt(nx * nx + ny * ny)
    dip = math.degrees(math.atan2(horiz_mag, nz))

    if dip < 1e-6:
        # Nearly horizontal plane (vertical fault normal)
        # Strike is ambiguous; use 0
        strike = 0.0
        rake = 0.0
        return strike, dip, rake

    # Strike: The normal to a fault plane with dip direction has
    # strike = atan2(nx, -ny) (following right-hand rule: dip is to the right
    # when looking along strike)
    # Normal horizontal component points in the dip direction
    # Strike = dip_direction - 90
    dip_direction = math.degrees(math.atan2(nx, ny))
    strike = (dip_direction + 90.0) % 360.0

    # Compute rake from the shear traction direction on the plane
    traction = stress_matrix @ normal
    normal_stress = float(np.dot(traction, normal))
    t_shear = traction - normal_stress * normal

    t_shear_mag = float(np.linalg.norm(t_shear))
    if t_shear_mag < 1e-15:
        rake = 0.0
        return strike, dip, rake

    # Slip direction = shear traction direction (unit vector in the fault plane)
    slip_dir = t_shear / t_shear_mag

    # Compute rake: angle of slip direction relative to strike direction
    # Strike direction vector
    strike_rad = math.radians(strike)
    ss = math.sin(strike_rad)
    cs = math.cos(strike_rad)
    l_strike = np.array([ss, cs, 0.0])

    # Updip direction
    dip_rad = math.radians(dip)
    l_updip = np.array([-cs * math.cos(dip_rad),
                         ss * math.cos(dip_rad),
                         math.sin(dip_rad)])

    rake = math.degrees(math.atan2(
        float(np.dot(slip_dir, l_updip)),
        float(np.dot(slip_dir, l_strike)),
    ))

    return strike, dip, rake
