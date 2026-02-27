# OpenCoulomb — Arc42 Architecture Documentation

Architecture documentation structured according to the [Arc42 template](https://arc42.org/).

## Sections

| # | Section | Description |
|---|---------|-------------|
| 1 | [Introduction and Goals](01-introduction.md) | System purpose, quality goals, stakeholders |
| 2 | [Constraints](02-constraints.md) | Technical and organisational constraints |
| 3 | [System Context](03-context.md) | Users, external systems, interfaces |
| 4 | [Solution Strategy](04-solution-strategy.md) | Technology choices and key architectural patterns |
| 5 | [Building Blocks](05-building-blocks.md) | Component decomposition: types/, core/, io/, viz/, cli/ |
| 6 | [Runtime View](06-runtime-view.md) | Key computation workflows: parse → compute → output |
| 7 | [Deployment](07-deployment.md) | Installation, PyPI distribution, Docker |
| 8 | [Cross-Cutting Concepts](08-crosscutting.md) | Error handling, logging, testing strategy, numerics |
| 9 | [Architecture Decisions](09-decisions/) | ADRs for key design choices |

## Architecture Decision Records

| ADR | Decision | Outcome |
|-----|----------|---------|
| [ADR-001](09-decisions/adr-001-pure-numpy-okada.md) | Okada engine implementation | Pure NumPy (no Fortran f2py) |
| [ADR-002](09-decisions/adr-002-frozen-dataclasses.md) | Domain object representation | Frozen dataclasses (no Pydantic/attrs) |
| [ADR-003](09-decisions/adr-003-state-machine-parser.md) | .inp file parser design | Explicit state machine |

## Quick Architecture Summary

```
.inp file  →  io/inp_parser.py  →  CoulombModel  →  core/pipeline.py  →  CoulombResult
                (state machine)    (frozen DC)       (vectorized Okada)

CoulombResult  →  io/csv_writer.py   →  .csv
               →  io/dat_writer.py   →  .dat
               →  io/cou_writer.py   →  .cou
               →  viz/maps.py        →  PNG / PDF
```

**Key numbers:** Python 3.10+, 800+ tests, 95.77% coverage, ≤ 1e-10 Okada accuracy, Apache 2.0.

## Related Documents

- [Program Specification](../claude/design/program-specification.md) — detailed scientific specification
- [Architecture Research](../claude/architecture/architecture.md) — extended architecture notes
- [Development Plan](../claude/plan/development-plan.md) — phase-by-phase implementation plan
