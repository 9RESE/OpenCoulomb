"""CSV and text summary output writers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opencoulomb.types.model import CoulombModel
    from opencoulomb.types.result import CoulombResult

_GRID_COLUMNS = [
    "x_km", "y_km",
    "cfs_bar", "shear_bar", "normal_bar",
    "sxx_bar", "syy_bar", "szz_bar", "syz_bar", "sxz_bar", "sxy_bar",
    "ux_m", "uy_m", "uz_m",
]


def write_csv(
    result: CoulombResult,
    filepath: str | Path,
) -> None:
    """Write grid results as CSV with header row.

    Parameters
    ----------
    result : CoulombResult
        Computation result.
    filepath : str or Path
        Output file path.
    """
    filepath = Path(filepath)
    stress = result.stress
    n = stress.n_points

    with filepath.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(_GRID_COLUMNS)

        for i in range(n):
            writer.writerow([
                f"{stress.x[i]:.6f}",
                f"{stress.y[i]:.6f}",
                f"{result.cfs[i]:.6e}",
                f"{result.shear[i]:.6e}",
                f"{result.normal[i]:.6e}",
                f"{stress.sxx[i]:.6e}",
                f"{stress.syy[i]:.6e}",
                f"{stress.szz[i]:.6e}",
                f"{stress.syz[i]:.6e}",
                f"{stress.sxz[i]:.6e}",
                f"{stress.sxy[i]:.6e}",
                f"{stress.ux[i]:.6e}",
                f"{stress.uy[i]:.6e}",
                f"{stress.uz[i]:.6e}",
            ])


def write_summary(
    result: CoulombResult,
    model: CoulombModel,
    filepath: str | Path,
) -> None:
    """Write a human-readable text summary.

    Parameters
    ----------
    result : CoulombResult
        Computation result.
    model : CoulombModel
        Input model.
    filepath : str or Path
        Output file path.
    """
    import numpy as np

    filepath = Path(filepath)
    grid = model.grid
    mat = model.material
    n_y, n_x = result.grid_shape

    with filepath.open("w") as f:
        f.write("OpenCoulomb Computation Summary\n")
        f.write("=" * 40 + "\n\n")

        f.write(f"Model: {model.title}\n\n")

        f.write("Material Properties\n")
        f.write(f"  Poisson's ratio:  {mat.poisson:.4f}\n")
        f.write(f"  Young's modulus:  {mat.young:.0f} bar\n")
        f.write(f"  Friction coeff:   {mat.friction:.4f}\n\n")

        f.write("Grid\n")
        f.write(f"  X range: {grid.start_x:.2f} to {grid.finish_x:.2f} km\n")
        f.write(f"  Y range: {grid.start_y:.2f} to {grid.finish_y:.2f} km\n")
        f.write(f"  Spacing: {grid.x_inc:.4f} x {grid.y_inc:.4f} km\n")
        f.write(f"  Points:  {n_x} x {n_y} = {n_x * n_y}\n")
        f.write(f"  Depth:   {grid.depth:.2f} km\n\n")

        f.write("Faults\n")
        f.write(f"  Source faults:   {model.n_sources}\n")
        f.write(f"  Receiver faults: {model.n_receivers}\n\n")

        f.write("CFS Results\n")
        f.write(f"  Receiver: strike={result.receiver_strike:.1f}, "
                f"dip={result.receiver_dip:.1f}, "
                f"rake={result.receiver_rake:.1f}\n")
        f.write(f"  Max CFS:  {float(np.max(result.cfs)):.4e} bar\n")
        f.write(f"  Min CFS:  {float(np.min(result.cfs)):.4e} bar\n")
        f.write(f"  Mean CFS: {float(np.mean(result.cfs)):.4e} bar\n\n")

        f.write("Displacement\n")
        f.write(f"  Max |u|:  {float(np.max(np.sqrt(result.stress.ux**2 + result.stress.uy**2 + result.stress.uz**2))):.4e} m\n")
