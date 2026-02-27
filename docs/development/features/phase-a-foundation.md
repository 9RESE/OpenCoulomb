# Phase A: Foundation — Completion Report

**Phase**: A — Foundation
**Tasks**: 001–010 (10/10 completed)
**Status**: COMPLETE
**Date**: 2026-02-27
**Test Count**: 412 passing
**Coverage**: 94.55% total (90% threshold: PASSED)
**Lint**: ruff clean (0 violations)

---

## Scope and Deliverables

Phase A established the full foundational layer of the OpenCoulomb project: project scaffold, developer tooling, CI pipeline, physical constants, all domain type definitions, the `.inp` file parser, and comprehensive test coverage. No computation logic (Okada engine, CFS) is included — that is Phase B.

The primary deliverable of Phase A is a clean, type-safe, well-tested Python package that can:

1. Read any Coulomb 3.4 `.inp` file from disk
2. Parse it into a validated `CoulombModel` aggregate
3. Expose all domain types as frozen, immutable dataclasses
4. Reject malformed input with structured errors carrying file/line context

---

## Project Structure Created

```
opencoulomb/                        # Repository root
├── src/
│   └── opencoulomb/                # Installable package (src layout)
│       ├── __init__.py             # Public re-exports
│       ├── __main__.py             # python -m opencoulomb entry point
│       ├── _constants.py           # Physical constants and defaults
│       ├── exceptions.py           # Exception hierarchy
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py             # Click CLI placeholder
│       ├── core/
│       │   └── __init__.py         # Phase B: Okada engine (placeholder)
│       ├── io/
│       │   ├── __init__.py         # Re-exports read_inp, parse_inp_string
│       │   └── inp_parser.py       # State machine parser (569 lines)
│       ├── types/
│       │   ├── __init__.py         # Re-exports all domain types
│       │   ├── fault.py            # FaultElement, Kode
│       │   ├── grid.py             # GridSpec
│       │   ├── material.py         # MaterialProperties
│       │   ├── model.py            # CoulombModel (aggregate root)
│       │   ├── result.py           # StressResult, CoulombResult, ElementResult
│       │   ├── section.py          # CrossSectionSpec, CrossSectionResult
│       │   └── stress.py           # PrincipalStress, RegionalStress, StressTensorComponents
│       └── viz/
│           └── __init__.py         # Phase D: visualization (placeholder)
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   │   └── inp_files/
│   │       ├── simple_strike_slip.inp      # Minimal synthetic file
│   │       ├── thrust_with_section.inp     # Synthetic with cross-section
│   │       ├── real/                       # 7 real files from kmaterna/elastic_stresses_py
│   │       ├── coulomb34/                  # 20 files from coulomb3402.zip distribution
│   │       └── usgs_finite_fault/          # 3 USGS finite-fault archive files
│   ├── integration/
│   │   └── test_inp_parsing.py     # 263 integration/real-file tests
│   ├── unit/
│   │   └── test_types.py           # 149 unit tests with Hypothesis
│   ├── performance/                # Phase B placeholder
│   └── validation/                 # Phase B placeholder
├── .github/
│   └── workflows/
│       └── ci.yml                  # 3 OS x 4 Python matrix
├── .pre-commit-config.yaml         # ruff + mypy hooks
├── pyproject.toml                  # hatchling build, all tool config
├── LICENSE                         # Apache 2.0
└── README.md
```

---

## Key Architectural Decisions

### Frozen Dataclasses as Domain Objects

All domain types use `@dataclass(frozen=True, slots=True)`. This was chosen to:

- Make objects hashable and safe to use in sets/dict keys
- Prevent accidental mutation across pipeline stages
- Enforce invariants at construction time via `__post_init__`
- Enable `__slots__` for memory efficiency on large grids

The only exception is `CoulombModel` (the aggregate root) and result types (`StressResult`, `CoulombResult`, `CrossSectionResult`), which are mutable (`frozen=False`) because they hold NumPy arrays — which cannot be hashed or made deeply immutable anyway, and are expected to be built up incrementally by the computation pipeline.

### State Machine Parser

The `.inp` parser uses an explicit finite state machine rather than regex-over-the-whole-file or a grammar-based approach. States transition linearly:

```
START → TITLE_LINE2 → PARAMS → FAULTS_HEADER → SOURCE_FAULTS
      → RECEIVER_HEADER → RECEIVER_FAULTS → GRID → CROSS_SECTION
      → MAP_INFO → DONE
```

This was chosen because:

- The `.inp` format is strictly positional and section-ordered — a state machine maps cleanly to it
- Error reporting is precise: `ParseError` carries filename and line number
- Edge cases (missing sections, out-of-order headers, no receiver faults) are handled naturally per-state
- The format is not formally specified; the state machine can be extended state-by-state as new variants are encountered

### src Layout

The `src/opencoulomb/` layout (PEP 517/518 compliant) was adopted to:

- Prevent accidental imports from the repository root during development
- Ensure installed behavior matches the editable install (`pip install -e .`)
- Align with modern Python packaging standards (hatchling build backend)

### Physical Constants as Module-Level Constants

All magic numbers are centralized in `_constants.py`. Every default value (Poisson's ratio, Young's modulus, friction, etc.) is named and documented there. No raw literals appear in domain code.

---

## Module Reference

### `opencoulomb._constants`

Physical constants and defaults for the entire package.

| Constant | Value | Description |
|----------|-------|-------------|
| `DEFAULT_POISSON` | 0.25 | Poisson's ratio |
| `DEFAULT_YOUNG_BAR` | 8.0e5 | Young's modulus (bar; 1 bar = 0.1 MPa) |
| `DEFAULT_FRICTION` | 0.4 | Effective friction coefficient |
| `DEFAULT_DEPTH_KM` | 10.0 | Default computation depth (km) |
| `KM_TO_M` | 1000.0 | Unit conversion |
| `BAR_TO_PA` | 1.0e5 | Unit conversion |
| `SINGULARITY_THRESHOLD` | 1.0e-12 | Numerical stability guard |
| `DEG_TO_RAD` | π/180 | Angle conversion |
| `FREE_SURFACE_FACTOR` | 2.0 | Okada free-surface image correction |

---

### `opencoulomb.exceptions`

Structured exception hierarchy. All exceptions carry context.

```
OpenCoulombError (base)
├── InputError
│   ├── ParseError          # filename, line_number attributes
│   └── ValidationError
├── ComputationError
│   ├── SingularityError
│   └── ConvergenceError
└── OutputError
    ├── FormatError
    └── ConfigError
```

`ParseError` is the most frequently raised exception in Phase A. It attaches `filename` and `line_number` so the user can see exactly where parsing failed.

---

### `opencoulomb.types.fault` — `FaultElement`, `Kode`

`Kode` is an `IntEnum` encoding the fault type as used in the `.inp` file:

| Value | Name | slip_1 | slip_2 |
|-------|------|--------|--------|
| 100 | `STANDARD` | right-lateral | reverse |
| 200 | `TENSILE_RL` | tensile opening | right-lateral |
| 300 | `TENSILE_REV` | tensile opening | reverse |
| 400 | `POINT_SOURCE` | right-lateral | reverse (point) |
| 500 | `TENSILE_INFL` | tensile opening | inflation |

`FaultElement` is a frozen dataclass with 10 required fields (coordinates, slip, geometry) and 2 optional fields (`label`, `element_index`). Validation in `__post_init__` enforces:

- `0 <= dip <= 90`
- `top_depth >= 0`
- `bottom_depth > top_depth`

Computed properties: `strike_deg`, `rake_deg`, `length`, `width`, `center_x/y/depth`, `is_source`, `is_receiver`, `is_point_source`.

---

### `opencoulomb.types.grid` — `GridSpec`

Defines the horizontal computation grid. Validates that extents are positive and increments are non-zero. Computed properties: `n_x`, `n_y`, `n_points`.

---

### `opencoulomb.types.material` — `MaterialProperties`

Elastic half-space properties. Validates Poisson's ratio is in (0, 0.5), Young's modulus is positive, friction is non-negative. Computed properties: `alpha` (Okada medium constant), `shear_modulus`, `lame_lambda`.

---

### `opencoulomb.types.stress` — `PrincipalStress`, `RegionalStress`, `StressTensorComponents`

Three frozen dataclasses for stress representations:

- `PrincipalStress`: azimuth, dip, intensity, gradient for one principal axis
- `RegionalStress`: container for s1/s2/s3 axes
- `StressTensorComponents`: full 6-component Voigt tensor at a point (bar, geographic coordinates: x=East, y=North, z=Up)

---

### `opencoulomb.types.result` — `StressResult`, `CoulombResult`, `ElementResult`

Mutable dataclasses for computation output (hold NumPy arrays):

- `StressResult`: raw stress tensor + displacement at N observation points
- `CoulombResult`: CFS, shear, normal stress + receiver geometry + optional OOPs arrays; `cfs_grid()` reshapes to 2D
- `ElementResult`: CFS at M individual receiver fault element centers

---

### `opencoulomb.types.section` — `CrossSectionSpec`, `CrossSectionResult`

`CrossSectionSpec` (frozen): profile endpoints, depth range, vertical spacing.
`CrossSectionResult` (mutable): full 2D arrays of CFS, displacement, and stress tensor on the section grid.

---

### `opencoulomb.types.model` — `CoulombModel`

The aggregate root: everything needed to run a computation. Produced by the parser; consumed by the Phase B engine.

Key fields:
- `title`: two-line title string
- `material`: `MaterialProperties`
- `faults`: unified list (sources first, then receivers)
- `n_fixed`: index boundary separating sources from receivers
- `grid`: `GridSpec`
- `regional_stress`: optional `RegionalStress`
- `symmetry`, `x_sym`, `y_sym`: symmetry parameters

Properties: `source_faults`, `receiver_faults`, `n_sources`, `n_receivers`.

---

### `opencoulomb.io.inp_parser`

**Public API:**

```python
from opencoulomb.io import read_inp, parse_inp_string

model: CoulombModel = read_inp("path/to/file.inp")
model: CoulombModel = parse_inp_string(raw_text, filename="display_name.inp")
```

**Internal implementation:** `_InpParser` class with `_ParserState` enum. The parser processes one line at a time and dispatches to a state handler. Parameter extraction uses two compiled regexes:

- `_KV_RE`: extracts `KEY=VALUE` pairs from parameter lines, supports scientific notation and values without leading digit (`.250`)
- `_GRID_LINE_RE`: parses numbered grid/cross-section lines (`1 --- Start-x = -100.0`), using `-+` to handle variable-length dash separators

State transitions are documented inline. The parser accumulates intermediate state into private dicts and lists, then calls `_build_model()` at the end to assemble the `CoulombModel`.

Encoding: tries UTF-8 first, falls back to latin-1 for legacy Coulomb files.

---

## Test Coverage Results

```
Name                                Stmts   Miss Branch BrPart  Cover
----------------------------------------------------------------------
src/opencoulomb/_constants.py          20      0      0      0   100%
src/opencoulomb/exceptions.py          20      0      4      1    96%
src/opencoulomb/io/inp_parser.py      286     15     98     12    92%
src/opencoulomb/types/fault.py         69      0     10      0   100%
src/opencoulomb/types/grid.py          28      0      6      0   100%
src/opencoulomb/types/material.py      28      0      8      0   100%
src/opencoulomb/types/model.py         26      0      0      0   100%
src/opencoulomb/types/result.py        44      0      0      0   100%
src/opencoulomb/types/section.py       29      0      0      0   100%
src/opencoulomb/types/stress.py        20      0      0      0   100%
----------------------------------------------------------------------
TOTAL (core modules)                  570      15    126     13   ~95%
TOTAL (package incl. placeholders)    588      22    128     13   94.55%
----------------------------------------------------------------------
```

The CLI and `__main__.py` placeholders are at 0% (they contain no logic yet); this does not affect the 90% threshold. All active code is at 92–100%.

**Test distribution:**

| Suite | File | Tests | Focus |
|-------|------|-------|-------|
| Unit | `tests/unit/test_types.py` | 149 | Domain types + Hypothesis property tests |
| Integration | `tests/integration/test_inp_parsing.py` | 263 | Parser, including 111 real-file tests |
| **Total** | | **412** | **All passing** |

Hypothesis strategies used in unit tests: `st.floats`, `st.text`, `st.integers`, with explicit assume() guards for domain constraints.

---

## Real Data Validation

After the initial 10 tasks were complete (301 tests, 95% coverage), the parser was validated against 7 real Coulomb `.inp` files downloaded from the `kmaterna/elastic_stresses_py` repository. These files exposed 4 parser bugs that were not covered by synthetic test cases.

During the Phase A/B code review remediation, the parser was further validated against the full Coulomb 3.4 distribution (20 files from `coulomb3402.zip`) plus 3 USGS finite-fault `.inp` files. This exposed a 5th parser bug (see Bug 5 below). All 30 fixture files now parse and compute successfully.

### Bug 1: `_KV_RE` — Values Without Leading Digit

**Problem:** The original regex `(\d+\.?\d*|\.\d+)` required at least one digit before or after the decimal point but did not handle `.250` (value starts with `.` and has no leading digit before the decimal).

**Real file trigger:** Parameter lines like `PR= .250000`.

**Fix:** Changed alternation from `\d+\.?\d*` to `(?:\d+\.?\d*|\.\d+)` — the non-capturing group handles both `1.25` and `.250`.

### Bug 2: `_GRID_LINE_RE` — Variable-Length Dash Separators

**Problem:** The original regex matched exactly `---` (three dashes) as the separator between the index number and the parameter name. Real Coulomb files use long dash lines (20–30 dashes) like:

```
  1  ----------------------------  Start-x =     -127.2099991
```

**Fix:** Changed `---` to `-+` (one or more dashes).

### Bug 3: Size Parameters Section — Premature State Transition

**Problem:** Real Coulomb files include a "Size Parameters" section between "Grid Parameters" and "Cross Section" containing three numbered lines (index 1, 2, 3 — the same index range used by grid params). The parser was transitioning to `CROSS_SECTION` state on blank lines after grid params, then misidentifying the Size Parameters section.

**Fix:** Added explicit handling for `size parameters` keyword in `_on_grid`: stay in `GRID` state and skip. Guard `_grid_params` population with `idx <= 6 and idx not in self._grid_params` to ignore duplicate/overlapping indices from Size Parameters.

### Bug 4: XSYM/YSYM Aliases for Symmetry Parameters

**Problem:** Real files use `XSYM` and `YSYM` as parameter names in `.inp` files, but the parser was only looking for `XLIM`/`YLIM` (names derived from reading the Coulomb 3.4 documentation).

**Fix:** Added `XSYM`/`YSYM` as recognized aliases in `_build_model()`, mapping them to `x_sym`/`y_sym` on `CoulombModel`.

### Bug 5: Blank-Line Grid State Transition (found during A/B review remediation)

**Problem:** USGS finite-fault `.inp` files include a blank line between the "Grid Parameters" and "Size Parameters" sections. The parser's `_on_grid` handler was transitioning to CROSS_SECTION state on any blank line when grid params were populated. This caused the Size Parameters numbered lines (indices 1-3) to be misinterpreted as cross-section data, producing `Missing cross-section parameters: [4, 5, 6, 7]`.

**Real file trigger:** All 3 USGS finite-fault files (layout: Grid params → blank → Size Parameters → blank → Cross Section).

**Fix:** Removed the blank-line transition from `_on_grid`. The handler now stays in GRID state across blank lines and only transitions on explicit "Cross section" or "Map info" keywords. The existing guard (`idx <= 6 and idx not in self._grid_params`) already prevented Size Parameters from overwriting grid params.

---

## Known Limitations and TODOs

The following items are known to be incomplete at the end of Phase A. They are not defects — they are intentionally deferred to later phases.

| Item | Deferred To | Notes |
|------|-------------|-------|
| Okada engine (`core/`) | Phase B | `core/__init__.py` is a placeholder only |
| CFS computation | Phase B | No stress math exists yet |
| CLI (`cli/main.py`) | Phase D | Placeholder; `opencoulomb --help` will fail gracefully |
| Visualization (`viz/`) | Phase D | Package exists but is empty |
| Cross-section `z_inc` validation | Phase A cleanup | `CrossSectionSpec` does not yet validate `z_inc > 0` or `depth_max > depth_min` |
| Okada reference values | Phase B | Needed to write Task 014 regression tests |
| Coulomb 3.4 `.inp` reference outputs | Phase B | Needed for integration accuracy tests |
| `_on_stress` state handler | Phase B | State defined, handler is a no-op pass; stress extracted from `_param_text` |

**Outstanding blockers (from project plan) — RESOLVED during Phase A/B review:**

- ~~Obtain Coulomb 3.4 compiled binary + example files~~ — Downloaded coulomb3402.zip, extracted all 20 example .inp files
- ~~Transcribe Okada (1992) Table 2 exact reference values~~ — Full Table 2 validated (12 components × 3 slip types) at ≤1e-10 relative error

---

## Quality Gate Summary

| Criterion | Target | Achieved |
|-----------|--------|----------|
| Tests passing | 100% | 412/412 |
| Total coverage | ≥ 90% | 94.55% |
| types/ coverage | ≥ 95% | 100% |
| io/ coverage | ≥ 90% | 92% |
| Ruff lint violations | 0 | 0 |
| Real file validation | Pass 7 files | Pass (after 4 bug fixes) |
| Coulomb 3.4 distribution | 20/20 files | Pass (after 5th bug fix) |
| USGS finite-fault files | 3/3 files | Pass |

Phase A quality gate: **PASSED**.
