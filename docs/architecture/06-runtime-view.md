# Arc42 § 6 — Runtime View

## 6.1 Primary Workflow: CLI Compute

The most common runtime scenario: a user runs `opencoulomb compute model.inp`.

```
User
 │
 │  $ opencoulomb compute model.inp --output results/
 ▼
cli/compute.py (Click command)
 │
 │  read_inp("model.inp")
 ▼
io/inp_parser.py (state machine)
 │  ├── Tokenise lines by state (HEADER, SIZE, MATERIAL, FAULTS, GRID, ...)
 │  ├── Build FaultElement list (sources then receivers)
 │  └── Return CoulombModel (frozen, validated)
 │
 │  compute_grid(model)
 ▼
core/pipeline.py
 │
 │  Step 1: Generate (x, y) observation grid from GridSpec
 │          shape: (N_y, N_x)
 │
 │  Step 2: For each source fault in model.source_faults:
 │    │
 │    ├── coordinates.compute_fault_geometry(fault)
 │    │     → strike/dip unit vectors, rotation matrix R
 │    │
 │    ├── okada.dc3d(fault, x_grid, y_grid, depth=grid.depth)
 │    │     → ux, uy, uz          shape (N_y, N_x)
 │    │     → uxx, uxy, ... uzz   shape (N_y, N_x)  [9 displacement gradients]
 │    │
 │    ├── stress.gradients_to_stress(gradients, material)
 │    │     → σ_xx, σ_yy, σ_zz, σ_xy, σ_xz, σ_yz  (Hooke's law)
 │    │
 │    ├── stress.rotate_stress_tensor(σ, R)
 │    │     → stress in geographic frame
 │    │
 │    └── Accumulate: total_stress += fault_stress
 │                    total_disp   += fault_disp
 │
 │  Step 3: Resolve CFS on receiver orientation
 │    │
 │    └── coulomb.compute_cfs_on_receiver(total_stress, receiver_fault, μ)
 │          → ΔCFS array  shape (N_y, N_x)
 │
 │  Step 4 (optional): Cross-section
 │    └── Repeat Steps 1-3 on vertical profile points
 │
 │  Return CoulombResult(cfs, stress, displacement, model, grid)
 │
 │  csv_writer.write(result, "results/cfs.csv")
 │  dat_writer.write(result, "results/cfs.dat")
 ▼
Done — files written to results/
```

## 6.2 Library API Workflow

Users entering via the Python API can bypass the CLI entirely:

```python
from opencoulomb.io import read_inp
from opencoulomb.core.pipeline import compute_grid

model = read_inp("model.inp")          # → CoulombModel
result = compute_grid(model)           # → CoulombResult
cfs_array = result.cfs                 # shape (N_y, N_x), units: bar
x_coords  = result.grid.x_coords      # shape (N_x,)
y_coords  = result.grid.y_coords      # shape (N_y,)
```

## 6.3 Okada Vectorisation (Inner Loop)

The Okada engine is the performance-critical path. It operates on the full grid in one call:

```
Input:
  fault: FaultElement  (scalar geometry parameters)
  X: NDArray[float64]  shape (N_y * N_x,)  — flattened grid x
  Y: NDArray[float64]  shape (N_y * N_x,)  — flattened grid y
  Z: float             — observation depth (negative downward)

Output:
  ux, uy, uz:           NDArray[float64]  shape (N_y * N_x,)
  uxx, uxy, ..., uzz:   NDArray[float64]  shape (N_y * N_x,)  × 9

No Python loop over grid points — all arithmetic is NumPy ufuncs.
```

Singularity points (observation point on fault plane boundary) raise `SingularityError`.

## 6.4 State Machine Parser States

The `.inp` parser transitions through an ordered sequence of named states:

```
INIT
 └─► HEADER          (lines 1-2: title)
      └─► SIZE_PARAMS (fault count, grid size)
           └─► MATERIAL (Young's modulus, Poisson's ratio, friction)
                └─► SOURCE_FAULTS (n_fixed fault lines)
                     └─► RECEIVER_FAULTS (remaining fault lines)
                          └─► GRID_SPEC (x/y bounds, spacing, depth)
                               └─► REGIONAL_STRESS? (optional)
                                    └─► CROSS_SECTION? (optional)
                                         └─► DONE
```

State transitions are triggered by:
- Line count (e.g., first 2 lines are always the title)
- Keyword tokens (section headers containing known strings)
- Blank/comment lines (skipped in most states)

## 6.5 Plot Workflow

```
$ opencoulomb plot model.inp --type cfs --output map.png

cli/plot.py
 ├── read_inp(model.inp)      → CoulombModel
 ├── compute_grid(model)      → CoulombResult
 ├── viz/maps.plot_cfs(result) → matplotlib.Figure
 ├── viz/faults.overlay_faults(fig, model.faults)
 └── viz/export.save(fig, "map.png")
```

Figures are never displayed interactively by the library; `plt.show()` is only called when the user passes `--show` to the CLI.

## 6.6 Error Propagation

```
ParseError    ─┐
               ├─► cli catches OpenCoulombError
ValidationError─┤   prints message to stderr
ComputationError┤   exits with code 1
OutputError   ─┘

SingularityError ─► logged as WARNING; affected grid cell set to NaN
```
