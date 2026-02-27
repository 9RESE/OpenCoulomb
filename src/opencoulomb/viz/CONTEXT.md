# viz — Context for LLMs

## Purpose
Matplotlib-based visualization layer for OpenCoulomb results. Provides ready-made
plot functions for CFS maps, cross-sections, displacement fields, and fault traces,
plus publication-quality style presets and Coulomb-style colormaps.

## Key Files
| File | Purpose |
|------|---------|
| `_base.py` | Low-level figure helpers: `create_figure`, `finalize_figure`, `add_colorbar`, `set_axis_labels` |
| `colormaps.py` | Custom colormaps and normalization: `coulomb_cmap`, `stress_cmap`, `displacement_cmap`, `symmetric_norm` |
| `maps.py` | `plot_cfs_map` — filled contour map of CFS on the horizontal grid |
| `sections.py` | `plot_cross_section` — 2D CFS/stress image on a vertical profile |
| `displacement.py` | `plot_displacement` — quiver/vector displacement map |
| `faults.py` | `plot_fault_traces` — overlay source/receiver fault surface traces |
| `styles.py` | `publication_style`, `screen_style` context managers; `PUBLICATION_RCPARAMS`, `SCREEN_RCPARAMS` |
| `export.py` | `save_figure` — save to PNG/PDF/SVG with DPI/bbox control |

## Key Functions

### Plot functions (all return `(Figure, Axes)`)
- **`plot_cfs_map(result, model, ax=None, vmax=None, contour_levels=20, show_faults=True)`**
  Filled contour map of CFS using `coulomb_cmap` and `symmetric_norm`. Overlays
  fault traces when `show_faults=True`.
- **`plot_cross_section(section, model, ax=None, vmax=None)`**
  `imshow`-based 2D view of a `CrossSectionResult` (distance × depth).
- **`plot_displacement(result, model, ax=None, component="uz", scale=None)`**
  Displacement field as a color image or quiver plot.
- **`plot_fault_traces(model, ax, show_receivers=True)`**
  Draws fault surface traces; sources solid, receivers dashed.

### Style utilities
- **`publication_style()`** / **`screen_style()`** — context managers applying `rcParams`
  suitable for journal figures or on-screen display respectively
- **`symmetric_norm(data, vmax=None)`** — `TwoSlopeNorm` centred at zero for diverging colormaps

### Export
- **`save_figure(fig, path, dpi=300, bbox_inches="tight")`** — wraps `fig.savefig`

## Dependencies
- **Depends on**: `matplotlib` (required), `numpy`, `opencoulomb.types` (CoulombResult, CoulombModel, CrossSectionResult)
- **Does not depend on**: `core` or `io`
- **Used by**: `opencoulomb.cli` (plot command)

## Conventions
- All plot functions accept an optional `ax` — pass one to embed in a larger figure,
  omit to get a new standalone figure
- `coulomb_cmap` is a blue-white-red diverging colormap matching the classic Coulomb 3.4 palette
- Color limits default to `symmetric_norm` around the data maximum unless `vmax` is supplied
- Fault traces are always plotted in geographic km coordinates (same as GridSpec)
- Style context managers use `matplotlib.rcParams` and restore the previous state on exit
