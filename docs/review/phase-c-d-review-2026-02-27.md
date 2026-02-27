# Phase C/D Code Review Report

Date: 2026-02-27  
Scope: Phase C (Tasks 021-024) and Phase D (Tasks 025-036) implementation against `.claude/plans/opencoulomb-implementation-2026-02-27/`

## Findings (ordered by severity)

### 1) High — Phase D type-check gate is failing (mypy errors in viz/export path)
- File references:
  - `src/opencoulomb/viz/export.py:43`
  - `src/opencoulomb/viz/maps.py:42`
  - `src/opencoulomb/viz/maps.py:53`
  - `src/opencoulomb/viz/displacement.py:42`
  - `src/opencoulomb/viz/displacement.py:54`
  - `src/opencoulomb/viz/displacement.py:58`
  - `src/opencoulomb/viz/sections.py:37`
  - `src/opencoulomb/viz/sections.py:51`
  - `src/opencoulomb/viz/faults.py:28`
- Impact:
  - The strict type-check quality gate is not passing for current Phase D modules, so CI quality enforcement is broken.
- Evidence:
  - Local run `mypy src` failed with 9 errors in 5 files (generic `dict` typing, `Figure|SubFigure|None` assignment incompatibilities, and `add_colorbar` type mismatch for `QuadContourSet`/`Quiver`).
- Minimal remediation:
  - Widen `add_colorbar` input typing to accept all `ScalarMappable`-like objects used by contour/quiver.
  - Normalize `ax.get_figure()` handling and typing in viz functions.
  - Add concrete type parameters for dicts.

### 2) High — Planned CLI surface for Phase D is incomplete (`validate`/`convert` missing)
- File references:
  - `.claude/plans/opencoulomb-implementation-2026-02-27/plan.md:192`
  - `src/opencoulomb/cli/main.py:18`
  - `src/opencoulomb/cli/main.py:19`
  - `src/opencoulomb/cli/main.py:20`
- Impact:
  - Task 033 explicitly requires `info/validate/convert` utilities, but only `info` is implemented and wired. User-facing Phase D scope is functionally incomplete.
- Evidence:
  - CLI registration includes only `compute`, `plot`, and `info`.
  - `python -m opencoulomb --help` lists only those three commands.
- Minimal remediation:
  - Implement `validate` and `convert` commands (or adjust plan/scope docs if intentionally deferred).
  - Add corresponding CLI tests under `tests/unit/test_cli.py`.

### 3) High — Phase C acceptance criteria (Coulomb 3.4 reference validation) are not enforced
- File references:
  - `.claude/plans/opencoulomb-implementation-2026-02-27/execution.md:138`
  - `.claude/plans/opencoulomb-implementation-2026-02-27/execution.md:139`
  - `.claude/plans/opencoulomb-implementation-2026-02-27/plan.md:175`
  - `.claude/plans/opencoulomb-implementation-2026-02-27/plan.md:176`
  - `tests/unit/test_oops.py:196`
  - `tests/unit/test_cross_section.py:88`
- Impact:
  - OOP and cross-section tests can pass without demonstrating compatibility against Coulomb 3.4 reference outputs, leaving the primary scientific correctness gate unverified.
- Evidence:
  - Current tests are mostly synthetic/shape/finite checks.
  - No tests reference Coulomb OOP outputs or `dcff_section.cou` reference comparisons for tolerance-based assertions.
- Minimal remediation:
  - Add reference fixtures and validation tests for:
    - OOP strike/dip/CFS comparisons vs Coulomb 3.4.
    - Cross-section output comparisons vs `dcff_section.cou`.

### 4) Medium — Cross-section spec validation is missing; invalid specs fail with raw runtime errors
- File references:
  - `src/opencoulomb/types/section.py:14`
  - `src/opencoulomb/core/pipeline.py:503`
  - `src/opencoulomb/core/pipeline.py:504`
- Impact:
  - Invalid section settings (`z_inc <= 0`, inverted depth ranges) are accepted by the data model and can crash at runtime with low-quality errors.
- Evidence:
  - `CrossSectionSpec` has no `__post_init__` validation.
  - Local reproduction with `z_inc=0` raised `ZeroDivisionError` in `compute_cross_section`.
- Minimal remediation:
  - Add `CrossSectionSpec` validation for:
    - `depth_max > depth_min`
    - `z_inc > 0`
    - non-negative depth bounds (if required by model conventions).
  - Convert runtime math failures into `ValidationError`/`ComputationError`.

### 5) Medium — Numerical runtime warnings occur in Phase C tests and are not treated as failures
- File references:
  - `src/opencoulomb/core/okada.py:233`
  - `src/opencoulomb/core/okada.py:240`
  - `src/opencoulomb/core/okada.py:243`
  - `src/opencoulomb/core/stress.py:73`
  - `src/opencoulomb/core/stress.py:76`
- Impact:
  - Silent divide-by-zero/invalid operations can mask unstable edge-case numerics, especially in deep/section workflows.
- Evidence:
  - Targeted test run produced warnings:
    - divide-by-zero / invalid value warnings in Okada + stress conversions.
  - Tests still pass, so this class of numerical warning is currently tolerated.
- Minimal remediation:
  - Add singularity guards or controlled `np.errstate` handling with explicit sanitization.
  - Promote critical runtime warnings to test failures for core numeric paths.

### 6) Medium — `write_fault_surface_dat()` behavior does not match its own format contract
- File references:
  - `src/opencoulomb/io/dat_writer.py:58`
  - `src/opencoulomb/io/dat_writer.py:59`
  - `src/opencoulomb/io/dat_writer.py:79`
  - `src/opencoulomb/io/dat_writer.py:80`
- Impact:
  - Function claims to emit 4-corner fault polygons in GMT multi-segment format, but writes only a 2-point trace segment. Downstream mapping users expecting polygons may get incorrect geometry.
- Evidence:
  - Docstring states “polygon defined by four corners.”
  - Implementation writes only start/end surface trace points.
- Minimal remediation:
  - Either implement full polygon corner export or correct function/doc naming and expectations to “trace segments.”

## Open Questions / Assumptions
- Are `validate` and `convert` intentionally deferred to a later phase, or should they be considered blocking for Phase D completion?
- Should numerical runtime warnings in core compute paths be treated as CI failures?
- For cross-sections, should horizontal sampling use `x_inc` unconditionally, or adapt to profile direction / both grid increments?

## Brief Summary
- Phase C/D have substantial implementation and passing runtime tests, but three key quality gaps remain: type-check failures in Phase D code, missing planned CLI utilities, and missing Coulomb-reference validation for OOP/cross-section correctness.
