# cli — Context for LLMs

## Purpose
Click-based command-line interface for OpenCoulomb. Wires together `io`, `core`,
and `viz` into user-facing subcommands invoked as `opencoulomb <command>`.

## Key Files
| File | Purpose |
|------|---------|
| `main.py` | Root Click group (`cli`); registers all subcommands |
| `compute.py` | `compute` — parse .inp, run full grid computation, write outputs |
| `validate.py` | `validate` — parse .inp and report geometry/grid warnings |
| `info.py` | `info` — print model summary (faults, grid, material) without computing |
| `plot.py` | `plot` — render CFS map or cross-section from a result file |
| `convert.py` | `convert` — convert between output formats (re-write existing results) |
| `_logging.py` | `setup_logging(verbose)` — configures the `opencoulomb` logger |

## Key Commands

### `opencoulomb compute <inp_file> [options]`
Full pipeline: parse → `compute_grid` → (optionally) `compute_cross_section` → write outputs.
- `--output-dir / -o` — destination directory (default: same as input)
- `--format / -f` — one or more of `cou`, `csv`, `dat`, `all` (default: `all`)
- `--field` — which field for `.dat`: `cfs`, `shear`, or `normal` (default: `cfs`)
- `--receiver` — 0-based receiver fault index for CFS resolution
- `--cross-section / --no-cross-section` — compute profile if model has one (default: on)

### `opencoulomb validate <inp_file>`
Parse and check; reports warnings (zero-length faults, very large grids, deep faults, etc.).
Exit code 0 even with warnings (issues are non-fatal).

### `opencoulomb info <inp_file>`
Print model metadata: title, material constants, grid bounds, fault count, cross-section.
No computation performed.

### `opencoulomb plot <result_file> [options]`
Render a saved result file (`.cou` or `.csv`) as a CFS map or cross-section.

### `opencoulomb convert <inp_file> [options]`
Re-run computation and write in a different output format.

## Dependencies
- **Depends on**: `opencoulomb.io` (parse + write), `opencoulomb.core` (compute), `opencoulomb.viz` (plot), `click`
- **Does not contain** business logic — all heavy lifting delegated to `core` and `io`

## Conventions
- All commands use lazy imports inside the command function body to keep startup fast
- Logging is controlled via `setup_logging(verbose)`: `verbose=True` → DEBUG, else INFO
- Logger name is `"opencoulomb"` throughout the package
- Output filenames follow the pattern `{stem}_{suffix}.{ext}` (e.g., `myhama_dcff.cou`)
- The CLI entry point is declared in `pyproject.toml` as `opencoulomb = "opencoulomb.cli.main:cli"`
- `click.ClickException` is raised (not raw exceptions) so Click formats error messages consistently
