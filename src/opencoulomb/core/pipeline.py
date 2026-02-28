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
4. (Optional) OOPs: add regional stress, find optimal failure planes
5. Cross-section: compute stress/displacement on a vertical profile
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
from opencoulomb.exceptions import ComputationError
from opencoulomb.types.fault import FaultElement, Kode
from opencoulomb.types.result import (
    CoulombResult,
    ElementResult,
    StrainResult,
    StressResult,
    VolumeResult,
)

if TYPE_CHECKING:
    from opencoulomb.core.tapering import TaperSpec
    from opencoulomb.types.grid import VolumeGridSpec
    from opencoulomb.types.model import CoulombModel
    from opencoulomb.types.section import CrossSectionResult, CrossSectionSpec


def compute_grid(
    model: CoulombModel,
    receiver_index: int | None = None,
    compute_strain: bool = False,
    taper: TaperSpec | None = None,
) -> CoulombResult:
    """Run the full CFS computation on a grid.

    Grid CFS is resolved onto a single receiver fault orientation,
    matching Coulomb 3.4 behavior. Use ``compute_element_cfs`` for
    per-receiver CFS at element centers.

    Parameters
    ----------
    model : CoulombModel
        Fully populated model from .inp parser.
    receiver_index : int or None
        Which receiver fault to use for resolving grid CFS.
        ``None`` (default) uses the first receiver (index 0), or
        falls back to the first source fault orientation if no
        receivers exist.
    compute_strain : bool
        If True, also compute strain tensor at grid points.
    taper : TaperSpec or None
        If provided, subdivide source faults and apply slip taper.

    Returns
    -------
    CoulombResult
        Complete result with stress, displacement, and CFS on the grid.

    Raises
    ------
    ComputationError
        If the model has no source faults.
    ValidationError
        If *receiver_index* is out of bounds.
    """
    if not model.source_faults:
        raise ComputationError(
            "Model has no source faults; cannot compute grid CFS. "
            "At least one source fault with non-zero slip is required."
        )

    grid = model.grid
    material = model.material

    # 1. Generate observation grid
    # Grid generation: the +x_inc*0.5 ensures the endpoint is included
    # despite floating-point rounding in np.arange.
    x_1d = np.arange(grid.start_x, grid.finish_x + grid.x_inc * 0.5, grid.x_inc)
    y_1d = np.arange(grid.start_y, grid.finish_y + grid.y_inc * 0.5, grid.y_inc)
    n_x = len(x_1d)
    n_y = len(y_1d)

    # Meshgrid: x varies along columns, y along rows
    gx, gy = np.meshgrid(x_1d, y_1d)
    x_flat = gx.ravel()
    y_flat = gy.ravel()
    z_flat = np.full_like(x_flat, -grid.depth)  # negative = below surface (Okada convention: z<=0)
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
        if taper is not None:
            from opencoulomb.core.tapering import subdivide_and_taper
            for sub in subdivide_and_taper(fault, taper):
                _accumulate_fault(
                    sub, alpha, material.young, material.poisson,
                    x_flat, y_flat, z_flat,
                    total_ux, total_uy, total_uz,
                    total_sxx, total_syy, total_szz,
                    total_syz, total_sxz, total_sxy,
                )
        else:
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
    # Grid CFS uses a single receiver orientation (Coulomb 3.4 behavior).
    receivers = model.receiver_faults
    if receivers:
        idx = receiver_index if receiver_index is not None else 0
        if idx < 0 or idx >= len(receivers):
            from opencoulomb.exceptions import ValidationError
            raise ValidationError(
                f"receiver_index={idx} out of range; "
                f"model has {len(receivers)} receiver(s) (0..{len(receivers) - 1})"
            )
        recv = receivers[idx]
        geom = compute_fault_geometry(
            recv.x_start, recv.y_start, recv.x_fin, recv.y_fin,
            recv.dip, recv.top_depth, recv.bottom_depth,
        )
        recv_strike = geom["strike_rad"]
        recv_dip = geom["dip_rad"]
        recv_rake = recv.rake_rad
    else:
        if receiver_index is not None:
            from opencoulomb.exceptions import ValidationError
            raise ValidationError(
                f"receiver_index={receiver_index} specified but model has no receivers"
            )
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

    # 5. OOPs: optimally oriented planes (when regional stress is specified)
    oops_strike = None
    oops_dip = None
    oops_rake = None

    if model.regional_stress is not None:
        from opencoulomb.core.oops import compute_regional_stress_tensor, find_optimal_planes

        # Depth is positive downward for regional stress
        depth_positive = np.abs(z_flat)

        r_sxx, r_syy, r_szz, r_syz, r_sxz, r_sxy = (
            compute_regional_stress_tensor(model.regional_stress, depth_positive)
        )

        # Total stress = earthquake + regional (superposition)
        t_sxx = total_sxx + r_sxx
        t_syy = total_syy + r_syy
        t_szz = total_szz + r_szz
        t_syz = total_syz + r_syz
        t_sxz = total_sxz + r_sxz
        t_sxy = total_sxy + r_sxy

        oops_strike, oops_dip, oops_rake, _ = find_optimal_planes(
            t_sxx, t_syy, t_szz, t_syz, t_sxz, t_sxy,
            material.friction,
        )

    # Compute strain if requested
    strain_result: StrainResult | None = None
    if compute_strain:
        strain_result = _compute_strain_from_stress_result(stress, material.young, material.poisson)

    return CoulombResult(
        stress=stress,
        cfs=cfs,
        shear=shear,
        normal=normal,
        receiver_strike=math.degrees(recv_strike),
        receiver_dip=math.degrees(recv_dip),
        receiver_rake=math.degrees(recv_rake),
        grid_shape=(n_y, n_x),
        oops_strike=oops_strike,
        oops_dip=oops_dip,
        oops_rake=oops_rake,
        strain=strain_result,
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

    # Guard against degenerate faults that would produce NaN
    if geom["length"] < 1e-10 and not fault.is_point_source:
        import warnings
        warnings.warn(
            f"Skipping degenerate fault (length={geom['length']:.2e} km): {fault.label}",
            stacklevel=2,
        )
        return

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


def compute_cross_section(
    model: CoulombModel,
    spec: CrossSectionSpec | None = None,
    receiver_index: int | None = None,
) -> CrossSectionResult:
    """Compute stress/displacement on a vertical cross-section profile.

    Generates a 2D grid of observation points along a profile line and
    at regular depth intervals, then computes the full stress field and
    CFS at each point.

    Parameters
    ----------
    model : CoulombModel
        Fully populated model from .inp parser.
    spec : CrossSectionSpec or None
        Cross-section specification. If None, uses ``model.cross_section``.
    receiver_index : int or None
        Which receiver fault to use for CFS resolution (same as compute_grid).

    Returns
    -------
    CrossSectionResult
        Stress, displacement, and CFS on the 2D profile grid.

    Raises
    ------
    ComputationError
        If the model has no source faults or no cross-section specification.
    ValidationError
        If *receiver_index* is out of bounds.
    """
    from opencoulomb.types.section import CrossSectionResult as _CSResult

    if not model.source_faults:
        raise ComputationError(
            "Model has no source faults; cannot compute cross-section. "
            "At least one source fault with non-zero slip is required."
        )

    cs = spec if spec is not None else model.cross_section
    if cs is None:
        raise ComputationError(
            "No cross-section specification provided. "
            "Pass a CrossSectionSpec or use a model with cross-section parameters."
        )

    material = model.material
    alpha = material.alpha
    grid = model.grid

    # Generate profile geometry
    dx = cs.finish_x - cs.start_x
    dy = cs.finish_y - cs.start_y
    profile_length = math.sqrt(dx * dx + dy * dy)

    if profile_length < 1e-10:
        raise ComputationError(
            "Cross-section profile has zero length "
            f"(start=({cs.start_x}, {cs.start_y}), "
            f"finish=({cs.finish_x}, {cs.finish_y}))"
        )

    # Horizontal resolution: use grid x_inc
    h_inc = grid.x_inc
    n_horiz = max(round(profile_length / h_inc) + 1, 2)

    # Depth resolution
    depth_range = cs.depth_max - cs.depth_min
    n_vert = max(round(depth_range / cs.z_inc) + 1, 2)

    # 1D arrays
    distance = np.linspace(0.0, profile_length, n_horiz)
    depth = np.linspace(cs.depth_min, cs.depth_max, n_vert)

    # Direction unit vector along profile
    ux_dir = dx / profile_length
    uy_dir = dy / profile_length

    # 2D meshgrid: (depth, distance)
    dist_2d, depth_2d = np.meshgrid(distance, depth)
    dist_flat = dist_2d.ravel()
    depth_flat = depth_2d.ravel()
    n_pts = len(dist_flat)

    # Geographic coordinates of observation points
    x_flat = cs.start_x + dist_flat * ux_dir
    y_flat = cs.start_y + dist_flat * uy_dir
    z_flat = -depth_flat  # negative below surface (Okada convention)

    # Initialize accumulators
    total_ux = np.zeros(n_pts)
    total_uy = np.zeros(n_pts)
    total_uz = np.zeros(n_pts)
    total_sxx = np.zeros(n_pts)
    total_syy = np.zeros(n_pts)
    total_szz = np.zeros(n_pts)
    total_syz = np.zeros(n_pts)
    total_sxz = np.zeros(n_pts)
    total_sxy = np.zeros(n_pts)

    # Source fault loop (superposition)
    for fault in model.source_faults:
        _accumulate_fault(
            fault, alpha, material.young, material.poisson,
            x_flat, y_flat, z_flat,
            total_ux, total_uy, total_uz,
            total_sxx, total_syy, total_szz,
            total_syz, total_sxz, total_sxy,
        )

    # Determine receiver orientation (same logic as compute_grid)
    receivers = model.receiver_faults
    if receivers:
        idx = receiver_index if receiver_index is not None else 0
        if idx < 0 or idx >= len(receivers):
            from opencoulomb.exceptions import ValidationError
            raise ValidationError(
                f"receiver_index={idx} out of range; "
                f"model has {len(receivers)} receiver(s) (0..{len(receivers) - 1})"
            )
        recv = receivers[idx]
        geom = compute_fault_geometry(
            recv.x_start, recv.y_start, recv.x_fin, recv.y_fin,
            recv.dip, recv.top_depth, recv.bottom_depth,
        )
        recv_strike = geom["strike_rad"]
        recv_dip = geom["dip_rad"]
        recv_rake = recv.rake_rad
    else:
        if receiver_index is not None:
            from opencoulomb.exceptions import ValidationError
            raise ValidationError(
                f"receiver_index={receiver_index} specified but model has no receivers"
            )
        src = model.source_faults[0]
        geom = compute_fault_geometry(
            src.x_start, src.y_start, src.x_fin, src.y_fin,
            src.dip, src.top_depth, src.bottom_depth,
        )
        recv_strike = geom["strike_rad"]
        recv_dip = geom["dip_rad"]
        recv_rake = 0.0

    # Resolve CFS
    cfs_flat, shear_flat, normal_flat = compute_cfs_on_receiver(
        total_sxx, total_syy, total_szz,
        total_syz, total_sxz, total_sxy,
        recv_strike, recv_dip, recv_rake,
        material.friction,
    )

    # Reshape to 2D (n_vert, n_horiz)
    shape = (n_vert, n_horiz)

    return _CSResult(
        distance=distance,
        depth=depth,
        cfs=cfs_flat.reshape(shape),
        shear=shear_flat.reshape(shape),
        normal=normal_flat.reshape(shape),
        ux=total_ux.reshape(shape),
        uy=total_uy.reshape(shape),
        uz=total_uz.reshape(shape),
        sxx=total_sxx.reshape(shape),
        syy=total_syy.reshape(shape),
        szz=total_szz.reshape(shape),
        syz=total_syz.reshape(shape),
        sxz=total_sxz.reshape(shape),
        sxy=total_sxy.reshape(shape),
        spec=cs,
    )


def compute_volume(
    model: CoulombModel,
    volume_spec: VolumeGridSpec,
    receiver_index: int | None = None,
    compute_strain: bool = False,
    taper: TaperSpec | None = None,
) -> VolumeResult:
    """Compute 3D CFS volume through multiple depth layers.

    Generates a full 3D meshgrid and passes all points through the
    same accumulation loop as ``compute_grid``.

    Parameters
    ----------
    model : CoulombModel
        Fully populated model.
    volume_spec : VolumeGridSpec
        3D grid specification with depth range.
    receiver_index : int or None
        Receiver fault for CFS resolution.
    compute_strain : bool
        If True, also compute strain tensor.
    taper : TaperSpec or None
        Optional slip tapering.

    Returns
    -------
    VolumeResult
        3D stress, displacement, and CFS.
    """
    if not model.source_faults:
        raise ComputationError(
            "Model has no source faults; cannot compute volume."
        )

    material = model.material
    alpha = material.alpha

    # Generate 3D meshgrid
    x_1d = np.arange(
        volume_spec.start_x,
        volume_spec.finish_x + volume_spec.x_inc * 0.5,
        volume_spec.x_inc,
    )
    y_1d = np.arange(
        volume_spec.start_y,
        volume_spec.finish_y + volume_spec.y_inc * 0.5,
        volume_spec.y_inc,
    )
    depths = volume_spec.depths
    n_x = len(x_1d)
    n_y = len(y_1d)
    n_z = len(depths)

    # Build 3D grid: order (depth, y, x) for natural slicing
    # meshgrid with indexing='ij' for (z, y, x) ordering
    gd, gy, gx = np.meshgrid(depths, y_1d, x_1d, indexing="ij")
    x_flat = gx.ravel()
    y_flat = gy.ravel()
    z_flat = -gd.ravel()  # negative below surface (Okada convention)
    n_pts = len(x_flat)

    # Initialize accumulators
    total_ux = np.zeros(n_pts)
    total_uy = np.zeros(n_pts)
    total_uz = np.zeros(n_pts)
    total_sxx = np.zeros(n_pts)
    total_syy = np.zeros(n_pts)
    total_szz = np.zeros(n_pts)
    total_syz = np.zeros(n_pts)
    total_sxz = np.zeros(n_pts)
    total_sxy = np.zeros(n_pts)

    # Source fault loop
    for fault in model.source_faults:
        if taper is not None:
            from opencoulomb.core.tapering import subdivide_and_taper
            for sub in subdivide_and_taper(fault, taper):
                _accumulate_fault(
                    sub, alpha, material.young, material.poisson,
                    x_flat, y_flat, z_flat,
                    total_ux, total_uy, total_uz,
                    total_sxx, total_syy, total_szz,
                    total_syz, total_sxz, total_sxy,
                )
        else:
            _accumulate_fault(
                fault, alpha, material.young, material.poisson,
                x_flat, y_flat, z_flat,
                total_ux, total_uy, total_uz,
                total_sxx, total_syy, total_szz,
                total_syz, total_sxz, total_sxy,
            )

    stress = StressResult(
        x=x_flat, y=y_flat, z=z_flat,
        ux=total_ux, uy=total_uy, uz=total_uz,
        sxx=total_sxx, syy=total_syy, szz=total_szz,
        syz=total_syz, sxz=total_sxz, sxy=total_sxy,
    )

    # Receiver orientation (same logic as compute_grid)
    recv_strike, recv_dip, recv_rake = _resolve_receiver_orientation(
        model, receiver_index,
    )

    cfs, shear, normal = compute_cfs_on_receiver(
        total_sxx, total_syy, total_szz,
        total_syz, total_sxz, total_sxy,
        recv_strike, recv_dip, recv_rake,
        material.friction,
    )

    strain_result: StrainResult | None = None
    if compute_strain:
        strain_result = _compute_strain_from_stress_result(stress, material.young, material.poisson)

    return VolumeResult(
        stress=stress,
        cfs=cfs,
        shear=shear,
        normal=normal,
        receiver_strike=math.degrees(recv_strike),
        receiver_dip=math.degrees(recv_dip),
        receiver_rake=math.degrees(recv_rake),
        volume_shape=(n_z, n_y, n_x),
        depths=depths,
        strain=strain_result,
    )


def _resolve_receiver_orientation(
    model: CoulombModel,
    receiver_index: int | None,
) -> tuple[float, float, float]:
    """Determine receiver fault orientation for CFS resolution.

    Returns strike_rad, dip_rad, rake_rad.
    """
    receivers = model.receiver_faults
    if receivers:
        idx = receiver_index if receiver_index is not None else 0
        if idx < 0 or idx >= len(receivers):
            from opencoulomb.exceptions import ValidationError
            raise ValidationError(
                f"receiver_index={idx} out of range; "
                f"model has {len(receivers)} receiver(s) (0..{len(receivers) - 1})"
            )
        recv = receivers[idx]
        geom = compute_fault_geometry(
            recv.x_start, recv.y_start, recv.x_fin, recv.y_fin,
            recv.dip, recv.top_depth, recv.bottom_depth,
        )
        return geom["strike_rad"], geom["dip_rad"], recv.rake_rad

    if receiver_index is not None:
        from opencoulomb.exceptions import ValidationError
        raise ValidationError(
            f"receiver_index={receiver_index} specified but model has no receivers"
        )
    src = model.source_faults[0]
    geom = compute_fault_geometry(
        src.x_start, src.y_start, src.x_fin, src.y_fin,
        src.dip, src.top_depth, src.bottom_depth,
    )
    return geom["strike_rad"], geom["dip_rad"], 0.0


def _compute_strain_from_stress_result(
    stress: StressResult,
    young: float,
    poisson: float,
) -> StrainResult:
    """Compute strain from stress using inverse Hooke's law.

    For consistency with the forward computation, we invert:
    sigma = lambda*tr(e)*I + 2*mu*e  →  e = (sigma - lambda*tr(sigma)*I/(3*lambda+2*mu)) / (2*mu)

    But it's simpler to use the compliance form:
    e_ij = ((1+nu)/E) * sigma_ij - (nu/E) * delta_ij * sigma_kk
    """
    nu = poisson
    e = young
    inv_e = 1.0 / e
    factor_diag = (1.0 + nu) * inv_e
    factor_vol = nu * inv_e

    sigma_kk = stress.sxx + stress.syy + stress.szz

    exx = factor_diag * stress.sxx - factor_vol * sigma_kk
    eyy = factor_diag * stress.syy - factor_vol * sigma_kk
    ezz = factor_diag * stress.szz - factor_vol * sigma_kk
    eyz = factor_diag * stress.syz  # off-diagonal: no volumetric term
    exz = factor_diag * stress.sxz
    exy = factor_diag * stress.sxy
    vol = exx + eyy + ezz

    return StrainResult(
        exx=exx, eyy=eyy, ezz=ezz,
        eyz=eyz, exz=exz, exy=exy,
        volumetric=vol,  # type: ignore[arg-type]  # numpy dtype inference limitation
    )
