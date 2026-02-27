"""Matplotlib style presets for publication and screen."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

import matplotlib as mpl

PUBLICATION_RCPARAMS: dict[str, Any] = {
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "lines.linewidth": 1.0,
    "axes.linewidth": 0.8,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "figure.figsize": (8, 6),
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
}

SCREEN_RCPARAMS: dict[str, Any] = {
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.dpi": 150,
    "lines.linewidth": 1.5,
    "axes.linewidth": 1.0,
    "figure.figsize": (10, 8),
}


@contextmanager
def publication_style() -> Generator[None, None, None]:
    """Context manager applying publication-quality style."""
    with mpl.rc_context(PUBLICATION_RCPARAMS):
        yield


@contextmanager
def screen_style() -> Generator[None, None, None]:
    """Context manager applying screen-optimized style."""
    with mpl.rc_context(SCREEN_RCPARAMS):
        yield
