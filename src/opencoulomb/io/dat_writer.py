"""GMT-compatible .dat output writers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from opencoulomb.types.fault import FaultElement
    from opencoulomb.types.result import CoulombResult


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

    data = field_map[field].reshape(n_y, n_x)
    np.savetxt(filepath, data, fmt="%12.4e", delimiter="\t")


def write_fault_surface_dat(
    faults: list[FaultElement],
    filepath: str | Path,
) -> None:
    """Write fault surface projections in GMT multi-segment format.

    Each fault is a polygon defined by its four corners, written as
    a GMT multi-segment file with '>' separators.

    Parameters
    ----------
    faults : list of FaultElement
        Fault elements to write.
    filepath : str or Path
        Output file path.
    """
    filepath = Path(filepath)

    with filepath.open("w") as f:
        f.write("# GMT fault surface projections\n")
        f.write("# Format: x(km) y(km)\n")

        for i, fault in enumerate(faults):
            label = fault.label or f"Fault {i + 1}"
            f.write(f"> {label}\n")

            # Fault trace: start to finish (surface projection)
            f.write(f"{fault.x_start:.6f} {fault.y_start:.6f}\n")
            f.write(f"{fault.x_fin:.6f} {fault.y_fin:.6f}\n")
