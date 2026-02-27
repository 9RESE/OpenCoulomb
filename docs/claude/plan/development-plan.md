# OpenCoulomb Development Plan

**Phase 4 -- Development Planning**
**Version**: 1.0
**Date**: 2026-02-27
**Status**: Draft
**Derived From**: Phase 1 Research, Phase 2 Specification, Phase 3 Architecture

---

## Table of Contents

1. [Development Phases and Milestones](#1-development-phases-and-milestones)
2. [Detailed Task Breakdown](#2-detailed-task-breakdown)
3. [Documentation Plan](#3-documentation-plan)
4. [Testing Strategy per Phase](#4-testing-strategy-per-phase)
5. [Quality Gates](#5-quality-gates)
6. [Risk Mitigation Actions](#6-risk-mitigation-actions)
7. [Documentation Directory Structure](#7-documentation-directory-structure)
8. [Continuous Documentation Updates](#8-continuous-documentation-updates)

---

## 1. Development Phases and Milestones

The 13 milestones from the specification are grouped into 5 development phases. Each phase produces a working, testable increment. The phases map to the release strategy: 0.1.0-alpha, 0.2.0-alpha, 0.5.0-beta, and 1.0.0.

### Phase A: Foundation (M1 + M4)

**Goal**: Repository scaffold and input parsing. Establish the project skeleton, CI pipeline, coding standards, and the .inp parser so that all subsequent phases can read real Coulomb input files.

**Milestones**: M1 (Project scaffold), M4 (.inp parser)

**Deliverables**:
- Repository with `pyproject.toml`, src layout, CI/CD, linting, type checking
- All data model types (`types/` package) implemented and tested
- Complete `.inp` file parser that handles all Coulomb 3.4 example files
- Exception hierarchy
- Constants module
- Project CLAUDE.md and initial LLM context files

**Dependencies**: None (starting point)

**Done Criteria**:
- `pip install -e .` succeeds
- `ruff check` and `mypy` pass with zero errors
- All ~20 Coulomb 3.4 example `.inp` files parse without error
- Data model types have 100% test coverage
- Parser has >= 90% test coverage
- Project CLAUDE.md exists and is accurate

**Complexity**: **M** (Medium) -- straightforward but requires careful fixed-width parsing

---

### Phase B: Core Computation Engine (M2 + M3 + M5)

**Goal**: The computational heart of OpenCoulomb. Implement Okada DC3D, stress computation, coordinate transforms, and CFS calculation. This is the highest-risk phase requiring numerical validation.

**Milestones**: M2 (Okada DC3D engine), M3 (Stress computation), M5 (CFS calculation)

**Deliverables**:
- Vectorized DC3D and DC3D0 implementation
- Hooke's law stress conversion with 0.001 unit factor
- Tensor rotation (Bond matrix)
- Coordinate transforms (geographic to fault-local and back)
- CFS calculation on specified receiver faults
- Computation pipeline orchestrator (`pipeline.py`)
- Validation Level 1 (Okada vs Fortran) and Level 2 (CFS vs Coulomb 3.4) passing

**Dependencies**: Phase A (needs data model types and parser for integration tests)

**Done Criteria**:
- DC3D matches Okada (1992) Table 2 values to relative error < 1e-10
- CFS on all example files matches Coulomb 3.4 to < 1e-6 bar
- 100x100 grid with 10 faults computes in < 10 seconds
- Core modules have >= 95% test coverage
- All validation Level 1 and Level 2 tests pass

**Complexity**: **XL** (Extra Large) -- most critical and complex phase; numerical accuracy is paramount

**Release**: 0.1.0-alpha after this phase

---

### Phase C: Extended Computation (M6 + M7)

**Goal**: Add optimally oriented planes and cross-section computation, completing all computation capabilities needed for Tier 1.

**Milestones**: M6 (OOPs), M7 (Cross-section)

**Deliverables**:
- Regional stress field computation
- OOP solver (eigendecomposition + Mohr-Coulomb)
- Cross-section profile computation
- OOP and cross-section validated against Coulomb 3.4

**Dependencies**: Phase B (needs full stress computation pipeline)

**Done Criteria**:
- OOP strike/dip matches Coulomb 3.4 for all OOP example files
- Cross-section values match `dcff_section.cou` reference outputs
- OOP and cross-section modules have >= 90% test coverage

**Complexity**: **L** (Large) -- OOP eigendecomposition is moderately complex; cross-section is straightforward

**Release**: 0.2.0-alpha after this phase

---

### Phase D: User-Facing Layer (M8 + M9 + M10)

**Goal**: Make the computation accessible through visualization, CLI, and output files. After this phase, OpenCoulomb is a usable tool.

**Milestones**: M8 (Visualization), M9 (CLI), M10 (Output files)

**Deliverables**:
- 2D CFS contour maps with fault traces
- Cross-section plots
- Displacement vector (quiver) plots
- Figure export (PNG, PDF, SVG)
- Complete Click-based CLI (`opencoulomb compute`, `opencoulomb plot`, `opencoulomb info`)
- All Tier 1 output formats: `dcff.cou`, `dcff_section.cou`, `coulomb_out.dat`, `gmt_fault_surface.dat`, CSV
- Colormap configuration (diverging, symmetric, Coulomb conventions)

**Dependencies**: Phase C (needs all computation modules)

**Done Criteria**:
- `opencoulomb compute example.inp` produces correct output files
- `opencoulomb compute example.inp --plot map` produces a CFS contour map
- All Tier 1 CLI commands functional with `--help`
- Output file formats match Coulomb 3.4 column layout
- Visualization tests pass (image comparison or smoke tests)
- CLI and I/O modules have >= 85% test coverage

**Complexity**: **L** (Large) -- broad scope across three milestones but individually moderate tasks

**Release**: 0.5.0-beta after this phase

---

### Phase E: Validation, Packaging, and Documentation (M11 + M12 + M13)

**Goal**: Harden the software for public release. Full validation suite, cross-platform packaging, and comprehensive documentation for humans and LLMs.

**Milestones**: M11 (Validation), M12 (Packaging), M13 (Documentation)

**Deliverables**:
- Full 6-level validation suite passing
- Validation report generation script
- Cross-platform CI (Ubuntu, macOS, Windows; Python 3.10-3.13)
- PyPI package (`pip install opencoulomb`)
- conda-forge recipe (or feedstock PR)
- Docker image
- Complete technical documentation (Arc42)
- Complete human user documentation (Diataxis: tutorials, how-to, reference, explanation)
- Complete LLM-optimized documentation (CLAUDE.md, CONTEXT.md, skills, structured references)
- CONTRIBUTING.md, CHANGELOG.md

**Dependencies**: Phase D (needs working CLI and all features)

**Done Criteria**:
- All 6 validation levels pass on all three platforms
- `pip install opencoulomb` installs cleanly on Python 3.10+ on all platforms
- `opencoulomb --version` works after pip install
- Documentation site builds without errors
- All public functions have docstrings
- All three documentation types (technical, human, LLM) are complete
- Performance benchmarks meet targets

**Complexity**: **XL** (Extra Large) -- validation is critical; documentation is extensive

**Release**: 1.0.0 after this phase

---

### Phase Summary Table

| Phase | Milestones | Complexity | Depends On | Release |
|-------|-----------|------------|------------|---------|
| **A: Foundation** | M1, M4 | M | -- | -- |
| **B: Core Engine** | M2, M3, M5 | XL | A | 0.1.0-alpha |
| **C: Extended Computation** | M6, M7 | L | B | 0.2.0-alpha |
| **D: User-Facing** | M8, M9, M10 | L | C | 0.5.0-beta |
| **E: Release** | M11, M12, M13 | XL | D | 1.0.0 |

---

## 2. Detailed Task Breakdown

### M1: Project Scaffold

#### M1-T01: Initialize repository and pyproject.toml

**Module**: `pyproject.toml`, repository root
**Description**: Create the repository with PEP 621 `pyproject.toml` using hatchling as the build backend. Include all metadata (name, version, description, license, classifiers, Python requirement, core dependencies, optional dependency groups, tool configurations for pytest, ruff, mypy, coverage). Create `LICENSE` (Apache 2.0), `.gitignore`, and `README.md` stub.
**Inputs**: Dependency list from architecture doc Section 12
**Outputs**: Installable package skeleton (`pip install -e .` works)
**Tests**: `test_package_installs` (import opencoulomb succeeds, `__version__` is "0.1.0")
**Dependencies**: None
**Complexity**: S

#### M1-T02: Create source package directory structure

**Module**: `src/opencoulomb/` (all `__init__.py` files)
**Description**: Create the full directory tree: `core/`, `types/`, `io/`, `viz/`, `cli/`, `gui/`, `web/`. Each gets an `__init__.py`. The root `__init__.py` exposes `__version__`. Create `__main__.py` for `python -m opencoulomb` support. Create `_constants.py` with all physical constants and defaults. Create `exceptions.py` with the full exception hierarchy.
**Inputs**: Architecture doc Section 2.1 (directory layout)
**Outputs**: Empty but importable package structure
**Tests**: `test_import_subpackages` (all subpackage imports succeed)
**Dependencies**: M1-T01
**Complexity**: S

#### M1-T03: Configure CI/CD pipeline

**Module**: `.github/workflows/test.yml`, `.github/workflows/lint.yml`
**Description**: Set up GitHub Actions workflows: (1) test workflow running pytest on matrix of OS (ubuntu, macos, windows) x Python (3.10, 3.11, 3.12, 3.13), (2) lint workflow running ruff check and mypy. Add pre-commit configuration (`.pre-commit-config.yaml`) with ruff and mypy hooks.
**Inputs**: Architecture doc Section 12.4 (CI matrix)
**Outputs**: Green CI on empty test suite
**Tests**: CI pipeline itself validates
**Dependencies**: M1-T01
**Complexity**: S

#### M1-T04: Configure development tooling

**Module**: `ruff.toml` or `pyproject.toml` `[tool.ruff]`, `mypy` config
**Description**: Configure ruff (line-length 88, target Python 3.10, select rules E/F/I/N/W/UP/B/SIM/NPY), mypy (strict mode), and pytest (testpaths, markers for benchmark/slow/validation). Create `conftest.py` with shared fixtures path pointing to `tests/fixtures/`.
**Inputs**: Architecture doc Section 12
**Outputs**: `ruff check src/` and `mypy src/` pass
**Tests**: Linting and type checking green
**Dependencies**: M1-T02
**Complexity**: S

#### M1-T05: Create test directory structure and conftest

**Module**: `tests/` directory tree
**Description**: Create `tests/unit/`, `tests/integration/`, `tests/validation/`, `tests/performance/`, `tests/fixtures/` (with subdirs `inp_files/`, `reference_outputs/`, `okada_reference/`). Create `tests/conftest.py` with a `fixtures_dir` fixture returning the absolute path to `tests/fixtures/`. Add a placeholder test in each subdirectory.
**Inputs**: Architecture doc Section 2.1
**Outputs**: `pytest` discovers and runs placeholder tests
**Tests**: `pytest --collect-only` shows tests in all subdirectories
**Dependencies**: M1-T02
**Complexity**: S

#### M1-T06: Implement MaterialProperties dataclass

**Module**: `src/opencoulomb/types/material.py`
**Description**: Implement the `MaterialProperties` frozen dataclass with fields: `poisson` (default 0.25), `young` (default 8.0e5), `friction` (default 0.4), `depth` (default 10.0). Include `__post_init__` validation (Poisson in (0, 0.5), Young > 0, friction >= 0, depth >= 0). Add computed properties: `alpha`, `shear_modulus`, `lame_lambda`.
**Inputs**: Architecture doc Section 4.1
**Outputs**: Validated, immutable material properties container
**Tests**: `test_material_defaults`, `test_material_custom`, `test_material_validation_poisson`, `test_material_validation_young`, `test_material_alpha`, `test_material_shear_modulus`, `test_material_lame_lambda`
**Dependencies**: M1-T02 (needs `_constants.py` and `exceptions.py`)
**Complexity**: S

#### M1-T07: Implement Kode enum and FaultElement dataclass

**Module**: `src/opencoulomb/types/fault.py`
**Description**: Implement `Kode` IntEnum (STANDARD=100, TENSILE_RL=200, TENSILE_REV=300, POINT_SOURCE=400, TENSILE_INFL=500). Implement `FaultElement` frozen dataclass with all 12 fields per architecture doc Section 4.2. Include `__post_init__` validation (dip 0-90, top_depth >= 0, bottom_depth > top_depth). Add computed properties: `is_source`, `is_receiver`, `is_point_source`, `strike_deg`, `rake_deg`.
**Inputs**: Architecture doc Section 4.2
**Outputs**: Validated fault element container with derived geometry properties
**Tests**: `test_kode_values`, `test_fault_element_creation`, `test_fault_validation_dip`, `test_fault_validation_depth`, `test_is_source_with_slip`, `test_is_receiver_zero_slip`, `test_strike_deg_computation`, `test_rake_deg_standard`
**Dependencies**: M1-T06
**Complexity**: S

#### M1-T08: Implement GridSpec dataclass

**Module**: `src/opencoulomb/types/grid.py`
**Description**: Implement `GridSpec` frozen dataclass with fields: `start_x`, `start_y`, `finish_x`, `finish_y`, `x_inc`, `y_inc`, `depth` (default 10.0). Include validation (finish > start, increments > 0). Add computed properties: `n_x`, `n_y`, `n_points`.
**Inputs**: Architecture doc Section 4.3
**Outputs**: Validated grid specification container
**Tests**: `test_grid_creation`, `test_grid_validation`, `test_grid_n_points`, `test_grid_n_x_n_y`
**Dependencies**: M1-T02
**Complexity**: S

#### M1-T09: Implement RegionalStress and StressTensor types

**Module**: `src/opencoulomb/types/stress.py`
**Description**: Implement `PrincipalStress` frozen dataclass (direction, dip, intensity, gradient). Implement `RegionalStress` frozen dataclass (s1, s2, s3 as PrincipalStress). Implement `StressTensorComponents` frozen dataclass (sxx, syy, szz, syz, sxz, sxy).
**Inputs**: Architecture doc Section 4.4
**Outputs**: Regional stress and tensor containers
**Tests**: `test_principal_stress_creation`, `test_regional_stress_creation`, `test_stress_tensor_components`
**Dependencies**: M1-T02
**Complexity**: S

#### M1-T10: Implement result types (StressResult, CoulombResult, ElementResult, CrossSectionResult)

**Module**: `src/opencoulomb/types/result.py`, `src/opencoulomb/types/section.py`
**Description**: Implement `StressResult` dataclass (x, y, z, ux, uy, uz, sxx-sxy arrays, n_points property). Implement `CoulombResult` dataclass (stress, cfs, shear, normal, receiver orientation, grid_shape, optional OOP fields, cfs_grid() and displacement_grid() methods). Implement `ElementResult`. Implement `CrossSectionSpec` and `CrossSectionResult` dataclasses.
**Inputs**: Architecture doc Sections 4.5, 4.7
**Outputs**: All result container types
**Tests**: `test_stress_result_creation`, `test_coulomb_result_cfs_grid`, `test_coulomb_result_displacement_grid`, `test_cross_section_spec`, `test_element_result`
**Dependencies**: M1-T06 through M1-T09
**Complexity**: S

#### M1-T11: Implement CoulombModel aggregate root

**Module**: `src/opencoulomb/types/model.py`
**Description**: Implement `CoulombModel` dataclass with fields: title, material, faults, grid, n_fixed, regional_stress (optional), symmetry, x_sym, y_sym. Add computed properties: `source_faults`, `receiver_faults`, `n_sources`, `n_receivers`.
**Inputs**: Architecture doc Section 4.6
**Outputs**: Top-level model container
**Tests**: `test_model_source_receiver_split`, `test_model_properties`, `test_model_empty_receivers`
**Dependencies**: M1-T06 through M1-T10
**Complexity**: S

#### M1-T12: Wire types package __init__.py re-exports

**Module**: `src/opencoulomb/types/__init__.py`
**Description**: Re-export all public types from the `types` package `__init__.py` for convenient imports: `from opencoulomb.types import CoulombModel, FaultElement, ...`
**Inputs**: All M1-T06 through M1-T11
**Outputs**: Clean public API surface for types
**Tests**: `test_types_reexports` (verify all types importable from `opencoulomb.types`)
**Dependencies**: M1-T06 through M1-T11
**Complexity**: S

---

### M4: .inp Parser

#### M4-T01: Obtain and commit Coulomb 3.4 example .inp files

**Module**: `tests/fixtures/inp_files/`
**Description**: Download `coulomb3402.zip` from the USGS S3 bucket, extract the `input_file/` directory, and commit all ~20 example `.inp` files to the test fixtures directory. Catalog each file with a brief description of its content (fault type, number of elements, features exercised).
**Inputs**: USGS Coulomb 3.4 download URL
**Outputs**: Test fixture files committed to repository
**Tests**: Files exist and are non-empty
**Dependencies**: M1-T05
**Complexity**: S

#### M4-T02: Implement .inp parser state machine skeleton

**Module**: `src/opencoulomb/io/inp_parser.py`
**Description**: Implement the state machine parser skeleton with states: TITLE, PARAMETERS, REGIONAL_STRESS, FAULT_HEADER, FAULT_ELEMENTS, GRID_HEADER, GRID_PARAMETERS, OPTIONAL_SECTIONS, DONE. The public function `parse_inp_file(path: str | Path) -> CoulombModel` opens the file and drives the state machine. Each state transition is a separate private method. Raise `ParseError` with filename and line number on any parse failure.
**Inputs**: Spec Section 4.1 (.inp format specification)
**Outputs**: Parser skeleton that can read and transition through states
**Tests**: `test_parser_reads_file`, `test_parser_error_on_missing_file`
**Dependencies**: M1-T11 (needs CoulombModel type)
**Complexity**: M

#### M4-T03: Implement header parameter parsing

**Module**: `src/opencoulomb/io/inp_parser.py`
**Description**: Parse the title lines (lines 1-2) and model parameters block: `#reg1`, `#reg2`, `#fixed`, `sym`, `PR1`, `PR2`, `DEPTH`, `E1`, `E2`, `XLIM`/`XSYM`, `YLIM`/`YSYM`, `FRIC`. Handle both scientific notation (`0.800000E+06`) and decimal formats. Create `MaterialProperties` from parsed values.
**Inputs**: Spec Section 4.1.2 (model parameters block format)
**Outputs**: Title string, n_fixed, symmetry flags, MaterialProperties
**Tests**: `test_parse_header_defaults`, `test_parse_header_custom_values`, `test_parse_header_scientific_notation`, `test_parse_header_missing_fric`
**Dependencies**: M4-T02
**Complexity**: M

#### M4-T04: Implement regional stress parameter parsing

**Module**: `src/opencoulomb/io/inp_parser.py`
**Description**: Parse the S1DR/S1DP/S1IN/S1GD, S2DR/S2DP/S2IN/S2GD, S3DR/S3DP/S3IN/S3GD parameters. Construct `RegionalStress` with three `PrincipalStress` instances. Handle the case where all regional stress values are zero (common) by setting `regional_stress = None`.
**Inputs**: Spec Section 4.1.3 (regional stress format)
**Outputs**: `RegionalStress` or `None`
**Tests**: `test_parse_regional_stress_present`, `test_parse_regional_stress_all_zero`, `test_parse_regional_stress_normal_regime`
**Dependencies**: M4-T03
**Complexity**: S

#### M4-T05: Implement fault element line parsing

**Module**: `src/opencoulomb/io/inp_parser.py`
**Description**: Parse individual fault element lines in fixed-width format. Extract: element number (int), x_start, y_start, x_fin, y_fin (float), kode (int), slip_1, slip_2 (float), dip (float), top_depth, bottom_depth (float), optional label (string). Handle whitespace variations (tabs, multiple spaces). Construct `FaultElement` for each line. Recognize and skip column header lines and blank separator lines.
**Inputs**: Spec Section 4.1.4 (fault element format)
**Outputs**: List of `FaultElement` instances
**Tests**: `test_parse_single_fault`, `test_parse_kode_100`, `test_parse_kode_400_point`, `test_parse_fault_with_label`, `test_parse_fault_without_label`, `test_skip_header_line`, `test_skip_blank_line`
**Dependencies**: M4-T04
**Complexity**: M

#### M4-T06: Implement source/receiver fault classification

**Module**: `src/opencoulomb/io/inp_parser.py`
**Description**: Use the `#fixed` parameter to split faults into source (indices 0 to n_fixed-1) and receiver (n_fixed onwards). Validate that source faults have non-zero slip and receivers have zero slip (warn but do not error if violated, since some edge cases exist).
**Inputs**: Spec Section 4.1.6
**Outputs**: Correct `n_fixed` value in `CoulombModel`
**Tests**: `test_source_receiver_split`, `test_fixed_boundary`, `test_all_sources_no_receivers`
**Dependencies**: M4-T05
**Complexity**: S

#### M4-T07: Implement grid parameter parsing

**Module**: `src/opencoulomb/io/inp_parser.py`
**Description**: Detect the "Grid Parameters" keyword line, then parse the 6 numbered parameter lines (Start-x, Start-y, Finish-x, Finish-y, x-increment, y-increment). Handle the `N  ---  Key = Value` format with regex. Construct `GridSpec`.
**Inputs**: Spec Section 4.1.7 (grid parameters format)
**Outputs**: `GridSpec` instance
**Tests**: `test_parse_grid_parameters`, `test_parse_grid_fine_spacing`, `test_parse_grid_large_area`
**Dependencies**: M4-T05
**Complexity**: S

#### M4-T08: Implement optional section parsing (cross-section, map info)

**Module**: `src/opencoulomb/io/inp_parser.py`
**Description**: After grid parameters, optionally parse: (1) Cross-section specification if "Cross Section" keyword found, (2) Map info block (lon/lat reference point) if present. Store cross-section as `CrossSectionSpec` (or None). Store map info as optional fields on the model.
**Inputs**: Spec Section 4.1.8
**Outputs**: Optional `CrossSectionSpec`, optional map reference point
**Tests**: `test_parse_with_cross_section`, `test_parse_without_cross_section`, `test_parse_with_map_info`
**Dependencies**: M4-T07
**Complexity**: S

#### M4-T09: Integration test -- parse all Coulomb 3.4 example files

**Module**: `tests/integration/test_inp_parsing.py`
**Description**: Parametrized test that reads every `.inp` file in `tests/fixtures/inp_files/` and verifies: (1) no parse error, (2) at least one fault element, (3) grid is valid, (4) material properties are physically reasonable. This is the critical acceptance test for the parser.
**Inputs**: All fixture `.inp` files
**Outputs**: All files parse successfully
**Tests**: Parametrized across all fixture files
**Dependencies**: M4-T01 through M4-T08
**Complexity**: M

#### M4-T10: Input validation and error reporting

**Module**: `src/opencoulomb/io/inp_parser.py`
**Description**: Add comprehensive validation: detect malformed lines with clear error messages including filename and line number, detect inconsistent n_fixed vs actual fault count, warn on unusual values (negative dip, zero grid spacing, etc.), validate KODE values. Implement a `validate_model(model: CoulombModel) -> list[str]` function that returns a list of warnings.
**Inputs**: Spec T1-INP-09
**Outputs**: Clear error messages and warnings
**Tests**: `test_parse_error_malformed_line`, `test_parse_error_bad_kode`, `test_validate_model_warnings`, `test_parse_error_missing_grid`
**Dependencies**: M4-T09
**Complexity**: S

---

### M2: Okada DC3D Engine

#### M2-T01: Obtain and commit Okada reference values

**Module**: `tests/fixtures/okada_reference/`
**Description**: Compile the Fortran DC3D code from NIED (or use the DC3D.f90 modern rewrite) and generate reference output for a comprehensive set of test points. Include: (1) all three slip components individually, (2) combined slip, (3) surface and depth observation points, (4) various dip angles (0, 30, 45, 60, 90), (5) point source DC3D0. Store as JSON or CSV files with full precision (16+ significant digits). Also transcribe Okada (1992) Table 2 values.
**Inputs**: NIED Fortran DC3D code, Okada (1992) paper
**Outputs**: Reference value files in `tests/fixtures/okada_reference/`
**Tests**: Files exist and contain expected test cases
**Dependencies**: M1-T05
**Complexity**: M

#### M2-T02: Implement _OkadaConstants namedtuple and _dccon0

**Module**: `src/opencoulomb/core/okada.py`
**Description**: Implement the `_OkadaConstants` NamedTuple with 12 fields (alp1-alp5, sd, cd, sdsd, cdcd, sdcd, s2d, c2d). Implement `_dccon0(alpha: float, dip: float) -> _OkadaConstants` that precomputes these from the medium constant alpha and dip angle.
**Inputs**: Architecture doc Section 3.1.3
**Outputs**: Constants data structure
**Tests**: `test_dccon0_standard_params` (alpha=2/3, dip=70), `test_dccon0_vertical_fault` (dip=90), `test_dccon0_horizontal` (dip=0), `test_dccon0_alpha_values`
**Dependencies**: M1-T02 (needs `_constants.py`)
**Complexity**: S

#### M2-T03: Implement _dccon1 and _dccon2 helper functions

**Module**: `src/opencoulomb/core/okada.py`
**Description**: Implement `_dccon1(x, y, d, sd, cd)` computing corner-specific intermediate parameters (p, q, s, t, etc.). Implement `_dccon2(xi, et, q, sd, cd, kxi, ket)` computing secondary parameters (r, r2, etc.) with singularity checks. All operations must be vectorized (inputs are arrays of shape (N,)).
**Inputs**: Okada (1992) paper, architecture doc Section 3.1.2
**Outputs**: Vectorized intermediate parameter functions
**Tests**: `test_dccon1_shape_preservation`, `test_dccon2_singularity_handling`, `test_dccon2_vectorized`
**Dependencies**: M2-T02
**Complexity**: M

#### M2-T04: Implement _ua (Part A: infinite medium term)

**Module**: `src/opencoulomb/core/okada.py`
**Description**: Implement `_ua(xi, et, q, disl1, disl2, disl3, consts)` returning 12 arrays (3 displacements + 9 gradients). This computes the Part A contributions (infinite medium analytical expressions) for all three dislocation types. All NumPy vectorized, no Python loops. Include singularity guards using `np.where` masks.
**Inputs**: Okada (1992) Equations for Part A
**Outputs**: 12-tuple of arrays shape (N,)
**Tests**: `test_ua_strike_slip_only`, `test_ua_dip_slip_only`, `test_ua_tensile_only`, `test_ua_vectorized_shape`
**Dependencies**: M2-T03
**Complexity**: L

#### M2-T05: Implement _ub (Part B: image source term)

**Module**: `src/opencoulomb/core/okada.py`
**Description**: Implement `_ub(xi, et, q, disl1, disl2, disl3, consts)` returning 12 arrays. Part B accounts for the image source due to the free surface. Same vectorization pattern as _ua.
**Inputs**: Okada (1992) Equations for Part B
**Outputs**: 12-tuple of arrays shape (N,)
**Tests**: `test_ub_strike_slip`, `test_ub_dip_slip`, `test_ub_tensile`, `test_ub_vectorized`
**Dependencies**: M2-T03
**Complexity**: L

#### M2-T06: Implement _uc (Part C: depth-dependent correction)

**Module**: `src/opencoulomb/core/okada.py`
**Description**: Implement `_uc(xi, et, q, z, disl1, disl2, disl3, consts)` returning 12 arrays. Part C provides depth-dependent correction terms. The `z` parameter is needed here (not in UA/UB). Handle the z=0 limiting case.
**Inputs**: Okada (1992) Equations for Part C
**Outputs**: 12-tuple of arrays shape (N,)
**Tests**: `test_uc_strike_slip`, `test_uc_depth_zero`, `test_uc_depth_nonzero`, `test_uc_vectorized`
**Dependencies**: M2-T03
**Complexity**: L

#### M2-T07: Implement dc3d (finite rectangular fault -- Chinnery summation)

**Module**: `src/opencoulomb/core/okada.py`
**Description**: Implement the public `dc3d()` function. For each of 4 rectangle corners (Chinnery's notation), call _dccon1, _dccon2, _ua, _ub, _uc, then sum with alternating signs: `f(x,p,q) = f(x,p) - f(x,p-W) - f(x-L,p) + f(x-L,p-W)`. Apply free-surface correction for z != 0. Return 12-tuple of displacements and gradients.
**Inputs**: Architecture doc Section 3.1.2 (call tree)
**Outputs**: Public `dc3d()` function matching the API in architecture doc Section 3.1.1
**Tests**: `test_dc3d_vs_okada_table2`, `test_dc3d_strike_slip_surface`, `test_dc3d_dip_slip_surface`, `test_dc3d_tensile_surface`, `test_dc3d_internal_point`, `test_dc3d_combined_slip`
**Dependencies**: M2-T04, M2-T05, M2-T06
**Complexity**: L

#### M2-T08: Implement _ua0, _ub0, _uc0 (point source sub-functions)

**Module**: `src/opencoulomb/core/okada.py`
**Description**: Implement the point source variants of UA, UB, UC. These use potency parameters (pot1-pot4) instead of dislocation components. Vectorized, with singularity handling.
**Inputs**: Okada (1992) DC3D0 equations
**Outputs**: Point source sub-functions
**Tests**: `test_ua0_vectorized`, `test_ub0_vectorized`, `test_uc0_vectorized`
**Dependencies**: M2-T03
**Complexity**: M

#### M2-T09: Implement dc3d0 (point source)

**Module**: `src/opencoulomb/core/okada.py`
**Description**: Implement the public `dc3d0()` function for point sources. Simpler than dc3d (no Chinnery summation, direct evaluation). Return same 12-tuple format.
**Inputs**: Architecture doc Section 3.1.1 (dc3d0 API)
**Outputs**: Public `dc3d0()` function
**Tests**: `test_dc3d0_strike_slip`, `test_dc3d0_dip_slip`, `test_dc3d0_inflation`, `test_dc3d0_matches_reference`
**Dependencies**: M2-T08
**Complexity**: M

#### M2-T10: Singularity handling comprehensive tests

**Module**: `src/opencoulomb/core/okada.py`, `tests/unit/test_okada.py`
**Description**: Implement and test all 5 singularity conditions documented in architecture doc Section 3.1.5: (1) R=0, (2) xi=0 and q=0, (3) R+xi=0, (4) R+et=0, (5) z=0. Ensure no NaN/Inf in output. Use `np.where` masks for vectorized singularity avoidance.
**Inputs**: Architecture doc Section 3.1.5
**Outputs**: Robust singularity handling
**Tests**: `test_singularity_on_fault_edge`, `test_singularity_on_corner`, `test_singularity_r_zero`, `test_no_nan_in_output`, `test_free_surface_observation`
**Dependencies**: M2-T07, M2-T09
**Complexity**: M

#### M2-T11: Validation -- DC3D against Fortran reference

**Module**: `tests/validation/test_vs_okada_reference.py`
**Description**: Parametrized validation test comparing dc3d() and dc3d0() outputs against the Fortran reference values from M2-T01. Test all 12 output components for each test case. Tolerance: relative error < 1e-10. This is Validation Level 1.
**Inputs**: Reference values from `tests/fixtures/okada_reference/`
**Outputs**: Full Okada validation passing
**Tests**: Parametrized across all reference test cases
**Dependencies**: M2-T01, M2-T07, M2-T09
**Complexity**: M

---

### M3: Stress Computation

#### M3-T01: Implement gradients_to_stress (Hooke's law)

**Module**: `src/opencoulomb/core/stress.py`
**Description**: Implement the `gradients_to_stress()` function that converts 9 displacement gradient components to 6 stress tensor components using Hooke's law for isotropic media. Apply the 0.001 unit factor (km/m conversion). Use the sk/gk formulation from architecture doc Section 3.2.2: `sk = E/(1+nu)`, `gk = nu/(1-2*nu)`.
**Inputs**: Architecture doc Section 3.2.1-3.2.2
**Outputs**: 6-tuple of stress arrays (sxx, syy, szz, syz, sxz, sxy) in bar
**Tests**: `test_hooke_uniaxial_extension`, `test_hooke_pure_shear`, `test_hooke_volumetric`, `test_hooke_unit_factor_001`, `test_hooke_default_material`, `test_hooke_custom_material`
**Dependencies**: M1-T06 (MaterialProperties)
**Complexity**: S

#### M3-T02: Implement tensor_rotate (stress tensor rotation)

**Module**: `src/opencoulomb/core/stress.py`
**Description**: Implement `tensor_rotate()` that rotates a stress tensor from fault-local to geographic coordinates using the 6x6 Bond transformation matrix. The rotation is about the vertical axis by the fault strike angle. Build the direction cosine matrix from strike, then construct the 6x6 Bond matrix, then apply `[s_geo] = M @ [s_local]`.
**Inputs**: Architecture doc Section 3.2.1 (tensor_rotate API), Appendix B.4
**Outputs**: Rotated stress tensor components
**Tests**: `test_rotate_identity` (strike=0 gives identity), `test_rotate_90_degrees`, `test_rotate_180_degrees`, `test_rotate_roundtrip` (rotate by theta then -theta gives original), `test_rotate_vectorized`
**Dependencies**: M1-T02
**Complexity**: M

#### M3-T03: Implement compute_strain

**Module**: `src/opencoulomb/core/stress.py`
**Description**: Implement `compute_strain()` that computes the symmetric strain tensor from displacement gradients: `eij = 0.5 * (uij + uji)`.
**Inputs**: Architecture doc Section 3.2.1
**Outputs**: 6-tuple of strain arrays
**Tests**: `test_strain_symmetric`, `test_strain_from_pure_extension`, `test_strain_from_shear`
**Dependencies**: M1-T02
**Complexity**: S

#### M3-T04: Implement geo_to_fault coordinate transform

**Module**: `src/opencoulomb/core/coordinates.py`
**Description**: Implement `geo_to_fault()` that transforms geographic (x=East, y=North, z=Up) coordinates to Okada's fault-local system. This involves: (1) translate origin to fault center, (2) rotate by strike angle, (3) negate z for Okada convention (z <= 0 below surface). Must be vectorized.
**Inputs**: Architecture doc Section 3.4
**Outputs**: Transformed coordinate arrays
**Tests**: `test_geo_to_fault_ns_strike`, `test_geo_to_fault_ew_strike`, `test_geo_to_fault_arbitrary_strike`, `test_geo_to_fault_z_convention`, `test_geo_to_fault_vectorized`
**Dependencies**: M1-T07 (FaultElement)
**Complexity**: M

#### M3-T05: Implement fault_to_geo coordinate transform

**Module**: `src/opencoulomb/core/coordinates.py`
**Description**: Implement `fault_to_geo()` that rotates displacement vectors from fault-local back to geographic coordinates. This is the inverse rotation by strike angle.
**Inputs**: Architecture doc Section 3.4
**Outputs**: Geographic displacement arrays
**Tests**: `test_fault_to_geo_identity`, `test_fault_to_geo_90deg`, `test_geo_fault_roundtrip`
**Dependencies**: M3-T04
**Complexity**: S

#### M3-T06: Implement compute_fault_geometry

**Module**: `src/opencoulomb/core/coordinates.py`
**Description**: Implement `compute_fault_geometry()` that computes all derived geometric properties of a FaultElement: strike (from endpoints), length, width (from dip and depth range), center point (x, y, depth), Okada parameters (al1, al2, aw1, aw2), and corner coordinates. Returns a dict with all derived quantities.
**Inputs**: Architecture doc Section 3.4
**Outputs**: Dict of computed fault geometry parameters
**Tests**: `test_geometry_ns_fault`, `test_geometry_ew_fault`, `test_geometry_diagonal_fault`, `test_geometry_vertical_fault`, `test_geometry_shallow_dip`, `test_al1_al2_symmetric`, `test_width_from_dip`
**Dependencies**: M1-T07
**Complexity**: M

#### M3-T07: Implement lonlat_to_xy and xy_to_lonlat

**Module**: `src/opencoulomb/core/coordinates.py`
**Description**: Implement equirectangular projection for lon/lat to local km conversion and its inverse. Use the simple `dx = (lon - ref_lon) * cos(ref_lat) * 111.19`, `dy = (lat - ref_lat) * 111.19` formula (matching Coulomb 3.4). Vectorized.
**Inputs**: Architecture doc Section 3.4
**Outputs**: Coordinate transform functions
**Tests**: `test_lonlat_to_xy_equator`, `test_lonlat_to_xy_midlat`, `test_lonlat_xy_roundtrip`
**Dependencies**: M1-T02
**Complexity**: S

---

### M5: CFS Calculation

#### M5-T01: Implement bond_matrix

**Module**: `src/opencoulomb/core/coulomb.py`
**Description**: Implement `bond_matrix(strike_rad, dip_rad, rake_rad)` that builds the 6x6 Bond transformation matrix for stress resolution from geographic to fault-local coordinates. Build direction cosines from (strike, dip): n1 (strike), n2 (updip), n3 (normal). Then construct the 6x6 matrix using standard Voigt transformation rules.
**Inputs**: Architecture doc Section 3.3.1, Appendix B.4
**Outputs**: 6x6 NumPy array
**Tests**: `test_bond_matrix_vertical_ns`, `test_bond_matrix_vertical_ew`, `test_bond_matrix_dipping`, `test_bond_matrix_orthogonal` (verify M^T M = I for orthogonal transform)
**Dependencies**: M1-T02
**Complexity**: M

#### M5-T02: Implement resolve_stress

**Module**: `src/opencoulomb/core/coulomb.py`
**Description**: Implement `resolve_stress()` that resolves a full stress tensor onto a receiver fault plane using the Bond matrix. Returns shear stress (in rake direction) and normal stress. Shear = s'_xz * cos(rake) + s'_yz * sin(rake). Normal = s'_zz. Vectorized over N observation points.
**Inputs**: Architecture doc Section 3.3.1, Appendix B.4
**Outputs**: (shear, normal) tuple of arrays
**Tests**: `test_resolve_uniaxial_on_ns_fault`, `test_resolve_pure_shear`, `test_resolve_normal_stress_sign`, `test_resolve_vectorized`
**Dependencies**: M5-T01
**Complexity**: M

#### M5-T03: Implement compute_cfs

**Module**: `src/opencoulomb/core/coulomb.py`
**Description**: Implement `compute_cfs()` which calls `resolve_stress()` and then computes CFS = shear + friction * normal. Return (cfs, shear, normal) tuple.
**Inputs**: Architecture doc Section 3.3.1
**Outputs**: (cfs, shear, normal) tuple
**Tests**: `test_cfs_positive_shear_positive_normal`, `test_cfs_friction_effect`, `test_cfs_zero_friction`, `test_cfs_high_friction`
**Dependencies**: M5-T02
**Complexity**: S

#### M5-T04: Implement compute_cfs_on_elements

**Module**: `src/opencoulomb/core/coulomb.py`
**Description**: Implement `compute_cfs_on_elements()` that computes CFS at multiple points where each point has a different receiver orientation (strike, dip, rake arrays). Loop over elements or use batched Bond matrix construction.
**Inputs**: Architecture doc Section 3.3.1
**Outputs**: Per-element CFS results
**Tests**: `test_cfs_elements_single`, `test_cfs_elements_multiple`, `test_cfs_elements_varied_orientations`
**Dependencies**: M5-T03
**Complexity**: S

#### M5-T05: Implement _compute_single_fault (KODE dispatch)

**Module**: `src/opencoulomb/core/pipeline.py`
**Description**: Implement `_compute_single_fault()` that dispatches to dc3d or dc3d0 based on fault KODE, applying the correct sign conventions for each KODE type. Critical: KODE 100 applies `DISL1 = -slip_1` (sign flip for right-lateral to left-lateral convention).
**Inputs**: Architecture doc Section 3.6.2 (KODE dispatch table)
**Outputs**: 12-tuple of displacement/gradient arrays
**Tests**: `test_dispatch_kode_100`, `test_dispatch_kode_200`, `test_dispatch_kode_300`, `test_dispatch_kode_400`, `test_dispatch_kode_500`, `test_sign_flip_kode_100`
**Dependencies**: M2-T07 (dc3d), M2-T09 (dc3d0)
**Complexity**: M

#### M5-T06: Implement _generate_grid

**Module**: `src/opencoulomb/core/pipeline.py`
**Description**: Implement `_generate_grid(grid_spec)` that generates flattened grid coordinates using `np.arange` and `np.meshgrid`. Returns (grid_x, grid_y, grid_z) each of shape (N,) where z = -depth (Okada convention).
**Inputs**: Architecture doc Section 3.6.1
**Outputs**: Flattened grid coordinate arrays
**Tests**: `test_generate_grid_shape`, `test_generate_grid_values`, `test_generate_grid_depth_convention`
**Dependencies**: M1-T08 (GridSpec)
**Complexity**: S

#### M5-T07: Implement compute_grid (full pipeline orchestrator)

**Module**: `src/opencoulomb/core/pipeline.py`
**Description**: Implement `compute_grid(model: CoulombModel) -> CoulombResult`. This is the primary entry point. Algorithm: (1) generate grid, (2) initialize accumulator arrays, (3) for each source fault: compute geometry, transform coords, call dc3d/dc3d0, rotate displacements, compute stress, rotate stress, accumulate. (4) Resolve onto receivers (using first receiver's orientation or grid-uniform receiver). (5) Package into CoulombResult.
**Inputs**: Architecture doc Section 3.6
**Outputs**: `CoulombResult` with all fields populated
**Tests**: `test_compute_grid_single_fault`, `test_compute_grid_superposition`, `test_compute_grid_shape`
**Dependencies**: M5-T05, M5-T06, M5-T03, M3-T01 through M3-T06
**Complexity**: L

#### M5-T08: Implement compute_stress_field (lower-level API)

**Module**: `src/opencoulomb/core/pipeline.py`
**Description**: Implement `compute_stress_field()` that computes raw stress tensor and displacements at arbitrary points without CFS resolution. Used by cross-section and element computation.
**Inputs**: Architecture doc Section 3.6
**Outputs**: `StressResult` with tensor and displacement at all points
**Tests**: `test_stress_field_arbitrary_points`, `test_stress_field_single_point`
**Dependencies**: M5-T07 (shares inner loop logic)
**Complexity**: M

#### M5-T09: Validation -- CFS against Coulomb 3.4

**Module**: `tests/validation/test_vs_coulomb34.py`
**Description**: Run the full pipeline on example `.inp` files and compare CFS grid output against Coulomb 3.4 reference `dcff.cou` files. This is Validation Level 2 and Level 3. Compare CFS, shear, and normal stress at every grid point. Tolerance: absolute CFS difference < 1e-6 bar.
**Inputs**: Reference `.cou` outputs (need to be generated from Coulomb 3.4)
**Outputs**: Validation Level 2/3 passing
**Tests**: Parametrized across example files
**Dependencies**: M5-T07, reference outputs committed
**Complexity**: M

---

### M6: Optimally Oriented Planes (OOPs)

#### M6-T01: Implement compute_regional_stress_tensor

**Module**: `src/opencoulomb/core/oops.py`
**Description**: Implement `compute_regional_stress_tensor()` that converts the 3-axis principal stress specification (direction, dip, intensity, gradient) to a full 6-component stress tensor at a given depth. Intensity at depth = base_intensity + gradient * depth. Rotate principal stresses to geographic coordinates using the specified direction and dip for each axis.
**Inputs**: Architecture doc Section 3.5
**Outputs**: 6-tuple of stress arrays (regional stress at each grid point)
**Tests**: `test_regional_uniaxial_ns`, `test_regional_depth_gradient`, `test_regional_normal_faulting_regime`, `test_regional_strike_slip_regime`
**Dependencies**: M1-T09 (RegionalStress type)
**Complexity**: M

#### M6-T02: Implement find_optimal_planes

**Module**: `src/opencoulomb/core/oops.py`
**Description**: Implement `find_optimal_planes()`. Algorithm: (1) build 3x3 stress tensor at each point, (2) eigendecompose using `np.linalg.eigh`, (3) sort eigenvalues s1 >= s2 >= s3, (4) compute Mohr-Coulomb angle beta = pi/4 - 0.5*atan(friction), (5) construct two conjugate planes rotated +/-beta from s1 toward s3, (6) convert plane normals to (strike, dip), (7) compute CFS on each, (8) return the one with max |CFS|.
**Inputs**: Architecture doc Section 3.5, Appendix B.5
**Outputs**: (strike_opt, dip_opt, cfs_opt, rake_opt) arrays
**Tests**: `test_oops_known_stress_state`, `test_oops_uniaxial`, `test_oops_two_conjugate_planes`, `test_oops_friction_effect`
**Dependencies**: M6-T01, M5-T03 (compute_cfs)
**Complexity**: L

#### M6-T03: Integrate OOPs into compute_grid pipeline

**Module**: `src/opencoulomb/core/pipeline.py`
**Description**: Extend `compute_grid()` to support OOP mode. When the model has regional_stress and OOP is requested: (1) compute earthquake-induced stress field, (2) compute regional stress at grid depth, (3) sum total stress, (4) call `find_optimal_planes()`, (5) populate oops_strike, oops_dip, oops_rake fields in CoulombResult.
**Inputs**: Architecture doc Section 3.6
**Outputs**: CoulombResult with OOP fields populated
**Tests**: `test_compute_grid_oops_mode`, `test_compute_grid_oops_with_regional`
**Dependencies**: M6-T02, M5-T07
**Complexity**: M

#### M6-T04: Validation -- OOPs against Coulomb 3.4

**Module**: `tests/validation/test_vs_coulomb34.py`
**Description**: Validate OOP output against Coulomb 3.4 OOP reference outputs. Compare optimal strike, dip, and CFS values. Tolerance: strike within 1 degree, CFS within 1e-6 bar.
**Inputs**: Coulomb 3.4 OOP reference outputs
**Outputs**: OOP validation passing
**Tests**: Parametrized across OOP example files
**Dependencies**: M6-T03
**Complexity**: M

---

### M7: Cross-Section

#### M7-T01: Implement compute_section

**Module**: `src/opencoulomb/core/pipeline.py`
**Description**: Implement `compute_section(model, section_spec)`. Generate a 2D grid of points along the profile line and at depth intervals. For each point, compute the full stress field using `compute_stress_field()`, then resolve onto receiver to get CFS. Package into `CrossSectionResult`.
**Inputs**: Architecture doc Section 3.6
**Outputs**: `CrossSectionResult` with 2D arrays
**Tests**: `test_section_horizontal_profile`, `test_section_diagonal_profile`, `test_section_depth_range`, `test_section_result_shape`
**Dependencies**: M5-T08
**Complexity**: M

#### M7-T02: Validation -- cross-section against Coulomb 3.4

**Module**: `tests/validation/test_vs_coulomb34.py`
**Description**: Compare cross-section output against Coulomb 3.4 `dcff_section.cou` reference files. Tolerance: absolute CFS difference < 1e-6 bar.
**Inputs**: Reference `dcff_section.cou` files
**Outputs**: Cross-section validation passing
**Tests**: Parametrized across files with cross-section definitions
**Dependencies**: M7-T01
**Complexity**: S

---

### M8: Visualization

#### M8-T01: Implement colormap configuration

**Module**: `src/opencoulomb/viz/colormaps.py`
**Description**: Define the default Coulomb colormap configuration: diverging, symmetric around zero, red=positive CFS, blue=negative CFS. Support `RdBu_r` (Matplotlib built-in) and optionally `vik` (cmcrameri). Provide a `get_cfs_cmap(name=None)` function and `get_symmetric_norm(data, vmax=None)` for symmetric color normalization.
**Inputs**: Spec Section 3.4 (visualization stack)
**Outputs**: Colormap utilities
**Tests**: `test_default_colormap`, `test_symmetric_norm`, `test_custom_vmax`
**Dependencies**: M1-T02
**Complexity**: S

#### M8-T02: Implement fault trace rendering

**Module**: `src/opencoulomb/viz/faults.py`
**Description**: Implement `plot_fault_traces(ax, faults, n_fixed)` that draws source faults as solid lines and receiver faults as dashed lines on a Matplotlib axes. Color-code by type. Add optional fault labels.
**Inputs**: FaultElement list
**Outputs**: Matplotlib line artists on axes
**Tests**: `test_plot_faults_smoke`, `test_plot_faults_source_style`, `test_plot_faults_receiver_style`
**Dependencies**: M1-T07
**Complexity**: S

#### M8-T03: Implement 2D CFS contour map

**Module**: `src/opencoulomb/viz/maps.py`
**Description**: Implement `plot_cfs_map(result: CoulombResult, ax=None, **kwargs) -> Figure` that creates a filled contour map of CFS values. Reshape CFS to 2D grid, apply symmetric colormap, add colorbar with "CFS (bar)" label, overlay fault traces, add axis labels ("East (km)", "North (km)"). Support configurable: cmap, vmax, contour levels, figure size, DPI.
**Inputs**: CoulombResult
**Outputs**: Matplotlib Figure
**Tests**: `test_cfs_map_smoke`, `test_cfs_map_with_faults`, `test_cfs_map_custom_vmax`, `test_cfs_map_returns_figure`
**Dependencies**: M8-T01, M8-T02
**Complexity**: M

#### M8-T04: Implement cross-section plot

**Module**: `src/opencoulomb/viz/sections.py`
**Description**: Implement `plot_section(section_result: CrossSectionResult, ax=None, **kwargs) -> Figure` that creates a filled color plot of CFS on the vertical cross-section. X-axis = distance along profile, Y-axis = depth (positive downward). Add fault intersections if they cross the section plane.
**Inputs**: CrossSectionResult
**Outputs**: Matplotlib Figure
**Tests**: `test_section_plot_smoke`, `test_section_plot_depth_axis_inverted`, `test_section_plot_colorbar`
**Dependencies**: M8-T01
**Complexity**: M

#### M8-T05: Implement displacement vector (quiver) plot

**Module**: `src/opencoulomb/viz/displacement.py`
**Description**: Implement `plot_displacement(result: CoulombResult, component='horizontal', ax=None, **kwargs) -> Figure`. For horizontal: quiver plot of (ux, uy). For vertical: color map of uz. Subsample arrows for readability on dense grids. Add reference arrow with magnitude label.
**Inputs**: CoulombResult
**Outputs**: Matplotlib Figure
**Tests**: `test_displacement_quiver_smoke`, `test_displacement_vertical_smoke`, `test_displacement_subsampling`
**Dependencies**: M8-T01
**Complexity**: M

#### M8-T06: Implement publication-quality styles

**Module**: `src/opencoulomb/viz/styles.py`
**Description**: Define Matplotlib rcParams presets for publication output: appropriate font sizes, line widths, tick formatting. Provide `set_publication_style()` and `set_screen_style()` context managers. Define a default OpenCoulomb Matplotlib style file.
**Inputs**: Spec T2-PUB-04
**Outputs**: Style presets
**Tests**: `test_publication_style_applies`, `test_screen_style_applies`
**Dependencies**: M1-T02
**Complexity**: S

#### M8-T07: Implement figure export

**Module**: `src/opencoulomb/viz/export.py`
**Description**: Implement `save_figure(fig, path, format=None, dpi=300)` supporting PNG, PDF, SVG. Auto-detect format from extension. For PDF/SVG, ensure vector output (no rasterization of lines/text). Provide `export_all(result, output_dir, formats=['png'])` convenience function.
**Inputs**: Spec T1-VIZ-06
**Outputs**: Figure files on disk
**Tests**: `test_save_png`, `test_save_pdf`, `test_save_svg`, `test_auto_format_detection`
**Dependencies**: M8-T03
**Complexity**: S

#### M8-T08: Implement base plotting utilities

**Module**: `src/opencoulomb/viz/_base.py`
**Description**: Shared plotting utilities: `create_figure(figsize=None)`, axis labeling helpers, grid line helpers, title formatting. Used by all viz modules.
**Inputs**: Common patterns across viz modules
**Outputs**: Shared utilities
**Tests**: `test_create_figure_default`, `test_create_figure_custom_size`
**Dependencies**: M1-T02
**Complexity**: S

---

### M9: CLI

#### M9-T01: Implement main CLI entry point

**Module**: `src/opencoulomb/cli/main.py`
**Description**: Create the top-level Click group with global options: `--verbose/-v` (count), `--quiet`, `--version`. Set up logging configuration based on verbosity. Register subcommands: `compute`, `plot`, `info`, `convert`, `validate`.
**Inputs**: Spec T1-CLI-08, T1-CLI-09, T1-CLI-10
**Outputs**: `opencoulomb --help` shows all commands
**Tests**: `test_cli_help`, `test_cli_version`, `test_cli_verbose_flag`
**Dependencies**: M1-T02
**Complexity**: S

#### M9-T02: Implement 'compute' command

**Module**: `src/opencoulomb/cli/compute.py`
**Description**: Implement `opencoulomb compute <input.inp>` with options: `--output {cfs,displacement,strain,stress,all}`, `--receiver {specified,oops}`, `--plot {map,section,displacement,none}`, `--format {coulomb,csv,text}`, `--friction FLOAT`, `--depth FLOAT`, `--poisson FLOAT`, `--young FLOAT`, `--grid-start X Y`, `--grid-end X Y`, `--grid-spacing DX DY`, `--output-dir DIR`. Orchestrate: parse inp, apply overrides, compute, write outputs, optionally plot.
**Inputs**: Spec T1-CLI-01 through T1-CLI-07
**Outputs**: Full computation pipeline accessible from CLI
**Tests**: `test_compute_basic`, `test_compute_with_overrides`, `test_compute_csv_output`, `test_compute_with_plot`, `test_compute_oops_mode`
**Dependencies**: M5-T07, M6-T03, M8-T03, M10-T01 through M10-T04
**Complexity**: L

#### M9-T03: Implement 'plot' command

**Module**: `src/opencoulomb/cli/plot.py`
**Description**: Implement `opencoulomb plot <input.inp>` with options: `--type {map,section,displacement}`, `--output FILE`, `--format {png,pdf,svg}`, `--dpi INT`, `--cmap NAME`, `--vmax FLOAT`, `--figsize W H`. Standalone plotting from .inp file (computes then plots).
**Inputs**: Spec T1-VIZ-07
**Outputs**: Plot files
**Tests**: `test_plot_map_command`, `test_plot_section_command`, `test_plot_output_format`
**Dependencies**: M8-T03 through M8-T07
**Complexity**: M

#### M9-T04: Implement 'info' command

**Module**: `src/opencoulomb/cli/info.py`
**Description**: Implement `opencoulomb info <input.inp>` that parses and displays a human-readable summary: title, material properties, number of source/receiver faults, grid dimensions, regional stress (if any), fault list with key parameters.
**Inputs**: CoulombModel
**Outputs**: Formatted text summary to stdout
**Tests**: `test_info_basic`, `test_info_with_regional_stress`, `test_info_output_format`
**Dependencies**: M4-T09 (parser complete)
**Complexity**: S

#### M9-T05: Implement 'validate' command

**Module**: `src/opencoulomb/cli/validate.py`
**Description**: Implement `opencoulomb validate <input.inp>` that parses the file and reports any warnings or errors without running computation. Useful for checking .inp files before processing.
**Inputs**: Parser validation function
**Outputs**: Validation report to stdout
**Tests**: `test_validate_good_file`, `test_validate_bad_file`
**Dependencies**: M4-T10
**Complexity**: S

#### M9-T06: Implement logging configuration

**Module**: `src/opencoulomb/cli/_logging.py`
**Description**: Configure Python logging with formatters for CLI output. Support: default (WARNING), `-v` (INFO), `-vv` (DEBUG), `--quiet` (ERROR only). Add progress reporting for long computations (optional tqdm or simple percent output).
**Inputs**: Spec T1-CLI-08
**Outputs**: Logging infrastructure
**Tests**: `test_logging_levels`, `test_quiet_mode`
**Dependencies**: M1-T02
**Complexity**: S

---

### M10: Output Files

#### M10-T01: Implement dcff.cou writer

**Module**: `src/opencoulomb/io/cou_writer.py`
**Description**: Implement `write_dcff_cou(result: CoulombResult, path: Path)` that writes the Coulomb stress grid file in Coulomb 3.4 format. Match the exact column layout: x, y, CFS, shear, normal, and all 6 stress components. Include header lines with model parameters.
**Inputs**: Spec T1-OUT-01, Coulomb 3.4 `dcff.cou` format
**Outputs**: `dcff.cou` file
**Tests**: `test_write_dcff_cou_format`, `test_write_dcff_cou_header`, `test_write_dcff_cou_values`
**Dependencies**: M5-T07 (CoulombResult)
**Complexity**: M

#### M10-T02: Implement dcff_section.cou writer

**Module**: `src/opencoulomb/io/cou_writer.py`
**Description**: Implement `write_dcff_section_cou(section: CrossSectionResult, path: Path)` for cross-section output.
**Inputs**: Spec T1-OUT-02
**Outputs**: `dcff_section.cou` file
**Tests**: `test_write_section_cou_format`, `test_write_section_cou_values`
**Dependencies**: M7-T01 (CrossSectionResult)
**Complexity**: S

#### M10-T03: Implement coulomb_out.dat and gmt_fault_surface.dat writers

**Module**: `src/opencoulomb/io/dat_writer.py`
**Description**: Implement `write_coulomb_out_dat()` for the primary stress change grid output and `write_gmt_fault_surface_dat()` for GMT-compatible fault trace output.
**Inputs**: Spec T1-OUT-03, T1-OUT-04
**Outputs**: `.dat` files
**Tests**: `test_write_coulomb_out_dat`, `test_write_gmt_fault_surface`
**Dependencies**: M5-T07
**Complexity**: S

#### M10-T04: Implement CSV export

**Module**: `src/opencoulomb/io/csv_writer.py`
**Description**: Implement `write_csv(result: CoulombResult, path: Path)` with a header row documenting column order: x, y, cfs, shear, normal, sxx, syy, szz, syz, sxz, sxy, ux, uy, uz. Use Python `csv` module.
**Inputs**: Spec T1-OUT-05
**Outputs**: CSV file
**Tests**: `test_write_csv_header`, `test_write_csv_values`, `test_write_csv_roundtrip`
**Dependencies**: M5-T07
**Complexity**: S

#### M10-T05: Implement text summary writer

**Module**: `src/opencoulomb/io/csv_writer.py` or new module
**Description**: Implement `write_summary(model: CoulombModel, result: CoulombResult, path: Path)` that writes a human-readable text summary: input parameters, computation statistics (min/max CFS, number of grid points, computation time), and key results.
**Inputs**: Spec T1-OUT-06
**Outputs**: Text summary file
**Tests**: `test_write_summary_content`, `test_write_summary_includes_parameters`
**Dependencies**: M5-T07
**Complexity**: S

---

### M11: Validation

#### M11-T01: Generate and commit Coulomb 3.4 reference outputs

**Module**: `tests/fixtures/reference_outputs/`
**Description**: Using a MATLAB/Coulomb 3.4 installation (or outputs from a collaborator), run every example `.inp` file and save all output files (`dcff.cou`, `dcff_section.cou`, `coulomb_out.dat`, etc.). Commit these as test fixtures. Document the exact Coulomb version and platform used.
**Inputs**: Coulomb 3.4 + MATLAB
**Outputs**: Reference output files for all examples
**Tests**: Files exist and contain expected data
**Dependencies**: M4-T01 (example .inp files)
**Complexity**: M (logistics of obtaining MATLAB outputs)

#### M11-T02: Implement Validation Level 1 -- Okada DC3D

**Module**: `tests/validation/test_vs_okada_reference.py`
**Description**: Already covered in M2-T11. Ensure it is fully parametrized across all test geometries and all 12 output components. Relative error < 1e-10.
**Inputs**: Okada reference values
**Outputs**: Passing Level 1 validation
**Tests**: Comprehensive parametrized test
**Dependencies**: M2-T11
**Complexity**: S (already implemented)

#### M11-T03: Implement Validation Level 2 -- Stress/CFS pipeline

**Module**: `tests/validation/test_vs_coulomb34.py`
**Description**: Already partially covered in M5-T09. Expand to cover: single vertical strike-slip, single dipping reverse, multiple sources (superposition), specified receivers, OOPs, cross-section, displacement field. Absolute CFS < 1e-6 bar.
**Inputs**: Reference outputs
**Outputs**: Passing Level 2 validation
**Tests**: 7+ test cases
**Dependencies**: M5-T09, M11-T01
**Complexity**: M

#### M11-T04: Implement Validation Level 3 -- full example files

**Module**: `tests/validation/test_vs_coulomb34.py`
**Description**: Parametrized test running every example `.inp` file through the full pipeline and comparing all outputs against Coulomb 3.4 reference. Compare grid CFS, section CFS, per-element stress, displacement.
**Inputs**: All example files + reference outputs
**Outputs**: Passing Level 3 validation
**Tests**: Parametrized across all ~20 files
**Dependencies**: M11-T01, M11-T03
**Complexity**: M

#### M11-T05: Implement Validation Level 4 -- cross-validation with elastic_stresses_py

**Module**: `tests/validation/test_vs_elastic_stresses.py`
**Description**: Run shared test cases through both OpenCoulomb and elastic_stresses_py. Compare CFS on 5 test cases (simple strike-slip, multi-segment, dipping with rake, varying friction, varying depth). Tolerance: < 1e-4 bar.
**Inputs**: elastic_stresses_py outputs (generate and commit)
**Outputs**: Passing Level 4 validation
**Tests**: 5 test cases
**Dependencies**: M5-T07
**Complexity**: M

#### M11-T06: Implement Validation Level 5 -- published results

**Module**: `tests/validation/test_published_results.py`
**Description**: Reproduce CFS patterns from: King, Stein & Lin (1994) Fig 2 (Landers 1992), Toda et al. (2011) user guide examples. Qualitative validation: correct lobe pattern, correct sign, approximate magnitude match.
**Inputs**: Digitized published values or pattern comparison
**Outputs**: Passing Level 5 validation
**Tests**: 3 published result reproductions
**Dependencies**: M5-T07
**Complexity**: M

#### M11-T07: Implement Validation Level 6 -- edge cases and regression

**Module**: `tests/validation/test_edge_cases.py`
**Description**: Implement all 18+ edge case tests from spec Section 8.2.6: zero slip, single-component slip, surface fault, very long/small fault, observation at fault center/far field, extreme Poisson/friction, 0/90 dip, cardinal strikes, grid point on fault, 1x1 grid, 1000x1000 grid.
**Inputs**: Spec Section 8.2.6
**Outputs**: All edge cases pass
**Tests**: 18+ parametrized edge case tests
**Dependencies**: M5-T07
**Complexity**: M

#### M11-T08: Implement validation report generator

**Module**: `scripts/generate_validation_report.py`
**Description**: Script that runs all validation tests and generates a formatted report (text and markdown) showing pass/fail status, tolerances achieved, performance metrics, and platform information. Output to `docs/validation/validation-report.md`.
**Inputs**: pytest output
**Outputs**: Validation report
**Tests**: Script runs without error
**Dependencies**: M11-T02 through M11-T07
**Complexity**: S

---

### M12: Packaging

#### M12-T01: Finalize pyproject.toml for release

**Module**: `pyproject.toml`
**Description**: Update version to 1.0.0, verify all metadata (classifiers, URLs, descriptions), verify dependency version bounds, verify optional dependency groups work (`pip install opencoulomb[gui]`, `pip install opencoulomb[geo]`, etc.). Test `python -m build` produces wheel and sdist.
**Inputs**: Architecture doc Section 12
**Outputs**: Correct wheel and sdist
**Tests**: `pip install dist/opencoulomb-1.0.0-py3-none-any.whl` succeeds
**Dependencies**: All prior milestones
**Complexity**: S

#### M12-T02: Cross-platform CI testing

**Module**: `.github/workflows/test.yml`
**Description**: Expand CI matrix to all target platforms: Ubuntu (latest), macOS (latest), Windows (latest) x Python (3.10, 3.11, 3.12, 3.13). Verify all tests pass on all combinations. Add matrix exclusions per architecture doc Section 12.4.
**Inputs**: Architecture doc Section 12.4
**Outputs**: Green CI on full matrix
**Tests**: CI itself
**Dependencies**: M1-T03
**Complexity**: M

#### M12-T03: PyPI publication workflow

**Module**: `.github/workflows/publish.yml`
**Description**: GitHub Actions workflow that publishes to PyPI on tagged releases. Use trusted publisher (OIDC) authentication. Publish to TestPyPI first for verification, then to PyPI.
**Inputs**: PyPI account, trusted publisher config
**Outputs**: `pip install opencoulomb` works from PyPI
**Tests**: Install from TestPyPI in CI
**Dependencies**: M12-T01
**Complexity**: M

#### M12-T04: Docker image

**Module**: `Dockerfile`
**Description**: Create a minimal Docker image based on `python:3.12-slim` that installs opencoulomb with all optional dependencies. Provide `docker run opencoulomb compute` entry point.
**Inputs**: Spec Section 3.8
**Outputs**: Working Docker image
**Tests**: `docker run opencoulomb --version` succeeds
**Dependencies**: M12-T01
**Complexity**: S

#### M12-T05: conda-forge recipe

**Module**: External (`conda-forge/staged-recipes` PR)
**Description**: Create a conda-forge recipe (`meta.yaml`) for opencoulomb. Submit PR to staged-recipes repository. Verify `conda install -c conda-forge opencoulomb` works.
**Inputs**: pyproject.toml, dependency list
**Outputs**: conda-forge package
**Tests**: `conda install opencoulomb` in clean environment
**Dependencies**: M12-T03 (needs PyPI package first)
**Complexity**: M

---

### M13: Documentation

Task breakdown for M13 is covered in detail in Section 3 (Documentation Plan). The high-level tasks are:

#### M13-T01: Technical documentation (Arc42)
#### M13-T02: API reference auto-generation
#### M13-T03: Contributing guide
#### M13-T04: Tutorials (Diataxis)
#### M13-T05: How-to guides (Diataxis)
#### M13-T06: Reference documentation (Diataxis)
#### M13-T07: Explanations (Diataxis)
#### M13-T08: Project CLAUDE.md (LLM root context)
#### M13-T09: Module CONTEXT.md files (LLM module context)
#### M13-T10: Claude Code skills (LLM development skills)
#### M13-T11: Structured LLM reference files
#### M13-T12: Documentation site build pipeline

See Section 3 for full details on each.

---

## 3. Documentation Plan

Documentation is a first-class deliverable in OpenCoulomb. Three distinct documentation types serve three distinct audiences: developers/contributors (technical), seismologists/students (human user), and AI coding assistants (LLM-optimized). Each milestone produces documentation updates across all three types.

### 3.1 Technical Documentation (Arc42-Style)

Technical documentation follows the Arc42 template adapted for a scientific Python project. It targets developers and contributors who need to understand the codebase internals.

#### 3.1.1 Architecture Documentation

**Location**: `docs/technical/architecture/`

| Document | Content | Create At | Update At |
|----------|---------|-----------|-----------|
| `01-introduction.md` | Goals, stakeholders, constraints | Phase A (M1) | M13 |
| `02-constraints.md` | Technical and organizational constraints | Phase A (M1) | M13 |
| `03-context.md` | System context (C4 Level 1) | Phase A (M1) | M13 |
| `04-solution-strategy.md` | Key design decisions, technology choices | Phase A (M1) | As decisions change |
| `05-building-blocks.md` | Component diagram (C4 Level 2-3), module descriptions | Phase B (M2) | Each milestone |
| `06-runtime-view.md` | Data flow, computation pipeline sequence | Phase B (M5) | M6, M7 |
| `07-deployment-view.md` | Installation, Docker, CI/CD, PyPI | Phase E (M12) | M12 |
| `08-cross-cutting.md` | Error handling, logging, testing, conventions | Phase A (M1) | Each milestone |
| `09-decisions/` | Architecture Decision Records (ADRs) | As needed | Ongoing |
| `10-quality.md` | Quality tree, test strategy, coverage targets | Phase A (M1) | M11 |

#### 3.1.2 Architecture Decision Records

**Location**: `docs/technical/architecture/09-decisions/`
**Format**: MADR (Markdown Any Decision Record)

Planned ADRs:

| ADR | Decision | Phase |
|-----|----------|-------|
| ADR-001 | Use Python with NumPy vectorization for Okada engine | Phase A |
| ADR-002 | Pure Python DC3D vs Fortran wrapper | Phase B |
| ADR-003 | Frozen dataclasses for data model | Phase A |
| ADR-004 | State machine parser for .inp files | Phase A |
| ADR-005 | Click for CLI framework | Phase D |
| ADR-006 | Matplotlib as primary visualization library | Phase D |
| ADR-007 | Apache 2.0 license | Phase A |
| ADR-008 | Hatchling build backend | Phase A |
| ADR-009 | Singularity handling strategy in Okada | Phase B |
| ADR-010 | 0.001 unit factor placement | Phase B |

#### 3.1.3 API Reference (Auto-Generated)

**Location**: `docs/api/` (generated output)
**Tool**: MkDocs + mkdocstrings (or Sphinx + autodoc)
**Source**: Docstrings in source code (NumPy-style)

Every public function, class, and method must have a complete docstring including:
- One-line summary
- Extended description (for non-trivial functions)
- Parameters with types, units, and descriptions
- Returns with types, units, and descriptions
- Raises section for expected exceptions
- Notes section for mathematical details (with LaTeX formulas where appropriate)
- Examples section (for key functions)

**Docstring enforcement**: Per-milestone. Every module touched in a milestone must have 100% docstring coverage before the milestone is marked complete.

| Milestone | Modules requiring docstrings |
|-----------|------------------------------|
| M1 | `types/*`, `_constants.py`, `exceptions.py` |
| M2 | `core/okada.py` |
| M3 | `core/stress.py`, `core/coordinates.py` |
| M4 | `io/inp_parser.py` |
| M5 | `core/coulomb.py`, `core/pipeline.py` |
| M6 | `core/oops.py` |
| M7 | `core/pipeline.py` (cross-section additions) |
| M8 | `viz/*` |
| M9 | `cli/*` |
| M10 | `io/cou_writer.py`, `io/csv_writer.py`, `io/dat_writer.py` |

#### 3.1.4 Contributing Guide

**Location**: `CONTRIBUTING.md` (root) + `docs/technical/contributing/`
**Create At**: Phase A (M1)
**Update At**: M12, M13

Contents:
- Development environment setup (git clone, pip install -e ".[dev]", pre-commit)
- Code style guide (ruff config, naming conventions)
- Type annotation requirements (mypy strict)
- Testing guide (running tests, writing tests, fixtures, validation tests)
- Branch and PR workflow
- Commit message convention (`type(scope): description`)
- Release process
- Code of Conduct

#### 3.1.5 Changelog

**Location**: `CHANGELOG.md` (root)
**Format**: Keep a Changelog
**Create At**: Phase A (M1)
**Update At**: Every release

---

### 3.2 Human User Documentation (Diataxis Framework)

Human user documentation follows the Diataxis framework and targets seismologists, students, and agency scientists who use OpenCoulomb as a tool. Written in clear, jargon-appropriate language (seismology terms are fine; software engineering terms should be explained).

**Location**: `docs/user/`
**Build tool**: MkDocs with Material for MkDocs theme

#### 3.2.1 Tutorials (Learning-Oriented)

**Location**: `docs/user/tutorials/`

Tutorials are step-by-step walkthroughs that teach by doing. Each tutorial has a clear learning goal, uses real earthquake data where possible, and produces a concrete result (a figure, a file, or a computed value).

| Tutorial | Description | Prerequisites | Create At |
|----------|-------------|---------------|-----------|
| `getting-started.md` | Install OpenCoulomb, run first computation on a simple strike-slip fault, view the CFS map | None | Phase E (M13) |
| `first-cfs-calculation.md` | Detailed walkthrough: load an .inp file, understand the model, compute CFS, interpret the red/blue lobes | getting-started | Phase E (M13) |
| `understanding-inp-files.md` | Anatomy of a .inp file: header, faults, grid. Build one from scratch. | first-cfs | Phase E (M13) |
| `interpreting-stress-maps.md` | Read CFS maps: stress shadows, lobes, units, color scale meaning. Compare with published results for the 1992 Landers earthquake. | first-cfs | Phase E (M13) |
| `migrating-from-coulomb34.md` | For existing Coulomb users: equivalent commands, same .inp files, output comparison, key differences | Coulomb 3.4 experience | Phase E (M13) |

#### 3.2.2 How-To Guides (Task-Oriented)

**Location**: `docs/user/how-to/`

How-to guides are practical recipes that solve specific problems. They assume the reader already understands the basics and needs to accomplish a task.

| Guide | Description | Create At |
|-------|-------------|-----------|
| `compute-cfs-earthquake.md` | How to compute CFS for a specific earthquake: obtain fault parameters, create .inp file, run computation | Phase E (M13) |
| `publication-quality-figures.md` | How to create journal-ready figures: style settings, PDF/SVG export, font sizes, multi-panel layout | Phase E (M13) |
| `batch-calculations.md` | How to run multiple computations: shell loops, parameter sweeps, collecting results | Phase E (M13) |
| `cross-section-analysis.md` | How to compute and visualize a vertical cross-section through your model | Phase E (M13) |
| `custom-receiver-faults.md` | How to specify custom receiver fault orientations for CFS calculation | Phase E (M13) |
| `optimally-oriented-planes.md` | How to compute CFS on optimally oriented planes with regional stress | Phase E (M13) |
| `use-as-python-library.md` | How to use OpenCoulomb as a Python library in scripts and Jupyter notebooks | Phase E (M13) |
| `compare-with-gps.md` | How to compare computed displacements with GPS observations (placeholder for Tier 2) | Tier 2 |

#### 3.2.3 Reference Documentation (Information-Oriented)

**Location**: `docs/user/reference/`

Reference docs are comprehensive, factual descriptions of the system. They are looked up, not read end-to-end.

| Reference | Description | Create At |
|-----------|-------------|-----------|
| `cli-reference.md` | Complete CLI command reference: all commands, all options, all defaults | Phase D (M9) |
| `inp-format.md` | Complete .inp file format reference with every field, KODE type, and example | Phase A (M4) |
| `output-formats.md` | All output file formats: .cou, .dat, .csv column layouts and header formats | Phase D (M10) |
| `physical-constants.md` | Default values, units, and physical constants used by OpenCoulomb | Phase A (M1) |
| `coordinate-conventions.md` | Geographic system, fault-local system, Okada convention, sign conventions, depth convention | Phase B (M3) |
| `configuration.md` | Configuration file format (opencoulomb.toml), environment variables, default overrides | Phase D (M9) |
| `error-messages.md` | Catalog of error messages with explanations and solutions | Phase E (M13) |
| `glossary.md` | Terms and definitions (CFS, DC3D, OOP, receiver, source, etc.) | Phase A (M1) |

#### 3.2.4 Explanation Documentation (Understanding-Oriented)

**Location**: `docs/user/explanation/`

Explanations provide conceptual background. They help users understand *why* things work the way they do.

| Explanation | Description | Create At |
|-------------|-------------|-----------|
| `coulomb-stress-transfer.md` | What is Coulomb stress transfer? History, concept, significance for earthquake hazard | Phase E (M13) |
| `okada-model-explained.md` | The Okada (1992) elastic dislocation model: what it computes, assumptions, limitations | Phase E (M13) |
| `optimally-oriented-planes.md` | Understanding OOPs: Mohr-Coulomb criterion, regional stress, interpretation | Phase E (M13) |
| `units-coordinates-signs.md` | Deep explanation of the unit system (bar, km, m), coordinate conventions, and sign conventions that trip people up | Phase E (M13) |
| `validation-approach.md` | How OpenCoulomb is validated against Coulomb 3.4 and published results | Phase E (M13) |
| `architecture-for-scientists.md` | Non-technical overview of how the code is organized, for users who want to understand or extend it | Phase E (M13) |

---

### 3.3 LLM-Optimized Documentation

LLM-optimized documentation is specifically structured for AI coding assistants (Claude Code, GitHub Copilot, ChatGPT) to effectively assist with OpenCoulomb development and usage. This documentation prioritizes machine-parseability, explicit context, and the domain knowledge that LLMs lack.

#### 3.3.1 Project CLAUDE.md

**Location**: `CLAUDE.md` (repository root)
**Create At**: Phase A (M1) -- initial version
**Update At**: Every milestone

This is the primary context file that Claude Code loads automatically. It must be concise (under 200 substantive lines) and pack maximum useful information.

Contents:

```
# OpenCoulomb

## What This Is
OpenCoulomb is an open-source Python replacement for the USGS Coulomb 3.4 MATLAB
software for computing Coulomb failure stress changes from earthquake fault slip.

## Tech Stack
- Python 3.10+ with NumPy/SciPy/Matplotlib/Click
- Build: hatchling, pyproject.toml (PEP 621)
- Tests: pytest, hypothesis, numpy.testing
- Lint: ruff (line-length 88), mypy (strict)
- License: Apache 2.0

## Module Map
src/opencoulomb/
  _constants.py    - Physical constants, defaults, unit factors
  exceptions.py    - Custom exception hierarchy
  types/           - Data model (frozen dataclasses): FaultElement, GridSpec, CoulombModel, etc.
  core/            - Computation engine (zero I/O, zero viz)
    okada.py       - Okada (1992) DC3D/DC3D0 dislocation solution (vectorized NumPy)
    stress.py      - Hooke's law, tensor rotation (0.001 unit factor!)
    coulomb.py     - CFS = shear + friction * normal, Bond matrix
    coordinates.py - Geographic <-> fault-local transforms
    oops.py        - Optimally oriented planes (eigendecomposition + Mohr-Coulomb)
    pipeline.py    - Orchestrator: compute_grid(), compute_section()
  io/              - File I/O: .inp parser (state machine), .cou/.dat/.csv writers
  viz/             - Matplotlib visualization: maps, sections, displacement, export
  cli/             - Click CLI: compute, plot, info, validate commands

## Key Commands
pytest                          # Run tests
pytest -m "not slow"            # Skip slow tests
pytest tests/validation/        # Run validation suite
ruff check src/                 # Lint
mypy src/                       # Type check
opencoulomb compute input.inp   # Run computation
opencoulomb info input.inp      # Inspect .inp file

## Critical Domain Knowledge
- Okada DC3D: analytical solution for displacement/strain in elastic half-space
- CFS = delta_tau + mu' * delta_sigma_n (positive = closer to failure)
- SIGN CONVENTION: .inp file uses RL+ but Okada uses LL+ => DISL1 = -slip_1 for KODE 100
- The 0.001 factor: gradients are du(m)/dx(km), multiply by 0.001 to get true strain
- Coordinates: X=East, Y=North, Z=Up (but Okada z<=0 below surface)
- Units: stress in bar (1 bar = 0.1 MPa), distance in km, slip in m
- All core/ functions are vectorized: observation points are arrays, faults are scalar per loop

## Coding Conventions
- Frozen dataclasses with __slots__ for data model
- NumPy-style docstrings on all public functions (include units!)
- Type hints on everything (mypy strict)
- No I/O in core/ modules; no viz in core/ modules
- Tests use numpy.testing.assert_allclose for numerical comparison
```

#### 3.3.2 Module-Level CONTEXT.md Files

**Location**: Inside each source package directory
**Create At**: When each module is implemented
**Update At**: When module changes significantly

These files provide detailed context that an LLM needs to work effectively within a specific module. They are more detailed than CLAUDE.md and focus on patterns, gotchas, and domain specifics.

**`src/opencoulomb/core/CONTEXT.md`**
Create at: Phase B (M2)

Contents:
- Purpose of the core engine (zero I/O, zero viz, pure computation)
- Vectorization pattern: observation points are arrays, faults are scalar
- The complete Okada DC3D call tree (dc3d -> _dccon0 -> _ua/_ub/_uc -> Chinnery sum)
- Singularity handling strategy (5 cases with code patterns)
- The 0.001 unit factor: where it is applied and why
- Sign convention table (Coulomb vs Okada for each slip component)
- KODE dispatch table (100/200/300/400/500 -> which Okada parameters)
- Performance expectations (inner loop is NumPy, outer loop is Python over faults)
- Mathematical references (Okada 1992 equation numbers for each sub-function)

**`src/opencoulomb/io/CONTEXT.md`**
Create at: Phase A (M4)

Contents:
- .inp file format overview with example snippets
- State machine parser design (state enum, transitions)
- Fixed-width format quirks (tabs vs spaces, scientific notation variants)
- Column header detection patterns
- How #fixed works (source/receiver boundary)
- Common parsing edge cases and how they are handled
- Output file format specifications (column widths, header lines)
- Encoding assumptions (ASCII, no Unicode in .inp files)

**`src/opencoulomb/viz/CONTEXT.md`**
Create at: Phase D (M8)

Contents:
- Matplotlib idioms used (Figure/Axes pattern, not pyplot)
- Colormap convention (diverging, symmetric, red=positive CFS)
- How to add a new plot type (follow the pattern in maps.py)
- Publication style settings (rcParams)
- Export formats and their quirks (PDF vector vs PNG raster)
- Testing strategy for viz (smoke tests, not pixel comparison)

**`src/opencoulomb/cli/CONTEXT.md`**
Create at: Phase D (M9)

Contents:
- Click patterns used (groups, commands, options, callbacks)
- How CLI commands map to core functions
- Logging configuration (verbosity levels)
- How parameter overrides work (CLI -> model -> defaults)
- Error handling in CLI context (user-friendly messages)
- Testing CLI (Click's testing runner)

**`src/opencoulomb/types/CONTEXT.md`**
Create at: Phase A (M1)

Contents:
- Why frozen dataclasses (immutability prevents bugs in computation)
- Validation pattern (__post_init__ raises ValidationError)
- Computed properties pattern (strike_deg, alpha, etc.)
- CoulombModel as aggregate root (the complete input for a computation)
- Result types (mutable dataclasses because they are populated during computation)
- Unit conventions for every field

#### 3.3.3 Claude Code Skills

**Location**: `~/.claude/skills/opencoulomb-dev/` and `~/.claude/skills/opencoulomb-science/`
**Also**: `.claude/skills/` in the repository for project-scoped skills
**Create At**: Phase E (M13), with initial versions at Phase A
**Update At**: As the project evolves

**Skill 1: `opencoulomb-dev`**

```yaml
# .claude/skills/opencoulomb-dev/SKILL.md
---
name: opencoulomb-dev
description: OpenCoulomb development workflow. Use when making code changes, running tests, or adding features.
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
---

# OpenCoulomb Development Workflow

## Running Tests
- All tests: `pytest`
- Fast tests only: `pytest -m "not slow and not validation"`
- Single module: `pytest tests/unit/test_okada.py`
- With coverage: `pytest --cov=opencoulomb --cov-report=term-missing`
- Validation suite: `pytest tests/validation/ -v`

## Before Committing
1. `ruff check src/ tests/` -- fix any lint errors
2. `mypy src/` -- fix any type errors
3. `pytest -x` -- ensure tests pass (stop on first failure)

## Adding a New Feature
1. Add/update types in `src/opencoulomb/types/` if new data structures needed
2. Implement computation in `src/opencoulomb/core/` (no I/O here!)
3. Add I/O support in `src/opencoulomb/io/` if new file format
4. Add visualization in `src/opencoulomb/viz/` if new plot type
5. Add CLI command/option in `src/opencoulomb/cli/`
6. Write tests in corresponding `tests/` subdirectory
7. Update CONTEXT.md files in affected modules

## Numerical Code Patterns
- Use `numpy.testing.assert_allclose(actual, expected, rtol=1e-10)` for validation
- Use `np.where` for singularity guards, NEVER use Python if/else on arrays
- All observation-point variables are arrays of shape (N,); fault params are scalar
- Apply 0.001 factor inside `gradients_to_stress()`, nowhere else

## Common Pitfalls
- Sign convention: DISL1 = -slip_1 for KODE 100 (RL+ in file, LL+ in Okada)
- Depth: Coulomb uses positive downward, Okada uses negative downward (z <= 0)
- The 0.001 factor is NOT a bug -- it converts du(m)/dx(km) to true strain
- Frozen dataclasses: use dataclasses.replace() to create modified copies
```

**Skill 2: `opencoulomb-science`**

```yaml
# .claude/skills/opencoulomb-science/SKILL.md
---
name: opencoulomb-science
description: Earthquake science domain knowledge for OpenCoulomb. Use when writing or reviewing scientific computation code.
allowed-tools: Read, Grep, Glob
---

# OpenCoulomb Science Reference

## Coulomb Failure Stress (CFS)
Delta_CFS = Delta_tau + mu' * Delta_sigma_n

- Delta_tau: shear stress change resolved in slip direction (bar)
  - Positive = promotes slip on receiver fault
- Delta_sigma_n: normal stress change on receiver fault (bar)
  - Positive = unclamping (tension), promotes failure
  - Negative = clamping (compression), inhibits failure
- mu': effective friction coefficient (default 0.4, includes pore pressure)

Interpretation:
- Positive CFS = fault brought closer to failure (red on maps)
- Negative CFS = stress shadow, fault stabilized (blue on maps)
- Typical values: 0.1-10 bar for moderate earthquakes

## Okada (1992) DC3D
Analytical closed-form solution for displacement and displacement gradients
at any point in a homogeneous isotropic elastic half-space due to a
rectangular dislocation source.

Key parameters:
- alpha = (lambda + mu) / (lambda + 2*mu) = 1/(2*(1-nu))
  For nu=0.25: alpha = 2/3
- Three dislocation types:
  - DISL1: strike-slip (positive = LEFT-lateral in Okada convention)
  - DISL2: dip-slip (positive = reverse/thrust)
  - DISL3: tensile (positive = opening)

Returns 12 values per observation point:
  ux, uy, uz (displacement in meters)
  uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz (gradients: du_i/dx_j)

## Hooke's Law (Coulomb Formulation)
sk = E / (1 + nu)        # = 2 * shear_modulus
gk = nu / (1 - 2*nu)     # = lambda / mu
vol = uxx + uyy + uzz    # volumetric strain

sxx = sk * (gk * vol + uxx) * 0.001
syy = sk * (gk * vol + uyy) * 0.001
szz = sk * (gk * vol + uzz) * 0.001
sxy = (sk/2) * (uxy + uyx) * 0.001
sxz = (sk/2) * (uxz + uzx) * 0.001
syz = (sk/2) * (uyz + uzy) * 0.001

The 0.001 factor: Okada returns du(meters)/dx(km). To get dimensionless
strain, divide by 1000 (convert km to m): strain = du(m) / (dx(km)*1000).

## Coordinate Systems
Geographic: X=East, Y=North, Z=Up
Okada fault-local: X=along-strike, Y=perpendicular, Z=Up (z<=0 below surface)
Depth: Coulomb positive downward; Okada z negative downward

## Sign Convention Table
| Quantity | .inp file | Okada (internal) | Conversion |
|----------|-----------|-------------------|------------|
| Right-lateral slip | positive | DISL1 negative | DISL1 = -col7 |
| Left-lateral slip | negative | DISL1 positive | DISL1 = -col7 |
| Reverse (thrust) | positive | DISL2 positive | DISL2 = col8 |
| Normal slip | negative | DISL2 negative | DISL2 = col8 |
| Tensile opening | positive | DISL3 positive | DISL3 = col5 |
| Depth | positive down | z negative down | z = -depth |

## KODE Dispatch
| KODE | col5 meaning | col6 meaning | DISL1 | DISL2 | DISL3 |
|------|-------------|-------------|-------|-------|-------|
| 100 | right-lateral | reverse | -col5 | col6 | 0 |
| 200 | tensile | right-lateral | -col6 | 0 | col5 |
| 300 | tensile | reverse | 0 | col6 | col5 |
| 400 | right-lateral | reverse | -col5 (pot1) | col6 (pot2) | 0 |
| 500 | tensile | inflation | 0 | 0 | col5 (pot3), col6 (pot4) |

## Default Physical Constants
| Parameter | Value | Unit |
|-----------|-------|------|
| Poisson's ratio | 0.25 | dimensionless |
| Young's modulus | 8.0e5 | bar (80 GPa) |
| Friction coeff | 0.4 | dimensionless |
| Computation depth | 10.0 | km |
| alpha (medium const) | 0.6667 | dimensionless |
| Shear modulus | 3.2e5 | bar (32 GPa) |

## Stress Resolution onto Receiver Fault
1. Build direction cosine matrix from (strike, dip)
2. Build 6x6 Bond transformation matrix
3. Transform: s'_ij = M @ s_ij (geographic -> fault-local)
4. Normal stress = s'_zz (stress on fault normal)
5. Shear stress = s'_xz * cos(rake) + s'_yz * sin(rake)
6. CFS = shear + friction * normal

## Optimally Oriented Planes (OOPs)
1. Total stress = regional_stress(depth) + earthquake_stress
2. Eigendecompose: find s1 >= s2 >= s3 and eigenvectors
3. Mohr-Coulomb angle: beta = pi/4 - 0.5*atan(mu')
4. Two conjugate planes at +/-beta from s1 toward s3
5. Compute CFS on each, return max |CFS|
```

#### 3.3.4 Structured Reference for LLMs

**Location**: `docs/llm/`
**Create At**: Phase E (M13), with initial versions growing during development
**Update At**: Every milestone

**`docs/llm/function-index.md`** -- Machine-Readable Function Index

Format: One entry per public function with consistent structure for LLM parsing.

```
## opencoulomb.core.okada.dc3d
- Module: src/opencoulomb/core/okada.py
- Purpose: Compute displacement and gradients for finite rectangular fault
- Signature: dc3d(alpha, x, y, z, depth, dip, al1, al2, aw1, aw2, disl1, disl2, disl3)
- Input units: alpha (dimensionless), x/y/z/depth/al/aw (km), dip (degrees), disl (m)
- Output: 12-tuple of (ux,uy,uz in m, 9 gradients in m/km)
- Vectorized: x, y, z can be arrays of shape (N,)
- Key gotcha: z must be <= 0 (Okada convention)

## opencoulomb.core.coulomb.compute_cfs
- Module: src/opencoulomb/core/coulomb.py
- Purpose: Compute Coulomb failure stress on receiver fault
- Signature: compute_cfs(sxx, syy, szz, syz, sxz, sxy, strike, dip, rake, friction)
- Input units: stress in bar, angles in degrees, friction dimensionless
- Output: (cfs, shear, normal) each in bar
- Vectorized: stress arrays shape (N,), angles are scalar
- Formula: CFS = shear + friction * normal
```

This index is generated/maintained for every public function across all modules.

**`docs/llm/data-structures.md`** -- Data Structure Reference

```
## FaultElement
- Location: src/opencoulomb/types/fault.py
- Type: frozen dataclass with __slots__
- Fields:
  - x_start: float (km, East) - Starting X of surface trace
  - y_start: float (km, North) - Starting Y of surface trace
  - x_fin: float (km, East) - Ending X of surface trace
  - y_fin: float (km, North) - Ending Y of surface trace
  - kode: Kode (IntEnum: 100/200/300/400/500) - Element type
  - slip_1: float (m) - Slip component 1 (meaning depends on kode)
  - slip_2: float (m) - Slip component 2 (meaning depends on kode)
  - dip: float (degrees, 0-90) - Dip angle
  - top_depth: float (km, >= 0) - Fault top depth
  - bottom_depth: float (km, > top_depth) - Fault bottom depth
  - label: str (default "") - Optional text label
  - element_index: int (default 0) - 1-based index from .inp file
- Validation: dip in [0,90], top_depth >= 0, bottom_depth > top_depth
- Computed: is_source, is_receiver, is_point_source, strike_deg, rake_deg
- Immutable: use dataclasses.replace() to create modified copies
```

This reference covers every dataclass with every field, type, unit, and validation rule.

**`docs/llm/common-errors.md`** -- Common Error Patterns and Fixes

```
## NaN in Okada output
- Cause: Observation point on fault edge (singularity)
- Fix: Singularity guards in _dccon2 using np.where masks
- Prevention: DEPTH_EPSILON shifts points slightly off singularities

## CFS values wrong sign
- Cause: Missing sign flip for KODE 100 (DISL1 = -slip_1)
- Fix: Check _compute_single_fault dispatch table
- Test: test_sign_flip_kode_100

## Stress values off by factor of 1000
- Cause: Missing 0.001 unit factor in gradients_to_stress
- Fix: Ensure factor is applied exactly once in gradients_to_stress()
- Test: test_hooke_unit_factor_001

## Tensor rotation gives wrong results
- Cause: Strike angle in wrong units (degrees vs radians)
- Fix: All public APIs accept degrees; convert to radians internally
- Test: test_rotate_roundtrip
```

**`docs/llm/test-commands.md`** -- Test Command Cheatsheet

```
# All tests
pytest

# Specific test file
pytest tests/unit/test_okada.py

# Specific test function
pytest tests/unit/test_okada.py::test_dc3d_vs_okada_table2

# Tests matching keyword
pytest -k "singularity"

# With coverage
pytest --cov=opencoulomb --cov-report=term-missing

# Only fast tests (skip validation and benchmarks)
pytest -m "not slow and not validation and not benchmark"

# Validation suite only
pytest tests/validation/ -v

# Performance benchmarks
pytest tests/performance/ --benchmark-only

# Type checking
mypy src/

# Linting
ruff check src/ tests/
ruff format --check src/ tests/
```

#### 3.3.5 AI-Friendly Code Patterns

These are coding standards enforced throughout the codebase to maximize LLM effectiveness. They are not separate documents but coding requirements:

| Pattern | Requirement | Why It Helps LLMs |
|---------|-------------|-------------------|
| Type hints everywhere | All function signatures, all variables where non-obvious | LLMs use type info for context and suggestions |
| NumPy-style docstrings | Parameters with types, units, descriptions | LLMs extract parameter info from docstrings |
| Module-level docstrings | First line of every module explains purpose | LLMs use these to understand module scope |
| Consistent naming | `compute_*` for calculations, `parse_*` for parsing, `write_*` for output, `plot_*` for viz | Predictable names help LLM navigation |
| Explicit imports | No wildcard imports, no runtime imports (except for optional deps) | LLMs can trace dependencies |
| Constants, not magic numbers | All physical constants in `_constants.py` | LLMs can find and verify values |
| Small functions | Each function does one thing, < 50 lines preferred | LLMs work better with focused functions |
| Descriptive variable names | `strike_rad` not `sr`, `grid_x` not `gx` | Self-documenting code |

#### 3.3.6 Per-Milestone LLM Documentation Updates

| Milestone | LLM Doc Updates |
|-----------|----------------|
| M1 | Create CLAUDE.md (initial), types/CONTEXT.md |
| M2 | Update CLAUDE.md module map, create core/CONTEXT.md (Okada section) |
| M3 | Update core/CONTEXT.md (stress, coordinates sections) |
| M4 | Create io/CONTEXT.md, update CLAUDE.md |
| M5 | Update core/CONTEXT.md (pipeline section), update CLAUDE.md commands |
| M6 | Update core/CONTEXT.md (OOPs section) |
| M7 | Update core/CONTEXT.md (cross-section) |
| M8 | Create viz/CONTEXT.md |
| M9 | Create cli/CONTEXT.md, update CLAUDE.md commands |
| M10 | Update io/CONTEXT.md (output formats) |
| M11 | Create docs/llm/common-errors.md |
| M12 | Update CLAUDE.md (installation, packaging) |
| M13 | Create all docs/llm/ files, create skills, final CLAUDE.md |

---

## 4. Testing Strategy per Phase

### Phase A: Foundation (M1 + M4)

**Unit Tests**:
- `tests/unit/test_types.py`: All dataclass creation, validation, computed properties, immutability. Parametrize across valid/invalid inputs for each type. Target: 100% coverage of `types/` package.
- `tests/unit/test_constants.py`: Verify all constants have expected values and types.

**Integration Tests**:
- `tests/integration/test_inp_parsing.py`: Parametrized test parsing every Coulomb 3.4 example `.inp` file. Verify: no errors, correct number of faults, reasonable material values, valid grid.
- `tests/integration/test_inp_roundtrip.py`: Parse a file, inspect the CoulombModel, verify specific field values match hand-checked expectations.

**Test Fixtures Needed**:
- All ~20 Coulomb 3.4 example `.inp` files (from `coulomb3402.zip`)
- A minimal synthetic `.inp` file for quick unit testing (single fault, small grid)
- A malformed `.inp` file for error handling tests

**Coverage Target**: types/ >= 100%, io/inp_parser.py >= 90%

---

### Phase B: Core Computation Engine (M2 + M3 + M5)

**Unit Tests**:
- `tests/unit/test_okada.py`:
  - `_dccon0`: verify constants for standard, vertical, and horizontal dip
  - `_ua`, `_ub`, `_uc`: verify each sub-function independently for each slip type
  - `dc3d`: comprehensive tests against Okada (1992) Table 2 values; parametrize across all slip types, dip angles, observation locations
  - `dc3d0`: point source tests
  - Singularity handling: 5 singularity conditions, verify no NaN/Inf
  - Vectorization: verify shape (N,) output for array inputs
  - Performance: verify vectorized call is faster than N scalar calls

- `tests/unit/test_stress.py`:
  - `gradients_to_stress`: uniaxial extension, pure shear, volumetric, verify 0.001 factor
  - `tensor_rotate`: identity (strike=0), 90-degree rotation, 180 reversal, roundtrip
  - `compute_strain`: symmetric tensor computation
  - Property-based tests (hypothesis): rotation roundtrip for random angles

- `tests/unit/test_coordinates.py`:
  - `geo_to_fault`: various strike angles, verify z-convention
  - `fault_to_geo`: inverse rotation
  - `compute_fault_geometry`: known fault geometries, Okada parameters
  - `lonlat_to_xy`: equator, mid-latitude, roundtrip
  - Property-based tests (hypothesis): geo_to_fault -> fault_to_geo roundtrip

- `tests/unit/test_coulomb.py`:
  - `bond_matrix`: orthogonality check (M^T M = I), known geometries
  - `resolve_stress`: uniaxial stress on known fault, verify shear/normal decomposition
  - `compute_cfs`: various friction values, verify formula
  - `compute_cfs_on_elements`: multiple receivers with different orientations

- `tests/unit/test_pipeline.py`:
  - `_generate_grid`: shape, values, depth convention
  - `_compute_single_fault`: each KODE type dispatched correctly
  - `compute_grid`: single fault, verify output shape and CoulombResult structure
  - Superposition: two identical faults with half slip == one fault with full slip

**Validation Tests**:
- `tests/validation/test_vs_okada_reference.py` (Level 1): DC3D output vs Fortran reference for 11+ test geometries. Tolerance: relative error < 1e-10.
- `tests/validation/test_vs_coulomb34.py` (Level 2): Full pipeline CFS vs Coulomb 3.4 `dcff.cou` for 7+ test cases. Tolerance: absolute CFS < 1e-6 bar.

**Test Fixtures Needed**:
- Fortran DC3D reference values (JSON/CSV with 16+ digit precision) for ~20 test configurations
- Coulomb 3.4 reference `dcff.cou` output files for key example inputs
- Synthetic test cases with analytically known results (e.g., vertical strike-slip fault at surface should produce symmetric four-lobed CFS pattern)

**Coverage Target**: core/ >= 95%

---

### Phase C: Extended Computation (M6 + M7)

**Unit Tests**:
- `tests/unit/test_oops.py`:
  - `compute_regional_stress_tensor`: uniaxial stress, depth gradient, normal/thrust/strike-slip regimes
  - `find_optimal_planes`: known stress state with analytically predictable OOP orientation
  - Mohr-Coulomb angle: verify beta = pi/4 - 0.5*atan(mu) for various friction values
  - Two conjugate planes: verify they are symmetric about s1-s3 plane

- `tests/unit/test_pipeline.py` (additions):
  - `compute_section`: horizontal profile, diagonal profile, depth range, result shape
  - `compute_grid` in OOP mode: verify OOP fields populated

**Validation Tests**:
- `tests/validation/test_vs_coulomb34.py` (OOP cases): Compare optimal strike, dip, and CFS against Coulomb 3.4 OOP outputs for example files that include regional stress.
- `tests/validation/test_vs_coulomb34.py` (cross-section cases): Compare `dcff_section.cou` values.

**Test Fixtures Needed**:
- Coulomb 3.4 OOP reference outputs (example files that specify regional stress)
- Coulomb 3.4 cross-section reference outputs (`dcff_section.cou`)
- Synthetic OOP test case with known optimal orientation

**Coverage Target**: core/oops.py >= 90%, cross-section code >= 90%

---

### Phase D: User-Facing Layer (M8 + M9 + M10)

**Unit Tests**:
- `tests/unit/test_viz.py`:
  - Smoke tests: each plot function runs without error and returns a Figure
  - Colormap: default colormap is diverging, symmetric normalization works
  - Fault rendering: source vs receiver styles differ
  - Export: PNG/PDF/SVG files are created and non-empty

- `tests/integration/test_cli.py`:
  - Each CLI command with `--help` returns 0
  - `opencoulomb compute simple.inp` produces output files
  - `opencoulomb compute simple.inp --format csv` produces CSV
  - `opencoulomb compute simple.inp --plot map --output-dir /tmp/test` produces PNG
  - `opencoulomb info simple.inp` displays model summary
  - `opencoulomb validate simple.inp` reports no errors
  - Parameter overrides: `--friction 0.6` changes CFS values
  - Verbosity: `-v` and `--quiet` change log output
  - Error handling: non-existent file produces helpful error message

- `tests/unit/test_writers.py`:
  - `write_dcff_cou`: verify format matches Coulomb 3.4 column layout (compare header, column count, float formatting)
  - `write_csv`: verify header row, column count, roundtrip (write then read)
  - `write_dat`: verify format

**Integration Tests**:
- `tests/integration/test_full_pipeline.py`:
  - End-to-end: parse `.inp` -> compute -> write all outputs -> verify each output file exists and is non-empty
  - Roundtrip: parse `.inp` -> compute -> write `.cou` -> compare with reference

**Test Fixtures Needed**:
- Reference output files (format exemplars) for column layout comparison
- A simple `.inp` file that produces known output for CLI testing

**Coverage Target**: viz/ >= 80%, cli/ >= 85%, io/ writers >= 85%

---

### Phase E: Release (M11 + M12 + M13)

**Validation Tests** (the core of this phase):
- Level 1 (Okada): Already passing from Phase B
- Level 2 (Stress/CFS): Already passing from Phase B
- Level 3 (All examples): Parametrized across all ~20 `.inp` files, all output types
- Level 4 (Cross-validation): 5 test cases vs elastic_stresses_py
- Level 5 (Published results): King+Stein (1994), Toda et al. (2011) user guide figures
- Level 6 (Edge cases): 18+ edge case tests per spec Section 8.2.6

**Performance Tests**:
- `tests/performance/test_benchmarks.py`:
  - 100x100 grid, 10 faults: < 10 seconds
  - 200x200 grid, 50 faults: < 120 seconds
  - Single dc3d call, 250000 points: measure baseline
  - Memory usage: < 500 MB for 500x500 grid

**Packaging Tests**:
- Install from wheel in clean virtual environment on each OS
- `opencoulomb --version` after install
- `python -c "import opencoulomb; print(opencoulomb.__version__)"` after install
- Install with each optional dependency group: `[gui]`, `[geo]`, `[science]`

**Documentation Tests**:
- MkDocs/Sphinx builds without errors or warnings
- All cross-references resolve
- No broken links
- All code examples in docs are syntactically valid

**Coverage Target**: Overall >= 85%, core/ >= 95%, validation suite 100% pass

---

## 5. Quality Gates

Before any milestone is marked complete and before moving to the next phase, all applicable quality gates must pass.

### Gate 1: Code Quality (Every Milestone)

| Check | Tool | Threshold | Command |
|-------|------|-----------|---------|
| Lint passes | ruff | Zero errors | `ruff check src/ tests/` |
| Format correct | ruff | Zero diffs | `ruff format --check src/ tests/` |
| Type check passes | mypy | Zero errors (strict mode) | `mypy src/` |
| No `# type: ignore` without comment | Manual review | Zero unexplained ignores | Grep for `type: ignore` |

### Gate 2: Test Coverage (Every Milestone)

| Module Category | Minimum Coverage | Measured By |
|----------------|-----------------|-------------|
| `core/` (computation) | 95% line + branch | `pytest --cov` |
| `types/` (data model) | 100% line | `pytest --cov` |
| `io/` (parsers, writers) | 85% line | `pytest --cov` |
| `viz/` (visualization) | 80% line | `pytest --cov` |
| `cli/` (command-line) | 85% line | `pytest --cov` |
| Overall package | 85% line | `pytest --cov` |

### Gate 3: Numerical Validation (Phases B through E)

| Level | What | Tolerance | When Required |
|-------|------|-----------|---------------|
| Level 1 | Okada DC3D vs Fortran | Relative error < 1e-10 | Phase B onward |
| Level 2 | CFS vs Coulomb 3.4 | Absolute < 1e-6 bar | Phase B onward |
| Level 3 | All example files | All within Level 2 tolerance | Phase E |
| Level 4 | vs elastic_stresses_py | Absolute < 1e-4 bar | Phase E |
| Level 5 | Published results | Qualitative match | Phase E |
| Level 6 | Edge cases | No NaN/Inf, physically reasonable | Phase E |

### Gate 4: Documentation (Every Milestone)

| Check | Requirement |
|-------|-------------|
| Docstrings | 100% of public functions/classes touched in this milestone |
| CONTEXT.md | Updated for each module modified |
| CLAUDE.md | Updated if module map or key commands changed |
| CHANGELOG | Entry for every milestone |

### Gate 5: Performance (Phases B, D, E)

| Benchmark | Target | When |
|-----------|--------|------|
| 100x100 grid, 10 faults | < 10 seconds | Phase B, regress check thereafter |
| Single dc3d, 100k points | < 2 seconds | Phase B |
| .inp parse, 1000 faults | < 1 second | Phase A |
| CLI cold start to `--help` | < 2 seconds | Phase D |

### Gate 6: Cross-Platform (Phase E)

| Platform | Python Versions | Status |
|----------|----------------|--------|
| Ubuntu latest | 3.10, 3.11, 3.12, 3.13 | All tests pass |
| macOS latest | 3.11, 3.12, 3.13 | All tests pass |
| Windows latest | 3.11, 3.12, 3.13 | All tests pass |

### Gate 7: Release Readiness (Phase E Only)

| Check | Requirement |
|-------|-------------|
| All 6 validation levels pass | 100% on all platforms |
| `pip install opencoulomb` works from TestPyPI | Clean install in fresh venv |
| All three doc types complete | Technical, Human, LLM |
| CHANGELOG complete | All milestones documented |
| LICENSE file present | Apache 2.0 |
| README accurate | Installation, quick start, links |

---

## 6. Risk Mitigation Actions

Mapping risks from the specification's risk register (Section 10) to specific tasks and phases.

### R1: Okada DC3D Numerical Inaccuracy in Pure Python

**Risk**: Pure NumPy implementation may accumulate floating-point errors differently than the Fortran reference.

**Mitigation Actions**:
| Action | Task | Phase |
|--------|------|-------|
| Generate exhaustive reference values from Fortran DC3D | M2-T01 | B |
| Test all 12 output components at 1e-10 relative tolerance | M2-T11 | B |
| Test singularity edge cases explicitly | M2-T10 | B |
| Use `np.float64` throughout (never float32) | Coding standard | All |
| If tolerance fails: implement Fortran wrapper via ctypes | Contingency task (not scheduled) | B (if needed) |
| Document numerical precision in validation report | M11-T08 | E |

**Decision point**: If any dc3d test fails at 1e-10 relative error after debugging, switch to the Fortran wrapper approach (okada_wrapper pattern). Create ADR-002 documenting the decision.

### R2: Performance Too Slow for Large Grids

**Risk**: Python loop overhead or non-vectorized code paths cause unacceptable computation times.

**Mitigation Actions**:
| Action | Task | Phase |
|--------|------|-------|
| Vectorize all observation-point computations from the start | M2-T04 through M2-T06 | B |
| Benchmark after Phase B (100x100, 10 faults < 10s gate) | Performance gate | B |
| Profile with `cProfile` if gate fails | Contingency | B |
| NumPy broadcasting instead of explicit loops where possible | Coding standard | All |
| Chunk processing for grids > 100k points | M5-T07 (pipeline) | B |
| If still too slow: Fortran inner loop via ctypes | Contingency (not scheduled) | C |

**Decision point**: Performance gate after Phase B. If 100x100x10 > 10s, investigate with profiling. If the bottleneck is Python overhead in the fault loop, it is acceptable (typically < 100 faults). If the bottleneck is within dc3d vectorized operations, escalate to Fortran wrapper.

### R3: .inp Format Undocumented Edge Cases

**Risk**: Real-world .inp files contain formatting variants not covered by the specification.

**Mitigation Actions**:
| Action | Task | Phase |
|--------|------|-------|
| Test against ALL available example files from Coulomb 3.4 | M4-T01, M4-T09 | A |
| Inspect Coulomb 3.4 MATLAB parser source (`read_input_file.m`) | Research during M4 | A |
| Implement forgiving parsing (warn, do not error, on non-critical deviations) | M4-T10 | A |
| Document every .inp format quirk in io/CONTEXT.md | M4 CONTEXT.md update | A |
| Provide `opencoulomb validate` command for users to check files | M9-T05 | D |
| Community bug reports for new edge cases | Post-release | Ongoing |

### R4: Coulomb 3.4 Reference Outputs Not Available

**Risk**: Need MATLAB license to generate reference outputs for validation.

**Mitigation Actions**:
| Action | Task | Phase |
|--------|------|-------|
| Obtain reference outputs via academic MATLAB license or collaborator | M11-T01 | A (begin), E (complete) |
| Cross-validate against elastic_stresses_py (MIT, no MATLAB needed) | M11-T05 | E |
| Use Okada (1992) Table 2 published values (available without MATLAB) | M2-T01 | B |
| Use Fortran DC3D output as ground truth for Okada layer | M2-T01 | B |
| If no MATLAB access: rely on Levels 1, 4, 5 validation; defer Level 3 | Contingency | E |

### R5: GUI Development Takes Longer Than Estimated

**Risk**: PyQt6 GUI development is complex and time-consuming.

**Mitigation Actions**:
| Action | Task | Phase |
|--------|------|-------|
| GUI is Tier 2, NOT part of MVP 1.0 release | Architecture decision | -- |
| CLI-first architecture ensures tool is usable without GUI | Phases A-E | All |
| Python API (Tier 3) provides programmatic access as alternative | Post-1.0 | -- |
| Consider simpler Panel/Streamlit prototype before full PyQt6 | Tier 2 planning | -- |

**No mitigation tasks in the current plan** because GUI is out of scope for Tier 1.

### R6: Scope Creep into Coulomb 4.0 Features

**Risk**: Adding C4.0 features delays the 1.0 release.

**Mitigation Actions**:
| Action | Task | Phase |
|--------|------|-------|
| Strict tier discipline: only Tier 1 features in 1.0 | All milestone definitions | All |
| Track Tier 2/3 feature requests in issues, do not implement | Project management | All |
| Coulomb 4.0 .inp format monitoring (if format diverges, add parser variant later) | Post-release monitoring | -- |

### R8: Coordinate Convention Errors (Sign Flips, Axis Order)

**Risk**: This is the highest-likelihood risk. Sign convention errors are subtle and can produce plausible but wrong results.

**Mitigation Actions**:
| Action | Task | Phase |
|--------|------|-------|
| Document all conventions prominently (architecture Appendix A) | Already done | -- |
| KODE dispatch table with explicit sign flips in code comments | M5-T05 | B |
| Unit tests for each convention independently | M3-T04, M3-T05, M5-T01, M5-T02 | B |
| Property-based tests for coordinate roundtrips | M3 (hypothesis tests) | B |
| Cross-validation against Coulomb 3.4 catches any remaining errors | M5-T09, M11-T04 | B, E |
| Sign convention table in core/CONTEXT.md and opencoulomb-science skill | Section 3.3 | A, B |
| Code review focus: every sign flip gets a comment explaining why | Coding standard | All |

### R9: Dependency Conflicts

**Risk**: NumPy/SciPy/Matplotlib version conflicts with user's environment.

**Mitigation Actions**:
| Action | Task | Phase |
|--------|------|-------|
| Minimal core dependencies (numpy, scipy, matplotlib, click) | pyproject.toml | A |
| Follow NEP 29 for version bounds | M12-T01 | E |
| Test in clean environments on CI | M12-T02 | E |
| Optional dependency groups for heavy packages | pyproject.toml | A |
| Docker image as conflict-free alternative | M12-T04 | E |

---

## 7. Documentation Directory Structure

The complete planned directory structure for all documentation:

```
docs/
    technical/                          # Technical docs (Arc42) -- for developers
        architecture/
            01-introduction.md
            02-constraints.md
            03-context.md
            04-solution-strategy.md
            05-building-blocks.md
            06-runtime-view.md
            07-deployment-view.md
            08-cross-cutting.md
            09-decisions/
                ADR-001-python-numpy-okada.md
                ADR-002-pure-python-vs-fortran.md
                ADR-003-frozen-dataclasses.md
                ADR-004-state-machine-parser.md
                ADR-005-click-cli.md
                ADR-006-matplotlib-viz.md
                ADR-007-apache-license.md
                ADR-008-hatchling-build.md
                ADR-009-singularity-handling.md
                ADR-010-unit-factor-placement.md
            10-quality.md
        contributing/
            development-setup.md
            code-style.md
            testing-guide.md
            release-process.md

    user/                               # Human user docs (Diataxis) -- for seismologists
        tutorials/
            getting-started.md
            first-cfs-calculation.md
            understanding-inp-files.md
            interpreting-stress-maps.md
            migrating-from-coulomb34.md
        how-to/
            compute-cfs-earthquake.md
            publication-quality-figures.md
            batch-calculations.md
            cross-section-analysis.md
            custom-receiver-faults.md
            optimally-oriented-planes.md
            use-as-python-library.md
        reference/
            cli-reference.md
            inp-format.md
            output-formats.md
            physical-constants.md
            coordinate-conventions.md
            configuration.md
            error-messages.md
            glossary.md
        explanation/
            coulomb-stress-transfer.md
            okada-model-explained.md
            optimally-oriented-planes.md
            units-coordinates-signs.md
            validation-approach.md
            architecture-for-scientists.md

    llm/                                # LLM-optimized docs -- for AI assistants
        function-index.md
        data-structures.md
        common-errors.md
        test-commands.md
        sign-conventions.md
        formulas.md

    api/                                # Auto-generated API reference
        index.md                        # Generated by mkdocstrings
        core/
        types/
        io/
        viz/
        cli/

    research/                           # Phase 1 (already exists)
        research-summary.md

    design/                             # Phase 2 (already exists)
        program-specification.md

    architecture/                       # Phase 3 (already exists)
        architecture.md

    plan/                               # Phase 4 (this document)
        development-plan.md

    validation/                         # Generated validation reports
        validation-report.md

# Root-level documentation files
CLAUDE.md                               # LLM project context (root)
README.md                              # Project overview
CONTRIBUTING.md                        # Contributor guide (points to docs/technical/contributing/)
CHANGELOG.md                           # Version history
LICENSE                                # Apache 2.0

# Module-level LLM context files
src/opencoulomb/core/CONTEXT.md
src/opencoulomb/types/CONTEXT.md
src/opencoulomb/io/CONTEXT.md
src/opencoulomb/viz/CONTEXT.md
src/opencoulomb/cli/CONTEXT.md

# Claude Code skills (user-scoped or project-scoped)
.claude/skills/opencoulomb-dev/SKILL.md
.claude/skills/opencoulomb-science/SKILL.md
```

---

## 8. Continuous Documentation Updates

### 8.1 When to Update Documentation

| Trigger | What to Update |
|---------|---------------|
| **Every milestone completion** | CHANGELOG, CLAUDE.md module map, relevant CONTEXT.md files |
| **Every new public function** | Docstring (immediately), function-index.md (at milestone end) |
| **Every new data structure** | Docstring, data-structures.md (at milestone end) |
| **Every PR that changes behavior** | Affected CONTEXT.md, relevant how-to/reference docs |
| **Every architecture decision** | New ADR in `docs/technical/architecture/09-decisions/` |
| **Every release** | CHANGELOG, validation report, version in CLAUDE.md |
| **Bug fix for confusing behavior** | common-errors.md, relevant explanation doc |

### 8.2 Documentation Review Checklist

Before any milestone is marked complete, verify:

- [ ] All new public functions have NumPy-style docstrings with parameters, returns, raises, and units
- [ ] Module-level docstring is present and accurate for any new module
- [ ] CONTEXT.md files updated for any modified module
- [ ] CLAUDE.md updated if module structure or key commands changed
- [ ] CHANGELOG has an entry for this milestone
- [ ] No TODO/FIXME in docstrings (either resolve or file an issue)
- [ ] Type hints present on all new function signatures
- [ ] Examples in docstrings are syntactically valid Python

### 8.3 Keeping LLM Docs in Sync with Code

LLM documentation becomes stale quickly if not maintained. The following strategies prevent drift:

**Automated checks** (CI pipeline):
- `scripts/check_function_index.py`: Script that parses all public functions from source and compares against `docs/llm/function-index.md`. Fails CI if a public function is missing from the index.
- `scripts/check_context_files.py`: Verifies that every package directory containing Python modules also contains a CONTEXT.md file.
- `scripts/check_docstrings.py`: Verifies that all public functions have docstrings (using `pydocstyle` or custom script).

**Manual discipline**:
- Any PR that adds or modifies a public function must include updates to:
  - The function's docstring
  - The module's CONTEXT.md (if behavior patterns changed)
  - `docs/llm/function-index.md` (added to the PR checklist)
- Any PR that fixes a non-obvious bug must add an entry to `docs/llm/common-errors.md`

**Scheduled updates**:
- At each milestone boundary: regenerate API docs, review all CONTEXT.md files, update CLAUDE.md
- At each release: regenerate function-index.md and data-structures.md from source, update validation report

### 8.4 Documentation Generation Pipeline

**API Reference** (automated):
```yaml
# In CI or as a make target
mkdocs build        # Builds full documentation site including auto-generated API reference
```

MkDocs configuration (`mkdocs.yml`) uses `mkdocstrings` to auto-generate API docs from source code docstrings. The output goes to `docs/api/`.

**Validation Report** (automated):
```bash
# scripts/generate_validation_report.py
# Runs pytest on validation suite, captures results, formats as markdown
python scripts/generate_validation_report.py > docs/validation/validation-report.md
```

**Function Index** (semi-automated):
```bash
# scripts/generate_function_index.py
# Parses all public functions and generates docs/llm/function-index.md
python scripts/generate_function_index.py > docs/llm/function-index.md
```

**Data Structure Reference** (semi-automated):
```bash
# scripts/generate_data_structures.py
# Parses all dataclasses in types/ and generates docs/llm/data-structures.md
python scripts/generate_data_structures.py > docs/llm/data-structures.md
```

### 8.5 Documentation Dependency Graph

```
Source Code (docstrings, type hints)
    |
    +--> API Reference (auto-generated by mkdocstrings)
    +--> Function Index (semi-auto script)
    +--> Data Structures Reference (semi-auto script)
    |
CONTEXT.md files (manually maintained per module)
    |
    +--> CLAUDE.md (summarizes all CONTEXT.md files)
    +--> Skills (reference CONTEXT.md patterns)
    |
User Documentation (manually written)
    |
    +--> Tutorials (reference API, include code examples)
    +--> How-to guides (reference CLI, include commands)
    +--> Reference (derived from source + .inp format spec)
    +--> Explanation (standalone, references published papers)
```

---

## Appendix A: Task Dependency Graph

```
Phase A: Foundation
  M1-T01 -> M1-T02 -> M1-T04 -> M1-T05
  M1-T01 -> M1-T03
  M1-T02 -> M1-T06 -> M1-T07 -> M1-T08 -> M1-T09 -> M1-T10 -> M1-T11 -> M1-T12
  M1-T05 -> M4-T01
  M1-T11 -> M4-T02 -> M4-T03 -> M4-T04 -> M4-T05 -> M4-T06 -> M4-T07 -> M4-T08 -> M4-T09 -> M4-T10

Phase B: Core Engine
  M1-T05 -> M2-T01
  M1-T02 -> M2-T02 -> M2-T03 -> {M2-T04, M2-T05, M2-T06} -> M2-T07 -> M2-T10
  M2-T03 -> M2-T08 -> M2-T09 -> M2-T10
  {M2-T01, M2-T07, M2-T09} -> M2-T11
  M1-T06 -> M3-T01
  M1-T02 -> M3-T02
  M1-T07 -> M3-T04 -> M3-T05
  M1-T07 -> M3-T06
  M1-T02 -> M3-T07
  M1-T02 -> M5-T01 -> M5-T02 -> M5-T03 -> M5-T04
  {M2-T07, M2-T09} -> M5-T05
  M1-T08 -> M5-T06
  {M5-T05, M5-T06, M5-T03, M3-T01, M3-T02, M3-T04, M3-T05, M3-T06} -> M5-T07 -> M5-T08
  {M5-T07} -> M5-T09

Phase C: Extended Computation
  M1-T09 -> M6-T01
  {M6-T01, M5-T03} -> M6-T02
  {M6-T02, M5-T07} -> M6-T03 -> M6-T04
  M5-T08 -> M7-T01 -> M7-T02

Phase D: User-Facing
  M1-T02 -> M8-T01 -> M8-T03, M8-T04
  M1-T07 -> M8-T02
  {M8-T01, M8-T02} -> M8-T03
  M8-T01 -> M8-T04, M8-T05
  M8-T03 -> M8-T07
  M1-T02 -> M9-T01
  {M5-T07, M6-T03, M8-T03, M10-T01..T04} -> M9-T02
  {M8-T03, M8-T04, M8-T05, M8-T07} -> M9-T03
  M4-T09 -> M9-T04
  M4-T10 -> M9-T05
  M5-T07 -> {M10-T01, M10-T03, M10-T04, M10-T05}
  M7-T01 -> M10-T02

Phase E: Release
  M4-T01 -> M11-T01
  M2-T11 -> M11-T02
  {M5-T09, M11-T01} -> M11-T03 -> M11-T04
  M5-T07 -> M11-T05
  M5-T07 -> M11-T06
  M5-T07 -> M11-T07
  {M11-T02..T07} -> M11-T08
  All milestones -> M12-T01 -> M12-T03 -> M12-T05
  M1-T03 -> M12-T02
  M12-T01 -> M12-T04
  All milestones -> M13 tasks
```

## Appendix B: Complete Task Count Summary

| Milestone | Task Count | Complexity Mix |
|-----------|-----------|----------------|
| M1: Project scaffold | 12 | 12S |
| M2: Okada DC3D engine | 11 | 1S, 5M, 5L |
| M3: Stress computation | 7 | 3S, 4M |
| M4: .inp parser | 10 | 5S, 4M, 1M |
| M5: CFS calculation | 9 | 3S, 5M, 1L |
| M6: OOPs | 4 | 0S, 3M, 1L |
| M7: Cross-section | 2 | 1S, 1M |
| M8: Visualization | 8 | 5S, 3M |
| M9: CLI | 6 | 4S, 1M, 1L |
| M10: Output files | 5 | 4S, 1M |
| M11: Validation | 8 | 2S, 6M |
| M12: Packaging | 5 | 2S, 3M |
| M13: Documentation | 12 | (see Section 3) |
| **Total** | **99 tasks** | |

---

*End of Development Plan*
*Document version 1.0 -- 2026-02-27*
*Phase 4 of the OpenCoulomb project*
