"""Coordinate transforms between geographic and fault-local systems.

Geographic system: X=East, Y=North, Z=Up (km).
Okada fault-local: X=along-strike, Y=updip-horizontal, Z=up.

All angles in radians unless noted. All coordinates in km.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def direction_cosines(
    strike_rad: float, dip_rad: float
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Compute fault direction cosine vectors.

    Parameters
    ----------
    strike_rad : float
        Strike angle in radians (clockwise from North).
    dip_rad : float
        Dip angle in radians (0 = horizontal, pi/2 = vertical).

    Returns
    -------
    l_strike, l_updip, l_normal : ndarray of shape (3,)
        Unit vectors in geographic (East, North, Up) coordinates.
        l_strike: along-strike direction.
        l_updip: updip direction in the fault plane (horizontal component).
        l_normal: outward normal to the fault plane.
    """
    # Following Okada (1992) coordinate convention:
    # x=along-strike, y=updip-horizontal, z=up.
    # Strike measured clockwise from North.
    # Dip measured from horizontal (0=horizontal, pi/2=vertical).
    ss = np.sin(strike_rad)
    cs = np.cos(strike_rad)
    sd = np.sin(dip_rad)
    cd = np.cos(dip_rad)

    l_strike = np.array([ss, cs, 0.0])
    l_updip = np.array([-cs * cd, ss * cd, sd])
    l_normal = np.array([cs * sd, -ss * sd, cd])

    return l_strike, l_updip, l_normal


def rotation_matrix(strike_rad: float, dip_rad: float) -> NDArray[np.float64]:
    """Build 3x3 rotation matrix from geographic to fault-local coordinates.

    Parameters
    ----------
    strike_rad, dip_rad : float
        Strike and dip in radians.

    Returns
    -------
    R : ndarray of shape (3, 3)
        Rows are the fault-local basis vectors expressed in geographic coords.
        v_local = R @ v_geo.
    """
    l_strike, l_updip, l_normal = direction_cosines(strike_rad, dip_rad)
    return np.vstack([l_strike, l_updip, l_normal])


def strike_dip_to_normal(
    strike_rad: float, dip_rad: float
) -> NDArray[np.float64]:
    """Compute the outward unit normal to a fault plane.

    Parameters
    ----------
    strike_rad, dip_rad : float
        Strike and dip in radians.

    Returns
    -------
    normal : ndarray of shape (3,)
        Unit normal vector in geographic (E, N, Up) coordinates.
    """
    _, _, n = direction_cosines(strike_rad, dip_rad)
    return n


def geo_to_fault(
    x_geo: NDArray[np.float64],
    y_geo: NDArray[np.float64],
    z_geo: NDArray[np.float64],
    fault_x: float,
    fault_y: float,
    fault_depth: float,
    strike_rad: float,
    dip_rad: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Transform geographic coordinates to fault-local coordinates.

    The fault-local origin is at the fault reference point (center of the
    top edge projected to surface for Coulomb convention).

    Parameters
    ----------
    x_geo, y_geo, z_geo : ndarray of shape (N,)
        Observation points in geographic coords (km). z positive upward.
    fault_x, fault_y : float
        Fault reference point (km, geographic).
    fault_depth : float
        Fault reference depth (km, positive downward).
    strike_rad, dip_rad : float
        Fault orientation (radians).

    Returns
    -------
    x_local, y_local, z_local : ndarray of shape (N,)
        Coordinates in fault-local system.
    """
    R = rotation_matrix(strike_rad, dip_rad)

    dx = x_geo - fault_x
    dy = y_geo - fault_y
    dz = z_geo + fault_depth  # z_geo is negative below surface, depth is positive

    x_local = R[0, 0] * dx + R[0, 1] * dy + R[0, 2] * dz
    y_local = R[1, 0] * dx + R[1, 1] * dy + R[1, 2] * dz
    z_local = R[2, 0] * dx + R[2, 1] * dy + R[2, 2] * dz

    return x_local, y_local, z_local


def fault_to_geo_displacement(
    ux_local: NDArray[np.float64],
    uy_local: NDArray[np.float64],
    uz_local: NDArray[np.float64],
    strike_rad: float,
    dip_rad: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Rotate displacement vector from fault-local to geographic coordinates.

    Parameters
    ----------
    ux_local, uy_local, uz_local : ndarray of shape (N,)
        Displacement in fault-local system (m).
    strike_rad, dip_rad : float
        Fault orientation (radians).

    Returns
    -------
    ux_geo, uy_geo, uz_geo : ndarray of shape (N,)
        Displacement in geographic (East, North, Up) system (m).
    """
    R = rotation_matrix(strike_rad, dip_rad)
    # Inverse rotation: v_geo = R^T @ v_local
    RT = R.T

    ux_geo = RT[0, 0] * ux_local + RT[0, 1] * uy_local + RT[0, 2] * uz_local
    uy_geo = RT[1, 0] * ux_local + RT[1, 1] * uy_local + RT[1, 2] * uz_local
    uz_geo = RT[2, 0] * ux_local + RT[2, 1] * uy_local + RT[2, 2] * uz_local

    return ux_geo, uy_geo, uz_geo


def compute_fault_geometry(
    x_start: float,
    y_start: float,
    x_fin: float,
    y_fin: float,
    dip_deg: float,
    top_depth: float,
    bottom_depth: float,
) -> dict[str, float]:
    """Compute derived fault geometry for Okada input.

    Parameters
    ----------
    x_start, y_start : float
        Fault trace start point (km, geographic).
    x_fin, y_fin : float
        Fault trace end point (km, geographic).
    dip_deg : float
        Dip angle in degrees.
    top_depth, bottom_depth : float
        Depth range (km, positive downward).

    Returns
    -------
    dict with keys:
        strike_rad, dip_rad : float
            Angles in radians.
        length : float
            Fault trace length (km).
        width : float
            Down-dip width (km).
        center_x, center_y, center_depth : float
            Fault centroid (km).
        al1, al2 : float
            Half-lengths along strike (km). al1 = -L/2, al2 = +L/2.
        aw1, aw2 : float
            Half-widths down-dip (km). aw1 = -W/2, aw2 = +W/2.
        depth : float
            Reference depth for Okada (km, center of fault).
    """
    dx = x_fin - x_start
    dy = y_fin - y_start
    length = np.sqrt(dx * dx + dy * dy)

    strike_rad = np.arctan2(dx, dy)  # atan2(East, North) = clockwise from N
    dip_rad = np.radians(dip_deg)

    # Down-dip width
    depth_range = bottom_depth - top_depth
    sd = np.sin(dip_rad)
    width = depth_range / sd if sd > 1e-10 else depth_range  # vertical for ~horizontal

    # Center of fault (geographic)
    mid_x = (x_start + x_fin) / 2.0
    mid_y = (y_start + y_fin) / 2.0
    mid_depth = (top_depth + bottom_depth) / 2.0

    # Horizontal offset from trace midpoint to fault center (updip direction)
    cd = np.cos(dip_rad)
    horiz_offset = (mid_depth - top_depth) * cd / sd if sd > 1e-10 else 0.0

    # The updip direction perpendicular to strike (to the right when looking along strike)
    cs = np.cos(strike_rad)
    ss = np.sin(strike_rad)
    center_x = mid_x - cs * horiz_offset  # perpendicular to strike = (-cos(s), sin(s))
    center_y = mid_y + ss * horiz_offset

    # Okada half-dimensions (symmetric about center)
    al1 = -length / 2.0
    al2 = length / 2.0
    aw1 = -width / 2.0
    aw2 = width / 2.0

    return {
        "strike_rad": float(strike_rad),
        "dip_rad": float(dip_rad),
        "length": float(length),
        "width": float(width),
        "center_x": float(center_x),
        "center_y": float(center_y),
        "center_depth": float(mid_depth),
        "al1": float(al1),
        "al2": float(al2),
        "aw1": float(aw1),
        "aw2": float(aw2),
        "depth": float(mid_depth),
    }
