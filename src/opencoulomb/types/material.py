"""Material property data structures."""

from dataclasses import dataclass

from opencoulomb._constants import (
    DEFAULT_DEPTH_KM,
    DEFAULT_FRICTION,
    DEFAULT_POISSON,
    DEFAULT_YOUNG_BAR,
)
from opencoulomb.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class MaterialProperties:
    """Elastic material properties for the half-space.

    Attributes
    ----------
    poisson : float
        Poisson's ratio (dimensionless, 0 < nu < 0.5). Default: 0.25.
    young : float
        Young's modulus in bar (1 bar = 0.1 MPa). Default: 8.0e5 (80 GPa).
    friction : float
        Effective friction coefficient mu' (dimensionless, >= 0). Default: 0.4.
    depth : float
        Default calculation depth in km (>= 0). Default: 10.0.
    """
    poisson: float = DEFAULT_POISSON
    young: float = DEFAULT_YOUNG_BAR
    friction: float = DEFAULT_FRICTION
    depth: float = DEFAULT_DEPTH_KM

    def __post_init__(self) -> None:
        if not (0.0 < self.poisson < 0.5):
            raise ValidationError(
                f"Poisson's ratio must be in (0, 0.5), got {self.poisson}")
        if self.young <= 0:
            raise ValidationError(
                f"Young's modulus must be positive, got {self.young}")
        if self.friction < 0:
            raise ValidationError(
                f"Friction must be non-negative, got {self.friction}")
        if self.depth < 0:
            raise ValidationError(
                f"Depth must be non-negative, got {self.depth}")

    @property
    def alpha(self) -> float:
        """Okada medium constant: (lambda+mu)/(lambda+2*mu) = 1/(2*(1-nu))."""
        return 1.0 / (2.0 * (1.0 - self.poisson))

    @property
    def shear_modulus(self) -> float:
        """Shear modulus mu in bar: E / (2*(1+nu))."""
        return self.young / (2.0 * (1.0 + self.poisson))

    @property
    def lame_lambda(self) -> float:
        """Lame's first parameter lambda in bar."""
        nu = self.poisson
        return self.young * nu / ((1 + nu) * (1 - 2 * nu))
