# io — Context for LLMs

## Purpose
Handles all file I/O: parsing Coulomb 3.4 `.inp` input files into `CoulombModel`
objects, and writing computation results to multiple output formats compatible
with Coulomb 3.4 and downstream tools.

## Key Files
| File | Purpose |
|------|---------|
| `inp_parser.py` | State-machine parser for `.inp` files → `CoulombModel` |
| `cou_writer.py` | Write `_dcff.cou` and `_section.cou` (Coulomb 3.4 format) |
| `csv_writer.py` | Write `.csv` grid data and `_summary.txt` |
| `dat_writer.py` | Write `.dat` and fault surface data (GMT-compatible) |

## Key Functions

### Parsing
- **`read_inp(path) -> CoulombModel`** — read `.inp` from disk; auto-detects UTF-8 or latin-1 encoding
- **`parse_inp_string(text) -> CoulombModel`** — parse from a string (useful for tests)
- Both raise `ParseError` on malformed input; all known quirks of real Coulomb 3.4 files are handled

### Writing
- **`write_dcff_cou(result, model, filepath)`** — Coulomb-compatible grid output with columns: x, y, CFS, shear, normal, sxx…sxy
- **`write_section_cou(section, model, filepath)`** — same format for cross-section results
- **`write_csv(result, filepath)`** — tabular grid output; human-readable
- **`write_summary(result, model, filepath)`** — plain-text run summary (stats, receiver orientation, extrema)
- **`write_coulomb_dat(result, filepath, field="cfs")`** — GMT-style `.dat` file for one field; `field` in `{"cfs", "shear", "normal"}`
- **`write_fault_surface_dat(model, filepath)`** — fault surface geometry for 3D visualisation

## Dependencies
- **Depends on**: `opencoulomb.types` (consumes and produces domain types), `pathlib.Path`
- **Used by**: `opencoulomb.cli` (compute and convert commands call all writers)
- **Does not depend on**: `core` or `viz`

## Conventions
- The `.inp` parser is a **state machine** with named states (`HEADER`, `MATERIAL`,
  `SIZE_PARAMS`, `FAULT_TABLE`, `REGIONAL_STRESS`, `CROSS_SECTION`, …)
- Parser bugs in real Coulomb files handled: `.NNN` floats (no leading zero),
  long em-dashes in headers, `XSYM`/`YSYM` aliases for symmetry keywords
- Source vs. receiver split: the first `n_fixed` faults in the fault table are
  sources; the remainder are receivers (zero-slip rows)
- Output paths are always `pathlib.Path`; writers create parent dirs if needed
- `.cou` format columns are space-delimited with a fixed 2-line header; units match Coulomb 3.4 (km, bar, m)
- Encoding fallback: UTF-8 first, then latin-1 (for legacy files with Windows-1252 characters)
