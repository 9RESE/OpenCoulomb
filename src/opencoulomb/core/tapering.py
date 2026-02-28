"""Slip tapering for realistic source fault models.

Subdivides a large fault into smaller elements and applies a slip
taper profile so edges have reduced slip (more physically realistic
than uniform slip). This reduces stress singularities at fault tips.

Supports cosine, linear, and elliptical taper profiles.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from opencoulomb.types.fault import FaultElement


class TaperProfile(Enum):
    """Slip taper profile shape."""

    COSINE = "cosine"
    LINEAR = "linear"
    ELLIPTICAL = "elliptical"


@dataclass(frozen=True, slots=True)
class TaperSpec:
    """Specification for fault subdivision and slip tapering.

    Attributes
    ----------
    profile : TaperProfile
        Shape of the taper function.
    n_along_strike : int
        Number of subdivisions along strike (>= 1).
    n_down_dip : int
        Number of subdivisions down-dip (>= 1).
    taper_width_fraction : float
        Fraction of fault dimension over which taper is applied (0-0.5).
        0.0 = no taper, 0.5 = taper across entire fault.
    """

    profile: TaperProfile = TaperProfile.COSINE
    n_along_strike: int = 5
    n_down_dip: int = 3
    taper_width_fraction: float = 0.2

    def __post_init__(self) -> None:
        if self.n_along_strike < 1:
            msg = f"n_along_strike must be >= 1, got {self.n_along_strike}"
            raise ValueError(msg)
        if self.n_down_dip < 1:
            msg = f"n_down_dip must be >= 1, got {self.n_down_dip}"
            raise ValueError(msg)
        if not (0.0 <= self.taper_width_fraction <= 0.5):
            msg = f"taper_width_fraction must be in [0, 0.5], got {self.taper_width_fraction}"
            raise ValueError(msg)


def taper_function(
    xi: float,
    profile: TaperProfile,
    taper_fraction: float,
) -> float:
    """Compute taper weight at normalized position xi in [0, 1].

    Parameters
    ----------
    xi : float
        Normalized position along fault dimension (0 = start, 1 = end).
    profile : TaperProfile
        Taper shape.
    taper_fraction : float
        Fraction of fault over which taper is applied at each edge.

    Returns
    -------
    float
        Weight in [0, 1]. 1.0 = full slip, 0.0 = no slip.
    """
    if taper_fraction <= 0.0:
        return 1.0

    # Distance from nearest edge (0 = at edge, 0.5 = center)
    edge_dist = min(xi, 1.0 - xi)

    if edge_dist >= taper_fraction:
        return 1.0

    # Normalized position within taper zone: 0=edge, 1=full slip
    t = edge_dist / taper_fraction

    if profile == TaperProfile.COSINE:
        return 0.5 * (1.0 - math.cos(math.pi * t))
    if profile == TaperProfile.LINEAR:
        return t
    if profile == TaperProfile.ELLIPTICAL:
        return math.sqrt(1.0 - (1.0 - t) ** 2)
    return 1.0  # pragma: no cover


def subdivide_fault(
    fault: FaultElement,
    n_strike: int,
    n_dip: int,
) -> list[FaultElement]:
    """Subdivide a fault into a grid of smaller elements.

    Parameters
    ----------
    fault : FaultElement
        Original fault to subdivide.
    n_strike : int
        Number of subdivisions along strike.
    n_dip : int
        Number of subdivisions down-dip.

    Returns
    -------
    list[FaultElement]
        n_strike * n_dip sub-faults tiling the original.
    """
    if n_strike == 1 and n_dip == 1:
        return [fault]

    strike_rad = math.radians(fault.strike_deg)
    dip_rad = math.radians(fault.dip)
    sin_s = math.sin(strike_rad)
    cos_s = math.cos(strike_rad)
    sin_d = math.sin(dip_rad)
    cos_d = math.cos(dip_rad) if dip_rad != 0 else 0.0

    total_depth_range = fault.bottom_depth - fault.top_depth
    sub_depth_range = total_depth_range / n_dip

    # Horizontal offset per depth increment (updip direction)
    horiz_per_depth = cos_d / sin_d if sin_d > 1e-10 else 0.0

    subfaults: list[FaultElement] = []
    idx = 0
    for j in range(n_dip):
        sub_top = fault.top_depth + j * sub_depth_range
        sub_bottom = sub_top + sub_depth_range

        # Horizontal offset from surface trace due to depth
        depth_offset = sub_top * horiz_per_depth - fault.top_depth * horiz_per_depth
        offset_x = -cos_s * depth_offset
        offset_y = sin_s * depth_offset

        for i in range(n_strike):
            frac_start = i / n_strike
            frac_end = (i + 1) / n_strike

            # Surface trace endpoints for this sub-fault
            x_s = fault.x_start + frac_start * (fault.x_fin - fault.x_start) + offset_x
            y_s = fault.y_start + frac_start * (fault.y_fin - fault.y_start) + offset_y
            x_f = fault.x_start + frac_end * (fault.x_fin - fault.x_start) + offset_x
            y_f = fault.y_start + frac_end * (fault.y_fin - fault.y_start) + offset_y

            idx += 1
            subfaults.append(FaultElement(
                x_start=x_s,
                y_start=y_s,
                x_fin=x_f,
                y_fin=y_f,
                kode=fault.kode,
                slip_1=fault.slip_1,
                slip_2=fault.slip_2,
                dip=fault.dip,
                top_depth=sub_top,
                bottom_depth=sub_bottom,
                label=f"{fault.label}_sub{idx}" if fault.label else f"sub{idx}",
                element_index=0,
            ))

    return subfaults


def apply_taper(
    subfaults: list[FaultElement],
    taper_spec: TaperSpec,
) -> list[FaultElement]:
    """Apply slip taper weights to a list of subdivided faults.

    Assumes subfaults are ordered: row-major (dip-major, strike-minor),
    as produced by ``subdivide_fault``.

    Parameters
    ----------
    subfaults : list[FaultElement]
        Subdivided fault elements (from subdivide_fault).
    taper_spec : TaperSpec
        Taper specification.

    Returns
    -------
    list[FaultElement]
        Subfaults with tapered slip values.
    """
    n_s = taper_spec.n_along_strike
    n_d = taper_spec.n_down_dip
    profile = taper_spec.profile
    tw = taper_spec.taper_width_fraction

    tapered: list[FaultElement] = []
    for idx, sf in enumerate(subfaults):
        j = idx // n_s  # dip index
        i = idx % n_s   # strike index

        # Normalized center positions
        xi_s = (i + 0.5) / n_s if n_s > 1 else 0.5
        xi_d = (j + 0.5) / n_d if n_d > 1 else 0.5

        w_s = taper_function(xi_s, profile, tw)
        w_d = taper_function(xi_d, profile, tw)
        weight = w_s * w_d

        tapered.append(FaultElement(
            x_start=sf.x_start,
            y_start=sf.y_start,
            x_fin=sf.x_fin,
            y_fin=sf.y_fin,
            kode=sf.kode,
            slip_1=sf.slip_1 * weight,
            slip_2=sf.slip_2 * weight,
            dip=sf.dip,
            top_depth=sf.top_depth,
            bottom_depth=sf.bottom_depth,
            label=sf.label,
            element_index=sf.element_index,
        ))

    return tapered


def subdivide_and_taper(
    fault: FaultElement,
    taper: TaperSpec,
) -> list[FaultElement]:
    """Subdivide a fault and apply slip taper in one step.

    Parameters
    ----------
    fault : FaultElement
        Original source fault.
    taper : TaperSpec
        Subdivision + taper specification.

    Returns
    -------
    list[FaultElement]
        Tapered subfault elements.
    """
    subs = subdivide_fault(fault, taper.n_along_strike, taper.n_down_dip)
    return apply_taper(subs, taper)
