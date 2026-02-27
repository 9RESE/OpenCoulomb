# Changelog

All notable changes to OpenCoulomb will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-27

### Added
- **Core computation engine**
  - Okada DC3D/DC3D0 vectorized NumPy implementation
  - Stress tensor computation (Hooke's law, tensor rotation, Bond matrix)
  - Coulomb failure stress (CFS) resolution on specified receiver faults
  - Optimally oriented planes (OOPs) computation
  - Cross-section stress/displacement computation
  - Grid-based pipeline with multi-source superposition
- **Data model** — Frozen dataclasses for all domain types (FaultElement, GridSpec, CoulombModel, etc.)
- **.inp parser** — State machine parser for Coulomb 3.4 fixed-width format (23 files tested)
- **Output writers** — Coulomb .cou, CSV, GMT .dat, text summary formats
- **Visualization** — CFS contour maps, fault traces, displacement quivers, cross-section plots, publication/screen styles
- **CLI** — Click-based commands: `compute`, `plot`, `info`, `validate`, `convert`
- **Validation suite** — 811 tests across 6 levels (unit, integration, Okada reference, CFS comparison, end-to-end, performance)
- **Documentation** — Arc42 architecture (12 files, 3 ADRs), Diataxis user docs (12 files), LLM guide
- **Packaging** — PyPI-ready with hatchling, sdist/wheel builds verified
