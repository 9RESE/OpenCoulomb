"""GPS displacement comparison plotting."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from opencoulomb.types.gps import GPSDataset
    from opencoulomb.types.model import CoulombModel
    from opencoulomb.types.result import CoulombResult


def plot_gps_comparison(
    result: CoulombResult,
    _model: CoulombModel,
    gps: GPSDataset,
    ax: Axes | None = None,
    component: str = "horizontal",
    observed_color: str = "black",
    modeled_color: str = "red",
    scale: float | None = None,
    show_residuals: bool = False,
) -> tuple[Figure, Axes]:
    """Plot observed vs modeled GPS displacements.

    Interpolates modeled displacement at GPS station locations and
    plots both as arrow vectors.

    Parameters
    ----------
    result : CoulombResult
        CFS computation result with displacement field.
    _model : CoulombModel
        Input model (reserved for future fault overlay).
    gps : GPSDataset
        Observed GPS displacements.
    ax : Axes or None
        Existing axes. Creates new figure if None.
    component : str
        "horizontal" for East+North arrows, "vertical" for vertical bars.
    observed_color, modeled_color : str
        Arrow colors.
    scale : float or None
        Quiver scale factor. None = auto.
    show_residuals : bool
        Also plot residual vectors (observed - modeled).

    Returns
    -------
    tuple[Figure, Axes]
    """
    from scipy.interpolate import RegularGridInterpolator  # type: ignore[import-untyped]

    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    else:
        fig = ax.figure  # type: ignore[assignment]

    n_y, n_x = result.grid_shape
    x_1d = result.stress.x.reshape(n_y, n_x)[0, :]
    y_1d = result.stress.y.reshape(n_y, n_x)[:, 0]

    ux_2d, uy_2d, uz_2d = result.displacement_grid()

    interp_ux = RegularGridInterpolator((y_1d, x_1d), ux_2d, bounds_error=False, fill_value=0.0)
    interp_uy = RegularGridInterpolator((y_1d, x_1d), uy_2d, bounds_error=False, fill_value=0.0)
    interp_uz = RegularGridInterpolator((y_1d, x_1d), uz_2d, bounds_error=False, fill_value=0.0)

    # Get station positions and observed displacements
    sx = np.array([s.x for s in gps.stations])
    sy = np.array([s.y for s in gps.stations])
    obs_ux = np.array([s.ux for s in gps.stations])
    obs_uy = np.array([s.uy for s in gps.stations])
    obs_uz = np.array([s.uz for s in gps.stations])

    # Interpolate modeled displacements
    pts = np.column_stack([sy, sx])
    mod_ux = interp_ux(pts)
    mod_uy = interp_uy(pts)
    mod_uz = interp_uz(pts)

    if component == "horizontal":
        # Observed arrows (black)
        ax.quiver(sx, sy, obs_ux, obs_uy, color=observed_color, scale=scale,
                  label="Observed", zorder=5)
        # Modeled arrows (red)
        ax.quiver(sx, sy, mod_ux, mod_uy, color=modeled_color, scale=scale,
                  label="Modeled", zorder=4)

        if show_residuals:
            res_ux = obs_ux - mod_ux
            res_uy = obs_uy - mod_uy
            ax.quiver(sx, sy, res_ux, res_uy, color="green", scale=scale,
                      label="Residual", zorder=3, alpha=0.7)

        ax.set_xlabel("East (km)")
        ax.set_ylabel("North (km)")
        ax.set_title("GPS Displacement Comparison (Horizontal)")
    else:
        # Vertical: bar chart
        x_pos = np.arange(len(gps.stations))
        width = 0.35
        ax.bar(x_pos - width / 2, obs_uz * 1000, width, color=observed_color, label="Observed")
        ax.bar(x_pos + width / 2, mod_uz * 1000, width, color=modeled_color, label="Modeled")
        ax.set_xticks(x_pos)
        ax.set_xticklabels([s.name for s in gps.stations], rotation=45, ha="right")
        ax.set_ylabel("Vertical Displacement (mm)")
        ax.set_title("GPS Displacement Comparison (Vertical)")

    ax.legend()
    ax.set_aspect("equal" if component == "horizontal" else "auto")

    return fig, ax


def compute_misfit(
    result: CoulombResult,
    _model: CoulombModel,
    gps: GPSDataset,
) -> dict[str, Any]:
    """Compute misfit statistics between modeled and observed GPS.

    Parameters
    ----------
    result : CoulombResult
        CFS computation result.
    model : CoulombModel
        Input model.
    gps : GPSDataset
        Observed GPS data.

    Returns
    -------
    dict
        Keys: rms_horizontal, rms_vertical, rms_3d, per_station_residuals,
        reduction_of_variance.
    """
    from scipy.interpolate import RegularGridInterpolator

    n_y, n_x = result.grid_shape
    x_1d = result.stress.x.reshape(n_y, n_x)[0, :]
    y_1d = result.stress.y.reshape(n_y, n_x)[:, 0]
    ux_2d, uy_2d, uz_2d = result.displacement_grid()

    interp_ux = RegularGridInterpolator((y_1d, x_1d), ux_2d, bounds_error=False, fill_value=0.0)
    interp_uy = RegularGridInterpolator((y_1d, x_1d), uy_2d, bounds_error=False, fill_value=0.0)
    interp_uz = RegularGridInterpolator((y_1d, x_1d), uz_2d, bounds_error=False, fill_value=0.0)

    residuals = []
    for s in gps.stations:
        pt = np.array([[s.y, s.x]])
        res_ux = s.ux - float(interp_ux(pt))
        res_uy = s.uy - float(interp_uy(pt))
        res_uz = s.uz - float(interp_uz(pt))
        residuals.append({
            "name": s.name, "res_ux": res_ux, "res_uy": res_uy, "res_uz": res_uz,
            "res_h": float(np.sqrt(res_ux**2 + res_uy**2)),
        })

    h_res = np.array([r["res_h"] for r in residuals])
    z_res = np.array([r["res_uz"] for r in residuals])
    all_res = np.array([[r["res_ux"], r["res_uy"], r["res_uz"]] for r in residuals])

    obs_h = np.array([np.sqrt(s.ux**2 + s.uy**2) for s in gps.stations])
    obs_var = float(np.sum(obs_h**2))
    res_var = float(np.sum(h_res**2))
    rov = 1.0 - res_var / obs_var if obs_var > 0 else 0.0

    return {
        "rms_horizontal": float(np.sqrt(np.mean(h_res**2))),
        "rms_vertical": float(np.sqrt(np.mean(z_res**2))),
        "rms_3d": float(np.sqrt(np.mean(np.sum(all_res**2, axis=1)))),
        "per_station_residuals": residuals,
        "reduction_of_variance": rov,
    }
