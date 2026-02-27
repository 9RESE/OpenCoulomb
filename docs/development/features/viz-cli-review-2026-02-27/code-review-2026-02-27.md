# Code Review: Visualization, CLI, and Test Suite

## Review Summary
**Reviewer**: Code Review Agent
**Date**: 2026-02-27
**Scope**: Phase C/D — viz (9 files), cli (6 files), tests (5 files)
**Files Reviewed**: 20 files
**Issues Found**: 15 total (2 HIGH, 8 MEDIUM, 5 LOW)

---

## Findings

### Finding 1: No plt.close() After Figure Creation in Viz Tests (Severity: HIGH)
**File**: `tests/unit/test_viz.py` — all test methods in `TestCfsMap`, `TestFaultTraces`, `TestCrossSectionPlot`, `TestDisplacement`, `TestExport`
**Issue**: Every test that calls a viz function (`plot_cfs_map`, `plot_fault_traces`, `plot_cross_section`, `plot_displacement`, `save_figure`) creates a Matplotlib `Figure` object and never closes it. With `pytest-xdist` parallelism or on large test runs, this leaks open figures into the process-global Matplotlib state. The Matplotlib `Agg` backend accumulates all unclosed figures and emits a `RuntimeWarning: More than 20 figures have been opened` once the test count reaches that threshold. In CI environments this can mask legitimate warnings or cause OOM in low-memory runners.
**Recommendation**: Add `plt.close(fig)` (or `plt.close("all")`) as a finalizer in each test, or use a pytest fixture with a `yield`/`finally` block:
```python
@pytest.fixture(autouse=True)
def close_figures():
    yield
    import matplotlib.pyplot as plt
    plt.close("all")
```
Apply this fixture at the module level in `test_viz.py`.

---

### Finding 2: `matplotlib.use("Agg")` Called Inside Test Methods — Race Condition Risk (Severity: HIGH)
**File**: `tests/unit/test_viz.py:113`, `tests/unit/test_viz.py:163`, and ~15 other call sites throughout `test_viz.py` and `test_cli.py`
**Issue**: `matplotlib.use("Agg")` is called inside individual test methods rather than once at module or session scope. Matplotlib only allows backend switching before any figure is created. When tests run in any non-isolated order (e.g., `pytest-randomly`, or if another test imports pyplot first), this call becomes a no-op and emits a warning, or raises a `UserWarning` that breaks assertions relying on clean output. The duplication across 15+ test sites is also a maintenance burden.
**Recommendation**: Set the backend exactly once at module import time or in `conftest.py`:
```python
# tests/conftest.py  (or at top of test_viz.py)
import matplotlib
matplotlib.use("Agg")
```
Remove all per-method `matplotlib.use("Agg")` calls. This is the standard pattern recommended by the Matplotlib documentation for headless test environments.

---

### Finding 3: `plot_cmd` Does Not Close Figure After Saving (Severity: MEDIUM)
**File**: `src/opencoulomb/cli/plot.py:65`
**Issue**: The `plot_cmd` function calls `save_figure(fig, output, dpi=dpi)` but never calls `plt.close(fig)`. In a CLI context this is a single-shot process, so there is no memory leak at runtime. However, if `plot_cmd` is ever called more than once in the same process (e.g., from a script that imports and calls `cli()` in a loop, or from test runners that invoke it repeatedly), figures accumulate in the Matplotlib figure manager. Sixty such calls will hit the 20-figure warning threshold.
**Recommendation**: Add `import matplotlib.pyplot as plt; plt.close(fig)` immediately after `save_figure`:
```python
save_figure(fig, output, dpi=dpi)
import matplotlib.pyplot as plt
plt.close(fig)
click.echo(f"Saved: {output}")
```

---

### Finding 4: `sections.py` — Invalid `field` Key Raises Unguarded `KeyError` (Severity: MEDIUM)
**File**: `src/opencoulomb/viz/sections.py:43`
**Issue**:
```python
field_map = {"cfs": section.cfs, "shear": section.shear, "normal": section.normal}
data = field_map[field]
```
If `field` is any string other than `"cfs"`, `"shear"`, or `"normal"`, a bare `KeyError` is raised. The public API docstring lists only those three valid values, but there is no guard and no `ValueError` with a helpful message. An end-user calling `plot_cross_section(section, field="CFS")` (wrong case) would see a cryptic `KeyError: 'CFS'`.
**Recommendation**: Replace with an explicit validation and user-friendly `ValueError`:
```python
valid_fields = ("cfs", "shear", "normal")
if field not in valid_fields:
    msg = f"Unknown field '{field}'. Valid options: {valid_fields}"
    raise ValueError(msg)
data = field_map[field]
```

---

### Finding 5: `displacement.py` — Vertical Component Uses Sequential Colormap Without Symmetric Norm (Severity: MEDIUM)
**File**: `src/opencoulomb/viz/displacement.py:60`
**Issue**:
```python
cf = ax.contourf(x, y, uz_2d, levels=20, cmap=displacement_cmap())
```
The vertical displacement (`uz`) is plotted with a sequential colormap (`viridis`) and no norm. Vertical displacement is a signed quantity (positive = uplift, negative = subsidence). Using a non-diverging colormap with automatic data-driven limits makes it impossible to visually distinguish positive from negative values, and produces misleading color gradients when the data is symmetric around zero. The existing `symmetric_norm` and `coulomb_cmap` are already available in the same module.
**Recommendation**: Apply the diverging colormap and symmetric normalization for the vertical component:
```python
from opencoulomb.viz.colormaps import coulomb_cmap, symmetric_norm
norm_uz = symmetric_norm(uz_2d, vmax=vmax)
cf = ax.contourf(x, y, uz_2d, levels=20, cmap=coulomb_cmap(), norm=norm_uz)
```
Also propagate the `vmax` parameter through the function signature for the vertical case. Currently `vmax` is accepted in the signature but only used when delegated to `plot_cfs_map`, not in this branch.

---

### Finding 6: `_logging.py` — Handler Is Added Every Call, Causing Duplicate Log Output (Severity: MEDIUM)
**File**: `src/opencoulomb/cli/_logging.py:14`
**Issue**:
```python
logger.addHandler(handler)
```
`setup_logging` is called once per CLI invocation in production. However, the test suite calls CLI commands many times via `CliRunner.invoke()` within the same process, and each call executes `setup_logging`, which calls `logger.addHandler(handler)`. Python loggers accumulate handlers without deduplication. After N test invocations, the `opencoulomb` logger has N handlers, and each log record is emitted N times to stderr. This produces noise in verbose test output and can slow down log-heavy tests.
**Recommendation**: Guard with `if not logger.handlers:` or use `logging.basicConfig`-style once-only setup:
```python
def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger("opencoulomb")
    if logger.handlers:
        logger.setLevel(level)
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.setLevel(level)
    logger.addHandler(handler)
```

---

### Finding 7: `compute.py` — Missing Error Handling Around Core Computation (Severity: MEDIUM)
**File**: `src/opencoulomb/cli/compute.py:48`
**Issue**: The `compute_grid` and `read_inp` calls have no `try/except` block. If the `.inp` file parses successfully but the computation raises (e.g., a singular matrix from degenerate fault geometry, or a NumPy overflow), the exception propagates as an unhandled Python traceback rather than a clean `click.ClickException`. This exposes internal stack traces to end-users, which is poor UX and potentially leaks implementation details.
**Recommendation**: Wrap the computation in a `try/except` block:
```python
try:
    result = compute_grid(model, receiver_index=receiver)
except Exception as exc:
    raise click.ClickException(f"Computation failed: {exc}") from exc
```
Apply the same pattern around `read_inp`. The `validate` command already demonstrates this pattern correctly at line 26.

---

### Finding 8: `info.py` — No Error Handling for Malformed Input Files (Severity: MEDIUM)
**File**: `src/opencoulomb/cli/info.py:14`
**Issue**: `read_inp(inp_file)` is called without a `try/except` block. A malformed `.inp` file will produce a raw Python traceback rather than the user-friendly `ClickException` message pattern used in `validate.py:27`. This is inconsistent with the rest of the CLI.
**Recommendation**: Wrap with the same pattern as `validate_cmd`:
```python
try:
    model = read_inp(inp_file)
except Exception as exc:
    raise click.ClickException(f"Parse error: {exc}") from exc
```

---

### Finding 9: `export.py` — Parent Directory Is Not Created Before Save (Severity: MEDIUM)
**File**: `src/opencoulomb/viz/export.py:47`
**Issue**: `fig.savefig(filepath, ...)` will raise `FileNotFoundError` if the parent directory of `filepath` does not exist. The `compute_cmd` already calls `output_dir.mkdir(parents=True, exist_ok=True)`, but `save_figure` is a general-purpose public API that may be called directly by end-users or library consumers who do not pre-create the directory.
**Recommendation**: Add a `mkdir` call before saving:
```python
filepath.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(filepath, **kwargs)
```

---

### Finding 10: `test_viz.py` — `tmp_path` Typed as `object` in Export Tests (Severity: LOW)
**File**: `tests/unit/test_viz.py:380`, `tests/unit/test_viz.py:395`, `tests/unit/test_viz.py:410`, `tests/unit/test_viz.py:437`
**Issue**: The `tmp_path` fixture parameter is typed as `object` instead of `Path` in the `TestExport` class methods:
```python
def test_save_png(self, tmp_path: object, ...) -> None:
```
This is a copy-paste error — `tmp_path` is a built-in pytest fixture with type `Path`. Typing it as `object` means mypy/pyright cannot verify the `Path(str(tmp_path)) /` path construction downstream and requires the redundant `Path(str(tmp_path))` coercion that appears in all four export tests.
**Recommendation**: Change the type annotation to `Path` and remove the redundant coercion:
```python
def test_save_png(self, tmp_path: Path, ...) -> None:
    ...
    out = save_figure(fig, tmp_path / "test.png")
```

---

### Finding 11: `test_benchmarks.py` — Wall-Clock Timing Is Environment-Dependent (Severity: LOW)
**File**: `tests/performance/test_benchmarks.py:82`, `tests/performance/test_benchmarks.py:94`
**Issue**: The benchmarks assert hard wall-clock limits (`elapsed < 10.0`, `elapsed < 3.0`). Wall-clock time is non-deterministic: it varies with CI runner load, virtualization overhead, and cold-start JIT effects. These tests will produce intermittent failures ("flaky tests") in shared CI environments, especially on slower runners such as GitHub Actions free tier.
**Recommendation**: Either:
1. Mark these tests with a `@pytest.mark.skipif` that skips on CI unless `BENCHMARK_ENABLED=1`, or
2. Use relative scaling assertions only (the `test_single_fault_linear_time` test already does this correctly), or
3. Use `pytest-benchmark` which handles warmup, repetitions, and comparison baselines properly.
The scaling test on line 96 (`ratio < 8.0`) is the most defensible assertion here, as it is environment-agnostic.

---

### Finding 12: `validate.py` — `model.faults` Iteration vs. Documented Intent (Severity: LOW)
**File**: `src/opencoulomb/cli/validate.py:48`
**Issue**:
```python
for i, fault in enumerate(model.faults):
```
This iterates over all faults (sources + receivers). The check on line 49 (`fault.length < 1e-6`) is appropriate for all faults. However, the check on line 51 (`fault.bottom_depth > 100`) applies indiscriminately without distinguishing source faults from receivers. If a receiver fault is intentionally defined at great depth for sensitivity studies (common in academic Coulomb analyses), the warning is a false positive. Additionally, `model.faults` is a private/implementation detail — the public-facing `source_faults` and `receiver_faults` properties exist for this purpose.
**Recommendation**: Use the semantic properties and tag issues with fault type:
```python
for i, fault in enumerate(model.source_faults):
    if fault.length < 1e-6:
        issues.append(f"Source fault {i}: zero-length trace")
    if fault.bottom_depth > 100:
        issues.append(f"Source fault {i}: very deep ({fault.bottom_depth} km)")
for i, fault in enumerate(model.receiver_faults):
    if fault.length < 1e-6:
        issues.append(f"Receiver fault {i}: zero-length trace")
```

---

### Finding 13: `colormaps.py` — TYPE_CHECKING Import of `numpy` Is Unused at Runtime (Severity: LOW)
**File**: `src/opencoulomb/viz/colormaps.py:11`
**Issue**:
```python
if TYPE_CHECKING:
    import numpy as np
    from matplotlib.colors import Colormap, Normalize
    from numpy.typing import NDArray
```
`numpy` is imported at runtime inside `symmetric_norm` on line 53 (`import numpy as np`). The `TYPE_CHECKING`-guarded `import numpy as np` on line 11 is therefore redundant — it exists only for type annotations in the `symmetric_norm` signature, but the runtime import already covers it. This creates a confusing dual-import pattern where the module appears to have NumPy as a type-check-only dep but actually requires it at runtime.
**Recommendation**: Move the runtime `import numpy as np` from inside the function body to the module top level (not guarded by `TYPE_CHECKING`), and remove the guarded `import numpy as np`:
```python
import numpy as np
import matplotlib.colors as mcolors
# TYPE_CHECKING block retains only: Colormap, Normalize, NDArray
```

---

### Finding 14: `test_cli.py` — No Assertion on Output File Content for Compute (Severity: LOW)
**File**: `tests/unit/test_cli.py:80-102`
**Issue**: `TestComputeCommand.test_compute_all` asserts that `*_dcff.cou` and `*.csv` files are created, but does not verify file content (e.g., that the CSV has a valid header, that the COU file is non-empty, that no file contains NaN values). The same pattern exists in `test_compute_cou_only`, `test_compute_csv_only`, and `test_compute_dat_only`. While the E2E tests cover some of this, the unit-level CLI tests provide no diagnostic information when the writer produces a zero-byte or malformed file.
**Recommendation**: Add minimal content assertions:
```python
csv_files = list(tmp_path.glob("*.csv"))
assert csv_files, "No CSV file created"
content = csv_files[0].read_text()
assert "x_km" in content  # header present
assert "nan" not in content.lower()  # no NaN values
```

---

### Finding 15: `__init__.py` — `stress_cmap` Exported but Undocumented in Public API (Severity: LOW)
**File**: `src/opencoulomb/viz/__init__.py:31`
**Issue**: `stress_cmap` is exported in `__all__` and is identical in implementation to `coulomb_cmap` (both return `RdBu_r`). There is no usage of `stress_cmap` in any other viz module or test beyond the `TestColormaps` export assertion. This creates an unnecessarily wide public surface area with an undifferentiated duplicate.
**Recommendation**: Either remove `stress_cmap` from the public API and consolidate with `coulomb_cmap`, or document when users should prefer `stress_cmap` over `coulomb_cmap` (e.g., for stress-tensor component plots vs. CFS plots). If both are retained, add distinct color ramp behavior to justify the naming distinction.

---

## Summary Table

| # | Severity | Category | File |
|---|----------|----------|------|
| 1 | HIGH | Memory | `tests/unit/test_viz.py` |
| 2 | HIGH | Quality/Flaky | `tests/unit/test_viz.py`, `tests/unit/test_cli.py` |
| 3 | MEDIUM | Memory | `src/opencoulomb/cli/plot.py` |
| 4 | MEDIUM | UX/Error | `src/opencoulomb/viz/sections.py` |
| 5 | MEDIUM | Scientific/UX | `src/opencoulomb/viz/displacement.py` |
| 6 | MEDIUM | Quality/Flaky | `src/opencoulomb/cli/_logging.py` |
| 7 | MEDIUM | UX/Error | `src/opencoulomb/cli/compute.py` |
| 8 | MEDIUM | UX/Error | `src/opencoulomb/cli/info.py` |
| 9 | MEDIUM | Robustness | `src/opencoulomb/viz/export.py` |
| 10 | LOW | Types | `tests/unit/test_viz.py` |
| 11 | LOW | Flaky | `tests/performance/test_benchmarks.py` |
| 12 | LOW | Quality | `src/opencoulomb/cli/validate.py` |
| 13 | LOW | Style | `src/opencoulomb/viz/colormaps.py` |
| 14 | LOW | Coverage | `tests/unit/test_cli.py` |
| 15 | LOW | API Design | `src/opencoulomb/viz/__init__.py` |

## Security Assessment

No path traversal or injection vulnerabilities were found. All CLI file arguments use `click.Path(exists=True)` which prevents missing-file exploitation. Output paths are constructed via `pathlib.Path` operations (stem + suffix), not string interpolation. The `save_figure` extension check is whitelist-based, not blacklist. No shell subprocess calls exist in the reviewed code.

## UX Assessment

- Help text quality: Good. All commands have docstrings and all options have `help=` text. The `--help` output for each command is informative.
- Error messages: Inconsistent. `validate.py` wraps parse errors with `ClickException` correctly; `info.py` and `compute.py` do not (Findings 7, 8).
- Default values: Sensible. `--format all`, `--type cfs`, `--dpi 300` are all reasonable defaults for a seismology workflow.
- Exit codes: Correct where tested. `click.ClickException` sets exit code 1 automatically.

## Patterns Learned for Future Reviews

1. In Matplotlib test suites: always check for `plt.close()` calls and `matplotlib.use()` placement.
2. CLI commands should follow a consistent pattern: parse -> validate -> compute -> write, with `try/except ClickException` at each transition.
3. Benchmark tests with wall-clock assertions are inherently flaky in CI; prefer relative scaling assertions.
4. TYPE_CHECKING-only imports mixed with runtime imports of the same module inside function bodies are a red flag for confusing import structure.
5. Diverging data (signed quantities like displacement, stress) should always use diverging colormaps with symmetric normalization.

**Review Complete**: Documentation created. All findings documented with specific file locations and actionable recommendations.
