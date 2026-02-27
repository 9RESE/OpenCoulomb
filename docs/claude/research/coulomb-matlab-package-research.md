# Coulomb MATLAB Package - Source Code Analysis

**Research Type**: Technology Evaluation & Source Code Analysis
**Date**: 2026-02-27
**Confidence Score**: 95%

---

## Executive Summary

The Coulomb software is a MATLAB-based application for calculating static displacements, strains, and stresses caused by fault slip, magmatic intrusion, or dike expansion/contraction in an elastic half-space. Originally developed by Shinji Toda, Ross S. Stein, Jian Lin, and Volkan Sevilgen under USGS sponsorship, it has been downloaded over 10,000 times and cited in over 3,000 journal articles. The software exists in two major lineages: Coulomb 3.x (3.3/3.4, hosted by USGS and Temblor.net) and Coulomb 4.0 (a rewrite by Kaede Yoshizawa at Tohoku University, hosted on GitHub). Multiple Python and C reimplementations exist.

---

## 1. Official Software Versions and Download Locations

### Coulomb 3.3/3.4 (USGS)

- **Download**: https://coulomb.s3.us-west-2.amazonaws.com/downloads/coulomb3402.zip (86.5 MB)
- **Portal**: https://temblor.net/coulomb/
- **USGS Publication Page**: https://pubs.usgs.gov/of/2011/1060/
- **USGS Software Page**: https://www.usgs.gov/node/279387
- **User Guide PDF**: https://pubs.usgs.gov/of/2011/1060/of2011-1060.pdf
- **Authors**: Toda, S., Stein, R.S., Sevilgen, V., Lin, J.
- **Year**: 2011 (User Guide), package updated through 2022

### Coulomb 4.0 Beta (Tohoku / Temblor)

- **GitHub**: https://github.com/YoshKae/Coulomb_ver4 (primary), https://github.com/YoshKae/Coulomb_Update (companion, same content)
- **Temblor Landing Page**: https://temblor.net/coulomb/ (links to both repos + legacy coulomb3402.zip)
- **Author**: Kaede Yoshizawa (Tohoku University), with Toda, Stein, Sevilgen, Lin
- **Release Date**: 2026-02-08 (ver. 4.0.0 beta)
- **Requirements**: MATLAB 2024a+ (more stable on 2025a+); Mapping Toolbox, Image Processing Toolbox, Curve Fitting Toolbox
- **Architecture**: Single MATLAB App Designer file (coulomb.mlapp) replacing the collection of .m scripts

---

## 2. Coulomb 3.4 Package Structure (coulomb3402.zip)

### Top-Level Directory Layout

```
coulomb3402/
+-- coulomb.m                          # Main entry point (10,682 bytes)
+-- sources/                           # Core computation and GUI code (~120 .m files)
+-- okada_source_conversion/           # Okada DC3D/DC3D0 MATLAB translation (~11 .m files)
+-- coulomb_cui_set/                   # Command-line (CUI) interface + duplicate Okada files
+-- plug_ins/                          # Extension plugins (~35 .m files + data)
+-- resources/                         # Utility functions, Google Earth toolbox, etc.
+-- utm/                               # UTM coordinate conversion and Wells-Coppersmith window
+-- DATABASE/                          # Geophysical data (coastlines, plates, volcanoes, CMT, faults)
+-- input_file/                        # Example .inp input files (~20 files)
+-- output_files/                      # Output directory (empty)
+-- coastline_data/                    # Coastline data files
+-- earthquake_data/                   # Earthquake catalog data
+-- active_fault_data/                 # Active fault trace data
+-- gps_data/                          # GPS displacement data
+-- gmt_files/                         # GMT plotting files
+-- miscellaneous_data/                # Misc data files
+-- slides/                            # Presentation slides
+-- preferences/                       # User preference files
+-- license/                           # License information
```

### Total MATLAB File Count: ~242 .m files

---

## 3. Core Computation Files (Algorithm Engine)

### 3.1 Okada Dislocation Engine (`okada_source_conversion/`)

These files are a direct MATLAB translation of Okada's original Fortran DC3D subroutines. They compute displacement and displacement derivatives (strains) at any point in an elastic half-space due to a finite rectangular or point dislocation source.

| File | Size | Description |
|------|------|-------------|
| `Okada_DC3D.m` | 11,440 B | **Main routine**: Displacement and strain at depth due to buried finite rectangular fault. Direct translation of Okada (1992) DC3D Fortran subroutine. |
| `Okada_DC3D0.m` | 5,508 B | **Point source variant**: Displacement and strain due to a point source. Translation of Okada DC3D0. |
| `DCCON0.m` | 2,070 B | Common parameter initialization for DC3D. |
| `DCCON1.m` | 3,007 B | Coordinate conversion subroutine (part of DC3D). |
| `DCCON2.m` | 4,843 B | Additional coordinate conversions for DC3D. |
| `UA.m` | 5,295 B | Displacement contributions from strike-slip, dip-slip, and tensile components (Part A). |
| `UB.m` | 6,501 B | Displacement contributions Part B (image source). |
| `UC.m` | 7,055 B | Displacement contributions Part C (depth-dependent terms). |
| `UA0.m` | 7,172 B | Point source displacement Part A. |
| `UB0.m` | 7,849 B | Point source displacement Part B. |
| `UC0.m` | 8,895 B | Point source displacement Part C. |

**Note**: Identical copies exist in `coulomb_cui_set/okada_source_conversion_cexp/`.

### 3.2 Core Computation Pipeline (`sources/`)

| File | Size | Description |
|------|------|-------------|
| `Okada_halfspace.m` | 13,036 B | **Master computation orchestrator**: Iterates over grid points and fault elements, calls `Okada_DC3D` or `Okada_DC3D0`, converts strains to stresses using Hooke's law, rotates tensors from fault-local to geographic coordinates via `tensor_trans`. Populates global `DC3D` matrix (N_CELL x 14). |
| `Okada_halfspace_one.m` | 10,721 B | Single-element version of the halfspace calculation (used for individual fault stress queries). |
| `calc_coulomb.m` | 3,597 B | **Coulomb stress resolver**: Takes stress tensor (6 components), fault orientation (strike, dip, rake), and friction coefficient; resolves shear, normal, and Coulomb stress on the fault plane using 6x6 tensor transformation matrix. Key equation: `coulomb = shear + friction * normal`. |
| `calc_element.m` | 3,011 B | Calculates stress on individual fault elements. |
| `tensor_trans.m` | 1,933 B | **Tensor rotation**: Rotates 6-component stress tensor (Voigt notation) from Okada's fault-local coordinate system to the geographic coordinate system using direction cosines. |
| `stress_trans.m` | 3,563 B | General stress tensor transformation given arbitrary principal axis orientations. |
| `coord_conversion.m` | 1,951 B | **Coordinate transform**: Converts geographic (x,y) coordinates to Okada's fault-centered coordinate system. Handles fault center point, strike rotation, and dip projection. |
| `dc3de_calc.m` | 3,783 B | Internal function for computing DC3D at arbitrary (x,y) points (used for point stress calculations on faults). |
| `coulomb_calc_and_view.m` | 14,518 B | High-level driver that orchestrates calculation and visualization. |
| `coulomb_section.m` | 18,993 B | Cross-section computation and visualization. |
| `split_calc.m` | 2,228 B | Splits fault elements for refined calculations. |
| `split_element.m` | 1,290 B | Subdivides fault elements into smaller patches. |
| `taper_calc.m` | 6,039 B | Applies slip taper to fault edges. |
| `fault_int_sec.m` | 14,460 B | Fault intersection/section calculations. |
| `nodal_plane_calc.m` | 19,819 B | Nodal plane and focal mechanism calculations. |
| `focal_mech_calc.m` | 23,189 B | Focal mechanism computation and conversion. |

### 3.3 Coordinate and Utility Functions

| File | Description |
|------|-------------|
| `lonlat2xy.m` | Longitude/latitude to local km conversion |
| `xy2lonlat.m` | Local km to longitude/latitude conversion |
| `change_coordinates.m` | Coordinate system switching |
| `check_unit_vector.m` | Unit vector validation |
| `fault_corners.m` | Compute fault corner positions |
| `fault_corners_vec.m` | Vectorized fault corner computation |
| `rake2comp.m` | Convert rake angle to strike-slip and dip-slip components |
| `comp2rake.m` | Convert components back to rake angle |
| `seis_moment.m` | Seismic moment calculation |
| `calc_seis_moment.m` | Extended seismic moment computation |
| `distance2.m` | Distance calculation between points |
| `regional_stress.m` | Regional stress field application |

### 3.4 GUI and Visualization (`sources/`)

The GUI files are extensive (the largest is `main_menu_window.m` at 55,261 bytes). Major GUI files include:

| File | Description |
|------|-------------|
| `main_menu_window.m` | Main application window (55 KB) |
| `input_window.m` | Fault input interface (37 KB) |
| `element_modification_window.m` | Fault element editor (32 KB) |
| `preference_window.m` | Settings/preferences (32 KB) |
| `coulomb_window.m` | Coulomb stress display controls |
| `displ_open.m` | Displacement visualization |
| `strain_window.m` | Strain visualization |
| `xsec_window.m` | Cross-section controls |
| `grid_drawing.m` | Map/grid rendering |
| `grid_drawing_3d.m` | 3D visualization |

### 3.5 Plugin Files (`plug_ins/`)

| Plugin | Description |
|--------|-------------|
| `srcmod2coulomb.m` / `srcmod2coulomb2.m` | Import SRCMOD finite-fault models |
| `seis_rate_change.m` | Seismicity rate change calculation (Dieterich 1994) |
| `expected_seis_rate.m` | Expected seismicity rate computation |
| `smoothed_background.m` | Smoothed background seismicity |
| `receiver_matrix_maker.m` | Generate receiver fault grids |
| `coulomb_3d_view.m` | 3D visualization |
| `coulomb2googleearth.m` | Export to Google Earth KML |
| `coulomb2gmt_source.m` / `coulomb2gmt_cout.m` / `coulomb2gmt_meca.m` | Export to GMT |
| `digitize_faults.m` | Interactive fault digitization |
| `digitize_polygon.m` | Polygon digitization |
| `how_to_write_plugin.m` | Plugin authoring guide |

---

## 4. Key Data Structures and Global Variables

From `global_variable_explanation.m`:

### DC3D Matrix (N_CELL x 14)
The central computation result matrix:
```
Column 1-2:  XYCOORD (x, y position in study area, km)
Column 3:    X (x position in fault coordinate)
Column 4:    Y (y position in fault coordinate)
Column 5:    Z (z position/depth)
Column 6:    UXG (Displacement along x-axis, m)
Column 7:    UYG (Displacement along y-axis, m)
Column 8:    UZG (Displacement along z-axis, m)
Column 9:    SXX (Stress component sigma_xx, bar)
Column 10:   SYY (Stress component sigma_yy, bar)
Column 11:   SZZ (Stress component sigma_zz, bar)
Column 12:   SYZ (Shear stress sigma_yz, bar)
Column 13:   SXZ (Shear stress sigma_xz, bar)
Column 14:   SXY (Shear stress sigma_xy, bar)
```

### ELEMENT Matrix (NUM x 9)
Each source/receiver fault element:
```
Column 1: xstart (km)
Column 2: ystart (km)
Column 3: xfinish (km)
Column 4: yfinish (km)
Column 5: right-lateral slip (m) or other per KODE
Column 6: reverse slip (m) or other per KODE
Column 7: dip (degrees)
Column 8: fault top depth (km)
Column 9: fault bottom depth (km)
```

### KODE Values
```
100: Standard fault: right-lateral slip (col 5) + reverse slip (col 6)
200: Tensile opening (col 5) + right-lateral slip (col 6)
300: Tensile opening (col 5) + reverse slip (col 6)
400: Point source: right-lateral (col 5) + reverse (col 6)
500: Tensile opening (col 5) + point inflation (col 6)
```

### FUNC_SWITCH Values
```
1: Grid drawing
2: Horizontal displacement
3: Wireframe
4: Vertical displacement
5: 3D draped plot
6: Strain calculation
7: Shear stress change
8: Normal stress change
9: Coulomb stress change
10: Stress on faults (EC function)
```

### Key Scalar Parameters
- `POIS`: Poisson's ratio (typically 0.25)
- `YOUNG`: Young's modulus (typically 800,000 bar = 80 GPa)
- `FRIC`: Coefficient of friction (typically 0.4)
- `CALC_DEPTH`: Calculation depth (km)

---

## 5. Input File Format (.inp)

### Header Structure (Lines 1-4)
```
Line 1: Title/description text
Line 2: Additional description
Line 3: Parameters header (fixed-format):
  #reg1= 0  #reg2= 0  #fixed= NNN  sym= 1
  PR1= 0.250  PR2= 0.250  DEPTH= 10.0
  E1= 0.800000E+06  E2= 0.800000E+06
  XSYM= 0.000  YSYM= 0.000  FRIC= 0.400
Line 4: Regional stress parameters:
  S1DR= 24.0001  S1DP= 0.0001  S1IN= 100.000  S1GD= 0.000
  S3DR= 114.0001  S3DP= 0.0001  S3IN= 30.000  S3GD= 0.000
  S2DR= 89.9999  S2DP= -89.999  S2IN= 0.000  S2GD= 0.000
```

Key parameters:
- `#fixed=`: Total number of fault elements (sources + receivers)
- `PR1`, `PR2`: Poisson's ratio for regions 1 and 2
- `E1`, `E2`: Young's modulus for regions 1 and 2 (bar)
- `DEPTH`: Default calculation depth (km)
- `FRIC`: Friction coefficient
- `S1DR/S1DP/S1IN`: Sigma-1 direction/dip/intensity (regional stress)

### Column Header (Line 5)
```
  #   X-start    Y-start     X-fin      Y-fin   Kode   shear    normal   dip angle     top      bot
```

### Fault Element Format (Lines 6+)
```
xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx  label
```
Fixed-width columns:
- Column 1: Element number flag (1 = source with slip, 1 with zero slip = receiver)
- X-start, Y-start: Start coordinates (km from origin, or lon/lat)
- X-fin, Y-fin: End coordinates
- Kode: Element type (100, 200, 300, 400, 500)
- Shear: Right-lateral slip (m) -- 0 for receiver faults
- Normal: Reverse slip (m) -- 0 for receiver faults
- Dip angle: Fault dip (degrees, must be positive)
- Top: Fault top depth (km)
- Bot: Fault bottom depth (km)
- Label: Text description

### Grid Parameters (after fault elements)
```
Grid Parameters
  1  ---  Start-x = value
  2  ---  Start-y = value
  3  ---  Finish-x = value
  4  ---  Finish-y = value
  5  ---  x-increment = value
  6  ---  y-increment = value
```

### Sign Conventions
- Right-lateral slip: POSITIVE
- Left-lateral slip: NEGATIVE
- Reverse slip: POSITIVE
- Normal slip: NEGATIVE
- Dip: Always POSITIVE
- Strike direction: Looking along strike, hanging wall is to the right
- Depth: POSITIVE downward

---

## 6. Mathematical Formulations

### 6.1 Okada's Elastic Half-Space Solution (Okada 1992)

The core engine computes displacement **u_i** and displacement gradients **du_i/dx_j** at an arbitrary point (x, y, z) in a homogeneous, isotropic elastic half-space due to a rectangular dislocation source. The medium constant alpha is:

```
alpha = (lambda + mu) / (lambda + 2*mu) = 1 / (2*(1 - nu))
```

where nu is Poisson's ratio.

**Inputs to DC3D**:
- ALPHA: Medium constant
- X, Y, Z: Observation point coordinates
- DEPTH: Source depth (center of fault)
- DIP: Dip angle (degrees)
- AL1, AL2: Fault half-lengths along strike (-strike, +strike)
- AW1, AW2: Fault half-widths along dip (down-dip, up-dip)
- DISL1, DISL2, DISL3: Strike-slip, dip-slip, tensile dislocation

**Outputs**:
- UX, UY, UZ: Displacement components
- UXX, UYX, UZX, UXY, UYY, UZY, UXZ, UYZ, UZZ: Displacement gradient tensor (9 components)

### 6.2 Strain to Stress Conversion (Hooke's Law)

From `Okada_halfspace.m`:
```matlab
sk = YOUNG / (1.0 + POIS);                    % 2 * shear modulus
gk = POIS / (1.0 - 2.0 * POIS);               % lambda/mu ratio
vol = UXX + UYY + UZZ;                         % volumetric strain

sxx = sk * (gk * vol + UXX) * 0.001;           % Factor 0.001 for km->m unit conversion
syy = sk * (gk * vol + UYY) * 0.001;
szz = sk * (gk * vol + UZZ) * 0.001;
sxy = (YOUNG/(2*(1+POIS))) * (UXY + UYX) * 0.001;
sxz = (YOUNG/(2*(1+POIS))) * (UXZ + UZX) * 0.001;
syz = (YOUNG/(2*(1+POIS))) * (UYZ + UZY) * 0.001;
```

Note: The 0.001 factor converts from the mixed km/m unit system (strains are unitless derivatives of m displacement over km distance).

### 6.3 Tensor Rotation (tensor_trans.m)

Rotates the 6-component stress tensor (Voigt notation: [sxx, syy, szz, syz, sxz, sxy]) from fault-local to geographic coordinates using a 6x6 transformation matrix built from direction cosines.

### 6.4 Coulomb Failure Stress (calc_coulomb.m)

```
Delta_CFS = Delta_tau + mu' * Delta_sigma_n
```

Where:
- Delta_tau = resolved shear stress change on the receiver fault (in rake direction)
- Delta_sigma_n = resolved normal stress change (positive = unclamping)
- mu' = effective coefficient of friction (typically 0.4, includes pore pressure effects)

The code resolves the full 3D stress tensor onto the receiver fault plane defined by (strike, dip, rake) using the Bond transformation matrix (6x6 direction cosine matrix), then applies a rake rotation to extract shear stress in the slip direction.

---

## 7. Computation Workflow

```
1. Parse .inp file --> ELEMENT array, GRID parameters, material properties
2. For each grid point (NXINC x NYINC):
   3. For each source fault element (ii = 1:NUM):
      a. coord_conversion(): Transform grid point from geographic to fault-local coords
      b. Okada_DC3D(): Compute displacement + 9 displacement derivatives
      c. Rotate displacements back to geographic coordinates
      d. Convert displacement gradients to stress tensor (Hooke's law)
      e. tensor_trans(): Rotate stress tensor to geographic coordinates
      f. Accumulate results in DC3D matrix (superposition)
4. For Coulomb stress visualization:
   a. calc_coulomb(): Resolve stress tensor onto receiver fault orientation
   b. Compute shear + friction * normal = Coulomb stress
5. Visualization and output
```

---

## 8. Coulomb 4.0 Beta Structure

```
Coulomb_ver4_beta/
+-- coulomb.mlapp           # Single MATLAB App Designer file (main application)
+-- input_files/            # Finite fault model data
+-- input_overlay_files/    # Overlay data for visualization
+-- other_functions/        # Optional utilities
+-- output_cou_files/       # Coulomb output files
+-- output_data_files/      # Processed data outputs
+-- preferences/            # Runtime configuration
+-- slides/                 # Documentation/presentations
```

Key differences from 3.4:
- Entire application in a single .mlapp file (MATLAB App Designer)
- Requires MATLAB 2025a+
- Requires Mapping Toolbox, Image Processing Toolbox, Curve Fitting Toolbox
- Integrates ISC earthquake toolbox and USGS finite fault models
- Unified workspace (no pop-ups)
- Coastline visualization via NOAA GSHHG data

---

## 9. GitHub Repositories

### Direct Coulomb Software
| Repository | URL | Description |
|-----------|-----|-------------|
| **Coulomb 4.0** | https://github.com/YoshKae/Coulomb_ver4 | Official Coulomb 4.0 beta (primary repository) |
| **Coulomb 4.0 Update** | https://github.com/YoshKae/Coulomb_Update | Official Coulomb 4.0 companion repository (currently shares same content) |

### Coulomb-Related Tools
| Repository | URL | Description |
|-----------|-----|-------------|
| **3D-faults** | https://github.com/ZoeMildon/3D-faults | Generates 3D strike-variable fault planes for Coulomb 3.4 input |
| **3D-Faults-stress-plotter** | https://github.com/MDiercks/3D-Faults-stress-plotter | MATLAB app to plot Coulomb stress on 3D fault networks |
| **CoulombAnalysis** | https://github.com/jjwangw/CoulombAnalysis | Fortran/MATLAB/Shell program for Coulomb stress changes |
| **coulomb2gmt** | https://github.com/demanasta/coulomb2gmt | Bash scripts to plot Coulomb results with GMT |

### Python Implementations (Coulomb-equivalent)
| Repository | URL | Description |
|-----------|-----|-------------|
| **elastic_stresses_py** | https://github.com/kmaterna/elastic_stresses_py | Python "mini-Coulomb" -- reads .inp files, reproduces Coulomb outputs. Uses Okada 1992 via cutde library. Most complete Python replacement. |
| **OkadaPy** | https://github.com/hemmelig/OkadaPy | Python+C implementation of Okada 1992. Computes displacement, strain, stress. |
| **okada_wrapper** | https://github.com/tbenthompson/okada_wrapper | MATLAB and Python wrappers for Okada DC3D/DC3D0 Fortran code via MEX/ctypes |
| **okada4py** | https://github.com/jolivetr/okada4py | Pure Python Okada implementation |

### Other Okada Implementations
| Repository | URL | Language | Description |
|-----------|-----|----------|-------------|
| **IPGP deformation-lib** | https://github.com/IPGP/deformation-lib | MATLAB/Octave | Okada85 literal transcription + other deformation models |
| **DC3D.f90** | https://github.com/hydrocoast/DC3D.f90 | Fortran 90 | Modern Fortran rewrite of Okada's DC3D |
| **Pyrocko okada** | https://pyrocko.org/docs/current/library/reference/pyrocko.modelling.okada.html | Python | Okada module in the Pyrocko seismology toolkit |
| **GeoClaw okada** | https://github.com/clawpack/geoclaw/blob/master/src/python/geoclaw/okada.py | Python | Okada model in Clawpack for tsunami modeling |
| **CutAndDisplace** | https://github.com/Timmmdavis/CutAndDisplace | MATLAB | Boundary element code for faults including Coulomb stress |

### Seismicity Rate Change Tools
| Repository | URL | Description |
|-----------|-----|-------------|
| **tdsr** | https://github.com/torstendahm/tdsr | Time-dependent stress response seismicity model |
| **seismicity_stress** | https://github.com/alomax/seismicity_stress | Spatial correlation between seismicity and CFS change |

---

## 10. Official DC3D Fortran Source (NIED)

The original Fortran source code for DC3D0/DC3D by Yoshimitsu Okada is maintained by Japan's National Research Institute for Earth Science and Disaster Resilience (NIED):

- **URL**: https://www.bosai.go.jp/e/dc3d.html
- **Downloads**: Fortran source (39 KB), User manual (163 KB PDF), Flowchart (250 KB), 5 supplementary derivation PDFs
- **Subroutines**: DC3D0 (point source) and DC3D (finite rectangular fault)
- **Language**: Fortran 77 (fixed-form)

---

## 11. Key Academic Papers

### Foundational Algorithms

1. **Okada, Y. (1985)**. "Surface deformation due to shear and tensile faults in a half-space." *Bulletin of the Seismological Society of America*, 75(4), 1135-1154.
   - Surface displacement solutions only.

2. **Okada, Y. (1992)**. "Internal deformation due to shear and tensile faults in a half-space." *Bulletin of the Seismological Society of America*, 82(2), 1018-1040.
   - DOI: https://doi.org/10.1785/BSSA0820021018
   - PDF: https://www.bosai.go.jp/e/pdf/Okada_1992_BSSA.pdf
   - **THE core algorithm** used by Coulomb. Provides closed-form expressions for internal displacement, strain, and stress due to point and finite rectangular sources.

3. **King, G.C.P., Stein, R.S., and Lin, J. (1994)**. "Static stress changes and the triggering of earthquakes." *Bulletin of the Seismological Society of America*, 84(3), 935-953.
   - DOI: https://doi.org/10.1785/BSSA0840030935
   - Foundational paper for Coulomb stress transfer theory. Demonstrated that aftershocks concentrate where Coulomb stress increased by >0.5 bar, and are sparse where it decreased.

### Coulomb Software Papers

4. **Toda, S., Stein, R.S., Richards-Dinger, K., and Bozkurt, S.B. (2005)**. "Forecasting the evolution of seismicity in southern California: Animations built on earthquake stress transfer." *Journal of Geophysical Research*, 110, B05S16.
   - DOI: https://doi.org/10.1029/2004JB003415
   - Describes the rate/state seismicity rate change model integrated into Coulomb.

5. **Toda, S., Stein, R.S., Sevilgen, V., and Lin, J. (2011)**. "Coulomb 3.3 Graphic-rich deformation and stress-change software for earthquake, tectonic, and volcano research and teaching - User guide." *USGS Open-File Report 2011-1060*.
   - URL: https://pubs.usgs.gov/of/2011/1060/
   - **The official user guide** for the software.

### Related Software Papers

6. **Wang, J., Xu, C., Freymueller, J.T., Wen, Y., and Xiao, Z. (2021)**. "AutoCoulomb: An Automated Configurable Program to Calculate Coulomb Stress Changes on Receiver Faults with Any Orientation." *Seismological Research Letters*, 92(4), 2591-2609.
   - Automated batch processing of Coulomb stress calculations.

---

## 12. elastic_stresses_py (PyCoulomb) - Detailed Structure

The most complete Python reimplementation. Located at https://github.com/kmaterna/elastic_stresses_py

### Directory Structure
```
elastic_stresses_py/PyCoulomb/
+-- __init__.py
+-- configure_calc.py          # Calculation configuration setup
+-- conversion_math.py         # Mathematical conversions (coordinate, tensor)
+-- coulomb_collections.py     # Data structures for stress collections
+-- input_values.py            # Input value handling
+-- io_additionals.py          # Additional I/O operations
+-- output_manager.py          # Output data management
+-- pyc_fault_object.py        # Fault object implementations
+-- pygmt_plots.py             # Plotting via PyGMT
+-- run_dc3d.py                # DC3D elastic dislocation solver wrapper
+-- run_mogi.py                # Mogi point source calculations
+-- run_okada_wrapper.py       # Okada wrapper interface
+-- utilities.py               # General utilities
+-- bin/                       # Executable scripts
+-- disp_points_object/        # Displacement point data structures
+-- fault_slip_object/         # Fault slip representation objects
+-- fault_slip_triangle/       # Triangular fault elements
+-- inputs_object/             # Input configuration objects
+-- point_source_object/       # Point source representations
```

### Key Features
- Reads Coulomb .inp files directly
- Reproduces Coulomb outputs on test cases
- Uses Ben Thompson's cutde library for Okada calculations
- Supports Wells & Coppersmith scaling, focal mechanism input
- PyGMT-based visualization
- Python 3.9+, requires gfortran/gcc for cutde compilation

### CFS Equation (matching Coulomb convention)
```
Delta_CFS = Delta_tau_shear + mu * (Delta_sigma_normal + B * Delta_sigma_kk/3)
```
Where B is Skempton's coefficient for pore pressure effects.

---

## 13. MATLAB File Exchange Listings

- **Okada Surface Deformation**: https://www.mathworks.com/matlabcentral/fileexchange/25982-okada-surface-deformation-due-to-a-finite-rectangular-source
  - Computes Okada 1985 solution (surface only)

- **Okada Solution**: https://www.mathworks.com/matlabcentral/fileexchange/39819-okada-solution
  - Another Okada implementation

---

## 14. Summary of Available Implementations

| Implementation | Language | Okada Version | Internal Stress | CFS | GUI | Reads .inp | License |
|---------------|----------|--------------|----------------|-----|-----|------------|---------|
| **Coulomb 3.4** | MATLAB | 1992 (full) | Yes | Yes | Yes (extensive) | Yes | USGS |
| **Coulomb 4.0** | MATLAB (.mlapp) | 1992 | Yes | Yes | Yes (App Designer) | Yes | Unknown |
| **elastic_stresses_py** | Python | 1992 (via cutde) | Yes | Yes | No (CLI+PyGMT) | Yes | Open source |
| **OkadaPy** | Python+C | 1992 | Yes | No (manual) | No | No | Open source |
| **okada_wrapper** | Python+MATLAB | 1992 (Fortran MEX) | Yes | No | No | No | MIT |
| **CoulombAnalysis** | Fortran+MATLAB | Unknown | Yes | Yes | No | Unknown | Open source |
| **IPGP deformation-lib** | MATLAB | 1985 | No (surface only) | No | No | No | Open source |
| **Pyrocko** | Python | 1992 | Yes | No (manual) | Yes (Snuffler) | No | GPLv3 |
| **DC3D.f90** | Fortran 90 | 1992 | Yes | No | No | No | Unknown |

---

## 15. Key Technical Insights for Reimplementation

1. **Unit System**: Coulomb uses km for distances, meters for slip, bar for stress. The 0.001 factor in strain-to-stress conversion handles the km/m mismatch.

2. **Coordinate Convention**: Left-lateral slip is positive in Okada's code but NEGATIVE in Coulomb's convention. The code applies `e5 = -ELEMENT(ii,5)` to flip the sign.

3. **Fault Parameterization**: Faults are defined by start/end surface trace points (xs,ys,xf,yf), NOT by center+strike. The code internally computes strike from the trace direction.

4. **Superposition Principle**: Stresses from multiple fault elements are summed linearly in the DC3D matrix (elastic superposition).

5. **Receiver Fault Convention**: Receiver faults have zero slip in the input file. They share the same ELEMENT format as source faults.

6. **Depth Convention**: Depth is positive downward. In Okada's code, z is negative below the free surface.

7. **Fault Center**: The code computes the fault center point by averaging start/end coordinates AND shifting by the dip-projected half-width.

8. **Young's Modulus**: Default is 8.0E+05 bar (= 80 GPa), and Poisson's ratio is 0.25 (Poisson solid).

---

*This report is based on direct inspection of the coulomb3402.zip package (downloaded from the official S3 bucket), the Coulomb 4.0 GitHub repository, the USGS user guide, and comprehensive web research of related implementations.*
