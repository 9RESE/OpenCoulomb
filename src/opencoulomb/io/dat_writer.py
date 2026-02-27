"""GMT-compatible .dat output writers."""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from opencoulomb.types.fault import FaultElement
    from opencoulomb.types.result import CoulombResult

from opencoulomb.exceptions import OutputError


def write_coulomb_dat(
    result: CoulombResult,
    filepath: str | Path,
    field: str = "cfs",
) -> None:
    """Write a grid field as a GMT-compatible .dat matrix.

    The output is an NY-rows x NX-columns matrix of the selected field,
    suitable for GMT ``grdconvert`` or ``xyz2grd``.

    Parameters
    ----------
    result : CoulombResult
        Computation result.
    filepath : str or Path
        Output file path.
    field : str
        Which field to write: 'cfs', 'shear', 'normal', 'ux', 'uy', 'uz'.
    """
    filepath = Path(filepath)
    n_y, n_x = result.grid_shape

    field_map: dict[str, NDArray[np.float64]] = {
        "cfs": result.cfs,
        "shear": result.shear,
        "normal": result.normal,
        "ux": result.stress.ux,
        "uy": result.stress.uy,
        "uz": result.stress.uz,
    }

    if field not in field_map:
        raise ValueError(
            f"Unknown field '{field}'. Must be one of: {sorted(field_map.keys())}"
        )
    data = field_map[field].reshape(n_y, n_x)
    try:
        np.savetxt(filepath, data, fmt="%12.4e", delimiter="\t")
    except OSError as exc:
        raise OutputError(f"Cannot write {filepath}: {exc}") from exc


def write_fault_surface_dat(
    faults: list[FaultElement],
    filepath: str | Path,
) -> None:
    """Write fault surface projections as closed polygons in GMT multi-segment format.

    Each fault is a closed polygon defined by its four surface-projected
    corners: the two surface trace endpoints and the two downdip-projected
    bottom-edge endpoints. Written as a GMT multi-segment file with '>'
    separators.

    Parameters
    ----------
    faults : list of FaultElement
        Fault elements to write.
    filepath : str or Path
        Output file path.
    """
    filepath = Path(filepath)

    try:
        with filepath.open("w", encoding="utf-8") as f:
            f.write("# GMT fault surface projections\n")
            f.write("# Format: x(km) y(km) - closed polygons\n")

            for i, fault in enumerate(faults):
                label = fault.label or f"Fault {i + 1}"
                f.write(f"> {label}\n")

                corners = _fault_polygon_corners(fault)
                for cx, cy in corners:
                    f.write(f"{cx:.6f} {cy:.6f}\n")
                # Close the polygon by repeating the first corner
                f.write(f"{corners[0][0]:.6f} {corners[0][1]:.6f}\n")
    except OSError as exc:
        raise OutputError(f"Cannot write {filepath}: {exc}") from exc


def _fault_polygon_corners(
    fault: FaultElement,
) -> list[tuple[float, float]]:
    """Compute the 4 surface-projected corners of a fault plane.

    Returns corners in order: trace-start, trace-end, bottom-end, bottom-start
    (counter-clockwise when viewed from above for right-hand-rule dip).

    For vertical faults (dip=90), the polygon collapses to the trace line.
    """
    dip_rad = math.radians(fault.dip)

    # Horizontal offset from trace to bottom edge (surface projection)
    _DIP_THRESHOLD = 1e-6  # degrees
    if fault.dip <= _DIP_THRESHOLD or fault.dip >= 90.0:
        h_offset = 0.0
    else:
        depth_diff = fault.bottom_depth - fault.top_depth
        h_offset = depth_diff / math.tan(dip_rad)

    # Strike direction (unit vector along trace)
    dx = fault.x_fin - fault.x_start
    dy = fault.y_fin - fault.y_start
    trace_len = math.sqrt(dx * dx + dy * dy)

    if trace_len < 1e-12:
        # Point-like fault: return degenerate polygon at center
        cx, cy = fault.center_x, fault.center_y
        return [(cx, cy), (cx, cy), (cx, cy), (cx, cy)]

    # Perpendicular to strike, pointing in dip direction (90° clockwise)
    # Strike = atan2(dx, dy), dip direction = strike + 90° clockwise
    perp_x = dy / trace_len   # perpendicular x component
    perp_y = -dx / trace_len  # perpendicular y component

    # Offset for top-edge to account for non-zero top_depth
    h_offset_top = 0.0 if fault.dip <= _DIP_THRESHOLD or fault.dip >= 90.0 else fault.top_depth / math.tan(dip_rad)

    # 4 corners (surface projection)
    # Top-left (trace start, offset for top_depth)
    x0 = fault.x_start + perp_x * h_offset_top
    y0 = fault.y_start + perp_y * h_offset_top
    # Top-right (trace end, offset for top_depth)
    x1 = fault.x_fin + perp_x * h_offset_top
    y1 = fault.y_fin + perp_y * h_offset_top
    # Bottom-right (trace end + full downdip offset)
    x2 = fault.x_fin + perp_x * (h_offset_top + h_offset)
    y2 = fault.y_fin + perp_y * (h_offset_top + h_offset)
    # Bottom-left (trace start + full downdip offset)
    x3 = fault.x_start + perp_x * (h_offset_top + h_offset)
    y3 = fault.y_start + perp_y * (h_offset_top + h_offset)

    return [(x0, y0), (x1, y1), (x2, y2), (x3, y3)]
