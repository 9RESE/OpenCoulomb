# Arc42 § 3 — System Context

## 3.1 Context Diagram

```
                   ┌─────────────────────────────────┐
  .inp file ──────►│                                 │──► .csv / .dat / .cou
                   │          OpenCoulomb            │
  CLI flags ──────►│   (library + opencoulomb CLI)   │──► PNG / PDF figures
                   │                                 │
  Python API ─────►│                                 │──► CoulombResult object
                   └─────────────────────────────────┘
                              │           ▲
                    NumPy /   │           │  SciPy (scipy.special)
                    SciPy     ▼           │
                         Vectorised Okada engine
```

## 3.2 Users and Use Cases

### Primary Users

**Research seismologist**
- Receives or produces a Coulomb 3.4 `.inp` file describing an earthquake source model.
- Runs `opencoulomb compute model.inp` to generate CFS maps.
- Runs `opencoulomb plot model.inp` to produce publication-quality figures.
- Compares results to original Coulomb 3.4 MATLAB output.

**Research software engineer / script author**
- Imports `opencoulomb` as a Python library inside a Jupyter notebook or analysis pipeline.
- Calls `read_inp()` → `compute_grid()` → inspects `CoulombResult.cfs` NumPy array.
- Chains multiple `.inp` files for systematic parameter studies.

**Instructor / student**
- Runs `opencoulomb info model.inp` and `opencoulomb validate model.inp` to inspect and check models before computing.

### Indirect Stakeholders

**CI / CD system**
- Invokes the test suite (`pytest`) and coverage check against every pull request.
- Publishes wheel to PyPI on tagged release.

## 3.3 External Systems and Interfaces

| External System | Interface | Direction | Notes |
|----------------|-----------|-----------|-------|
| **Coulomb 3.4 .inp files** | File format (text) | In | Created by MATLAB Coulomb 3.4 or by hand |
| **PyPI** | `pip install opencoulomb` | Out | Distribution channel |
| **NumPy** | Python API + C extension | Internal | Array computation |
| **SciPy** | `scipy.special` (Okada special functions) | Internal | Used for specific edge cases |
| **Matplotlib** | Python API | Internal | All visualisation |
| **Click** | Python API | Internal | CLI argument parsing |
| **Filesystem** | POSIX / Windows paths | In/Out | Input `.inp`; output `.csv`, `.dat`, `.cou`, images |

## 3.4 What OpenCoulomb Does NOT Interface With

- MATLAB or any licensed software
- Network services or APIs (fully offline)
- Seismic catalogue databases (FDSN, IRIS)
- GIS systems (no shapefile/GeoJSON I/O in MVP)
- Databases
