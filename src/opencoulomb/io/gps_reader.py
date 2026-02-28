"""GPS displacement data readers."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from opencoulomb.types.gps import GPSDataset, GPSStation


def read_gps_csv(path: str | Path) -> GPSDataset:
    """Read GPS station data from CSV.

    Expected columns: name, x_km, y_km, ux_m, uy_m, uz_m
    Optional columns: sigma_ux, sigma_uy, sigma_uz

    Parameters
    ----------
    path : str or Path
        Path to CSV file.

    Returns
    -------
    GPSDataset
    """
    path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        stations = [
            GPSStation(
                name=row["name"],
                x=float(row["x_km"]),
                y=float(row["y_km"]),
                ux=float(row["ux_m"]),
                uy=float(row["uy_m"]),
                uz=float(row["uz_m"]),
                sigma_ux=float(row.get("sigma_ux", 0.0)),
                sigma_uy=float(row.get("sigma_uy", 0.0)),
                sigma_uz=float(row.get("sigma_uz", 0.0)),
            )
            for row in reader
        ]

    return GPSDataset(stations=stations)


def read_gps_json(path: str | Path) -> GPSDataset:
    """Read GPS station data from JSON.

    Parameters
    ----------
    path : str or Path
        Path to JSON file.

    Returns
    -------
    GPSDataset
    """
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))

    stations = [
        GPSStation(
            name=s["name"],
            x=float(s["x_km"]),
            y=float(s["y_km"]),
            ux=float(s["ux_m"]),
            uy=float(s["uy_m"]),
            uz=float(s["uz_m"]),
            sigma_ux=float(s.get("sigma_ux", 0.0)),
            sigma_uy=float(s.get("sigma_uy", 0.0)),
            sigma_uz=float(s.get("sigma_uz", 0.0)),
        )
        for s in data.get("stations", [])
    ]

    return GPSDataset(
        stations=stations,
        reference_frame=data.get("reference_frame", ""),
    )
