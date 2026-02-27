# Arc42 § 4 — Solution Strategy

## 4.1 Technology Choices

| Decision | Choice | Alternative Considered | Rationale |
|----------|--------|----------------------|-----------|
| Language | Python 3.10+ | C++, Julia | Largest scientific user base; NumPy ecosystem; easiest contribution path |
| Numerical engine | Pure NumPy (vectorized) | Fortran f2py, Cython | No compiler required at install time; sufficient performance for typical grids (see ADR-001) |
| Domain objects | Frozen dataclasses | attrs, Pydantic v2 | Zero runtime dependency; Python stdlib; slots give memory efficiency (see ADR-002) |
| `.inp` parser | State machine | pyparsing, regex-only | Robust against Coulomb 3.4 format quirks; clear state transitions (see ADR-003) |
| CLI framework | Click | argparse, Typer | Mature, widely used, composable command groups |
| Build backend | hatchling | setuptools, flit | PEP 621 native; clean `pyproject.toml`; no legacy config |
| Test framework | pytest | unittest | Standard in scientific Python; fixture composability |

## 4.2 Key Architectural Patterns

### Pipeline Pattern

The computation follows a strict linear pipeline with no feedback loops:

```
read_inp()  →  CoulombModel  →  compute_grid()  →  CoulombResult  →  writers / viz
```

Each stage is a pure function (no global mutable state). This makes individual stages independently testable and allows Python API users to enter the pipeline at any point.

### Aggregate Root

`CoulombModel` is the aggregate root of the domain model. It owns all fault elements, grid specification, material properties, and optional regional stress. The parser produces exactly one `CoulombModel`; the pipeline consumes exactly one.

### Superposition

Source faults are processed independently and their stress contributions summed (superposition principle of linear elasticity). This is the key loop inside `compute_grid()`:

```python
for fault in model.source_faults:
    # Okada → stress gradients → Hooke's law → rotate → accumulate
    total_stress += fault_stress
```

### Vectorisation

All Okada computations are NumPy-vectorized over the grid: the entire `(N, M)` observation grid is passed as arrays, producing displacement and stress arrays in a single call rather than a Python loop over grid points.

### Typed Exception Hierarchy

Errors are expressed through a domain-specific hierarchy rooted at `OpenCoulombError`, with specialised subclasses for each failure domain (`ParseError`, `ValidationError`, `ComputationError`, `OutputError`). Callers can catch at the granularity they need.

## 4.3 Key Design Decisions (Summary)

| Decision | Choice | ADR |
|----------|--------|-----|
| Okada implementation | Pure NumPy, no Fortran | [ADR-001](09-decisions/adr-001-pure-numpy-okada.md) |
| Domain objects | Frozen dataclasses with `slots=True` | [ADR-002](09-decisions/adr-002-frozen-dataclasses.md) |
| `.inp` format parser | Explicit state machine | [ADR-003](09-decisions/adr-003-state-machine-parser.md) |

## 4.4 Quality Attribute Trade-offs

| Quality | How achieved | Trade-off |
|---------|-------------|-----------|
| **Accuracy** | Validated against Okada (1992) Table 2; regression tests against Coulomb 3.4 reference outputs | — |
| **Performance** | NumPy vectorisation; grid computed in one pass | Fortran f2py would be ~5-10× faster for very large grids, but adds install complexity |
| **Maintainability** | Pure Python; frozen domain objects; high coverage | Slight verbosity of dataclass definitions vs Pydantic/attrs |
| **Portability** | No compiled extensions; universal wheel | Cannot use GPU acceleration without architectural change |
| **Compatibility** | State machine parser handles all known `.inp` variants | Parser is more complex than a simple line-by-line reader |
