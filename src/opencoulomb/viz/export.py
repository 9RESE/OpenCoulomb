"""Figure export utilities."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.figure import Figure

_SUPPORTED_FORMATS = {"png", "pdf", "svg", "eps", "jpg"}


def save_figure(
    fig: Figure,
    filepath: str | Path,
    dpi: int | None = None,
    transparent: bool = False,
) -> Path:
    """Save a figure to disk.

    Parameters
    ----------
    fig : Figure
    filepath : str or Path
    dpi : int or None — defaults to figure's DPI
    transparent : bool — transparent background

    Returns
    -------
    Path — resolved output path

    Raises
    ------
    ValueError — if format is not supported
    """
    filepath = Path(filepath)
    suffix = filepath.suffix.lstrip(".").lower()
    if suffix not in _SUPPORTED_FORMATS:
        msg = f"Unsupported format '{suffix}'. Use one of: {sorted(_SUPPORTED_FORMATS)}"
        raise ValueError(msg)

    kwargs: dict = {"bbox_inches": "tight", "pad_inches": 0.1, "transparent": transparent}
    if dpi is not None:
        kwargs["dpi"] = dpi

    fig.savefig(filepath, **kwargs)
    return filepath.resolve()
