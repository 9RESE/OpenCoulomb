# Coulomb Project - Research Index

- Phase: `1 - Research`
- Date: `2026-02-27`
- Status: `Completed`
- Output directory: `docs/claude/research`
- Feeds: `Phase 2 - Program Specification`

---

## Documents

| # | Document | Description |
|---|----------|-------------|
| 1 | [coulomb-matlab-research.md](./coulomb-matlab-research.md) | Comprehensive overview: features, history, algorithms, alternatives, license |
| 2 | [coulomb-matlab-package-research.md](./coulomb-matlab-package-research.md) | Source code analysis: file structure, data structures, computation pipeline, reimplementation insights |
| 3 | [research-summary.md](./research-summary.md) | Executive summary and key findings for downstream phases |

---

## Research Scope

- Confirm current upstream Coulomb distribution channels and GitHub repositories.
- Identify MATLAB/runtime/toolbox dependencies to replace.
- Identify scientific/format compatibility requirements for a standalone reimplementation.
- Identify legal/licensing constraints for open-source redistribution.
- Identify existing open-source alternatives and reuse opportunities.
- Inspect Coulomb 3.4 source code for data structures, algorithms, and conventions.

---

## Key Findings Summary

### What Is Coulomb?
USGS/Temblor MATLAB software for calculating Coulomb failure stress changes, displacements, and strains from earthquake fault slip using the Okada (1992) elastic dislocation solution. 10,000+ downloads, 3,000+ citations.

### Why a Standalone Version?
- Coulomb requires MATLAB ($2,000-5,000+ license)
- Coulomb 4.0 requires 3 additional toolboxes (~$3,000-9,000 more)
- No existing free tool provides Coulomb's full feature set (GUI + CFS + catalogs + visualization + .inp compatibility)

### Core Algorithm
Okada (1992) closed-form analytical solution for displacement/strain/stress from rectangular dislocations in an elastic half-space, combined with the Coulomb failure criterion.

### Existing Alternatives (None Complete)
- **elastic_stresses_py** (Python, MIT) - closest, reads .inp, no GUI
- **Pyrocko** (Python, GPLv3) - mature, Okada+CFS, no .inp support
- **OkadaPy** (Python/C, GPLv3) - early stage, low-level only
- **PSGRN/PSCMP** (Fortran) - more physics, no GUI, no .inp

---

## Phase Gate

Phase 2 (Program Specification) can start only after these are explicitly accepted from Phase 1:

1. Standalone target scope: `Coulomb 3.4 computational parity first`.
2. Clean-room/legal approach: behavior-compatible reimplementation only (no MATLAB code translation).
3. MVP compatibility contract: `.inp` ingestion + core stress/displacement outputs.
4. Replacement stack direction: Python scientific stack + CLI-first.
5. License governance: explicit OSS license (Apache-2.0 or MIT) with provenance notes.
