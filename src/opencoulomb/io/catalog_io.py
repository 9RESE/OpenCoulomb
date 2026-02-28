"""Earthquake catalog file I/O (CSV/JSON)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from opencoulomb.types.catalog import CatalogEvent, EarthquakeCatalog


def read_catalog_csv(path: str | Path) -> EarthquakeCatalog:
    """Read an earthquake catalog from CSV.

    Expected columns: latitude, longitude, depth_km, magnitude, time
    Optional columns: event_id, magnitude_type

    Parameters
    ----------
    path : str or Path
        Path to CSV file.

    Returns
    -------
    EarthquakeCatalog
    """
    path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        events = [
            CatalogEvent(
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                depth_km=float(row["depth_km"]),
                magnitude=float(row["magnitude"]),
                time=row.get("time", ""),
                event_id=row.get("event_id", ""),
                magnitude_type=row.get("magnitude_type", ""),
            )
            for row in reader
        ]

    return EarthquakeCatalog(events=events, source=f"CSV:{path.name}")


def write_catalog_csv(catalog: EarthquakeCatalog, path: str | Path) -> None:
    """Write an earthquake catalog to CSV.

    Parameters
    ----------
    catalog : EarthquakeCatalog
        Catalog to write.
    path : str or Path
        Output CSV file path.
    """
    path = Path(path)
    fieldnames = ["latitude", "longitude", "depth_km", "magnitude", "time", "event_id", "magnitude_type"]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ev in catalog.events:
            writer.writerow({
                "latitude": ev.latitude,
                "longitude": ev.longitude,
                "depth_km": ev.depth_km,
                "magnitude": ev.magnitude,
                "time": ev.time,
                "event_id": ev.event_id,
                "magnitude_type": ev.magnitude_type,
            })


def read_catalog_json(path: str | Path) -> EarthquakeCatalog:
    """Read an earthquake catalog from JSON.

    Parameters
    ----------
    path : str or Path
        Path to JSON file with {"events": [...], "source": "..."}.

    Returns
    -------
    EarthquakeCatalog
    """
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))

    events = [
        CatalogEvent(
            latitude=float(e["latitude"]),
            longitude=float(e["longitude"]),
            depth_km=float(e["depth_km"]),
            magnitude=float(e["magnitude"]),
            time=e.get("time", ""),
            event_id=e.get("event_id", ""),
            magnitude_type=e.get("magnitude_type", ""),
        )
        for e in data.get("events", [])
    ]

    return EarthquakeCatalog(events=events, source=data.get("source", f"JSON:{path.name}"))


def write_catalog_json(catalog: EarthquakeCatalog, path: str | Path) -> None:
    """Write an earthquake catalog to JSON.

    Parameters
    ----------
    catalog : EarthquakeCatalog
        Catalog to write.
    path : str or Path
        Output JSON file path.
    """
    path = Path(path)
    data = {
        "source": catalog.source,
        "events": [
            {
                "latitude": ev.latitude,
                "longitude": ev.longitude,
                "depth_km": ev.depth_km,
                "magnitude": ev.magnitude,
                "time": ev.time,
                "event_id": ev.event_id,
                "magnitude_type": ev.magnitude_type,
            }
            for ev in catalog.events
        ],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
