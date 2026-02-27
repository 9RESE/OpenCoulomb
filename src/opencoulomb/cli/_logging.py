"""CLI logging configuration."""
from __future__ import annotations

import logging
import sys


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI output."""
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger = logging.getLogger("opencoulomb")
    logger.setLevel(level)
    logger.addHandler(handler)
