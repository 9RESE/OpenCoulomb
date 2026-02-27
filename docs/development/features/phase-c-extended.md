# Phase C: Extended Computation — Completion Report

**Phase**: C — Extended Computation
**Tasks**: 021–024 (4/4 completed)
**Status**: COMPLETE
**Date**: 2026-02-27
**Test Count**: 717 passing (668 prior + 49 new)
**Lint**: ruff clean (0 violations), mypy strict (0 errors)

---

## Scope and Deliverables

Phase C adds two independent computation capabilities that extend the Phase B core engine:

1. **Optimally Oriented Planes (OOPs)**: Given a regional stress field plus earthquake-induced stress, find the fault orientation at each grid point that maximizes Coulomb failure stress.

2. **Cross-Section Computation**: Compute stress, displacement, and CFS on a vertical profile through the model, producing 2D depth-vs-distance results.

---

## New Modules

### `core/oops.py` — Optimally Oriented Planes

| Function | Purpose |
|----------|---------|
| `compute_regional_stress_tensor(regional, depth)` | Build 6-component stress tensor from 3 principal stress axes at given depths |
| `mohr_coulomb_angle(friction)` | Compute optimal failure angle: `0.5 * atan(1/mu)` |
| `find_optimal_planes(sxx..sxy, friction)` | Eigendecompose stress tensor, find conjugate Mohr-Coulomb planes, return the one with maximum CFS |

**Algorithm**:
1. Build (N, 3, 3) symmetric stress matrices from Voigt components
2. Batch eigendecomposition via `np.linalg.eigh`
3. Compute Mohr-Coulomb angle `beta = 0.5 * atan(1/friction)`
4. Construct two conjugate plane normals: `cos(beta)*s1 +/- sin(beta)*s3`
5. Compute CFS on each conjugate plane via traction vector resolution
6. Select plane with higher |CFS|
7. Convert normal to geographic (strike, dip, rake)

**Internal helpers**:
- `_build_stress_matrices()` — Voigt to 3x3 batch conversion
- `_compute_cfs_on_normals()` — Vectorized traction and CFS computation
- `_normal_to_strike_dip_rake()` — Normal vector to fault orientation

### `core/pipeline.py` — Cross-Section Extension

| Function | Purpose |
|----------|---------|
| `compute_cross_section(model, spec, receiver_index)` | Full cross-section computation on a vertical profile |

**Algorithm**:
1. Generate profile geometry: N_horiz points along profile, N_vert depth levels
2. Horizontal resolution from `grid.x_inc`, vertical from `spec.z_inc`
3. Geographic coordinates: `(start + t * direction, -depth)` for each point
4. Source fault loop: reuses `_accumulate_fault()` from Phase B
5. CFS resolution onto receiver fault orientation (same as `compute_grid`)
6. Reshape to 2D `(n_vert, n_horiz)` arrays in `CrossSectionResult`

---

## Model Changes

### `types/model.py` — CoulombModel

Added `cross_section: CrossSectionSpec | None = None` field to store parsed cross-section parameters.

### `io/inp_parser.py`

Updated `_build_model()` to pass the parsed `CrossSectionSpec` into `CoulombModel.cross_section` (previously parsed but discarded with a TODO comment).

### `core/__init__.py`

Exported new public API: `compute_cross_section`, `compute_regional_stress_tensor`, `find_optimal_planes`, `mohr_coulomb_angle`.

---

## Pipeline Integration

### OOPs in `compute_grid()`

When `model.regional_stress` is not None:
1. Compute regional stress tensor at grid depth
2. Add to earthquake-induced stress (superposition)
3. Call `find_optimal_planes()` on total stress
4. Populate `CoulombResult.oops_strike`, `oops_dip`, `oops_rake`

When `regional_stress` is None: OOP fields remain None (no change to existing behavior).

### Cross-Section API

```python
# Using model's parsed cross-section spec
result = compute_cross_section(model)

# Using explicit spec
spec = CrossSectionSpec(start_x=-20, start_y=0, finish_x=20, finish_y=0,
                         depth_min=0, depth_max=15, z_inc=1)
result = compute_cross_section(model, spec=spec)
```

---

## Test Coverage

### OOPs Tests (26 tests in `tests/unit/test_oops.py`)

| Test Class | Tests | Coverage |
|------------|-------|----------|
| TestMohrCoulombAngle | 4 | Angle computation for standard, zero, high, typical friction |
| TestRegionalStressTensor | 6 | N/E/vertical axes, depth gradient, hydrostatic, oblique |
| TestBuildStressMatrices | 3 | Shape, symmetry, values |
| TestFindOptimalPlanes | 6 | Uniaxial, uniform, hydrostatic, range checks, single point |
| TestNormalToStrikeDipRake | 4 | Vertical, north/east dipping, flipped normal |
| TestOOPsInPipeline | 2 | No regional → None; with regional → populated |

### Cross-Section Tests (23 tests in `tests/unit/test_cross_section.py`)

| Test Class | Tests | Coverage |
|------------|-------|----------|
| TestCrossSectionParsing | 3 | Model has spec, correct type, valid values |
| TestCrossSectionShape | 5 | Shape, distance, depth arrays, all-same-shape, spec preserved |
| TestCrossSectionFinite | 3 | CFS, displacement, stress all finite |
| TestProfileOrientation | 3 | E-W, N-S, diagonal profiles |
| TestSurfaceConsistency | 1 | Surface CFS consistent with grid computation |
| TestDepthAxis | 3 | Positive downward, shallow, deep |
| TestModelSpec | 2 | Uses model spec, explicit overrides |
| TestCrossSectionErrors | 3 | No sources, no spec, zero-length, invalid receiver |

---

## Quality Gates

| Metric | Before | After |
|--------|--------|-------|
| Source files (core/) | 23 | 24 (+oops.py) |
| Test count | 668 | 717 (+49) |
| mypy errors | 0 | 0 |
| ruff violations | 0 | 0 |
