# OpenCoulomb — LLM Development Guide

## Project Overview
OpenCoulomb is a Python 3.10+ replacement for the Coulomb 3.4 MATLAB seismology package. It computes Coulomb failure stress (CFS) from earthquake fault dislocations using the Okada (1992) elastic half-space model.

## Quick Start
```bash
pip install -e ".[dev]"        # Editable install with dev deps
opencoulomb compute input.inp  # Compute CFS from .inp file
pytest tests/ -q               # Run all tests (~800)
ruff check src/                # Lint
```

## Architecture

### Source Layout
```
src/opencoulomb/
├── types/          # Frozen dataclasses: FaultElement, GridSpec, CoulombModel, etc.
├── core/           # Pure computation: okada.py, stress.py, coulomb.py, pipeline.py
├── io/             # .inp parser, .cou/.csv/.dat writers
├── viz/            # Matplotlib: maps, faults, sections, displacement, export
├── cli/            # Click CLI: compute, plot, info, validate, convert
├── _constants.py   # Physical constants
└── exceptions.py   # ValidationError, ParseError, ComputationError
```

### Data Flow
```
.inp file → read_inp() → CoulombModel → compute_grid() → CoulombResult → writers/viz
```

### Key Types
- `CoulombModel` — Immutable aggregate: title, material, faults, grid, regional stress
- `FaultElement` — Single fault segment with geometry, slip, and Kode classification
- `GridSpec` — Observation grid definition (start/finish/increment)
- `CoulombResult` — CFS, shear, normal stress + displacement arrays on grid
- `CrossSectionResult` — Stress/displacement on vertical profile

### Key Functions
| Function | Module | Purpose |
|----------|--------|---------|
| `read_inp(path)` | `io.inp_parser` | Parse Coulomb 3.4 .inp file → CoulombModel |
| `compute_grid(model)` | `core.pipeline` | Full CFS computation on observation grid |
| `compute_cross_section(model)` | `core.pipeline` | CFS on vertical cross-section |
| `compute_element_cfs(model)` | `core.pipeline` | CFS at receiver fault elements |
| `dc3d(...)` | `core.okada` | Okada DC3D rectangular dislocation |
| `dc3d0(...)` | `core.okada` | Okada DC3D0 point source |
| `write_dcff_cou(result, model, path)` | `io.cou_writer` | Coulomb .cou output |
| `write_csv(result, path)` | `io.csv_writer` | CSV stress table |
| `write_coulomb_dat(result, path)` | `io.dat_writer` | GMT-compatible .dat grid |
| `plot_cfs_map(result, model)` | `viz.maps` | CFS filled contour map |

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
```
Coverage target: ≥90% overall (currently 95.77%)

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

## Documentation
- Architecture: `docs/architecture/` (Arc42)
- User guides: `docs/user/` (Diataxis)
- Research: `docs/claude/research/`
- Design spec: `docs/claude/design/program-specification.md`
