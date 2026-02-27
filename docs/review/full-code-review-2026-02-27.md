# OpenCoulomb Full Code Review

**Date:** 2026-02-27
**Commit:** `2a0d7b5`
**Reviewers:** 4 parallel agents (Opus + Sonnet)
**Scope:** Entire codebase — core engine, types, I/O, viz, CLI, tests

## Summary

| Area | HIGH | MEDIUM | LOW | Total |
|------|------|--------|-----|-------|
| Core Engine | 3 | 8 | 8 | 19 |
| Types/Data Model | 1* | 9 | 9 | 19* |
| I/O Parser & Writers | 4 | 4 | 5 | 13 |
| Viz, CLI & Tests | 2 | 7 | 6 | 15 |
| **Total** | **10** | **28** | **28** | **66** |

\* Types Finding 1 (alpha formula) marked FALSE POSITIVE and excluded from counts.

---

## HIGH Severity (10 findings)

### CORE-H1: DC3D0 `errstate` scope bug
**File:** `src/opencoulomb/core/okada.py` (DC3D0 function)
**Issue:** `np.errstate(divide="ignore", invalid="ignore")` context manager may not cover the full computation — indentation error leaves some operations outside the guarded scope.
**Impact:** Spurious runtime warnings on edge cases; no numerical error but noisy.
**Fix:** Verify the `with` block encompasses the entire DC3D0 computation body.

### CORE-H2: DC3D0 rotation verification
**File:** `src/opencoulomb/core/okada.py`
**Issue:** The coordinate rotation into the fault-local frame (strike rotation) should be verified against Okada (1992) equations 25-26. The rotation angle sign convention needs a cross-check.
**Impact:** If wrong, all displacement/stress results are silently incorrect.
**Fix:** Add explicit reference to Okada (1992) eq. numbers in comments; add a test that verifies rotation for a known asymmetric case.

### CORE-H3: Zero-length fault produces silent NaN
**File:** `src/opencoulomb/core/okada.py`
**Issue:** A `FaultElement` with `length=0` or `width=0` passes validation but produces NaN in Okada outputs. These propagate silently through CFS computation.
**Impact:** NaN contamination in output arrays.
**Fix:** Add validation in `compute_grid` to skip or warn on degenerate faults (length < epsilon or width < epsilon).

### TYPES-H1: GridSpec `n_x`/`n_y` vs `np.arange` count divergence
**File:** `src/opencoulomb/types/grid.py`
**Issue:** `GridSpec.n_x` uses `round((x_max - x_min) / x_inc) + 1` but the actual grid arrays are built with `np.arange(x_min, x_max + x_inc/2, x_inc)`. Floating-point rounding can make these disagree by 1 point.
**Impact:** Shape mismatch between reported grid dimensions and actual array sizes.
**Fix:** Either derive `n_x`/`n_y` from the actual `np.arange` result length, or use `np.linspace` with the computed count.

### IO-H1: `PermissionError`/`OSError` not caught in `read_inp`
**File:** `src/opencoulomb/io/inp_parser.py:56-60`
**Issue:** `read_inp` catches `UnicodeDecodeError` but not `OSError`. Permission-denied or broken symlinks raise raw OS exceptions, bypassing the `ParseError` hierarchy.
**Fix:** Wrap `read_text()` calls in `except OSError as exc: raise ParseError(f"Cannot read: {exc}", ...) from exc`.

### IO-H2: `ZeroDivisionError` for horizontal faults (dip=0) in `_fault_polygon_corners`
**File:** `src/opencoulomb/io/dat_writer.py:101-123`
**Issue:** `math.tan(0)` returns 0; division by `tan(dip_rad)` crashes for `dip=0`. The guard only handles `dip >= 90`.
**Fix:** Add symmetric lower-bound guard: `if fault.dip <= DIP_THRESHOLD or fault.dip >= 90: h_offset = 0.0`.

### IO-H3: Output writers don't wrap `OSError` in `OutputError`
**Files:** `cou_writer.py`, `csv_writer.py`, `dat_writer.py`
**Issue:** Write failures raise raw `FileNotFoundError`/`PermissionError`, not `OutputError`. Callers can't catch all library errors with `except OpenCoulombError`.
**Fix:** Wrap `filepath.open("w")` in `try/except OSError as exc: raise OutputError(...) from exc`.

### IO-H4: Multiline title corrupts `.cou` file header row count
**Files:** `inp_parser.py:546`, `cou_writer.py:42,93`
**Issue:** Parser joins two title lines with `\n`. Writers emit this as-is, producing 4 header lines instead of 3. Downstream parsers expecting fixed header count will misalign all data columns.
**Fix:** Sanitize at write time: `safe_title = model.title.replace("\n", " | ")`.

### VIZ-H1: No `plt.close()` in visualization tests
**File:** `tests/unit/test_viz.py`
**Issue:** Viz tests create matplotlib figures but never close them. Accumulates memory; produces ResourceWarning at scale.
**Fix:** Add `plt.close(fig)` in teardown or use `@pytest.fixture` that auto-closes.

### VIZ-H2: `matplotlib.use("Agg")` called per-method
**File:** `tests/unit/test_viz.py`
**Issue:** Backend set repeatedly instead of once at module level. Risk of backend-switch errors if tests run after interactive backend is initialized.
**Fix:** Move `matplotlib.use("Agg")` to module-level or conftest.py.

---

## MEDIUM Severity (28 findings)

### Core Engine (8)

| ID | Finding | File |
|----|---------|------|
| CORE-M1 | Near-horizontal dip (dip~0) gives infinite width in Okada | `okada.py` |
| CORE-M2 | Missing z<=0 validation for observation points | `okada.py` |
| CORE-M3 | Stress rotation convention not documented | `stress.py` |
| CORE-M4 | OOPs loop not vectorized (slow for large grids) | `oops.py` |
| CORE-M5 | Missing Poisson ratio validation (0 < nu < 0.5) in stress | `stress.py` |
| CORE-M6 | Receiver centroid offset for dipping faults | `pipeline.py` |
| CORE-M7 | Floating-point grid `np.arange` can produce extra/missing points | `pipeline.py` |
| CORE-M8 | Unnecessary temporary array allocations in stress tensor | `stress.py` |

### Types/Data Model (9)

| ID | Finding | File |
|----|---------|------|
| TYPES-M1 | `_KM_TO_M` constant duplicated across modules | `constants.py` + others |
| TYPES-M2 | `GridSpec.depth` not validated (should be non-negative) | `grid.py` |
| TYPES-M3 | `CoulombModel` has mutable list fields | `model.py` |
| TYPES-M4 | `CoulombModel` no `__post_init__` validation | `model.py` |
| TYPES-M5 | `is_source` uses exact float equality for slip check | `fault.py` |
| TYPES-M6 | `PrincipalStress` no validation on eigenvalues | `results.py` |
| TYPES-M7 | Result array shapes not validated in constructors | `results.py` |
| TYPES-M8 | `CrossSectionSpec` allows zero-length profiles | `section.py` |
| TYPES-M9 | Exception classes not exported from package `__init__` | `__init__.py` |

### I/O Parser & Writers (4)

| ID | Finding | File |
|----|---------|------|
| IO-M1 | `KeyError` for invalid `field` in `write_coulomb_dat` | `dat_writer.py` |
| IO-M2 | Cross-section `h_inc` (param 5) silently discarded | `inp_parser.py` |
| IO-M3 | `_ParserState.STRESS` and `_on_stress` are dead code | `inp_parser.py` |
| IO-M4 | Handler dict rebuilt on every `_dispatch` call | `inp_parser.py` |

### Viz, CLI & Tests (7)

| ID | Finding | File |
|----|---------|------|
| VIZ-M1 | `plot_cmd` doesn't close figure after save | `cli/plot.py` |
| VIZ-M2 | Unguarded `KeyError` in cross-section plotting | `viz/sections.py` |
| VIZ-M3 | Vertical displacement uses diverging colormap (should be sequential) | `viz/maps.py` |
| VIZ-M4 | Duplicate log handlers on repeated CLI invocations | `cli/__init__.py` |
| VIZ-M5 | Raw tracebacks in `compute` command error paths | `cli/compute.py` |
| VIZ-M6 | No error handling in `info` command for malformed files | `cli/info.py` |
| VIZ-M7 | `save_figure` doesn't create parent directories | `viz/utils.py` |

---

## LOW Severity (28 findings)

### Core Engine (8)
CORE-L1: Chinnery sign comment misleading
CORE-L2: `_dccon2` dict allocation per call
CORE-L3: OOPs `abs(CFS)` selection may not match Coulomb 3.4
CORE-L4: Missing coordinate module exports
CORE-L5: Stress convention docstring error (compression sign)
CORE-L6: Regional stress orthogonality not validated
CORE-L7: 2D rotation helper comment incorrect
CORE-L8: Tensile receiver rake handling undefined

### Types/Data Model (9)
TYPES-L1: `element_index` default 0 ambiguous (0 vs None)
TYPES-L2: `width` property returns 0 for horizontal faults
TYPES-L3: `rake_deg` property undefined for tensile faults
TYPES-L4: Missing `shear_grid`/`normal_grid` convenience methods on results
TYPES-L5: `ParseError` annotation attributes not typed
TYPES-L6: `ConfigError` defined but never raised
TYPES-L7: Constants module missing docstring
TYPES-L8: `GridSpec` error messages don't include actual values
TYPES-L9: `ElementResult` docstring incomplete

### I/O Parser & Writers (5)
IO-L1: `ParseError` reports `line_number=0` for empty files
IO-L2: `numpy` imported inside `write_summary` function body
IO-L3: Writers use system-default encoding (not UTF-8)
IO-L4: `_current_line()` method defined but never called
IO-L5: Non-ASCII em dash in `.cou`/`.dat` headers (Coulomb 3.4 was ASCII)

### Viz, CLI & Tests (6)
VIZ-L1: `tmp_path` typed as `object` in test fixtures
VIZ-L2: Fragile wall-clock timing assertions in benchmarks
VIZ-L3: `validate.py` iterates all faults for summary (O(n))
VIZ-L4: Redundant numpy import in test module
VIZ-L5: CLI tests assert exit code but not output content
VIZ-L6: `stress_cmap` duplicate definition

---

## FALSE POSITIVES (excluded)

### TYPES-FP1: Alpha formula "incorrect"
**Claim:** `alpha = 1/(2*(1-nu))` should be `(1-2*nu)/(2*(1-nu))`.
**Verdict:** FALSE POSITIVE. Okada (1992) defines `alpha = (lambda+mu)/(lambda+2*mu)`. Working through Lame parameters: `alpha = 1/(2*(1-nu))` is correct. For nu=0.25, alpha=2/3=0.667. All Okada reference tests pass with this formula.

---

## Priority Remediation Plan

### Phase 1: Critical fixes (10 HIGH findings)
Estimated: 1-2 sessions

1. **IO-H4** — Title sanitization in writers (quick fix, high impact)
2. **IO-H2** — Dip=0 ZeroDivisionError guard (quick fix)
3. **IO-H1** — OSError wrapping in `read_inp`
4. **IO-H3** — OSError wrapping in all writers
5. **CORE-H3** — Zero-length fault NaN guard
6. **CORE-H1** — DC3D0 errstate scope verification
7. **TYPES-H1** — GridSpec n_x/n_y consistency
8. **CORE-H2** — Rotation convention verification + test
9. **VIZ-H1** — plt.close() in tests
10. **VIZ-H2** — matplotlib.use("Agg") at module level

### Phase 2: Medium fixes (28 findings)
Estimated: 2-3 sessions, parallelizable

- Error handling improvements (IO-M1, VIZ-M5, VIZ-M6)
- Validation additions (CORE-M2, CORE-M5, TYPES-M2, TYPES-M4)
- Dead code removal (IO-M3, IO-M4)
- Performance (CORE-M4, CORE-M8, IO-M4)
- Correctness (CORE-M6, CORE-M7, TYPES-M3, TYPES-M5)

### Phase 3: Low priority (28 findings)
Address opportunistically during related work.
