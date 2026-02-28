"""Earthquake catalog data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class CatalogEvent:
    """A single earthquake event from a seismicity catalog.

    Attributes
    ----------
    latitude, longitude : float
        Epicenter (degrees).
    depth_km : float
        Hypocenter depth (km, positive down).
    magnitude : float
        Event magnitude.
    time : str
        Origin time (ISO 8601 string).
    event_id : str
        Catalog event identifier.
    magnitude_type : str
        Magnitude type (Mw, mb, ML, etc.).
    """

    latitude: float
    longitude: float
    depth_km: float
    magnitude: float
    time: str
    event_id: str = ""
    magnitude_type: str = ""


@dataclass(slots=True)
class EarthquakeCatalog:
    """Collection of earthquake events with filtering capabilities.

    Attributes
    ----------
    events : list[CatalogEvent]
        Earthquake events.
    source : str
        Data source (e.g. "ISC", "USGS").
    """

    events: list[CatalogEvent] = field(default_factory=list)
    source: str = ""

    def __len__(self) -> int:
        return len(self.events)

    def filter_by_magnitude(
        self, min_mag: float = -999.0, max_mag: float = 999.0,
    ) -> EarthquakeCatalog:
        """Return a new catalog filtered by magnitude range."""
        return EarthquakeCatalog(
            events=[e for e in self.events if min_mag <= e.magnitude <= max_mag],
            source=self.source,
        )

    def filter_by_depth(
        self, min_depth: float = 0.0, max_depth: float = 999.0,
    ) -> EarthquakeCatalog:
        """Return a new catalog filtered by depth range (km)."""
        return EarthquakeCatalog(
            events=[e for e in self.events if min_depth <= e.depth_km <= max_depth],
            source=self.source,
        )

    def filter_by_region(
        self,
        min_lat: float = -90.0,
        max_lat: float = 90.0,
        min_lon: float = -180.0,
        max_lon: float = 180.0,
    ) -> EarthquakeCatalog:
        """Return a new catalog filtered by geographic bounding box."""
        return EarthquakeCatalog(
            events=[
                e for e in self.events
                if min_lat <= e.latitude <= max_lat and min_lon <= e.longitude <= max_lon
            ],
            source=self.source,
        )

    def to_arrays(self) -> dict[str, NDArray[np.float64]]:
        """Convert catalog to dict of NumPy arrays for plotting.

        Returns dict with keys: latitude, longitude, depth_km, magnitude.
        """
        import numpy as np
        if not self.events:
            return {
                "latitude": np.array([], dtype=np.float64),
                "longitude": np.array([], dtype=np.float64),
                "depth_km": np.array([], dtype=np.float64),
                "magnitude": np.array([], dtype=np.float64),
            }
        return {
            "latitude": np.array([e.latitude for e in self.events], dtype=np.float64),
            "longitude": np.array([e.longitude for e in self.events], dtype=np.float64),
            "depth_km": np.array([e.depth_km for e in self.events], dtype=np.float64),
            "magnitude": np.array([e.magnitude for e in self.events], dtype=np.float64),
        }
