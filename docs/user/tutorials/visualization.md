# Tutorial: Creating Visualizations

This tutorial walks through creating CFS maps, displacement plots, and vertical
cross-sections using the `opencoulomb plot` command and the Python API.

## Prerequisites

Make sure OpenCoulomb is installed with visualization support:

```bash
pip install "opencoulomb[viz]"
```

Use the `strike_slip.inp` file from the [quickstart tutorial](quickstart.md).

## CFS map (default)

The simplest plot is a horizontal CFS map at the grid depth:

```bash
opencoulomb plot strike_slip.inp -o cfs_map.png
```

The output is a 300 DPI PNG with:
- Color-filled CFS field (diverging colormap, red=positive, blue=negative)
- Black lines marking source fault surface traces
- Dashed lines marking receiver fault traces

## Displacement map

Plot the three components of surface displacement (ux, uy, uz):

```bash
opencoulomb plot strike_slip.inp -t displacement -o displacement.png
```

This produces a three-panel figure showing east, north, and vertical
displacement in metres.

## Vertical cross-section

If your `.inp` file defines a `Cross section default` block (see
[file format reference](../reference/file-formats.md)), you can plot a vertical
profile:

```bash
opencoulomb plot thrust.inp -t section -o section.png
```

The cross-section shows CFS in a vertical plane between the two endpoints
defined in the input file.

## Adjusting the color scale

By default the colormap is symmetric around zero with limits set to the 98th
percentile of the absolute CFS values. Override with `--vmax`:

```bash
# Fix color scale at ±1 bar
opencoulomb plot strike_slip.inp --vmax 1.0 -o cfs_fixed.png
```

Use a small value to saturate large outliers and reveal subtle features:

```bash
opencoulomb plot strike_slip.inp --vmax 0.2 -o cfs_detail.png
```

## Resolution and file format

Control output DPI (default 300):

```bash
opencoulomb plot strike_slip.inp --dpi 150 -o cfs_draft.png   # fast draft
opencoulomb plot strike_slip.inp --dpi 600 -o cfs_print.png   # print quality
```

The output format is inferred from the file extension. Supported formats:

```bash
opencoulomb plot strike_slip.inp -o figure.png   # PNG (raster)
opencoulomb plot strike_slip.inp -o figure.pdf   # PDF (vector)
opencoulomb plot strike_slip.inp -o figure.svg   # SVG (vector)
```

## Selecting a receiver fault

When a model has multiple receiver faults, the first one (index 0) is used by
default. Select a different receiver with `--receiver`:

```bash
# CFS resolved onto the second receiver fault (index 1)
opencoulomb plot strike_slip.inp --receiver 1 -o cfs_receiver1.png
```

## Hiding fault traces

Remove fault trace overlays for a clean CFS field:

```bash
opencoulomb plot strike_slip.inp --no-faults -o cfs_clean.png
```

## Python API for custom plots

For full control, use the Python API directly:

```python
from opencoulomb.io import read_inp
from opencoulomb.core import compute_grid
from opencoulomb.viz import plot_cfs_map, save_figure
import matplotlib.pyplot as plt

# Load and compute
model = read_inp("strike_slip.inp")
result = compute_grid(model)

# Plot with custom settings
fig, ax = plot_cfs_map(result, model, vmax=0.5, show_faults=True)

# Further customization
ax.set_title("Strike-Slip CFS — 10 km depth", fontsize=14)
ax.set_xlabel("Distance (km)")
ax.set_ylabel("Distance (km)")

# Add a custom annotation
ax.annotate("Max stress", xy=(25, 0), fontsize=10, color="darkred")

save_figure(fig, "custom_cfs.png", dpi=300)
plt.close(fig)
```

## Displacement plot via API

```python
from opencoulomb.viz import plot_displacement

fig, axes = plot_displacement(result, model, show_faults=True)
# axes is a list of three Axes: [ax_ux, ax_uy, ax_uz]
save_figure(fig, "displacement.pdf", dpi=300)
```

## Cross-section via API

```python
from opencoulomb.core import compute_cross_section
from opencoulomb.viz import plot_cross_section

section = compute_cross_section(model)
fig, ax = plot_cross_section(section, vmax=0.5)
save_figure(fig, "section.png", dpi=300)
```

## Next steps

- [Custom visualization how-to](../how-to/custom-visualization.md) — colormaps,
  styles, batch export
- [CLI reference — plot command](../reference/cli.md#plot)
- [API reference — viz module](../reference/api.md#visualization)
