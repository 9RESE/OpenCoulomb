# OpenCoulomb Technical Architecture

**Phase 3 -- Architecture Design**
**Version**: 1.0
**Date**: 2026-02-27
**Status**: Draft
**Derived From**: Phase 2 Program Specification (docs/claude/design/program-specification.md)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Package Structure](#2-package-structure)
3. [Core Computation Architecture](#3-core-computation-architecture)
4. [Data Model](#4-data-model)
5. [I/O Architecture](#5-io-architecture)
6. [Visualization Architecture](#6-visualization-architecture)
7. [CLI Architecture](#7-cli-architecture)
8. [Error Handling Strategy](#8-error-handling-strategy)
9. [Testing Architecture](#9-testing-architecture)
10. [Extension Points](#10-extension-points)
11. [Performance Considerations](#11-performance-considerations)
12. [Dependency Management](#12-dependency-management)

---

## 1. System Overview

### 1.1 C4 Model -- Level 1: System Context

```
+------------------+          +-------------------+          +------------------+
|                  |          |                   |          |                  |
|  Research        |  .inp    |                   |  .cou    |  Visualization   |
|  Seismologist    +--------->+   OpenCoulomb     +--------->+  Tools (GMT,     |
|  / Student       |  files   |                   |  .csv    |  GIS, Inkscape)  |
|                  |          |                   |  .pdf    |                  |
+------------------+          +--------+----------+          +------------------+
                                       |
                                       | Python API
                                       v
                              +--------+----------+
                              |                   |
                              |  Jupyter Notebook  |
                              |  / Python Script   |
                              |  / Pipeline        |
                              |                   |
                              +-------------------+

External Data Sources (Tier 2):
  - USGS ComCat API (earthquake catalogs)
  - ISC/GCMT catalog files
  - GPS displacement files
  - SRCMOD finite fault models

File System:
  - Input: .inp files (Coulomb 3.4 format)
  - Output: .cou, .dat, .csv, .pdf, .svg, .png, .geojson, .nc
  - Config: opencoulomb.toml (optional user config)
```

### 1.2 C4 Model -- Level 2: Container Diagram

```
+-----------------------------------------------------------------------+
|                          OpenCoulomb Package                           |
|                                                                       |
|  +-------------+   +-------------+   +-------------+   +----------+  |
|  |             |   |             |   |             |   |          |  |
|  |  CLI        |   |  GUI        |   |  Python     |   |  Web     |  |
|  |  (Click)    |   |  (PyQt6)    |   |  API        |   |  (Tier3) |  |
|  |  Tier 1     |   |  Tier 2     |   |  Tier 3     |   |          |  |
|  +------+------+   +------+------+   +------+------+   +----+-----+  |
|         |                 |                 |                |        |
|         +---------+-------+---------+-------+--------+-------+       |
|                   |                 |                                 |
|                   v                 v                                 |
|         +---------+------+  +------+---------+                       |
|         |                |  |                |                       |
|         |  Visualization |  |  I/O Layer     |                       |
|         |  (Matplotlib)  |  |  (Parsers,     |                       |
|         |                |  |   Writers)     |                       |
|         +--------+-------+  +-------+--------+                       |
|                  |                  |                                 |
|                  +--------+---------+                                 |
|                           |                                          |
|                           v                                          |
|                  +--------+---------+                                 |
|                  |                  |                                 |
|                  |  Core Engine     |                                 |
|                  |  (Okada DC3D,    |                                 |
|                  |   Stress, CFS,   |                                 |
|                  |   Coordinates)   |                                 |
|                  |                  |                                 |
|                  +--------+---------+                                 |
|                           |                                          |
|                           v                                          |
|                  +--------+---------+                                 |
|                  |                  |                                 |
|                  |  Data Model      |                                 |
|                  |  (Types, Enums,  |                                 |
|                  |   Dataclasses)   |                                 |
|                  |                  |                                 |
|                  +------------------+                                 |
+-----------------------------------------------------------------------+
         |
         v
+------------------+
| NumPy / SciPy    |
| (array compute)  |
+------------------+
```

### 1.3 C4 Model -- Level 3: Component Diagram (Core Engine)

```
+-----------------------------------------------------------------------+
|                          Core Engine                                   |
|                                                                       |
|  +------------------+     +-------------------+     +--------------+  |
|  | coordinates.py   |     | okada.py          |     | stress.py    |  |
|  |                  |     |                   |     |              |  |
|  | geo_to_fault()   |     | dc3d()            |     | hooke()      |  |
|  | fault_to_geo()   +---->+ dc3d0()           +---->+ tensor_rot() |  |
|  | fault_geometry() |     | _ua(), _ub(), _uc()|    | strain()     |  |
|  |                  |     | _dccon0/1/2()     |     |              |  |
|  +--------+---------+     +-------------------+     +------+-------+  |
|           |                                                |          |
|           |            +-------------------+               |          |
|           |            | coulomb.py        |               |          |
|           |            |                   |<--------------+          |
|           +----------->+ resolve_stress()  |                          |
|                        | compute_cfs()     |                          |
|                        | bond_matrix()     |                          |
|                        +--------+----------+                          |
|                                 |                                     |
|                                 v                                     |
|                        +--------+----------+                          |
|                        | oops.py           |                          |
|                        |                   |                          |
|                        | regional_stress() |                          |
|                        | find_oops()       |                          |
|                        | mohr_coulomb()    |                          |
|                        +-------------------+                          |
|                                                                       |
|  +------------------------------------------------------------------+ |
|  | pipeline.py (Orchestrator)                                        | |
|  |                                                                   | |
|  | compute_grid()    -- full grid computation                        | |
|  | compute_section() -- cross-section computation                    | |
|  | compute_elements()-- stress on receiver elements                  | |
|  | compute_point()   -- single point computation                     | |
|  +-------------------------------------------------------------------+ |
+-----------------------------------------------------------------------+
```

### 1.4 High-Level Data Flow

```
  .inp file
      |
      v
  [inp_parser.py] -- parse_inp_file()
      |
      v
  CoulombModel dataclass
  (faults, grid, material, regional_stress)
      |
      v
  [pipeline.py] -- compute_grid()
      |
      +---> For each source fault:
      |        |
      |        +--> [coordinates.py] geo_to_fault()
      |        |       Transform grid points to fault-local coords
      |        |
      |        +--> [okada.py] dc3d() / dc3d0()
      |        |       Compute displacement + 9 gradient components
      |        |       (vectorized over all grid points)
      |        |
      |        +--> [stress.py] hooke()
      |        |       Displacement gradients --> stress tensor
      |        |       (with 0.001 km/m unit factor)
      |        |
      |        +--> [stress.py] tensor_rotate()
      |        |       Fault-local --> geographic coordinates
      |        |
      |        +--> Accumulate (superposition)
      |
      v
  StressResult (6-component tensor + 3 displacements at every grid point)
      |
      +---> [coulomb.py] resolve_stress() / compute_cfs()
      |        Resolve onto receiver planes, compute CFS
      |
      +---> [oops.py] find_oops()  (if OOP mode)
      |        Add regional stress, find optimal planes
      |
      v
  CoulombResult
  (CFS, shear, normal, stress tensor, displacements, OOP orientations)
      |
      +---> [cou_writer.py]  --> dcff.cou, dcff_section.cou
      +---> [csv_writer.py]  --> results.csv
      +---> [dat_writer.py]  --> coulomb_out.dat, gmt_fault_surface.dat
      +---> [maps.py]        --> CFS contour map (PNG/PDF/SVG)
      +---> [sections.py]    --> cross-section plot
      +---> [displacement.py]--> displacement vector plot
```

---

## 2. Package Structure

### 2.1 Directory Layout

```
opencoulomb/                        # Repository root
    pyproject.toml                  # PEP 621 build config
    LICENSE                         # Apache 2.0
    README.md                       # Project overview
    CHANGELOG.md                    # Version history
    CONTRIBUTING.md                 # Contributor guide

    src/
        opencoulomb/
            __init__.py             # Package root: __version__, public API re-exports
            __main__.py             # python -m opencoulomb support
            _constants.py           # Physical constants, default values, unit factors

            core/                   # Computation engine (zero I/O, zero viz)
                __init__.py         # Re-exports: dc3d, compute_cfs, compute_grid, ...
                okada.py            # Okada (1992) DC3D / DC3D0
                stress.py           # Hooke's law, tensor rotation, strain
                coulomb.py          # CFS calculation, Bond matrix, stress resolution
                coordinates.py      # Coordinate transformations
                oops.py             # Optimally oriented planes
                pipeline.py         # Computation orchestrator

            types/                  # Data model (pure dataclasses, no logic)
                __init__.py         # Re-exports all types
                fault.py            # FaultElement, Kode enum
                grid.py             # Grid, GridSpec
                material.py         # MaterialProperties
                stress.py           # RegionalStress, StressTensor
                result.py           # StressResult, CoulombResult, DisplacementResult
                model.py            # CoulombModel (aggregate root)
                section.py          # CrossSectionSpec, CrossSectionResult

            io/                     # File I/O (parsers, writers)
                __init__.py         # Re-exports: read_inp, write_cou, ...
                inp_parser.py       # .inp file reader (state machine)
                inp_writer.py       # .inp file writer (Tier 2)
                cou_writer.py       # .cou output writer
                csv_writer.py       # CSV export
                dat_writer.py       # .dat file writers (coulomb_out, gmt_fault)
                formats.py          # Format registry, auto-detection
                catalog.py          # Earthquake catalog reader (Tier 2)
                gps.py              # GPS data reader (Tier 2)
                geojson.py          # GeoJSON I/O (Tier 3)
                netcdf.py           # NetCDF I/O (Tier 3)

            viz/                    # Visualization (Matplotlib-based)
                __init__.py         # Re-exports: plot_cfs_map, plot_section, ...
                maps.py             # 2D stress/displacement contour maps
                sections.py         # Cross-section plots
                faults.py           # Fault trace rendering
                displacement.py     # Displacement vector (quiver) plots
                colormaps.py        # Colormap configuration, Coulomb defaults
                styles.py           # Matplotlib rcParams, publication presets
                three_d.py          # 3D visualization (Tier 2, PyVista)
                export.py           # Figure export (PDF, SVG, PNG, multi-panel)
                _base.py            # Base plotting utilities, axis helpers

            cli/                    # Command-line interface (Click)
                __init__.py
                main.py             # Top-level Click group, global options
                compute.py          # 'compute' command
                plot.py             # 'plot' command
                info.py             # 'info' command
                convert.py          # 'convert' command
                validate.py         # 'validate' command
                batch.py            # 'batch' command (Tier 3)
                _logging.py         # Logging configuration, progress bars

            gui/                    # Desktop GUI (Tier 2, PyQt6/PySide6)
                __init__.py
                app.py              # QApplication, main window
                fault_editor.py     # Fault element editor widget
                map_panel.py        # Matplotlib canvas widget
                controls.py         # Parameter control widgets
                preferences.py      # Settings dialog
                section_panel.py    # Cross-section display widget
                _signals.py         # Custom Qt signals for model updates

            web/                    # Web GUI (Tier 3)
                __init__.py
                server.py           # FastAPI/Panel server

            exceptions.py          # Custom exception hierarchy

    tests/                          # Test suite
        __init__.py
        conftest.py                 # Shared fixtures, reference data paths
        unit/
            test_okada.py
            test_stress.py
            test_coulomb.py
            test_coordinates.py
            test_oops.py
            test_pipeline.py
            test_types.py
        integration/
            test_inp_parsing.py
            test_output_formats.py
            test_full_pipeline.py
            test_cli.py
        validation/
            test_vs_coulomb34.py
            test_vs_elastic_stresses.py
            test_published_results.py
        performance/
            test_benchmarks.py
        fixtures/
            inp_files/              # Example .inp files from Coulomb 3.4
            reference_outputs/      # Coulomb 3.4 reference .cou/.dat outputs
            okada_reference/        # DC3D reference values from Fortran

    docs/                           # Documentation
    examples/                       # Example notebooks and scripts
    benchmarks/                     # Performance benchmark scripts
```

### 2.2 Module Specifications

Each module below is described with its purpose, key contents, internal dependencies, and external dependencies.

#### 2.2.1 `opencoulomb/__init__.py`

**Purpose**: Package entry point. Exposes the public API surface and version.

```python
"""OpenCoulomb: Open-source Coulomb failure stress computation."""

__version__ = "0.1.0"

# Public API re-exports (Tier 3 convenience imports)
from opencoulomb.types import (
    CoulombModel,
    CoulombResult,
    FaultElement,
    Grid,
    Kode,
    MaterialProperties,
    RegionalStress,
)
from opencoulomb.core import compute_grid, compute_cfs, dc3d, dc3d0
from opencoulomb.io import read_inp, write_cou, write_csv
```

**Dependencies**: None external. Imports from own subpackages.

#### 2.2.2 `opencoulomb/_constants.py`

**Purpose**: Central registry of physical constants, default parameter values, and unit conversion factors. No computation logic.

```python
"""Physical constants and default values for OpenCoulomb."""

# Default material properties
DEFAULT_POISSON: float = 0.25
DEFAULT_YOUNG_BAR: float = 8.0e5       # 80 GPa in bar
DEFAULT_FRICTION: float = 0.4
DEFAULT_DEPTH_KM: float = 10.0

# Unit conversion
KM_TO_M: float = 1000.0
M_TO_KM: float = 0.001
# The 0.001 factor in Coulomb's stress conversion:
# Strains are du(m)/dx(km), stress = E * strain, but we need bar output.
# Since du is in m and dx is in km, the derivative has units 1/1000.
# This factor corrects for that.
STRAIN_UNIT_FACTOR: float = 0.001

# Numerical stability
SINGULARITY_THRESHOLD: float = 1.0e-12
DEPTH_EPSILON: float = 1.0e-6          # km, to avoid z=0 singularity

# Earth
EARTH_RADIUS_KM: float = 6371.0
DEG_TO_RAD: float = 0.017453292519943295   # pi / 180
RAD_TO_DEG: float = 57.29577951308232      # 180 / pi
```

**Dependencies**: None.

#### 2.2.3 `opencoulomb/exceptions.py`

**Purpose**: Custom exception hierarchy for the entire package.

```python
"""OpenCoulomb exception hierarchy."""


class OpenCoulombError(Exception):
    """Base exception for all OpenCoulomb errors."""


# --- Input/Parsing Errors ---

class InputError(OpenCoulombError):
    """Base for input-related errors."""


class ParseError(InputError):
    """Failed to parse an input file."""

    def __init__(self, message: str, filename: str | None = None,
                 line_number: int | None = None):
        self.filename = filename
        self.line_number = line_number
        loc = ""
        if filename:
            loc += f"{filename}"
        if line_number is not None:
            loc += f":{line_number}"
        if loc:
            message = f"{loc}: {message}"
        super().__init__(message)


class ValidationError(InputError):
    """Input data is syntactically valid but physically invalid."""


# --- Computation Errors ---

class ComputationError(OpenCoulombError):
    """Error during numerical computation."""


class SingularityError(ComputationError):
    """Observation point at or near a singularity in the Okada solution."""


class ConvergenceError(ComputationError):
    """Iterative solver did not converge (e.g., OOP optimization)."""


# --- Output Errors ---

class OutputError(OpenCoulombError):
    """Error writing output files."""


class FormatError(OutputError):
    """Unsupported or invalid output format."""


# --- Configuration Errors ---

class ConfigError(OpenCoulombError):
    """Invalid configuration."""
```

**Dependencies**: None (stdlib only).

---

## 3. Core Computation Architecture

This section details every module in `opencoulomb/core/`. These modules contain zero file I/O and zero visualization logic. They operate exclusively on NumPy arrays and OpenCoulomb dataclasses.

### 3.1 Okada DC3D Module (`core/okada.py`)

This is the most performance-critical module. It implements Okada's (1992) closed-form analytical solution for displacement and displacement gradients at any point in a homogeneous, isotropic elastic half-space due to a rectangular or point dislocation source.

#### 3.1.1 Public API

```python
"""Okada (1992) DC3D and DC3D0 dislocation solutions.

All functions are vectorized: scalar observation point parameters (x, y, z)
may be replaced by NumPy arrays of shape (N,) to compute N observation
points in a single call. All outputs then have shape (N,).
"""

import numpy as np
from numpy.typing import NDArray

# Type alias for float arrays that may also be scalar floats
FloatArray = NDArray[np.float64] | float


def dc3d(
    alpha: float,
    x: FloatArray,
    y: FloatArray,
    z: FloatArray,
    depth: float,
    dip: float,
    al1: float,
    al2: float,
    aw1: float,
    aw2: float,
    disl1: float,
    disl2: float,
    disl3: float,
) -> tuple[
    FloatArray, FloatArray, FloatArray,           # ux, uy, uz
    FloatArray, FloatArray, FloatArray,           # uxx, uyx, uzx
    FloatArray, FloatArray, FloatArray,           # uxy, uyy, uzy
    FloatArray, FloatArray, FloatArray,           # uxz, uyz, uzz
]:
    """Compute displacement and gradients for a finite rectangular fault.

    Implements Okada (1992) DC3D: displacement field u_i and displacement
    gradient tensor du_i/dx_j at observation point(s) (x, y, z) due to a
    rectangular dislocation source in an elastic half-space.

    Parameters
    ----------
    alpha : float
        Medium constant = (lambda + mu) / (lambda + 2*mu) = 1/(2*(1-nu)).
    x, y, z : float or ndarray of shape (N,)
        Observation point coordinates in the fault-centered coordinate
        system. z must be <= 0 (negative below free surface).
    depth : float
        Depth of the fault reference point (positive, in km).
    dip : float
        Dip angle in degrees (0-90).
    al1, al2 : float
        Fault half-lengths along strike: from -al1 to +al2 (km).
    aw1, aw2 : float
        Fault half-widths along dip: from -aw1 (down-dip) to +aw2 (km).
    disl1 : float
        Strike-slip dislocation (m). Left-lateral positive (Okada convention).
    disl2 : float
        Dip-slip dislocation (m). Reverse positive.
    disl3 : float
        Tensile dislocation (m). Opening positive.

    Returns
    -------
    tuple of 12 arrays
        (ux, uy, uz, uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz)
        Displacements in meters, gradients as raw du(m)/dx(km) derivatives.

    Raises
    ------
    SingularityError
        If observation point is exactly on the fault plane edge and the
        singularity cannot be resolved by Okada's perturbation method.
    """
    ...


def dc3d0(
    alpha: float,
    x: FloatArray,
    y: FloatArray,
    z: FloatArray,
    depth: float,
    dip: float,
    pot1: float,
    pot2: float,
    pot3: float,
    pot4: float,
) -> tuple[
    FloatArray, FloatArray, FloatArray,           # ux, uy, uz
    FloatArray, FloatArray, FloatArray,           # uxx, uyx, uzx
    FloatArray, FloatArray, FloatArray,           # uxy, uyy, uzy
    FloatArray, FloatArray, FloatArray,           # uxz, uyz, uzz
]:
    """Compute displacement and gradients for a point source.

    Implements Okada (1992) DC3D0: point source variant.

    Parameters
    ----------
    alpha : float
        Medium constant.
    x, y, z : float or ndarray of shape (N,)
        Observation point coordinates.
    depth : float
        Source depth (positive, km).
    dip : float
        Dip angle (degrees).
    pot1 : float
        Strike-slip potency (m^2 for moment / mu).
    pot2 : float
        Dip-slip potency.
    pot3 : float
        Tensile potency.
    pot4 : float
        Inflation potency.

    Returns
    -------
    tuple of 12 arrays
        Same layout as dc3d().
    """
    ...
```

#### 3.1.2 Internal Structure and Sub-Functions

The DC3D computation follows Okada's decomposition into sub-problems. Each sub-function is a private module-level function, vectorized over observation points.

```
dc3d()
  |
  +--> _dccon0(alpha, dip)           --> Precompute common constants
  |      Returns: _OkadaConstants namedtuple
  |
  +--> For each of 4 rectangle corners (Chinnery's notation):
  |      |
  |      +--> _dccon1(x, y, d, sd, cd)  --> Corner-specific parameters
  |      |
  |      +--> _dccon2(xi, et, q, sd, cd, kxi, ket)  --> Secondary params
  |      |
  |      +--> _ua(xi, et, q, disl1, disl2, disl3, consts)
  |      |      Part A: displacement from strike-slip, dip-slip, tensile
  |      |      Returns: (u1, u2, u3, du1/dx1..du3/dx3) -- 12 values
  |      |
  |      +--> _ub(xi, et, q, disl1, disl2, disl3, consts)
  |      |      Part B: image source contributions
  |      |
  |      +--> _uc(xi, et, q, z, disl1, disl2, disl3, consts)
  |             Part C: depth-dependent correction terms
  |
  +--> Sum with Chinnery signs:
  |      f(x,p,q) = f(x,p) - f(x,p-W) - f(x-L,p) + f(x-L,p-W)
  |
  +--> Apply free-surface correction for z != 0
```

Similarly for dc3d0:

```
dc3d0()
  |
  +--> _dccon0(alpha, dip)
  |
  +--> _ua0(xi, et, q, pot1..pot4, consts)    Point source Part A
  +--> _ub0(xi, et, q, pot1..pot4, consts)    Point source Part B
  +--> _uc0(xi, et, q, z, pot1..pot4, consts) Point source Part C
```

#### 3.1.3 Constants Data Structure

```python
from typing import NamedTuple


class _OkadaConstants(NamedTuple):
    """Precomputed constants shared across UA/UB/UC calls for one fault."""
    alp1: float    # (1 - alpha) / 2
    alp2: float    # alpha / 2
    alp3: float    # (1 - alpha) / alpha
    alp4: float    # 1 - alpha
    alp5: float    # alpha
    sd: float      # sin(dip)
    cd: float      # cos(dip)
    sdsd: float    # sin(dip)^2
    cdcd: float    # cos(dip)^2
    sdcd: float    # sin(dip) * cos(dip)
    s2d: float     # sin(2 * dip)
    c2d: float     # cos(2 * dip)
```

#### 3.1.4 Vectorization Strategy

The key to performance is eliminating the Python loop over grid points. All observation-point-dependent variables (`x`, `y`, `z`, `xi`, `et`, `q`, `r`, etc.) are 1-D NumPy arrays of shape `(N,)` where `N = n_x * n_y` (the total number of grid points). Fault parameters (`depth`, `dip`, `disl1`, etc.) remain scalars since we iterate over faults in Python (there are far fewer faults than grid points).

```python
# Pseudocode for the vectorization pattern inside _ua():

def _ua(
    xi: NDArray[np.float64],    # shape (N,)
    et: NDArray[np.float64],    # shape (N,)
    q: NDArray[np.float64],     # shape (N,)
    disl1: float,
    disl2: float,
    disl3: float,
    c: _OkadaConstants,
) -> tuple[NDArray, ...]:       # 12 arrays, each shape (N,)
    """Part A displacement contributions (vectorized)."""
    r = np.sqrt(xi**2 + et**2 + q**2)   # shape (N,)
    # All operations use NumPy broadcasting, no Python loops.
    # Singularity guard:
    r_safe = np.where(r < SINGULARITY_THRESHOLD, SINGULARITY_THRESHOLD, r)
    # ...
    return (u1, u2, u3, u1x, u2x, u3x, u1y, u2y, u3y, u1z, u2z, u3z)
```

The outer loop structure:

```python
# In pipeline.py:
for fault_idx in range(n_source_faults):
    # Transform ALL grid points to this fault's local coords (vectorized)
    x_local, y_local, z_local = geo_to_fault(grid_x, grid_y, grid_z, fault)
    # One dc3d call computes ALL grid points for this fault
    results = dc3d(alpha, x_local, y_local, z_local, ...)
    # Accumulate via superposition
    total_ux += ux
    # ...
```

This means the Python loop runs `n_faults` times (typically 1-100), while the heavy computation inside each iteration is pure NumPy operating on arrays of size `n_grid_points` (typically 10,000-250,000).

#### 3.1.5 Singularity Handling

Okada's solution has mathematical singularities when the observation point lies on the fault plane edges or at exact corners. The original Fortran code handles these by perturbing the observation point by a small epsilon. We replicate this:

```python
# Singularity conditions and handling:
#
# 1. R = 0 (observation point on dislocation line)
#    --> Perturb z by DEPTH_EPSILON
#
# 2. xi = 0 and q = 0 (on fault edge)
#    --> Set singular log/atan terms to 0.0
#
# 3. R + xi = 0 (specific corner case)
#    --> Set log(R + xi) to -log(R - xi)
#
# 4. R + et = 0 (specific corner case)
#    --> Set log(R + et) to -log(R - et)
#
# 5. z = 0 (free surface)
#    --> Use limiting forms of depth-dependent terms

# Implementation: np.where masks for each condition
r_plus_xi = r + xi
singular_mask = np.abs(r_plus_xi) < SINGULARITY_THRESHOLD
log_r_xi = np.where(singular_mask,
                     -np.log(np.abs(r - xi) + SINGULARITY_THRESHOLD),
                     np.log(np.abs(r_plus_xi)))
```

#### 3.1.6 Dependencies

- **Internal**: `opencoulomb._constants`, `opencoulomb.exceptions`
- **External**: `numpy`

---

### 3.2 Stress Computation Module (`core/stress.py`)

Converts displacement gradients from Okada to the full stress tensor via Hooke's law, and rotates tensors between coordinate systems.

#### 3.2.1 Public API

```python
"""Stress tensor computation and rotation."""

import numpy as np
from numpy.typing import NDArray
from opencoulomb.types import MaterialProperties


def gradients_to_stress(
    uxx: NDArray, uyy: NDArray, uzz: NDArray,
    uxy: NDArray, uyx: NDArray,
    uxz: NDArray, uzx: NDArray,
    uyz: NDArray, uzy: NDArray,
    material: MaterialProperties,
) -> tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]:
    """Convert displacement gradients to stress tensor via Hooke's law.

    Applies the 0.001 unit factor for the km/m distance/displacement mismatch.

    Parameters
    ----------
    uxx, uyy, uzz : ndarray of shape (N,)
        Normal displacement gradients (du_i/dx_i).
    uxy, uyx, uxz, uzx, uyz, uzy : ndarray of shape (N,)
        Off-diagonal displacement gradients.
    material : MaterialProperties
        Contains young_modulus (bar) and poisson_ratio.

    Returns
    -------
    sxx, syy, szz, syz, sxz, sxy : ndarray of shape (N,)
        Stress tensor components in bar (Voigt ordering).

    Notes
    -----
    The computation follows Coulomb 3.4 exactly::

        sk = E / (1 + nu)                    # = 2 * shear_modulus
        gk = nu / (1 - 2*nu)                 # = lambda / mu
        vol = uxx + uyy + uzz                # volumetric strain
        sxx = sk * (gk * vol + uxx) * 0.001
        syy = sk * (gk * vol + uyy) * 0.001
        szz = sk * (gk * vol + uzz) * 0.001
        sxy = (E / (2*(1+nu))) * (uxy + uyx) * 0.001
        sxz = (E / (2*(1+nu))) * (uxz + uzx) * 0.001
        syz = (E / (2*(1+nu))) * (uyz + uzy) * 0.001
    """
    ...


def tensor_rotate(
    sxx: NDArray, syy: NDArray, szz: NDArray,
    syz: NDArray, sxz: NDArray, sxy: NDArray,
    strike_rad: float,
) -> tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]:
    """Rotate stress tensor from fault-local to geographic coordinates.

    Implements tensor_trans.m from Coulomb 3.4. The rotation is about the
    vertical axis by the fault strike angle.

    Parameters
    ----------
    sxx..sxy : ndarray of shape (N,)
        Stress tensor in fault-local coordinates (bar).
    strike_rad : float
        Fault strike angle in radians (clockwise from North).

    Returns
    -------
    sxx_g..sxy_g : ndarray of shape (N,)
        Stress tensor in geographic coordinates (bar).

    Notes
    -----
    Uses the 6x6 Bond transformation matrix built from direction cosines.
    For rotation about the vertical axis by angle theta::

        l1 = [cos(theta),  sin(theta), 0]
        l2 = [-sin(theta), cos(theta), 0]
        l3 = [0,           0,          1]

    The 6x6 transformation matrix M is then applied as::

        [s_geo] = M . [s_local]

    where [s] = [sxx, syy, szz, syz, sxz, sxy]^T (Voigt notation).
    """
    ...


def compute_strain(
    uxx: NDArray, uyy: NDArray, uzz: NDArray,
    uxy: NDArray, uyx: NDArray,
    uxz: NDArray, uzx: NDArray,
    uyz: NDArray, uzy: NDArray,
) -> tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]:
    """Compute symmetric strain tensor from displacement gradients.

    Returns
    -------
    exx, eyy, ezz, eyz, exz, exy : ndarray of shape (N,)
        exy = 0.5 * (uxy + uyx), etc.
    """
    ...
```

#### 3.2.2 The 0.001 Unit Factor

This is critical to get right. Okada's DC3D returns displacements in meters and displacement gradients as du(m)/dx(km). To convert to stress in bar:

```
stress (bar) = E (bar) * strain (dimensionless)
strain = du(m) / dx(m) = du(m) / (dx(km) * 1000) = (du/dx from Okada) * 0.001
```

The 0.001 factor converts the mixed-unit gradient to a true dimensionless strain before multiplying by Young's modulus. Applied inside `gradients_to_stress()` at the same point as in Coulomb 3.4 for numerical compatibility.

#### 3.2.3 Dependencies

- **Internal**: `opencoulomb.types.MaterialProperties`, `opencoulomb._constants`
- **External**: `numpy`

---

### 3.3 CFS Calculation Module (`core/coulomb.py`)

Resolves the 3D stress tensor onto a receiver fault plane and computes Coulomb failure stress change.

#### 3.3.1 Public API

```python
"""Coulomb failure stress calculation."""

import numpy as np
from numpy.typing import NDArray


def bond_matrix(
    strike_rad: float, dip_rad: float, rake_rad: float,
) -> NDArray:
    """Build the 6x6 Bond transformation matrix for stress resolution.

    Transforms stress from geographic (x=E, y=N, z=Up) to fault-local
    (x'=strike, y'=updip, z'=normal) coordinates.

    Parameters
    ----------
    strike_rad, dip_rad, rake_rad : float
        Receiver fault orientation in radians.

    Returns
    -------
    M : ndarray of shape (6, 6)
        Bond transformation matrix.

    Notes
    -----
    Direction cosine matrix (3x3)::

        n1 = strike dir  = [sin(strike), cos(strike), 0]
        n2 = updip dir   = [-cos(strike)*cos(dip), sin(strike)*cos(dip), sin(dip)]
        n3 = fault normal = [cos(strike)*sin(dip), -sin(strike)*sin(dip), cos(dip)]

    The 6x6 Bond matrix is built from these using standard Voigt
    transformation rules.
    """
    ...


def resolve_stress(
    sxx: NDArray, syy: NDArray, szz: NDArray,
    syz: NDArray, sxz: NDArray, sxy: NDArray,
    strike: float, dip: float, rake: float,
) -> tuple[NDArray, NDArray]:
    """Resolve stress tensor onto a receiver fault plane.

    Parameters
    ----------
    sxx..sxy : ndarray of shape (N,)
        Full stress tensor in geographic coordinates (bar).
    strike, dip, rake : float
        Receiver fault orientation (degrees).

    Returns
    -------
    shear : ndarray of shape (N,)
        Shear stress resolved in the rake direction (bar).
        Positive = promotes slip.
    normal : ndarray of shape (N,)
        Normal stress on the fault plane (bar).
        Positive = unclamping (promotes failure).
    """
    ...


def compute_cfs(
    sxx: NDArray, syy: NDArray, szz: NDArray,
    syz: NDArray, sxz: NDArray, sxy: NDArray,
    strike: float, dip: float, rake: float,
    friction: float,
) -> tuple[NDArray, NDArray, NDArray]:
    """Compute Coulomb failure stress change on a receiver fault.

    Returns
    -------
    cfs, shear, normal : ndarray of shape (N,)
        CFS = shear + friction * normal (bar).
    """
    shear, normal = resolve_stress(sxx, syy, szz, syz, sxz, sxy,
                                    strike, dip, rake)
    cfs = shear + friction * normal
    return cfs, shear, normal


def compute_cfs_on_elements(
    sxx: NDArray, syy: NDArray, szz: NDArray,
    syz: NDArray, sxz: NDArray, sxy: NDArray,
    strikes: NDArray, dips: NDArray, rakes: NDArray,
    friction: float,
) -> tuple[NDArray, NDArray, NDArray]:
    """Compute CFS at multiple points with different receiver orientations.

    Parameters
    ----------
    sxx..sxy : ndarray of shape (M,)
        Stress at M receiver element centers.
    strikes, dips, rakes : ndarray of shape (M,)
        Orientation of each receiver (degrees).
    friction : float

    Returns
    -------
    cfs, shear, normal : ndarray of shape (M,)
    """
    ...
```

#### 3.3.2 Dependencies

- **Internal**: `opencoulomb._constants`
- **External**: `numpy`

---

### 3.4 Coordinate Transformation Module (`core/coordinates.py`)

```python
"""Coordinate transformations between geographic and fault-local systems."""

import numpy as np
from numpy.typing import NDArray
from opencoulomb.types import FaultElement


def geo_to_fault(
    x_geo: NDArray, y_geo: NDArray, z_geo: NDArray,
    fault: FaultElement,
) -> tuple[NDArray, NDArray, NDArray]:
    """Transform geographic coords to Okada's fault-local system.

    Fault-local system:
    - Origin at fault center point (projected along dip)
    - X along fault strike
    - Y perpendicular to strike (horizontal)
    - Z vertical (negative downward, Okada convention)
    """
    ...


def fault_to_geo(
    ux_fault: NDArray, uy_fault: NDArray, uz_fault: NDArray,
    strike_rad: float,
) -> tuple[NDArray, NDArray, NDArray]:
    """Rotate displacement vector from fault-local to geographic."""
    ...


def compute_fault_geometry(fault: FaultElement) -> dict:
    """Compute derived geometric properties of a fault element.

    Returns dict with keys: strike_rad, strike_deg, length_km, width_km,
    center_x, center_y, center_depth, al1, al2, aw1, aw2, corners.
    """
    ...


def lonlat_to_xy(
    lon: NDArray, lat: NDArray,
    ref_lon: float, ref_lat: float,
) -> tuple[NDArray, NDArray]:
    """Longitude/latitude to local km (equirectangular projection)."""
    ...


def xy_to_lonlat(
    x: NDArray, y: NDArray,
    ref_lon: float, ref_lat: float,
) -> tuple[NDArray, NDArray]:
    """Local km back to longitude/latitude."""
    ...
```

**Dependencies**: `opencoulomb.types.FaultElement`, `opencoulomb._constants`, `numpy`. Optional: `pyproj` (Tier 2 UTM).

---

### 3.5 Optimally Oriented Planes Module (`core/oops.py`)

```python
"""Optimally Oriented Planes (OOPs) computation."""

import numpy as np
from numpy.typing import NDArray
from opencoulomb.types import RegionalStress


def compute_regional_stress_tensor(
    regional: RegionalStress,
    depth: float | NDArray,
) -> tuple[NDArray, NDArray, NDArray, NDArray, NDArray, NDArray]:
    """Convert regional stress specification to tensor components.

    Stress intensity at depth = base_intensity + gradient * depth.
    Rotates principal stresses to geographic coordinates using
    the specified direction and dip for each principal axis.
    """
    ...


def find_optimal_planes(
    sxx_total: NDArray, syy_total: NDArray, szz_total: NDArray,
    syz_total: NDArray, sxz_total: NDArray, sxy_total: NDArray,
    friction: float,
) -> tuple[NDArray, NDArray, NDArray, NDArray]:
    """Find optimally oriented fault plane at each grid point.

    Algorithm:
    1. Compute eigenvalues (s1 >= s2 >= s3) and eigenvectors
       using np.linalg.eigh on 3x3 stress tensor matrices
    2. Mohr-Coulomb angle: beta = pi/4 - 0.5 * atan(mu)
    3. Two conjugate planes rotated +/- beta from s1 toward s3
    4. Convert plane normals to (strike, dip)
    5. Compute CFS on each conjugate plane
    6. Return the plane with max |CFS|

    Returns
    -------
    strike_opt, dip_opt, cfs_opt, rake_opt : ndarray of shape (N,)
    """
    ...
```

**Dependencies**: `opencoulomb.types.RegionalStress`, `opencoulomb.core.coulomb`, `opencoulomb._constants`, `numpy`.

---

### 3.6 Computation Pipeline Orchestrator (`core/pipeline.py`)

```python
"""Computation pipeline orchestrator."""

import numpy as np
from numpy.typing import NDArray
from opencoulomb.types import (
    CoulombModel, CoulombResult, StressResult,
    CrossSectionSpec, CrossSectionResult,
    FaultElement, MaterialProperties, GridSpec,
)


def compute_grid(model: CoulombModel) -> CoulombResult:
    """Run full computation pipeline on a 2D grid.

    Primary entry point replicating Coulomb 3.4's coulomb_calc_and_view.m.

    Algorithm:
    1. Generate grid coordinates from model.grid
    2. Initialize accumulator arrays (stress tensor, displacement)
    3. For each source fault:
       a. Compute fault geometry (strike, center, Okada params)
       b. Transform grid points to fault-local coordinates
       c. Call dc3d() or dc3d0() depending on KODE
       d. Rotate displacements back to geographic
       e. Convert gradients to stress (Hooke's law + 0.001 factor)
       f. Rotate stress tensor to geographic
       g. Accumulate via superposition
    4. Resolve onto receivers (specified or OOP)
    5. Package into CoulombResult
    """
    ...


def compute_stress_field(
    grid_x: NDArray, grid_y: NDArray, grid_z: NDArray,
    source_faults: list[FaultElement],
    material: MaterialProperties,
) -> StressResult:
    """Compute raw stress tensor and displacements at arbitrary points.

    Lower-level: does not resolve onto receivers or compute CFS.
    """
    ...


def compute_section(
    model: CoulombModel,
    section: CrossSectionSpec,
) -> CrossSectionResult:
    """Compute stress/displacement along a vertical cross-section."""
    ...


def compute_at_points(
    points_x: NDArray, points_y: NDArray, points_z: NDArray,
    source_faults: list[FaultElement],
    material: MaterialProperties,
) -> StressResult:
    """Compute stress/displacement at arbitrary points (GPS, elements)."""
    return compute_stress_field(points_x, points_y, points_z,
                                source_faults, material)
```

#### 3.6.1 Grid Generation

```python
def _generate_grid(grid_spec: GridSpec) -> tuple[NDArray, NDArray, NDArray]:
    """Generate flattened grid coordinates.

    N = n_x * n_y where n_x = floor((finish_x - start_x) / x_inc) + 1.
    z is filled with -depth (negative, Okada convention).
    """
    x_coords = np.arange(grid_spec.start_x,
                          grid_spec.finish_x + grid_spec.x_inc * 0.5,
                          grid_spec.x_inc)
    y_coords = np.arange(grid_spec.start_y,
                          grid_spec.finish_y + grid_spec.y_inc * 0.5,
                          grid_spec.y_inc)
    yy, xx = np.meshgrid(y_coords, x_coords, indexing='ij')
    grid_x = xx.ravel()
    grid_y = yy.ravel()
    grid_z = np.full_like(grid_x, -grid_spec.depth)
    return grid_x, grid_y, grid_z
```

#### 3.6.2 Source Fault Dispatch by KODE

```python
def _compute_single_fault(
    x_local: NDArray, y_local: NDArray, z_local: NDArray,
    fault: FaultElement, geometry: dict, alpha: float,
) -> tuple[NDArray, ...]:
    """Dispatch to dc3d or dc3d0 based on fault KODE.

    KODE 100: dc3d(disl1=-col5, disl2=col6, disl3=0)
              Sign flip on col5: Coulomb=RL+, Okada=LL+
    KODE 200: dc3d(disl1=-col6, disl2=0, disl3=col5)
              Tensile + right-lateral
    KODE 300: dc3d(disl1=0, disl2=col6, disl3=col5)
              Tensile + reverse
    KODE 400: dc3d0(pot1=-col5, pot2=col6, pot3=0, pot4=0)
              Point source
    KODE 500: dc3d0(pot1=0, pot2=0, pot3=col5, pot4=col6)
              Tensile + inflation point source
    """
    ...
```

#### 3.6.3 Multi-Fault Superposition

```python
# Initialize accumulators
n_points = len(grid_x)
total_ux = np.zeros(n_points)
total_uy = np.zeros(n_points)
total_uz = np.zeros(n_points)
total_sxx = np.zeros(n_points)
# ... (6 stress + 3 displacement accumulators)

for fault in source_faults:
    geom = compute_fault_geometry(fault)
    x_f, y_f, z_f = geo_to_fault(grid_x, grid_y, grid_z, fault)

    ux, uy, uz, *grads = _compute_single_fault(
        x_f, y_f, z_f, fault, geom, alpha)

    # Rotate displacements: fault-local --> geographic
    ux_g, uy_g, uz_g = fault_to_geo(ux, uy, uz, geom['strike_rad'])
    total_ux += ux_g
    total_uy += uy_g
    total_uz += uz_g

    # Compute stress from gradients (includes 0.001 factor)
    sxx, syy, szz, syz, sxz, sxy = gradients_to_stress(*grads, material)

    # Rotate stress: fault-local --> geographic
    sxx_g, syy_g, szz_g, syz_g, sxz_g, sxy_g = tensor_rotate(
        sxx, syy, szz, syz, sxz, sxy, geom['strike_rad'])

    total_sxx += sxx_g
    total_syy += syy_g
    total_szz += szz_g
    total_syz += syz_g
    total_sxz += sxz_g
    total_sxy += sxy_g
```

#### 3.6.4 Memory Budget

For large grids, 12 arrays from `dc3d()` at shape `(N,)` are the main memory consumers:

```
Memory = 9 * N * 8 bytes (accumulators)
       + 12 * N * 8 bytes (per-fault temporaries, freed each iteration)
       + 3 * N * 8 bytes (grid coordinates)
       = ~24 * N * 8 bytes peak
       = 48 MB for N=250,000 (500x500 grid)
```

Well within the 500 MB budget. For extreme cases (Tier 3), process in chunks:

```python
CHUNK_SIZE = 100_000

if n_points > CHUNK_SIZE:
    for start in range(0, n_points, CHUNK_SIZE):
        end = min(start + CHUNK_SIZE, n_points)
        chunk_result = _compute_chunk(grid_x[start:end], ...)
```

**Dependencies**: All `core/` modules, all `types/` modules, `numpy`.

---

## 4. Data Model

All data structures are Python `dataclasses` using `__slots__` for memory efficiency. Every field has an explicit type annotation, unit in the docstring, and validation in `__post_init__`. All structures are immutable where practical (frozen dataclasses) to prevent accidental mutation during computation.

### 4.1 `types/material.py` -- MaterialProperties

```python
"""Material property data structures."""

from dataclasses import dataclass
from opencoulomb._constants import (
    DEFAULT_POISSON, DEFAULT_YOUNG_BAR, DEFAULT_FRICTION, DEFAULT_DEPTH_KM,
)
from opencoulomb.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class MaterialProperties:
    """Elastic material properties for the half-space.

    Attributes
    ----------
    poisson : float
        Poisson's ratio (dimensionless, 0 < nu < 0.5). Default: 0.25.
    young : float
        Young's modulus in bar (1 bar = 0.1 MPa). Default: 8.0e5 (80 GPa).
    friction : float
        Effective friction coefficient mu' (dimensionless, >= 0). Default: 0.4.
        Includes pore pressure effects implicitly.
    depth : float
        Default calculation depth in km (>= 0). Default: 10.0.

    Derived (computed, not stored):
        alpha = 1 / (2 * (1 - poisson))       # Okada medium constant
        shear_modulus = young / (2 * (1 + poisson))  # mu, in bar
        lame_lambda = young * poisson / ((1 + poisson) * (1 - 2*poisson))
    """
    poisson: float = DEFAULT_POISSON
    young: float = DEFAULT_YOUNG_BAR
    friction: float = DEFAULT_FRICTION
    depth: float = DEFAULT_DEPTH_KM

    def __post_init__(self) -> None:
        if not (0.0 < self.poisson < 0.5):
            raise ValidationError(
                f"Poisson's ratio must be in (0, 0.5), got {self.poisson}")
        if self.young <= 0:
            raise ValidationError(
                f"Young's modulus must be positive, got {self.young}")
        if self.friction < 0:
            raise ValidationError(
                f"Friction must be non-negative, got {self.friction}")
        if self.depth < 0:
            raise ValidationError(
                f"Depth must be non-negative, got {self.depth}")

    @property
    def alpha(self) -> float:
        """Okada medium constant: (lambda+mu)/(lambda+2*mu)."""
        return 1.0 / (2.0 * (1.0 - self.poisson))

    @property
    def shear_modulus(self) -> float:
        """Shear modulus mu in bar."""
        return self.young / (2.0 * (1.0 + self.poisson))

    @property
    def lame_lambda(self) -> float:
        """Lame's first parameter lambda in bar."""
        nu = self.poisson
        return self.young * nu / ((1 + nu) * (1 - 2 * nu))
```

### 4.2 `types/fault.py` -- FaultElement and Kode

```python
"""Fault element data structures."""

from dataclasses import dataclass
from enum import IntEnum
from opencoulomb.exceptions import ValidationError


class Kode(IntEnum):
    """Fault element type code.

    Determines the physical interpretation of slip columns 5 and 6
    in the .inp file format.
    """
    STANDARD = 100       # col5=right-lateral, col6=reverse
    TENSILE_RL = 200     # col5=tensile, col6=right-lateral
    TENSILE_REV = 300    # col5=tensile, col6=reverse
    POINT_SOURCE = 400   # col5=right-lateral, col6=reverse (point)
    TENSILE_INFL = 500   # col5=tensile, col6=inflation


@dataclass(frozen=True, slots=True)
class FaultElement:
    """A single fault element (source or receiver).

    Attributes
    ----------
    x_start : float
        Starting X coordinate of surface trace (km, East).
    y_start : float
        Starting Y coordinate of surface trace (km, North).
    x_fin : float
        Ending X coordinate of surface trace (km, East).
    y_fin : float
        Ending Y coordinate of surface trace (km, North).
    kode : Kode
        Element type code (100, 200, 300, 400, 500).
    slip_1 : float
        Slip component 1 (m). Interpretation depends on kode:
        KODE 100/400: right-lateral slip (positive = right-lateral)
        KODE 200/300/500: tensile opening (positive = opening)
    slip_2 : float
        Slip component 2 (m). Interpretation depends on kode:
        KODE 100/400: reverse slip (positive = reverse/thrust)
        KODE 200: right-lateral slip
        KODE 300: reverse slip
        KODE 500: inflation
    dip : float
        Dip angle in degrees (0-90, always positive).
    top_depth : float
        Fault top depth in km (>= 0).
    bottom_depth : float
        Fault bottom depth in km (> top_depth).
    label : str
        Optional text label/name for the element. Default: "".
    element_index : int
        1-based element number from .inp file. Default: 0.
    """
    x_start: float
    y_start: float
    x_fin: float
    y_fin: float
    kode: Kode
    slip_1: float
    slip_2: float
    dip: float
    top_depth: float
    bottom_depth: float
    label: str = ""
    element_index: int = 0

    def __post_init__(self) -> None:
        if not (0 <= self.dip <= 90):
            raise ValidationError(
                f"Dip must be in [0, 90] degrees, got {self.dip}")
        if self.top_depth < 0:
            raise ValidationError(
                f"Top depth must be >= 0, got {self.top_depth}")
        if self.bottom_depth <= self.top_depth:
            raise ValidationError(
                f"Bottom depth ({self.bottom_depth}) must exceed "
                f"top depth ({self.top_depth})")

    @property
    def is_source(self) -> bool:
        """True if this element has non-zero slip (is a source fault)."""
        return self.slip_1 != 0.0 or self.slip_2 != 0.0

    @property
    def is_receiver(self) -> bool:
        """True if this element has zero slip (is a receiver fault)."""
        return not self.is_source

    @property
    def is_point_source(self) -> bool:
        """True if this is a point source (KODE 400 or 500)."""
        return self.kode in (Kode.POINT_SOURCE, Kode.TENSILE_INFL)

    @property
    def strike_deg(self) -> float:
        """Strike angle in degrees, computed from trace endpoints."""
        import math
        dx = self.x_fin - self.x_start
        dy = self.y_fin - self.y_start
        return math.degrees(math.atan2(dx, dy)) % 360.0

    @property
    def rake_deg(self) -> float:
        """Rake angle in degrees, computed from slip components.

        Follows the convention: rake = atan2(reverse_slip, rl_slip).
        For KODE 100: rake = atan2(slip_2, -slip_1)
        (sign flip because Coulomb RL+ but rake measured differently).
        """
        import math
        if self.kode == Kode.STANDARD or self.kode == Kode.POINT_SOURCE:
            return math.degrees(math.atan2(self.slip_2, -self.slip_1))
        return 0.0  # Not well-defined for tensile sources
```

### 4.3 `types/grid.py` -- GridSpec

```python
"""Grid specification data structures."""

from dataclasses import dataclass
import math
from opencoulomb.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class GridSpec:
    """Computation grid specification.

    Attributes
    ----------
    start_x : float
        Western boundary (km, East from origin).
    start_y : float
        Southern boundary (km, North from origin).
    finish_x : float
        Eastern boundary (km).
    finish_y : float
        Northern boundary (km).
    x_inc : float
        Grid spacing in X/East direction (km, > 0).
    y_inc : float
        Grid spacing in Y/North direction (km, > 0).
    depth : float
        Calculation depth (km, >= 0). Overrides material.depth when set.
    """
    start_x: float
    start_y: float
    finish_x: float
    finish_y: float
    x_inc: float
    y_inc: float
    depth: float = 10.0

    def __post_init__(self) -> None:
        if self.finish_x <= self.start_x:
            raise ValidationError("finish_x must exceed start_x")
        if self.finish_y <= self.start_y:
            raise ValidationError("finish_y must exceed start_y")
        if self.x_inc <= 0 or self.y_inc <= 0:
            raise ValidationError("Grid increments must be positive")

    @property
    def n_x(self) -> int:
        """Number of grid points in X direction."""
        return math.floor((self.finish_x - self.start_x) / self.x_inc) + 1

    @property
    def n_y(self) -> int:
        """Number of grid points in Y direction."""
        return math.floor((self.finish_y - self.start_y) / self.y_inc) + 1

    @property
    def n_points(self) -> int:
        """Total number of grid points."""
        return self.n_x * self.n_y
```

### 4.4 `types/stress.py` -- RegionalStress, StressTensor

```python
"""Stress field data structures."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PrincipalStress:
    """One principal stress axis with orientation and magnitude.

    Attributes
    ----------
    direction : float
        Azimuth in degrees (clockwise from North, 0-360).
    dip : float
        Dip from horizontal in degrees (-90 to 90).
    intensity : float
        Stress magnitude at surface (bar). Compression positive.
    gradient : float
        Stress increase with depth (bar/km).
    """
    direction: float
    dip: float
    intensity: float
    gradient: float


@dataclass(frozen=True, slots=True)
class RegionalStress:
    """Regional background stress field (3 principal stresses).

    Convention: s1 >= s2 >= s3 (most compressive to least compressive).
    - Normal faulting regime: s1 vertical
    - Thrust regime: s3 vertical
    - Strike-slip regime: s2 vertical

    Attributes
    ----------
    s1 : PrincipalStress
        Maximum compressive stress (sigma-1).
    s2 : PrincipalStress
        Intermediate stress (sigma-2).
    s3 : PrincipalStress
        Minimum compressive / maximum tensile stress (sigma-3).
    """
    s1: PrincipalStress
    s2: PrincipalStress
    s3: PrincipalStress


@dataclass(frozen=True, slots=True)
class StressTensorComponents:
    """6-component stress tensor at a single point (Voigt notation).

    All values in bar. Geographic coordinates: x=East, y=North, z=Up.

    Attributes
    ----------
    sxx, syy, szz : float
        Normal stress components (bar).
    syz, sxz, sxy : float
        Shear stress components (bar).
    """
    sxx: float
    syy: float
    szz: float
    syz: float
    sxz: float
    sxy: float
```

### 4.5 `types/result.py` -- Computation Results

```python
"""Computation result data structures."""

from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray


@dataclass(slots=True)
class StressResult:
    """Raw stress tensor and displacement at observation points.

    All arrays have shape (N,) where N is the number of observation points.

    Attributes
    ----------
    x, y, z : ndarray of shape (N,)
        Observation point coordinates (km). z negative = below surface.
    ux, uy, uz : ndarray of shape (N,)
        Displacement components (m). East, North, Up.
    sxx, syy, szz, syz, sxz, sxy : ndarray of shape (N,)
        Stress tensor components (bar).
    """
    x: NDArray[np.float64]
    y: NDArray[np.float64]
    z: NDArray[np.float64]
    ux: NDArray[np.float64]
    uy: NDArray[np.float64]
    uz: NDArray[np.float64]
    sxx: NDArray[np.float64]
    syy: NDArray[np.float64]
    szz: NDArray[np.float64]
    syz: NDArray[np.float64]
    sxz: NDArray[np.float64]
    sxy: NDArray[np.float64]

    @property
    def n_points(self) -> int:
        return len(self.x)


@dataclass(slots=True)
class CoulombResult:
    """Complete computation result including CFS.

    Extends StressResult with Coulomb failure stress and optional
    optimally oriented plane information.

    Attributes
    ----------
    stress : StressResult
        Raw stress tensor and displacement field.
    cfs : ndarray of shape (N,)
        Coulomb failure stress change (bar).
    shear : ndarray of shape (N,)
        Resolved shear stress change (bar).
    normal : ndarray of shape (N,)
        Resolved normal stress change (bar).
    receiver_strike : float
        Receiver fault strike used for CFS calculation (degrees).
    receiver_dip : float
        Receiver fault dip (degrees).
    receiver_rake : float
        Receiver fault rake (degrees).
    grid_shape : tuple[int, int]
        (n_y, n_x) shape for reshaping flat arrays to 2D grids.
    oops_strike : ndarray of shape (N,) or None
        Optimal fault strike at each point (degrees). None if not OOP mode.
    oops_dip : ndarray of shape (N,) or None
        Optimal fault dip at each point (degrees). None if not OOP mode.
    oops_rake : ndarray of shape (N,) or None
        Optimal fault rake (degrees). None if not OOP mode.
    """
    stress: StressResult
    cfs: NDArray[np.float64]
    shear: NDArray[np.float64]
    normal: NDArray[np.float64]
    receiver_strike: float
    receiver_dip: float
    receiver_rake: float
    grid_shape: tuple[int, int]
    oops_strike: NDArray[np.float64] | None = None
    oops_dip: NDArray[np.float64] | None = None
    oops_rake: NDArray[np.float64] | None = None

    def cfs_grid(self) -> NDArray[np.float64]:
        """Reshape CFS to 2D grid: shape (n_y, n_x)."""
        return self.cfs.reshape(self.grid_shape)

    def displacement_grid(self) -> tuple[NDArray, NDArray, NDArray]:
        """Reshape displacements to 2D grids."""
        s = self.grid_shape
        return (self.stress.ux.reshape(s),
                self.stress.uy.reshape(s),
                self.stress.uz.reshape(s))


@dataclass(slots=True)
class ElementResult:
    """CFS results on individual receiver fault elements.

    Attributes
    ----------
    elements : list of FaultElement
        Receiver fault elements.
    cfs : ndarray of shape (M,)
        CFS at each receiver element center (bar).
    shear : ndarray of shape (M,)
        Shear stress at each receiver (bar).
    normal : ndarray of shape (M,)
        Normal stress at each receiver (bar).
    """
    elements: list  # list[FaultElement], avoid circular import
    cfs: NDArray[np.float64]
    shear: NDArray[np.float64]
    normal: NDArray[np.float64]
```

### 4.6 `types/model.py` -- CoulombModel (Aggregate Root)

```python
"""Top-level model data structure."""

from dataclasses import dataclass, field

from opencoulomb.types.fault import FaultElement
from opencoulomb.types.grid import GridSpec
from opencoulomb.types.material import MaterialProperties
from opencoulomb.types.stress import RegionalStress


@dataclass(slots=True)
class CoulombModel:
    """Complete input model for a Coulomb stress computation.

    This is the aggregate root: it contains everything needed to run
    a computation. It is produced by the .inp parser and consumed by
    the computation pipeline.

    Attributes
    ----------
    title : str
        Model title (from .inp file lines 1-2).
    material : MaterialProperties
        Elastic material properties.
    faults : list of FaultElement
        All fault elements (both source and receiver).
    grid : GridSpec
        Computation grid specification.
    regional_stress : RegionalStress or None
        Background regional stress field. None if not specified.
    n_fixed : int
        Number of source (fixed) fault elements. Elements 0..n_fixed-1
        are sources; n_fixed..end are receivers.
    symmetry : int
        Symmetry flag (1 = none). From .inp file.
    x_sym : float
        X symmetry axis (km).
    y_sym : float
        Y symmetry axis (km).
    """
    title: str
    material: MaterialProperties
    faults: list[FaultElement]
    grid: GridSpec
    n_fixed: int
    regional_stress: RegionalStress | None = None
    symmetry: int = 1
    x_sym: float = 0.0
    y_sym: float = 0.0

    @property
    def source_faults(self) -> list[FaultElement]:
        """Fault elements with non-zero slip (sources)."""
        return self.faults[:self.n_fixed]

    @property
    def receiver_faults(self) -> list[FaultElement]:
        """Fault elements with zero slip (receivers)."""
        return self.faults[self.n_fixed:]

    @property
    def n_sources(self) -> int:
        return self.n_fixed

    @property
    def n_receivers(self) -> int:
        return len(self.faults) - self.n_fixed
```

### 4.7 `types/section.py` -- Cross-Section

```python
"""Cross-section data structures."""

from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class CrossSectionSpec:
    """Cross-section profile specification.

    Attributes
    ----------
    start_x, start_y : float
        Profile start point (km).
    finish_x, finish_y : float
        Profile end point (km).
    depth_min : float
        Minimum depth (km, >= 0). Typically 0 (surface).
    depth_max : float
        Maximum depth (km, > depth_min).
    z_inc : float
        Vertical spacing (km, > 0).
    """
    start_x: float
    start_y: float
    finish_x: float
    finish_y: float
    depth_min: float
    depth_max: float
    z_inc: float


@dataclass(slots=True)
class CrossSectionResult:
    """Computation results on a cross-section grid.

    Attributes
    ----------
    distance : ndarray of shape (N_horiz,)
        Horizontal distance along the profile (km).
    depth : ndarray of shape (N_vert,)
        Depth values (km, positive downward).
    cfs : ndarray of shape (N_vert, N_horiz)
        CFS on the cross-section grid (bar).
    shear : ndarray of shape (N_vert, N_horiz)
        Shear stress (bar).
    normal : ndarray of shape (N_vert, N_horiz)
        Normal stress (bar).
    ux, uy, uz : ndarray of shape (N_vert, N_horiz)
        Displacement components (m).
    sxx, syy, szz, syz, sxz, sxy : ndarray of shape (N_vert, N_horiz)
        Full stress tensor on the section (bar).
    spec : CrossSectionSpec
        The specification that produced this result.
    """
    distance: NDArray[np.float64]
    depth: NDArray[np.float64]
    cfs: NDArray[np.float64]
    shear: NDArray[np.float64]
    normal: NDArray[np.float64]
    ux: NDArray[np.float64]
    uy: NDArray[np.float64]
    uz: NDArray[np.float64]
    sxx: NDArray[np.float64]
    syy: NDArray[np.float64]
    szz: NDArray[np.float64]
    syz: NDArray[np.float64]
    sxz: NDArray[np.float64]
    sxy: NDArray[np.float64]
    spec: CrossSectionSpec
```

---

## 5. I/O Architecture

### 5.1 `.inp` Parser (`io/inp_parser.py`)

The `.inp` parser uses a state machine design to handle the sequential sections of the file format. This is more robust than regex-only parsing for the fixed-width format with its irregular whitespace and optional sections.

#### 5.1.1 State Machine Design

```
                    +----------+
                    |  START   |
                    +----+-----+
                         |
                         v
                    +----------+
                    | TITLE    |  Lines 1-2: free text
                    +----+-----+
                         |
                         v
                    +----------+
                    | PARAMS   |  Lines 3-4: #reg1=, PR1=, E1=, FRIC=
                    +----+-----+
                         |
                         v
                    +----------+
                    | STRESS   |  S1DR=, S2DR=, S3DR= (regional stress)
                    +----+-----+
                         |
                         v
                    +----------+
                    | FAULTS   |  Column header, then fault element lines
                    +----+-----+  (source section, blank, receiver section)
                         |
                         v
                    +----------+
                    | GRID     |  "Grid Parameters" keyword, 6 param lines
                    +----+-----+
                         |
                         v
                    +----------+
                    | OPTIONAL |  "Cross Section", "Map info" (if present)
                    +----+-----+
                         |
                         v
                    +----------+
                    |   DONE   |
                    +----------+
```

#### 5.1.2 Public API

```python
"""Coulomb .inp file parser."""

from pathlib import Path
from opencoulomb.types import CoulombModel
from opencoulomb.exceptions import ParseError


def read_inp(path: str | Path) -> CoulombModel:
    """Parse a Coulomb 3.4 .inp file into a CoulombModel.

    Parameters
    ----------
    path : str or Path
        Path to the .inp file.

    Returns
    -------
    CoulombModel
        Complete parsed model ready for computation.

    Raises
    ------
    ParseError
        If the file cannot be parsed. Includes filename and line number.
    ValidationError
        If the file parses but contains physically invalid values.
    FileNotFoundError
        If the file does not exist.
    """
    ...


def parse_inp_string(text: str, filename: str = "<string>") -> CoulombModel:
    """Parse .inp format from a string (for testing and API use)."""
    ...
```

#### 5.1.3 Internal Parser Structure

```python
from enum import Enum, auto


class _ParserState(Enum):
    START = auto()
    TITLE = auto()
    PARAMS = auto()
    STRESS = auto()
    FAULTS_HEADER = auto()
    SOURCE_FAULTS = auto()
    RECEIVER_HEADER = auto()
    RECEIVER_FAULTS = auto()
    GRID = auto()
    CROSS_SECTION = auto()
    MAP_INFO = auto()
    DONE = auto()


class _InpParser:
    """State machine parser for .inp files."""

    def __init__(self, filename: str = "<string>"):
        self.filename = filename
        self.state = _ParserState.START
        self.line_number = 0
        self.title_lines: list[str] = []
        self.param_lines: list[str] = []
        self.stress_lines: list[str] = []
        self.fault_lines: list[str] = []
        self.grid_lines: list[str] = []
        self.section_lines: list[str] = []
        self.map_lines: list[str] = []

    def parse(self, text: str) -> CoulombModel:
        """Run the state machine over all lines."""
        ...

    def _transition(self, line: str) -> None:
        """Process one line and potentially change state."""
        ...

    def _parse_params(self) -> dict:
        """Extract key=value pairs from parameter lines.

        Handles both space-separated and '=' delimited formats.
        Uses regex: r'(\w+)\s*=\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)'
        """
        ...

    def _parse_fault_line(self, line: str) -> FaultElement:
        """Parse one fixed-width fault element line.

        Fixed-width column positions (approximate, but we use split
        with fallback to positional parsing for robustness):
        - Columns are whitespace-delimited in practice
        - Label is everything after the 11th numeric field
        """
        ...

    def _parse_grid_param(self, line: str) -> tuple[int, float]:
        """Parse one grid parameter line.

        Format: '  N  ---  Key = Value'
        Returns: (param_number, value)
        """
        ...
```

#### 5.1.4 Parsing Strategy for Fixed-Width Quirks

The `.inp` format is nominally fixed-width but in practice varies:

1. **Whitespace**: Tabs and spaces are mixed. Solution: use `str.split()` (whitespace-agnostic) as the primary tokenizer, with positional fallback for edge cases.

2. **Parameter block**: Keys like `PR1=`, `FRIC=` may appear on the same line or different lines. Solution: concatenate all parameter lines, then extract with regex `r'(\w+)\s*=\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)'`.

3. **Section transitions**: The transition from source faults to receiver faults is signaled by a blank line followed by another column header. Solution: track blank lines and column header patterns in the state machine.

4. **Fault labels**: Optional trailing text after the 11th numeric field. Solution: after extracting 11 numeric tokens, join remaining tokens as the label.

5. **Scientific notation**: `0.800000E+06`. Solution: Python's `float()` handles this natively.

### 5.2 `.inp` Writer (`io/inp_writer.py`, Tier 2)

```python
"""Coulomb .inp file writer."""

from pathlib import Path
from opencoulomb.types import CoulombModel


def write_inp(model: CoulombModel, path: str | Path) -> None:
    """Write a CoulombModel to a Coulomb 3.4 .inp file.

    The output must round-trip: read_inp(write_inp(model)) == model.
    Uses the exact fixed-width format expected by Coulomb 3.4.
    """
    ...
```

### 5.3 Output Writers

#### 5.3.1 `.cou` Writer (`io/cou_writer.py`)

```python
"""Coulomb .cou output file writer."""

from pathlib import Path
from opencoulomb.types import CoulombResult, CoulombModel, CrossSectionResult


def write_dcff_cou(
    result: CoulombResult,
    model: CoulombModel,
    path: str | Path,
) -> None:
    """Write dcff.cou -- Coulomb stress grid file.

    Format: header + one line per grid point with columns:
    X(km) Y(km) CFS(bar) Shear(bar) Normal(bar) Sxx Syy Szz Syz Sxz Sxy
    """
    ...


def write_dcff_section_cou(
    result: CrossSectionResult,
    model: CoulombModel,
    path: str | Path,
) -> None:
    """Write dcff_section.cou -- cross-section stress data.

    Same columns as dcff.cou but col1=distance, col2=depth.
    """
    ...
```

#### 5.3.2 CSV Writer (`io/csv_writer.py`)

```python
"""CSV output writer."""

from pathlib import Path
from opencoulomb.types import CoulombResult


def write_csv(result: CoulombResult, path: str | Path) -> None:
    """Write computation results to CSV.

    Header row with column names, then one data row per grid point.
    Columns: x_km, y_km, cfs_bar, shear_bar, normal_bar,
             sxx_bar, syy_bar, szz_bar, syz_bar, sxz_bar, sxy_bar,
             ux_m, uy_m, uz_m
    """
    ...
```

#### 5.3.3 DAT Writers (`io/dat_writer.py`)

```python
"""Coulomb .dat output file writers."""

from pathlib import Path
from opencoulomb.types import CoulombResult, CoulombModel


def write_coulomb_out_dat(
    result: CoulombResult, model: CoulombModel, path: str | Path,
) -> None:
    """Write coulomb_out.dat -- primary grid output matrix."""
    ...


def write_gmt_fault_surface(
    model: CoulombModel, path: str | Path,
) -> None:
    """Write gmt_fault_surface.dat -- GMT multi-segment fault traces.

    Format: '>' separator, then corner coordinates for each fault polygon.
    """
    ...
```

### 5.4 Format Registry (`io/formats.py`)

```python
"""File format registry for extensible I/O."""

from pathlib import Path
from typing import Callable, Any

# Registry mapping file extensions to reader/writer functions
_READERS: dict[str, Callable] = {}
_WRITERS: dict[str, Callable] = {}


def register_reader(extension: str, reader: Callable) -> None:
    """Register a file reader for a given extension."""
    _READERS[extension.lower()] = reader


def register_writer(extension: str, writer: Callable) -> None:
    """Register a file writer for a given extension."""
    _WRITERS[extension.lower()] = writer


def detect_format(path: str | Path) -> str:
    """Auto-detect file format from extension."""
    return Path(path).suffix.lower()


def get_reader(extension: str) -> Callable:
    """Get the registered reader for a file extension."""
    ext = extension.lower()
    if ext not in _READERS:
        raise FormatError(f"No reader registered for '{ext}'")
    return _READERS[ext]


def get_writer(extension: str) -> Callable:
    """Get the registered writer for a file extension."""
    ext = extension.lower()
    if ext not in _WRITERS:
        raise FormatError(f"No writer registered for '{ext}'")
    return _WRITERS[ext]


# Auto-register built-in formats on import
def _register_builtins() -> None:
    from opencoulomb.io.inp_parser import read_inp
    from opencoulomb.io.cou_writer import write_dcff_cou
    from opencoulomb.io.csv_writer import write_csv
    register_reader('.inp', read_inp)
    register_writer('.cou', write_dcff_cou)
    register_writer('.csv', write_csv)

_register_builtins()
```

---

## 6. Visualization Architecture

### 6.1 Design Principles

1. **Separation of data and presentation**: Plotting functions receive `CoulombResult` / `CrossSectionResult` objects, not raw arrays. They never call computation functions.
2. **Reusable components**: Every plot function returns a `matplotlib.figure.Figure` object that can be displayed, saved, or embedded in a GUI panel.
3. **Consistent styling**: A central `styles.py` module manages Matplotlib rcParams and provides presets (default, publication, presentation).
4. **Colormap convention**: Diverging colormap centered on zero. Red/warm = positive CFS (promotes failure). Blue/cool = negative CFS (stress shadow).

### 6.2 Module Structure

#### 6.2.1 Color and Style Configuration (`viz/colormaps.py`, `viz/styles.py`)

```python
# viz/colormaps.py
"""Colormap configuration for Coulomb stress plots."""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

# Default colormap: try cmcrameri 'vik', fallback to RdBu_r
def get_default_cmap() -> mcolors.Colormap:
    """Get the default diverging colormap."""
    try:
        import cmcrameri.cm as cmc
        return cmc.vik
    except ImportError:
        return plt.cm.RdBu_r


def make_symmetric_norm(
    vmin: float | None, vmax: float | None, data: "NDArray | None" = None,
) -> mcolors.TwoSlopeNorm:
    """Create a symmetric diverging normalization centered on zero.

    If vmin/vmax not specified, uses max(abs(data)) for symmetric range.
    """
    ...
```

```python
# viz/styles.py
"""Matplotlib style presets."""

import matplotlib as mpl

STYLE_DEFAULT: dict = {
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'figure.dpi': 100,
    'savefig.dpi': 300,
    'figure.figsize': (10, 8),
}

STYLE_PUBLICATION: dict = {
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 8,
    'axes.labelsize': 9,
    'axes.titlesize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 600,
    'figure.figsize': (7, 5.5),
    'lines.linewidth': 0.8,
}

STYLE_PRESENTATION: dict = {
    'font.size': 14,
    'axes.labelsize': 16,
    'axes.titlesize': 18,
    'figure.dpi': 150,
    'figure.figsize': (12, 9),
}


def apply_style(preset: str = "default") -> None:
    """Apply a named style preset to Matplotlib."""
    styles = {
        'default': STYLE_DEFAULT,
        'publication': STYLE_PUBLICATION,
        'presentation': STYLE_PRESENTATION,
    }
    mpl.rcParams.update(styles.get(preset, STYLE_DEFAULT))
```

#### 6.2.2 CFS Map Plot (`viz/maps.py`)

```python
"""2D stress/displacement map plotting."""

import matplotlib.pyplot as plt
import matplotlib.figure
import numpy as np
from numpy.typing import NDArray

from opencoulomb.types import CoulombResult, CoulombModel


def plot_cfs_map(
    result: CoulombResult,
    model: CoulombModel | None = None,
    field: str = "cfs",
    clim: tuple[float, float] | None = None,
    cmap: str | None = None,
    symmetric: bool = True,
    title: str | None = None,
    show_faults: bool = True,
    show_colorbar: bool = True,
    figsize: tuple[float, float] | None = None,
    ax: "plt.Axes | None" = None,
) -> matplotlib.figure.Figure:
    """Plot a 2D color-filled contour map of CFS or other fields.

    Parameters
    ----------
    result : CoulombResult
        Computation results.
    model : CoulombModel, optional
        Model for fault trace overlay. Required if show_faults=True.
    field : str
        Field to plot: 'cfs', 'shear', 'normal', 'sxx', 'syy', 'szz',
        'syz', 'sxz', 'sxy', 'ux', 'uy', 'uz', 'umag', 'dilatation'.
    clim : (float, float), optional
        Color scale limits. Auto-computed if None.
    cmap : str, optional
        Colormap name. Uses default diverging if None.
    symmetric : bool
        Force symmetric color scale around zero.
    title : str, optional
        Figure title. Auto-generated if None.
    show_faults : bool
        Overlay fault traces on the map.
    show_colorbar : bool
        Show the color bar.
    figsize : (float, float), optional
        Figure size in inches.
    ax : plt.Axes, optional
        Existing axes to plot on. If None, creates a new figure.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The figure object. Can be saved with fig.savefig().
    """
    ...
```

#### 6.2.3 Fault Trace Rendering (`viz/faults.py`)

```python
"""Fault trace rendering on map plots."""

import matplotlib.pyplot as plt
from opencoulomb.types import FaultElement


def draw_fault_traces(
    ax: plt.Axes,
    faults: list[FaultElement],
    n_fixed: int,
    source_color: str = "black",
    source_linewidth: float = 2.0,
    receiver_color: str = "gray",
    receiver_linewidth: float = 1.0,
    receiver_linestyle: str = "--",
    show_labels: bool = False,
) -> None:
    """Draw fault traces on a Matplotlib axes.

    Source faults (indices < n_fixed): solid lines.
    Receiver faults (indices >= n_fixed): dashed lines.
    """
    ...
```

#### 6.2.4 Cross-Section Plot (`viz/sections.py`)

```python
"""Cross-section visualization."""

import matplotlib.figure
from opencoulomb.types import CrossSectionResult, CoulombModel


def plot_section(
    result: CrossSectionResult,
    model: CoulombModel | None = None,
    field: str = "cfs",
    clim: tuple[float, float] | None = None,
    cmap: str | None = None,
    title: str | None = None,
    show_faults: bool = True,
    figsize: tuple[float, float] | None = None,
) -> matplotlib.figure.Figure:
    """Plot a vertical cross-section of stress/displacement.

    X-axis: distance along profile (km).
    Y-axis: depth (km, positive downward, inverted axis).
    Color fill: selected field value.
    """
    ...
```

#### 6.2.5 Displacement Vectors (`viz/displacement.py`)

```python
"""Displacement vector (quiver) plots."""

import matplotlib.figure
from opencoulomb.types import CoulombResult


def plot_displacement(
    result: CoulombResult,
    component: str = "horizontal",
    scale: float | None = None,
    figsize: tuple[float, float] | None = None,
) -> matplotlib.figure.Figure:
    """Plot displacement vectors as a quiver plot.

    component: 'horizontal' (East+North arrows), 'vertical' (Up color fill),
               'all' (horizontal arrows + vertical color fill).
    """
    ...
```

#### 6.2.6 Figure Export (`viz/export.py`)

```python
"""Figure export utilities."""

from pathlib import Path
import matplotlib.figure


def save_figure(
    fig: matplotlib.figure.Figure,
    path: str | Path,
    dpi: int = 300,
    transparent: bool = False,
) -> None:
    """Save a figure to file. Format auto-detected from extension.

    Supports: .png, .pdf, .svg, .eps
    For PDF/SVG: text rendered as vector, lines as paths.
    """
    fmt = Path(path).suffix.lstrip('.')
    fig.savefig(path, format=fmt, dpi=dpi, bbox_inches='tight',
                transparent=transparent)


def create_multi_panel(
    figures: list[matplotlib.figure.Figure],
    layout: tuple[int, int] = (1, 2),
    figsize: tuple[float, float] | None = None,
) -> matplotlib.figure.Figure:
    """Combine multiple figures into a multi-panel layout.

    Used for publication figures: map + cross-section side by side.
    """
    ...
```

### 6.3 GUI Integration Strategy

All `viz/` functions accept an optional `ax` parameter (Matplotlib Axes). When called from the GUI, the GUI creates a `FigureCanvasQTAgg` widget, extracts its axes, and passes it to the plotting function. This ensures the same plotting code works in both CLI/script and GUI contexts:

```python
# In CLI/script:
fig = plot_cfs_map(result, model)
fig.savefig("output.pdf")

# In GUI (PyQt6):
canvas = FigureCanvasQTAgg(Figure())
ax = canvas.figure.add_subplot(111)
plot_cfs_map(result, model, ax=ax)
canvas.draw()
```

---

## 7. CLI Architecture

### 7.1 Command Structure

The CLI uses Click's command group pattern with a top-level `opencoulomb` group.

```python
# cli/main.py
"""OpenCoulomb CLI entry point."""

import click
import logging

from opencoulomb import __version__


@click.group()
@click.version_option(__version__, prog_name="opencoulomb")
@click.option('-v', '--verbose', count=True,
              help="Increase verbosity (-v, -vv).")
@click.option('-q', '--quiet', is_flag=True,
              help="Suppress non-error output.")
@click.option('--config', type=click.Path(exists=True),
              help="Configuration file (TOML).")
@click.option('--output-dir', type=click.Path(),
              default='./opencoulomb_output/',
              help="Output directory.")
@click.pass_context
def cli(ctx: click.Context, verbose: int, quiet: bool,
        config: str | None, output_dir: str) -> None:
    """OpenCoulomb: Coulomb failure stress computation."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['quiet'] = quiet
    ctx.obj['output_dir'] = output_dir
    _setup_logging(verbose, quiet)
    if config:
        ctx.obj['config'] = _load_config(config)
```

### 7.2 Command Implementations

```python
# cli/compute.py
"""The 'compute' command."""

import click
from pathlib import Path


@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Choice(
    ['cfs', 'displacement', 'strain', 'stress', 'all']), default='cfs')
@click.option('--receiver', type=click.Choice(['specified', 'oops']),
              default='specified')
@click.option('--depth', type=float, help="Override depth (km).")
@click.option('--friction', type=float, help="Override friction.")
@click.option('--poisson', type=float, help="Override Poisson's ratio.")
@click.option('--young', type=float, help="Override Young's modulus (bar).")
@click.option('--grid-start', nargs=2, type=float, help="Grid start X Y (km).")
@click.option('--grid-end', nargs=2, type=float, help="Grid end X Y (km).")
@click.option('--grid-spacing', nargs=2, type=float, help="Grid spacing DX DY (km).")
@click.option('--format', 'output_format',
              type=click.Choice(['coulomb', 'csv', 'text']), default='coulomb')
@click.option('--plot', type=click.Choice(
    ['map', 'section', 'displacement', 'all', 'none']), default='none')
@click.option('--section', nargs=4, type=float, help="Cross-section: X1 Y1 X2 Y2.")
@click.option('--section-depth', nargs=2, type=float, help="Section depth range: MIN MAX.")
@click.option('--section-spacing', type=float, help="Section vertical spacing (km).")
@click.pass_context
def compute(ctx: click.Context, input_file: str, output: str,
            receiver: str, depth: float | None, friction: float | None,
            poisson: float | None, young: float | None,
            grid_start: tuple | None, grid_end: tuple | None,
            grid_spacing: tuple | None, output_format: str,
            plot: str, section: tuple | None,
            section_depth: tuple | None,
            section_spacing: float | None) -> None:
    """Run stress/displacement computation from .inp file."""
    from opencoulomb.io import read_inp
    from opencoulomb.core import compute_grid
    from opencoulomb.io import write_dcff_cou, write_csv

    # 1. Parse input
    model = read_inp(input_file)

    # 2. Apply CLI overrides
    model = _apply_overrides(model, depth=depth, friction=friction,
                              poisson=poisson, young=young,
                              grid_start=grid_start, grid_end=grid_end,
                              grid_spacing=grid_spacing)

    # 3. Compute
    click.echo(f"Computing {output} for {Path(input_file).name}...")
    result = compute_grid(model)

    # 4. Write output
    out_dir = Path(ctx.obj['output_dir'])
    out_dir.mkdir(parents=True, exist_ok=True)
    if output_format == 'coulomb':
        write_dcff_cou(result, model, out_dir / 'dcff.cou')
    elif output_format == 'csv':
        write_csv(result, out_dir / 'results.csv')

    # 5. Optional plot
    if plot != 'none':
        from opencoulomb.viz import plot_cfs_map, save_figure
        fig = plot_cfs_map(result, model)
        save_figure(fig, out_dir / f'cfs_map.png')
        click.echo(f"Plot saved to {out_dir / 'cfs_map.png'}")

    click.echo("Done.")
```

```python
# cli/info.py
@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--json', 'as_json', is_flag=True, help="Output as JSON.")
def info(input_file: str, as_json: bool) -> None:
    """Inspect and summarize a .inp file."""
    ...

# cli/validate.py
@click.command()
@click.argument('input_file', type=click.Path(exists=True))
def validate(input_file: str) -> None:
    """Check .inp file for errors without computing."""
    ...

# cli/convert.py
@click.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
@click.option('--from', 'from_fmt', help="Source format.")
@click.option('--to', 'to_fmt', help="Target format.")
def convert(input_path: str, output_path: str,
            from_fmt: str | None, to_fmt: str | None) -> None:
    """Convert between file formats."""
    ...

# cli/plot.py
@click.command()
@click.argument('result_file', type=click.Path(exists=True))
@click.option('--type', 'plot_type',
              type=click.Choice(['map', 'section', 'displacement', '3d']))
@click.option('--field', type=str, default='cfs')
@click.option('--clim', nargs=2, type=float, help="Color limits: MIN MAX.")
@click.option('--cmap', type=str, help="Colormap name.")
@click.option('--faults', type=click.Path(exists=True),
              help="Overlay fault traces from .inp file.")
@click.option('--format', 'export_format', default='png')
@click.option('--output', '-o', type=click.Path())
@click.option('--dpi', type=int, default=300)
@click.option('--figsize', nargs=2, type=float, help="Figure size: W H inches.")
def plot(result_file: str, plot_type: str, field: str, **kwargs) -> None:
    """Generate visualizations from computation results."""
    ...
```

### 7.3 Configuration File Support

```toml
# opencoulomb.toml -- optional user configuration

[defaults]
friction = 0.4
poisson = 0.25
young = 800000.0
depth = 10.0

[output]
format = "coulomb"         # coulomb, csv, text
directory = "./opencoulomb_output/"

[plot]
cmap = "vik"
dpi = 300
figsize = [10, 8]
style = "default"          # default, publication, presentation

[logging]
level = "WARNING"          # DEBUG, INFO, WARNING, ERROR
```

### 7.4 Logging and Progress

```python
# cli/_logging.py
"""Logging configuration."""

import logging
import sys


def setup_logging(verbosity: int, quiet: bool) -> None:
    """Configure logging based on CLI verbosity flags.

    -q:   ERROR only
    (none): WARNING
    -v:   INFO
    -vv:  DEBUG
    """
    if quiet:
        level = logging.ERROR
    elif verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        stream=sys.stderr,
    )


def get_progress_bar(total: int, label: str = "Computing"):
    """Get a Click progress bar for long computations."""
    import click
    return click.progressbar(length=total, label=label)
```

### 7.5 Entry Points

In `pyproject.toml`:

```toml
[project.scripts]
opencoulomb = "opencoulomb.cli.main:cli"
```

Also supports `python -m opencoulomb` via `__main__.py`:

```python
# __main__.py
from opencoulomb.cli.main import cli
cli()
```

---

## 8. Error Handling Strategy

### 8.1 Exception Hierarchy

The full hierarchy is defined in `opencoulomb/exceptions.py` (see Section 2.2.3). The design follows these principles:

1. **All OpenCoulomb exceptions inherit from `OpenCoulombError`**, enabling blanket catch if needed.
2. **Specific subclasses for each error category**: `ParseError`, `ValidationError`, `SingularityError`, `ConvergenceError`, `FormatError`, `ConfigError`.
3. **Context in exceptions**: `ParseError` carries `filename` and `line_number`. All exceptions produce human-readable messages.

### 8.2 Validation Boundaries

Validation occurs at three boundaries:

```
                    +---------------------------+
  User input        |  BOUNDARY 1: CLI/API      |
  (.inp file,       |  - File exists?            |
   CLI args,        |  - Args in valid range?    |
   Python API)      |  - Format recognized?      |
                    +-------------+-------------+
                                  |
                    +-------------v-------------+
  Parsed model      |  BOUNDARY 2: Data Model   |
                    |  - __post_init__ checks    |
                    |  - Poisson in (0, 0.5)?    |
                    |  - Dip in [0, 90]?         |
                    |  - Depths consistent?      |
                    |  - Grid dimensions valid?  |
                    +-------------+-------------+
                                  |
                    +-------------v-------------+
  During compute    |  BOUNDARY 3: Computation   |
                    |  - NaN/Inf detection       |
                    |  - Singularity guards      |
                    |  - Convergence checks      |
                    +---------------------------+
```

#### Boundary 1: Input Validation

```python
# In cli/compute.py:
@click.command()
def compute(input_file, friction, ...):
    # Click validates types automatically (float, Path exists, etc.)
    # Additional semantic validation:
    if friction is not None and friction < 0:
        raise click.BadParameter("Friction must be non-negative")
```

#### Boundary 2: Data Model Validation

Every dataclass validates in `__post_init__`:

```python
@dataclass(frozen=True, slots=True)
class GridSpec:
    ...
    def __post_init__(self):
        if self.finish_x <= self.start_x:
            raise ValidationError("finish_x must exceed start_x")
        # etc.
```

#### Boundary 3: Numerical Guards

```python
# In core/pipeline.py after computing each fault:
def _check_numerical_health(arrays: dict[str, NDArray]) -> None:
    """Detect NaN/Inf in computation results."""
    for name, arr in arrays.items():
        n_nan = np.count_nonzero(np.isnan(arr))
        n_inf = np.count_nonzero(np.isinf(arr))
        if n_nan > 0 or n_inf > 0:
            import warnings
            warnings.warn(
                f"Numerical issue in {name}: {n_nan} NaN, {n_inf} Inf "
                f"out of {arr.size} values. These may indicate "
                f"observation points near fault singularities.",
                stacklevel=2,
            )
            # Replace NaN/Inf with 0.0 (matching Coulomb 3.4 behavior)
            arr[~np.isfinite(arr)] = 0.0
```

### 8.3 Error Reporting

- **CLI**: Errors print to stderr with context. `ParseError` includes filename and line number. Exit code 1 for errors, 2 for warnings-only.
- **Python API**: Exceptions propagate normally. Users can catch `OpenCoulombError` for any OpenCoulomb issue.
- **GUI** (Tier 2): Errors display in a message dialog. Computations run in a worker thread; errors are sent back to the main thread via a Qt signal.

---

## 9. Testing Architecture

### 9.1 Directory Structure

```
tests/
    __init__.py
    conftest.py                     # Shared fixtures, paths, helpers

    unit/                           # Fast, isolated tests
        __init__.py
        test_okada.py               # DC3D/DC3D0 against reference values
        test_stress.py              # Hooke's law, tensor rotation
        test_coulomb.py             # CFS, Bond matrix, stress resolution
        test_coordinates.py         # Coordinate transforms
        test_oops.py                # Optimally oriented planes
        test_pipeline.py            # Pipeline orchestrator (mocked I/O)
        test_types.py               # Data model validation

    integration/                    # Multi-module, real I/O
        __init__.py
        test_inp_parsing.py         # Parser on all example .inp files
        test_output_formats.py      # Round-trip: parse -> compute -> write
        test_full_pipeline.py       # End-to-end: .inp -> CoulombResult -> .cou
        test_cli.py                 # CLI commands via Click's CliRunner

    validation/                     # Numerical accuracy against references
        __init__.py
        test_vs_coulomb34.py        # Compare output against Coulomb 3.4
        test_vs_elastic_stresses.py # Cross-validate with elastic_stresses_py
        test_published_results.py   # Reproduce King+Stein 1994, etc.

    performance/                    # Performance regression tests
        __init__.py
        test_benchmarks.py          # Timing tests with pytest-benchmark

    fixtures/                       # Test data
        inp_files/                  # Example .inp files
            landers.inp
            northridge.inp
            ...                     # All ~20 from coulomb3402.zip
        reference_outputs/          # Coulomb 3.4 reference outputs
            landers_dcff.cou
            landers_displacement.cou
            ...
        okada_reference/            # DC3D reference values
            dc3d_test_cases.json    # Input/output pairs from Fortran
```

### 9.2 Fixtures (`conftest.py`)

```python
"""Shared test fixtures."""

import pytest
import numpy as np
from pathlib import Path

from opencoulomb.types import (
    MaterialProperties, FaultElement, Kode, GridSpec,
    CoulombModel, RegionalStress, PrincipalStress,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
INP_DIR = FIXTURES_DIR / "inp_files"
REF_DIR = FIXTURES_DIR / "reference_outputs"
OKADA_DIR = FIXTURES_DIR / "okada_reference"


@pytest.fixture
def default_material() -> MaterialProperties:
    """Default material properties (Coulomb 3.4 defaults)."""
    return MaterialProperties(
        poisson=0.25, young=8.0e5, friction=0.4, depth=10.0
    )


@pytest.fixture
def simple_fault() -> FaultElement:
    """A simple vertical strike-slip fault for testing."""
    return FaultElement(
        x_start=-10.0, y_start=0.0,
        x_fin=10.0, y_fin=0.0,
        kode=Kode.STANDARD,
        slip_1=1.0, slip_2=0.0,   # 1 m right-lateral
        dip=90.0,
        top_depth=0.0, bottom_depth=15.0,
        label="Test fault",
        element_index=1,
    )


@pytest.fixture
def simple_grid() -> GridSpec:
    """A 21x21 grid for testing."""
    return GridSpec(
        start_x=-50.0, start_y=-50.0,
        finish_x=50.0, finish_y=50.0,
        x_inc=5.0, y_inc=5.0,
        depth=10.0,
    )


@pytest.fixture
def simple_model(default_material, simple_fault, simple_grid) -> CoulombModel:
    """A minimal model with one fault and a grid."""
    return CoulombModel(
        title="Test model",
        material=default_material,
        faults=[simple_fault],
        grid=simple_grid,
        n_fixed=1,
    )


@pytest.fixture
def all_inp_files() -> list[Path]:
    """All example .inp files from Coulomb 3.4."""
    return sorted(INP_DIR.glob("*.inp"))


@pytest.fixture
def dc3d_reference_cases() -> list[dict]:
    """Reference input/output pairs for DC3D from Fortran."""
    import json
    with open(OKADA_DIR / "dc3d_test_cases.json") as f:
        return json.load(f)
```

### 9.3 Unit Test Examples

#### 9.3.1 Okada DC3D Tests (`test_okada.py`)

```python
"""Tests for the Okada DC3D implementation."""

import numpy as np
import numpy.testing as npt
import pytest

from opencoulomb.core.okada import dc3d, dc3d0


class TestDC3D:
    """Test DC3D against Fortran reference values."""

    def test_strike_slip_surface(self, dc3d_reference_cases):
        """Verify displacement for a surface-breaking strike-slip fault."""
        case = dc3d_reference_cases[0]  # Pre-defined reference case
        result = dc3d(
            alpha=case['alpha'], x=case['x'], y=case['y'], z=case['z'],
            depth=case['depth'], dip=case['dip'],
            al1=case['al1'], al2=case['al2'],
            aw1=case['aw1'], aw2=case['aw2'],
            disl1=case['disl1'], disl2=case['disl2'], disl3=case['disl3'],
        )
        ux, uy, uz = result[0], result[1], result[2]
        npt.assert_allclose(ux, case['ux'], rtol=1e-10)
        npt.assert_allclose(uy, case['uy'], rtol=1e-10)
        npt.assert_allclose(uz, case['uz'], rtol=1e-10)

    def test_vectorized_matches_scalar(self):
        """Vectorized call produces same results as N scalar calls."""
        alpha = 2.0 / 3.0
        N = 100
        x = np.linspace(-50, 50, N)
        y = np.zeros(N)
        z = np.full(N, -10.0)

        # Vectorized call
        vec_result = dc3d(alpha, x, y, z, 10.0, 90.0,
                          -10.0, 10.0, -7.5, 7.5, 1.0, 0.0, 0.0)

        # Scalar calls
        for i in range(N):
            scalar_result = dc3d(alpha, x[i], y[i], z[i], 10.0, 90.0,
                                  -10.0, 10.0, -7.5, 7.5, 1.0, 0.0, 0.0)
            for j in range(12):
                npt.assert_allclose(
                    np.atleast_1d(vec_result[j])[i],
                    np.atleast_1d(scalar_result[j])[0],
                    rtol=1e-14,
                    err_msg=f"Mismatch at point {i}, component {j}")

    def test_singularity_on_fault_edge(self):
        """No NaN/Inf when observation point is on fault edge."""
        alpha = 2.0 / 3.0
        result = dc3d(alpha, 0.0, 0.0, 0.0, 10.0, 90.0,
                      -10.0, 10.0, -7.5, 7.5, 1.0, 0.0, 0.0)
        for component in result:
            arr = np.atleast_1d(component)
            assert np.all(np.isfinite(arr)), "NaN/Inf at fault edge"

    @pytest.mark.parametrize("dip", [0.1, 30.0, 45.0, 60.0, 89.9])
    def test_various_dip_angles(self, dip):
        """DC3D produces finite results for various dip angles."""
        alpha = 2.0 / 3.0
        x = np.array([0.0, 10.0, -10.0, 0.0, 0.0])
        y = np.array([0.0, 0.0, 0.0, 10.0, -10.0])
        z = np.full(5, -5.0)
        result = dc3d(alpha, x, y, z, 10.0, dip,
                      -10.0, 10.0, -7.5, 7.5, 1.0, 0.0, 0.0)
        for component in result:
            assert np.all(np.isfinite(component))


class TestDC3D0:
    """Test DC3D0 point source."""

    def test_point_source_reference(self, dc3d_reference_cases):
        """Verify DC3D0 against Fortran reference values."""
        # Filter for point source cases
        ps_cases = [c for c in dc3d_reference_cases if c['type'] == 'point']
        for case in ps_cases:
            result = dc3d0(
                alpha=case['alpha'], x=case['x'], y=case['y'], z=case['z'],
                depth=case['depth'], dip=case['dip'],
                pot1=case['pot1'], pot2=case['pot2'],
                pot3=case['pot3'], pot4=case['pot4'],
            )
            npt.assert_allclose(result[0], case['ux'], rtol=1e-10)
```

### 9.4 Validation Tests

```python
# test_vs_coulomb34.py
"""Validate OpenCoulomb output against Coulomb 3.4 reference outputs."""

import numpy as np
import numpy.testing as npt
import pytest
from pathlib import Path

from opencoulomb.io import read_inp
from opencoulomb.core import compute_grid


@pytest.fixture(params=[
    ("landers.inp", "landers_dcff.cou"),
    ("northridge.inp", "northridge_dcff.cou"),
    # ... all example files
])
def inp_and_reference(request, all_inp_files):
    inp_name, ref_name = request.param
    inp_path = INP_DIR / inp_name
    ref_path = REF_DIR / ref_name
    if not inp_path.exists() or not ref_path.exists():
        pytest.skip(f"Missing fixture: {inp_name} or {ref_name}")
    return inp_path, ref_path


def test_cfs_matches_coulomb34(inp_and_reference):
    """CFS values match Coulomb 3.4 output to < 1e-6 bar."""
    inp_path, ref_path = inp_and_reference

    # Compute with OpenCoulomb
    model = read_inp(inp_path)
    result = compute_grid(model)

    # Load Coulomb 3.4 reference
    ref_data = np.loadtxt(ref_path, skiprows=2)
    ref_cfs = ref_data[:, 2]  # Column 3 = CFS

    npt.assert_allclose(
        result.cfs, ref_cfs,
        atol=1e-6,  # bar
        err_msg=f"CFS mismatch for {inp_path.name}"
    )
```

### 9.5 Property-Based Testing

```python
# In test_coordinates.py:
"""Property-based tests for coordinate transforms."""

from hypothesis import given, strategies as st
import numpy as np
from opencoulomb.core.coordinates import geo_to_fault, fault_to_geo


@given(
    strike=st.floats(0, 360),
    x=st.floats(-100, 100),
    y=st.floats(-100, 100),
)
def test_rotation_roundtrip(strike, x, y):
    """Rotating to fault-local and back yields original coordinates."""
    strike_rad = np.radians(strike)
    # Forward: geo -> fault displacement
    ux_f, uy_f, uz_f = fault_to_geo(
        np.array([x]), np.array([y]), np.array([0.0]), strike_rad)
    # The inverse rotation should recover (x, y)
    # ... (test the actual roundtrip property)
```

### 9.6 Performance Tests

```python
# test_benchmarks.py
"""Performance regression tests."""

import pytest
import numpy as np
from opencoulomb.core.okada import dc3d


@pytest.mark.benchmark
def test_dc3d_10k_points(benchmark):
    """Benchmark DC3D on 10,000 observation points."""
    N = 10_000
    x = np.random.uniform(-50, 50, N)
    y = np.random.uniform(-50, 50, N)
    z = np.full(N, -10.0)

    result = benchmark(
        dc3d, 2.0/3.0, x, y, z,
        10.0, 90.0, -10.0, 10.0, -7.5, 7.5,
        1.0, 0.0, 0.0,
    )
    assert result is not None


@pytest.mark.benchmark
def test_full_pipeline_100x100(benchmark, simple_model):
    """Benchmark full pipeline on a 100x100 grid."""
    from opencoulomb.core import compute_grid

    # Modify grid to 100x100
    model = simple_model  # Adjust grid_spec as needed
    result = benchmark(compute_grid, model)
    assert result.cfs.shape[0] > 0
```

---

## 10. Extension Points

### 10.1 Plugin Architecture (Tier 3)

OpenCoulomb supports extension through a plugin system based on Python entry points. Plugins can add new source types, output formats, and visualization types.

#### 10.1.1 Entry Point Groups

```toml
# In a plugin's pyproject.toml:
[project.entry-points."opencoulomb.io.readers"]
srcmod = "opencoulomb_srcmod:read_srcmod"

[project.entry-points."opencoulomb.io.writers"]
kml = "opencoulomb_kml:write_kml"

[project.entry-points."opencoulomb.sources"]
mogi = "opencoulomb_mogi:compute_mogi"

[project.entry-points."opencoulomb.viz"]
gmt = "opencoulomb_gmt:plot_gmt"
```

#### 10.1.2 Plugin Discovery

```python
# In opencoulomb/plugins.py (Tier 3)
"""Plugin discovery and registration."""

import importlib.metadata


def discover_plugins() -> dict[str, list]:
    """Discover installed plugins via entry points."""
    plugins = {}
    for group in ['opencoulomb.io.readers', 'opencoulomb.io.writers',
                  'opencoulomb.sources', 'opencoulomb.viz']:
        eps = importlib.metadata.entry_points(group=group)
        plugins[group] = [
            {'name': ep.name, 'loader': ep.load}
            for ep in eps
        ]
    return plugins


def register_plugins() -> None:
    """Load and register all discovered plugins."""
    from opencoulomb.io.formats import register_reader, register_writer
    plugins = discover_plugins()
    for ep_info in plugins.get('opencoulomb.io.readers', []):
        register_reader(f'.{ep_info["name"]}', ep_info['loader']())
    for ep_info in plugins.get('opencoulomb.io.writers', []):
        register_writer(f'.{ep_info["name"]}', ep_info['loader']())
```

### 10.2 Adding New Source Types

To add a new dislocation source type (e.g., Mogi point source, triangular elements):

1. **Create a new computation function** with the same signature pattern as `dc3d()`:
   ```python
   def compute_mogi(x, y, z, source_x, source_y, source_depth, volume_change, ...):
       """Mogi (1958) point source inflation/deflation."""
       # Returns: (ux, uy, uz, uxx, uyx, uzx, ...)
   ```

2. **Register it** in the KODE dispatch or as a new entry point.

3. **Extend `FaultElement`** (or create a new dataclass) for the new source parameters.

### 10.3 Adding New Output Formats

1. **Write a writer function** following the pattern in `io/csv_writer.py`:
   ```python
   def write_netcdf(result: CoulombResult, path: Path) -> None:
       """Write results to NetCDF format."""
       ...
   ```

2. **Register** via `register_writer('.nc', write_netcdf)` or as an entry point.

3. The format is then available to the CLI via `--format netcdf` and to the convert command.

### 10.4 Adding New Visualization Types

1. **Create a plotting function** in `viz/` following the pattern:
   ```python
   def plot_seismicity_overlay(
       result: CoulombResult,
       catalog: EarthquakeCatalog,
       ax: plt.Axes | None = None,
   ) -> matplotlib.figure.Figure:
       ...
   ```

2. **Integrate with CLI** by adding a new `--type` option to the `plot` command.

---

## 11. Performance Considerations

### 11.1 Vectorization Strategy

The performance-critical path is the Okada DC3D computation, called for every combination of grid point and source fault. The vectorization approach eliminates the inner loop (over grid points) by using NumPy array operations:

```
Performance model:
  T = N_faults * T_dc3d(N_points)

  Where T_dc3d(N) is the time for one vectorized DC3D call over N points.

  For pure NumPy:
    T_dc3d(10,000)  ~= 5 ms      (estimated)
    T_dc3d(100,000) ~= 50 ms     (estimated)

  For 100x100 grid (10,000 points) with 10 faults:
    T ~= 10 * 5 ms = 50 ms       (well under 10 second budget)

  For 200x200 grid (40,000 points) with 50 faults:
    T ~= 50 * 20 ms = 1,000 ms   (well under 120 second budget)
```

### 11.2 Memory Layout

All grid arrays use C-contiguous (row-major) layout, which is NumPy's default:

```python
# Grids are stored as 1-D arrays during computation for vectorization
grid_x = np.ascontiguousarray(xx.ravel())  # shape (N,), C-contiguous

# Reshaping to 2D for output/plotting:
cfs_2d = cfs.reshape(n_y, n_x)  # (n_y, n_x) for row=y convention
```

The `indexing='ij'` in `np.meshgrid` ensures the y-axis varies along rows (axis 0) and x-axis along columns (axis 1), matching Matplotlib's `imshow`/`contourf` conventions.

### 11.3 Parallelism Opportunities

#### 11.3.1 Multi-Fault Parallelism (Tier 3)

Since fault contributions are independent (superposition), the fault loop can be parallelized:

```python
from concurrent.futures import ProcessPoolExecutor

def _compute_fault_contribution(args):
    """Compute one fault's stress contribution (for multiprocessing)."""
    fault, grid_x, grid_y, grid_z, material = args
    # ... returns stress arrays
    return sxx, syy, szz, syz, sxz, sxy, ux, uy, uz

# In compute_grid():
if n_faults > 4 and n_points > 10000:  # Only parallelize if worthwhile
    with ProcessPoolExecutor(max_workers=min(n_faults, os.cpu_count())) as pool:
        results = pool.map(_compute_fault_contribution,
                           [(f, grid_x, grid_y, grid_z, material)
                            for f in source_faults])
    for sxx, syy, ... in results:
        total_sxx += sxx
        # ...
```

#### 11.3.2 Batch Parallelism (Tier 3)

Multiple input files are completely independent and can be processed in parallel:

```python
# In cli/batch.py:
from multiprocessing import Pool

def process_batch(inp_files: list[Path], n_workers: int = 4):
    with Pool(n_workers) as pool:
        results = pool.map(_process_single_file, inp_files)
    return results
```

#### 11.3.3 GUI Threading (Tier 2)

Computations run in a background QThread to keep the GUI responsive:

```python
# In gui/app.py:
class ComputeWorker(QThread):
    finished = pyqtSignal(CoulombResult)
    error = pyqtSignal(Exception)
    progress = pyqtSignal(int, int)  # current_fault, total_faults

    def run(self):
        try:
            result = compute_grid(self.model, progress_callback=self.progress.emit)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)
```

### 11.4 Profiling and Benchmarking

```python
# benchmarks/profile_dc3d.py
"""Profile the DC3D computation to identify bottlenecks."""

import cProfile
import pstats
import numpy as np
from opencoulomb.core.okada import dc3d

def profile_dc3d():
    N = 100_000
    x = np.random.uniform(-50, 50, N)
    y = np.random.uniform(-50, 50, N)
    z = np.full(N, -10.0)

    profiler = cProfile.Profile()
    profiler.enable()

    for _ in range(10):
        dc3d(2.0/3.0, x, y, z, 10.0, 90.0,
             -10.0, 10.0, -7.5, 7.5, 1.0, 0.0, 0.0)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)

if __name__ == '__main__':
    profile_dc3d()
```

The performance gate defined in the specification: if the Tier 1 MVP on a 100x100 grid with 10 faults takes more than 10 seconds, escalate to the Fortran wrapper approach (wrapping the original DC3D Fortran subroutine via `ctypes`, following the `okada_wrapper` pattern).

### 11.5 Fortran Fallback (`core/_okada_fortran.py`, optional)

```python
"""Optional Fortran wrapper for DC3D (performance fallback).

Only used if the pure NumPy implementation fails the performance gate.
Wraps the original DC3D Fortran subroutine via ctypes.
"""

import ctypes
import numpy as np
from pathlib import Path

# Try to load the compiled Fortran shared library
_LIB_PATH = Path(__file__).parent / '_dc3d.so'
_lib = None

def _load_fortran_lib():
    global _lib
    if _LIB_PATH.exists():
        _lib = ctypes.CDLL(str(_LIB_PATH))
        # Configure argument types...
    return _lib is not None

def dc3d_fortran(alpha, x, y, z, depth, dip,
                 al1, al2, aw1, aw2, disl1, disl2, disl3):
    """Call the Fortran DC3D via ctypes. Falls back to NumPy if unavailable."""
    if _lib is None and not _load_fortran_lib():
        from opencoulomb.core.okada import dc3d
        return dc3d(alpha, x, y, z, depth, dip,
                    al1, al2, aw1, aw2, disl1, disl2, disl3)
    # ... ctypes call
```

---

## 12. Dependency Management

### 12.1 pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "opencoulomb"
version = "0.1.0"
description = "Open-source Coulomb failure stress computation"
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.10"
authors = [
    {name = "OpenCoulomb Contributors"},
]
keywords = ["seismology", "earthquake", "coulomb", "stress", "okada"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Scientific/Engineering :: Physics",
    "Topic :: Scientific/Engineering :: GIS",
]

# --- Core dependencies (Tier 1 MVP) ---
dependencies = [
    "numpy>=1.24",
    "scipy>=1.10",
    "matplotlib>=3.7",
    "click>=8.1",
]

[project.optional-dependencies]
# Tier 2: GUI and geographic support
gui = [
    "PySide6>=6.5",        # LGPL, avoids PyQt6 GPL concern
    "PyVista>=0.42",       # 3D visualization
]
geo = [
    "cartopy>=0.22",       # Map projections, coastlines
    "pyproj>=3.5",         # Coordinate transforms (UTM etc.)
]
# Tier 3: Advanced features
web = [
    "plotly>=5.18",
    "fastapi>=0.100",
    "uvicorn>=0.20",
]
science = [
    "cmcrameri>=1.7",      # Scientific colormaps (Crameri 2018)
    "xarray>=2023.1",      # NetCDF via xarray
    "netCDF4>=1.6",        # NetCDF file format
    "pandas>=2.0",         # DataFrame output
]
# Everything
all = [
    "opencoulomb[gui]",
    "opencoulomb[geo]",
    "opencoulomb[web]",
    "opencoulomb[science]",
]
# Development
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "pytest-benchmark>=4.0",
    "hypothesis>=6.80",
    "ruff>=0.1",
    "mypy>=1.5",
    "pre-commit>=3.3",
]

[project.scripts]
opencoulomb = "opencoulomb.cli.main:cli"

[project.urls]
Homepage = "https://github.com/opencoulomb/opencoulomb"
Documentation = "https://opencoulomb.readthedocs.io"
Repository = "https://github.com/opencoulomb/opencoulomb"
Issues = "https://github.com/opencoulomb/opencoulomb/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/opencoulomb"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"
markers = [
    "benchmark: performance benchmark tests",
    "slow: tests that take > 10 seconds",
    "validation: numerical validation against Coulomb 3.4",
]

[tool.ruff]
target-version = "py310"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM", "NPY"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.coverage.run]
source = ["opencoulomb"]
branch = true

[tool.coverage.report]
fail_under = 85
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "\\.\\.\\.",
]
```

### 12.2 Dependency Rationale

| Dependency | Version | Why Required | Why This Version |
|------------|---------|-------------|------------------|
| `numpy` | >= 1.24 | Core array computation, vectorized Okada | Supports Python 3.10+, NDArray typing |
| `scipy` | >= 1.10 | Eigenvalue solver (OOPs), interpolation | Stable API, performance improvements |
| `matplotlib` | >= 3.7 | All 2D plotting (contour, quiver, sections) | Subfigure improvements, style system |
| `click` | >= 8.1 | CLI framework (commands, options, groups) | Rich help formatting, type validation |

Optional dependencies are loaded lazily to avoid import-time overhead:

```python
# Pattern for optional imports:
def plot_3d_faults(faults, ...):
    try:
        import pyvista as pv
    except ImportError:
        raise ImportError(
            "3D visualization requires PyVista. "
            "Install with: pip install opencoulomb[gui]"
        )
    # ... use pv
```

### 12.3 Minimum Version Policy

- **Python**: 3.10+ (for `X | Y` union types, match statements, `slots=True` in dataclasses)
- **NumPy**: 1.24+ (for `numpy.typing.NDArray` stability, NEP 29 compliance)
- **Core deps**: Follow NEP 29 (support versions released in the last 24 months)
- **Optional deps**: Minimum version tested in CI; older versions may work but are not guaranteed

### 12.4 CI Test Matrix

```yaml
# .github/workflows/test.yml (conceptual)
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ["3.10", "3.11", "3.12", "3.13"]
    exclude:
      # Skip some combinations to reduce CI time
      - os: macos-latest
        python-version: "3.10"
      - os: windows-latest
        python-version: "3.10"
```

---

## Appendix A: Coordinate System Reference

```
Geographic coordinate system:
    X = East       (positive eastward)
    Y = North      (positive northward)
    Z = Up         (positive upward)

    In OpenCoulomb, depths are stored as positive values (depth_km).
    When passed to Okada's DC3D, z is negated: z_okada = -depth_km.

Okada fault-local coordinate system:
    X = along-strike  (positive in strike direction)
    Y = horizontal, perpendicular to strike  (positive to the right)
    Z = vertical      (positive upward, z <= 0 below surface)

    Origin: at the fault center point, projected to the surface.
    The center is computed from the surface trace midpoint plus
    the dip-projected offset of the fault centroid.

Strike convention:
    Measured clockwise from North (0-360 degrees).
    When looking along the strike direction, the fault dips to the right.

Dip convention:
    Measured from horizontal (0-90 degrees).
    Always positive.

Depth convention:
    Coulomb: positive downward (depth_km > 0 below surface)
    Okada: negative downward (z < 0 below surface)
    Conversion: z_okada = -depth_km

Slip sign conventions:
    .inp file (Coulomb):
        Right-lateral = POSITIVE
        Reverse/thrust = POSITIVE
    Okada DC3D internal:
        Left-lateral = POSITIVE (DISL1 > 0)
        Reverse = POSITIVE (DISL2 > 0)
    Conversion: DISL1 = -slip_1 (for KODE 100)
```

## Appendix B: Key Mathematical Formulas

### B.1 Okada Medium Constant

```
alpha = (lambda + mu) / (lambda + 2*mu) = 1 / (2 * (1 - nu))

For nu = 0.25: alpha = 2/3
```

### B.2 Hooke's Law (Coulomb formulation)

```
sk = E / (1 + nu)                          # = 2 * mu (twice shear modulus)
gk = nu / (1 - 2*nu)                       # = lambda / mu

vol = du_x/dx + du_y/dy + du_z/dz          # volumetric strain

sigma_xx = sk * (gk * vol + du_x/dx) * 0.001
sigma_yy = sk * (gk * vol + du_y/dy) * 0.001
sigma_zz = sk * (gk * vol + du_z/dz) * 0.001
sigma_xy = mu * (du_x/dy + du_y/dx) * 0.001
sigma_xz = mu * (du_x/dz + du_z/dx) * 0.001
sigma_yz = mu * (du_y/dz + du_z/dy) * 0.001

where mu = E / (2*(1+nu)) = sk/2
```

### B.3 Coulomb Failure Stress

```
Delta_CFS = Delta_tau + mu' * Delta_sigma_n

Delta_tau   = resolved shear stress change (positive promotes slip)
Delta_sigma_n = normal stress change (positive = unclamping, tension)
mu'         = effective friction coefficient (default 0.4)
```

### B.4 Bond Transformation (Stress Resolution)

To resolve a stress tensor `[sxx, syy, szz, syz, sxz, sxy]` onto a fault plane defined by (strike, dip, rake):

```
1. Build direction cosine matrix from (strike, dip):
   n1 = [sin(strike), cos(strike), 0]                   # strike direction
   n2 = [-cos(strike)*cos(dip), sin(strike)*cos(dip), sin(dip)]  # updip
   n3 = [cos(strike)*sin(dip), -sin(strike)*sin(dip), cos(dip)]  # normal

2. Build 6x6 Bond matrix M from direction cosines (standard Voigt rules)

3. Transform: [s'_xx, s'_yy, s'_zz, s'_yz, s'_xz, s'_xy] = M @ [sxx, syy, szz, syz, sxz, sxy]

4. Normal stress on fault: sigma_n = s'_zz
   (s'_zz is the stress on the plane whose normal is n3)

5. Shear stress in rake direction:
   tau = s'_xz * cos(rake) + s'_yz * sin(rake)
   (resolve the traction vector in the slip direction)
```

### B.5 Optimally Oriented Planes

```
1. Total stress tensor = regional_stress(depth) + earthquake_stress

2. Eigendecomposition: S = Q . diag(s1, s2, s3) . Q^T
   where s1 >= s2 >= s3

3. Mohr-Coulomb failure angle:
   beta = pi/4 - 0.5 * atan(mu')

4. Two conjugate fault planes:
   - Plane 1 normal: rotated by +beta from s1 axis toward s3 axis
   - Plane 2 normal: rotated by -beta from s1 axis toward s3 axis

5. For each plane: compute CFS, return the one with max |CFS|
```

---

*End of Architecture Document*
