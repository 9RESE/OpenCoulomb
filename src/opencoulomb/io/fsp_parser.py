"""Parsers for USGS FSP (Finite Source Parameter) and GeoJSON fault formats.

FSP is the SRCMOD standard format for finite fault slip distributions.
GeoJSON is used by USGS for web-based fault visualization.
"""

from __future__ import annotations

import contextlib
import math
import re
from typing import Any

from opencoulomb.types.fault import FaultElement, Kode


def parse_fsp(content: str) -> list[FaultElement]:
    """Parse an FSP (Finite Source Parameter) format string.

    The FSP format contains a header with metadata followed by a table
    of subfault parameters (lat, lon, x, y, z, slip, rake, etc.).

    Parameters
    ----------
    content : str
        FSP file content as a string.

    Returns
    -------
    list[FaultElement]
        Parsed fault elements. Each row becomes one FaultElement.
    """
    elements: list[FaultElement] = []

    # Extract metadata from header
    strike = 0.0
    dip = 90.0

    for line in content.splitlines():
        line = line.strip()
        # Look for strike/dip in header comments
        m = re.search(r"STRIKE\s*=\s*([\d.]+)", line, re.IGNORECASE)
        if m:
            strike = float(m.group(1))
        m = re.search(r"DIP\s*=\s*([\d.]+)", line, re.IGNORECASE)
        if m:
            dip = float(m.group(1))

    # Find data section (after header lines starting with %)
    in_data = False
    idx = 0
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("%"):
            in_data = True
            continue
        if not in_data:
            continue

        parts = line.split()
        if len(parts) < 8:
            continue

        try:
            # Standard FSP columns: lat, lon, x(km), y(km), z(km), slip(m), rake(deg), ...
            x_km = float(parts[2])
            y_km = float(parts[3])
            z_km = float(parts[4])
            slip_m = float(parts[5])
            rake_deg = float(parts[6])

            # Estimate subfault size from spacing (assume 1km default)
            sub_length = 1.0  # km
            if len(parts) > 7:
                with contextlib.suppress(ValueError):
                    sub_length = float(parts[7])

            half_len = sub_length / 2.0
            strike_rad = math.radians(strike)
            dx = half_len * math.sin(strike_rad)
            dy = half_len * math.cos(strike_rad)

            # Slip components from total slip and rake
            rake_rad = math.radians(rake_deg)
            slip_1 = -slip_m * math.cos(rake_rad)  # right-lateral
            slip_2 = slip_m * math.sin(rake_rad)    # reverse

            # Depth range
            dip_rad = math.radians(dip)
            half_width_z = 0.5 * math.sin(dip_rad) if dip > 0 else 0.5
            top = max(0.0, z_km - half_width_z)
            bottom = z_km + half_width_z

            if bottom <= top:
                bottom = top + 0.01  # minimum thickness

            idx += 1
            elements.append(FaultElement(
                x_start=x_km - dx,
                y_start=y_km - dy,
                x_fin=x_km + dx,
                y_fin=y_km + dy,
                kode=Kode.STANDARD,
                slip_1=slip_1,
                slip_2=slip_2,
                dip=dip,
                top_depth=top,
                bottom_depth=bottom,
                label=f"fsp_{idx}",
                element_index=idx,
            ))
        except (ValueError, IndexError):
            continue

    return elements


def parse_geojson_faults(geojson: dict[str, Any]) -> list[FaultElement]:
    """Parse fault elements from a USGS GeoJSON finite fault response.

    Parameters
    ----------
    geojson : dict
        GeoJSON feature collection with fault segment features.

    Returns
    -------
    list[FaultElement]
        Parsed fault elements.
    """
    elements: list[FaultElement] = []

    features = geojson.get("features", [])
    idx = 0
    for feature in features:
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})

        slip = float(props.get("slip", 0.0))
        rake = float(props.get("rake", 0.0))
        strike = float(props.get("strike", 0.0))
        dip = float(props.get("dip", 90.0))
        depth = float(props.get("depth", 10.0))

        # Get coordinates
        coords = geom.get("coordinates", [])
        if not coords or geom.get("type") not in ("Polygon", "LineString", "Point"):
            continue

        if geom["type"] == "Point":
            x, y = coords[0], coords[1]
            half_len = 0.5
        elif geom["type"] == "LineString" and len(coords) >= 2:
            x = (coords[0][0] + coords[-1][0]) / 2
            y = (coords[0][1] + coords[-1][1]) / 2
            dx = coords[-1][0] - coords[0][0]
            dy = coords[-1][1] - coords[0][1]
            half_len = math.sqrt(dx * dx + dy * dy) * 111.0 / 2  # rough deg→km
        else:
            # Polygon: use centroid
            xs = [c[0] for c in coords[0]] if coords else [0]
            ys = [c[1] for c in coords[0]] if coords else [0]
            x = sum(xs) / len(xs)
            y = sum(ys) / len(ys)
            half_len = 1.0

        strike_rad = math.radians(strike)
        dx_km = half_len * math.sin(strike_rad)
        dy_km = half_len * math.cos(strike_rad)

        rake_rad = math.radians(rake)
        slip_1 = -slip * math.cos(rake_rad)
        slip_2 = slip * math.sin(rake_rad)

        dip_rad = math.radians(dip)
        half_w_z = 0.5 * math.sin(dip_rad) if dip > 0 else 0.5
        top = max(0.0, depth - half_w_z)
        bottom = depth + half_w_z
        if bottom <= top:
            bottom = top + 0.01

        idx += 1
        elements.append(FaultElement(
            x_start=x - dx_km,
            y_start=y - dy_km,
            x_fin=x + dx_km,
            y_fin=y + dy_km,
            kode=Kode.STANDARD,
            slip_1=slip_1,
            slip_2=slip_2,
            dip=dip,
            top_depth=top,
            bottom_depth=bottom,
            label=f"geojson_{idx}",
            element_index=idx,
        ))

    return elements
