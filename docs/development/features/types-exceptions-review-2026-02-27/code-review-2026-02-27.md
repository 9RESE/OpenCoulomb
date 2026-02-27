# Code Review: OpenCoulomb Data Model (types/) and Exception Hierarchy

## Review Summary
**Reviewer**: Code Review Agent
**Date**: 2026-02-27
**Files Reviewed**: 10 files
**Issues Found**: 20 (2 HIGH, 9 MEDIUM, 9 LOW)

Files reviewed:
- `src/opencoulomb/types/fault.py`
- `src/opencoulomb/types/grid.py`
- `src/opencoulomb/types/material.py`
- `src/opencoulomb/types/model.py`
- `src/opencoulomb/types/result.py`
- `src/opencoulomb/types/section.py`
- `src/opencoulomb/types/stress.py`
- `src/opencoulomb/types/__init__.py`
- `src/opencoulomb/exceptions.py`
- `src/opencoulomb/_constants.py`

Supporting files also consulted:
- `src/opencoulomb/core/pipeline.py`
- `src/opencoulomb/core/stress.py`
- `src/opencoulomb/core/okada.py`

## Findings

### Finding 1: `alpha` Formula — Code or Comment Is Wrong vs Okada (1992) (Severity: HIGH)

**File**: `src/opencoulomb/types/material.py:50`

**Issue**: The docstring states `alpha = (lambda+mu)/(lambda+2*mu) = 1/(2*(1-nu))`. The algebraic
identity is wrong. The correct derivation using Lame parameters gives
`(lambda+mu)/(lambda+2*mu) = (1-2*nu)/(2*(1-nu))`.

For the default nu=0.25:
- Okada definition: alpha = (1-0.5)/(2*0.75) = 1/3 ≈ 0.333
- Code `1/(2*(1-0.25))` = 1/1.5 ≈ 0.667

One of the code formula or the Okada reference formula is wrong. This is a critical accuracy
issue that affects all Okada displacement and stress computations.

**Recommendation**: Verify against Okada (1992) Appendix A. The correct formula is
`(1 - 2*nu) / (2*(1 - nu))`. Fix both code and comment together and confirm via the
reference validation tests (`tests/unit/test_reference_validation.py`).

```python
@property
def alpha(self) -> float:
    """Okada medium constant: (lambda+mu)/(lambda+2*mu) = (1-2*nu)/(2*(1-nu))."""
    return (1.0 - 2.0 * self.poisson) / (2.0 * (1.0 - self.poisson))
```

### Finding 17: `GridSpec.n_x`/`n_y` Can Disagree With Pipeline's `np.arange` Count (Severity: HIGH)

**File**: `src/opencoulomb/types/grid.py:47-54` vs `src/opencoulomb/core/pipeline.py:82-83`

**Issue**: `GridSpec.n_x` uses `math.floor((finish_x - start_x) / x_inc) + 1` but the pipeline
uses `np.arange(grid.start_x, grid.finish_x + grid.x_inc * 0.5, grid.x_inc)`. These two
formulas are not guaranteed to agree due to floating-point arithmetic differences. When they
disagree, `grid_shape = (n_y, n_x)` stored in `CoulombResult` will not match the actual flat
array length, causing numpy reshape errors in `cfs_grid()` or silent shape mismatches.

**Recommendation**: Make the pipeline use `np.linspace` (derived from `n_x`, `n_y`) and
make `n_x`, `n_y` the canonical grid size:

```python
# pipeline.py
x_1d = np.linspace(grid.start_x, grid.finish_x, grid.n_x)
y_1d = np.linspace(grid.start_y, grid.finish_y, grid.n_y)
```

### Finding 2: `_KM_TO_M` Duplicated in `stress.py` Instead of Imported (Severity: MEDIUM)

**File**: `src/opencoulomb/core/stress.py:23`

**Issue**: `_KM_TO_M = 0.001` duplicates `M_TO_KM` from `_constants.py`.

**Recommendation**: `from opencoulomb._constants import M_TO_KM as _KM_TO_M`

### Finding 3: `GridSpec.depth` Not Validated as >= 0 (Severity: MEDIUM)

**File**: `src/opencoulomb/types/grid.py:38-44`

**Issue**: `__post_init__` does not validate `depth >= 0`. A negative depth produces z > 0 in
the pipeline, placing observation points above the free surface — physically invalid and not
caught until Okada runtime errors.

**Recommendation**:
```python
if self.depth < 0:
    raise ValidationError(f"Calculation depth must be >= 0, got {self.depth}")
```

### Finding 4: `CoulombModel` Is Mutable (No `frozen=True`) (Severity: MEDIUM)

**File**: `src/opencoulomb/types/model.py:16`

**Issue**: Unlike all leaf types, `CoulombModel` uses `@dataclass(slots=True)` without
`frozen=True`. Post-construction field assignment (e.g. `model.n_fixed = -1`) produces
inconsistent state with no error. There is no intentional mutation in the codebase.

**Recommendation**: Add `frozen=True`.

### Finding 5: `CoulombModel` Has No `__post_init__` Validation (Severity: MEDIUM)

**File**: `src/opencoulomb/types/model.py:53`

**Issue**: No check that `0 <= n_fixed <= len(faults)`. Direct construction (common in tests)
bypasses all parser-level invariant checks. `source_faults` and `receiver_faults` produce
wrong slices silently when `n_fixed` is invalid.

**Recommendation**:
```python
def __post_init__(self) -> None:
    if not (0 <= self.n_fixed <= len(self.faults)):
        raise ValidationError(
            f"n_fixed={self.n_fixed} is out of range for "
            f"{len(self.faults)} fault element(s)"
        )
```

### Finding 6: `FaultElement.is_source` Uses Exact Float Equality (Severity: MEDIUM)

**File**: `src/opencoulomb/types/fault.py:89`

**Issue**: `slip_1 != 0.0 or slip_2 != 0.0` — exact float equality. Text-parsed slip values
may have representational epsilon differences. More importantly, `is_source` is logically
redundant with the `n_fixed` index split in `CoulombModel`; a discrepancy between them is
a latent bug.

**Recommendation**: Add docstring note that these properties are informational only and should
not be used for authoritative source/receiver classification (use `n_fixed` instead).

### Finding 10: `PrincipalStress`/`RegionalStress` Have No Validation (Severity: MEDIUM)

**File**: `src/opencoulomb/types/stress.py:6-38`

**Issue**: `PrincipalStress` documents `direction` in [0, 360] and `dip` in [-90, 90] but
enforces neither. `RegionalStress` documents `s1 >= s2 >= s3` convention but does not
validate it. Invalid values propagate into OOPs calculations silently.

**Recommendation**: Add `__post_init__` to `PrincipalStress`:
```python
def __post_init__(self) -> None:
    if not (0.0 <= self.direction <= 360.0):
        raise ValidationError(f"direction must be in [0, 360], got {self.direction}")
    if not (-90.0 <= self.dip <= 90.0):
        raise ValidationError(f"dip must be in [-90, 90], got {self.dip}")
    if self.gradient < 0:
        raise ValidationError(f"gradient must be >= 0, got {self.gradient}")
```

### Finding 11: Result Types Have No Array-Shape Consistency Checks (Severity: MEDIUM)

**File**: `src/opencoulomb/types/result.py:15-104`

**Issue**: `StressResult` and `CoulombResult` do not check that all arrays have consistent
shapes. Mismatched arrays produce delayed `IndexError` or wrong reshaped grids in `cfs_grid()`.
The `cfs_grid()` reshape error message from numpy is not diagnostic.

**Recommendation**: Add `__post_init__` that validates all array lengths match `len(self.x)`.

### Finding 13: `CrossSectionSpec` Does Not Reject Zero-Length Profiles (Severity: MEDIUM)

**File**: `src/opencoulomb/types/section.py:41-49`

**Issue**: Zero-length profile (start == finish) passes construction and fails later with
`ComputationError` in the pipeline. This violates the principle of failing fast at construction.

**Recommendation**: Add to `__post_init__`:
```python
if (self.finish_x - self.start_x) ** 2 + (self.finish_y - self.start_y) ** 2 < 1e-20:
    raise ValidationError("Cross-section profile has zero length")
```

### Finding 16: `types/__init__.py` Exports No Exception Types (Severity: MEDIUM)

**File**: `src/opencoulomb/types/__init__.py` + `src/opencoulomb/__init__.py`

**Issue**: `ValidationError` (and all other exceptions) require a separate import from
`opencoulomb.exceptions`. The top-level `__init__.py` only exports `__version__`. Users of the
library must know the internal module structure to catch any errors, which is a poor API surface.

**Recommendation**: Re-export all public exceptions from the top-level `__init__.py`:
```python
from opencoulomb.exceptions import (
    OpenCoulombError, ParseError, ValidationError,
    ComputationError, SingularityError, OutputError, ConfigError,
)
```

### Finding 7: `element_index` Default of 0 Is Ambiguous (Severity: LOW)

**File**: `src/opencoulomb/types/fault.py:73`

**Issue**: Docstring says "1-based from .inp file. Default: 0." — 0 is not a valid 1-based index
and cannot be distinguished from "not from a file" vs "element 1 with wrong index."

**Recommendation**: Use `int | None = None`.

### Finding 8: `FaultElement.width` Returns 0 for Horizontal Faults (Severity: LOW)

**File**: `src/opencoulomb/types/fault.py:135-137`

**Issue**: dip=0 with top_depth != bottom_depth returns `width=0.0`, implying zero fault area.
The correct geometry has infinite width in the down-dip direction. Callers using `width` for
area computations will silently get wrong results.

**Recommendation**: Return `float('inf')` or raise `ValidationError` for dip=0 with
non-zero depth extent. At minimum add a docstring warning.

### Finding 9: `rake_deg` Silently Returns 0.0 for Tensile Sources (Severity: LOW)

**File**: `src/opencoulomb/types/fault.py:116-118`

**Issue**: Tensile KODE (200/300/500) elements return `rake_deg = 0.0` (pure strike-slip).
Callers who do not check `kode` first feed wrong rake into CFS resolution.

**Recommendation**: Add explicit docstring warning and consider returning `float('nan')` for
undefined cases.

### Finding 12: `CoulombResult` Missing `shear_grid()` and `normal_grid()` (Severity: LOW)

**File**: `src/opencoulomb/types/result.py:91-104`

**Issue**: Breaks symmetry with `cfs_grid()`. Downstream code must manually call
`.reshape(result.grid_shape)` on `shear` and `normal`.

**Recommendation**: Add `shear_grid()` and `normal_grid()` methods.

### Finding 14: `ParseError` Fields Lack Type Annotations (Severity: LOW)

**File**: `src/opencoulomb/exceptions.py:27-40`

**Issue**: `self.filename` and `self.line_number` are instance attributes without class-level
type annotations, making them invisible to type checkers.

**Recommendation**:
```python
class ParseError(InputError):
    filename: str | None
    line_number: int | None
```

### Finding 15: `ConfigError` Is Unused and Not Exported (Severity: LOW)

**File**: `src/opencoulomb/exceptions.py:90-92`

**Issue**: `ConfigError` is never raised in the current codebase and is not in any `__all__`.

**Recommendation**: Either remove until Phase D CLI config parsing, or add a `# TODO(Phase D)`
comment and export from the package `__init__.py`.

### Finding 18: `DEFAULT_YOUNG_BAR` Comment Could Be Clearer (Severity: LOW)

**File**: `src/opencoulomb/_constants.py:7`

**Issue**: Comment reads `# 80 GPa in bar (1 bar = 0.1 MPa)` — conversion chain is implicit.

**Recommendation**: `# 80 GPa = 8e4 MPa = 8e5 bar`

### Finding 19: `GridSpec` Validation Errors Omit Actual Values (Severity: LOW)

**File**: `src/opencoulomb/types/grid.py:40-44`

**Issue**: All three `ValidationError` messages omit the actual bad values, unlike other types
in the codebase that consistently include them.

**Recommendation**:
```python
raise ValidationError(
    f"finish_x ({self.finish_x}) must exceed start_x ({self.start_x})"
)
```

### Finding 20: `ElementResult.elements` Docstring Uses `list` Instead of `list[FaultElement]` (Severity: LOW)

**File**: `src/opencoulomb/types/result.py:113-114`

**Issue**: Docstring inconsistency — `elements : list` with `(list[FaultElement])` as a
parenthetical, while the field annotation uses `list[FaultElement]` directly.

**Recommendation**: `elements : list[FaultElement]` in the docstring.

## Summary Table

| # | File | Finding | Severity |
|---|------|---------|----------|
| 1 | `types/material.py:50` | `alpha` formula in code or comment wrong vs Okada (1992) | HIGH |
| 17 | `types/grid.py:47-54` + `core/pipeline.py:82` | `n_x`/`n_y` can disagree with `np.arange` grid size | HIGH |
| 2 | `core/stress.py:23` | `_KM_TO_M` duplicated from `_constants.py` | MEDIUM |
| 3 | `types/grid.py:38-44` | `GridSpec.depth` not validated as >= 0 | MEDIUM |
| 4 | `types/model.py:16` | `CoulombModel` mutable (no `frozen=True`) | MEDIUM |
| 5 | `types/model.py:53` | `CoulombModel` has no `__post_init__` for `n_fixed` bounds | MEDIUM |
| 6 | `types/fault.py:89` | `is_source` uses exact float equality | MEDIUM |
| 10 | `types/stress.py:6-38` | `PrincipalStress`/`RegionalStress` have no validation | MEDIUM |
| 11 | `types/result.py:15-104` | Result types have no array-shape consistency checks | MEDIUM |
| 13 | `types/section.py:41-49` | `CrossSectionSpec` accepts zero-length profiles | MEDIUM |
| 16 | `types/__init__.py` | No exception types exported anywhere | MEDIUM |
| 7 | `types/fault.py:73` | `element_index` default 0 ambiguous vs 1-based convention | LOW |
| 8 | `types/fault.py:135-137` | `width` returns 0 for horizontal faults with depth extent | LOW |
| 9 | `types/fault.py:116-118` | `rake_deg` silently 0.0 for tensile sources | LOW |
| 12 | `types/result.py:91-104` | `shear_grid()` and `normal_grid()` missing | LOW |
| 14 | `exceptions.py:27-40` | `ParseError.filename`/`line_number` lack type annotations | LOW |
| 15 | `exceptions.py:90-92` | `ConfigError` unused and not exported | LOW |
| 18 | `_constants.py:7` | `DEFAULT_YOUNG_BAR` comment incomplete | LOW |
| 19 | `types/grid.py:40-44` | `GridSpec` errors omit actual bad values | LOW |
| 20 | `types/result.py:113-114` | `ElementResult.elements` docstring inconsistency | LOW |

## Patterns Learned

- Frozen dataclasses should be uniformly applied to all domain types, including aggregate roots
- `n_x`/`n_y` grid-count properties must be computed using the same arithmetic as the array
  generation code — `math.floor + arange` vs `linspace` can diverge
- Exact float equality for "is zero slip" classification is fragile in a text-parsing pipeline
- Physical constants that appear in multiple modules must be imported from the canonical source,
  not re-declared
- Exception types with structured attributes (`filename`, `line_number`) need class-level
  type annotations for type checker visibility
- Validation should fail at construction time (dataclass `__post_init__`), not at computation
  time in the pipeline

## Knowledge Contributions

- New pattern: When a `__post_init__` validates X, check that all direct constructors
  (parser, tests, and library callers) produce inputs that pass that validation
- Anti-pattern identified: Mutable aggregate root over immutable leaf types — breaks
  the invariant that the domain model is safe to pass across module boundaries
- Anti-pattern identified: `np.arange` with fractional steps for grid generation —
  prefer `np.linspace` when endpoint count matters

**Review Status**: Complete — no changes implemented (review-only mode)
