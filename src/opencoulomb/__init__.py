"""OpenCoulomb: Open-source Coulomb failure stress computation."""

__version__ = "0.1.0"

from opencoulomb.exceptions import (
    ComputationError,
    ConfigError,
    ConvergenceError,
    FormatError,
    InputError,
    OpenCoulombError,
    OutputError,
    ParseError,
    SingularityError,
    ValidationError,
)

__all__ = [
    "ComputationError",
    "ConfigError",
    "ConvergenceError",
    "FormatError",
    "InputError",
    "OpenCoulombError",
    "OutputError",
    "ParseError",
    "SingularityError",
    "ValidationError",
    "__version__",
]
