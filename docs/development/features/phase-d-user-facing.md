# Phase D: User-Facing (Visualization, CLI, Output Writers)

**Status**: Complete
**Date**: 2026-02-27

## Summary

Phase D implements the user-facing components of OpenCoulomb: visualization modules,
output file writers, and CLI commands. These provide the primary interfaces for
users to compute CFS, generate plots, and export results.

## Components

### Visualization (`src/opencoulomb/viz/`)

| Module | Functions | Description |
|--------|-----------|-------------|
| `_base.py` | `create_figure`, `add_colorbar`, `set_axis_labels`, `finalize_figure` | Shared Matplotlib helpers |
| `colormaps.py` | `coulomb_cmap`, `displacement_cmap`, `stress_cmap`, `symmetric_norm` | Colormaps and normalization |
| `styles.py` | `publication_style`, `screen_style` | Context managers for style presets |
| `maps.py` | `plot_cfs_map` | CFS filled contour map with fault overlay |
| `faults.py` | `plot_fault_traces` | Source (red) and receiver (blue) traces |
| `sections.py` | `plot_cross_section` | Cross-section depth profile |
| `displacement.py` | `plot_displacement` | Quiver (horizontal) or contour (vertical) |
| `export.py` | `save_figure` | PNG/PDF/SVG/EPS/JPG export |

### Output Writers (`src/opencoulomb/io/`)

| Module | Functions | Format |
|--------|-----------|--------|
| `cou_writer.py` | `write_dcff_cou`, `write_section_cou` | Coulomb 3.4 `.cou` |
| `csv_writer.py` | `write_csv`, `write_summary` | CSV + text summary |
| `dat_writer.py` | `write_coulomb_dat`, `write_fault_surface_dat` | GMT `.dat` matrix |

### CLI Commands (`src/opencoulomb/cli/`)

| Command | Description |
|---------|-------------|
| `opencoulomb compute <file.inp>` | Compute CFS and write output files |
| `opencoulomb plot <file.inp>` | Generate CFS/displacement/section plots |
| `opencoulomb info <file.inp>` | Display model summary |

## Test Coverage

- 66 new tests across 3 test files
- `test_viz.py`: 30 tests (base, colormaps, styles, maps, faults, sections, displacement, export)
- `test_writers.py`: 17 tests (cou, csv, dat writers)
- `test_cli.py`: 19 tests (group, info, compute, plot commands, exports)
- Overall coverage: 96.96% (783 total tests)

## CLI Usage Examples

```bash
# Compute CFS and export all formats
opencoulomb compute input.inp -o output/

# Compute and export only CSV
opencoulomb compute input.inp -f csv

# Generate CFS map
opencoulomb plot input.inp -t cfs -o cfs_map.png

# Generate displacement plot
opencoulomb plot input.inp -t displacement --dpi 300

# Show model info
opencoulomb info input.inp
```
