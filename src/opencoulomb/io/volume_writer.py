"""Volume output writers for 3D stress/CFS data."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from opencoulomb.types.result import VolumeResult


def write_volume_csv(volume: VolumeResult, path: str | Path) -> None:
    """Write 3D volume result to CSV with depth column.

    Columns: x, y, depth, ux, uy, uz, sxx, syy, szz, syz, sxz, sxy, cfs, shear, normal

    Parameters
    ----------
    volume : VolumeResult
        3D computation result.
    path : str or Path
        Output CSV file path.
    """
    path = Path(path)
    s = volume.stress
    depth = -s.z  # convert back to positive-down

    header = "x,y,depth,ux,uy,uz,sxx,syy,szz,syz,sxz,sxy,cfs,shear,normal"
    data = np.column_stack([
        s.x, s.y, depth,
        s.ux, s.uy, s.uz,
        s.sxx, s.syy, s.szz, s.syz, s.sxz, s.sxy,
        volume.cfs, volume.shear, volume.normal,
    ])
    np.savetxt(path, data, delimiter=",", header=header, comments="", fmt="%.6e")


def write_volume_slices(
    volume: VolumeResult,
    output_dir: str | Path,
    field: str = "cfs",
) -> list[Path]:
    """Write one .dat file per depth layer.

    Each .dat file is a GMT-compatible grid matrix (n_y rows x n_x columns).

    Parameters
    ----------
    volume : VolumeResult
        3D computation result.
    output_dir : str or Path
        Directory for output files.
    field : str
        Field to write: "cfs", "shear", "normal".

    Returns
    -------
    list[Path]
        Paths to written files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    n_z, _n_y, _n_x = volume.volume_shape

    if field == "cfs":
        data_3d = volume.cfs.reshape(volume.volume_shape)
    elif field == "shear":
        data_3d = volume.shear.reshape(volume.volume_shape)
    elif field == "normal":
        data_3d = volume.normal.reshape(volume.volume_shape)
    else:
        msg = f"Unknown field: {field!r}. Use 'cfs', 'shear', or 'normal'."
        raise ValueError(msg)

    paths: list[Path] = []
    for k in range(n_z):
        depth_km = float(volume.depths[k])
        filename = f"{field}_depth_{depth_km:.1f}km.dat"
        filepath = output_dir / filename
        np.savetxt(filepath, data_3d[k], fmt="%.6e")
        paths.append(filepath)

    return paths
