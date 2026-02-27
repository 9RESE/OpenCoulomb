# Phase A/B Code Review — Remediation Report

Date: 2026-02-27
Review: `docs/review/phase-a-b-review-2026-02-27.md`
Scope: All 5 findings addressed, plus parser compatibility expanded to full Coulomb 3.4 distribution.

---

## Finding 1 (High): mypy strict type-check failures — RESOLVED

**33 errors → 0 errors.**

| File | Issue | Fix |
|------|-------|-----|
| `core/okada.py` (31 errors) | Bare `NDArray` without type parameter | Replaced all with `NDArray[np.float64]` |
| `types/result.py` (1 error) | `elements: list` unparameterized | Changed to `list[FaultElement]`, added TYPE_CHECKING import |
| `io/inp_parser.py` (1 error) | Untyped callable in dispatch dict | Added explicit `dict[_ParserState, Callable[[str], None]]` annotation; moved `Callable` import to TYPE_CHECKING block |

---

## Finding 2 (High): compute_grid ignores all receivers except first — RESOLVED

**Added `receiver_index` parameter with full validation.**

API change:
```python
# Before
def compute_grid(model: CoulombModel) -> CoulombResult

# After
def compute_grid(model: CoulombModel, receiver_index: int | None = None) -> CoulombResult
```

Behavior:
- `receiver_index=None` (default): uses `receivers[0]`, matching Coulomb 3.4 behavior
- `receiver_index=N`: uses `receivers[N]` with bounds checking
- `ValidationError` raised for out-of-bounds index or index specified with no receivers

Tests added (5):
- `test_default_uses_first_receiver` — None == index 0
- `test_receiver_index_1_differs_from_0` — different orientations produce different CFS
- `test_receiver_index_out_of_bounds` — ValidationError
- `test_receiver_index_negative` — ValidationError
- `test_receiver_index_on_no_receiver_model` — ValidationError

---

## Finding 3 (High): Numerical validation gates not enforced — RESOLVED

**Added full Okada Table 2 validation and CFS regression fixtures.**

### Okada validation (6 tests)
- All 12 output components (3 displacement + 9 gradients) × 3 slip types (strike, dip, tensile)
- Table 2 published values checked at 5e-4 relative tolerance (matches 4 significant figure precision)
- Regression fixtures stored at full computation precision, validated at ≤1e-10 relative error

### CFS regression (1 test)
- `simplest_receiver.inp`: 5 grid point CFS values checked within 1e-6 bar absolute error

---

## Finding 4 (Medium): Parser compatibility under-tested — RESOLVED

**Expanded from 7 → 30 fixture files. All 20 Coulomb 3.4 distribution files parse and compute.**

### Source: Coulomb 3.4 distribution (20 files)
Downloaded from `https://coulomb.s3.us-west-2.amazonaws.com/downloads/coulomb3402.zip`,
directory `coulomb3402/input_file/`. Stored in `tests/fixtures/inp_files/coulomb34/`.

Files cover:
- KODE 100 (standard), 200 (tensile+RL), 300 (tensile+reverse), 400 (point source), 500 (tensile+inflation)
- Uniform and variable slip models
- Real earthquakes: Kobe 1995, Landers 1992
- Lon/lat coordinate variants
- Surface deformation variants
- Multi-fault models (up to 180 subfaults)
- Receiver fault models

### Source: USGS Earthquake Hazards Program (3 files)
Downloaded from USGS finite-fault archive. Stored in `tests/fixtures/inp_files/usgs_finite_fault/`.

| File | Event | Faults |
|------|-------|--------|
| `usgs_philippines_M7.4.inp` | 2025 M7.4 Santiago, Philippines | 900 |
| `usgs_japan_M7.6.inp` | 2025 M7.6 Aomori Prefecture, Japan | 225 |
| `usgs_russia_M7.8.inp` | 2024 M7.8 Kamchatka, Russia | 270 |

### Parser bug fix: Blank-line grid state transition

The USGS files exposed an additional parser bug: blank lines between "Grid Parameters" and "Size Parameters" sections caused premature transition to CROSS_SECTION state, which then misinterpreted Size Parameters numbered lines as cross-section data.

**Root cause:** `_on_grid` transitioned to CROSS_SECTION on any blank line when `self._grid_params` was populated.

**Fix:** Removed the blank-line transition from `_on_grid`. The handler now stays in GRID state across blank lines and only transitions on explicit "Cross section" or "Map info" keywords. The existing guard (`idx <= 6 and idx not in self._grid_params`) already prevented Size Parameters from overwriting grid params.

### Test coverage (91 tests)
- `TestCoulomb34Distribution`: 80 parametrized tests (parse, compute, grid shape, displacement finite × 20 files)
- `TestUSGSFiniteFault`: 6 parametrized tests (parse, compute × 3 files)
- `TestKodeCoverageAcrossDistribution`: 5 tests verifying all KODE types present across distribution

---

## Finding 5 (Medium): compute_grid crashes on no-fault models — RESOLVED

**Added precondition check with clear error message.**

```python
if not model.source_faults:
    raise ComputationError(
        "Model has no source faults; cannot compute grid CFS. "
        "At least one source fault with non-zero slip is required."
    )
```

Tests added (2):
- `test_no_sources_raises_computation_error` — receiver-only model
- `test_no_faults_at_all_raises_computation_error` — empty model

---

## Open Questions — Resolved

| Question | Resolution |
|----------|------------|
| Grid CFS for single/all/aggregate receivers? | Single receiver (Coulomb 3.4 behavior), explicit `receiver_index` parameter |
| Are zero-fault models valid? | Syntactically valid, but `ComputationError` at compute time |
| Mypy deferral? | No deferral — all 33 errors fixed, strict mode passes |

---

## Summary

| Metric | Before | After |
|--------|--------|-------|
| mypy errors | 33 | 0 |
| Test count | 566 | 668 |
| .inp fixture files | 7 | 30 |
| Coulomb 3.4 distribution coverage | 0/20 | 20/20 |
| USGS finite-fault files | 0 | 3 |
| KODE types tested via real files | 1 (100) | 5 (100, 200, 300, 400, 500) |
| ruff violations | 0 | 0 |
| All quality gates | PASS | PASS |
