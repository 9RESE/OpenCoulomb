# Changelog

All notable changes to OpenCoulomb will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
