# ADR-001 — Pure NumPy Okada Implementation

**Status**: Accepted
**Date**: 2026-02-27
**Deciders**: Backend Engineer, Tech Lead

---

## Context

The Okada (1992) elastic dislocation equations (DC3D and DC3D0) are the performance-critical kernel of OpenCoulomb. They compute displacement and displacement gradients at every observation grid point for every source fault.

The original Coulomb 3.4 implementation calls MATLAB's built-in matrix operations. The open-source geophysics community also commonly uses a Fortran 77 implementation (the original code from Okada 1992), wrapped with f2py as `okada4py` or similar packages.

Two implementation options were evaluated:

**Option A — Fortran f2py wrapper**
Wrap the original Okada Fortran 77 code using NumPy's f2py. This is the approach taken by several existing Python packages (okada4py, csi).

**Option B — Pure NumPy (vectorized)**
Translate the Okada equations directly into NumPy array operations. No compiled code.

---

## Decision

**Option B (Pure NumPy)** was chosen.

---

## Rationale

### Installation simplicity

Option A requires a Fortran compiler (gfortran) at install time. This is a significant barrier:
- Most scientists install packages with `pip` into a standard Python environment.
- conda-forge provides gfortran but many users prefer PyPI.
- GitHub Actions CI would require `sudo apt-get install gfortran` on every runner.
- Windows users have no system Fortran compiler by default.

Option B produces a **universal wheel** that installs everywhere without any compiler.

### Performance is sufficient

Typical use cases involve grids up to ~500×500 points and ≤ 20 source faults. A 100×100 grid with 10 faults benchmarks at well under 10 seconds on a modern laptop with the NumPy implementation. This meets the stated performance target.

For truly large grids (1000×1000+), Fortran would be faster, but such use cases are rare in the target user community and can be addressed later (e.g., with an optional `opencoulomb[fast]` extra that installs the Fortran wrapper).

### Correctness verifiability

The NumPy translation is written in plain Python and can be read, audited, and debugged by any contributor. Validation against Okada (1992) Table 2 confirmed sub-1e-10 accuracy, matching the Fortran reference.

### Maintainability

Fortran wrappers require f2py ABI compatibility across Python versions and are a common source of CI failures. Pure Python is simpler to maintain.

---

## Consequences

**Positive:**
- `pip install opencoulomb` works without a compiler on all platforms.
- Source is fully readable and auditable.
- Validated to ≤ 1e-10 relative error vs Okada (1992) Table 2.

**Negative:**
- Approximately 5–10× slower than Fortran for very large grids.
- Cannot easily leverage GPU (CuPy) without architectural changes.

**Mitigations:**
- If performance becomes a bottleneck, an optional Fortran/Cython backend can be added as `opencoulomb[fast]` without changing the public API.
- NumPy itself uses BLAS/LAPACK internally and is already multi-threaded for matrix operations.

---

## References

- Okada, Y. (1992). Internal deformation due to shear and tensile faults in a half-space. *BSSA*, 82(2), 1018–1040.
- NumPy vectorization performance benchmarks: `tests/benchmarks/`
