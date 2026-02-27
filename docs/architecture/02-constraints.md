# Arc42 § 2 — Constraints

## 2.1 Technical Constraints

| Constraint | Rationale |
|-----------|-----------|
| **Python 3.10+** | `match` statements, `X \| Y` union types, `slots=True` dataclasses are used throughout. Lower versions are excluded. |
| **Pure Python wheel** | No Fortran (f2py) compilation step. The Okada engine is implemented in NumPy. This ensures `pip install` works on all platforms without a compiler toolchain. |
| **NumPy / SciPy / Matplotlib** | Standard scientific Python stack. These are the only non-stdlib runtime dependencies. |
| **No MATLAB dependency** | The entire purpose of the project is to eliminate the MATLAB requirement. No `.m` files or MATLAB Engine calls are permitted. |
| **`.inp` format fidelity** | The parser must accept files produced by Coulomb 3.4 without modification. Format quirks (long-dash separators, `.NNN` floats, `XSYM`/`YSYM` aliases) must be handled. |
| **Immutable domain objects** | All `types/` dataclasses use `frozen=True` (or `slots=True` on Python 3.10+ which implies mutability guard). Business logic must not mutate parsed model state. |
| **src layout** | Package lives in `src/opencoulomb/`. This prevents accidental import of the development tree and is required by hatchling. |
| **hatchling build backend** | PEP 621 compliant `pyproject.toml`. No `setup.py` or `setup.cfg`. |

## 2.2 Organisational Constraints

| Constraint | Rationale |
|-----------|-----------|
| **Apache 2.0 licence** | Chosen for compatibility with the scientific Python ecosystem. All dependencies must be licence-compatible (NumPy: BSD-3, SciPy: BSD-3, Matplotlib: PSF, Click: BSD-3). |
| **Test coverage ≥ 90% overall** | Core modules require ≥ 95%; I/O, CLI, and viz ≥ 85%. Coverage is enforced in CI. |
| **No backwards-incompatible changes to public API without a major version bump** | Downstream scripts that call `opencoulomb.io.read_inp()` or `opencoulomb.core.pipeline.compute_grid()` must continue to work. |
| **Reproducible results** | Given identical `.inp` input, outputs must be bit-identical across platforms and Python versions (within IEEE 754 double precision). |

## 2.3 Conventions

| Convention | Detail |
|-----------|--------|
| Code style | Ruff (select E, W, F, I, B, C4, UP, ARG, SIM, TCH, PTH, S, ASYNC, RUF, PERF) |
| Type annotations | Full annotations on all public functions; `TYPE_CHECKING` guard for heavy imports |
| Docstrings | NumPy-style on all public symbols |
| Commit convention | `<type>(<scope>): <description>` (feat, fix, test, chore, docs, refactor) |
| Error handling | Typed exception hierarchy (`ParseError`, `ValidationError`, `ComputationError`, etc.); never raise bare `Exception` |
