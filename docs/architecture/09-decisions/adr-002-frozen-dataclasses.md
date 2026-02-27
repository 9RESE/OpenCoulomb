# ADR-002 — Frozen Dataclasses for Domain Objects

**Status**: Accepted
**Date**: 2026-02-27
**Deciders**: Backend Engineer, Tech Lead

---

## Context

The domain model layer (`types/`) requires a representation for scientific data structures: `FaultElement`, `GridSpec`, `MaterialProperties`, `CoulombModel`, `CoulombResult`, etc. These objects are:

- Produced by the parser (once)
- Consumed by the pipeline (read-only)
- Inspected by the CLI and visualisation layer
- Never modified after creation

Three options were evaluated:

**Option A — Pydantic v2 models**
Use `pydantic.BaseModel` with `model_config = ConfigDict(frozen=True)`.

**Option B — attrs classes**
Use `@attrs.define(frozen=True)`.

**Option C — Standard library frozen dataclasses**
Use `@dataclass(frozen=True)` (Python 3.10+: `@dataclass(slots=True)`).

---

## Decision

**Option C (standard library frozen dataclasses)** was chosen.

---

## Rationale

### Zero runtime dependency

Pydantic v2 and attrs are excellent libraries, but they are runtime dependencies. OpenCoulomb's domain objects are used by the computation engine (`core/`), which has no need for JSON serialisation, validators, or other Pydantic features. Adding Pydantic purely for data structures would bloat the dependency graph without benefit.

Standard library dataclasses provide everything needed:
- Immutability via `frozen=True`
- Memory efficiency via `slots=True` (Python 3.10+)
- `__repr__`, `__eq__`, `__hash__` for free
- `dataclasses.replace()` for creating modified copies

### Appropriate feature set

The domain objects are **not** API models (no JSON serialisation needed), **not** config models (no environment variable parsing), and **not** ORM models (no database). They are pure value objects representing scientific quantities. Dataclasses are the right level of abstraction.

### Pydantic's validation overhead

Pydantic v2 performs field validation on construction. For performance-sensitive paths where thousands of fault elements might be constructed (e.g., during grid parsing or result generation), this overhead is unnecessary. Validation in OpenCoulomb is performed as a dedicated step in the parser, not at object construction time.

### Readability

Standard dataclasses are understood by every Python developer without library-specific knowledge. Contributors do not need to learn Pydantic's `field()`, `model_validator`, or attrs's `@attrs.define` decorator semantics.

---

## Consequences

**Positive:**
- No runtime dependency on Pydantic or attrs.
- Immutable objects prevent accidental mutation in the pipeline.
- `slots=True` reduces memory usage for large result arrays (though the main data is in NumPy arrays, not Python objects).
- Standard Python — no special IDE plugins required.

**Negative:**
- No built-in JSON serialisation (not needed).
- No field-level validators on construction (validation is in the parser, which is appropriate).
- Verbose `dataclasses.replace()` for constructing modified copies (acceptable given infrequent use).

**Mitigations:**
- Input validation is centralised in `io/inp_parser.py` where errors can include line numbers.
- If JSON serialisation is needed in future (e.g., for a REST API), a thin serialisation layer can be added without changing the domain objects.

---

## References

- Python docs: `dataclasses` — https://docs.python.org/3/library/dataclasses.html
- PEP 557 — Data Classes
- Python 3.10 `slots=True` addition to `@dataclass`
