"""Fault trace visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from opencoulomb.types.model import CoulombModel


def plot_fault_traces(
    model: CoulombModel,
    ax: Axes | None = None,
    show_labels: bool = True,
) -> tuple[Figure, Axes]:
    """Plot source and receiver fault surface traces.

    Sources: solid red lines. Receivers: dashed blue lines.
    """
    from opencoulomb.viz._base import create_figure, set_axis_labels

    if ax is None:
        fig, ax = create_figure()
    else:
        fig = ax.get_figure()

    for fault in model.source_faults:
        ax.plot(
            [fault.x_start, fault.x_fin],
            [fault.y_start, fault.y_fin],
            "r-",
            linewidth=2.0,
            solid_capstyle="round",
        )
        if show_labels and fault.label:
            ax.annotate(
                fault.label,
                xy=(
                    (fault.x_start + fault.x_fin) / 2,
                    (fault.y_start + fault.y_fin) / 2,
                ),
                fontsize=7,
                ha="center",
                va="bottom",
                color="red",
            )

    for fault in model.receiver_faults:
        ax.plot(
            [fault.x_start, fault.x_fin],
            [fault.y_start, fault.y_fin],
            "b--",
            linewidth=1.5,
        )
        if show_labels and fault.label:
            ax.annotate(
                fault.label,
                xy=(
                    (fault.x_start + fault.x_fin) / 2,
                    (fault.y_start + fault.y_fin) / 2,
                ),
                fontsize=7,
                ha="center",
                va="bottom",
                color="blue",
            )

    set_axis_labels(ax)
    ax.set_aspect("equal")
    return fig, ax
