# Coulomb Research Summary

**Phase 1 Consolidated Findings**
**Date**: 2026-02-27

---

## 1. What We're Replacing

**Coulomb 3.4 / 4.0** - MATLAB software by USGS (Toda, Stein, Sevilgen, Lin) for computing Coulomb failure stress changes from earthquake fault slip. The de facto standard in earthquake seismology (10,000+ downloads, 3,000+ citations).

**The problem**: Requires MATLAB ($2k-5k+) and up to 3 additional toolboxes ($3k-9k more). No free alternative provides Coulomb's full capabilities.

---

## 2. Core Capabilities to Replicate

### 2.1 Computation Engine
| Capability | Priority | Complexity |
|-----------|----------|-----------|
| Okada (1992) DC3D/DC3D0 dislocation solution | Critical | Medium - well-documented analytical solution |
| Coulomb failure stress (CFS) calculation | Critical | Low - tensor resolution + linear formula |
| Stress tensor computation (Hooke's law) | Critical | Low - standard elasticity |
| Tensor rotation (fault-local to geographic) | Critical | Low - direction cosine matrix |
| Coordinate transforms (geo <-> fault-local) | Critical | Low - rotation + translation |
| Optimally oriented planes (OOPs) | High | Medium - Mohr-Coulomb optimization |
| Displacement field computation | High | Low - direct from Okada |
| Strain tensor computation | High | Low - direct from Okada |
| Seismicity rate change (Dieterich 1994) | Medium | Medium - rate/state model |
| GPS displacement comparison | Medium | Low - vector comparison |

### 2.2 Input/Output
| Capability | Priority | Complexity |
|-----------|----------|-----------|
| Read Coulomb .inp files | Critical | Medium - fixed-format parser |
| Write .inp files | High | Low - fixed-format writer |
| Read/write .cou output files | High | Low - grid data format |
| CSV/text export | High | Low |
| Read earthquake catalogs (ISC, CMT) | Medium | Medium |
| Read USGS finite fault models | Medium | Medium |

### 2.3 Visualization
| Capability | Priority | Complexity |
|-----------|----------|-----------|
| 2D stress/strain map (color-filled contour) | Critical | Medium |
| Fault trace display (source + receiver) | Critical | Low |
| Cross-section (vertical slice) | High | Medium |
| Displacement vector arrows | High | Low |
| 3D fault geometry display | Medium | High |
| Earthquake overlay (catalog seismicity) | Medium | Medium |
| Publication-quality output (PDF/SVG) | Medium | Medium |

### 2.4 Interactive Features
| Capability | Priority | Complexity |
|-----------|----------|-----------|
| GUI for model building/exploration | Critical | High |
| Interactive fault editing | High | High |
| Parameter sensitivity testing | Medium | Low |
| Batch/scripting mode | High | Medium |

---

## 3. Technical Architecture of Coulomb 3.4

### 3.1 File Count
- **242 MATLAB .m files** total
- ~11 files: Okada DC3D engine (translated from Fortran)
- ~25 files: Core computation (stress, strain, coordinate transforms)
- ~60 files: GUI windows and controls
- ~35 files: Plugins
- ~111 files: Utilities, I/O, visualization helpers

### 3.2 Core Algorithm Pipeline
```
1. Parse .inp file -> ELEMENT array + GRID params + material properties
2. For each grid point (NXINC x NYINC):
   3. For each source fault element:
      a. coord_conversion(): geographic -> fault-local coords
      b. Okada_DC3D(): displacement + 9 gradient components
      c. Hooke's law: gradients -> stress tensor (6 components)
      d. tensor_trans(): fault-local -> geographic stress tensor
      e. Accumulate (superposition)
4. For CFS visualization:
   a. calc_coulomb(): resolve stress onto receiver plane
   b. CFS = shear + friction * normal
5. Visualize
```

### 3.3 Key Data Structures

**DC3D Matrix** (N_CELL x 14):
```
Cols 1-2:  Grid position (km)
Cols 3-5:  Fault-local position (x, y, z)
Cols 6-8:  Displacement (ux, uy, uz) in meters
Cols 9-14: Stress tensor (sxx, syy, szz, syz, sxz, sxy) in bars
```

**ELEMENT Matrix** (NUM x 9):
```
Cols 1-4: Fault trace endpoints (xstart, ystart, xfin, yfin) in km
Col 5:    Right-lateral slip (m) or tensile opening
Col 6:    Reverse slip (m) or other per KODE
Col 7:    Dip angle (degrees)
Cols 8-9: Top and bottom depth (km)
```

**KODE Values**: 100=standard fault, 200=tensile+RL, 300=tensile+reverse, 400=point source, 500=tensile+inflation

### 3.4 Key Constants
| Parameter | Default | Unit |
|-----------|---------|------|
| Poisson's ratio | 0.25 | - |
| Young's modulus | 8.0e5 | bar (80 GPa) |
| Friction coefficient | 0.4 | - |
| Stress unit | bar | 1 bar = 0.1 MPa |
| Distance unit | km | |
| Slip unit | m | |

### 3.5 Coordinate Conventions
- X = East, Y = North, Z = Up (depth positive downward)
- Strike: clockwise from North (0-360)
- Dip: from horizontal (0-90, always positive)
- Rake: in fault plane from strike direction (-180 to 180)
- Right-lateral slip: POSITIVE in .inp files (NEGATIVE internally in Okada convention - code flips sign)
- Reverse slip: POSITIVE

---

## 4. MATLAB Dependencies to Replace

### 4.1 Computation (Straightforward)
| MATLAB Feature | Replacement |
|---------------|-------------|
| Matrix operations | NumPy / Eigen / standard array libs |
| Complex math | Standard math libraries |
| File I/O (fopen/fscanf/fprintf) | Standard file I/O |
| Struct arrays | Classes / named tuples / dataclasses |

### 4.2 Visualization (Moderate)
| MATLAB Feature | Replacement Options |
|---------------|-------------------|
| figure/axes/plot | Matplotlib / Plotly / VTK / web-based |
| contourf (filled contours) | Matplotlib / D3.js / deck.gl |
| quiver (vector arrows) | Matplotlib / custom rendering |
| patch (3D surfaces) | VTK / Three.js / Plotly |
| colormap/colorbar | Built into most viz libs |
| PDF export | Cairo / SVG export / ReportLab |
| .fig interactive figures | Web-based interactivity |

### 4.3 GUI (Most Complex)
| MATLAB Feature | Replacement Options |
|---------------|-------------------|
| GUIDE/App Designer | Qt / Electron / Web (React/Vue) / PyQt |
| Interactive callbacks | Event-driven UI framework |
| Menu system | Framework-native menus |
| Dialog boxes | Framework-native dialogs |

### 4.4 Toolbox Functions (Coulomb 4.0 only)
| Toolbox | Functions Used | Replacement |
|---------|--------------|-------------|
| Mapping | Geographic projections, coastlines | Proj / GeoPandas / Leaflet / Mapbox |
| Image Processing | Image overlay | Pillow / OpenCV |
| Curve Fitting | Interpolation, surface fitting | SciPy / custom |

---

## 5. Existing Code to Leverage

### 5.1 Okada Implementation Sources (Available for Reference)
| Source | Language | License | Notes |
|--------|----------|---------|-------|
| DC3D original (NIED) | Fortran 77 | Public | The reference implementation |
| DC3D.f90 | Fortran 90 | Unknown | Modern Fortran rewrite |
| Coulomb 3.4 okada_source_conversion/ | MATLAB | USGS/Public Domain | Direct Fortran translation |
| elastic_stresses_py (cutde) | Python | MIT | Uses compiled C for speed |
| OkadaPy | Python/C (64% C) | GPLv3 | Efficient C core |
| okada_wrapper | Python (ctypes) | MIT | Wraps Fortran via ctypes |

### 5.2 Coulomb-Equivalent Code
| Source | What to Leverage |
|--------|-----------------|
| elastic_stresses_py | .inp parser, CFS calculation, output format, test cases |
| CoulombAnalysis | Automated batch processing patterns |
| coulomb2gmt | Output format specifications |

---

## 6. Gap Analysis: What No Existing Tool Provides

No single free tool provides ALL of:
1. Interactive GUI for fault model building
2. Coulomb stress on specified AND optimally oriented faults
3. Earthquake catalog integration (ISC, USGS, CMT)
4. GPS displacement comparison
5. Cross-section AND 3D visualization
6. Coulomb .inp file compatibility
7. Publication-quality output
8. No proprietary dependencies

This is the value proposition of our standalone implementation.

---

## 7. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Okada implementation numerical accuracy | High | Validate against Coulomb 3.4 outputs + original Fortran DC3D |
| GUI development complexity | High | Start CLI-first, add GUI incrementally; consider web-based UI |
| .inp format parsing edge cases | Medium | Test against all example .inp files from Coulomb 3.4 |
| Performance (Python vs MATLAB) | Medium | NumPy vectorization; C extension for Okada if needed |
| Visualization matching Coulomb quality | Medium | Use established viz libraries (Matplotlib/Plotly) |
| Scope creep (Coulomb 4.0 features) | Medium | Focus on Coulomb 3.4 parity first |

---

## 8. Recommendations for Phase 2 (Design)

1. **Target Coulomb 3.4 feature parity first** - it's the most widely used version and doesn't require extra toolbox features
2. **Python is the natural choice** - NumPy for computation, Matplotlib for viz, rich ecosystem, free, cross-platform
3. **CLI-first architecture** - scriptable computation engine, then add GUI
4. **Web-based GUI** - more portable than Qt/Tk, enables remote use
5. **Validate against Coulomb 3.4** - use the example .inp files and known outputs as test suite
6. **Consider wrapping existing Fortran DC3D** via ctypes/f2py for maximum numerical fidelity
7. **Read elastic_stresses_py carefully** - it's the closest existing work and MIT-licensed

---

## Sources

### Official Coulomb
- [USGS Coulomb 3 Page](https://www.usgs.gov/node/279387)
- [Coulomb User Guide (USGS OFR 2011-1060)](https://pubs.usgs.gov/of/2011/1060/)
- [Temblor.net Coulomb Portal](https://temblor.net/coulomb/)
- [Coulomb 4.0 GitHub (ver4)](https://github.com/YoshKae/Coulomb_ver4)
- [Coulomb 4.0 GitHub (Update)](https://github.com/YoshKae/Coulomb_Update)
- [Coulomb 3.4 Download](https://coulomb.s3.us-west-2.amazonaws.com/downloads/coulomb3402.zip)

### Academic Papers
- Okada (1992) - Core algorithm - [DOI](https://doi.org/10.1785/BSSA0820021018)
- King, Stein & Lin (1994) - Coulomb stress transfer theory - [DOI](https://doi.org/10.1785/BSSA0840030935)
- Toda et al. (2005) - Rate/state seismicity model - [DOI](https://doi.org/10.1029/2004JB003415)
- Toda et al. (2011) - Coulomb 3.3 User Guide - [USGS](https://pubs.usgs.gov/of/2011/1060/)

### Alternative Implementations
- [elastic_stresses_py (PyCoulomb)](https://github.com/kmaterna/elastic_stresses_py) - MIT, Python
- [OkadaPy](https://github.com/hemmelig/OkadaPy) - GPLv3, Python/C
- [okada_wrapper](https://github.com/tbenthompson/okada_wrapper) - MIT, Python
- [Pyrocko](https://pyrocko.org/) - GPLv3, Python
- [DC3D Fortran (NIED)](https://www.bosai.go.jp/e/dc3d.html) - Original Okada code
- [DC3D.f90](https://github.com/hydrocoast/DC3D.f90) - Modern Fortran rewrite
- [CoulombAnalysis](https://github.com/jjwangw/CoulombAnalysis) - Fortran/MATLAB
- [PSGRN/PSCMP](https://github.com/RongjiangWang/PSGRN-PSCMP_2020) - Fortran
