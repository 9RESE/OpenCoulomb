# Coulomb MATLAB Package - Technology Assessment

**Date**: 2026-02-27
**Research Type**: Technology Evaluation & Assessment
**Confidence Score**: 92%

---

## 1. What Is the Coulomb Package?

Coulomb is a MATLAB-based software package for calculating static displacements, strains, and stresses caused by fault slip, magmatic intrusion, or dike expansion/contraction in an elastic halfspace. It is the standard tool in earthquake seismology and tectonics for computing **Coulomb stress transfer** -- the process by which stress changes from one earthquake promote or inhibit failure on nearby faults.

### Core Equation

The fundamental Coulomb Failure Stress change (delta-CFS) is:

```
delta_CFS = delta_tau + mu' * delta_sigma_n
```

Where:
- `delta_tau` = change in shear stress (resolved on the receiver fault plane, in the slip direction)
- `delta_sigma_n` = change in normal stress (positive = unclamping/tension)
- `mu'` = apparent (effective) coefficient of friction = `mu * (1 - B)`
- `mu` = coefficient of friction (typically 0.0 to 0.8, default ~0.4)
- `B` = Skempton's coefficient for pore pressure (0 to 1)

A **positive delta_CFS** means a fault has been brought closer to failure; **negative** means it has been moved further from failure (stress shadow).

### What It Calculates

1. **Coulomb Failure Stress Changes (delta_CFS)** on:
   - Specified receiver faults (known geometry)
   - Optimally Oriented Planes (OOPs) -- faults oriented to maximize failure under the regional + perturbed stress field
   - Generalized faults of a specified orientation

2. **Static Displacements** -- surface and subsurface deformation vectors (East, North, Up)

3. **Strain Tensors** -- all six components (xx, yy, zz, xy, xz, yz)

4. **Stress Tensors** -- full stress tensor components including:
   - Normal stress changes
   - Shear stress changes
   - Dilatation (volumetric strain)
   - Maximum shear stress
   - Principal stresses and their axes

5. **GPS displacement modeling** -- comparison of modeled vs. observed GPS vectors

---

## 2. Creators and History

### Authors

| Name | Affiliation | Role |
|------|-------------|------|
| **Shinji Toda** | IRIDeS, Tohoku University, Japan | Lead developer (Coulomb 3.x and 4.0) |
| **Ross S. Stein** | Temblor, Inc. (formerly USGS) | Co-creator, scientific lead |
| **Volkan Sevilgen** | Temblor, Inc. (formerly USGS) | Co-developer |
| **Jian Lin** | Woods Hole Oceanographic Institution | Co-developer |
| **Kaede Yoshizawa** | (Coulomb 4.0) | Developer |

### Version History

| Version | Approximate Year | Key Changes |
|---------|-----------------|-------------|
| Coulomb 1.x | ~1990s | Original USGS tool |
| Coulomb 2.x | ~2000s | Enhanced GUI |
| Coulomb 3.0 | ~2005 | Major MATLAB GUI rewrite |
| Coulomb 3.1 | ~2007 | Improved documentation |
| Coulomb 3.2 | ~2009 | Additional features |
| Coulomb 3.3 | 2011 | Official USGS Open-File Report (2011-1060), 63-page user guide |
| Coulomb 3.4 | ~2014-2015 | Bug fixes, minor enhancements, last USGS-hosted version |
| Coulomb 3.4.2 | ~2016 | Patch release |
| Coulomb 4.0 | 2026 (beta 2026-02-08) | Major rewrite: unified workspace, ISC catalog, depth-loop engine, 3D capabilities |

### Impact

- Coulomb 3.x has been **downloaded over 10,000 times**
- **Cited in over 3,000 journal articles**
- De facto standard for Coulomb stress transfer analysis in the seismology community

---

## 3. Source Code and Distribution

### Coulomb 3.x (USGS)

- **USGS Page**: https://www.usgs.gov/node/279387 (Coulomb 3)
- **User Guide**: USGS Open-File Report 2011-1060
  - HTML: https://pubs.usgs.gov/of/2011/1060/
  - PDF: https://pubs.usgs.gov/of/2011/1060/of2011-1060.pdf
- **Distribution**: Originally distributed as a ZIP file from the USGS website containing MATLAB source code (.m files) and example input files
- **No GitHub repository** exists for the official USGS Coulomb 3.x code

### Coulomb 4.0 (Temblor / Tohoku University)

- **Landing Page**: https://temblor.net/coulomb/
- **Announcement**: https://temblor.net/earthquake-insights/introducing-coulomb-4-0-enhanced-stress-interaction-and-deformation-software-for-research-and-teaching-17066/
- Described as "open source MATLAB software"
- **GitHub Repositories** (both maintained by Kaede Yoshizawa):
  - https://github.com/YoshKae/Coulomb_ver4 — primary Coulomb 4.0 beta repository
  - https://github.com/YoshKae/Coulomb_Update — companion update repository (currently shares same content)
- **Version**: ver. 4.0.0 beta (2026-02-08)
- **Requirements**: MATLAB 2024a+ (more stable on 2025a+); Mapping Toolbox, Image Processing Toolbox, Curve Fitting Toolbox
- The Temblor Coulomb page links to both GitHub repositories and also exposes the legacy `coulomb3402.zip` download

### Related GitHub Repositories

| Repository | Language | Purpose |
|-----------|----------|---------|
| [Coulomb_ver4](https://github.com/YoshKae/Coulomb_ver4) | MATLAB (.mlapp) | **Official Coulomb 4.0 beta** |
| [Coulomb_Update](https://github.com/YoshKae/Coulomb_Update) | MATLAB (.mlapp) | **Official Coulomb 4.0 companion repository** |
| [coulomb3.4-additional-code](https://github.com/ZoeMildon/coulomb3.4-additional-code) | MATLAB | Additional 3D fault visualization code for Coulomb 3.4 |
| [3D-faults](https://github.com/ZoeMildon/3D-faults) | MATLAB | Generate 3D strike-variable fault planes for Coulomb 3.4 input |
| [3D-Faults-stress-plotter](https://github.com/MDiercks/3D-Faults-stress-plotter) | MATLAB | Plot Coulomb stress on 3D fault networks from Coulomb 3.3+ |
| [coulomb2gmt](https://github.com/demanasta/coulomb2gmt) | Bash/GMT | Plot Coulomb output files using Generic Mapping Tools |

---

## 4. Current Version

**Coulomb 4.0** is the current version (ver. 4.0.0 beta released 2026-02-08 per the GitHub repository README), developed primarily by Yoshizawa, Toda, Stein, Sevilgen, and Lin and hosted on GitHub and at Temblor, Inc. Development began circa 2024-2025.

**Coulomb 3.4.2** is the last USGS-distributed version and remains widely used.

---

## 5. Complete Features and Capabilities

### 5.1 Source Modeling

- **Fault slip sources**: Rectangular dislocation patches (Okada model)
  - Defined by: strike, dip, rake, length, width, depth, slip magnitude
  - Right-lateral and reverse slip are positive by convention
  - Can compose complex ruptures from multiple sub-fault patches
- **Tensile/opening sources**: Dike expansion/contraction, sill intrusion
- **Magmatic sources**: Magma chamber inflation/deflation modeling
- **Multiple source faults**: Superposition of solutions (linearity)

### 5.2 Receiver Fault Types

1. **Specified faults** (known geometry): User defines strike, dip, rake
2. **Optimally Oriented Planes (OOPs)**: Automatically computed to maximize delta_CFS given regional + perturbed stress field
3. **Subdivided receivers**: Faults discretized into smaller patches for stress resolution
4. **CMT/focal mechanism receivers**: Import from earthquake catalogs
5. **Nodal planes**: Both nodal planes from focal mechanisms

### 5.3 Stress Calculations

- **Coulomb failure stress change (delta_CFS)** on all receiver types
- **Normal stress change** (clamping/unclamping)
- **Shear stress change** (in slip direction)
- **Maximum shear stress**
- **Dilatation** (volumetric strain)
- **Principal stress axes** and magnitudes
- **Regional stress field** specification (orientation, magnitude, regime)
- **Effective friction coefficient** (mu' = mu(1-B), configurable)

### 5.4 Deformation Calculations

- **Surface displacements**: East, North, Up components on a grid
- **Subsurface displacements**: At any specified depth
- **GPS comparison**: Import observed GPS vectors, compare with modeled
- **Strain components**: Full tensor (xx, yy, zz, xy, xz, yz)

### 5.5 Visualization (Coulomb 3.x)

- **Map view**: Color-filled stress/strain maps at specified depth
- **Cross-sections**: Vertical slices showing stress/displacement at depth
- **3D fault display**: Source and receiver fault geometry
- **Slip vectors**: On fault patches
- **Principal stress axes**: Direction and magnitude
- **Earthquake overlays**: Plot catalog seismicity on stress maps
- **Fault trace overlays**: Import and display known fault maps
- **GPS displacement vectors**: Observed vs. modeled
- **Publication-quality PDF output**: Vector graphics, editable
- **MATLAB .fig files**: Interactive 3D figures

### 5.6 Visualization (Coulomb 4.0 Additions)

- **Unified workspace**: All modeling, catalogs, overlays in one window (eliminated pop-ups)
- **Depth-loop engine**: Stress at multiple depths, enabling:
  - Iso-surfaces (3D stress contours)
  - Vertical slices
  - Horizontal slices at arbitrary depths
- **ISC earthquake catalog integration**: Plot global seismicity directly
- **USGS finite fault model integration**: Import published slip models
- **Interactive source/receiver building**: Build directly on the map
- **3D seismicity correlation**: Test whether aftershocks fall in stress-increase zones

### 5.7 Additional Capabilities

- **Earthquake-earthquake interaction**: How one earthquake promotes/inhibits the next
- **Earthquake sequence analysis**: Cumulative stress from multiple events
- **Fault-magma interaction**: How fault slip affects nearby magma chambers
- **Tectonic loading**: Apply background tectonic strain
- **Sensitivity testing**: Vary friction, depth, geometry parameters

---

## 6. MATLAB Dependencies

### Coulomb 3.x

- **MATLAB** (base): Core computation and GUI
- **MATLAB GUI framework**: Uses GUIDE-based figure windows with menus and interactive controls
- Uses standard MATLAB plotting functions (figure, axes, patch, contour, quiver, etc.)
- No specific toolbox requirements documented for Coulomb 3.3/3.4

### Coulomb 4.0

Requires three MATLAB Toolboxes:

| Toolbox | Purpose |
|---------|---------|
| **Mapping Toolbox** | Geographic projections, map display, coastlines, coordinate transformations |
| **Image Processing Toolbox** | Image manipulation for overlays and visualization |
| **Curve Fitting Toolbox** | Data fitting, interpolation, surface fitting |

### MATLAB-Specific Features Used

- MATLAB GUI system (GUIDE / App Designer)
- MATLAB figure system (`.fig` files)
- Matrix operations (core computation)
- File I/O (`fopen`, `fscanf`, `fprintf`, text parsing)
- Plotting: `figure`, `axes`, `patch`, `surf`, `contourf`, `quiver`, `plot3`
- Color mapping: `colormap`, `colorbar`, `caxis`
- Struct/cell array data structures
- `.mat` file save/load (binary workspace files)
- Interactive callbacks (button clicks, menu selections)

---

## 7. Input File Formats

### Primary: `.inp` Format (ASCII Text)

The `.inp` file is the core input format. Structure:

```
[Header lines - title/comments]
#reg1=  0  #reg2=  0  #fixed=  N  sym=  X
 PR1=       PR2=       DEPTH=
  E1=        E2=       XSYM=       YSYM=
FRIC=
  S1DR=  S1DP=  S1IN=  S1GD=
  S2DR=  S2DP=  S2IN=  S2GD=
  S3DR=  S3DP=  S3IN=  S3GD=

  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot
  xxx xxxxxxxxx xxxxxxxxx xxxxxxxxx xxxxxxxxx xxx xxxxxxx xxxxxxx xxxxx xxxxx xxxxx
  [... source fault elements ...]

  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot
  [... receiver fault elements ...]

  [Grid parameters]
```

#### Header Parameters

| Parameter | Description |
|-----------|-------------|
| `#reg1`, `#reg2` | Region identifiers |
| `#fixed` | Number of fixed (source) fault elements |
| `sym` | Symmetry flag |
| `PR1`, `PR2` | Poisson's ratio for regions 1 and 2 (typically 0.25) |
| `DEPTH` | Calculation depth (km) |
| `E1`, `E2` | Young's modulus for regions 1 and 2 (typically 8.0e+05 bars = 80 GPa) |
| `XSYM`, `YSYM` | Symmetry axis positions |
| `FRIC` | Coefficient of friction (effective, mu') |
| `S1DR/S1DP/S1IN/S1GD` | Principal stress 1: direction, dip, intensity, gradient |
| `S2DR/S2DP/S2IN/S2GD` | Principal stress 2: direction, dip, intensity, gradient |
| `S3DR/S3DP/S3IN/S3GD` | Principal stress 3: direction, dip, intensity, gradient |

#### Fault Element Fields

| Field | Description | Units |
|-------|-------------|-------|
| `X-start` | Starting X coordinate | km |
| `Y-start` | Starting Y coordinate | km |
| `X-fin` | Ending X coordinate | km |
| `Y-fin` | Ending Y coordinate | km |
| `Kode` | Fault type code (100=source, 200=receiver) | integer |
| `rt.lat` | Right-lateral slip (positive) / Left-lateral (negative) | m |
| `reverse` | Reverse slip (positive) / Normal (negative) | m |
| `dip` | Dip angle (always positive) | degrees |
| `top` | Top depth of fault | km |
| `bot` | Bottom depth of fault | km |

#### Slip Format Variants

Coulomb supports multiple input formats for source specification:

| Format | Description |
|--------|-------------|
| `Source_Patch` | strike, rake, dip, length_km, width_km, lon, lat, depth_km, slip_m [, tensile_m] |
| `Source_WC` | Wells-Coppersmith scaling from magnitude |
| `Source_FM` | From focal mechanism data |
| `Receiver` | Receiver fault specification |
| `Receiver_Horizontal_Profile` | Horizontal profile receiver |

### Secondary: `.mat` Format (MATLAB Binary)

- MATLAB workspace file containing all model data
- Can include fault geometries, earthquake catalogs, and map overlays
- Not human-readable, but faster to load

### Additional Input Sources

- **CMT catalogs**: Import focal mechanisms (Global CMT format)
- **USGS finite fault models**: Published slip distribution models
- **ISC earthquake catalogs** (Coulomb 4.0): Direct integration
- **GPS observation files**: lon/lat/displacement vectors

---

## 8. Output Formats and Visualizations

### Output Files

| File | Contents |
|------|----------|
| `dcff.cou` | Coulomb failure stress change grid (all stress components) |
| `dcff_section.cou` | Cross-section Coulomb stress data |
| `dilatation_section.cou` | Cross-sectional dilatation data |
| `Strain.cou` | Strain tensor components (xx, yy, zz, yz, xz, xy) |
| `coulomb_out.dat` | Primary stress change grid matrix |
| `gmt_fault_surface.dat` | Source and receiver fault traces at surface |
| `gmt_fault_map_proj.dat` | Projected fault surface geometry |
| `gmt_fault_calc_dep.dat` | Fault plane intersection at target depth |
| `Cross_section.dat` | Cross-section parameters and data |
| `GPS_output.csv` | Observed vs. modeled GPS displacements |
| `Focal_mech_stress_output.csv` | Stress values at focal mechanism locations |

### Visualization Outputs

| Type | Format | Description |
|------|--------|-------------|
| Vector graphics | `.pdf` | Publication-quality, editable |
| MATLAB figures | `.fig` | Interactive 3D, rotatable |
| Stress maps | On-screen | Color-filled contour maps |
| Cross-sections | On-screen | Vertical depth slices |
| Displacement vectors | On-screen | GPS-style arrows |

### CSV Export Structure (from Coulomb 3.4)

The CSV output contains columns including:
- Column 2: X-center (km or UTM)
- Column 3: Y-center (km or UTM)
- Column 4: Z-center (depth, km)
- Column 6: Strike angle (degrees)
- Column 7: Dip angle (degrees)
- Column 20: Coulomb stress transferred (bars)

(With a 2-line header that must be skipped when parsing)

---

## 9. Algorithms and Mathematical Models

### 9.1 Core: Okada (1992) Elastic Dislocation Solution

Coulomb uses the **Okada (1992)** analytical solution for a rectangular dislocation in a homogeneous, isotropic, elastic half-space.

**Reference**: Okada, Y. (1992). Internal deformation due to shear and tensile faults in a half-space. Bulletin of the Seismological Society of America, 82(2), 1018-1040.

**What it computes**:
- Complete 3D displacement field (u_x, u_y, u_z) at any point in the half-space
- Complete strain tensor (6 independent components) via spatial differentiation
- Complete stress tensor via Hooke's law for isotropic elastic media

**Input to Okada**:
- Fault geometry: length, width, strike, dip, depth of upper edge
- Slip vector: strike-slip component, dip-slip component, tensile component
- Elastic parameters: Poisson's ratio (nu), typically 0.25
- Observer point coordinates: (x, y, z)

**Key properties**:
- Analytical closed-form solution (no numerical approximation)
- Linear: solutions can be superposed for multiple fault patches
- Half-space: flat free surface, infinite depth, homogeneous elastic properties
- Handles both shear faults (earthquake model) and tensile faults (dike/intrusion model)

**Original Fortran code**: DC3D by Okada, hosted at NIED (National Research Institute for Earth Science and Disaster Resilience, Japan)
- http://www.bosai.go.jp/e/dc3d.html

### 9.2 Earlier: Okada (1985)

Surface-only deformation formulas (subset of 1992 solution):
- Okada, Y. (1985). Surface deformation due to shear and tensile faults in a half-space. Bulletin of the Seismological Society of America, 75(4), 1135-1154.

### 9.3 Coulomb Failure Criterion

```
delta_CFS = delta_tau + mu' * delta_sigma_n
```

Where:
- `delta_tau` = change in shear stress resolved on receiver plane in the rake direction
- `delta_sigma_n` = change in normal stress on receiver plane (positive = unclamping)
- `mu'` = effective friction coefficient = mu * (1 - B)
- `mu` = coefficient of friction (0.0 - 0.8)
- `B` = Skempton's pore pressure coefficient (0 - 1)

Typical default: `mu' = 0.4`

### 9.4 Optimally Oriented Planes (OOPs)

For computing stress on optimally oriented faults:
1. Specify the background (regional/tectonic) stress field (3 principal stresses with orientations)
2. Add the earthquake-induced stress perturbation
3. Find the fault orientation that maximizes delta_CFS under the combined stress field
4. Uses Mohr-Coulomb failure criterion to determine optimal orientation

### 9.5 Elastic Half-Space Assumptions

| Parameter | Typical Value |
|-----------|---------------|
| Poisson's ratio (nu) | 0.25 |
| Young's modulus (E) | 80 GPa (8 x 10^5 bars) |
| Shear modulus (G) | 32 GPa (3.2 x 10^5 bars) |
| Medium | Homogeneous, isotropic, elastic |
| Surface | Flat, free surface (no topography) |
| Geometry | Half-space (infinite below surface) |

### 9.6 Stress Units

Coulomb works in **bars** (1 bar = 10^5 Pa = 0.1 MPa).

Typical stress changes of interest: 0.1 - 10 bars (where even 0.1 bar ~ 0.01 MPa has been shown to affect seismicity rates).

### 9.7 Coordinate System

- **Local Cartesian**: X (East), Y (North), Z (Up/positive downward for depth)
- **Geographic**: Longitude, Latitude for map display
- Fault geometry uses right-hand rule conventions
- Strike measured clockwise from North (0-360 degrees)
- Dip measured from horizontal (0-90 degrees, always positive)
- Rake measured in the fault plane from strike direction (-180 to 180 degrees)

---

## 10. Existing Non-MATLAB Alternatives and Ports

### 10.1 Python Alternatives

#### elastic_stresses_py (Kathryn Materna)
- **URL**: https://github.com/kmaterna/elastic_stresses_py
- **License**: MIT
- **Language**: Python 3.9+
- **Status**: Active, well-maintained
- **Capabilities**:
  - Reads Coulomb `.inp` files directly
  - Computes displacements, strains, stresses, Coulomb failure stress
  - Uses Okada (1992) formulation
  - Outputs text files, GRD files, PNG plots
  - Supports GPS point files, strain/stress point files
  - Reproduces Coulomb outputs on test cases
- **Dependencies**: gfortran, gcc, NumPy, Matplotlib, PyGMT, cutde, tectonic_utils
- **Limitations**: No GUI, no interactive fault building, subset of Coulomb's visualization features
- **Assessment**: Best Python alternative -- "mini-Coulomb" as self-described

#### OkadaPy
- **URL**: https://github.com/hemmelig/OkadaPy
- **License**: GPLv3
- **Language**: Python + C (63.8% C, 36.2% Python)
- **Status**: Very new (v0.0.1, December 2024)
- **Capabilities**:
  - Displacement, strain, and stress field computation
  - Finite rectangular and point sources
  - Efficient C-based core
- **Dependencies**: Python 3.11+, C compiler
- **Limitations**: Early stage, no Coulomb stress calculation wrapper, no file format compatibility
- **Assessment**: Low-level Okada implementation, not a Coulomb replacement

#### Pyrocko
- **URL**: https://pyrocko.org/
- **License**: GPLv3
- **Language**: Python
- **Status**: Mature, actively maintained
- **Capabilities**:
  - Okada (1992) solution for displacement and stress
  - Coulomb failure stress calculation
  - Green's function database management
  - Seismic source characterization
  - InSAR and GPS modeling
  - Integration with PSGRN/PSCMP for viscoelastic models
- **Assessment**: Full seismology toolbox -- Coulomb stress is one of many capabilities

### 10.2 Fortran Alternatives

#### PSGRN/PSCMP (Rongjiang Wang)
- **URL**: https://github.com/RongjiangWang/PSGRN-PSCMP_2020
- **License**: Not specified
- **Language**: Fortran
- **Capabilities**:
  - Co-seismic AND post-seismic deformation (viscoelastic)
  - Layered half-space (not just homogeneous)
  - Gravity and geoid changes
  - Can produce same Coulomb stress maps as Coulomb 3.4
- **Assessment**: More physically sophisticated (viscoelastic, layered), but no GUI, harder to use

#### DC3D (Okada's original)
- **URL**: http://www.bosai.go.jp/e/dc3d.html
- **Language**: Fortran
- **Capabilities**: The original Okada dislocation routines
- **Assessment**: Core computation only, no wrapper or visualization

### 10.3 Mixed Language Alternatives

#### CoulombAnalysis / AutoCoulomb (Wang et al., 2021)
- **URL**: https://github.com/jjwangw/CoulombAnalysis
- **License**: Not specified
- **Language**: Fortran (43%), MATLAB (33%), Shell (23%)
- **Publication**: Wang et al. (2021), Seismological Research Letters, 92(4), 2591
- **Capabilities**:
  - Automated batch processing of Coulomb stress changes
  - Receiver faults with any orientation
  - Non-vertical profiles with any trend
  - More flexible than Coulomb 3.4 for automated workflows
- **Assessment**: Addresses automation limitations of Coulomb, but complex setup

### 10.4 MATLAB Add-ons

#### CutAndDisplace
- **URL**: https://github.com/Timmmdavis/CutAndDisplace
- **Language**: MATLAB
- **Capabilities**: Boundary Element code for faults, can calculate Coulomb stress
- **Assessment**: Different approach (BEM vs. analytical), more general but more complex

#### DMODELS (USGS)
- **Language**: MATLAB
- **Capabilities**: Crustal deformation near faults and volcanic centers
- **Assessment**: Complementary to Coulomb, focuses on volcanic sources

### 10.5 Summary Comparison

| Tool | Language | GUI | Reads .inp | CFS | Vis | Maturity | License |
|------|----------|-----|-----------|-----|-----|----------|---------|
| **Coulomb 3.4** | MATLAB | Yes | Yes | Yes | Rich | High | USGS/Public |
| **Coulomb 4.0** | MATLAB | Yes | Yes | Yes | Rich+ | Medium | Open Source |
| **elastic_stresses_py** | Python | No | Yes | Yes | Basic | Medium | MIT |
| **OkadaPy** | Python/C | No | No | No | Basic | Low | GPLv3 |
| **Pyrocko** | Python | No | No | Yes | Medium | High | GPLv3 |
| **PSGRN/PSCMP** | Fortran | No | No | Yes | None | High | -- |
| **AutoCoulomb** | Fortran/MATLAB | No | Yes | Yes | Basic | Medium | -- |

---

## 11. License

### Coulomb 3.x (USGS)

USGS software is generally released into the **public domain** under U.S. government work doctrine. The USGS distributes software under Creative Commons CC0 or similar public domain dedication. However, Coulomb 3.x requires MATLAB (proprietary, MathWorks license) to run.

Key points:
- The Coulomb MATLAB source code itself is public domain (USGS government work)
- Users need a valid MATLAB license (commercial software)
- Coulomb 4.0 requires additional toolbox licenses (Mapping, Image Processing, Curve Fitting)
- No formal open-source license file (like MIT or GPL) has been identified for the USGS versions

### Coulomb 4.0 (Temblor / Tohoku University)

Described as "open source" but the Coulomb 4.0 GitHub repositories (`Coulomb_ver4`, `Coulomb_Update`) do not contain a standard OSS license file (e.g., MIT, GPL, Apache). Given that Ross Stein moved from USGS to Temblor, Inc. (a private company), the licensing may differ from the USGS public domain approach.

**Practical implication**: Treat upstream Coulomb code as license-uncertain for derivative coding purposes. A strict clean-room reimplementation is required: use published equations/specifications and black-box output comparison only. Do not port MATLAB code line-by-line.

---

## 12. Key References

### Software Documentation

1. Toda, S., Stein, R.S., Sevilgen, V., and Lin, J. (2011). Coulomb 3.3 Graphic-rich deformation and stress-change software for earthquake, tectonic, and volcano research and teaching -- User guide. U.S. Geological Survey Open-File Report 2011-1060, 63 p.

### Foundational Papers

2. Okada, Y. (1992). Internal deformation due to shear and tensile faults in a half-space. Bulletin of the Seismological Society of America, 82(2), 1018-1040.

3. Okada, Y. (1985). Surface deformation due to shear and tensile faults in a half-space. Bulletin of the Seismological Society of America, 75(4), 1135-1154.

4. King, G.C.P., Stein, R.S., and Lin, J. (1994). Static stress changes and the triggering of earthquakes. Bulletin of the Seismological Society of America, 84, 935-953.

5. Stein, R.S. (1999). The role of stress transfer in earthquake occurrence. Nature, 402, 605-609.

### Alternative Tool Papers

6. Wang, R., Lorenzo-Martin, F., and Roth, F. (2006). PSGRN/PSCMP -- a new code for calculating co- and post-seismic deformation, geoid and gravity changes based on the viscoelastic-gravitational dislocation theory. Computers & Geosciences, 32, 527-541.

7. Wang, J., Xu, C., Freymueller, J.T., Wen, Y., and Xiao, Z. (2021). AutoCoulomb: An automated configurable program to calculate Coulomb stress changes on receiver faults with any orientation. Seismological Research Letters, 92(4), 2591.

---

## 13. Summary of Key Findings for Project Planning

### What Makes Coulomb Unique

1. **Interactive GUI** for building and exploring fault models -- no other tool matches this
2. **Integrated visualization** with publication-quality output
3. **Earthquake catalog integration** (ISC, USGS finite faults)
4. **Broad user base** (10,000+ downloads, 3,000+ citations)
5. **Well-documented** (63-page USGS user guide)

### Key Technical Constraints of the MATLAB Version

1. **Requires MATLAB license** (~$2,000+ for academic, ~$5,000+ commercial)
2. **Coulomb 4.0 requires 3 additional toolboxes** (~$1,000-3,000 each)
3. **No command-line / batch processing** (GUI-centric)
4. **Homogeneous elastic half-space only** (no layered models, no viscoelasticity)
5. **Limited automation** for large-scale studies
6. **Platform-dependent GUI** (MATLAB GUI framework, not modern web-based)
7. **No version control** of the official source code (no public git repo)

### Gaps Not Addressed by Existing Alternatives

No existing tool provides ALL of:
- Interactive GUI for model building
- Coulomb stress calculation on specified and optimally oriented faults
- Integrated earthquake catalog display
- GPS displacement comparison
- Cross-section and 3D visualization
- Coulomb `.inp` file compatibility
- Free/open-source with no proprietary dependencies

This represents the opportunity space for a new implementation.

---

## Sources

- [Coulomb 3 - USGS](https://www.usgs.gov/node/279387)
- [Coulomb 3.3 User Guide - USGS Open-File Report 2011-1060](https://pubs.usgs.gov/of/2011/1060/)
- [Coulomb Software and User Guide - Temblor.net](https://temblor.net/coulomb/)
- [Introducing Coulomb 4.0 - Temblor.net](https://temblor.net/earthquake-insights/introducing-coulomb-4-0-enhanced-stress-interaction-and-deformation-software-for-research-and-teaching-17066/)
- [Coulomb 4.0 (Coulomb_ver4) - GitHub](https://github.com/YoshKae/Coulomb_ver4)
- [Coulomb 4.0 (Coulomb_Update) - GitHub](https://github.com/YoshKae/Coulomb_Update)
- [elastic_stresses_py - GitHub](https://github.com/kmaterna/elastic_stresses_py)
- [CoulombAnalysis / AutoCoulomb - GitHub](https://github.com/jjwangw/CoulombAnalysis)
- [OkadaPy - GitHub](https://github.com/hemmelig/OkadaPy)
- [Pyrocko - okada module](https://pyrocko.org/docs/current/library/reference/pyrocko.modelling.okada.html)
- [PSGRN/PSCMP 2020 - GitHub](https://github.com/RongjiangWang/PSGRN-PSCMP_2020)
- [coulomb2gmt - GitHub](https://github.com/demanasta/coulomb2gmt)
- [3D-faults for Coulomb 3.4 - GitHub](https://github.com/ZoeMildon/3D-faults)
- [3D-Faults-stress-plotter - GitHub](https://github.com/MDiercks/3D-Faults-stress-plotter)
- [DC3D Okada Fortran - NIED](https://www.bosai.go.jp/e/dc3d.html)
- [Okada MATLAB implementation - MathWorks File Exchange](https://www.mathworks.com/matlabcentral/fileexchange/25982-okada-surface-deformation-due-to-a-finite-rectangular-source)
- [USGS Software Distribution Policy](https://www.usgs.gov/products/software/software-management/distribution-usgs-code)
- [Coulomb stress transfer - Wikipedia](https://en.wikipedia.org/wiki/Coulomb_stress_transfer)
