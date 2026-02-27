"""Stress field data structures."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PrincipalStress:
    """One principal stress axis with orientation and magnitude.

    Attributes
    ----------
    direction : float
        Azimuth in degrees (clockwise from North, 0-360).
    dip : float
        Dip from horizontal in degrees (-90 to 90).
    intensity : float
        Stress magnitude at surface (bar). Compression positive.
    gradient : float
        Stress increase with depth (bar/km).
    """
    direction: float
    dip: float
    intensity: float
    gradient: float


@dataclass(frozen=True, slots=True)
class RegionalStress:
    """Regional background stress field (3 principal stresses).

    Convention: s1 >= s2 >= s3 (most compressive to least compressive).
    - Normal faulting regime: s1 vertical
    - Thrust regime: s3 vertical
    - Strike-slip regime: s2 vertical
    """
    s1: PrincipalStress
    s2: PrincipalStress
    s3: PrincipalStress


@dataclass(frozen=True, slots=True)
class StressTensorComponents:
    """6-component stress tensor at a single point (Voigt notation).

    All values in bar. Geographic coordinates: x=East, y=North, z=Up.
    """
    sxx: float
    syy: float
    szz: float
    syz: float
    sxz: float
    sxy: float
