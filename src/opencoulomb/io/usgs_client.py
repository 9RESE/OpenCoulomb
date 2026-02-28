"""USGS ComCat API client for finite fault products.

Provides access to USGS earthquake event data and finite fault models.
Requires the ``requests`` package (install via ``pip install opencoulomb[network]``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opencoulomb.types.model import CoulombModel

_COMCAT_BASE = "https://earthquake.usgs.gov/fdsnws/event/1"
_DETAIL_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/{event_id}.geojson"


def _get_requests() -> Any:
    """Import requests with a clear error message."""
    try:
        import requests  # type: ignore[import-untyped]
        return requests
    except ImportError:
        msg = (
            "The 'requests' package is required for USGS data access. "
            "Install it with: pip install opencoulomb[network]"
        )
        raise ImportError(msg) from None


@dataclass(frozen=True, slots=True)
class USGSEvent:
    """Summary of a USGS earthquake event.

    Attributes
    ----------
    event_id : str
        USGS event ID (e.g. "us7000abcd").
    title : str
        Event title (e.g. "M 7.1 - 18 km SW of ...").
    magnitude : float
        Event magnitude.
    latitude, longitude : float
        Epicenter coordinates (degrees).
    depth_km : float
        Hypocenter depth (km).
    time : str
        Origin time (ISO 8601 string).
    """

    event_id: str
    title: str
    magnitude: float
    latitude: float
    longitude: float
    depth_km: float
    time: str


def search_events(
    min_magnitude: float = 5.0,
    start_time: str | None = None,
    end_time: str | None = None,
    min_latitude: float | None = None,
    max_latitude: float | None = None,
    min_longitude: float | None = None,
    max_longitude: float | None = None,
    limit: int = 20,
) -> list[USGSEvent]:
    """Search USGS ComCat for earthquake events.

    Parameters
    ----------
    min_magnitude : float
        Minimum magnitude filter.
    start_time, end_time : str or None
        ISO 8601 date strings (e.g. "2024-01-01").
    min_latitude, max_latitude, min_longitude, max_longitude : float or None
        Geographic bounding box (degrees).
    limit : int
        Maximum number of events to return.

    Returns
    -------
    list[USGSEvent]
        Matching events, sorted by time (newest first).
    """
    requests = _get_requests()

    params: dict[str, Any] = {
        "format": "geojson",
        "minmagnitude": min_magnitude,
        "limit": limit,
        "orderby": "time",
    }
    if start_time:
        params["starttime"] = start_time
    if end_time:
        params["endtime"] = end_time
    if min_latitude is not None:
        params["minlatitude"] = min_latitude
    if max_latitude is not None:
        params["maxlatitude"] = max_latitude
    if min_longitude is not None:
        params["minlongitude"] = min_longitude
    if max_longitude is not None:
        params["maxlongitude"] = max_longitude

    url = f"{_COMCAT_BASE}/query"
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    events: list[USGSEvent] = []
    for feature in data.get("features", []):
        props = feature["properties"]
        coords = feature["geometry"]["coordinates"]
        events.append(USGSEvent(
            event_id=feature["id"],
            title=props.get("title", ""),
            magnitude=float(props.get("mag", 0)),
            longitude=float(coords[0]),
            latitude=float(coords[1]),
            depth_km=float(coords[2]),
            time=props.get("time", ""),
        ))

    return events


def fetch_coulomb_inp(event_id: str, output_path: str | Path) -> Path:
    """Download the Coulomb .inp file for a USGS finite fault product.

    Parameters
    ----------
    event_id : str
        USGS event ID.
    output_path : str or Path
        Where to save the .inp file.

    Returns
    -------
    Path
        Path to the saved file.
    """
    requests = _get_requests()
    output_path = Path(output_path)

    # Get event detail to find finite-fault product URL
    detail_url = _DETAIL_URL.format(event_id=event_id)
    resp = requests.get(detail_url, timeout=30)
    resp.raise_for_status()
    detail = resp.json()

    products = detail.get("properties", {}).get("products", {})
    ff_products = products.get("finite-fault", [])
    if not ff_products:
        msg = f"No finite-fault product found for event {event_id}"
        raise ValueError(msg)

    # Find coulomb.inp in product contents
    contents = ff_products[0].get("contents", {})
    inp_key = None
    for key in contents:
        if key.endswith("coulomb.inp") or key.endswith(".inp"):
            inp_key = key
            break

    if inp_key is None:
        msg = f"No .inp file found in finite-fault product for event {event_id}"
        raise ValueError(msg)

    inp_url = contents[inp_key]["url"]
    inp_resp = requests.get(inp_url, timeout=60)
    inp_resp.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(inp_resp.text, encoding="utf-8")

    return output_path


def fetch_finite_fault(event_id: str) -> tuple[USGSEvent, CoulombModel]:
    """Fetch a USGS finite fault model and parse it to CoulombModel.

    Downloads the .inp file, parses it, and returns both event
    metadata and the parsed model.

    Parameters
    ----------
    event_id : str
        USGS event ID.

    Returns
    -------
    tuple[USGSEvent, CoulombModel]
        Event metadata and parsed model.
    """
    import tempfile

    requests = _get_requests()

    # Get event detail
    detail_url = _DETAIL_URL.format(event_id=event_id)
    resp = requests.get(detail_url, timeout=30)
    resp.raise_for_status()
    detail = resp.json()

    props = detail["properties"]
    coords = detail["geometry"]["coordinates"]
    event = USGSEvent(
        event_id=event_id,
        title=props.get("title", ""),
        magnitude=float(props.get("mag", 0)),
        longitude=float(coords[0]),
        latitude=float(coords[1]),
        depth_km=float(coords[2]),
        time=str(props.get("time", "")),
    )

    # Download and parse .inp
    with tempfile.NamedTemporaryFile(suffix=".inp", mode="w", delete=False) as f:
        tmp_path = Path(f.name)

    fetch_coulomb_inp(event_id, tmp_path)

    from opencoulomb.io.inp_parser import read_inp
    model = read_inp(tmp_path)

    tmp_path.unlink(missing_ok=True)

    return event, model
