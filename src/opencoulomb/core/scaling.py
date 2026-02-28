"""Earthquake scaling relations.

Implements magnitude-to-fault dimension relationships:
- Wells & Coppersmith (1994): Empirical from surface rupture data
- Blaser et al. (2010): Updated with subduction zone events

References
----------
Wells, D.L. & Coppersmith, K.J. (1994). New empirical relationships among
    magnitude, rupture length, rupture width, rupture area, and surface
    displacement. BSSA 84(4), 974-1002.

Blaser, L., Krüger, F., Ohrnberger, M. & Scherbaum, F. (2010). Scaling
    relations of earthquake source parameter estimates with special focus on
    subduction environment. BSSA 100(6), 2914-2926.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opencoulomb.types.fault import FaultElement


class FaultType(Enum):
    """Fault mechanism type for scaling relations."""

    STRIKE_SLIP = "strike_slip"
    REVERSE = "reverse"
    NORMAL = "normal"
    ALL = "all"


@dataclass(frozen=True, slots=True)
class ScalingResult:
    """Result from a scaling relation computation.

    Attributes
    ----------
    length_km : float
        Surface rupture length (km).
    width_km : float
        Down-dip rupture width (km).
    area_km2 : float
        Rupture area (km²).
    displacement_m : float
        Average displacement (m).
    magnitude : float
        Input moment magnitude.
    fault_type : FaultType
        Fault mechanism used.
    relation : str
        Name of the scaling relation used.
    """

    length_km: float
    width_km: float
    area_km2: float
    displacement_m: float
    magnitude: float
    fault_type: FaultType
    relation: str


# ── Wells & Coppersmith (1994) Coefficients ──────────────────────────
# From Tables 2A (length, width, area vs M) and 2B (displacement vs M).
# Format: (a, b) for log10(Y) = a + b*M
# Keyed by (parameter, fault_type).

_WC94_COEFFS: dict[tuple[str, FaultType], tuple[float, float]] = {
    # Surface rupture length (SRL) vs magnitude: log10(SRL) = a + b*M
    ("length", FaultType.STRIKE_SLIP): (-3.55, 0.74),
    ("length", FaultType.REVERSE): (-2.86, 0.63),
    ("length", FaultType.NORMAL): (-2.01, 0.50),
    ("length", FaultType.ALL): (-3.22, 0.69),
    # Rupture width vs magnitude: log10(RW) = a + b*M
    ("width", FaultType.STRIKE_SLIP): (-0.76, 0.27),
    ("width", FaultType.REVERSE): (-1.61, 0.41),
    ("width", FaultType.NORMAL): (-1.14, 0.35),
    ("width", FaultType.ALL): (-1.01, 0.32),
    # Rupture area vs magnitude: log10(RA) = a + b*M
    ("area", FaultType.STRIKE_SLIP): (-3.42, 0.90),
    ("area", FaultType.REVERSE): (-3.99, 0.98),
    ("area", FaultType.NORMAL): (-2.87, 0.82),
    ("area", FaultType.ALL): (-3.49, 0.91),
    # Average displacement vs magnitude: log10(AD) = a + b*M
    ("displacement", FaultType.STRIKE_SLIP): (-6.32, 0.90),
    ("displacement", FaultType.REVERSE): (-0.74, 0.08),
    ("displacement", FaultType.NORMAL): (-4.45, 0.63),
    ("displacement", FaultType.ALL): (-4.80, 0.69),
}


def wells_coppersmith_1994(
    magnitude: float,
    fault_type: FaultType = FaultType.ALL,
) -> ScalingResult:
    """Compute fault dimensions from Wells & Coppersmith (1994).

    Parameters
    ----------
    magnitude : float
        Moment magnitude (Mw).
    fault_type : FaultType
        Fault mechanism. Default: ALL.

    Returns
    -------
    ScalingResult
        Estimated fault dimensions.
    """
    def _calc(param: str) -> float:
        a, b = _WC94_COEFFS[(param, fault_type)]
        return float(10.0 ** (a + b * magnitude))

    length = _calc("length")
    width = _calc("width")
    area = _calc("area")
    displacement = _calc("displacement")

    return ScalingResult(
        length_km=length,
        width_km=width,
        area_km2=area,
        displacement_m=displacement,
        magnitude=magnitude,
        fault_type=fault_type,
        relation="wells_coppersmith_1994",
    )


# ── Blaser et al. (2010) Coefficients ────────────────────────────────
# From Tables 2-4. Format: (a, b) for log10(Y) = a + b*M
# Note: Blaser uses different groupings. We map to our FaultType enum.

_BLASER10_COEFFS: dict[tuple[str, FaultType], tuple[float, float]] = {
    # Length vs magnitude
    ("length", FaultType.STRIKE_SLIP): (-2.69, 0.64),
    ("length", FaultType.REVERSE): (-2.37, 0.57),
    ("length", FaultType.NORMAL): (-1.91, 0.52),
    ("length", FaultType.ALL): (-2.69, 0.64),
    # Width vs magnitude
    ("width", FaultType.STRIKE_SLIP): (-0.76, 0.27),
    ("width", FaultType.REVERSE): (-1.86, 0.46),
    ("width", FaultType.NORMAL): (-1.20, 0.36),
    ("width", FaultType.ALL): (-1.01, 0.32),
    # Area vs magnitude
    ("area", FaultType.STRIKE_SLIP): (-3.07, 0.86),
    ("area", FaultType.REVERSE): (-3.89, 0.96),
    ("area", FaultType.NORMAL): (-2.87, 0.82),
    ("area", FaultType.ALL): (-3.49, 0.91),
}


def blaser_2010(
    magnitude: float,
    fault_type: FaultType = FaultType.ALL,
) -> ScalingResult:
    """Compute fault dimensions from Blaser et al. (2010).

    Parameters
    ----------
    magnitude : float
        Moment magnitude (Mw).
    fault_type : FaultType
        Fault mechanism. Default: ALL.

    Returns
    -------
    ScalingResult
        Estimated fault dimensions. ``displacement_m`` estimated from
        area and shear modulus (3e10 Pa) via seismic moment.

    Notes
    -----
    Blaser et al. do not provide displacement relations directly.
    Displacement is estimated from: M0 = mu * A * D, where
    mu = 3e10 Pa (typical crustal rigidity).
    """
    def _calc(param: str) -> float:
        a, b = _BLASER10_COEFFS[(param, fault_type)]
        return float(10.0 ** (a + b * magnitude))

    length = _calc("length")
    width = _calc("width")
    area = _calc("area")

    # Estimate displacement from seismic moment:
    # M0 = 10^(1.5*M + 9.05) N·m (Hanks & Kanamori)
    # D = M0 / (mu * A)
    m0 = 10.0 ** (1.5 * magnitude + 9.05)  # N·m
    mu = 3.0e10  # Pa (shear modulus)
    area_m2 = area * 1.0e6  # km² → m²
    displacement = m0 / (mu * area_m2) if area_m2 > 0 else 0.0

    return ScalingResult(
        length_km=length,
        width_km=width,
        area_km2=area,
        displacement_m=displacement,
        magnitude=magnitude,
        fault_type=fault_type,
        relation="blaser_2010",
    )


def magnitude_to_fault(
    magnitude: float,
    center_x: float,
    center_y: float,
    strike: float,
    dip: float,
    rake: float,
    top_depth: float,
    relation: str = "wells_coppersmith_1994",
    fault_type: FaultType = FaultType.ALL,
) -> FaultElement:
    """Create a FaultElement from magnitude using scaling relations.

    Parameters
    ----------
    magnitude : float
        Moment magnitude (Mw).
    center_x, center_y : float
        Fault center coordinates (km, E/N from origin).
    strike : float
        Strike angle (degrees, CW from North).
    dip : float
        Dip angle (degrees, 0-90).
    rake : float
        Rake angle (degrees). Used to determine slip components and FaultType.
    top_depth : float
        Depth to fault top (km).
    relation : str
        Scaling relation: "wells_coppersmith_1994" or "blaser_2010".
    fault_type : FaultType
        Override fault type. Default: ALL.

    Returns
    -------
    FaultElement
        Fault element with scaled dimensions and slip.
    """
    from opencoulomb.types.fault import FaultElement as _FE
    from opencoulomb.types.fault import Kode

    if relation == "wells_coppersmith_1994":
        sr = wells_coppersmith_1994(magnitude, fault_type)
    elif relation == "blaser_2010":
        sr = blaser_2010(magnitude, fault_type)
    else:
        msg = f"Unknown relation: {relation!r}. Use 'wells_coppersmith_1994' or 'blaser_2010'."
        raise ValueError(msg)

    half_len = sr.length_km / 2.0
    strike_rad = math.radians(strike)

    # Surface trace endpoints from center
    dx = half_len * math.sin(strike_rad)
    dy = half_len * math.cos(strike_rad)
    x_start = center_x - dx
    y_start = center_y - dy
    x_fin = center_x + dx
    y_fin = center_y + dy

    # Bottom depth from width and dip
    dip_rad = math.radians(dip)
    bottom_depth = top_depth + sr.width_km * math.sin(dip_rad)

    # Slip components from displacement and rake
    rake_rad = math.radians(rake)
    # KODE 100 convention: slip_1 = right-lateral (negative of cos(rake) for our convention)
    slip_1 = -sr.displacement_m * math.cos(rake_rad)  # right-lateral component
    slip_2 = sr.displacement_m * math.sin(rake_rad)  # reverse component

    return _FE(
        x_start=x_start,
        y_start=y_start,
        x_fin=x_fin,
        y_fin=y_fin,
        kode=Kode.STANDARD,
        slip_1=slip_1,
        slip_2=slip_2,
        dip=dip,
        top_depth=top_depth,
        bottom_depth=bottom_depth,
        label=f"M{magnitude:.1f} scaled ({relation})",
    )
