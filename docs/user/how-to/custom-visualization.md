# How to Customize Visualizations

This guide covers changing colormaps, adjusting figure layout, exporting to
different formats, and building publication-quality figures via the Python API.

## Change the colormap

The default CFS colormap is a diverging red-white-blue scheme. Use any
Matplotlib colormap via the API:

```python
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from opencoulomb.io import read_inp
from opencoulomb.core import compute_grid
from opencoulomb.viz import save_figure

model = read_inp("model.inp")
result = compute_grid(model)

# Access the CFS array directly and plot manually
fig, ax = plt.subplots(figsize=(8, 7))
cfs = result.cfs          # shape (ny, nx), values in bar
X = result.grid_x         # shape (ny, nx)
Y = result.grid_y         # shape (ny, nx)

vmax = 0.5
norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
im = ax.pcolormesh(X, Y, cfs, cmap="seismic", norm=norm, shading="auto")
fig.colorbar(im, ax=ax, label="CFS (bar)")
ax.set_aspect("equal")
ax.set_xlabel("Distance (km)")
ax.set_ylabel("Distance (km)")

save_figure(fig, "custom_colormap.png", dpi=300)
```

## Use a custom color scale

Saturate extreme values to highlight subtle features near zero:

```python
import numpy as np

# Clip at ±0.2 bar so the color scale is not dominated by stress concentrations
vmax = 0.2
cfs_clipped = np.clip(cfs, -vmax, vmax)

im = ax.pcolormesh(X, Y, cfs_clipped, cmap="RdBu_r",
                   vmin=-vmax, vmax=vmax, shading="auto")
```

## Add fault traces manually

```python
for fault in model.source_faults:
    ax.plot(
        [fault.start_x, fault.finish_x],
        [fault.start_y, fault.finish_y],
        "k-", linewidth=2, label="Source fault"
    )

for fault in model.receiver_faults:
    ax.plot(
        [fault.start_x, fault.finish_x],
        [fault.start_y, fault.finish_y],
        "k--", linewidth=1.5, label="Receiver fault"
    )

# Deduplicate legend entries
handles, labels = ax.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax.legend(by_label.values(), by_label.keys(), loc="upper right")
```

## Multi-panel figure

Compare CFS, shear, and normal stress side by side:

```python
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

fig, axes = plt.subplots(1, 3, figsize=(18, 6), constrained_layout=True)
fields = [
    (result.cfs,    "CFS (bar)"),
    (result.shear,  "Shear stress (bar)"),
    (result.normal, "Normal stress (bar)"),
]

vmax = 0.5
norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

for ax, (field, title) in zip(axes, fields):
    im = ax.pcolormesh(result.grid_x, result.grid_y, field,
                       cmap="RdBu_r", norm=norm, shading="auto")
    fig.colorbar(im, ax=ax, shrink=0.8, label="bar")
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.set_xlabel("km")

axes[0].set_ylabel("km")
save_figure(fig, "stress_components.pdf", dpi=300)
```

## Export to different formats

`save_figure` infers format from the file extension:

```python
from opencoulomb.viz import plot_cfs_map, save_figure

fig, ax = plot_cfs_map(result, model, vmax=0.5)

save_figure(fig, "map.png", dpi=300)    # PNG — good for web/reports
save_figure(fig, "map.pdf", dpi=300)    # PDF — vector, ideal for LaTeX
save_figure(fig, "map.svg", dpi=300)    # SVG — editable in Inkscape
save_figure(fig, "map.eps", dpi=300)    # EPS — some journals require this
```

## Publication-quality figure

Full example with Matplotlib rcParams for journal submission:

```python
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from opencoulomb.io import read_inp
from opencoulomb.core import compute_grid
from opencoulomb.viz import save_figure

# Apply journal style
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.linewidth": 0.8,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "figure.dpi": 300,
})

model = read_inp("northridge.inp")
result = compute_grid(model)

fig, ax = plt.subplots(figsize=(3.5, 3.0))  # single-column width

vmax = 2.0
norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)
im = ax.pcolormesh(result.grid_x, result.grid_y, result.cfs,
                   cmap="RdBu_r", norm=norm, shading="auto")

cbar = fig.colorbar(im, ax=ax, pad=0.02)
cbar.set_label("DCFS (bar)", fontsize=9)

# Fault traces
for f in model.source_faults:
    ax.plot([f.start_x, f.finish_x], [f.start_y, f.finish_y],
            "k-", lw=1.5)

ax.set_xlabel("Distance (km)")
ax.set_ylabel("Distance (km)")
ax.set_aspect("equal")

fig.savefig("figure_1.pdf", bbox_inches="tight")
```

## Batch export with consistent scale

When comparing multiple models, fix `vmax` to the same value across all plots:

```python
from pathlib import Path
from opencoulomb.io import read_inp
from opencoulomb.core import compute_grid
from opencoulomb.viz import plot_cfs_map, save_figure

VMAX = 1.0  # bar — same for all figures

for inp in sorted(Path("models").glob("*.inp")):
    model = read_inp(inp)
    result = compute_grid(model)
    fig, _ = plot_cfs_map(result, model, vmax=VMAX)
    save_figure(fig, f"plots/{inp.stem}_cfs.png", dpi=200)
```

## CLI equivalent options

The `opencoulomb plot` command exposes the most common options:

```bash
# Fixed scale, PDF output, 300 DPI (default)
opencoulomb plot model.inp --vmax 0.5 -o figure.pdf

# Draft quality PNG
opencoulomb plot model.inp --dpi 100 -o draft.png

# No fault traces
opencoulomb plot model.inp --no-faults -o clean.png
```

See the [CLI reference](../reference/cli.md#plot) for all options.
