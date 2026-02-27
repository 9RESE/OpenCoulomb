# types — Context for LLMs

## Purpose
Defines the immutable domain data model for OpenCoulomb. All types are frozen
dataclasses (or plain dataclasses for result aggregates) that flow through the
parse → compute → output pipeline as plain Python values.

## Key Files
| File | Purpose |
|------|---------|
| `fault.py` | `FaultElement` (single source/receiver fault) and `Kode` enum |
| `grid.py` | `GridSpec` (computation grid bounds and resolution) |
| `material.py` | `MaterialProperties` (elastic constants and friction) |
| `model.py` | `CoulombModel` (aggregate root: everything needed to run a computation) |
| `result.py` | `StressResult`, `CoulombResult`, `ElementResult` (outputs) |
| `section.py` | `CrossSectionSpec`, `CrossSectionResult` (vertical profile I/O) |
| `stress.py` | `RegionalStress`, `PrincipalStress`, `StressTensorComponents` |

## Key Types

### Input domain objects (frozen dataclasses)
- **`FaultElement`** — one row in the .inp fault table. Key properties:
  - `kode: Kode` — controls slip interpretation (100=standard, 200=tensile+RL,
    300=tensile+reverse, 400=point source, 500=tensile+inflation)
  - `slip_1`, `slip_2` — slip amounts in metres; meaning depends on `kode`
  - `is_source` / `is_receiver` — derived from whether slip is non-zero
  - `strike_deg`, `rake_deg`, `length`, `width`, `center_x/y/depth` — computed geometry
- **`GridSpec`** — observation grid; `n_x`, `n_y`, `n_points` computed from bounds + increment
- **`MaterialProperties`** — Young's modulus, Poisson's ratio, friction; exposes `alpha` (Okada's elastic constant = `(lambda + mu) / (lambda + 2*mu)`)
- **`CoulombModel`** — aggregate root; `source_faults` / `receiver_faults` sliced by `n_fixed`

### Output types (mutable dataclasses with NDArray fields)
- **`StressResult`** — flat arrays (N,) of coordinates and 9 stress/displacement components
- **`CoulombResult`** — `StressResult` + `cfs`, `shear`, `normal` arrays + grid metadata; `.cfs_grid()` reshapes to `(n_y, n_x)`
- **`ElementResult`** — per-receiver-element CFS (M,) arrays
- **`CrossSectionResult`** — 2D `(n_vert, n_horiz)` arrays for profile plots

## Dependencies
- **Depends on**: `opencoulomb.exceptions` (ValidationError raised in `__post_init__`)
- **Used by**: every other package (`core`, `io`, `viz`, `cli`) — this is the shared vocabulary

## Conventions
- All input types are `frozen=True, slots=True` — treat as immutable value objects
- Result types are mutable (slots only) because they hold large NumPy arrays
- Coordinate system: X = East (km), Y = North (km), Z = negative below surface (km)
- Depths are **positive downward** in user-facing fields (top_depth, bottom_depth, GridSpec.depth)
- Stress units: **bar**; displacement units: **metres**; distance: **km**
- `Kode` is an `IntEnum` so int literals (100, 200, …) compare equal to enum members
