# Code Review: OpenCoulomb I/O Module

## Review Summary
**Reviewer**: Code Review Agent (claude-sonnet-4-6)
**Date**: 2026-02-27
**Scope**: `src/opencoulomb/io/` — inp_parser, cou_writer, csv_writer, dat_writer, __init__
**Files Reviewed**: 5 files (~800 lines of production code)
**Issues Found**: 13 (4 HIGH, 4 MEDIUM, 5 LOW)

---

## Key Findings

### HIGH Severity Issues

#### H1 — `PermissionError`/`OSError` Not Caught in `read_inp`
**File**: `src/opencoulomb/io/inp_parser.py:56-60`

`read_inp` catches `UnicodeDecodeError` for the UTF-8 fallback path but wraps nothing else around the `p.read_text()` calls. A file that exists but is not readable (permission denied, broken symlink, directory) raises a raw OS exception bypassing the `ParseError` hierarchy.

**Fix**:
```python
try:
    text = p.read_text(encoding="utf-8")
except UnicodeDecodeError:
    try:
        text = p.read_text(encoding="latin-1")
    except OSError as exc:
        raise ParseError(f"Cannot read file: {exc}", filename=str(p)) from exc
except OSError as exc:
    raise ParseError(f"Cannot read file: {exc}", filename=str(p)) from exc
```

#### H2 — `ZeroDivisionError` for Horizontal Faults (dip=0) in `_fault_polygon_corners`
**File**: `src/opencoulomb/io/dat_writer.py:101-123`

The function guards against `dip >= 90` but not `dip = 0`. Both `depth_diff / math.tan(dip_rad)` and `fault.top_depth / math.tan(dip_rad)` raise `ZeroDivisionError` when `dip = 0.0`. A horizontal fault is a valid `FaultElement` (type validator accepts `[0, 90]`).

**Fix**:
```python
DIP_THRESHOLD = 1e-6  # degrees

if fault.dip <= DIP_THRESHOLD or fault.dip >= 90.0:
    h_offset = 0.0
else:
    h_offset = depth_diff / math.tan(dip_rad)

if fault.dip <= DIP_THRESHOLD or fault.dip >= 90.0:
    h_offset_top = 0.0
else:
    h_offset_top = fault.top_depth / math.tan(dip_rad)
```

#### H3 — Writers Do Not Wrap `OSError` in `OutputError`
**Files**: `cou_writer.py:40`, `csv_writer.py:38,84`, `dat_writer.py:50,73`

All writer functions propagate raw `FileNotFoundError`/`PermissionError` to callers. The `OutputError` exception class exists for this purpose but is unused by the writers. A caller cannot write a single `except OpenCoulombError` handler covering both read and write failures.

**Fix**: Wrap each `filepath.open("w")` in `try/except OSError` re-raising as `OutputError`.

#### H4 — Multiline Title Corrupts `.cou` File Header
**Files**: `inp_parser.py:546`, `cou_writer.py:42,93`

`_build_model` joins the two title lines with a literal `\n`:
```python
title = "\n".join(self._title_lines)
```

`write_dcff_cou` writes the title directly into what must be a single header line:
```python
f.write(f"  Coulomb Stress Change (bar) — {model.title}\n")
```

The output file gets 4 header lines instead of 3. Downstream tools expecting exactly 3 headers will misread column indices for all data rows.

**Demonstrated output**:
```
[0]: '  Coulomb Stress Change (bar) — Line 1\n'
[1]: 'Line 2\n'              <- spurious extra line
[2]: '  friction = 0.40 ...\n'
[3]: '        X(km) ...\n'   <- column header now at line 4
[4]: '       0.0000 ...\n'   <- first data row now at line 5
```

**Fix**: Strip/replace newlines in the title before writing:
```python
safe_title = model.title.replace("\n", " | ")
f.write(f"  Coulomb Stress Change (bar) - {safe_title}\n")
```

---

### MEDIUM Severity Issues

#### M1 — `KeyError` for Invalid `field` in `write_coulomb_dat`
**File**: `src/opencoulomb/io/dat_writer.py:49`

Passing an unknown `field` string raises a bare `KeyError` with no hint of valid values.

**Fix**:
```python
_VALID_FIELDS = frozenset({"cfs", "shear", "normal", "ux", "uy", "uz"})
if field not in _VALID_FIELDS:
    raise ValueError(f"Invalid field {field!r}. Must be one of: {sorted(_VALID_FIELDS)}")
```

#### M2 — Cross-Section Distance Increment (Parameter 5) Silently Discarded
**File**: `src/opencoulomb/io/inp_parser.py:527-542`

Coulomb 3.4 cross-section parameter 5 ("Distant-increment", the horizontal spacing along the profile) is required for validation but never used in `CrossSectionSpec` construction. `CrossSectionSpec` has no `h_inc` field.

**Fix**: Add `h_inc: float` to `CrossSectionSpec` and map parameter 5 to it.

#### M3 — `_ParserState.STRESS` and `_on_stress` Are Dead Code
**File**: `src/opencoulomb/io/inp_parser.py:121,235-237`

`STRESS` state is defined in the enum and mapped in `_dispatch`, but no transition ever sets `self._state = _ParserState.STRESS`. Verified by tracing all 32 fixture files. The `# pragma: no cover` comment on `_on_stress` confirms this is known.

**Fix**: Remove `_ParserState.STRESS` from the enum and its entry from `_dispatch`.

#### M4 — Handler Dict Rebuilt on Every `_dispatch` Call
**File**: `src/opencoulomb/io/inp_parser.py:187-201`

```python
def _dispatch(self, line: str) -> None:
    handler: dict[...] = {   # rebuilt every line
        _ParserState.START: self._on_start,
        ...
    }
    handler[self._state](line)
```

For a 900-fault file, `_dispatch` is called ~944 times, each time allocating and populating an 11-entry dict.

**Fix**: Build the dict once in `__init__`, store as `self._handlers`, look up in `_dispatch`.

---

### LOW Severity Issues

#### L1 — `ParseError` Reports `line_number=0` for Empty Files
**File**: `src/opencoulomb/io/inp_parser.py:170`

Empty-file detection fires before `self._lineno` is set to 1. `ParseError.line_number = 0` is meaningless for 1-based line numbers.

**Fix**: Omit `line_number` for the empty-file case:
```python
raise ParseError("Empty input", filename=self._filename)
```

#### L2 — `numpy` Imported Inside `write_summary` Function Body
**File**: `src/opencoulomb/io/csv_writer.py:77`

```python
def write_summary(...) -> None:
    import numpy as np   # local import
```

**Fix**: Move `import numpy as np` to the module top-level.

#### L3 — Writers Use System-Default Encoding
**Files**: `cou_writer.py:40,92`, `csv_writer.py:38,84`, `dat_writer.py:73`

`filepath.open("w")` without an `encoding` argument uses the platform default (may vary on Windows). The reader already handles UTF-8/latin-1 explicitly.

**Fix**: Add `encoding="utf-8"` to all writer `open()` calls.

#### L4 — `_current_line()` Defined But Never Called
**File**: `src/opencoulomb/io/inp_parser.py:154-155`

Dead helper method.

**Fix**: Remove.

#### L5 — Non-ASCII Em Dash in `.cou` Header
**Files**: `cou_writer.py:42,93`, `dat_writer.py:75`

Em dash (`—`, U+2014) in header lines departs from Coulomb 3.4's pure-ASCII output. May cause failures in legacy byte-oriented parsing scripts.

**Fix**: Replace with ASCII hyphen `-`.

---

## Positive Findings

- All file opens in writers use context managers (`with ... open(...)`). No resource leaks.
- `np.savetxt` in `dat_writer.py` correctly receives a `Path` object and handles its own file lifecycle.
- The UTF-8 → latin-1 fallback in `read_inp` is correct and handles real Coulomb 3.4 files (verified: `Landers_variable_slip.inp` contains byte 0xA1).
- The `_KV_RE` regex correctly matches all real Coulomb 3.4 parameter formats: scientific notation (`0.800000E+06`), leading-dot floats (`.250`), negative values, and compound lines with multiple key=value pairs.
- The `_GRID_LINE_RE` handles both short-dash (`---`) and long-dash (`----------------------------`) separators found in different Coulomb 3.4 versions.
- All 32 fixture files (USGS finite fault, Coulomb 3.4 examples, real seismic events) parse without errors.
- `_looks_like_fault_line` correctly returns `False` for grid parameter lines that start with a digit, preventing false-positive fault parsing.

---

## Testing Validation

- All 32 fixture `.inp` files parse successfully with current code.
- HIGH-severity bugs (H2, H4) are confirmed by test execution.
- Tests needed (not yet present):
  - `test_read_inp_permission_denied` — verifies H1 fix
  - `test_fault_polygon_dip_zero` — verifies H2 fix
  - `test_write_dcff_cou_bad_path_raises_output_error` — verifies H3 fix
  - `test_cou_header_row_count_multiline_title` — verifies H4 fix
  - `test_write_coulomb_dat_invalid_field` — verifies M1 fix

---

## Patterns Learned

1. **Two-part title join with `\n` is dangerous for single-line format outputs.** When a multi-line model attribute must appear in a single output line, sanitize it at write time, not at parse time.
2. **Dip range guards should be symmetric.** When guarding `tan(dip)` for vertical faults (`dip >= 90`), always pair with a guard for horizontal faults (`dip <= epsilon`).
3. **Exception hierarchy must be used consistently.** Defining `OutputError` but not raising it in writer code creates an inconsistent contract.
4. **Dict construction in hot loops is measurable overhead.** Even microsecond-level dict allocation adds up at 900+ calls; build once in `__init__`.

---

## Knowledge Contributions

- Updated pattern: "Writers must wrap OSError in the output exception type" added to security/error-handling standards.
- Updated pattern: "All geometric operations on dip angle need both upper (90) and lower (0) guards."
- Issue tracker: cross-section `h_inc` missing from `CrossSectionSpec` — Phase C task candidate.

**Review Complete**: Issues documented. HIGH-severity fixes required before Phase C integration.
