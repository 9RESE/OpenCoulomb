# OpenCoulomb - Development Plan Index

- Phase: `4 - Development Plan`
- Date: `2026-02-27`
- Status: `Completed (draft)`
- Output directory: `docs/claude/plan`
- Blocked by: `Phase 3 - Program Architecture`

---

## Documents

| # | Document | Description |
|---|----------|-------------|
| 1 | [development-plan.md](./development-plan.md) | Complete development plan (2,417 lines) |

---

## Dependency Check

Phase 4 consumes approved outputs from Phase 3:

- Module contracts and dependency direction.
- Data model and unit conventions.
- Validation architecture and performance strategy.
- Packaging and deployment architecture.

---

## Development Phases Overview

| Phase | Milestones | Scope | Release |
|-------|-----------|-------|---------|
| **A: Foundation** | M1 + M4 | Scaffold, data model, .inp parser | -- |
| **B: Core Engine** | M2 + M3 + M5 | Okada DC3D, stress, CFS | 0.1.0-alpha |
| **C: Extended** | M6 + M7 | OOPs, cross-sections | 0.2.0-alpha |
| **D: User-Facing** | M8 + M9 + M10 | Visualization, CLI, output files | 0.5.0-beta |
| **E: Release** | M11 + M12 + M13 | Validation, packaging, docs | 1.0.0 |

## 99 Tasks Across 13 Milestones

## Three Documentation Types

| Type | Audience | Framework | Key Outputs |
|------|----------|-----------|-------------|
| **Technical** | Developers/contributors | Arc42 | Architecture docs, ADRs, API ref, contributing guide |
| **Human User** | Seismologists/students | Diataxis | 5 tutorials, 8 how-to guides, 8 references, 6 explanations |
| **LLM-Optimized** | AI coding assistants | Custom | CLAUDE.md, 5 CONTEXT.md files, 2 skills, function index |

---

## Final Phase Gate

Execution can start after this plan is accepted for:

1. Milestone order and phase grouping.
2. Acceptance gates per milestone (done criteria).
3. Test and validation policy (6-level validation).
4. Risk contingency triggers and actions.
5. Release and delivery sequence (alpha -> beta -> 1.0.0).
