# OpenCoulomb — LLM Development Guide

## Project Overview
OpenCoulomb is a Python 3.10+ replacement for the Coulomb 3.4/4.0 MATLAB seismology package. It computes Coulomb failure stress (CFS) from earthquake fault dislocations using the Okada (1992) elastic half-space model. Version 0.2.0 adds Coulomb 4.0 features: 3D volume computation, scaling relations, slip tapering, USGS finite fault import, earthquake catalog integration, and advanced visualization.

## Quick Start
```bash
pip install -e ".[dev]"            # Editable install with dev deps
pip install -e ".[dev,network]"    # Include ObsPy + requests for network features
opencoulomb compute input.inp      # Compute CFS from .inp file
pytest tests/ -q                   # Run all tests (1271)
ruff check src/                    # Lint
mypy --strict src/opencoulomb/     # Type check
```

## Architecture

### Source Layout
```
src/opencoulomb/
├── types/          # Frozen dataclasses: FaultElement, GridSpec, CoulombModel, VolumeResult, etc.
├── core/           # Pure computation: okada.py, stress.py, coulomb.py, pipeline.py, scaling.py, tapering.py
├── io/             # .inp parser, .cou/.csv/.dat writers, USGS client, catalog/GPS I/O
├── viz/            # Matplotlib: maps, faults, sections, displacement, volume, beachball, GPS
├── cli/            # Click CLI: compute, plot, info, validate, convert, scale, fetch, catalog
├── _constants.py   # Physical constants
└── exceptions.py   # Exception hierarchy (10 classes, all exported from top-level)
```

### Data Flow
```
# 2D grid (v0.1.0)
.inp file → read_inp() → CoulombModel → compute_grid() → CoulombResult → writers/viz

# 3D volume (v0.2.0)
.inp file → read_inp() → CoulombModel → compute_volume(model, VolumeGridSpec) → VolumeResult → volume viz/writers

# USGS fetch (v0.2.0)
event_id → fetch_finite_fault() → CoulombModel → compute_grid() → CoulombResult
```

### Key Types
- `CoulombModel` — Immutable aggregate: title, material, faults, grid, regional stress
- `FaultElement` — Single fault segment with geometry, slip, and Kode classification
- `GridSpec` — 2D observation grid definition (start/finish/increment)
- `VolumeGridSpec` — 3D volume grid (2D bounds + depth range) [v0.2.0]
- `CoulombResult` — CFS, shear, normal stress + displacement arrays on 2D grid (optional `strain`)
- `VolumeResult` — 3D CFS with `cfs_volume()` and `slice_at_depth()` [v0.2.0]
- `StrainResult` — 6 strain tensor components + volumetric strain [v0.2.0]
- `CrossSectionResult` — Stress/displacement on vertical profile
- `CatalogEvent` / `EarthquakeCatalog` — Earthquake events with filtering [v0.2.0]
- `GPSStation` / `GPSDataset` — GPS displacement observations [v0.2.0]
- `ScalingResult` / `FaultType` — Scaling relation results [v0.2.0]
- `TaperSpec` / `TaperProfile` — Slip taper configuration [v0.2.0]

### Key Functions
| Function | Module | Purpose |
|----------|--------|---------|
| `read_inp(path)` | `io.inp_parser` | Parse Coulomb 3.4 .inp file → CoulombModel |
| `compute_grid(model)` | `core.pipeline` | Full CFS computation on observation grid |
| `compute_volume(model, spec)` | `core.pipeline` | 3D CFS computation through depth layers [v0.2.0] |
| `compute_cross_section(model)` | `core.pipeline` | CFS on vertical cross-section |
| `compute_element_cfs(model)` | `core.pipeline` | CFS at receiver fault elements |
| `dc3d(...)` | `core.okada` | Okada DC3D rectangular dislocation |
| `dc3d0(...)` | `core.okada` | Okada DC3D0 point source |
| `gradients_to_strain(...)` | `core.stress` | Displacement gradients → strain tensor [v0.2.0] |
| `wells_coppersmith_1994(mag)` | `core.scaling` | Magnitude → fault dimensions [v0.2.0] |
| `blaser_2010(mag)` | `core.scaling` | Alternative scaling relation [v0.2.0] |
| `subdivide_and_taper(fault, spec)` | `core.tapering` | Fault subdivision + slip taper [v0.2.0] |
| `write_dcff_cou(result, model, path)` | `io.cou_writer` | Coulomb .cou output |
| `write_csv(result, path)` | `io.csv_writer` | CSV stress table |
| `write_coulomb_dat(result, path)` | `io.dat_writer` | GMT-compatible .dat grid |
| `write_volume_csv(volume, path)` | `io.volume_writer` | 3D volume CSV output [v0.2.0] |
| `plot_cfs_map(result, model)` | `viz.maps` | CFS filled contour map |
| `plot_volume_slices(vol, model)` | `viz.volume` | Grid of horizontal depth slices [v0.2.0] |
| `plot_beachball(s, d, r, xy, ax)` | `viz.beachball` | Single focal mechanism [v0.2.0] |
| `plot_gps_comparison(res, mod, gps)` | `viz.gps` | GPS displacement comparison [v0.2.0] |

## Conventions

### Sign Conventions
- **Depth**: Positive downward (km). Okada z-axis: negative below surface.
- **Slip**: slip_1 = left-lateral strike-slip (positive), slip_2 = reverse dip-slip (positive)
- **Stress**: Positive = tension. CFS = shear + friction * normal (positive = failure promoted)
- **Kode**: 100 = standard, 200 = tensile, negative = point source

### Numerical Targets
- Okada DC3D: ≤1e-10 relative error vs Fortran reference (Table 2)
- CFS: ≤1e-6 bar vs Coulomb 3.4
- Performance: 100x100 grid + 10 faults < 10 seconds

### Testing
```bash
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration + pipeline
pytest tests/validation/     # End-to-end CLI
pytest tests/performance/    # Benchmarks
pytest -m reference          # Coulomb 3.4 reference (skipped until values available)
pytest -m network            # Network-dependent tests (requires connectivity)
```
Coverage target: ≥90% overall (currently 91%, 1271 tests)

### Code Style
- ruff (E/W/F/I/B/C4/UP/ARG/SIM/TCH/PTH/S/ASYNC/RUF/PERF)
- mypy strict mode
- Frozen dataclasses for all domain types
- TYPE_CHECKING blocks for type-only imports
- Conventional commits: `feat(core):`, `fix(io):`, `test(validation):`

## File Format Quick Reference

### .inp Input
Fixed-width Coulomb 3.4 format: 2 title lines → params (PR1, E1, FRIC, etc.) → fault table → Grid Parameters → Size Parameters → optional Cross section

### Output Formats
- `.cou` — Coulomb-compatible stress/displacement table with header
- `.csv` — 14-column CSV (x, y, z, ux-uz, sxx-sxy, cfs, shear, normal)
- `.dat` — GMT grid matrix (NY rows × NX columns)
- `_summary.txt` — Human-readable model + results summary
- `_volume.csv` — 15-column 3D CSV with depth column [v0.2.0]

## Optional Dependencies
Network features (`pip install opencoulomb[network]`):
- **ObsPy** >= 1.4 — FDSN client, beachball rendering, QuakeML parsing
- **requests** >= 2.28 — USGS ComCat API client

All network features guard imports with try/except and raise clear `ImportError` messages when missing.

## Documentation
- Architecture: `docs/architecture/` (Arc42)
- User guides: `docs/user/` (Diataxis)
- Research: `docs/claude/research/`
- Design spec: `docs/claude/design/program-specification.md`
