# Arc42 § 5 — Building Blocks

## 5.1 Top-Level Decomposition

```
src/opencoulomb/
├── types/          Domain model — immutable data structures
├── core/           Computation engine — pure functions
├── io/             I/O — parser and writers
├── viz/            Visualisation — Matplotlib figures
├── cli/            CLI — Click command group
├── exceptions.py   Exception hierarchy
└── _constants.py   Physical constants (μ, λ, etc.)
```

## 5.2 `types/` — Domain Model

Frozen dataclasses representing the scientific domain. No business logic; no I/O.

| Module | Key Type | Description |
|--------|----------|-------------|
| `model.py` | `CoulombModel` | Aggregate root: owns all faults, grid, material, optional regional stress and cross-section |
| `fault.py` | `FaultElement`, `Kode` | Single fault patch with geometry (strike, dip, rake, slip, depth) and kode (1=source, 3=receiver) |
| `grid.py` | `GridSpec` | Observation grid bounds, spacing, and depth |
| `material.py` | `MaterialProperties` | Young's modulus, Poisson's ratio, friction coefficient, Lamé parameters |
| `stress.py` | `RegionalStress`, `PrincipalStress` | Background stress field specification |
| `result.py` | `CoulombResult`, `ElementResult`, `StressResult` | Computation output arrays |
| `section.py` | `CrossSectionSpec`, `CrossSectionResult` | Vertical profile definition and results |

### CoulombModel dependencies

```
CoulombModel
├── MaterialProperties
├── list[FaultElement]  (sources: 0..n_fixed-1, receivers: n_fixed..end)
├── GridSpec
├── RegionalStress?
└── CrossSectionSpec?
```

## 5.3 `core/` — Computation Engine

Pure functions; no I/O; all inputs/outputs are NumPy arrays or domain types.

| Module | Responsibility |
|--------|---------------|
| `okada.py` | Vectorized Okada (1992) DC3D (finite rectangular fault) and DC3D0 (point source). Computes 3-component displacement and 6-component displacement gradient arrays over an observation grid. |
| `coordinates.py` | Geographic ↔ fault-local coordinate transforms; fault geometry helpers (`compute_fault_geometry`, `fault_to_geo_displacement`). |
| `stress.py` | `gradients_to_stress()` — displacement gradients → stress tensor via Hooke's law. `rotate_stress_tensor()` — rotate stress into receiver fault coordinates. |
| `coulomb.py` | `compute_cfs_on_receiver()` — resolve total stress tensor onto receiver fault orientation to produce ΔCFS. |
| `oops.py` | Optimal Orientation of Planes — find the fault orientation that maximises CFS given a regional stress field. |
| `pipeline.py` | Orchestrates the full computation: grid generation → per-source Okada → stress accumulation → CFS resolution. Entry point: `compute_grid(model)`. |

### Computation dependency graph (core)

```
pipeline.compute_grid()
  ├── coordinates.compute_fault_geometry()
  ├── okada.dc3d() / okada.dc3d0()
  ├── stress.gradients_to_stress()
  ├── stress.rotate_stress_tensor()
  ├── coordinates.fault_to_geo_displacement()
  └── coulomb.compute_cfs_on_receiver()
       └── oops.find_optimal_planes()  [optional]
```

## 5.4 `io/` — Input/Output

| Module | Responsibility |
|--------|---------------|
| `inp_parser.py` | State-machine parser for Coulomb 3.4 `.inp` text format. Public API: `read_inp(path)`, `parse_inp_string(text)`. Produces `CoulombModel`. |
| `csv_writer.py` | Write `CoulombResult` as comma-separated values (grid x, y, CFS, stress components). |
| `dat_writer.py` | Write grid results in Coulomb-compatible `.dat` space-delimited format. |
| `cou_writer.py` | Write results in `.cou` format (Coulomb 3.4 output-compatible). |

All writers accept a `CoulombResult` and a file path; they raise `OutputError` on failure.

## 5.5 `viz/` — Visualisation

All visualisation is built on Matplotlib. Modules produce `matplotlib.Figure` objects; they do not call `plt.show()` (that is the CLI's responsibility).

| Module | Responsibility |
|--------|---------------|
| `maps.py` | Map-view CFS plot: filled contour of ΔCFS with fault traces overlaid |
| `faults.py` | Draw individual fault rectangles in map or 3D view |
| `displacement.py` | Surface displacement vector field (quiver) and magnitude map |
| `sections.py` | Vertical cross-section CFS and displacement plots |
| `colormaps.py` | Custom diverging colourmap centred at zero (red/blue, Coulomb 3.4 style) |
| `styles.py` | Publication-quality rcParams defaults |
| `export.py` | Save figures to PNG / PDF / SVG |
| `_base.py` | Shared figure/axes setup helpers |

## 5.6 `cli/` — Command-Line Interface

Click command group exposed as the `opencoulomb` entry point.

| Module | Command | Description |
|--------|---------|-------------|
| `main.py` | `opencoulomb` | Root group; `--version` flag |
| `compute.py` | `opencoulomb compute` | Parse `.inp`, run pipeline, write output files |
| `plot.py` | `opencoulomb plot` | Parse `.inp`, run pipeline, render and save figures |
| `info.py` | `opencoulomb info` | Parse `.inp`, print model summary (faults, grid, material) |
| `validate.py` | `opencoulomb validate` | Parse `.inp` and report validation errors without computing |
| `convert.py` | `opencoulomb convert` | Convert between output formats (`.csv` ↔ `.dat` ↔ `.cou`) |
| `_logging.py` | — | Shared logging configuration (structured to stderr) |

## 5.7 `exceptions.py` — Exception Hierarchy

```
OpenCoulombError
├── InputError
│   ├── ParseError          (filename, line_number attributes)
│   └── ValidationError
├── ComputationError
│   ├── SingularityError    (Okada point coincides with fault edge)
│   └── ConvergenceError
├── OutputError
│   └── FormatError
└── ConfigError
```
