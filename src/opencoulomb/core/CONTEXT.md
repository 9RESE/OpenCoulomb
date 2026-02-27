# core — Context for LLMs

## Purpose
The computation engine: transforms a `CoulombModel` into stress, displacement,
and Coulomb failure stress (CFS) fields using the Okada (1985/1992) dislocation
model and linear elasticity (Hooke's law).

## Key Files
| File | Purpose |
|------|---------|
| `pipeline.py` | Top-level orchestration: `compute_grid`, `compute_element_cfs`, `compute_cross_section` |
| `okada.py` | Pure-NumPy vectorized Okada DC3D (finite fault) and DC3D0 (point source) |
| `coulomb.py` | CFS formula: `resolve_stress_on_fault`, `compute_cfs`, `compute_cfs_on_receiver` |
| `stress.py` | `gradients_to_stress` (Hooke's law) and `rotate_stress_tensor` |
| `coordinates.py` | `compute_fault_geometry`, `fault_to_geo_displacement` (coordinate transforms) |
| `oops.py` | Optimally Oriented Planes: `compute_regional_stress_tensor`, `find_optimal_planes`, `mohr_coulomb_angle` |

## Key Functions

### Pipeline (main entry points)
- **`compute_grid(model, receiver_index=None) -> CoulombResult`**
  Full grid computation. Superimposes all source faults, resolves CFS onto one
  receiver orientation (Coulomb 3.4 behavior). Returns flat arrays reshaped via
  `result.cfs_grid()` → `(n_y, n_x)`.
- **`compute_element_cfs(model) -> ElementResult | None`**
  CFS at individual receiver fault centers, each resolved on its own orientation.
  Returns `None` if model has no receivers.
- **`compute_cross_section(model, spec=None, receiver_index=None) -> CrossSectionResult`**
  Stress/CFS on a vertical 2D profile (distance × depth), using `model.cross_section`
  or an explicit `CrossSectionSpec`.

### Okada engine
- **`dc3d(...)`** — finite rectangular fault (KODE 100/200/300); returns 12-element
  array: `[ux, uy, uz, uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz]`
- **`dc3d0(...)`** — point source (KODE 400/500); same output shape
- All inputs in fault-local coordinates; Okada sign convention: z ≤ 0

### CFS formula
- **`resolve_stress_on_fault(..., strike_rad, dip_rad, rake_rad)`** → `(shear, normal)`
- **`compute_cfs_on_receiver(..., friction)`** → `(cfs, shear, normal)`
  `CFS = shear + friction * normal` (positive = promotes failure)

### Coordinate / stress utilities
- **`compute_fault_geometry(...)`** → dict with `strike_rad`, `dip_rad`, `depth`,
  `al1/al2` (along-strike half-lengths), `aw1/aw2` (down-dip half-widths), `center_x/y`
- **`gradients_to_stress(uxx, ..., young, poisson)`** — Hooke's law, outputs in bar
- **`rotate_stress_tensor(..., strike_rad, dip_rad)`** — fault-local → geographic frame

## Dependencies
- **Depends on**: `opencoulomb.types` (all domain types), `numpy` (vectorized ops)
- **Used by**: `opencoulomb.io` (writers receive results), `opencoulomb.cli` (compute command), `opencoulomb.viz` (plots consume results)

## Conventions
- Observation points use **geographic coordinates** (East/North/Up in km)
- Okada is called in **fault-local** coordinates; `_accumulate_fault` handles the full
  transform: geographic → local → Okada → rotate back → geographic
- Superposition: each source fault's contribution is accumulated in-place into total arrays
- Stress units throughout: **bar** (converted from Pa inside `gradients_to_stress`)
- Sign convention for CFS: positive shear = promotes slip; positive normal = unclamping
- Point sources (KODE 400/500) use `dc3d0` with potency inputs, not dislocation inputs
- KODE 100 strike-slip sign flip: Coulomb right-lateral+ → Okada left-lateral+ (`disl1 = -slip_1`)
