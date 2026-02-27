# Phase A/B Code Review Report

Date: 2026-02-27  
Scope: Implementation aligned to `.claude/plans/opencoulomb-implementation-2026-02-27/` (Phase A + Phase B)

## Findings (ordered by severity)

### 1) High — Type-check quality gate is currently failing
- File references:
  - `.github/workflows/ci.yml:49`
  - `pyproject.toml:69`
  - `src/opencoulomb/core/okada.py:97`
  - `src/opencoulomb/types/result.py:121`
  - `src/opencoulomb/io/inp_parser.py:197`
- Impact:
  - The plan’s Phase A quality gate requires mypy to pass, but the current implementation fails strict typing, so CI will fail at the type-check stage.
- Evidence:
  - Local run: `mypy src` reported 33 errors across 3 files (notably unparameterized `NDArray`, untyped call site in parser dispatch, and untyped `list` in `ElementResult`).
  - The CI workflow runs `mypy src/opencoulomb/`, so this failure path is active.
- Minimal remediation:
  - Parameterize `NDArray` annotations in `core/okada.py`.
  - Replace `elements: list` with a typed collection (`list[FaultElement]` or a forward-ref equivalent) in `types/result.py`.
  - Make parser dispatch type-safe (or refactor to avoid untyped callable dispatch).

### 2) High — `compute_grid()` ignores all receivers except the first, creating order-dependent CFS output
- File references:
  - `src/opencoulomb/core/pipeline.py:97`
  - `src/opencoulomb/core/pipeline.py:100`
  - `src/opencoulomb/core/pipeline.py:119`
  - `.claude/plans/opencoulomb-implementation-2026-02-27/plan.md:46`
  - `.claude/plans/opencoulomb-implementation-2026-02-27/plan.md:165`
- Impact:
  - For models with multiple receiver faults, grid CFS is computed from only `receivers[0]`. Reordering receiver lines changes the output field, which is a correctness risk and does not meet “specified receiver faults” behavior.
- Evidence:
  - The implementation explicitly selects `receivers[0]`.
  - Reproduced locally by swapping receiver order in otherwise identical input:
    - First run receiver orientation: `(strike=90.0, dip=45.0)`
    - Second run receiver orientation: `(strike=0.0, dip=80.0)`
    - `max abs cfs diff`: `26.14014510838698` bar
- Minimal remediation:
  - Support explicit receiver selection for grid CFS, or compute per-receiver CFS outputs.
  - Add a deterministic policy and test coverage for multi-receiver grids.

### 3) High — Phase B numerical validation gates are not actually enforced by tests
- File references:
  - `.claude/plans/opencoulomb-implementation-2026-02-27/plan.md:71`
  - `.claude/plans/opencoulomb-implementation-2026-02-27/plan.md:167`
  - `.claude/plans/opencoulomb-implementation-2026-02-27/execution.md:92`
  - `.claude/plans/opencoulomb-implementation-2026-02-27/execution.md:112`
  - `tests/unit/test_okada.py:63`
  - `tests/unit/test_okada.py:70`
  - `tests/unit/test_okada.py:77`
  - `tests/integration/test_pipeline.py:209`
- Impact:
  - The current test suite can pass while materially wrong scientific results slip through, because it does not enforce the plan’s core numerical thresholds.
- Evidence:
  - Plan requires Okada validation at `<= 1e-10 relative error` and Coulomb comparison at `< 1e-6 bar`.
  - Current Okada assertions use absolute tolerances of `1e-5` on three displacement components only.
  - Pipeline integration tests for real files mostly assert finite/non-NaN outputs, not reference agreement against Coulomb 3.4.
- Minimal remediation:
  - Add reference fixtures and relative-error assertions for Okada validation.
  - Add regression fixtures for Coulomb 3.4 comparisons and enforce the `< 1e-6 bar` criterion in tests.

### 4) Medium — Parser compatibility target (~20 example files) is under-tested (currently 7)
- File references:
  - `.claude/plans/opencoulomb-implementation-2026-02-27/plan.md:72`
  - `.claude/plans/opencoulomb-implementation-2026-02-27/plan.md:153`
  - `tests/integration/test_pipeline.py:199`
- Impact:
  - Claimed compatibility coverage is significantly broader than current real-file test coverage, increasing risk of format regressions on untested `.inp` variants.
- Evidence:
  - Real fixture set currently enumerates 7 files in integration tests.
  - Local fixture count in `tests/fixtures/inp_files/real`: 7.
- Minimal remediation:
  - Expand fixture corpus to the full planned set and run parser + compute integration over all of them.

### 5) Medium — `compute_grid()` crashes on validly parsed no-fault models
- File references:
  - `src/opencoulomb/core/pipeline.py:109`
  - `src/opencoulomb/core/pipeline.py:111`
- Impact:
  - A syntactically valid model with zero sources and zero receivers raises `IndexError` instead of a domain-specific, actionable error.
- Evidence:
  - Local reproduction with a parsed model where `len(model.faults) == 0`: `compute_grid()` raised `IndexError: list index out of range`.
- Minimal remediation:
  - Add precondition checks in `compute_grid()` (or parser-level validation) and raise `ValidationError`/`ComputationError` with a clear message.

## Open Questions / Assumptions
- Should grid CFS be computed for:
  - a single explicitly selected receiver,
  - all receivers (stacked output), or
  - an aggregate over receivers?
- Are zero-fault models considered valid inputs, or should parser/model validation reject them?
- Is the project accepting temporary deferral of strict mypy compliance, or should Phase A be considered incomplete until type checks pass?

## Brief Summary
- Runtime tests and coverage are strong (`566` tests passing, `97.71%` coverage), but several Phase A/B acceptance gates in the plan are not yet satisfied.
- Highest risks are correctness/validation gaps (receiver handling semantics and missing numeric reference assertions) plus an active CI type-check failure.
