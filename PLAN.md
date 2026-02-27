# Implementation Plan: OpenCoulomb

**Plan ID**: `opencoulomb-implementation-2026-02-27`
**Status**: DRAFT — Awaiting approval

## Summary

Full autonomous implementation of OpenCoulomb (Tier 1 MVP) — a standalone Python replacement for the Coulomb 3.4 MATLAB seismology package.

## Scope

**In**: Project scaffold, data model, .inp parser, Okada DC3D engine, stress/CFS computation, OOPs, cross-sections, 2D visualization, CLI, output files, 6-level validation, packaging, documentation.

**Out**: GUI, 3D viz, catalogs, GPS, seismicity rate change, web interface, batch processing.

## Phases & Tasks (42 total)

| Phase | Tasks | Key Deliverables | Quality Gate |
|-------|-------|-----------------|--------------|
| **A: Foundation** | 001-010 | Scaffold, data model, .inp parser | pip install works, parser handles all examples, ≥90% coverage |
| **B: Core Engine** | 011-020 | Okada DC3D, stress, CFS, pipeline | ≤1e-10 Okada accuracy, <1e-6 bar CFS, ≥95% core coverage |
| **C: Extended** | 021-024 | OOPs, cross-sections | Match Coulomb 3.4, ≥90% coverage |
| **D: User-Facing** | 025-036 | Matplotlib viz, Click CLI, output writers | CLI functional, ≥85% I/O/CLI/viz coverage |
| **E: Release** | 037-042 | Validation suite, PyPI, Arc42+Diataxis docs | All 6 validation levels pass, ≥90% overall |

## Execution

- **Mode**: `/orchestrate` (tech-lead coordinating agents)
- **Sessions**: 9 across 5 phases
- **Agents**: backend-engineer (primary), autonomous-coding-specialist (Okada, viz), qa-devops-engineer (CI, testing, packaging), tech-lead (docs, review)
- **Est. tokens**: ~1,295k total

## Blockers (must resolve before Phase B)

1. **Coulomb 3.4 example .inp files** — Need actual example files for testing/validation
2. **Okada (1992) Table 2 reference values** — Need for DC3D validation

## Plan Files

- **Main plan**: `.claude/plans/opencoulomb-implementation-2026-02-27/plan.md`
- **Resources**: `.claude/plans/opencoulomb-implementation-2026-02-27/resources.md`
- **Execution**: `.claude/plans/opencoulomb-implementation-2026-02-27/execution.md`
- **Task details**: `.claude/tasks/opencoulomb-implementation-2026-02-27/phase-{a,b,c,d,e}-*.md`
- **State tracking**: `.claude/state/opencoulomb-implementation-2026-02-27/`

## Next Step

Review plan, then run `/execute opencoulomb-implementation-2026-02-27`
