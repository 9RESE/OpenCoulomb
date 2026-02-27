"""Grid specification data structures."""

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
            raise ValidationError(
                f"finish_x ({self.finish_x}) must exceed start_x ({self.start_x})"
            )
        if self.finish_y <= self.start_y:
            raise ValidationError(
                f"finish_y ({self.finish_y}) must exceed start_y ({self.start_y})"
            )
        if self.x_inc <= 0 or self.y_inc <= 0:
            raise ValidationError(
                f"Grid increments must be positive, got x_inc={self.x_inc}, y_inc={self.y_inc}"
            )
        if self.depth < 0:
            raise ValidationError(f"Grid depth must be non-negative, got {self.depth}")

    @property
    def n_x(self) -> int:
        """Number of grid points in X direction.

        Matches np.arange(start_x, finish_x + x_inc*0.5, x_inc) count.
        """
        return round((self.finish_x - self.start_x) / self.x_inc) + 1

    @property
    def n_y(self) -> int:
        """Number of grid points in Y direction.

        Matches np.arange(start_y, finish_y + y_inc*0.5, y_inc) count.
        """
        return round((self.finish_y - self.start_y) / self.y_inc) + 1

    @property
    def n_points(self) -> int:
        """Total number of grid points."""
        return self.n_x * self.n_y
