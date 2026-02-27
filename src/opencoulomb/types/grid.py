"""Grid specification data structures."""

import math
from dataclasses import dataclass

from opencoulomb.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class GridSpec:
    """Computation grid specification.

    Attributes
    ----------
    start_x : float
        Western boundary (km, East from origin).
    start_y : float
        Southern boundary (km, North from origin).
    finish_x : float
        Eastern boundary (km).
    finish_y : float
        Northern boundary (km).
    x_inc : float
        Grid spacing in X/East direction (km, > 0).
    y_inc : float
        Grid spacing in Y/North direction (km, > 0).
    depth : float
        Calculation depth (km, >= 0). Overrides material.depth when set.
    """
    start_x: float
    start_y: float
    finish_x: float
    finish_y: float
    x_inc: float
    y_inc: float
    depth: float = 10.0

    def __post_init__(self) -> None:
        if self.finish_x <= self.start_x:
            raise ValidationError("finish_x must exceed start_x")
        if self.finish_y <= self.start_y:
            raise ValidationError("finish_y must exceed start_y")
        if self.x_inc <= 0 or self.y_inc <= 0:
            raise ValidationError("Grid increments must be positive")

    @property
    def n_x(self) -> int:
        """Number of grid points in X direction."""
        return math.floor((self.finish_x - self.start_x) / self.x_inc) + 1

    @property
    def n_y(self) -> int:
        """Number of grid points in Y direction."""
        return math.floor((self.finish_y - self.start_y) / self.y_inc) + 1

    @property
    def n_points(self) -> int:
        """Total number of grid points."""
        return self.n_x * self.n_y
