# Arc42 § 1 — Introduction and Goals

## 1.1 Purpose

OpenCoulomb is a standalone Python library and CLI that reproduces the Coulomb failure stress (CFS) computation workflow of the USGS **Coulomb 3.4** MATLAB package. It enables seismologists and geophysicists to model static stress transfer from earthquake sources onto receiver faults without a MATLAB license.

The core scientific question answered by OpenCoulomb: *does a slip event on one fault increase or decrease the likelihood of future earthquakes on nearby faults?* A positive ΔCFS (> ~0.1 bar) is widely associated with increased seismic hazard.

## 1.2 Quality Goals

| Priority | Goal | Metric |
|----------|------|--------|
| 1 | **Scientific accuracy** | CFS values ≤ 1 × 10⁻⁶ bar vs Coulomb 3.4 reference; Okada displacements ≤ 1 × 10⁻¹⁰ vs Okada (1992) Table 2 |
| 2 | **Numerical correctness** | 91% test coverage across 1271 tests |
| 3 | **Coulomb 3.4 compatibility** | Reads all real-world `.inp` files produced by Coulomb 3.4 |
| 4 | **Performance** | 100 × 100 grid + 10 source faults < 10 s on a modern laptop |
| 5 | **Installability** | Pure Python wheel; `pip install opencoulomb` with no Fortran compiler required |

## 1.3 Stakeholders

| Stakeholder | Role | Primary Interest |
|-------------|------|-----------------|
| Seismologists / geophysicists | End users | Reproduce and extend Coulomb 3.4 analyses |
| MATLAB-free research groups | End users | Open-source replacement without licensing cost |
| Research software engineers | Contributors | Clean, testable Python codebase |
| Package maintainers / CI | Ops | Reproducible builds, PyPI releases, test suite |
| Scientific Python ecosystem | Dependency consumers | Stable public API for downstream integration |

## 1.4 Scope

**In scope (Phases A–E, v0.1.0):**
- Parse Coulomb 3.4 `.inp` files (all known variants)
- Vectorized Okada (1992) DC3D / DC3D0 engine
- Coulomb failure stress computation on horizontal grids and cross-sections
- Optimal Orientation of Planes (OOPs)
- Visualization (map view, cross-section, displacement)
- Output formats: `.csv`, `.dat`, `.cou` (Coulomb-compatible)
- CLI commands: `compute`, `plot`, `info`, `validate`, `convert`

**In scope (Phases F–H, v0.2.0 — Coulomb 4.0 features):**
- 3D depth-loop volume grid CFS computation
- Scaling relations (Wells & Coppersmith 1994, Blaser et al. 2010)
- Slip tapering (cosine, linear, elliptical) with fault subdivision
- Strain tensor output alongside stress
- USGS finite fault import from ComCat API
- ISC/USGS earthquake catalog queries via ObsPy FDSN
- Beachball focal mechanism visualization
- GPS displacement comparison with misfit statistics
- 3D volume visualization (slices, cross-sections, animated GIF)
- CLI commands: `scale`, `fetch`, `catalog`; extended `compute` and `plot`

**Out of scope:**
- Dynamic (time-dependent) Coulomb stress
- Poroelastic / viscoelastic relaxation
- GUI (MATLAB-style interactive interface)
