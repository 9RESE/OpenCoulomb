# Arc42 § 8 — Cross-Cutting Concepts

## 8.1 Error Handling

### Exception Hierarchy

All errors are subclasses of `OpenCoulombError` (defined in `exceptions.py`):

```
OpenCoulombError
├── InputError
│   ├── ParseError          — .inp format violation; carries filename + line_number
│   └── ValidationError     — semantically invalid model (e.g. negative fault length)
├── ComputationError
│   ├── SingularityError    — observation point on Okada fault boundary
│   └── ConvergenceError    — iterative method did not converge
├── OutputError
│   └── FormatError         — unsupported or invalid output format
└── ConfigError             — invalid runtime configuration
```

### Principles

- **Never raise bare `Exception` or `RuntimeError`** — always use the typed hierarchy.
- **ParseError** attaches `filename` and `line_number` attributes for user-facing messages.
- **SingularityError** in the Okada engine is caught by the pipeline and the affected grid cell is set to `NaN`; computation continues. This matches Coulomb 3.4 behaviour.
- **CLI layer** catches `OpenCoulombError`, prints a concise message to stderr, and exits with code 1. Python tracebacks are suppressed for end users (enabled with `--debug`).

## 8.2 Logging

Logging is configured in `cli/_logging.py` and applies only when OpenCoulomb is used via the CLI. Library users get no logging by default (they configure their own logger as per Python conventions).

| Level | When used |
|-------|-----------|
| `DEBUG` | Okada call counts, grid generation details, parser state transitions |
| `INFO` | "Parsed N sources, M receivers", "Computing grid 100×100", "Wrote cfs.csv" |
| `WARNING` | Singularity encountered at (x, y); result set to NaN |
| `ERROR` | Non-fatal write failures |

Logs go to **stderr** (never stdout), so stdout can be piped to downstream tools.

CLI flags: `--verbose` sets DEBUG; `--quiet` suppresses INFO.

## 8.3 Testing Strategy

### Structure

```
tests/
├── unit/
│   ├── types/            — dataclass construction, property tests
│   ├── core/             — Okada, coordinates, stress, CFS, pipeline
│   └── io/               — parser states, writer output
├── integration/
│   ├── test_pipeline.py  — full .inp → compute → result assertions
│   └── test_cli.py       — Click test runner (CliRunner)
└── fixtures/
    └── inp_files/
        ├── synthetic/    — hand-crafted minimal .inp files
        └── real/         — 7 real Coulomb 3.4 .inp files
```

### Coverage Targets

| Module group | Target |
|-------------|--------|
| `core/` | ≥ 95% |
| `types/` | ≥ 95% |
| `io/` | ≥ 85% |
| `cli/` | ≥ 85% |
| `viz/` | ≥ 85% |
| **Overall** | **≥ 90%** |

Current: **95.77%** across 800+ tests.

### Scientific Validation Tests

The most important test class validates numerical accuracy:

- **Okada DC3D**: Strike-slip case from Okada (1992) Table 2. Expected: `ux=-8.689e-3`, `uy=-4.298e-3`, `uz=-2.747e-3`. Tolerance: `1e-10`.
- **CFS regression**: Reference outputs computed from Coulomb 3.4 on the 7 real `.inp` fixtures. Tolerance: `1e-6` bar.

### Test Isolation

- No global state in the library; each test constructs domain objects from scratch.
- The `.inp` parser is tested with both real files and synthetic edge-case files.
- CLI tests use Click's `CliRunner` (no subprocess spawning).
- Matplotlib backend set to `Agg` in `conftest.py` to prevent GUI windows during CI.

## 8.4 Immutability

All domain types (`types/`) use `@dataclass(frozen=True)` or `@dataclass(slots=True)`. This means:

- Parser produces immutable `CoulombModel` — cannot be accidentally mutated by pipeline.
- `CoulombResult` is also frozen — consumers cannot corrupt result state.
- New "modified" models are constructed via `dataclasses.replace()`.

## 8.5 Numerical Conventions

| Convention | Value |
|-----------|-------|
| Length units | kilometres (km) |
| Stress units | bar (1 bar = 0.1 MPa) |
| Depth sign | Negative downward (Okada convention: z ≤ 0 for underground points) |
| Angle convention | Strike: degrees clockwise from North; Dip: degrees from horizontal; Rake: Aki-Richards |
| Grid origin | Geographic (x = East km, y = North km) |

Physical constants are in `_constants.py` (e.g. conversion factors, default friction coefficient µ = 0.4).

## 8.6 Dependency Management

- **Runtime deps**: declared in `pyproject.toml` `[project.dependencies]`. No pinning; semver lower bounds only.
- **Dev deps**: declared in `[project.optional-dependencies] dev`. Includes pytest, coverage, ruff, mypy.
- **Lock file**: not included in the repository. Reproducibility for contributors is handled by `pip install -e ".[dev]"` against a fresh virtualenv, not a lockfile, to avoid over-constraining the dependency graph for library users.

## 8.7 Public API Surface

The stable public API consists of:

```python
# Parsing
from opencoulomb.io import read_inp, parse_inp_string

# Computation
from opencoulomb.core.pipeline import compute_grid, compute_element_cfs

# Domain types (for type annotations and result inspection)
from opencoulomb.types import CoulombModel, CoulombResult, FaultElement, GridSpec

# Exceptions
from opencoulomb.exceptions import (
    OpenCoulombError, ParseError, ValidationError, ComputationError
)
```

Internal modules (`core/okada.py`, `core/coordinates.py`, `viz/_base.py`, etc.) are implementation details and may change between minor versions.
