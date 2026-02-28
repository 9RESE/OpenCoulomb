# Changelog

All notable changes to OpenCoulomb will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-27

### Added
- **Scaling relations** — Wells & Coppersmith (1994) and Blaser et al. (2010) magnitude-to-fault dimension scaling
  - New CLI command: `opencoulomb scale 7.0 --type strike_slip --relation wells_coppersmith_1994`
  - `magnitude_to_fault()` creates `FaultElement` from magnitude + geometry
- **Strain output** — Full symmetric strain tensor computation alongside stress
  - New `StrainResult` type with 6 components + volumetric (dilatation)
  - `compute_grid(..., compute_strain=True)` populates strain fields
  - Extracted `gradients_to_strain()` from `gradients_to_stress()` (no behavioral change)
- **Depth-loop volume grid** — 3D Coulomb stress computation through depth layers
  - `VolumeGridSpec` type for 3D grid specification (x, y, depth ranges)
  - `VolumeResult` type with `cfs_volume()` and `slice_at_depth()` methods
  - `compute_volume(model, volume_spec)` pipeline function
  - CLI: `opencoulomb compute input.inp --volume --depth-min 0 --depth-max 20 --depth-inc 2`
  - Writers: `write_volume_csv()` and `write_volume_slices()` for 3D output
- **Slip tapering** — Realistic fault slip distributions with edge tapering
  - Cosine, linear, and elliptical taper profiles via `TaperSpec`
  - Fault subdivision into N×M sub-patches via `subdivide_fault()`
  - CLI: `opencoulomb compute input.inp --taper cosine --taper-nx 5 --taper-ny 3`
- **USGS finite fault import** — Fetch earthquake models from USGS ComCat API
  - `search_events()`, `fetch_coulomb_inp()`, `fetch_finite_fault()` in `io.usgs_client`
  - FSP (SRCMOD) and GeoJSON fault format parsers in `io.fsp_parser`
  - CLI: `opencoulomb fetch us7000abcd` and `opencoulomb fetch --search --min-mag 7.0`
- **ISC earthquake catalog** — Query earthquake catalogs via ObsPy FDSN client
  - `CatalogEvent` and `EarthquakeCatalog` types with filtering (magnitude, depth, region)
  - `query_isc()` and `query_usgs_catalog()` in `io.isc_client`
  - Catalog CSV/JSON read/write in `io.catalog_io`
  - CLI: `opencoulomb catalog --start 2024-01-01 --end 2024-12-31 --min-mag 4.0`
- **Beachball focal mechanisms** — Plot focal mechanisms on CFS maps
  - `plot_beachball()` using ObsPy `beach()` with pure-matplotlib fallback
  - `plot_beachballs_on_map()` with CFS-colored receivers and catalog overlay
  - CLI: `opencoulomb plot input.inp --type beachball --catalog catalog.csv`
- **GPS displacement comparison** — Compare modeled vs observed GPS vectors
  - `GPSStation` and `GPSDataset` types, CSV/JSON readers
  - `plot_gps_comparison()` with observed/modeled quiver arrows
  - `compute_misfit()` returns RMS horizontal/vertical/3D and reduction of variance
  - CLI: `opencoulomb plot input.inp --gps stations.csv`
- **3D volume visualization** — Multi-panel and animated depth visualizations
  - `plot_volume_slices()` — grid of horizontal CFS slices
  - `plot_volume_cross_sections()` — vertical E-W cross-sections
  - `plot_volume_3d()` — 3D scatter plot above threshold
  - `export_volume_gif()` — animated GIF through depth layers
  - `plot_catalog_on_volume()` — earthquake overlay on depth slices
  - CLI: `opencoulomb plot input.inp --type volume-slices`, `volume-3d`, `volume-gif`
- **Optional network dependencies** — `pip install opencoulomb[network]` adds ObsPy and requests

### Changed
- Version bumped from 0.1.0 to 0.2.0
- `compute_grid()` now accepts optional `compute_strain` and `taper` parameters (backward-compatible defaults)
- `CoulombResult` has optional `strain` field (defaults to `None`)
- `symmetric_norm()` in `viz.colormaps` accepts both `NDArray` and `float` arguments

## [0.1.0] - 2026-02-27

### Added
- **Core computation engine**
  - Okada DC3D/DC3D0 vectorized NumPy implementation
  - Stress tensor computation (Hooke's law, tensor rotation, Bond matrix)
  - Coulomb failure stress (CFS) resolution on specified receiver faults
  - Optimally oriented planes (OOPs) computation
  - Cross-section stress/displacement computation
  - Grid-based pipeline with multi-source superposition
- **Data model** — Frozen dataclasses for all domain types (FaultElement, GridSpec, CoulombModel, etc.)
- **.inp parser** — State machine parser for Coulomb 3.4 fixed-width format (23 files tested)
- **Output writers** — Coulomb .cou, CSV, GMT .dat, text summary formats
- **Visualization** — CFS contour maps, fault traces, displacement quivers, cross-section plots, publication/screen styles
- **CLI** — Click-based commands: `compute`, `plot`, `info`, `validate`, `convert`
- **Validation suite** — 811 tests across 6 levels (unit, integration, Okada reference, CFS comparison, end-to-end, performance)
- **Documentation** — Arc42 architecture (12 files, 3 ADRs), Diataxis user docs (12 files), LLM guide
- **Packaging** — PyPI-ready with hatchling, sdist/wheel builds verified

### Fixed
- **Core engine**
  - DC3D0 `np.errstate` scope bug — computation lines outside warning suppression block
  - Degenerate fault guard — skip zero-length faults instead of producing NaN
  - Poisson/Young validation in `gradients_to_stress` — reject unphysical values early
  - Okada (1992) convention reference comments in coordinate transforms
  - Documented Bond transformation formula in `rotate_stress_tensor` docstring
  - Exported all 6 coordinate functions from `opencoulomb.core`
- **Data model**
  - `GridSpec.n_x`/`n_y` — changed `math.floor()` to `round()` to match `np.arange` behavior
  - `GridSpec` depth validation — reject negative depth values
  - `CrossSectionSpec` — reject zero-length profiles at construction time
  - Improved error messages with actual values in validation failures
  - Clarified `is_source` docstring on exact float comparison for .inp compatibility
- **I/O**
  - `read_inp` — catches `OSError`/`PermissionError` and wraps as `InputError`
  - All writers — wrap `OSError` as `OutputError` for consistent error handling
  - Writers — sanitize multiline titles in `.cou` headers (newline → ` | `)
  - Writers — use `encoding="utf-8"` consistently, replace em dashes with ASCII dashes
  - `.inp` parser — removed dead `STRESS` state and `_current_line` method
  - Parser — handler dispatch built once in `__init__` instead of per-line
  - `.dat` writer — added dip threshold guard for dip=0 faults, field validation
- **Visualization / CLI**
  - `plot` command — close Matplotlib figure after saving to prevent memory leak
  - Cross-section plot — added field validation before dict access
  - CLI `_logging` — prevent duplicate handler attachment on repeated calls
  - `compute` and `info` commands — wrap parse/compute exceptions as `ClickException`
  - `save_figure` — create parent directories if they don't exist
  - Tests — added `matplotlib.use("Agg")` and `plt.close("all")` fixture globally
