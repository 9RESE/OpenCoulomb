"""GPS displacement data structures."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class GPSStation:
    """A single GPS station with observed displacement.

    Attributes
    ----------
    name : str
        Station name/code.
    x, y : float
        Station position (km from model origin, E/N).
    ux, uy, uz : float
        Observed displacement (m). East, North, Up.
    sigma_ux, sigma_uy, sigma_uz : float
        Displacement uncertainties (m, 1-sigma).
    """

    name: str
    x: float
    y: float
    ux: float
    uy: float
    uz: float
    sigma_ux: float = 0.0
    sigma_uy: float = 0.0
    sigma_uz: float = 0.0


@dataclass(slots=True)
class GPSDataset:
    """Collection of GPS stations with observed displacements.

    Attributes
    ----------
    stations : list[GPSStation]
        GPS station data.
    reference_frame : str
        Reference frame description.
    """

    stations: list[GPSStation] = field(default_factory=list)
    reference_frame: str = ""

    def __len__(self) -> int:
        return len(self.stations)
