# OpenCoulomb - Architecture Documents Index

- Phase: `3 - Program Architecture`
- Date: `2026-02-27`
- Status: `Completed (draft)`
- Output directory: `docs/claude/architecture`
- Blocked by: `Phase 2 - Program Specification`
- Feeds: `Phase 4 - Development Plan`

---

## Documents

| # | Document | Description |
|---|----------|-------------|
| 1 | [architecture.md](./architecture.md) | Complete technical architecture (3,749 lines) |

---

## Dependency Check

Phase 3 consumes approved outputs from Phase 2:

- MVP scope and non-goals.
- Functional requirements for parser, compute engine, outputs, and CLI.
- Non-functional targets (accuracy, performance, reproducibility).
- Governance requirement for clean-room implementation.
- Technology decisions (Python 3.10+, NumPy, Matplotlib, Click, PyQt6).

---

## Architecture Summary

### Layer Diagram
```
CLI (Click) / GUI (PyQt6) / Python API / Web (FastAPI)
        |               |            |           |
        +-------+-------+------+-----+-----+-----+
                |              |           |
         Visualization    I/O Layer    Core Engine
         (Matplotlib,     (.inp parser  (Okada DC3D,
          PyVista,         .cou writer   Stress,
          Cartopy)         CSV, DAT)     CFS, OOPs)
                |              |           |
                +------+-------+-----+-----+
                       |             |
                  Data Model      Constants
                  (dataclasses)   (_constants.py)
                       |
                    NumPy / SciPy
```

### Key Modules
| Module | Responsibility |
|--------|---------------|
| `core/okada.py` | Okada (1992) DC3D/DC3D0 - vectorized NumPy |
| `core/stress.py` | Hooke's law, tensor rotation |
| `core/coulomb.py` | CFS calculation, Bond matrix |
| `core/coordinates.py` | Coordinate transforms |
| `core/oops.py` | Optimally oriented planes |
| `core/pipeline.py` | Computation orchestrator |
| `types/` | All dataclasses: FaultElement, Grid, CoulombModel, CoulombResult |
| `io/inp_parser.py` | State-machine .inp parser |
| `viz/maps.py` | 2D CFS contour maps |
| `cli/main.py` | Click command group |

---

## Phase Gate

Phase 4 (Development Plan) can start only after these are approved:

1. Module boundaries and dependency direction are fixed.
2. Data model and unit conventions are explicit.
3. Compute and dataflow contracts are explicit enough for implementation tickets.
4. Validation architecture and performance strategy are defined.
5. No unresolved scope contradictions remain with Phase 2.
