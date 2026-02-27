# OpenCoulomb - Design Documents Index

- Phase: `2 - Program Specification`
- Date: `2026-02-27`
- Status: `Completed (draft)`
- Output directory: `docs/claude/design`
- Blocked by: `Phase 1 - Research`
- Feeds: `Phase 3 - Architecture`

---

## Documents

| # | Document | Description |
|---|----------|-------------|
| 1 | [program-specification.md](./program-specification.md) | Complete program specification (1,728 lines) |

---

## Dependency Check

Phase 2 uses these locked outputs from Phase 1:

- Scope lock: `Coulomb 3.4 parity first`.
- Clean-room implementation policy due to upstream license ambiguity.
- MATLAB replacement surface (compute, I/O, viz, UX).
- Compatibility priorities (`.inp`, stress outputs, reproducible CLI workflows).

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Project name** | OpenCoulomb | Recognizable to Coulomb users + signals open-source |
| **Language** | Python 3.10+ | Scientific ecosystem, target users know it, pip-installable |
| **Okada engine** | Pure NumPy vectorized (Phase 1), Fortran wrapper fallback | Speed + portability balance |
| **Visualization** | Matplotlib (static) + PyVista (3D) + Cartopy (maps) | Publication quality, proven stack |
| **GUI** | PyQt6/PySide6 (Tier 2), web GUI (Tier 3) | CLI-first, GUI later |
| **License** | Apache 2.0 | Permissive, compatible with scientific use |
| **Distribution** | pip install, conda, Docker | Zero-friction installation |

## Implementation Tiers

| Tier | Scope | Release |
|------|-------|---------|
| **Tier 1 (MVP)** | .inp parsing, Okada DC3D, CFS, OOPs, displacement, cross-section, static viz, CLI, output files | v1.0 |
| **Tier 2 (Parity)** | GUI, 3D viz, catalogs, GPS comparison, all KODE types, rate change, pub-quality output | v2.0 |
| **Tier 3 (Beyond)** | Python API, batch processing, web GUI, layered half-space, plugins | v3.0+ |

---

## Phase Gate

Phase 3 (Architecture) can start only after these are approved:

1. MVP scope and non-goals are explicit.
2. Functional and non-functional requirements are testable.
3. Governance and compatibility rules are explicit.
4. License/governance policy (Apache 2.0) accepted.
5. Technology decisions (Python, NumPy, Matplotlib, Click) accepted.
