"""Fault element data structures."""

import math
from dataclasses import dataclass
from enum import IntEnum

from opencoulomb.exceptions import ValidationError


class Kode(IntEnum):
    """Fault element type code.

    Determines the physical interpretation of slip columns 5 and 6
    in the .inp file format.
    """

    STANDARD = 100  # col5=right-lateral, col6=reverse
    TENSILE_RL = 200  # col5=tensile, col6=right-lateral
    TENSILE_REV = 300  # col5=tensile, col6=reverse
    POINT_SOURCE = 400  # col5=right-lateral, col6=reverse (point)
    TENSILE_INFL = 500  # col5=tensile, col6=inflation


@dataclass(frozen=True, slots=True)
class FaultElement:
    """A single fault element (source or receiver).

    Attributes
    ----------
    x_start : float
        Starting X coordinate of surface trace (km, East).
    y_start : float
        Starting Y coordinate of surface trace (km, North).
    x_fin : float
        Ending X coordinate of surface trace (km, East).
    y_fin : float
        Ending Y coordinate of surface trace (km, North).
    kode : Kode
        Element type code (100, 200, 300, 400, 500).
    slip_1 : float
        Slip component 1 (m). Interpretation depends on kode:
        KODE 100/400: right-lateral slip (positive = right-lateral)
        KODE 200/300/500: tensile opening (positive = opening)
    slip_2 : float
        Slip component 2 (m). Interpretation depends on kode:
        KODE 100/400: reverse slip (positive = reverse/thrust)
        KODE 200: right-lateral slip
        KODE 300: reverse slip
        KODE 500: inflation
    dip : float
        Dip angle in degrees (0-90, always positive).
    top_depth : float
        Fault top depth in km (>= 0).
    bottom_depth : float
        Fault bottom depth in km (> top_depth).
    label : str
        Optional text label/name for the element. Default: "".
    element_index : int
        1-based element number from .inp file. Default: 0.
    """

    x_start: float
    y_start: float
    x_fin: float
    y_fin: float
    kode: Kode
    slip_1: float
    slip_2: float
    dip: float
    top_depth: float
    bottom_depth: float
    label: str = ""
    element_index: int = 0

    def __post_init__(self) -> None:
        if not (0 <= self.dip <= 90):
            raise ValidationError(f"Dip must be in [0, 90] degrees, got {self.dip}")
        if self.top_depth < 0:
            raise ValidationError(f"Top depth must be >= 0, got {self.top_depth}")
        if self.bottom_depth <= self.top_depth:
            raise ValidationError(
                f"Bottom depth ({self.bottom_depth}) must exceed "
                f"top depth ({self.top_depth})"
            )

    @property
    def is_source(self) -> bool:
        """True if this element has non-zero slip (is a source fault).

        Uses exact float comparison: .inp files specify receiver slip as exactly 0.0.
        """
        return self.slip_1 != 0.0 or self.slip_2 != 0.0

    @property
    def is_receiver(self) -> bool:
        """True if this element has zero slip (is a receiver fault)."""
        return not self.is_source

    @property
    def is_point_source(self) -> bool:
        """True if this is a point source (KODE 400 or 500)."""
        return self.kode in (Kode.POINT_SOURCE, Kode.TENSILE_INFL)

    @property
    def strike_deg(self) -> float:
        """Strike angle in degrees, computed from trace endpoints."""
        dx = self.x_fin - self.x_start
        dy = self.y_fin - self.y_start
        return math.degrees(math.atan2(dx, dy)) % 360.0

    @property
    def rake_deg(self) -> float:
        """Rake angle in degrees, computed from slip components.

        Follows the convention: rake = atan2(reverse_slip, rl_slip).
        For KODE 100: rake = atan2(slip_2, -slip_1)
        (sign flip because Coulomb RL+ but rake measured differently).
        """
        if self.kode == Kode.STANDARD or self.kode == Kode.POINT_SOURCE:
            return math.degrees(math.atan2(self.slip_2, -self.slip_1))
        return 0.0  # Not well-defined for tensile sources

    @property
    def rake_rad(self) -> float:
        """Rake angle in radians."""
        return math.radians(self.rake_deg)

    @property
    def length(self) -> float:
        """Surface trace length in km."""
        dx = self.x_fin - self.x_start
        dy = self.y_fin - self.y_start
        return math.sqrt(dx * dx + dy * dy)

    @property
    def width(self) -> float:
        """Down-dip fault width in km."""
        if self.dip == 0.0:
            return 0.0
        return (self.bottom_depth - self.top_depth) / math.sin(math.radians(self.dip))

    @property
    def center_x(self) -> float:
        """X coordinate of fault center."""
        return (self.x_start + self.x_fin) / 2.0

    @property
    def center_y(self) -> float:
        """Y coordinate of fault center."""
        return (self.y_start + self.y_fin) / 2.0

    @property
    def center_depth(self) -> float:
        """Depth of fault center in km."""
        return (self.top_depth + self.bottom_depth) / 2.0
