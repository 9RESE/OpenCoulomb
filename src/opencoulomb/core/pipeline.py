"""Computation pipeline: .inp model → CFS results.

Orchestrates the full computation flow:
1. Generate observation grid from GridSpec
2. Loop over source faults (superposition):
   a. Coordinate transform (geographic → fault-local)
   b. Okada DC3D/DC3D0 computation
   c. Displacement rotation (fault-local → geographic)
   d. Stress from gradients (Hooke's law)
   e. Stress tensor rotation (fault-local → geographic)
   f. Accumulate into total stress/displacement
3. Resolve total stress onto receiver faults → CFS
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

from opencoulomb.core.coordinates import compute_fault_geometry, fault_to_geo_displacement
from opencoulomb.core.coulomb import compute_cfs_on_receiver
from opencoulomb.core.okada import dc3d, dc3d0
from opencoulomb.core.stress import gradients_to_stress, rotate_stress_tensor
from opencoulomb.types.fault import FaultElement, Kode
from opencoulomb.types.result import CoulombResult, ElementResult, StressResult

if TYPE_CHECKING:
    from opencoulomb.types.model import CoulombModel


def compute_grid(model: CoulombModel) -> CoulombResult:
    """Run the full CFS computation on a grid.

    Parameters
    ----------
    model : CoulombModel
        Fully populated model from .inp parser.

    Returns
    -------
    CoulombResult
        Complete result with stress, displacement, and CFS on the grid.
    """
    grid = model.grid
    material = model.material

    # 1. Generate observation grid
    x_1d = np.arange(grid.start_x, grid.finish_x + grid.x_inc * 0.5, grid.x_inc)
    y_1d = np.arange(grid.start_y, grid.finish_y + grid.y_inc * 0.5, grid.y_inc)
    n_x = len(x_1d)
    n_y = len(y_1d)

    # Meshgrid: x varies along columns, y along rows
    gx, gy = np.meshgrid(x_1d, y_1d)
    x_flat = gx.ravel()
    y_flat = gy.ravel()
    z_flat = np.full_like(x_flat, -grid.depth)  # negative below surface
    n_pts = len(x_flat)

    # 2. Initialize accumulators
    total_ux = np.zeros(n_pts)
    total_uy = np.zeros(n_pts)
    total_uz = np.zeros(n_pts)
    total_sxx = np.zeros(n_pts)
    total_syy = np.zeros(n_pts)
    total_szz = np.zeros(n_pts)
    total_syz = np.zeros(n_pts)
    total_sxz = np.zeros(n_pts)
    total_sxy = np.zeros(n_pts)

    alpha = material.alpha

    # 3. Source fault loop (superposition)
    for fault in model.source_faults:
        _accumulate_fault(
            fault, alpha, material.young, material.poisson,
            x_flat, y_flat, z_flat,
            total_ux, total_uy, total_uz,
            total_sxx, total_syy, total_szz,
            total_syz, total_sxz, total_sxy,
        )

    # Build StressResult
    stress = StressResult(
        x=x_flat, y=y_flat, z=z_flat,
        ux=total_ux, uy=total_uy, uz=total_uz,
        sxx=total_sxx, syy=total_syy, szz=total_szz,
        syz=total_syz, sxz=total_sxz, sxy=total_sxy,
    )

    # 4. Resolve CFS on receiver faults
    # Use first receiver fault orientation for grid CFS, or default
    receivers = model.receiver_faults
    if receivers:
        recv = receivers[0]
        geom = compute_fault_geometry(
            recv.x_start, recv.y_start, recv.x_fin, recv.y_fin,
            recv.dip, recv.top_depth, recv.bottom_depth,
        )
        recv_strike = geom["strike_rad"]
        recv_dip = geom["dip_rad"]
        recv_rake = recv.rake_rad
    else:
        # Default: use first source fault orientation with 0 rake
        src = model.source_faults[0]
        geom = compute_fault_geometry(
            src.x_start, src.y_start, src.x_fin, src.y_fin,
            src.dip, src.top_depth, src.bottom_depth,
        )
        recv_strike = geom["strike_rad"]
        recv_dip = geom["dip_rad"]
        recv_rake = 0.0

    cfs, shear, normal = compute_cfs_on_receiver(
        total_sxx, total_syy, total_szz,
        total_syz, total_sxz, total_sxy,
        recv_strike, recv_dip, recv_rake,
        material.friction,
    )

    return CoulombResult(
        stress=stress,
        cfs=cfs,
        shear=shear,
        normal=normal,
        receiver_strike=math.degrees(recv_strike),
        receiver_dip=math.degrees(recv_dip),
        receiver_rake=math.degrees(recv_rake),
        grid_shape=(n_y, n_x),
    )


def compute_element_cfs(model: CoulombModel) -> ElementResult | None:
    """Compute CFS at individual receiver fault element centers.

    Parameters
    ----------
    model : CoulombModel
        Model with source and receiver faults.

    Returns
    -------
    ElementResult or None
        CFS at each receiver element center. None if no receivers.
    """
    receivers = model.receiver_faults
    if not receivers:
        return None

    material = model.material
    alpha = material.alpha
    n_recv = len(receivers)

    # Compute observation points at receiver centers
    x_obs = np.empty(n_recv)
    y_obs = np.empty(n_recv)
    z_obs = np.empty(n_recv)

    for i, recv in enumerate(receivers):
        x_obs[i] = recv.center_x
        y_obs[i] = recv.center_y
        z_obs[i] = -recv.center_depth  # negative below surface

    # Initialize accumulators
    total_sxx = np.zeros(n_recv)
    total_syy = np.zeros(n_recv)
    total_szz = np.zeros(n_recv)
    total_syz = np.zeros(n_recv)
    total_sxz = np.zeros(n_recv)
    total_sxy = np.zeros(n_recv)
    total_ux = np.zeros(n_recv)
    total_uy = np.zeros(n_recv)
    total_uz = np.zeros(n_recv)

    # Accumulate stress from all source faults
    for fault in model.source_faults:
        _accumulate_fault(
            fault, alpha, material.young, material.poisson,
            x_obs, y_obs, z_obs,
            total_ux, total_uy, total_uz,
            total_sxx, total_syy, total_szz,
            total_syz, total_sxz, total_sxy,
        )

    # Resolve CFS at each receiver using its own orientation
    cfs_arr = np.empty(n_recv)
    shear_arr = np.empty(n_recv)
    normal_arr = np.empty(n_recv)

    for i, recv in enumerate(receivers):
        geom = compute_fault_geometry(
            recv.x_start, recv.y_start, recv.x_fin, recv.y_fin,
            recv.dip, recv.top_depth, recv.bottom_depth,
        )
        cfs_i, shear_i, normal_i = compute_cfs_on_receiver(
            total_sxx[i:i + 1], total_syy[i:i + 1], total_szz[i:i + 1],
            total_syz[i:i + 1], total_sxz[i:i + 1], total_sxy[i:i + 1],
            geom["strike_rad"], geom["dip_rad"], recv.rake_rad,
            material.friction,
        )
        cfs_arr[i] = cfs_i[0]
        shear_arr[i] = shear_i[0]
        normal_arr[i] = normal_i[0]

    return ElementResult(
        elements=list(receivers),
        cfs=cfs_arr,
        shear=shear_arr,
        normal=normal_arr,
    )


def _accumulate_fault(
    fault: FaultElement,
    alpha: float,
    young: float,
    poisson: float,
    x_obs: NDArray[np.float64],
    y_obs: NDArray[np.float64],
    z_obs: NDArray[np.float64],
    total_ux: NDArray[np.float64],
    total_uy: NDArray[np.float64],
    total_uz: NDArray[np.float64],
    total_sxx: NDArray[np.float64],
    total_syy: NDArray[np.float64],
    total_szz: NDArray[np.float64],
    total_syz: NDArray[np.float64],
    total_sxz: NDArray[np.float64],
    total_sxy: NDArray[np.float64],
) -> None:
    """Compute and accumulate displacement/stress from one source fault.

    Modifies the total_* arrays in place.
    """
    geom = compute_fault_geometry(
        fault.x_start, fault.y_start, fault.x_fin, fault.y_fin,
        fault.dip, fault.top_depth, fault.bottom_depth,
    )

    strike_rad = geom["strike_rad"]
    dip_rad = geom["dip_rad"]
    dip_deg = fault.dip

    # Transform observation points to fault-local coordinates
    ss = np.sin(strike_rad)
    cs = np.cos(strike_rad)

    # Translate to fault center
    dx = x_obs - geom["center_x"]
    dy = y_obs - geom["center_y"]

    # Rotate to fault-local (along-strike, perpendicular)
    x_local = ss * dx + cs * dy
    y_local = -cs * dx + ss * dy

    # Okada uses depth = center_depth, z_obs is negative
    # The Okada z input must be ≤ 0 (z_obs is already negative)

    # Dispatch based on KODE
    disl1, disl2, disl3 = _kode_to_dislocation(fault)

    if fault.kode in (Kode.POINT_SOURCE, Kode.TENSILE_INFL):
        pot1, pot2, pot3, pot4 = _kode_to_potency(fault)
        result = dc3d0(
            alpha, x_local, y_local, z_obs,
            geom["depth"], dip_deg,
            pot1, pot2, pot3, pot4,
        )
    else:
        result = dc3d(
            alpha, x_local, y_local, z_obs,
            geom["depth"], dip_deg,
            geom["al1"], geom["al2"],
            geom["aw1"], geom["aw2"],
            disl1, disl2, disl3,
        )

    ux_l, uy_l, uz_l = result[0], result[1], result[2]
    uxx, uyx, uzx = result[3], result[4], result[5]
    uxy, uyy, uzy = result[6], result[7], result[8]
    uxz, uyz, uzz = result[9], result[10], result[11]

    # Rotate displacement to geographic
    ux_g, uy_g, uz_g = fault_to_geo_displacement(
        ux_l, uy_l, uz_l, strike_rad, dip_rad,
    )

    # Compute stress in fault-local coordinates
    sxx_l, syy_l, szz_l, syz_l, sxz_l, sxy_l = gradients_to_stress(
        uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz,
        young, poisson,
    )

    # Rotate stress to geographic
    sxx_g, syy_g, szz_g, syz_g, sxz_g, sxy_g = rotate_stress_tensor(
        sxx_l, syy_l, szz_l, syz_l, sxz_l, sxy_l,
        strike_rad, dip_rad,
    )

    # Accumulate (in-place)
    total_ux += ux_g
    total_uy += uy_g
    total_uz += uz_g
    total_sxx += sxx_g
    total_syy += syy_g
    total_szz += szz_g
    total_syz += syz_g
    total_sxz += sxz_g
    total_sxy += sxy_g


def _kode_to_dislocation(
    fault: FaultElement,
) -> tuple[float, float, float]:
    """Convert fault element slip to Okada dislocation components.

    Handles sign conventions and KODE dispatch for finite faults.

    Returns
    -------
    disl1, disl2, disl3 : float
        Strike-slip, dip-slip, tensile dislocation (m).
    """
    kode = fault.kode
    col5 = fault.slip_1  # right-lateral or tensile
    col6 = fault.slip_2  # reverse or tensile

    if kode == Kode.STANDARD:       # 100: strike-slip + dip-slip
        return -col5, col6, 0.0     # sign flip: Coulomb RL+ → Okada LL+
    if kode == Kode.TENSILE_RL:     # 200: tensile + right-lateral
        return -col6, 0.0, col5
    if kode == Kode.TENSILE_REV:    # 300: tensile + reverse
        return 0.0, col6, col5
    # Point sources handled separately
    return 0.0, 0.0, 0.0


def _kode_to_potency(
    fault: FaultElement,
) -> tuple[float, float, float, float]:
    """Convert fault element to point source potency.

    Returns
    -------
    pot1, pot2, pot3, pot4 : float
        Strike, dip, tensile, inflation potency.
    """
    col5 = fault.slip_1
    col6 = fault.slip_2

    if fault.kode == Kode.POINT_SOURCE:     # 400
        return -col5, col6, 0.0, 0.0
    if fault.kode == Kode.TENSILE_INFL:     # 500
        return 0.0, 0.0, col5, col6
    return 0.0, 0.0, 0.0, 0.0
