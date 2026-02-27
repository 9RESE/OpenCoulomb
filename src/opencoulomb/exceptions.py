"""Exception hierarchy for OpenCoulomb."""

from __future__ import annotations


class OpenCoulombError(Exception):
    """Base exception for all OpenCoulomb errors."""


# ---------------------------------------------------------------------------
# Input errors
# ---------------------------------------------------------------------------


class InputError(OpenCoulombError):
    """Raised when there is a problem with the input data or file."""


class ParseError(InputError):
    """Raised when an .inp file cannot be parsed.

    Attributes:
        filename: Path to the file being parsed, if known.
        line_number: Line number where the parse error occurred, if known.
    """

    def __init__(
        self,
        message: str,
        filename: str | None = None,
        line_number: int | None = None,
    ) -> None:
        self.filename = filename
        self.line_number = line_number
        location = ""
        if filename:
            location += f" in '{filename}'"
        if line_number is not None:
            location += f" at line {line_number}"
        super().__init__(f"{message}{location}")


class ValidationError(InputError):
    """Raised when parsed input data fails semantic validation.

    For example: negative fault length, invalid rake angle, grid with
    zero extent, etc.
    """


# ---------------------------------------------------------------------------
# Computation errors
# ---------------------------------------------------------------------------


class ComputationError(OpenCoulombError):
    """Raised when the stress computation fails."""


class SingularityError(ComputationError):
    """Raised when a mathematical singularity is encountered during computation.

    Typically occurs when an observation point coincides exactly with a
    fault edge or tip (Okada singularity).
    """


class ConvergenceError(ComputationError):
    """Raised when an iterative computation fails to converge."""


# ---------------------------------------------------------------------------
# Output errors
# ---------------------------------------------------------------------------


class OutputError(OpenCoulombError):
    """Raised when writing output files fails."""


class FormatError(OutputError):
    """Raised when an unsupported or invalid output format is requested."""


# ---------------------------------------------------------------------------
# Configuration errors
# ---------------------------------------------------------------------------


class ConfigError(OpenCoulombError):
    """Raised when the runtime configuration is invalid or missing required values."""
