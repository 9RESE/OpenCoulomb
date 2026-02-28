"""ISC and USGS earthquake catalog clients via ObsPy FDSN.

Requires ObsPy (install via ``pip install opencoulomb[network]``).
"""

from __future__ import annotations

from typing import Any

from opencoulomb.types.catalog import CatalogEvent, EarthquakeCatalog


def _get_obspy_client(source: str = "ISC") -> Any:
    """Create an ObsPy FDSN client with a clear error message."""
    try:
        from obspy.clients.fdsn import Client  # type: ignore[import-not-found]
        return Client(source)
    except ImportError:
        msg = (
            "ObsPy is required for earthquake catalog access. "
            "Install it with: pip install opencoulomb[network]"
        )
        raise ImportError(msg) from None


def query_isc(
    start_time: str,
    end_time: str,
    min_magnitude: float = 0.0,
    min_latitude: float | None = None,
    max_latitude: float | None = None,
    min_longitude: float | None = None,
    max_longitude: float | None = None,
    max_depth: float | None = None,
) -> EarthquakeCatalog:
    """Query the ISC earthquake catalog via FDSN.

    Parameters
    ----------
    start_time, end_time : str
        Date range (ISO 8601, e.g. "2024-01-01").
    min_magnitude : float
        Minimum magnitude filter.
    min_latitude, max_latitude, min_longitude, max_longitude : float or None
        Geographic bounding box.
    max_depth : float or None
        Maximum depth (km).

    Returns
    -------
    EarthquakeCatalog
        Events from the ISC catalog.
    """
    from obspy import UTCDateTime  # type: ignore[import-not-found]

    client = _get_obspy_client("ISC")

    kwargs: dict[str, Any] = {
        "starttime": UTCDateTime(start_time),
        "endtime": UTCDateTime(end_time),
        "minmagnitude": min_magnitude,
    }
    if min_latitude is not None:
        kwargs["minlatitude"] = min_latitude
    if max_latitude is not None:
        kwargs["maxlatitude"] = max_latitude
    if min_longitude is not None:
        kwargs["minlongitude"] = min_longitude
    if max_longitude is not None:
        kwargs["maxlongitude"] = max_longitude
    if max_depth is not None:
        kwargs["maxdepth"] = max_depth

    cat = client.get_events(**kwargs)
    return catalog_from_obspy(cat, source="ISC")


def query_usgs_catalog(
    start_time: str,
    end_time: str,
    min_magnitude: float = 0.0,
    min_latitude: float | None = None,
    max_latitude: float | None = None,
    min_longitude: float | None = None,
    max_longitude: float | None = None,
) -> EarthquakeCatalog:
    """Query the USGS earthquake catalog via FDSN.

    Same parameters as ``query_isc`` but uses the USGS FDSN service.
    """
    from obspy import UTCDateTime

    client = _get_obspy_client("USGS")

    kwargs: dict[str, Any] = {
        "starttime": UTCDateTime(start_time),
        "endtime": UTCDateTime(end_time),
        "minmagnitude": min_magnitude,
    }
    if min_latitude is not None:
        kwargs["minlatitude"] = min_latitude
    if max_latitude is not None:
        kwargs["maxlatitude"] = max_latitude
    if min_longitude is not None:
        kwargs["minlongitude"] = min_longitude
    if max_longitude is not None:
        kwargs["maxlongitude"] = max_longitude

    cat = client.get_events(**kwargs)
    return catalog_from_obspy(cat, source="USGS")


def catalog_from_obspy(obspy_catalog: Any, source: str = "") -> EarthquakeCatalog:
    """Convert an ObsPy Catalog to EarthquakeCatalog.

    Parameters
    ----------
    obspy_catalog : obspy.core.event.Catalog
        ObsPy catalog object.
    source : str
        Source label.

    Returns
    -------
    EarthquakeCatalog
    """
    events: list[CatalogEvent] = []
    for event in obspy_catalog:
        origin = event.preferred_origin() or (event.origins[0] if event.origins else None)
        mag = event.preferred_magnitude() or (event.magnitudes[0] if event.magnitudes else None)

        if origin is None:
            continue

        lat = float(origin.latitude) if origin.latitude is not None else 0.0
        lon = float(origin.longitude) if origin.longitude is not None else 0.0
        depth = float(origin.depth / 1000.0) if origin.depth is not None else 0.0  # m → km
        time_str = str(origin.time) if origin.time else ""
        magnitude = float(mag.mag) if mag is not None else 0.0
        mag_type = str(mag.magnitude_type) if mag is not None else ""

        # Extract event ID from resource_id
        eid = ""
        if hasattr(event, "resource_id") and event.resource_id:
            eid = str(event.resource_id).split("/")[-1].split("?")[0]

        events.append(CatalogEvent(
            latitude=lat,
            longitude=lon,
            depth_km=depth,
            magnitude=magnitude,
            time=time_str,
            event_id=eid,
            magnitude_type=mag_type,
        ))

    return EarthquakeCatalog(events=events, source=source)
