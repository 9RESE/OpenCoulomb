# Program Specification: OpenCoulomb

**Phase 2 -- Design Specification**
**Version**: 1.0
**Date**: 2026-02-27
**Status**: Draft
**Derived From**: Phase 1 Research (docs/claude/research/)

---

## Table of Contents

1. [Product Vision and Goals](#1-product-vision-and-goals)
2. [Functional Requirements](#2-functional-requirements)
3. [Technology Decisions](#3-technology-decisions)
4. [Input/Output Specification](#4-inputoutput-specification)
5. [User Interface Specification](#5-user-interface-specification)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Compatibility Matrix](#7-compatibility-matrix)
8. [Validation Strategy](#8-validation-strategy)
9. [Project Phasing and Milestones](#9-project-phasing-and-milestones)
10. [Risk Register](#10-risk-register)

---

## 1. Product Vision and Goals

### 1.1 Project Name

**OpenCoulomb**

Rationale: The name preserves immediate recognition for the 10,000+ existing Coulomb users while the "Open" prefix signals the key differentiator -- no proprietary dependencies, no license fees, genuinely open-source. It is short, searchable, and unambiguous. Alternative names considered and rejected:

| Candidate | Rejected Because |
|-----------|-----------------|
| PyCoulomb | Already used informally for elastic_stresses_py; implies Python-only |
| FreeCoulomb | Could imply "free as in beer" without the "open" connotation |
| Coulomb.py | Confusing filename/module collision; too narrow |
| LibCoulomb | Implies a library, not an application |
| Seismostress | Too generic; loses Coulomb branding |

### 1.2 What This Software Is

OpenCoulomb is a standalone, open-source application for computing Coulomb failure stress changes, static displacements, strains, and stress tensors from earthquake fault slip, magmatic intrusion, and tectonic loading in an elastic half-space. It is a complete, license-free replacement for the USGS Coulomb 3.4 MATLAB software.

It provides:

- The full Okada (1992) DC3D analytical dislocation solution
- Coulomb failure stress calculation on specified and optimally oriented receiver faults
- 2D map, cross-section, and 3D visualization
- A command-line interface for scripting and batch processing
- An interactive graphical interface for model building and exploration
- Full compatibility with Coulomb 3.4 `.inp` input files and output formats

### 1.3 What This Software Is Not

- **Not a general finite-element code.** OpenCoulomb solves the Okada (1992) analytical solution for rectangular dislocations in a homogeneous, isotropic elastic half-space. It does not handle heterogeneous media, topography, or arbitrary fault geometries natively.
- **Not a viscoelastic or time-dependent model.** Post-seismic relaxation, afterslip, and viscoelastic deformation are out of scope. Users requiring these capabilities should use PSGRN/PSCMP or RELAX.
- **Not a seismic waveform tool.** OpenCoulomb computes static (final) deformation, not dynamic wave propagation.
- **Not a fork of Coulomb 3.4.** This is a clean-room reimplementation based on published algorithms (Okada 1992; King, Stein & Lin 1994). No MATLAB code is copied or translated. The original Coulomb software remains available for users who have MATLAB licenses.

### 1.4 Target Users

| User Group | Needs | Priority |
|-----------|-------|----------|
| **Research seismologists** | Compute CFS for published studies, batch processing, scripting, reproducible workflows | Primary |
| **University students** | Free access for coursework, teaching labs, thesis projects; low barrier to entry | Primary |
| **Geophysicists at agencies** (USGS, GNS, INGV, etc.) | Rapid post-earthquake stress analysis, operational use without license procurement | Primary |
| **Structural geologists** | Tectonic stress modeling, fault interaction studies | Secondary |
| **Volcanologists** | Dike/sill/chamber stress modeling | Secondary |
| **Software developers** | API for integration into larger workflows, earthquake hazard pipelines | Secondary |

### 1.5 Key Differentiators

| Differentiator | vs. Coulomb 3.4 (MATLAB) | vs. elastic_stresses_py | vs. Pyrocko |
|---------------|--------------------------|------------------------|-------------|
| No license cost | Requires MATLAB ($2k-14k+) | Free | Free |
| Interactive GUI | Yes (MATLAB GUIDE) | No | Limited (Snuffler) |
| CLI/scripting | No | Yes | Yes |
| `.inp` file compat | Yes (native) | Yes (partial) | No |
| Cross-platform install | Needs MATLAB | Needs gfortran, gcc, cutde | Complex |
| Pip-installable | No | Partial | Partial |
| Web-based GUI option | No | No | No |
| Batch processing | Manual only | Yes | Yes |
| Python API | No | Yes | Yes |
| Active maintenance | Ended (3.4) | Active | Active |

### 1.6 Project Goals (Prioritized)

1. **G1**: Numerical accuracy matching Coulomb 3.4 to within floating-point tolerance on all computation outputs
2. **G2**: Full Coulomb 3.4 `.inp` file compatibility -- every valid Coulomb 3.4 input file must parse and compute correctly
3. **G3**: Zero proprietary dependencies -- installable with `pip install opencoulomb` on Linux, macOS, and Windows
4. **G4**: CLI-first architecture enabling scripted, reproducible, batch workflows
5. **G5**: Interactive GUI for model building, visualization, and exploration
6. **G6**: Publication-quality visualization output (PDF, SVG, PNG)
7. **G7**: Python API for programmatic access and integration into larger scientific workflows
8. **G8**: Comprehensive documentation including tutorials, API reference, and migration guide from Coulomb 3.4

### 1.7 Success Criteria

| Criterion | Metric | Target |
|-----------|--------|--------|
| Numerical fidelity | Max absolute difference from Coulomb 3.4 on all example files | < 1e-6 bar (stress), < 1e-9 m (displacement) |
| File compatibility | Percentage of Coulomb 3.4 example `.inp` files that parse and compute correctly | 100% |
| Installation success | One-command install on clean Python 3.10+ environments | Works on Ubuntu 22+, macOS 13+, Windows 10+ |
| Performance | Time to compute 100x100 grid with 10 source faults | <= Coulomb 3.4 MATLAB time |
| Test coverage | Line coverage of core computation modules | >= 95% |
| Test coverage | Line coverage of I/O and CLI modules | >= 85% |
| Documentation | All public API functions documented | 100% |

---

## 2. Functional Requirements

Requirements are organized into three tiers reflecting implementation priority.

### 2.1 Tier 1 -- MVP (Minimum Viable Product)

Tier 1 delivers a usable tool for researchers who currently use Coulomb 3.4 for batch/scripting workflows. No GUI.

#### 2.1.1 Input Parsing

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T1-INP-01 | Parse Coulomb 3.4 `.inp` files (full format) | All ~20 example `.inp` files from coulomb3402.zip parse without error |
| T1-INP-02 | Parse header parameters: PR1, PR2, DEPTH, E1, E2, FRIC, XSYM, YSYM | Extracted values match file contents exactly |
| T1-INP-03 | Parse regional stress parameters: S1DR/S1DP/S1IN/S1GD, S2DR/S2DP/S2IN/S2GD, S3DR/S3DP/S3IN/S3GD | All 12 parameters extracted |
| T1-INP-04 | Parse fault elements: coordinates, KODE, slip values, dip, depth range, label | All KODE types (100, 200, 300, 400, 500) parsed correctly |
| T1-INP-05 | Distinguish source faults (have non-zero slip) from receiver faults (zero slip) | Source/receiver classification matches Coulomb 3.4 behavior |
| T1-INP-06 | Parse grid parameters: start-x, start-y, finish-x, finish-y, x-increment, y-increment | Grid dimensions and spacing extracted correctly |
| T1-INP-07 | Parse `#fixed=` parameter to determine source/receiver boundary | Boundary index correctly identified |
| T1-INP-08 | Handle both km-local and lon/lat coordinate inputs | Coordinate mode detected and handled |
| T1-INP-09 | Validate input: detect and report malformed files with line numbers | Clear error messages for common format errors |

#### 2.1.2 Okada DC3D Computation Engine

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T1-OKA-01 | Implement DC3D: displacement + 9 gradient components for finite rectangular fault | Output matches Okada (1992) reference values to 1e-10 relative error |
| T1-OKA-02 | Implement DC3D0: displacement + gradients for point source | Output matches reference values |
| T1-OKA-03 | Support all three dislocation components: strike-slip, dip-slip, tensile | Each component tested independently and in combination |
| T1-OKA-04 | Handle edge cases: observation point on fault plane, at surface, at depth=0 | No NaN/Inf; graceful degradation or singularity handling per Okada's conventions |
| T1-OKA-05 | Accept configurable Poisson's ratio (alpha = 1/(2*(1-nu))) | Non-default nu values produce correct results |
| T1-OKA-06 | Performance: vectorized computation over grid points | 100x100 grid with 10 faults computes in < 10 seconds on a modern CPU |

#### 2.1.3 Stress and Strain Computation

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T1-STR-01 | Convert displacement gradients to strain tensor (symmetric part of gradient) | 6 independent strain components correct |
| T1-STR-02 | Convert strain to stress via Hooke's law for isotropic medium | sk/gk formulation matches Coulomb 3.4 `Okada_halfspace.m` |
| T1-STR-03 | Apply 0.001 unit conversion factor (km distance / m displacement) | Stress output in bar, matching Coulomb conventions |
| T1-STR-04 | Rotate stress tensor from fault-local to geographic coordinates | `tensor_trans` equivalent produces identical rotation |
| T1-STR-05 | Superpose (sum) stress contributions from multiple source faults | Linear superposition validated against multi-fault Coulomb examples |

#### 2.1.4 Coulomb Failure Stress Calculation

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T1-CFS-01 | Resolve full 3D stress tensor onto receiver fault plane (strike, dip, rake) | Shear and normal stress components match Coulomb 3.4 `calc_coulomb.m` |
| T1-CFS-02 | Compute CFS = shear + friction * normal | CFS values match Coulomb 3.4 output to floating-point tolerance |
| T1-CFS-03 | Support user-specified friction coefficient (default 0.4) | Non-default friction values produce correct CFS |
| T1-CFS-04 | Compute CFS on a 2D grid at specified depth | Grid CFS output matches Coulomb 3.4 dcff.cou format |
| T1-CFS-05 | Compute CFS on individual receiver fault elements | Per-element CFS matches Coulomb 3.4 element output |

#### 2.1.5 Optimally Oriented Planes (OOPs)

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T1-OOP-01 | Accept regional stress field specification (3 principal stresses with direction, dip, intensity, gradient) | All 12 regional stress parameters used |
| T1-OOP-02 | Combine regional stress with earthquake-induced perturbation | Total stress field computed correctly |
| T1-OOP-03 | Find fault orientation maximizing CFS using Mohr-Coulomb criterion | OOP strike/dip matches Coulomb 3.4 for all test cases |
| T1-OOP-04 | Compute and display CFS on the optimally oriented plane at each grid point | Spatial pattern matches Coulomb 3.4 OOP output |

#### 2.1.6 Displacement Field

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T1-DIS-01 | Compute East, North, Up displacement components on a 2D grid | Displacement magnitudes match Coulomb 3.4 |
| T1-DIS-02 | Compute displacement at arbitrary points (not just grid) | Point displacement matches single-point Coulomb query |
| T1-DIS-03 | Support surface (z=0) and subsurface (z=DEPTH) displacement grids | Both modes produce correct output |

#### 2.1.7 Cross-Section Computation

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T1-XSC-01 | Compute stress/displacement along a vertical cross-section profile | Cross-section values match Coulomb 3.4 `dcff_section.cou` |
| T1-XSC-02 | User-specified profile endpoints, depth range, and resolution | All profile parameters configurable |
| T1-XSC-03 | Support CFS, normal stress, shear stress, and displacement fields in cross-section | All field types available |

#### 2.1.8 Visualization (Static)

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T1-VIZ-01 | 2D color-filled contour map of CFS at specified depth | Contour pattern visually matches Coulomb 3.4 output |
| T1-VIZ-02 | Fault trace overlay (source faults as solid lines, receivers as dashed) | Fault positions and styles correct |
| T1-VIZ-03 | Color scale with symmetric diverging colormap (red = positive CFS, blue = negative) | Color range matches Coulomb convention |
| T1-VIZ-04 | Cross-section visualization (vertical slice with color-filled stress) | Cross-section plot matches Coulomb 3.4 section output |
| T1-VIZ-05 | Displacement vector arrow plot (quiver) | Arrow directions and magnitudes correct |
| T1-VIZ-06 | Export to PNG, PDF, SVG | Vector formats retain editability |
| T1-VIZ-07 | Configurable: color scale limits, contour intervals, figure size, DPI | Parameters exposed via CLI flags and config |

#### 2.1.9 CLI Interface

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T1-CLI-01 | Main entry point: `opencoulomb compute <input.inp>` | Runs full computation pipeline |
| T1-CLI-02 | Output type selection: `--output {cfs,displacement,strain,stress,all}` | Each output type produces correct files |
| T1-CLI-03 | Visualization: `--plot {map,section,displacement,none}` | Each plot type generated correctly |
| T1-CLI-04 | Receiver specification: `--receiver {specified,oops}` | Both receiver modes functional |
| T1-CLI-05 | Parameter overrides: `--friction`, `--depth`, `--poisson`, `--young` | Overrides take precedence over `.inp` file values |
| T1-CLI-06 | Grid overrides: `--grid-start`, `--grid-end`, `--grid-spacing` | Grid parameters overrideable from CLI |
| T1-CLI-07 | Output format: `--format {coulomb,csv,text}` | Each output format correct |
| T1-CLI-08 | Verbosity: `-v`, `-vv`, `--quiet` | Appropriate output levels |
| T1-CLI-09 | Version: `--version` | Prints version string |
| T1-CLI-10 | Help: `--help`, `<command> --help` | Complete usage documentation |

#### 2.1.10 Output Files

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T1-OUT-01 | Write `dcff.cou` -- Coulomb stress grid file | File format byte-identical to Coulomb 3.4 output |
| T1-OUT-02 | Write `dcff_section.cou` -- cross-section stress data | Format matches Coulomb 3.4 |
| T1-OUT-03 | Write `coulomb_out.dat` -- primary stress change grid | Format matches Coulomb 3.4 |
| T1-OUT-04 | Write `gmt_fault_surface.dat` -- fault traces at surface | Format matches Coulomb 3.4 |
| T1-OUT-05 | Write CSV export with all stress components | Header row + data rows, documented column order |
| T1-OUT-06 | Write text summary of computation parameters and results | Human-readable log of input/output |

### 2.2 Tier 2 -- Full Parity with Coulomb 3.4

Tier 2 achieves feature parity with the MATLAB version, including an interactive GUI.

#### 2.2.1 Interactive GUI

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T2-GUI-01 | Main window with map view, fault display, and control panels | Layout comparable to Coulomb 3.4 main_menu_window |
| T2-GUI-02 | Fault element editor: add, modify, delete source and receiver faults | All ELEMENT parameters editable |
| T2-GUI-03 | Interactive fault drawing on map (click start/end points) | Faults drawn directly on visualization |
| T2-GUI-04 | Material properties editor (Poisson, Young, friction) | All properties editable with validation |
| T2-GUI-05 | Regional stress field editor | All 12 stress parameters editable |
| T2-GUI-06 | Grid parameter editor (bounds, spacing, depth) | Grid visible on map, adjustable |
| T2-GUI-07 | Computation trigger with progress indicator | Progress bar during long computations |
| T2-GUI-08 | Result visualization panel with field selector (CFS, normal, shear, displacement, strain) | All FUNC_SWITCH equivalent modes |
| T2-GUI-09 | Cross-section tool: draw profile line on map, display vertical slice | Interactive profile selection |
| T2-GUI-10 | Color scale controls (limits, colormap, symmetric/asymmetric) | Real-time update on change |
| T2-GUI-11 | File menu: open `.inp`, save `.inp`, save results, export figure | Standard file operations |
| T2-GUI-12 | Preferences/settings dialog | Persistent user preferences |

#### 2.2.2 3D Visualization

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T2-3D-01 | 3D fault geometry display (source and receiver faults as surfaces) | Fault patches rendered with correct geometry |
| T2-3D-02 | Interactive rotation, zoom, pan in 3D view | Smooth 60fps interaction |
| T2-3D-03 | Stress mapped onto fault surfaces (color by CFS) | Color mapping correct |
| T2-3D-04 | Slip vector arrows on fault patches | Arrow direction and magnitude correct |
| T2-3D-05 | Depth axis with labeled scale | Depth positive downward |

#### 2.2.3 Earthquake Catalog Integration

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T2-CAT-01 | Import Global CMT focal mechanisms (CSV/NDK format) | CMT mechanisms plotted as beach balls |
| T2-CAT-02 | Import ISC earthquake catalogs | Earthquakes plotted as circles sized by magnitude |
| T2-CAT-03 | Import USGS ComCat catalogs (via API or CSV) | Same as ISC |
| T2-CAT-04 | Filter catalog by magnitude, depth, time, spatial extent | Filters update display interactively |
| T2-CAT-05 | Overlay earthquakes on stress maps | Seismicity correlation with CFS visible |

#### 2.2.4 GPS Displacement Comparison

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T2-GPS-01 | Import GPS displacement observation files (lon, lat, E, N, U, sigE, sigN, sigU) | File parsed correctly |
| T2-GPS-02 | Compute modeled displacement at GPS station locations | Modeled displacements match Coulomb 3.4 |
| T2-GPS-03 | Display observed vs. modeled displacement vectors | Two-color vector overlay |
| T2-GPS-04 | Compute residual (observed - modeled) | Residual statistics (RMS, chi-squared) reported |
| T2-GPS-05 | Export GPS comparison to CSV | `GPS_output.csv` format matches Coulomb 3.4 |

#### 2.2.5 Advanced Fault Handling

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T2-FLT-01 | All KODE types: 100 (standard), 200 (tensile+RL), 300 (tensile+reverse), 400 (point), 500 (tensile+inflation) | Each KODE type produces correct results |
| T2-FLT-02 | Fault subdivision into smaller patches | Subdivided fault produces convergent results |
| T2-FLT-03 | Slip taper at fault edges | Taper function matches `taper_calc.m` |
| T2-FLT-04 | Nodal plane calculations from focal mechanisms | Both nodal planes extracted correctly |
| T2-FLT-05 | Wells-Coppersmith magnitude-to-fault scaling | Fault dimensions from magnitude match published regressions |
| T2-FLT-06 | Write `.inp` files (model export) | Round-trip: read `.inp`, write `.inp`, read again -- identical model |

#### 2.2.6 Seismicity Rate Change

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T2-SRC-01 | Dieterich (1994) rate/state seismicity rate change model | Rate change values match Coulomb 3.4 `seis_rate_change.m` |
| T2-SRC-02 | Configurable: A-sigma (stressing rate parameter), reference rate, time window | All parameters adjustable |
| T2-SRC-03 | Spatial map of seismicity rate change | Map display with appropriate color scale |

#### 2.2.7 Additional Output Formats

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T2-OUT-01 | `Strain.cou` -- strain tensor grid | Format matches Coulomb 3.4 |
| T2-OUT-02 | `dilatation_section.cou` -- cross-section dilatation | Format matches |
| T2-OUT-03 | `gmt_fault_map_proj.dat` -- projected fault surfaces | Format matches |
| T2-OUT-04 | `gmt_fault_calc_dep.dat` -- faults at calculation depth | Format matches |
| T2-OUT-05 | `Cross_section.dat` -- section parameters and data | Format matches |
| T2-OUT-06 | `Focal_mech_stress_output.csv` -- stress at focal mechanism locations | Format matches |
| T2-OUT-07 | Google Earth KML export | KML file opens correctly in Google Earth |
| T2-OUT-08 | GMT-compatible output files | Files plot correctly with GMT scripts |

#### 2.2.8 Publication-Quality Output

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T2-PUB-01 | PDF export with vector graphics (editable text, lines, fills) | Text selectable, lines not rasterized |
| T2-PUB-02 | SVG export | Imports correctly into Inkscape/Illustrator |
| T2-PUB-03 | High-resolution PNG (300+ DPI) | Suitable for journal submission |
| T2-PUB-04 | Configurable: font size, line width, colormap, annotation | All visual parameters adjustable |
| T2-PUB-05 | Multi-panel figure layout (map + cross-section + displacement) | Compound figures exportable |

### 2.3 Tier 3 -- Beyond Coulomb

Tier 3 provides capabilities that the MATLAB Coulomb never had.

#### 2.3.1 Python API

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T3-API-01 | Importable Python package: `import opencoulomb` | Package imports without side effects |
| T3-API-02 | Programmatic model construction (no `.inp` file required) | Build model entirely in Python code |
| T3-API-03 | Direct access to Okada DC3D function | `opencoulomb.okada.dc3d(...)` returns displacement + gradients |
| T3-API-04 | Fault, Grid, Model, and Result dataclasses | Clean, documented data structures |
| T3-API-05 | Jupyter notebook integration | Results display inline in notebooks |
| T3-API-06 | Pandas DataFrame output option | Results as DataFrame with labeled columns |

#### 2.3.2 Batch Processing

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T3-BAT-01 | Process multiple `.inp` files in one command: `opencoulomb batch *.inp` | All files processed, results collected |
| T3-BAT-02 | Parameter sweep: vary friction, depth, slip across runs | Sweep configuration via YAML/TOML file |
| T3-BAT-03 | Parallel computation (multiprocessing) | Near-linear speedup on multi-core systems |
| T3-BAT-04 | Output summary table across batch runs | CSV/table comparing key metrics across parameter values |

#### 2.3.3 Web-Based GUI

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T3-WEB-01 | Browser-based interface (no desktop installation for end users) | Opens in Chrome, Firefox, Safari |
| T3-WEB-02 | Remote operation (run on server, view in browser) | Works over SSH tunnel or VPN |
| T3-WEB-03 | Interactive 3D visualization (WebGL-based) | Smooth rotation/zoom in browser |
| T3-WEB-04 | Collaborative model sharing (URL-based) | Share model state via URL |

#### 2.3.4 Extended Physics

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T3-PHY-01 | Layered half-space option (via PSGRN/PSCMP or equivalent Green's functions) | Results for layered model differ from homogeneous |
| T3-PHY-02 | Triangular fault elements (for complex fault geometry) | Irregular fault surfaces modeled |
| T3-PHY-03 | Topographic correction (first-order) | Surface relief affects near-surface stress |

#### 2.3.5 Community and Ecosystem

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| T3-COM-01 | Plugin system for user-contributed extensions | Plugin discovery, loading, and execution |
| T3-COM-02 | Example gallery (Jupyter notebooks with known earthquakes) | 10+ worked examples |
| T3-COM-03 | GeoJSON input/output for fault geometries | Standard GIS interoperability |
| T3-COM-04 | NetCDF output for gridded results | CF-compliant NetCDF files |
| T3-COM-05 | SRCMOD finite fault model import | Published slip models loadable |

---

## 3. Technology Decisions

### 3.1 Implementation Language: Python

**Decision**: Python 3.10+

**Justification**:

| Factor | Python | C/C++ | Rust | Julia |
|--------|--------|-------|------|-------|
| Target user familiarity | Very high (standard in geoscience) | Low | Very low | Low-medium |
| NumPy/SciPy ecosystem | Native | Via bindings | Via bindings | Native equivalent |
| Visualization libraries | Matplotlib, Plotly, PyVista | VTK (complex API) | Plotters (immature) | Makie (good but niche) |
| Installation simplicity | `pip install` | Compilation required | Compilation required | Separate runtime |
| Jupyter integration | Native | No | No | Native |
| GUI frameworks | PyQt, web-based (many options) | Qt | Limited | Limited |
| Community contribution barrier | Low | High | Medium | Medium |
| Performance ceiling | Good with NumPy vectorization + optional C extensions | Highest | Highest | High |
| Existing Coulomb implementations to reference | elastic_stresses_py (MIT), Pyrocko | DC3D.f90 | None | None |

**Key concern -- performance**: The Okada DC3D function is called O(N_grid * N_faults) times. For a 200x200 grid with 50 faults, that is 2,000,000 calls. Mitigation strategy:

1. **Primary**: NumPy vectorization -- compute all grid points simultaneously for each fault element using array broadcasting. This eliminates the Python loop over grid points.
2. **Secondary**: If vectorized NumPy is insufficient, wrap the original Fortran DC3D via `ctypes` or `f2py`. The `okada_wrapper` package (MIT license) provides a proven pattern for this.
3. **Tertiary**: For extreme cases, implement the inner loop in C via Cython or write a dedicated C extension.

Profiling gates: If Tier 1 MVP computation on a 100x100 grid with 10 faults takes > 10 seconds, escalate to the secondary approach.

### 3.2 Core Computation Stack

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| Array computation | NumPy | >= 1.24 | Vectorized Okada computation, tensor operations |
| Scientific computing | SciPy | >= 1.10 | Interpolation, optimization (OOP solver), coordinate transforms |
| Data structures | Python dataclasses + attrs | stdlib + >= 23.1 | Fault, Grid, Model, Result types |
| Coordinate transforms | pyproj | >= 3.5 | Lon/lat to local km conversion (UTM, custom projections) |
| Unit handling | Internal constants module | -- | bar, km, m, degrees -- no external unit library overhead |

### 3.3 Okada DC3D Implementation Strategy

The Okada (1992) DC3D solution is the most performance-critical component. Implementation approach:

**Phase 1 (MVP)**: Pure NumPy vectorized implementation.
- Translate the analytical expressions from Okada (1992) directly into vectorized NumPy.
- Each sub-function (UA, UB, UC for finite faults; UA0, UB0, UC0 for point sources) becomes a function operating on arrays of observation points.
- Reference: The expressions are well-documented in the original paper and the NIED supplementary materials.
- Validation: Test against the original Fortran DC3D output for a comprehensive set of test points.

**Phase 2 (if needed)**: Fortran wrapper via ctypes.
- Wrap the original DC3D Fortran subroutine using `ctypes` (following the `okada_wrapper` pattern).
- Provides bit-identical results to the reference implementation.
- Falls back to pure Python if Fortran compiler unavailable.

**Phase 3 (Tier 3)**: C extension for maximum performance.
- Only if profiling shows the NumPy implementation is the bottleneck after vectorization.

### 3.4 Visualization Stack

| Layer | Library | Purpose |
|-------|---------|---------|
| **Static 2D plots** | Matplotlib >= 3.7 | Contour maps, cross-sections, quiver plots, publication figures |
| **Interactive 2D** | Matplotlib (Qt/TkAgg backend) or Plotly | Zoom, pan, hover in GUI |
| **3D visualization** | PyVista >= 0.42 (wraps VTK) | 3D fault surfaces, interactive rotation |
| **Web interactive** | Plotly >= 5.18 | Browser-based interactive plots (Tier 3 web GUI) |
| **Map backgrounds** | Cartopy >= 0.22 | Coastlines, borders, geographic projections |
| **Colormaps** | cmcrameri >= 1.7 | Scientific colormaps (Crameri 2018), perceptually uniform, CVD-safe |

Color convention: Diverging colormap centered on zero. Red/warm = positive CFS (brought closer to failure). Blue/cool = negative CFS (stress shadow). Default: `vik` from cmcrameri (or `RdBu_r` from Matplotlib as fallback).

### 3.5 GUI Framework

**Decision**: Desktop GUI via PyQt6, with a web-based GUI as a Tier 3 goal.

**Comparison of options**:

| Framework | Pros | Cons | Verdict |
|-----------|------|------|---------|
| **PyQt6** | Mature, fast, native look, Matplotlib embedding proven, QtDesigner | GPL/commercial dual license; 50MB install | **Tier 2 choice** |
| **PySide6** | Same as PyQt6 but LGPL license | Slightly behind PyQt in community | Acceptable alternative |
| **Tkinter** | Stdlib, no extra deps | Dated look, limited widgets, poor Matplotlib integration | Rejected |
| **wxPython** | Native look | Complex build, declining community | Rejected |
| **Streamlit** | Rapid prototyping, web-based | Limited interactivity, no custom widgets, not a real GUI | Rejected for main GUI |
| **FastAPI + React** | Maximum flexibility, remote access, modern UX | Two codebases (Python + JS), heavy engineering | **Tier 3 web GUI** |
| **Panel (HoloViz)** | Python-only web apps, good Matplotlib/Plotly integration | Less mature for complex GUIs | Consider for Tier 3 |

**License note**: If GPL is a concern, PySide6 (LGPL) provides an identical API and is a drop-in replacement. The choice between PyQt6 and PySide6 can be deferred to implementation.

### 3.6 File I/O Approach

| Format | Library | Notes |
|--------|---------|-------|
| `.inp` (Coulomb) | Custom parser (regex + fixed-width) | The format is fixed-width with some irregularities; a dedicated parser is required |
| `.cou` (Coulomb output) | Custom writer | Fixed-width columnar output |
| CSV | Python `csv` module or Pandas | Standard tabular output |
| JSON/GeoJSON | Python `json` module | Fault geometries for GIS |
| NetCDF | `netCDF4` or `xarray` | Gridded results (Tier 3) |
| KML | `simplekml` | Google Earth export (Tier 2) |
| HDF5 | `h5py` | Binary checkpoint/resume (Tier 3) |

The `.inp` parser deserves special attention. It must handle:
- Flexible whitespace (tabs and spaces mixed)
- Comment lines (lines starting with `#` in some contexts)
- The transition from header to fault elements to grid parameters
- Both integer and scientific notation for numeric fields
- Optional fault labels at end of element lines
- Variant formats: `Source_Patch`, `Source_WC`, `Source_FM`, `Receiver_Horizontal_Profile`

### 3.7 Testing Framework

| Tool | Purpose |
|------|---------|
| **pytest** >= 7.4 | Test runner, fixtures, parametrize |
| **pytest-cov** | Coverage reporting |
| **hypothesis** | Property-based testing (especially for coordinate transforms) |
| **numpy.testing** | `assert_allclose` for numerical comparisons |
| **pytest-benchmark** | Performance regression testing |

Test organization:
```
tests/
    unit/
        test_okada.py           # DC3D against reference values
        test_stress.py          # Hooke's law, tensor rotation
        test_coulomb.py         # CFS calculation
        test_coordinates.py     # Coordinate transforms
        test_oops.py            # Optimally oriented planes
    integration/
        test_pipeline.py        # Full .inp -> output pipeline
        test_inp_parsing.py     # Parser on all example files
        test_output_formats.py  # Output format correctness
    validation/
        test_vs_coulomb34.py    # Numerical comparison against Coulomb 3.4 reference outputs
        test_vs_elastic_stresses.py  # Cross-validation against elastic_stresses_py
        test_published.py       # Reproduce published results (King+Stein 1994, etc.)
    performance/
        test_benchmarks.py      # Performance regression tests
```

### 3.8 Distribution Strategy

| Channel | Method | Target Audience |
|---------|--------|-----------------|
| **PyPI** | `pip install opencoulomb` | Primary: all users |
| **conda-forge** | `conda install -c conda-forge opencoulomb` | Users with Anaconda/Miniconda |
| **GitHub releases** | Source tarball + wheel | Developers |
| **Docker** | `docker run opencoulomb` | Server deployment, reproducibility |
| **Standalone binary** | PyInstaller / Nuitka (Tier 3) | Users who cannot install Python |

**Dependency policy**: Minimize required dependencies for Tier 1.

Core (Tier 1) dependencies:
```
numpy >= 1.24
scipy >= 1.10
matplotlib >= 3.7
click >= 8.1       # CLI framework
```

Optional dependencies (installed via extras):
```
pip install opencoulomb[gui]     # + PyQt6, PyVista
pip install opencoulomb[geo]     # + Cartopy, pyproj
pip install opencoulomb[web]     # + Plotly, FastAPI (Tier 3)
pip install opencoulomb[all]     # Everything
```

### 3.9 Project Structure

```
opencoulomb/
    pyproject.toml              # Build configuration (PEP 621)
    LICENSE                     # Apache 2.0
    README.md                   # Project overview
    CHANGELOG.md                # Version history
    CONTRIBUTING.md             # Contributor guide

    src/
        opencoulomb/
            __init__.py         # Package root, version
            __main__.py         # python -m opencoulomb support

            # Core computation (Tier 1)
            core/
                __init__.py
                okada.py        # DC3D and DC3D0 implementation
                stress.py       # Hooke's law, tensor operations
                coulomb.py      # CFS calculation
                coordinates.py  # Coordinate transforms
                oops.py         # Optimally oriented planes
                displacement.py # Displacement field computation
                model.py        # Model orchestration (pipeline)

            # Data structures
            types/
                __init__.py
                fault.py        # Fault, FaultElement, KODE enum
                grid.py         # Grid, GridParameters
                material.py     # MaterialProperties
                stress_field.py # RegionalStress, StressTensor
                result.py       # ComputationResult, GridResult

            # I/O (Tier 1)
            io/
                __init__.py
                inp_parser.py   # .inp file reader
                inp_writer.py   # .inp file writer (Tier 2)
                cou_writer.py   # .cou output writer
                csv_writer.py   # CSV export
                dat_writer.py   # .dat file writer
                catalog.py      # Earthquake catalog reader (Tier 2)
                gps.py          # GPS data reader (Tier 2)
                geojson.py      # GeoJSON I/O (Tier 3)
                netcdf.py       # NetCDF I/O (Tier 3)

            # CLI (Tier 1)
            cli/
                __init__.py
                main.py         # Click CLI entry point
                compute.py      # 'compute' command
                plot.py         # 'plot' command
                batch.py        # 'batch' command (Tier 3)
                info.py         # 'info' command (inspect .inp files)

            # Visualization (Tier 1 static, Tier 2 interactive)
            viz/
                __init__.py
                maps.py         # 2D stress/displacement maps
                sections.py     # Cross-section plots
                faults.py       # Fault trace rendering
                displacement.py # Displacement vector plots
                colormaps.py    # Color scale configuration
                three_d.py      # 3D visualization (Tier 2)
                export.py       # Figure export (PDF, SVG, PNG)

            # GUI (Tier 2)
            gui/
                __init__.py
                app.py          # Main application window
                fault_editor.py # Fault element editor
                map_panel.py    # Map/visualization panel
                controls.py     # Parameter controls
                preferences.py  # Settings dialog

            # Web GUI (Tier 3)
            web/
                __init__.py
                server.py       # FastAPI/Panel server
                # ... frontend in separate directory

    tests/                      # Test suite (structure above)
    docs/                       # Documentation
    examples/                   # Example .inp files and notebooks
    benchmarks/                 # Performance benchmarks
    scripts/                    # Development scripts
```

### 3.10 License

**Decision**: Apache License 2.0

Rationale:
- Permissive: allows commercial use, modification, distribution
- Patent grant: provides explicit patent protection (important for algorithm implementations)
- Compatible with scientific community norms
- Compatible with NumPy (BSD), Matplotlib (PSF), SciPy (BSD) licenses
- More protective than MIT/BSD (patent clause) while remaining permissive
- Not GPL: avoids forcing derivative works to be GPL (important for agency/industry adoption)

Note: If PyQt6 is used (GPL), the GUI module must be clearly separated as an optional component. The core library remains Apache 2.0. Alternatively, use PySide6 (LGPL) to avoid license tension entirely.

---

## 4. Input/Output Specification

### 4.1 Coulomb `.inp` File Format (Complete Specification)

The `.inp` file is a fixed-width ASCII text format. This section documents the complete format as used by Coulomb 3.4.

#### 4.1.1 Overall Structure

```
Line 1:     Title line 1 (free text, max ~80 chars)
Line 2:     Title line 2 (free text, max ~80 chars)
Line 3:     Model parameters (fixed-format key=value pairs, may span 2-4 physical lines)
Line 4+:    Regional stress parameters (3 principal stresses)
            [blank line]
            Column header line for fault elements
            Source fault elements (1 per line)
            [blank line or divider]
            Column header line for receiver fault elements
            Receiver fault elements (1 per line)
            [blank line]
            "Grid Parameters" keyword line
            Grid parameter lines (6 lines, numbered 1-6)
            [optional: "Cross Section" keyword and parameters]
            [optional: map display parameters]
```

#### 4.1.2 Model Parameters Block

The model parameters appear on lines 3-4 of the file. The exact format is:

```
#reg1=  0  #reg2=  0  #fixed=  NNN  sym=  X
 PR1=       0.250 PR2=       0.250 DEPTH=      DD.D
  E1=  0.800000E+06  E2=  0.800000E+06 XLIM=     0.000 YLIM=     0.000
FRIC=       0.400
  S1DR=  DDD.DDDD S1DP=   DD.DDDD S1IN=  III.III  S1GD=  GGG.GGG
  S3DR=  DDD.DDDD S3DP=   DD.DDDD S3IN=  III.III  S3GD=  GGG.GGG
  S2DR=  DDD.DDDD S2DP=  -DD.DDD  S2IN=    I.III  S2GD=  GGG.GGG
```

| Parameter | Type | Default | Units | Description |
|-----------|------|---------|-------|-------------|
| `#reg1` | int | 0 | -- | Region 1 identifier |
| `#reg2` | int | 0 | -- | Region 2 identifier |
| `#fixed` | int | N/A | -- | Number of fixed (source) fault elements |
| `sym` | int | 1 | -- | Symmetry flag (1 = none) |
| `PR1` | float | 0.250 | -- | Poisson's ratio, region 1 |
| `PR2` | float | 0.250 | -- | Poisson's ratio, region 2 |
| `DEPTH` | float | 10.0 | km | Default calculation depth |
| `E1` | float | 8.0e5 | bar | Young's modulus, region 1 |
| `E2` | float | 8.0e5 | bar | Young's modulus, region 2 |
| `XLIM` | float | 0.0 | km | X symmetry axis (alias: XSYM) |
| `YLIM` | float | 0.0 | km | Y symmetry axis (alias: YSYM) |
| `FRIC` | float | 0.400 | -- | Effective friction coefficient (mu') |

#### 4.1.3 Regional Stress Parameters

| Parameter | Type | Units | Description |
|-----------|------|-------|-------------|
| `S1DR` | float | degrees | Sigma-1 (max compressive) direction (azimuth from North, clockwise) |
| `S1DP` | float | degrees | Sigma-1 dip (from horizontal) |
| `S1IN` | float | bar | Sigma-1 intensity (magnitude) |
| `S1GD` | float | bar/km | Sigma-1 gradient with depth |
| `S2DR` | float | degrees | Sigma-2 (intermediate) direction |
| `S2DP` | float | degrees | Sigma-2 dip |
| `S2IN` | float | bar | Sigma-2 intensity |
| `S2GD` | float | bar/km | Sigma-2 gradient |
| `S3DR` | float | degrees | Sigma-3 (min compressive / max tensile) direction |
| `S3DP` | float | degrees | Sigma-3 dip |
| `S3IN` | float | bar | Sigma-3 intensity |
| `S3GD` | float | bar/km | Sigma-3 gradient |

Note: S1 >= S2 >= S3 in magnitude (compression positive). A normal faulting regime has S1 vertical. A thrust regime has S3 vertical. Strike-slip has S2 vertical.

#### 4.1.4 Fault Element Format

Column header line:
```
  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot
```

Element data line (fixed-width):
```
  xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx  label_text
```

| Column | Field | Type | Units | Description |
|--------|-------|------|-------|-------------|
| 1 | Number | int | -- | Element index (1-based) |
| 2 | X-start | float | km | Starting X coordinate (East) |
| 3 | Y-start | float | km | Starting Y coordinate (North) |
| 4 | X-fin | float | km | Ending X coordinate |
| 5 | Y-fin | float | km | Ending Y coordinate |
| 6 | Kode | int | -- | Element type code (100, 200, 300, 400, 500) |
| 7 | rt.lat / shear | float | m | Slip component 1 (interpretation depends on KODE) |
| 8 | reverse / normal | float | m | Slip component 2 (interpretation depends on KODE) |
| 9 | dip | float | degrees | Dip angle (0-90, always positive) |
| 10 | top | float | km | Fault top depth |
| 11 | bot | float | km | Fault bottom depth |
| 12 | label | string | -- | Optional text label |

#### 4.1.5 KODE Interpretation

| KODE | Column 7 Meaning | Column 8 Meaning | Use Case |
|------|-------------------|-------------------|----------|
| 100 | Right-lateral slip (m) | Reverse slip (m) | Standard earthquake fault |
| 200 | Tensile opening (m) | Right-lateral slip (m) | Dike + strike-slip |
| 300 | Tensile opening (m) | Reverse slip (m) | Dike + dip-slip |
| 400 | Right-lateral slip (m) | Reverse slip (m) | Point source (DC3D0) |
| 500 | Tensile opening (m) | Point inflation (m^3?) | Magmatic source |

Sign conventions:
- Right-lateral slip: **positive**
- Left-lateral slip: **negative**
- Reverse slip (thrust): **positive**
- Normal slip: **negative**
- Tensile opening: **positive**
- Dip: always **positive** (0-90 degrees)

**Critical implementation note**: Coulomb internally flips the sign of right-lateral slip before passing to Okada's DC3D. The Okada convention is left-lateral positive (DISL1 > 0 = left-lateral). The code applies `DISL1 = -element_col5` for KODE 100.

#### 4.1.6 Source vs. Receiver Distinction

- Source faults: elements 1 through `#fixed` (have non-zero slip values)
- Receiver faults: elements `#fixed+1` through end (have zero slip values, define geometry for CFS calculation)
- In the `.inp` file, there is typically a blank line and a repeated column header between source and receiver sections, but parsing should not depend on this.

#### 4.1.7 Grid Parameters Block

```
Grid Parameters
  1  ---  Start-x =    XXX.XXX
  2  ---  Start-y =    YYY.YYY
  3  ---  Finish-x =   XXX.XXX
  4  ---  Finish-y =   YYY.YYY
  5  ---  x-increment = XX.XXX
  6  ---  y-increment = YY.YYY
```

| Parameter | Units | Description |
|-----------|-------|-------------|
| Start-x | km | Western boundary of computation grid |
| Start-y | km | Southern boundary |
| Finish-x | km | Eastern boundary |
| Finish-y | km | Northern boundary |
| x-increment | km | Grid spacing in X (East) direction |
| y-increment | km | Grid spacing in Y (North) direction |

Grid points: N_x = floor((finish_x - start_x) / x_inc) + 1, similarly for N_y.

#### 4.1.8 Optional Sections

Some `.inp` files include additional sections after the grid parameters:

**Cross-section parameters**:
```
Cross Section
  1  ---  Start-x =    XXX.XXX
  2  ---  Start-y =    YYY.YYY
  3  ---  Finish-x =   XXX.XXX
  4  ---  Finish-y =   YYY.YYY
  5  ---  Depth-min =  ZZZ.ZZZ
  6  ---  Depth-max =  ZZZ.ZZZ
  7  ---  z-increment = ZZ.ZZZ
```

**Map display parameters**:
```
Map info
  1  ---  Lon-min =    LLL.LLL
  2  ---  Lon-max =    LLL.LLL
  3  ---  Lat-min =    LL.LLL
  4  ---  Lat-max =    LL.LLL
  5  ---  Ref-Lon =    LLL.LLL
  6  ---  Ref-Lat =    LL.LLL
```

### 4.2 Output File Formats

#### 4.2.1 `dcff.cou` -- Coulomb Stress Grid

Primary output file containing CFS and all stress components on the computation grid.

```
Header line 1: Title / parameters summary
Header line 2: Column labels
Data lines: One per grid point

Columns:
  1: X (km)           - East coordinate
  2: Y (km)           - North coordinate
  3: CFS (bar)        - Coulomb failure stress change
  4: Shear (bar)      - Shear stress change (in rake direction)
  5: Normal (bar)     - Normal stress change (positive = unclamping)
  6: Sxx (bar)        - Stress tensor component
  7: Syy (bar)
  8: Szz (bar)
  9: Syz (bar)
  10: Sxz (bar)
  11: Sxy (bar)
```

#### 4.2.2 `dcff_section.cou` -- Cross-Section Stress Data

Same column format as `dcff.cou` but with:
- Column 1: distance along profile (km)
- Column 2: depth (km, positive downward)

#### 4.2.3 `coulomb_out.dat` -- Primary Grid Output

Tab/space-delimited grid matrix:
```
Header: Parameter names and values
Data: NX columns x NY rows of the selected stress/displacement field
```

#### 4.2.4 `gmt_fault_surface.dat` -- GMT Fault Traces

```
> Source fault N
lon1 lat1
lon2 lat2
lon3 lat3
lon4 lat4
lon1 lat1
> Receiver fault M
...
```

GMT multi-segment format with `>` separators. Each fault is a closed polygon (4 corners + repeat first).

#### 4.2.5 `GPS_output.csv` -- GPS Comparison

```
Station, Lon, Lat, Obs_E(m), Obs_N(m), Obs_U(m), Mod_E(m), Mod_N(m), Mod_U(m), Res_E(m), Res_N(m), Res_U(m)
```

#### 4.2.6 `Focal_mech_stress_output.csv` -- Stress at Focal Mechanisms

```
Header with 2 skip lines
Col 2: X-center (km)
Col 3: Y-center (km)
Col 4: Z-center (km)
Col 6: Strike (deg)
Col 7: Dip (deg)
Col 20: Coulomb stress (bar)
```

### 4.3 New Output Formats (Tier 3)

#### 4.3.1 GeoJSON

Fault geometries as GeoJSON FeatureCollection:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lon1,lat1], [lon2,lat2], [lon3,lat3], [lon4,lat4], [lon1,lat1]]]
      },
      "properties": {
        "type": "source",
        "strike": 45.0,
        "dip": 90.0,
        "rake": 0.0,
        "slip_rl": 1.0,
        "slip_reverse": 0.0,
        "top_depth_km": 0.0,
        "bottom_depth_km": 15.0,
        "cfs_bar": null
      }
    }
  ]
}
```

#### 4.3.2 NetCDF (CF-Compliant)

```
dimensions:
  x = NX
  y = NY
  z = NZ (for 3D grids)

variables:
  float x(x)        ; units="km" ; long_name="East distance"
  float y(y)        ; units="km" ; long_name="North distance"
  float cfs(y, x)   ; units="bar" ; long_name="Coulomb failure stress change"
  float shear(y, x) ; units="bar" ; long_name="Shear stress change"
  float normal(y, x); units="bar" ; long_name="Normal stress change"
  float ux(y, x)    ; units="m"  ; long_name="East displacement"
  float uy(y, x)    ; units="m"  ; long_name="North displacement"
  float uz(y, x)    ; units="m"  ; long_name="Up displacement"

global attributes:
  :title = "OpenCoulomb computation output"
  :Conventions = "CF-1.8"
  :source = "OpenCoulomb vX.Y.Z"
  :friction = 0.4
  :poisson = 0.25
  :youngs_modulus_bar = 800000.0
  :depth_km = 10.0
```

---

## 5. User Interface Specification

### 5.1 CLI Interface

The CLI uses a command-group pattern (similar to `git`, `docker`).

#### 5.1.1 Top-Level Commands

```
opencoulomb [OPTIONS] COMMAND [ARGS]

Commands:
  compute     Run stress/displacement computation from .inp file
  plot        Generate visualizations from computation results
  info        Inspect and summarize a .inp file
  convert     Convert between file formats
  validate    Check .inp file for errors without computing
  batch       Process multiple files or parameter sweeps (Tier 3)
  gui         Launch interactive GUI (Tier 2)
  version     Print version information

Global Options:
  --verbose, -v     Increase output verbosity (repeat for more: -vv)
  --quiet, -q       Suppress non-error output
  --version         Print version and exit
  --help            Print help and exit
  --config FILE     Path to configuration file (TOML)
  --output-dir DIR  Directory for output files (default: ./opencoulomb_output/)
```

#### 5.1.2 `compute` Command

```
opencoulomb compute [OPTIONS] INPUT_FILE

Arguments:
  INPUT_FILE              Coulomb .inp file to process

Computation Options:
  --output, -o TYPE       Output type: cfs, displacement, strain, stress, all
                          (default: cfs)
  --receiver TYPE         Receiver mode: specified, oops (default: specified)
  --depth FLOAT           Override calculation depth (km)
  --friction FLOAT        Override friction coefficient
  --poisson FLOAT         Override Poisson's ratio
  --young FLOAT           Override Young's modulus (bar)

Grid Options:
  --grid-start X Y        Override grid start coordinates (km)
  --grid-end X Y          Override grid end coordinates (km)
  --grid-spacing DX DY    Override grid spacing (km)
  --grid-depth FLOAT      Grid calculation depth (km)

Output Options:
  --format FMT            Output format: coulomb, csv, text, geojson, netcdf
                          (default: coulomb)
  --plot TYPE             Auto-generate plot: map, section, displacement, all, none
                          (default: none)
  --no-header             Omit header lines in output files

Cross-Section Options:
  --section X1 Y1 X2 Y2   Define cross-section profile endpoints (km)
  --section-depth MIN MAX  Depth range for cross-section (km)
  --section-spacing DZ     Vertical spacing in cross-section (km)

Examples:
  # Basic CFS computation
  opencoulomb compute landers.inp

  # Override friction and compute displacement
  opencoulomb compute --friction 0.6 --output displacement landers.inp

  # CFS on optimally oriented planes with auto-plot
  opencoulomb compute --receiver oops --plot map landers.inp

  # Custom grid and cross-section
  opencoulomb compute --grid-start -50 -50 --grid-end 50 50 \
                      --grid-spacing 1.0 1.0 \
                      --section -30 0 30 0 --section-depth 0 20 \
                      landers.inp
```

#### 5.1.3 `plot` Command

```
opencoulomb plot [OPTIONS] RESULT_FILE

Arguments:
  RESULT_FILE             Output file from 'compute' (dcff.cou, etc.)

Plot Options:
  --type TYPE             Plot type: map, section, displacement, 3d
  --field FIELD           Field to plot: cfs, shear, normal, sxx, syy, dilatation,
                          ux, uy, uz, umag
  --clim MIN MAX          Color scale limits (bar or m)
  --cmap NAME             Colormap name (default: vik)
  --symmetric             Force symmetric color scale around zero
  --faults FILE           Overlay fault traces from .inp file
  --earthquakes FILE      Overlay earthquake catalog
  --gps FILE              Overlay GPS vectors

Figure Options:
  --figsize W H           Figure size in inches (default: 10 8)
  --dpi INT               Resolution for raster export (default: 300)
  --format FMT            Export format: png, pdf, svg, eps (default: png)
  --title TEXT            Figure title
  --no-colorbar           Omit color bar
  --output FILE           Output file path (default: auto-named)

Examples:
  # Map of CFS
  opencoulomb plot --type map --field cfs dcff.cou

  # Cross-section with custom color scale
  opencoulomb plot --type section --clim -1 1 dcff_section.cou

  # Publication PDF with faults and earthquakes
  opencoulomb plot --type map --faults landers.inp \
                   --earthquakes socal_catalog.csv \
                   --format pdf --dpi 600 dcff.cou
```

#### 5.1.4 `info` Command

```
opencoulomb info [OPTIONS] INPUT_FILE

Prints a human-readable summary of the .inp file:
  - Title
  - Material properties (Poisson, Young, friction)
  - Number of source faults, total slip, moment
  - Number of receiver faults
  - Grid dimensions and spacing
  - Regional stress field
  - Coordinate system

Options:
  --json                  Output as JSON
  --format FMT            Output format: text, json, yaml
```

#### 5.1.5 `convert` Command

```
opencoulomb convert [OPTIONS] INPUT OUTPUT

Convert between file formats:
  .inp  <->  .json (OpenCoulomb model format)
  .cou  ->   .csv
  .cou  ->   .nc (NetCDF)
  .cou  ->   .geojson (fault geometries only)
  .inp  ->   .kml (Google Earth)

Options:
  --from FMT              Source format (auto-detected if omitted)
  --to FMT                Target format (inferred from output extension if omitted)
```

#### 5.1.6 `validate` Command

```
opencoulomb validate INPUT_FILE

Checks .inp file for:
  - Syntax errors (malformed lines, missing parameters)
  - Physical validity (negative dip, inverted depth range, unreasonable values)
  - Consistency (source count matches #fixed)
  - Warnings (extremely large/small values, potential unit errors)

Exit codes:
  0 = valid
  1 = errors found
  2 = warnings only
```

### 5.2 GUI Specification (Tier 2)

#### 5.2.1 Main Window Layout

```
+---------------------------------------------------------------------+
|  File   Edit   Model   Compute   View   Plugins   Help              |
+---------------------------------------------------------------------+
|                          |                                           |
|    Fault List Panel      |         Map / Visualization Panel         |
|    (tree view)           |         (Matplotlib canvas)               |
|                          |                                           |
|    [+] Source Faults     |         +---------------------------+     |
|      - Fault 1           |         |                           |     |
|      - Fault 2           |         |    Color-filled contour   |     |
|    [+] Receiver Faults   |         |    map with fault traces  |     |
|      - Receiver 1        |         |    and annotations        |     |
|                          |         |                           |     |
|    Properties Panel      |         +---------------------------+     |
|    (selected element)    |                                           |
|    Strike: ___           |         [CFS] [Shear] [Normal] [Disp]    |
|    Dip:    ___           |         [Strain] [Dilatation] [OOP]      |
|    Rake:   ___           |                                           |
|    Slip:   ___           +---------+---------+---------+             |
|    Top:    ___           | Friction| Depth   | Grid    |             |
|    Bottom: ___           |  [0.4]  | [10.0]  | [100x]  |             |
+--------------------------+---------+---------+---------+-------------+
|  Status: Ready  |  Grid: 100x100  |  Depth: 10.0 km  |  N faults: 5|
+---------------------------------------------------------------------+
```

#### 5.2.2 Key GUI Workflows

**Workflow 1: Open existing model and compute CFS**
1. File > Open > select `.inp` file
2. Fault list populates; map shows fault traces on blank grid
3. Adjust friction/depth if needed via Properties panel
4. Compute > Coulomb Stress (or press F5)
5. Progress bar shows computation status
6. Map updates with color-filled CFS contour
7. Click grid point to see stress values at cursor
8. File > Export Figure > PDF

**Workflow 2: Build model from scratch**
1. File > New Model
2. Set material properties (Poisson, Young, friction) in Properties panel
3. Set grid extent by dragging corners on map or entering coordinates
4. Model > Add Source Fault > click two points on map (start/end trace) > enter dip, depth, slip in dialog
5. Repeat for additional source faults
6. Model > Add Receiver Fault(s) > specify or use OOPs
7. Compute > Coulomb Stress
8. File > Save As > `.inp` (exports Coulomb-compatible file)

**Workflow 3: Cross-section analysis**
1. Open or build model and compute
2. View > Cross Section
3. Click two points on map to define profile line
4. Cross-section panel appears below map showing vertical stress slice
5. Adjust depth range and resolution
6. Export cross-section figure

**Workflow 4: Earthquake overlay**
1. Open model and compute CFS
2. File > Import Catalog > select CMT/ISC/USGS file
3. Earthquakes appear as circles on map
4. Filter by magnitude, depth, time using catalog controls
5. Visually correlate aftershock locations with stress lobes

### 5.3 Workflow: From `.inp` to Publication Figure

This section describes the complete end-to-end workflow for the most common use case.

**Step 1: Prepare input**
```bash
# Inspect the input file
opencoulomb info landers.inp
```
Output:
```
Title: 1992 Landers earthquake Coulomb stress change
Material: Poisson=0.25, Young=8.0e5 bar, Friction=0.4
Source faults: 5 (total moment: 1.1e19 N*m, Mw 6.9)
Receiver faults: 2 (strike=330, dip=90)
Grid: -100 to 100 km (E), -100 to 100 km (N), spacing=2 km
Depth: 10.0 km
Regional stress: S1=100 bar @ N24E, S3=30 bar @ N114E (strike-slip regime)
```

**Step 2: Compute**
```bash
opencoulomb compute --output all --plot map landers.inp
```

**Step 3: Review and refine**
```bash
# Adjust color scale
opencoulomb plot --type map --field cfs --clim -2 2 --cmap vik \
                 --faults landers.inp \
                 --format pdf --output landers_cfs.pdf \
                 opencoulomb_output/dcff.cou
```

**Step 4: Add cross-section**
```bash
opencoulomb compute --section -40 0 40 0 --section-depth 0 25 \
                    --section-spacing 0.5 landers.inp

opencoulomb plot --type section --field cfs --clim -2 2 \
                 --format pdf --output landers_section.pdf \
                 opencoulomb_output/dcff_section.cou
```

**Step 5: Compare with seismicity (Tier 2)**
```bash
opencoulomb plot --type map --field cfs --clim -2 2 \
                 --faults landers.inp \
                 --earthquakes aftershocks_1992_1997.csv \
                 --format pdf --dpi 600 \
                 --title "Landers 1992 CFS with aftershocks" \
                 opencoulomb_output/dcff.cou
```

---

## 6. Non-Functional Requirements

### 6.1 Numerical Accuracy

| ID | Requirement | Validation Method |
|----|-------------|------------------|
| NF-ACC-01 | DC3D displacement output matches Okada reference implementation to relative error < 1e-10 | Compare against original Fortran DC3D on standardized test points |
| NF-ACC-02 | Stress tensor matches Coulomb 3.4 to absolute difference < 1e-6 bar | Run all example `.inp` files through both and compare grid output |
| NF-ACC-03 | CFS matches Coulomb 3.4 to absolute difference < 1e-6 bar | Same as above, specifically for dcff.cou |
| NF-ACC-04 | Displacement matches Coulomb 3.4 to absolute difference < 1e-9 m | Compare displacement output grids |
| NF-ACC-05 | OOP orientation matches Coulomb 3.4 to < 0.01 degrees | Compare OOP strike/dip at all grid points |
| NF-ACC-06 | No silent precision loss: all internal computation in float64 (double precision) | Code review + static analysis |

Numerical precision notes:
- All internal computation uses IEEE 754 double precision (64-bit float).
- Coordinate transforms use the same formulation as Coulomb 3.4 to avoid introducing differences.
- The Okada DC3D function involves subtraction of nearly equal numbers near singularities; the implementation must handle these carefully (matching Okada's original approach).
- Unit conversion factor (0.001 for km-to-m) must be applied at exactly the same point in the pipeline as Coulomb 3.4.

### 6.2 Performance

| ID | Requirement | Target | Notes |
|----|-------------|--------|-------|
| NF-PRF-01 | 100x100 grid, 10 source faults | < 10 seconds | Baseline benchmark |
| NF-PRF-02 | 200x200 grid, 50 source faults | < 120 seconds | Large model |
| NF-PRF-03 | 500x500 grid, 100 source faults | < 30 minutes | Extreme (batch mode) |
| NF-PRF-04 | `.inp` file parsing | < 100 ms for any file | I/O should not be a bottleneck |
| NF-PRF-05 | Static plot generation | < 5 seconds | After computation |
| NF-PRF-06 | GUI responsiveness | < 200 ms for parameter changes | No computation; just UI update |
| NF-PRF-07 | Memory: 100x100 grid | < 500 MB | Including all intermediate arrays |

Benchmark platform: Intel Core i5 (4 cores, 3.0 GHz), 16 GB RAM, SSD. These targets should be achievable with NumPy vectorization. If not, the Fortran wrapper path (Section 3.3) provides a clear escalation.

### 6.3 Cross-Platform Compatibility

| ID | Requirement | Supported Versions |
|----|-------------|-------------------|
| NF-PLT-01 | Linux | Ubuntu 22.04+, Fedora 38+, Debian 12+ |
| NF-PLT-02 | macOS | macOS 13 (Ventura)+ on Intel and Apple Silicon (arm64) |
| NF-PLT-03 | Windows | Windows 10 (21H2)+, Windows 11 |
| NF-PLT-04 | Python version | 3.10, 3.11, 3.12, 3.13 |
| NF-PLT-05 | Architecture | x86_64, arm64 (Apple Silicon and Linux aarch64) |

CI testing: GitHub Actions matrix for all three OS families and Python 3.10 through 3.13.

### 6.4 Installation

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| NF-INS-01 | `pip install opencoulomb` on clean Python 3.10+ environment | Installs and runs `opencoulomb --version` in < 60 seconds |
| NF-INS-02 | No C compiler required for Tier 1 | Pure Python + pre-built NumPy/SciPy wheels |
| NF-INS-03 | `conda install -c conda-forge opencoulomb` | Works in fresh conda environment |
| NF-INS-04 | Offline installation from wheel file | `pip install opencoulomb-X.Y.Z-py3-none-any.whl` |
| NF-INS-05 | No root/admin privileges required | Standard user pip install (--user or venv) |
| NF-INS-06 | GUI install: `pip install opencoulomb[gui]` | Installs PyQt6/PySide6 + starts `opencoulomb gui` |

### 6.5 Documentation

| ID | Requirement | Format |
|----|-------------|--------|
| NF-DOC-01 | Installation guide (all platforms) | Docs website (Sphinx/MkDocs) |
| NF-DOC-02 | Quick start tutorial (5-minute first run) | Docs website |
| NF-DOC-03 | Migration guide from Coulomb 3.4 | Docs website |
| NF-DOC-04 | CLI reference (all commands, all flags) | Auto-generated from Click + docs |
| NF-DOC-05 | Python API reference (all public functions) | Auto-generated from docstrings (Sphinx autodoc) |
| NF-DOC-06 | File format specification (.inp, .cou, etc.) | Docs website (this document, refined) |
| NF-DOC-07 | Theory guide (Okada, CFS, OOPs, coordinates) | Docs website |
| NF-DOC-08 | Example gallery (10+ worked examples with plots) | Jupyter notebooks in `examples/` |
| NF-DOC-09 | Contributing guide | `CONTRIBUTING.md` |
| NF-DOC-10 | Changelog | `CHANGELOG.md` (Keep a Changelog format) |

Documentation framework: **MkDocs** with **mkdocs-material** theme and **mkdocstrings** for API docs. Rationale: Markdown-native (easier for contributors than RST), excellent search, good code block rendering, widely adopted in the Python scientific community.

### 6.6 Testing Requirements

| ID | Requirement | Coverage Target |
|----|-------------|-----------------|
| NF-TST-01 | Unit tests for all core computation functions | >= 95% line coverage |
| NF-TST-02 | Unit tests for I/O (parser, writer) | >= 90% line coverage |
| NF-TST-03 | Integration tests: full `.inp` -> output pipeline | All example files |
| NF-TST-04 | Validation tests: numerical comparison against Coulomb 3.4 reference outputs | All example files with known-good outputs |
| NF-TST-05 | Cross-validation against elastic_stresses_py | At least 5 test cases |
| NF-TST-06 | Edge case tests (surface faults, zero slip, point sources, extreme dips) | Documented edge case matrix |
| NF-TST-07 | Performance regression tests | Fail if > 2x slower than baseline |
| NF-TST-08 | CLI tests (all commands and flags) | >= 85% line coverage |
| NF-TST-09 | GUI tests (smoke tests for all dialogs) | All dialogs open and close without error |
| NF-TST-10 | CI runs on every PR and push to main | GitHub Actions |

### 6.7 Code Quality

| ID | Requirement | Tool |
|----|-------------|------|
| NF-CQ-01 | Type hints on all public functions | mypy strict mode |
| NF-CQ-02 | Docstrings on all public functions (NumPy format) | pydocstyle |
| NF-CQ-03 | Linting | Ruff (replaces flake8 + isort + pyupgrade) |
| NF-CQ-04 | Formatting | Ruff format (Black-compatible) |
| NF-CQ-05 | No `# type: ignore` without comment explaining why | mypy + code review |
| NF-CQ-06 | Maximum function length: 100 lines | Ruff rule |
| NF-CQ-07 | Maximum cyclomatic complexity: 15 | Ruff rule |

### 6.8 Security

| ID | Requirement | Notes |
|----|-------------|-------|
| NF-SEC-01 | No network access from core library | Computation is entirely local |
| NF-SEC-02 | Input validation on all `.inp` file parsing | Prevent crashes from malformed files |
| NF-SEC-03 | No pickle/eval of user-supplied data | Avoid arbitrary code execution |
| NF-SEC-04 | Dependencies pinned with hashes in lock file | Reproducible, tamper-resistant builds |
| NF-SEC-05 | SBOM (Software Bill of Materials) generated on release | SPDX or CycloneDX format |

---

## 7. Compatibility Matrix

### 7.1 Coulomb 3.4 `.inp` File Features

| Feature | Supported in MVP (Tier 1) | Supported in Tier 2 | Notes |
|---------|---------------------------|---------------------|-------|
| Standard header (PR, E, DEPTH, FRIC) | Yes | Yes | |
| Regional stress (S1/S2/S3) | Yes | Yes | |
| KODE 100 (standard fault) | Yes | Yes | |
| KODE 200 (tensile + RL) | Partial (parsed; computed if straightforward) | Yes | |
| KODE 300 (tensile + reverse) | Partial | Yes | |
| KODE 400 (point source) | Yes (DC3D0) | Yes | |
| KODE 500 (tensile + inflation) | Partial | Yes | |
| Grid parameters | Yes | Yes | |
| Cross-section parameters | Yes | Yes | |
| Map info (lon/lat reference) | Parsed, stored | Yes (used for geographic display) | |
| Source_Patch variant format | No | Yes | |
| Source_WC variant format | No | Yes | |
| Source_FM variant format | No | Yes | |
| Receiver_Horizontal_Profile | No | Yes | |
| Fault labels | Parsed, stored | Displayed in GUI | |
| #fixed boundary | Yes | Yes | |
| Symmetry (sym parameter) | Parsed; computation TBD | Yes | Rare feature |
| Two-region materials (PR1!=PR2) | Parsed; single-region computation | Yes (if semantics clarified) | Underdocumented in Coulomb |

### 7.2 Output Format Compatibility

| Output File | Tier 1 | Tier 2 | Byte-Identical to C3.4 |
|-------------|--------|--------|----------------------|
| `dcff.cou` | Yes | Yes | Format-identical (same column layout, minor float formatting differences acceptable) |
| `dcff_section.cou` | Yes | Yes | Same |
| `coulomb_out.dat` | Yes | Yes | Same |
| `gmt_fault_surface.dat` | Yes | Yes | Same |
| `gmt_fault_map_proj.dat` | No | Yes | Same |
| `gmt_fault_calc_dep.dat` | No | Yes | Same |
| `Cross_section.dat` | No | Yes | Same |
| `Strain.cou` | No | Yes | Same |
| `dilatation_section.cou` | No | Yes | Same |
| `GPS_output.csv` | No | Yes | Same |
| `Focal_mech_stress_output.csv` | No | Yes | Same |
| MATLAB `.fig` | No | No | Not applicable (proprietary format) |
| MATLAB `.mat` | No | No | Not applicable |

### 7.3 Coulomb 4.0 Compatibility Plan

Coulomb 4.0 is a MATLAB App Designer rewrite (`.mlapp` file) with significant new features. Compatibility strategy:

| C4.0 Feature | OpenCoulomb Plan | Timeline |
|--------------|-----------------|----------|
| `.inp` file format (if unchanged) | Supported natively | Tier 1 |
| ISC catalog integration | Direct ISC API integration | Tier 2 |
| USGS finite fault import | SRCMOD/USGS format parsers | Tier 2 |
| Depth-loop engine (multi-depth) | Native: loop/vectorize over depths | Tier 2-3 |
| Unified workspace GUI | Single-window design (already planned) | Tier 2 |
| NOAA GSHHG coastlines | Via Cartopy (built-in coastline data) | Tier 2 |
| Mapping Toolbox features | Via Cartopy + pyproj | Tier 2 |
| Image Processing features | Via Pillow/scikit-image if needed | Tier 3 |
| Curve Fitting features | Via SciPy.interpolate / SciPy.optimize | Tier 2-3 |

Note: Coulomb 4.0 is in beta (released 2026-02-08). Its `.inp` format and output formats should be monitored for changes. If the 4.0 `.inp` format diverges, a separate parser variant will be needed.

---

## 8. Validation Strategy

### 8.1 Reference Data Sources

| Source | What It Provides | How to Obtain |
|--------|-----------------|---------------|
| Coulomb 3.4 example `.inp` files | ~20 input files covering diverse fault geometries | From coulomb3402.zip (`input_file/` directory) |
| Coulomb 3.4 computed outputs | Reference `.cou`, `.dat`, `.csv` files for each example | Run each example through Coulomb 3.4 in MATLAB and save all outputs |
| Okada (1992) Table 2 | Published reference values for DC3D | From the original paper |
| NIED DC3D Fortran output | Reference DC3D output for arbitrary test points | Compile and run the Fortran code |
| elastic_stresses_py output | Independent Python implementation results | Run elastic_stresses_py on shared test cases |
| King, Stein & Lin (1994) | Published CFS maps for 1992 Landers earthquake | From the paper (digitized) |
| Toda et al. (2011) User Guide | Published example figures and values | From USGS OFR 2011-1060 |

### 8.2 Validation Test Suite

#### 8.2.1 Level 1: Okada DC3D Unit Validation

Test the raw DC3D implementation against known-good reference values.

| Test Case | Input | Expected Output Source |
|-----------|-------|----------------------|
| Single strike-slip fault, surface observation | Standard geometry from Okada (1992) Table 2 | Published values |
| Single dip-slip fault, surface observation | Standard geometry | Published values |
| Single tensile fault, surface observation | Standard geometry | Published values |
| Internal (depth) observation points | Various depths | NIED Fortran output |
| Point source (DC3D0) | Standard point source | NIED Fortran output |
| Fault at surface (top=0) | Edge case | Fortran output |
| Observation on fault plane | Singularity edge case | Fortran output (should return IRET != 0) |
| Very deep fault (100 km) | Deep source | Fortran output |
| Very thin fault (width = 0.01 km) | Near-degenerate | Fortran output |
| Pure tensile opening | No shear, only DISL3 | Fortran output |
| Combined slip (all 3 components) | DISL1 + DISL2 + DISL3 | Fortran output |

Tolerance: Relative error < 1e-10 for all displacement and gradient components.

#### 8.2.2 Level 2: Stress and CFS Validation

Test the full pipeline from fault definition through CFS.

| Test Case | Input | Validation Against |
|-----------|-------|--------------------|
| Single vertical strike-slip fault | Simple .inp | Coulomb 3.4 dcff.cou |
| Single dipping reverse fault | Simple .inp | Coulomb 3.4 dcff.cou |
| Multiple source faults (superposition) | Multi-fault .inp | Coulomb 3.4 dcff.cou |
| Specified receiver faults | With receivers | Coulomb 3.4 per-element output |
| Optimally oriented planes | With regional stress | Coulomb 3.4 OOP output |
| Cross-section computation | Profile defined | Coulomb 3.4 dcff_section.cou |
| Displacement field | Surface displacement grid | Coulomb 3.4 displacement output |

Tolerance: Absolute CFS difference < 1e-6 bar at all grid points.

#### 8.2.3 Level 3: Full Example File Validation

Run every `.inp` file from Coulomb 3.4's `input_file/` directory and compare all outputs.

Known example files (representative set):
```
input_file/
    1992_landers/landers.inp
    1994_northridge/northridge.inp
    1999_hector_mine/hector_mine.inp
    normal_fault_example/normal.inp
    thrust_fault_example/thrust.inp
    point_source_example/point.inp
    tensile_example/tensile.inp
    multi_fault_example/multi.inp
    oops_example/oops.inp
    gps_comparison/gps_example.inp
    ... (all available examples)
```

For each file, compare:
1. `dcff.cou` grid values (CFS, shear, normal, all stress components)
2. `dcff_section.cou` (if cross-section defined)
3. Displacement output
4. Per-element stress on receiver faults

#### 8.2.4 Level 4: Cross-Validation with elastic_stresses_py

Run shared test cases through both OpenCoulomb and elastic_stresses_py.

| Test Case | Purpose |
|-----------|---------|
| Simple strike-slip | Verify basic agreement |
| Multi-segment rupture | Verify superposition |
| Dipping fault with rake | Verify 3D stress resolution |
| Different friction values | Verify CFS parameterization |
| Different depths | Verify depth-dependence |

Tolerance: Absolute CFS difference < 1e-4 bar (allowing for minor implementation differences).

#### 8.2.5 Level 5: Published Result Reproduction

Reproduce specific published figures/values from landmark papers.

| Paper | Figure/Table | What to Reproduce |
|-------|-------------|-------------------|
| King, Stein & Lin (1994) Fig 2 | CFS map for Landers 1992 | Spatial pattern and magnitude of stress lobes |
| Toda et al. (2011) User Guide Figs 14-20 | Various example outputs | All example figures from the user guide |
| Stein (1999) Nature review | Conceptual CFS patterns | Qualitative agreement for canonical geometries |

#### 8.2.6 Level 6: Edge Cases and Regression

| Test Case | Why It Matters |
|-----------|---------------|
| Zero slip on all sources | Should produce zero stress everywhere |
| Slip on only one component (pure RL, pure reverse, pure tensile) | Isolate each mechanism |
| Fault at surface (top_depth = 0) | Free surface singularity handling |
| Very long fault (1000 km) | Numerical stability at large distances |
| Very small fault (0.1 km) | Near-point-source behavior |
| Observation at fault center | Singularity or maximum stress |
| Observation at great distance (1000x fault length) | Should approach zero |
| Poisson's ratio = 0.0, 0.49 | Extreme material parameters |
| Friction = 0.0, 1.0 | Extreme CFS parameterization |
| 90-degree dip (vertical fault) | Special case in coordinate transforms |
| 0-degree dip (horizontal fault) | Degenerate case |
| North-south strike (azimuth = 0 or 180) | Coordinate transform edge case |
| East-west strike (azimuth = 90 or 270) | Coordinate transform edge case |
| Grid point exactly on fault trace | Singularity handling |
| Single grid point (1x1 grid) | Minimal grid |
| Very fine grid (1000x1000) | Memory and performance |

### 8.3 Continuous Validation

- Reference outputs are committed to the test data repository (or stored as fixtures).
- Every CI run executes the full validation suite.
- Any numerical change triggers a diff report showing where and by how much values changed.
- Performance benchmarks run on every tagged release.

### 8.4 Validation Reporting

Each release includes a validation report:
```
OpenCoulomb vX.Y.Z Validation Report
=====================================
Date: YYYY-MM-DD
Platform: Linux x86_64, Python 3.12.x, NumPy 1.26.x

Level 1 - Okada DC3D:      PASS (11/11 tests, max rel error: 2.3e-15)
Level 2 - Stress/CFS:      PASS (7/7 tests, max abs CFS diff: 4.1e-10 bar)
Level 3 - Example files:   PASS (20/20 files, all within tolerance)
Level 4 - Cross-validation: PASS (5/5 tests, max diff: 1.2e-5 bar)
Level 5 - Published:       PASS (3/3 reproductions match qualitatively)
Level 6 - Edge cases:      PASS (18/18 tests)

Performance:
  100x100 x 10 faults:    3.2s (target: <10s)
  200x200 x 50 faults:   47.8s (target: <120s)
```

---

## 9. Project Phasing and Milestones

### 9.1 Phase Overview

| Phase | Scope | Duration Estimate | Deliverable |
|-------|-------|-------------------|-------------|
| **Phase 1** | Research | Complete | Research reports (docs/claude/research/) |
| **Phase 2** | Specification | Complete | This document |
| **Phase 3** | Architecture | 1-2 weeks | Architecture document, module design, ADRs |
| **Phase 4** | Tier 1 MVP | 6-8 weeks | Working CLI with core computation |
| **Phase 5** | Tier 2 GUI + Parity | 8-12 weeks | Full Coulomb 3.4 parity |
| **Phase 6** | Tier 3 Extensions | Ongoing | API, web GUI, extensions |

### 9.2 Tier 1 MVP Milestone Breakdown

| Milestone | Deliverables | Dependencies |
|-----------|-------------|--------------|
| **M1: Project scaffold** | Repository structure, CI, linting, docs skeleton, pyproject.toml | None |
| **M2: Okada DC3D engine** | `okada.py` with DC3D and DC3D0, validated against Fortran reference | M1 |
| **M3: Stress computation** | Hooke's law, tensor rotation, coordinate transforms, validated | M2 |
| **M4: `.inp` parser** | Full `.inp` parsing with all header fields, fault elements, grid parameters | M1 |
| **M5: CFS calculation** | CFS on specified receivers and on grid, validated against Coulomb 3.4 | M2, M3, M4 |
| **M6: OOPs** | Optimally oriented plane computation, validated | M5 |
| **M7: Cross-section** | Vertical profile computation | M5 |
| **M8: Visualization** | Static map, cross-section, displacement plots via Matplotlib | M5, M7 |
| **M9: CLI** | All Tier 1 CLI commands operational | M5, M7, M8 |
| **M10: Output files** | All Tier 1 output formats (.cou, .dat, .csv) | M5, M7 |
| **M11: Validation** | Full validation suite passing against Coulomb 3.4 reference | M5-M10 |
| **M12: Packaging** | `pip install opencoulomb` works on all platforms | M9, M10, M11 |
| **M13: Documentation** | Installation guide, quick start, CLI reference, theory guide | M12 |

### 9.3 Release Strategy

| Version | Scope | Quality Gate |
|---------|-------|-------------|
| 0.1.0-alpha | M1-M5: Core computation works | Okada validated, CFS on grid matches Coulomb 3.4 |
| 0.2.0-alpha | M6-M8: OOPs, cross-section, visualization | All Tier 1 computation validated |
| 0.5.0-beta | M9-M11: CLI complete, validation passing | Full Tier 1, all example files validated |
| 1.0.0 | Tier 1 complete: CLI, docs, packaging | All validation levels passing, docs complete |
| 1.x.x | Tier 2 features incrementally | Each release adds features with maintained validation |
| 2.0.0 | Full Coulomb 3.4 parity including GUI | All Tier 2 requirements met |

Versioning: Semantic Versioning (SemVer). Pre-1.0 releases may break API. Post-1.0, the public API (Python and CLI) is stable.

---

## 10. Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R1 | Okada DC3D numerical inaccuracy in pure Python | Medium | High | Validate exhaustively against Fortran reference; fallback to Fortran wrapper via ctypes |
| R2 | Performance too slow for large grids | Medium | Medium | NumPy vectorization first; Fortran/C inner loop if needed; profiling gates defined |
| R3 | `.inp` format undocumented edge cases | High | Medium | Test against all available example files; inspect Coulomb 3.4 parser source; community feedback |
| R4 | Coulomb 3.4 reference outputs not available (no MATLAB license) | Medium | High | Obtain reference outputs once via academic MATLAB license or collaborator; commit as test fixtures |
| R5 | GUI development takes longer than estimated | High | Medium | GUI is Tier 2, not MVP; CLI-first ensures core utility without GUI; consider simpler Panel/Streamlit prototype first |
| R6 | Scope creep into Coulomb 4.0 features | Medium | Medium | Strict tier discipline; Coulomb 3.4 parity is the 1.0 goal; 4.0 features are explicitly Tier 3 |
| R7 | PyQt6 licensing incompatibility | Low | Medium | Use PySide6 (LGPL) as drop-in replacement; GUI is a separate optional dependency |
| R8 | Coordinate convention errors (sign flips, axis order) | High | High | Extensive unit tests for coordinate transforms; test each convention independently; document conventions prominently |
| R9 | Dependency conflicts with other scientific Python packages | Medium | Low | Minimal core dependencies; use optional extras for heavy packages; test in clean environments |
| R10 | Existing tool (elastic_stresses_py) adds GUI, reducing our differentiation | Low | Medium | Focus on superior UX, better docs, pip-installable simplicity, and broader feature set |

---

## Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **CFS** | Coulomb Failure Stress change (delta_CFS). Positive = brought closer to failure. |
| **DC3D** | Okada's Fortran subroutine for displacement/strain from a finite rectangular dislocation |
| **DC3D0** | Point source variant of DC3D |
| **KODE** | Integer code defining fault element type (100-500) |
| **OOP** | Optimally Oriented Plane -- fault orientation maximizing CFS |
| **Receiver fault** | Fault on which stress is calculated (passive; has zero slip in model) |
| **Source fault** | Fault that slips and generates stress changes (active; has non-zero slip) |
| **Stress shadow** | Region of negative CFS change (inhibited failure) |
| **Half-space** | Semi-infinite elastic medium with a free surface (the standard Earth model for this problem) |
| **Superposition** | Principle that stresses from multiple sources sum linearly in a linear elastic medium |
| **Tensor rotation** | Transformation of stress/strain tensor from one coordinate system to another |

### Appendix B: Physical Constants and Defaults

| Constant | Symbol | Default Value | SI Equivalent | Notes |
|----------|--------|---------------|---------------|-------|
| Poisson's ratio | nu | 0.25 | -- | Poisson solid |
| Young's modulus | E | 8.0e5 bar | 80 GPa | Typical upper crust |
| Shear modulus | G = E/(2(1+nu)) | 3.2e5 bar | 32 GPa | Derived |
| Bulk modulus | K = E/(3(1-2nu)) | 5.33e5 bar | 53.3 GPa | Derived |
| Lame's first parameter | lambda = nu*E/((1+nu)(1-2nu)) | 3.2e5 bar | 32 GPa | Derived |
| Effective friction | mu' | 0.4 | -- | Includes pore pressure effect |
| Medium constant | alpha = (lambda+G)/(lambda+2G) | 0.6667 | -- | = 1/(2(1-nu)) for nu=0.25 |

### Appendix C: Coordinate Convention Summary

```
Geographic System:
  X = East (positive)
  Y = North (positive)
  Z = Up (positive), but depth is measured as positive downward

Fault Definition:
  Strike = clockwise angle from North (0-360 degrees)
  Dip = angle from horizontal (0-90 degrees, always positive)
  Rake = angle in fault plane from strike direction (-180 to 180)
    Rake = 0:    pure left-lateral
    Rake = 180:  pure right-lateral
    Rake = 90:   pure reverse (thrust)
    Rake = -90:  pure normal

.inp File Convention:
  Column 7 (rt.lat): positive = right-lateral
  Column 8 (reverse): positive = reverse (thrust)

Okada DC3D Convention (internal):
  DISL1: strike-slip (positive = left-lateral -- OPPOSITE of .inp)
  DISL2: dip-slip (positive = reverse)
  DISL3: tensile (positive = opening)

Sign flip: The code applies DISL1 = -inp_col7 when KODE = 100
```

### Appendix D: References

1. Okada, Y. (1992). Internal deformation due to shear and tensile faults in a half-space. *Bulletin of the Seismological Society of America*, 82(2), 1018-1040. https://doi.org/10.1785/BSSA0820021018

2. Okada, Y. (1985). Surface deformation due to shear and tensile faults in a half-space. *Bulletin of the Seismological Society of America*, 75(4), 1135-1154.

3. King, G.C.P., Stein, R.S., and Lin, J. (1994). Static stress changes and the triggering of earthquakes. *Bulletin of the Seismological Society of America*, 84(3), 935-953. https://doi.org/10.1785/BSSA0840030935

4. Toda, S., Stein, R.S., Richards-Dinger, K., and Bozkurt, S.B. (2005). Forecasting the evolution of seismicity in southern California: Animations built on earthquake stress transfer. *Journal of Geophysical Research*, 110, B05S16. https://doi.org/10.1029/2004JB003415

5. Toda, S., Stein, R.S., Sevilgen, V., and Lin, J. (2011). Coulomb 3.3 Graphic-rich deformation and stress-change software for earthquake, tectonic, and volcano research and teaching -- User guide. *USGS Open-File Report 2011-1060*, 63 p. https://pubs.usgs.gov/of/2011/1060/

6. Dieterich, J. (1994). A constitutive law for rate of earthquake production and its application to earthquake clustering. *Journal of Geophysical Research*, 99(B2), 2601-2618.

7. Stein, R.S. (1999). The role of stress transfer in earthquake occurrence. *Nature*, 402, 605-609.

8. Wells, D.L. and Coppersmith, K.J. (1994). New empirical relationships among magnitude, rupture length, rupture width, rupture area, and surface displacement. *Bulletin of the Seismological Society of America*, 84(4), 974-1002.

---

*End of Program Specification*
*Document version 1.0 -- 2026-02-27*
*Phase 2 of the OpenCoulomb project*
