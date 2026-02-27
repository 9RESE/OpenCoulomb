"""Coulomb .cou output file writers.

Writes stress computation results in the dcff.cou format
compatible with Coulomb 3.4.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opencoulomb.types.model import CoulombModel
    from opencoulomb.types.result import CoulombResult
    from opencoulomb.types.section import CrossSectionResult


def write_dcff_cou(
    result: CoulombResult,
    model: CoulombModel,
    filepath: str | Path,
) -> None:
    """Write grid CFS results in dcff.cou format.

    Format: x, y, CFS, shear, normal, sxx, syy, szz, syz, sxz, sxy

    Parameters
    ----------
    result : CoulombResult
        Computation result with stress and CFS arrays.
    model : CoulombModel
        Input model (for header metadata).
    filepath : str or Path
        Output file path.
    """
    filepath = Path(filepath)
    stress = result.stress
    n = stress.n_points

    with filepath.open("w") as f:
        # Header
        f.write(f"  Coulomb Stress Change (bar) — {model.title}\n")
        f.write(
            f"  friction = {model.material.friction:.2f}  "
            f"Poisson = {model.material.poisson:.2f}  "
            f"Young = {model.material.young:.0f} bar\n"
        )
        f.write(
            "        X(km)        Y(km)    CFS(bar)  "
            "Shear(bar) Normal(bar)   "
            "Sxx(bar)   Syy(bar)   Szz(bar)   "
            "Syz(bar)   Sxz(bar)   Sxy(bar)\n"
        )

        for i in range(n):
            f.write(
                f"  {stress.x[i]:11.4f} {stress.y[i]:11.4f}"
                f" {result.cfs[i]:11.4e}"
                f" {result.shear[i]:11.4e}"
                f" {result.normal[i]:11.4e}"
                f" {stress.sxx[i]:11.4e}"
                f" {stress.syy[i]:11.4e}"
                f" {stress.szz[i]:11.4e}"
                f" {stress.syz[i]:11.4e}"
                f" {stress.sxz[i]:11.4e}"
                f" {stress.sxy[i]:11.4e}\n"
            )


def write_section_cou(
    section: CrossSectionResult,
    model: CoulombModel,
    filepath: str | Path,
) -> None:
    """Write cross-section results in dcff_section.cou format.

    Format: distance, depth, CFS, shear, normal, sxx..sxy

    Parameters
    ----------
    section : CrossSectionResult
        Cross-section computation result.
    model : CoulombModel
        Input model (for header metadata).
    filepath : str or Path
        Output file path.
    """
    filepath = Path(filepath)
    spec = section.spec
    n_vert, n_horiz = section.cfs.shape

    with filepath.open("w") as f:
        f.write(f"  Cross Section Stress (bar) — {model.title}\n")
        f.write(
            f"  Profile: ({spec.start_x:.1f},{spec.start_y:.1f}) to "
            f"({spec.finish_x:.1f},{spec.finish_y:.1f})\n"
        )
        f.write(
            "    Dist(km)   Depth(km)    CFS(bar)  "
            "Shear(bar) Normal(bar)   "
            "Sxx(bar)   Syy(bar)   Szz(bar)   "
            "Syz(bar)   Sxz(bar)   Sxy(bar)\n"
        )

        for iv in range(n_vert):
            for ih in range(n_horiz):
                f.write(
                    f"  {section.distance[ih]:11.4f}"
                    f" {section.depth[iv]:11.4f}"
                    f" {section.cfs[iv, ih]:11.4e}"
                    f" {section.shear[iv, ih]:11.4e}"
                    f" {section.normal[iv, ih]:11.4e}"
                    f" {section.sxx[iv, ih]:11.4e}"
                    f" {section.syy[iv, ih]:11.4e}"
                    f" {section.szz[iv, ih]:11.4e}"
                    f" {section.syz[iv, ih]:11.4e}"
                    f" {section.sxz[iv, ih]:11.4e}"
                    f" {section.sxy[iv, ih]:11.4e}\n"
                )
