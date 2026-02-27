"""Okada (1992) DC3D and DC3D0 dislocation solutions.

Implements the closed-form analytical solutions for displacement and
displacement gradients at observation points in a homogeneous, isotropic
elastic half-space due to rectangular (DC3D) or point (DC3D0) dislocation
sources.

All functions are vectorized: observation-point parameters (x, y, z) may be
NumPy arrays of shape (N,) to compute N observation points in a single call.
All outputs then have shape (N,).

The implementation faithfully follows the Fortran subroutines DC3D and DC3D0
published in:

    Okada, Y. (1992). Internal deformation due to shear and tensile faults
    in a half-space. Bulletin of the Seismological Society of America,
    82(2), 1018-1040.

Conventions
-----------
- Coordinate system: x = strike, y = updip horizontal, z = up (z <= 0).
- Depth is positive downward.
- Dip angle in degrees.
- Displacements in meters; displacement gradients du(m)/dx(km).
- alpha = (lambda + mu) / (lambda + 2*mu).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_EPS = 1.0e-6   # Singularity detection threshold (km).
_PI2 = 2.0 * np.pi


# ---------------------------------------------------------------------------
# Precomputed constants
# ---------------------------------------------------------------------------

class _OkadaConstants(NamedTuple):
    """Precomputed medium and trigonometric constants (DCCON0)."""
    alp1: float  # (1 - alpha) / 2
    alp2: float  # alpha / 2
    alp3: float  # (1 - alpha) / alpha
    alp4: float  # 1 - alpha
    alp5: float  # alpha
    sd: float    # sin(dip)
    cd: float    # cos(dip)
    sdsd: float  # sin^2(dip)
    cdcd: float  # cos^2(dip)
    sdcd: float  # sin(dip)*cos(dip)
    s2d: float   # sin(2*dip)
    c2d: float   # cos(2*dip)


def _dccon0(alpha: float, dip_deg: float) -> _OkadaConstants:
    """Compute medium and trigonometric constants (Fortran DCCON0)."""
    alp1 = (1.0 - alpha) / 2.0
    alp2 = alpha / 2.0
    alp3 = (1.0 - alpha) / alpha if abs(alpha) > 1.0e-20 else 0.0
    alp4 = 1.0 - alpha
    alp5 = alpha

    dip_rad = np.radians(dip_deg)
    sd = np.sin(dip_rad)
    cd = np.cos(dip_rad)
    if abs(cd) < _EPS:
        cd = 0.0
        sd = 1.0 if sd > 0.0 else -1.0

    sdsd = sd * sd
    cdcd = cd * cd
    sdcd = sd * cd
    s2d = 2.0 * sdcd
    c2d = cdcd - sdsd

    return _OkadaConstants(
        alp1=alp1, alp2=alp2, alp3=alp3, alp4=alp4, alp5=alp5,
        sd=sd, cd=cd, sdsd=sdsd, cdcd=cdcd, sdcd=sdcd, s2d=s2d, c2d=c2d,
    )


# ---------------------------------------------------------------------------
# DCCON2 -- secondary geometric parameters for DC3D (vectorized)
# ---------------------------------------------------------------------------

def _dccon2(
    xi: NDArray[np.float64],
    et: NDArray[np.float64],
    q: NDArray[np.float64],
    sd: float,
    cd: float,
    kxi: NDArray[np.float64],
    ket: NDArray[np.float64],
) -> dict[str, NDArray[np.float64]]:
    """Compute secondary geometric parameters (Fortran DCCON2), vectorized.

    Parameters
    ----------
    xi, et, q : NDArray[np.float64] (N,)
        Corner-adjusted coordinates.
    sd, cd : float
        sin(dip), cos(dip).
    kxi, ket : NDArray[np.float64] bool (N,)
        Singularity flags for r+xi and r+et.

    Returns
    -------
    dict with keys: xi2, et2, q2, r, r2, r3, r5, y, d, tt,
                    alx, ale, x11, y11, x32, y32,
                    ey, ez, fy, fz, gy, gz, hy, hz
    """
    xi2 = xi * xi
    et2 = et * et
    q2 = q * q
    r2 = xi2 + et2 + q2
    r = np.sqrt(r2)
    r3 = r * r2
    r5 = r3 * r2

    # Avoid division by zero.
    r_s = np.maximum(r, _EPS)
    r3_s = np.maximum(r3, _EPS**3)

    y_v = et * cd + q * sd
    d_v = et * sd - q * cd

    # atan2 term (theta).
    tt = np.where(np.abs(q) < _EPS,
                  np.zeros_like(xi),
                  np.arctan2(xi * et, q * r_s))

    # --- X-related terms (r + xi) ---
    rxi = r + xi
    cond_rxi = kxi  # True when on negative extension

    rxi_safe = np.where(cond_rxi, 1.0, rxi)  # avoid log(0)
    alx = np.where(cond_rxi,
                   -np.log(np.maximum(r_s - xi, _EPS)),
                   np.log(np.maximum(np.abs(rxi), _EPS)))
    x11 = np.where(cond_rxi, 0.0, 1.0 / (r_s * np.maximum(np.abs(rxi), _EPS)))
    # X32 = (R+Rxi)*X11^2/R = (2R+xi)/(R^3*(R+xi)^2)
    x32 = np.where(cond_rxi, 0.0,
                   (r_s + rxi_safe) * x11 * x11 / r_s)

    # --- Y-related terms (r + et) ---
    ret = r + et
    cond_ret = ket

    ret_safe = np.where(cond_ret, 1.0, ret)
    ale = np.where(cond_ret,
                   -np.log(np.maximum(r_s - et, _EPS)),
                   np.log(np.maximum(np.abs(ret), _EPS)))
    y11 = np.where(cond_ret, 0.0, 1.0 / (r_s * np.maximum(np.abs(ret), _EPS)))
    y32 = np.where(cond_ret, 0.0,
                   (r_s + ret_safe) * y11 * y11 / r_s)

    # --- Higher-order terms ---
    ey = np.where(cond_ret, 0.0, sd / r_s - y_v * q / r3_s)
    ez = np.where(cond_ret, 0.0, cd / r_s + d_v * q / r3_s)
    fy = np.where(cond_ret, 0.0, d_v / (r3_s * np.maximum(np.abs(ret), _EPS)) + xi2 * y32 * sd)
    fz = np.where(cond_ret, 0.0, y_v / (r3_s * np.maximum(np.abs(ret), _EPS)) + xi2 * y32 * cd)
    gy = np.where(cond_ret, 0.0, 2.0 * x11 * sd - y_v * q * x32)
    gz = np.where(cond_ret, 0.0, 2.0 * x11 * cd + d_v * q * x32)
    hy = np.where(cond_ret, 0.0, d_v * q * x32 + xi * q * y32 * sd)
    hz = np.where(cond_ret, 0.0, y_v * q * x32 + xi * q * y32 * cd)

    return {
        'xi2': xi2, 'et2': et2, 'q2': q2,
        'r': r, 'r2': r2, 'r3': r3, 'r5': r5,
        'y': y_v, 'd': d_v, 'tt': tt,
        'alx': alx, 'ale': ale,
        'x11': x11, 'y11': y11, 'x32': x32, 'y32': y32,
        'ey': ey, 'ez': ez, 'fy': fy, 'fz': fz,
        'gy': gy, 'gz': gz, 'hy': hy, 'hz': hz,
    }


# ---------------------------------------------------------------------------
# UA -- Part A (infinite medium) for DC3D
# ---------------------------------------------------------------------------

def _ua(
    xi: NDArray[np.float64], et: NDArray[np.float64], q: NDArray[np.float64],
    disl1: float, disl2: float, disl3: float,
    c: _OkadaConstants, s: dict[str, NDArray[np.float64]],
) -> NDArray[np.float64]:
    """Part A contribution (Fortran UA), vectorized.

    Returns shape (12, N) array.
    """
    N = xi.shape[0]
    u = np.zeros((12, N), dtype=np.float64)

    r = s['r']
    r3 = np.maximum(s['r3'], _EPS**3)
    xi2 = s['xi2']
    q2 = s['q2']
    tt = s['tt']
    alx = s['alx']
    ale = s['ale']
    x11 = s['x11']
    y11 = s['y11']
    y32 = s['y32']
    ey = s['ey']
    ez = s['ez']
    fy = s['fy']
    fz = s['fz']
    gy = s['gy']
    gz = s['gz']
    hy = s['hy']
    hz = s['hz']
    d_v = s['d']
    y_v = s['y']

    xy = xi * y11
    qx = q * x11
    qy = q * y11

    # ---- Strike-slip ----
    if disl1 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = tt / 2.0 + c.alp2 * xi * qy
        du[1] = c.alp2 * q / r
        du[2] = c.alp1 * ale - c.alp2 * q * qy
        du[3] = -c.alp1 * qy - c.alp2 * xi2 * q * y32
        du[4] = -c.alp2 * xi * q / r3
        du[5] = c.alp1 * xy + c.alp2 * xi * q2 * y32
        du[6] = c.alp1 * xy * c.sd + c.alp2 * xi * fy + d_v / 2.0 * x11
        du[7] = c.alp2 * ey
        du[8] = c.alp1 * (c.cd / r + qy * c.sd) - c.alp2 * q * fy
        du[9] = c.alp1 * xy * c.cd + c.alp2 * xi * fz + y_v / 2.0 * x11
        du[10] = c.alp2 * ez
        du[11] = -c.alp1 * (c.sd / r - qy * c.cd) - c.alp2 * q * fz
        u += disl1 / _PI2 * du

    # ---- Dip-slip ----
    if disl2 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = c.alp2 * q / r
        du[1] = tt / 2.0 + c.alp2 * et * qx
        du[2] = c.alp1 * alx - c.alp2 * q * qx
        du[3] = -c.alp2 * xi * q / r3
        du[4] = -qy / 2.0 - c.alp2 * et * q / r3
        du[5] = c.alp1 / r + c.alp2 * q2 / r3
        du[6] = c.alp2 * ey
        du[7] = c.alp1 * d_v * x11 + xy / 2.0 * c.sd + c.alp2 * et * gy
        du[8] = c.alp1 * y_v * x11 - c.alp2 * q * gy
        du[9] = c.alp2 * ez
        du[10] = c.alp1 * y_v * x11 + xy / 2.0 * c.cd + c.alp2 * et * gz
        du[11] = -c.alp1 * d_v * x11 - c.alp2 * q * gz
        u += disl2 / _PI2 * du

    # ---- Tensile ----
    if disl3 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = -c.alp1 * ale - c.alp2 * q * qy
        du[1] = -c.alp1 * alx - c.alp2 * q * qx
        du[2] = tt / 2.0 - c.alp2 * (et * qx + xi * qy)
        du[3] = -c.alp1 * xy + c.alp2 * xi * q2 * y32
        du[4] = -c.alp1 / r + c.alp2 * q2 / r3
        du[5] = -c.alp1 * qy - c.alp2 * q * q2 * y32
        du[6] = -c.alp1 * (c.cd / r + qy * c.sd) - c.alp2 * q * fy
        du[7] = -c.alp1 * y_v * x11 - c.alp2 * q * gy
        du[8] = c.alp1 * (d_v * x11 + xy * c.sd) + c.alp2 * q * hy
        du[9] = c.alp1 * (c.sd / r - qy * c.cd) - c.alp2 * q * fz
        du[10] = c.alp1 * d_v * x11 - c.alp2 * q * gz
        du[11] = c.alp1 * (y_v * x11 + xy * c.cd) + c.alp2 * q * hz
        u += disl3 / _PI2 * du

    return u


# ---------------------------------------------------------------------------
# UB -- Part B (image source) for DC3D
# ---------------------------------------------------------------------------

def _ub(
    xi: NDArray[np.float64], et: NDArray[np.float64], q: NDArray[np.float64],
    disl1: float, disl2: float, disl3: float,
    c: _OkadaConstants, s: dict[str, NDArray[np.float64]],
) -> NDArray[np.float64]:
    """Part B contribution (Fortran UB), vectorized.

    Returns shape (12, N) array.
    """
    N = xi.shape[0]
    u = np.zeros((12, N), dtype=np.float64)

    r = s['r']
    r3 = np.maximum(s['r3'], _EPS**3)
    xi2 = s['xi2']
    q2 = s['q2']
    ale = s['ale']
    x11 = s['x11']
    y11 = s['y11']
    y32 = s['y32']
    ey = s['ey']
    ez = s['ez']
    fy = s['fy']
    fz = s['fz']
    gy = s['gy']
    gz = s['gz']
    hy = s['hy']
    hz = s['hz']
    d_v = s['d']
    y_v = s['y']
    tt = s['tt']

    xy = xi * y11
    qx = q * x11
    qy = q * y11

    rd = r + d_v
    rd_safe = np.where(np.abs(rd) < _EPS, _EPS, rd)
    d11 = 1.0 / (r * rd_safe)

    aj2 = xi * y_v / rd_safe * d11
    aj5 = -(d_v + y_v * y_v / rd_safe) * d11

    if abs(c.cd) > _EPS:
        # Non-vertical dip.
        x_val = np.sqrt(xi2 + q2)
        # ai4 requires special handling when xi=0.
        xi_zero = np.abs(xi) < _EPS
        numer = et * (x_val + q * c.cd) + x_val * (r + x_val) * c.sd
        denom = xi * (r + x_val) * c.cd
        denom_safe = np.where(xi_zero, 1.0, denom)
        ai4_inner = np.where(xi_zero, 0.0,
                             xi / rd_safe * c.sdcd + 2.0 * np.arctan2(numer, denom_safe))
        ai4 = 1.0 / c.cdcd * ai4_inner
        ai3 = (y_v * c.cd / rd_safe - ale + c.sd * np.log(np.maximum(np.abs(rd_safe), _EPS))) / c.cdcd
        ak1 = xi * (d11 - y11 * c.sd) / c.cd
        ak3 = (q * y11 - y_v * d11) / c.cd
        aj3 = (ak1 - aj2 * c.sd) / c.cd
        aj6 = (ak3 - aj5 * c.sd) / c.cd
    else:
        # Vertical dip (cd == 0).
        rd2 = rd_safe * rd_safe
        ai3 = (et / rd_safe + y_v * q / rd2 - ale) / 2.0
        ai4 = xi * y_v / rd2 / 2.0
        ak1 = xi * q / rd_safe * d11
        ak3 = c.sd / rd_safe * (xi2 * d11 - 1.0)
        aj3 = -xi / rd2 * (q2 * d11 - 0.5)
        aj6 = -y_v / rd2 * (xi2 * d11 - 0.5)

    ai1 = -xi / rd_safe * c.cd - ai4 * c.sd
    ai2 = np.log(np.maximum(np.abs(rd_safe), _EPS)) + ai3 * c.sd
    ak2 = 1.0 / r + ak3 * c.sd
    ak4 = xy * c.cd - ak1 * c.sd
    aj1 = aj5 * c.cd - aj6 * c.sd
    aj4 = -xy - aj2 * c.cd + aj3 * c.sd

    # ---- Strike-slip ----
    if disl1 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = -xi * qy - tt - c.alp3 * ai1 * c.sd
        du[1] = -q / r + c.alp3 * y_v / rd_safe * c.sd
        du[2] = q * qy - c.alp3 * ai2 * c.sd
        du[3] = xi2 * q * y32 - c.alp3 * aj1 * c.sd
        du[4] = xi * q / r3 - c.alp3 * aj2 * c.sd
        du[5] = -xi * q2 * y32 - c.alp3 * aj3 * c.sd
        du[6] = -xi * fy - d_v * x11 + c.alp3 * (xy + aj4) * c.sd
        du[7] = -ey + c.alp3 * (1.0 / r + aj5) * c.sd
        du[8] = q * fy - c.alp3 * (qy - aj6) * c.sd
        du[9] = -xi * fz - y_v * x11 + c.alp3 * ak1 * c.sd
        du[10] = -ez + c.alp3 * y_v * d11 * c.sd
        du[11] = q * fz + c.alp3 * ak2 * c.sd
        u += disl1 / _PI2 * du

    # ---- Dip-slip ----
    if disl2 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = -q / r + c.alp3 * ai3 * c.sdcd
        du[1] = -et * qx - tt - c.alp3 * xi / rd_safe * c.sdcd
        du[2] = q * qx + c.alp3 * ai4 * c.sdcd
        du[3] = xi * q / r3 + c.alp3 * aj4 * c.sdcd
        du[4] = et * q / r3 + qy + c.alp3 * aj5 * c.sdcd
        du[5] = -q2 / r3 + c.alp3 * aj6 * c.sdcd
        du[6] = -ey + c.alp3 * aj1 * c.sdcd
        du[7] = -et * gy - xy * c.sd + c.alp3 * aj2 * c.sdcd
        du[8] = q * gy + c.alp3 * aj3 * c.sdcd
        du[9] = -ez - c.alp3 * ak3 * c.sdcd
        du[10] = -et * gz - xy * c.cd - c.alp3 * xi * d11 * c.sdcd
        du[11] = q * gz - c.alp3 * ak4 * c.sdcd
        u += disl2 / _PI2 * du

    # ---- Tensile ----
    if disl3 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = q * qy - c.alp3 * ai3 * c.sdsd
        du[1] = q * qx + c.alp3 * xi / rd_safe * c.sdsd
        du[2] = et * qx + xi * qy - tt - c.alp3 * ai4 * c.sdsd
        du[3] = -xi * q2 * y32 - c.alp3 * aj4 * c.sdsd
        du[4] = -q2 / r3 - c.alp3 * aj5 * c.sdsd
        du[5] = q * q2 * y32 - c.alp3 * aj6 * c.sdsd
        du[6] = q * fy - c.alp3 * aj1 * c.sdsd
        du[7] = q * gy - c.alp3 * aj2 * c.sdsd
        du[8] = -q * hy - c.alp3 * aj3 * c.sdsd
        du[9] = q * fz + c.alp3 * ak3 * c.sdsd
        du[10] = q * gz + c.alp3 * xi * d11 * c.sdsd
        du[11] = -q * hz + c.alp3 * ak4 * c.sdsd
        u += disl3 / _PI2 * du

    return u


# ---------------------------------------------------------------------------
# UC -- Part C (depth-dependent correction) for DC3D
# ---------------------------------------------------------------------------

def _uc(
    xi: NDArray[np.float64], et: NDArray[np.float64], q: NDArray[np.float64], z: NDArray[np.float64],
    disl1: float, disl2: float, disl3: float,
    c: _OkadaConstants, s: dict[str, NDArray[np.float64]],
) -> NDArray[np.float64]:
    """Part C contribution (Fortran UC), vectorized.

    Returns shape (12, N) array.
    """
    N = xi.shape[0]
    u = np.zeros((12, N), dtype=np.float64)

    r = s['r']
    r2 = s['r2']
    r3 = np.maximum(s['r3'], _EPS**3)
    r5 = np.maximum(s['r5'], _EPS**5)
    xi2 = s['xi2']
    et2 = s['et2']
    q2 = s['q2']
    x11 = s['x11']
    y11 = s['y11']
    x32 = s['x32']
    y32 = s['y32']
    d_v = s['d']
    y_v = s['y']

    r2_s = np.maximum(r2, _EPS**2)

    c_val = d_v + z  # C = d + z in Fortran

    h = q * c.cd - z

    # X53, Y53 computed from X11, Y11, R.
    x53 = np.where(
        np.abs(x11) < _EPS * 1e-6, 0.0,
        (8.0 * r2 + 9.0 * r * xi + 3.0 * xi2) * x11**3 / r2_s
    )
    y53 = np.where(
        np.abs(y11) < _EPS * 1e-6, 0.0,
        (8.0 * r2 + 9.0 * r * et + 3.0 * et2) * y11**3 / r2_s
    )

    z32 = c.sd / r3 - h * y32
    z53 = 3.0 * c.sd / r5 - h * y53
    y0 = y11 - xi2 * y32
    z0 = z32 - xi2 * z53
    ppy = c.cd / r3 + q * y32 * c.sd
    ppz = c.sd / r3 - q * y32 * c.cd
    qq = z * y32 + z32 + z0
    qqy = 3.0 * c_val * d_v / r5 - qq * c.sd
    qqz = 3.0 * c_val * y_v / r5 - qq * c.cd + q * y32
    xy = xi * y11
    qy = q * y11
    qr = 3.0 * q / r5
    cdr = (c_val + d_v) / r3
    yy0 = y_v / r3 - y0 * c.cd

    # ---- Strike-slip ----
    if disl1 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = c.alp4 * xy * c.cd - c.alp5 * xi * q * z32
        du[1] = c.alp4 * (c.cd / r + 2.0 * qy * c.sd) - c.alp5 * c_val * q / r3
        du[2] = c.alp4 * qy * c.cd - c.alp5 * (c_val * et / r3 - z * y11 + xi2 * z32)
        du[3] = c.alp4 * y0 * c.cd - c.alp5 * q * z0
        du[4] = -c.alp4 * xi * (c.cd / r3 + 2.0 * q * y32 * c.sd) + c.alp5 * c_val * xi * qr
        du[5] = -c.alp4 * xi * q * y32 * c.cd + c.alp5 * xi * (3.0 * c_val * et / r5 - qq)
        du[6] = -c.alp4 * xi * ppy * c.cd - c.alp5 * xi * qqy
        du[7] = (c.alp4 * 2.0 * (d_v / r3 - y0 * c.sd) * c.sd - y_v / r3 * c.cd
                 - c.alp5 * (cdr * c.sd - et / r3 - c_val * y_v * qr))
        du[8] = (-c.alp4 * q / r3 + yy0 * c.sd
                 + c.alp5 * (cdr * c.cd + c_val * d_v * qr - (y0 * c.cd + q * z0) * c.sd))
        du[9] = c.alp4 * xi * ppz * c.cd - c.alp5 * xi * qqz
        du[10] = (c.alp4 * 2.0 * (y_v / r3 - y0 * c.cd) * c.sd + d_v / r3 * c.cd
                  - c.alp5 * (cdr * c.cd + c_val * d_v * qr))
        du[11] = (yy0 * c.cd
                  - c.alp5 * (cdr * c.sd - c_val * y_v * qr - y0 * c.sdsd + q * z0 * c.cd))
        u += disl1 / _PI2 * du

    # ---- Dip-slip ----
    if disl2 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = c.alp4 * c.cd / r - qy * c.sd - c.alp5 * c_val * q / r3
        du[1] = c.alp4 * y_v * x11 - c.alp5 * c_val * et * q * x32
        du[2] = -d_v * x11 - xy * c.sd - c.alp5 * c_val * (x11 - q2 * x32)
        du[3] = -c.alp4 * xi / r3 * c.cd + c.alp5 * c_val * xi * qr + xi * q * y32 * c.sd
        du[4] = -c.alp4 * y_v / r3 + c.alp5 * c_val * et * qr
        du[5] = d_v / r3 - y0 * c.sd + c.alp5 * c_val / r3 * (1.0 - 3.0 * q2 / r2_s)
        du[6] = -c.alp4 * et / r3 + y0 * c.sdsd - c.alp5 * (cdr * c.sd - c_val * y_v * qr)
        du[7] = (c.alp4 * (x11 - y_v * y_v * x32)
                 - c.alp5 * c_val * ((d_v + 2.0 * q * c.cd) * x32 - y_v * et * q * x53))
        du[8] = (xi * ppy * c.sd + y_v * d_v * x32
                 + c.alp5 * c_val * ((y_v + 2.0 * q * c.sd) * x32 - y_v * q2 * x53))
        du[9] = -q / r3 + y0 * c.sdcd - c.alp5 * (cdr * c.cd + c_val * d_v * qr)
        du[10] = (c.alp4 * y_v * d_v * x32
                  - c.alp5 * c_val * ((y_v - 2.0 * q * c.sd) * x32 + d_v * et * q * x53))
        du[11] = (-xi * ppz * c.sd + x11 - d_v * d_v * x32
                  - c.alp5 * c_val * ((d_v - 2.0 * q * c.cd) * x32 - d_v * q2 * x53))
        u += disl2 / _PI2 * du

    # ---- Tensile ----
    if disl3 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = -c.alp4 * (c.sd / r + qy * c.cd) - c.alp5 * (z * y11 - q2 * z32)
        du[1] = c.alp4 * 2.0 * xy * c.sd + d_v * x11 - c.alp5 * c_val * (x11 - q2 * x32)
        du[2] = c.alp4 * (y_v * x11 + xy * c.cd) + c.alp5 * q * (c_val * et * x32 + xi * z32)
        du[3] = (c.alp4 * xi / r3 * c.sd + xi * q * y32 * c.cd
                 + c.alp5 * xi * (3.0 * c_val * et / r5 - 2.0 * z32 - z0))
        du[4] = c.alp4 * 2.0 * y0 * c.sd - d_v / r3 + c.alp5 * c_val / r3 * (1.0 - 3.0 * q2 / r2_s)
        du[5] = -c.alp4 * yy0 - c.alp5 * (c_val * et * qr - q * z0)
        du[6] = (c.alp4 * (q / r3 + y0 * c.sdcd)
                 + c.alp5 * (z / r3 * c.cd + c_val * d_v * qr - q * z0 * c.sd))
        du[7] = (-c.alp4 * 2.0 * xi * ppy * c.sd - y_v * d_v * x32
                 + c.alp5 * c_val * ((y_v + 2.0 * q * c.sd) * x32 - y_v * q2 * x53))
        du[8] = (-c.alp4 * (xi * ppy * c.cd - x11 + y_v * y_v * x32)
                 + c.alp5 * (c_val * ((d_v + 2.0 * q * c.cd) * x32 - y_v * et * q * x53) + xi * qqy))
        du[9] = (-et / r3 + y0 * c.cdcd
                 - c.alp5 * (z / r3 * c.sd - c_val * y_v * qr - y0 * c.sdsd + q * z0 * c.cd))
        du[10] = (c.alp4 * 2.0 * xi * ppz * c.sd - x11 + d_v * d_v * x32
                  - c.alp5 * c_val * ((d_v - 2.0 * q * c.cd) * x32 - d_v * q2 * x53))
        du[11] = (c.alp4 * (xi * ppz * c.cd + y_v * d_v * x32)
                  + c.alp5 * (c_val * ((y_v - 2.0 * q * c.sd) * x32 + d_v * et * q * x53) + xi * qqz))
        u += disl3 / _PI2 * du

    return u


# ---------------------------------------------------------------------------
# DC3D -- Main finite rectangular fault function
# ---------------------------------------------------------------------------

def dc3d(
    alpha: float,
    x: NDArray[np.float64] | float,
    y: NDArray[np.float64] | float,
    z: NDArray[np.float64] | float,
    depth: float,
    dip: float,
    al1: float,
    al2: float,
    aw1: float,
    aw2: float,
    disl1: float,
    disl2: float,
    disl3: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64],
           NDArray[np.float64], NDArray[np.float64], NDArray[np.float64],
           NDArray[np.float64], NDArray[np.float64], NDArray[np.float64],
           NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Compute displacement and gradients for a finite rectangular fault.

    Implements Okada (1992) DC3D: displacement field u_i and displacement
    gradient tensor du_i/dx_j at observation point(s) (x, y, z) due to a
    rectangular dislocation source in an elastic half-space.

    Parameters
    ----------
    alpha : float
        Medium constant = (lambda + mu) / (lambda + 2*mu) = 1/(2*(1-nu)).
    x, y, z : float or ndarray of shape (N,)
        Observation point coordinates in the fault-centered coordinate
        system. z must be <= 0 (negative below free surface).
    depth : float
        Depth of the fault reference point (positive, in km).
    dip : float
        Dip angle in degrees (0-90).
    al1, al2 : float
        Fault bounds along strike: from al1 to al2 (km). Typically al1 < 0.
    aw1, aw2 : float
        Fault bounds along dip: from aw1 to aw2 (km). Typically aw1 < 0.
    disl1 : float
        Strike-slip dislocation (m). Left-lateral positive.
    disl2 : float
        Dip-slip dislocation (m). Reverse positive.
    disl3 : float
        Tensile dislocation (m). Opening positive.

    Returns
    -------
    tuple of 12 arrays of shape (N,)
        (ux, uy, uz, uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz)
        Displacements (m) and displacement gradients (m/km).
    """
    # Ensure arrays.
    x = np.atleast_1d(np.asarray(x, dtype=np.float64))
    y = np.atleast_1d(np.asarray(y, dtype=np.float64))
    z = np.atleast_1d(np.asarray(z, dtype=np.float64))
    N = x.shape[0]

    # Precompute medium/angle constants.
    co = _dccon0(alpha, dip)

    # Initialize output accumulator.
    u = np.zeros((12, N), dtype=np.float64)

    # Observation point z for image source.
    zz = z.copy()

    # xi values for the two along-strike edges.
    xi_arr = np.array([x - al1, x - al2])  # shape (2, N)
    # Snap near-zero xi.
    xi_arr = np.where(np.abs(xi_arr) < _EPS, 0.0, xi_arr)

    # ===================================================================
    # REAL-SOURCE CONTRIBUTION (depth + z)
    # ===================================================================
    d = depth + z  # d = depth + z (both could be arrays)
    p = y * co.cd + d * co.sd
    q_val = y * co.sd - d * co.cd
    # Snap q near zero.
    q_val = np.where(np.abs(q_val) < _EPS, 0.0, q_val)

    et_arr = np.array([p - aw1, p - aw2])  # shape (2, N)
    et_arr = np.where(np.abs(et_arr) < _EPS, 0.0, et_arr)

    # Compute KXI, KET flags (negative extension singularity).
    # KXI(K) = 1 if xi(1) < 0 and R(2,K) + xi(2) < EPS
    # KET(J) = 1 if et(1) < 0 and R(1,2) + et(2) < EPS  (etc.)
    # In Fortran: R12, R21, R22 are distances at specific corners.
    r12 = np.sqrt(xi_arr[0]**2 + et_arr[1]**2 + q_val**2)
    r21 = np.sqrt(xi_arr[1]**2 + et_arr[0]**2 + q_val**2)
    r22 = np.sqrt(xi_arr[1]**2 + et_arr[1]**2 + q_val**2)

    kxi = np.zeros((2, N), dtype=bool)
    ket = np.zeros((2, N), dtype=bool)
    kxi[0] = (xi_arr[0] < 0.0) & (r21 + xi_arr[1] < _EPS)
    kxi[1] = (xi_arr[0] < 0.0) & (r22 + xi_arr[1] < _EPS)
    ket[0] = (et_arr[0] < 0.0) & (r12 + et_arr[1] < _EPS)
    ket[1] = (et_arr[0] < 0.0) & (r22 + et_arr[1] < _EPS)

    # Loop over 4 corners (Chinnery's notation).
    # K=1,2 (et index), J=1,2 (xi index).
    # Sign: + when J+K != 3, - when J+K == 3.
    for k in range(2):
        for j in range(2):
            xi_jk = xi_arr[j]
            et_jk = et_arr[k]
            # DCCON2 with kxi[k] and ket[j]
            sp = _dccon2(xi_jk, et_jk, q_val, co.sd, co.cd, kxi[k], ket[j])

            dua = _ua(xi_jk, et_jk, q_val, disl1, disl2, disl3, co, sp)

            # Coordinate rotation: Fortran DO 220 loop.
            du = np.zeros((12, N), dtype=np.float64)
            for i in range(0, 12, 3):
                du[i] = -dua[i]
                du[i + 1] = -dua[i + 1] * co.cd + dua[i + 2] * co.sd
                du[i + 2] = -dua[i + 1] * co.sd - dua[i + 2] * co.cd
                if i == 9:  # last triplet (i=10,11,12 in Fortran)
                    du[i] = -du[i]
                    du[i + 1] = -du[i + 1]
                    du[i + 2] = -du[i + 2]

            sign = 1.0 if (j + k) != 1 else -1.0  # j+k: 0->+, 1->-, 2->+
            # In Fortran: J+K != 3 means + (J,K are 1-indexed so J+K=2,3,4).
            # In 0-indexed: j+k != 1 means +.
            u += sign * du

    # ===================================================================
    # IMAGE-SOURCE CONTRIBUTION (depth - z)
    # ===================================================================
    d = depth - z
    p = y * co.cd + d * co.sd
    q_val = y * co.sd - d * co.cd
    q_val = np.where(np.abs(q_val) < _EPS, 0.0, q_val)

    et_arr = np.array([p - aw1, p - aw2])
    et_arr = np.where(np.abs(et_arr) < _EPS, 0.0, et_arr)

    # Recompute KXI, KET for image source.
    r12 = np.sqrt(xi_arr[0]**2 + et_arr[1]**2 + q_val**2)
    r21 = np.sqrt(xi_arr[1]**2 + et_arr[0]**2 + q_val**2)
    r22 = np.sqrt(xi_arr[1]**2 + et_arr[1]**2 + q_val**2)

    kxi = np.zeros((2, N), dtype=bool)
    ket = np.zeros((2, N), dtype=bool)
    kxi[0] = (xi_arr[0] < 0.0) & (r21 + xi_arr[1] < _EPS)
    kxi[1] = (xi_arr[0] < 0.0) & (r22 + xi_arr[1] < _EPS)
    ket[0] = (et_arr[0] < 0.0) & (r12 + et_arr[1] < _EPS)
    ket[1] = (et_arr[0] < 0.0) & (r22 + et_arr[1] < _EPS)

    for k in range(2):
        for j in range(2):
            xi_jk = xi_arr[j]
            et_jk = et_arr[k]
            sp = _dccon2(xi_jk, et_jk, q_val, co.sd, co.cd, kxi[k], ket[j])

            dua = _ua(xi_jk, et_jk, q_val, disl1, disl2, disl3, co, sp)
            dub = _ub(xi_jk, et_jk, q_val, disl1, disl2, disl3, co, sp)
            duc = _uc(xi_jk, et_jk, q_val, zz, disl1, disl2, disl3, co, sp)

            du = np.zeros((12, N), dtype=np.float64)
            for i in range(0, 12, 3):
                du[i] = dua[i] + dub[i] + zz * duc[i]
                du[i + 1] = ((dua[i + 1] + dub[i + 1] + zz * duc[i + 1]) * co.cd
                             - (dua[i + 2] + dub[i + 2] + zz * duc[i + 2]) * co.sd)
                du[i + 2] = ((dua[i + 1] + dub[i + 1] - zz * duc[i + 1]) * co.sd
                             + (dua[i + 2] + dub[i + 2] - zz * duc[i + 2]) * co.cd)
                if i == 9:
                    du[9] = du[9] + duc[0]
                    du[10] = du[10] + duc[1] * co.cd - duc[2] * co.sd
                    du[11] = du[11] - duc[1] * co.sd - duc[2] * co.cd

            sign = 1.0 if (j + k) != 1 else -1.0
            u += sign * du

    return (
        u[0], u[1], u[2],
        u[3], u[4], u[5],
        u[6], u[7], u[8],
        u[9], u[10], u[11],
    )


# ============================================================================
# DC3D0 -- Point source
# ============================================================================

def _dccon1(
    x: NDArray[np.float64], y: NDArray[np.float64], d: NDArray[np.float64],
    sd: float, cd: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Compute point-source geometry constants (Fortran DCCON1), vectorized.

    Returns (r, p, q, s, t).
    """
    p = y * cd + d * sd
    q = y * sd - d * cd
    s = p * sd + q * cd
    t = p * cd - q * sd
    r = np.sqrt(x * x + y * y + d * d)
    return r, p, q, s, t


def _ua0(
    x: NDArray[np.float64], y: NDArray[np.float64], d: NDArray[np.float64],
    pot1: float, pot2: float, pot3: float, pot4: float,
    sd: float, cd: float,
    co: _OkadaConstants,
) -> NDArray[np.float64]:
    """Part A for point source (Fortran UA0), vectorized.

    Returns shape (12, N).
    """
    N = x.shape[0]
    u = np.zeros((12, N), dtype=np.float64)

    r, p, q, s, t = _dccon1(x, y, d, sd, cd)
    r2 = r * r
    r3 = np.maximum(r * r2, _EPS**3)
    r5 = np.maximum(r3 * r2, _EPS**5)
    r2_s = np.maximum(r2, _EPS**2)

    s2d = 2.0 * sd * cd
    c2d = cd * cd - sd * sd

    xy = x * y
    x2 = x * x
    y2 = y * y
    d2 = d * d

    qr = 3.0 * q / r5
    qrx = 5.0 * qr * x / r2_s

    a3 = 1.0 - 3.0 * x2 / r2_s
    a5 = 1.0 - 5.0 * x2 / r2_s
    b3 = 1.0 - 3.0 * y2 / r2_s
    c3 = 1.0 - 3.0 * d2 / r2_s

    uy = sd - 5.0 * y * q / r2_s
    uz = cd + 5.0 * d * q / r2_s
    vy = s - 5.0 * y * p * q / r2_s
    vz = t + 5.0 * d * p * q / r2_s
    wy = uy + sd
    wz = uz + cd

    # ---- Strike-slip ----
    if pot1 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = co.alp1 * q / r3 + co.alp2 * x2 * qr
        du[1] = co.alp1 * x / r3 * sd + co.alp2 * xy * qr
        du[2] = -co.alp1 * x / r3 * cd + co.alp2 * x * d * qr
        du[3] = x * qr * (-co.alp1 + co.alp2 * (1.0 + a5))
        du[4] = co.alp1 * a3 / r3 * sd + co.alp2 * y * qr * a5
        du[5] = -co.alp1 * a3 / r3 * cd + co.alp2 * d * qr * a5
        du[6] = co.alp1 * (sd / r3 - y * qr) + co.alp2 * 3.0 * x2 / r5 * uy
        du[7] = 3.0 * x / r5 * (-co.alp1 * y * sd + co.alp2 * (y * uy + q))
        du[8] = 3.0 * x / r5 * (co.alp1 * y * cd + co.alp2 * d * uy)
        du[9] = co.alp1 * (cd / r3 + d * qr) + co.alp2 * 3.0 * x2 / r5 * uz
        du[10] = 3.0 * x / r5 * (co.alp1 * d * sd + co.alp2 * y * uz)
        du[11] = 3.0 * x / r5 * (-co.alp1 * d * cd + co.alp2 * (d * uz - q))
        u += pot1 / _PI2 * du

    # ---- Dip-slip ----
    if pot2 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = co.alp2 * x * p * qr
        du[1] = co.alp1 * s / r3 + co.alp2 * y * p * qr
        du[2] = -co.alp1 * t / r3 + co.alp2 * d * p * qr
        du[3] = co.alp2 * p * qr * a5
        du[4] = -co.alp1 * 3.0 * x * s / r5 - co.alp2 * y * p * qrx
        du[5] = co.alp1 * 3.0 * x * t / r5 - co.alp2 * d * p * qrx
        du[6] = co.alp2 * 3.0 * x / r5 * vy
        du[7] = co.alp1 * (s2d / r3 - 3.0 * y * s / r5) + co.alp2 * (3.0 * y / r5 * vy + p * qr)
        du[8] = -co.alp1 * (c2d / r3 - 3.0 * y * t / r5) + co.alp2 * 3.0 * d / r5 * vy
        du[9] = co.alp2 * 3.0 * x / r5 * vz
        du[10] = co.alp1 * (c2d / r3 + 3.0 * d * s / r5) + co.alp2 * 3.0 * y / r5 * vz
        du[11] = co.alp1 * (s2d / r3 - 3.0 * d * t / r5) + co.alp2 * (3.0 * d / r5 * vz - p * qr)
        u += pot2 / _PI2 * du

    # ---- Tensile ----
    if pot3 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = co.alp1 * x / r3 - co.alp2 * x * q * qr
        du[1] = co.alp1 * t / r3 - co.alp2 * y * q * qr
        du[2] = co.alp1 * s / r3 - co.alp2 * d * q * qr
        du[3] = co.alp1 * a3 / r3 - co.alp2 * q * qr * a5
        du[4] = -co.alp1 * 3.0 * x * t / r5 + co.alp2 * y * q * qrx
        du[5] = -co.alp1 * 3.0 * x * s / r5 + co.alp2 * d * q * qrx
        du[6] = -co.alp1 * 3.0 * xy / r5 - co.alp2 * x * qr * wy
        du[7] = co.alp1 * (c2d / r3 - 3.0 * y * t / r5) - co.alp2 * (y * wy + q) * qr
        du[8] = co.alp1 * (s2d / r3 - 3.0 * y * s / r5) - co.alp2 * d * qr * wy
        du[9] = co.alp1 * 3.0 * x * d / r5 - co.alp2 * x * qr * wz
        du[10] = -co.alp1 * (s2d / r3 - 3.0 * d * t / r5) - co.alp2 * y * qr * wz
        du[11] = co.alp1 * (c2d / r3 + 3.0 * d * s / r5) - co.alp2 * (d * wz - q) * qr
        u += pot3 / _PI2 * du

    # ---- Inflation ----
    if pot4 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = -co.alp1 * x / r3
        du[1] = -co.alp1 * y / r3
        du[2] = -co.alp1 * d / r3
        du[3] = -co.alp1 * a3 / r3
        du[4] = co.alp1 * 3.0 * xy / r5
        du[5] = co.alp1 * 3.0 * x * d / r5
        du[6] = du[4].copy()
        du[7] = -co.alp1 * b3 / r3
        du[8] = co.alp1 * 3.0 * y * d / r5
        du[9] = -du[5].copy()
        du[10] = -du[8].copy()
        du[11] = co.alp1 * c3 / r3
        u += pot4 / _PI2 * du

    return u


def _ub0(
    x: NDArray[np.float64], y: NDArray[np.float64], d: NDArray[np.float64], z: NDArray[np.float64],
    pot1: float, pot2: float, pot3: float, pot4: float,
    sd: float, cd: float,
    co: _OkadaConstants,
) -> NDArray[np.float64]:
    """Part B for point source (Fortran UB0), vectorized.

    Returns shape (12, N).
    """
    N = x.shape[0]
    u = np.zeros((12, N), dtype=np.float64)

    r, p, q, s, t = _dccon1(x, y, d, sd, cd)
    r2 = r * r
    r3 = np.maximum(r * r2, _EPS**3)
    r5 = np.maximum(r3 * r2, _EPS**5)
    r2_s = np.maximum(r2, _EPS**2)

    xy = x * y
    x2 = x * x
    y2 = y * y
    d2 = d * d

    qr = 3.0 * q / r5
    qrx = 5.0 * qr * x / r2_s

    a3 = 1.0 - 3.0 * x2 / r2_s
    a5 = 1.0 - 5.0 * x2 / r2_s
    b3 = 1.0 - 3.0 * y2 / r2_s

    uy = sd - 5.0 * y * q / r2_s
    uz = cd + 5.0 * d * q / r2_s
    vy = s - 5.0 * y * p * q / r2_s
    vz = t + 5.0 * d * p * q / r2_s
    wy = uy + sd
    wz = uz + cd

    c_val = d + z
    rd = r + d
    rd_safe = np.where(np.abs(rd) < _EPS, _EPS, rd)

    d12 = 1.0 / (r * rd_safe * rd_safe)
    d32 = d12 * (2.0 * r + d) / r2_s
    d33 = d12 * (3.0 * r + d) / (r2_s * rd_safe)
    d53 = d12 * (8.0 * r2 + 9.0 * r * d + 3.0 * d2) / (r2_s * r2_s * rd_safe)
    d54 = d12 * (5.0 * r2 + 4.0 * r * d + d2) / r3 * d12

    fi1 = y * (d12 - x2 * d33)
    fi2 = x * (d12 - y2 * d33)
    fi3 = x / r3 - fi2
    fi4 = -xy * d32
    fi5 = 1.0 / (r * rd_safe) - x2 * d32

    fj1 = -3.0 * xy * (d33 - x2 * d54)
    fj2 = 1.0 / r3 - 3.0 * d12 + 3.0 * x2 * y2 * d54
    fj3 = a3 / r3 - fj2
    fj4 = -3.0 * xy / r5 - fj1

    fk1 = -y * (d32 - x2 * d53)
    fk2 = -x * (d32 - y2 * d53)
    fk3 = -3.0 * x * d / r5 - fk2

    # ---- Strike-slip ----
    if pot1 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = -x2 * qr - co.alp3 * fi1 * sd
        du[1] = -xy * qr - co.alp3 * fi2 * sd
        du[2] = -c_val * x * qr - co.alp3 * fi4 * sd
        du[3] = -x * qr * (1.0 + a5) - co.alp3 * fj1 * sd
        du[4] = -y * qr * a5 - co.alp3 * fj2 * sd
        du[5] = -c_val * qr * a5 - co.alp3 * fk1 * sd
        du[6] = -3.0 * x2 / r5 * uy - co.alp3 * fj2 * sd
        du[7] = -3.0 * xy / r5 * uy - x * qr - co.alp3 * fj4 * sd
        du[8] = -3.0 * c_val * x / r5 * uy - co.alp3 * fk2 * sd
        du[9] = -3.0 * x2 / r5 * uz + co.alp3 * fk1 * sd
        du[10] = -3.0 * xy / r5 * uz + co.alp3 * fk2 * sd
        du[11] = 3.0 * x / r5 * (-c_val * uz + co.alp3 * y * sd)
        u += pot1 / _PI2 * du

    # ---- Dip-slip ----
    if pot2 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = -x * p * qr + co.alp3 * fi3 * co.sdcd
        du[1] = -y * p * qr + co.alp3 * fi1 * co.sdcd
        du[2] = -c_val * p * qr + co.alp3 * fi5 * co.sdcd
        du[3] = -p * qr * a5 + co.alp3 * fj3 * co.sdcd
        du[4] = y * p * qrx + co.alp3 * fj1 * co.sdcd
        du[5] = c_val * p * qrx + co.alp3 * fk3 * co.sdcd
        du[6] = -3.0 * x / r5 * vy + co.alp3 * fj1 * co.sdcd
        du[7] = -3.0 * y / r5 * vy - p * qr + co.alp3 * fj2 * co.sdcd
        du[8] = -3.0 * c_val / r5 * vy + co.alp3 * fk1 * co.sdcd
        du[9] = -3.0 * x / r5 * vz - co.alp3 * fk3 * co.sdcd
        du[10] = -3.0 * y / r5 * vz - co.alp3 * fk1 * co.sdcd
        du[11] = -3.0 * c_val / r5 * vz + co.alp3 * a3 / r3 * co.sdcd
        u += pot2 / _PI2 * du

    # ---- Tensile ----
    if pot3 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = x * q * qr - co.alp3 * fi3 * co.sdsd
        du[1] = y * q * qr - co.alp3 * fi1 * co.sdsd
        du[2] = c_val * q * qr - co.alp3 * fi5 * co.sdsd
        du[3] = q * qr * a5 - co.alp3 * fj3 * co.sdsd
        du[4] = -y * q * qrx - co.alp3 * fj1 * co.sdsd
        du[5] = -c_val * q * qrx - co.alp3 * fk3 * co.sdsd
        du[6] = x * qr * wy - co.alp3 * fj1 * co.sdsd
        du[7] = qr * (y * wy + q) - co.alp3 * fj2 * co.sdsd
        du[8] = c_val * qr * wy - co.alp3 * fk1 * co.sdsd
        du[9] = x * qr * wz + co.alp3 * fk3 * co.sdsd
        du[10] = y * qr * wz + co.alp3 * fk1 * co.sdsd
        du[11] = c_val * qr * wz - co.alp3 * a3 / r3 * co.sdsd
        u += pot3 / _PI2 * du

    # ---- Inflation ----
    if pot4 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = co.alp3 * x / r3
        du[1] = co.alp3 * y / r3
        du[2] = co.alp3 * d / r3
        du[3] = co.alp3 * a3 / r3
        du[4] = -co.alp3 * 3.0 * xy / r5
        du[5] = -co.alp3 * 3.0 * x * d / r5
        du[6] = du[4].copy()
        du[7] = co.alp3 * b3 / r3
        du[8] = -co.alp3 * 3.0 * y * d / r5
        du[9] = -du[5].copy()
        du[10] = -du[8].copy()
        du[11] = -co.alp3 * (1.0 - 3.0 * d2 / r2_s) / r3
        u += pot4 / _PI2 * du

    return u


def _uc0(
    x: NDArray[np.float64], y: NDArray[np.float64], d: NDArray[np.float64], z: NDArray[np.float64],
    pot1: float, pot2: float, pot3: float, pot4: float,
    sd: float, cd: float,
    co: _OkadaConstants,
) -> NDArray[np.float64]:
    """Part C for point source (Fortran UC0), vectorized.

    Returns shape (12, N).
    """
    N = x.shape[0]
    u = np.zeros((12, N), dtype=np.float64)

    r, p, q, s, t = _dccon1(x, y, d, sd, cd)
    r2 = r * r
    r3 = np.maximum(r * r2, _EPS**3)
    r5 = np.maximum(r3 * r2, _EPS**5)
    r7 = np.maximum(r5 * r2, _EPS**7)
    r2_s = np.maximum(r2, _EPS**2)

    s2d = 2.0 * sd * cd
    c2d = cd * cd - sd * sd

    xy = x * y
    x2 = x * x
    y2 = y * y
    d2 = d * d

    c_val = d + z
    q2 = q * q

    qr = 3.0 * q / r5
    qr5 = 5.0 * q / r2_s
    qr7 = 7.0 * q / r2_s
    dr5 = 5.0 * d / r2_s

    a3 = 1.0 - 3.0 * x2 / r2_s
    a5 = 1.0 - 5.0 * x2 / r2_s
    a7 = 1.0 - 7.0 * x2 / r2_s
    b5 = 1.0 - 5.0 * y2 / r2_s
    b7 = 1.0 - 7.0 * y2 / r2_s
    c3 = 1.0 - 3.0 * d2 / r2_s
    c5 = 1.0 - 5.0 * d2 / r2_s
    c7 = 1.0 - 7.0 * d2 / r2_s
    d7 = 2.0 - 7.0 * q2 / r2_s

    qrx = 5.0 * qr * x / r2_s

    # ---- Strike-slip ----
    if pot1 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = -co.alp4 * a3 / r3 * cd + co.alp5 * c_val * qr * a5
        du[1] = 3.0 * x / r5 * (co.alp4 * y * cd + co.alp5 * c_val * (sd - y * qr5))
        du[2] = 3.0 * x / r5 * (-co.alp4 * y * sd + co.alp5 * c_val * (cd + d * qr5))
        du[3] = co.alp4 * 3.0 * x / r5 * (2.0 + a5) * cd - co.alp5 * c_val * qrx * (2.0 + a7)
        du[4] = 3.0 / r5 * (co.alp4 * y * a5 * cd + co.alp5 * c_val * (a5 * sd - y * qr5 * a7))
        du[5] = 3.0 / r5 * (-co.alp4 * y * a5 * sd + co.alp5 * c_val * (a5 * cd + d * qr5 * a7))
        du[6] = du[4].copy()
        du[7] = 3.0 * x / r5 * (co.alp4 * b5 * cd - co.alp5 * 5.0 * c_val / r2_s * (2.0 * y * sd + q * b7))
        du[8] = 3.0 * x / r5 * (-co.alp4 * b5 * sd + co.alp5 * 5.0 * c_val / r2_s * (d * b7 * sd - y * c7 * cd))
        du[9] = 3.0 / r5 * (-co.alp4 * d * a5 * cd + co.alp5 * c_val * (a5 * cd + d * qr5 * a7))
        du[10] = 15.0 * x / r7 * (co.alp4 * y * d * cd + co.alp5 * c_val * (d * b7 * sd - y * c7 * cd))
        du[11] = 15.0 * x / r7 * (-co.alp4 * y * d * sd + co.alp5 * c_val * (2.0 * d * cd - q * c7))
        u += pot1 / _PI2 * du

    # ---- Dip-slip ----
    if pot2 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = co.alp4 * 3.0 * x * t / r5 - co.alp5 * c_val * p * qrx
        du[1] = -co.alp4 / r3 * (c2d - 3.0 * y * t / r2_s) + co.alp5 * 3.0 * c_val / r5 * (s - y * p * qr5)
        du[2] = -co.alp4 * a3 / r3 * co.sdcd + co.alp5 * 3.0 * c_val / r5 * (t + d * p * qr5)
        du[3] = co.alp4 * 3.0 * t / r5 * a5 - co.alp5 * 5.0 * c_val * p * qr / r2_s * a7
        du[4] = 3.0 * x / r5 * (co.alp4 * (c2d - 5.0 * y * t / r2_s) - co.alp5 * 5.0 * c_val / r2_s * (s - y * p * qr7))
        du[5] = 3.0 * x / r5 * (co.alp4 * (2.0 + a5) * co.sdcd - co.alp5 * 5.0 * c_val / r2_s * (t + d * p * qr7))
        du[6] = du[4].copy()
        du[7] = (3.0 / r5 * (co.alp4 * (2.0 * y * c2d + t * b5)
                 + co.alp5 * c_val * (s2d - 10.0 * y * s / r2_s - p * qr5 * b7)))
        du[8] = 3.0 / r5 * (co.alp4 * y * a5 * co.sdcd - co.alp5 * c_val * ((3.0 + a5) * c2d + y * p * dr5 * qr7))
        du[9] = 3.0 * x / r5 * (-co.alp4 * (s2d - t * dr5) - co.alp5 * 5.0 * c_val / r2_s * (t + d * p * qr7))
        du[10] = (3.0 / r5 * (-co.alp4 * (d * b5 * c2d + y * c5 * s2d)
                  - co.alp5 * c_val * ((3.0 + a5) * c2d + y * p * dr5 * qr7)))
        du[11] = 3.0 / r5 * (-co.alp4 * d * a5 * co.sdcd - co.alp5 * c_val * (s2d - 10.0 * d * t / r2_s + p * qr5 * c7))
        u += pot2 / _PI2 * du

    # ---- Tensile ----
    if pot3 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = 3.0 * x / r5 * (-co.alp4 * s + co.alp5 * (c_val * q * qr5 - z))
        du[1] = co.alp4 / r3 * (s2d - 3.0 * y * s / r2_s) + co.alp5 * 3.0 / r5 * (c_val * (t - y + y * q * qr5) - y * z)
        du[2] = -co.alp4 / r3 * (1.0 - a3 * co.sdsd) - co.alp5 * 3.0 / r5 * (c_val * (s - d + d * q * qr5) - d * z)
        du[3] = -co.alp4 * 3.0 * s / r5 * a5 + co.alp5 * (c_val * qr * qr5 * a7 - 3.0 * z / r5 * a5)
        du[4] = 3.0 * x / r5 * (-co.alp4 * (s2d - 5.0 * y * s / r2_s) - co.alp5 * 5.0 / r2_s * (c_val * (t - y + y * q * qr7) - y * z))
        du[5] = 3.0 * x / r5 * (co.alp4 * (1.0 - (2.0 + a5) * co.sdsd) + co.alp5 * 5.0 / r2_s * (c_val * (s - d + d * q * qr7) - d * z))
        du[6] = du[4].copy()
        du[7] = (3.0 / r5 * (-co.alp4 * (2.0 * y * s2d + s * b5)
                 - co.alp5 * (c_val * (2.0 * co.sdsd + 10.0 * y * (t - y) / r2_s - q * qr5 * b7) + z * b5)))
        du[8] = (3.0 / r5 * (co.alp4 * y * (1.0 - a5 * co.sdsd)
                 + co.alp5 * (c_val * (3.0 + a5) * s2d - y * dr5 * (c_val * d7 + z))))
        du[9] = 3.0 * x / r5 * (-co.alp4 * (c2d + s * dr5) + co.alp5 * (5.0 * c_val / r2_s * (s - d + d * q * qr7) - 1.0 - z * dr5))
        du[10] = (3.0 / r5 * (co.alp4 * (d * b5 * s2d - y * c5 * c2d)
                  + co.alp5 * (c_val * ((3.0 + a5) * s2d - y * dr5 * d7) - y * (1.0 + z * dr5))))
        du[11] = (3.0 / r5 * (-co.alp4 * d * (1.0 - a5 * co.sdsd)
                  - co.alp5 * (c_val * (c2d + 10.0 * d * (s - d) / r2_s - q * qr5 * c7) + z * (1.0 + c5))))
        u += pot3 / _PI2 * du

    # ---- Inflation ----
    if pot4 != 0.0:
        du = np.empty((12, N), dtype=np.float64)
        du[0] = co.alp4 * 3.0 * x * d / r5
        du[1] = co.alp4 * 3.0 * y * d / r5
        du[2] = co.alp4 * c3 / r3
        du[3] = co.alp4 * 3.0 * d / r5 * a5
        du[4] = -co.alp4 * 15.0 * xy * d / r7
        du[5] = -co.alp4 * 3.0 * x / r5 * c5
        du[6] = du[4].copy()
        du[7] = co.alp4 * 3.0 * d / r5 * b5
        du[8] = -co.alp4 * 3.0 * y / r5 * c5
        du[9] = -du[5].copy()
        du[10] = -du[8].copy()
        du[11] = co.alp4 * 3.0 * d / r5 * (2.0 + c5)
        u += pot4 / _PI2 * du

    return u


def dc3d0(
    alpha: float,
    x: NDArray[np.float64] | float,
    y: NDArray[np.float64] | float,
    z: NDArray[np.float64] | float,
    depth: float,
    dip: float,
    pot1: float,
    pot2: float,
    pot3: float,
    pot4: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64],
           NDArray[np.float64], NDArray[np.float64], NDArray[np.float64],
           NDArray[np.float64], NDArray[np.float64], NDArray[np.float64],
           NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Compute displacement and gradients for a point dislocation source.

    Implements Okada (1992) DC3D0: point source variant.

    Parameters
    ----------
    alpha : float
        Medium constant = (lambda + mu) / (lambda + 2*mu).
    x, y, z : float or ndarray of shape (N,)
        Observation point coordinates. z must be <= 0.
    depth : float
        Source depth (positive, km).
    dip : float
        Dip angle (degrees).
    pot1 : float
        Strike-slip potency (m^2).
    pot2 : float
        Dip-slip potency.
    pot3 : float
        Tensile potency.
    pot4 : float
        Inflation potency.

    Returns
    -------
    tuple of 12 arrays of shape (N,)
        (ux, uy, uz, uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz)
    """
    x = np.atleast_1d(np.asarray(x, dtype=np.float64))
    y = np.atleast_1d(np.asarray(y, dtype=np.float64))
    z = np.atleast_1d(np.asarray(z, dtype=np.float64))
    N = x.shape[0]

    co = _dccon0(alpha, dip)

    u = np.zeros((12, N), dtype=np.float64)
    zz = z.copy()

    # Snap near-zero inputs.
    xx = np.where(np.abs(x) < _EPS, 0.0, x)
    yy = np.where(np.abs(y) < _EPS, 0.0, y)

    # ---- Real source ----
    dd = depth + z
    dd = np.where(np.abs(dd) < _EPS, 0.0, dd)

    dua = _ua0(xx, yy, dd, pot1, pot2, pot3, pot4, co.sd, co.cd, co)

    # Real source: u -= dua (with sign flip on last triplet)
    for i in range(12):
        if i < 9:
            u[i] -= dua[i]
        else:
            u[i] += dua[i]

    # ---- Image source ----
    dd = depth - z
    dd = np.where(np.abs(dd) < _EPS, 0.0, dd)

    dua = _ua0(xx, yy, dd, pot1, pot2, pot3, pot4, co.sd, co.cd, co)
    dub = _ub0(xx, yy, dd, zz, pot1, pot2, pot3, pot4, co.sd, co.cd, co)
    duc = _uc0(xx, yy, dd, zz, pot1, pot2, pot3, pot4, co.sd, co.cd, co)

    for i in range(12):
        du_val = dua[i] + dub[i] + zz * duc[i]
        if i >= 9:
            du_val = du_val + duc[i - 9]
        u[i] += du_val

    return (
        u[0], u[1], u[2],
        u[3], u[4], u[5],
        u[6], u[7], u[8],
        u[9], u[10], u[11],
    )
