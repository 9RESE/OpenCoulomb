# ADR-003 — State Machine Parser for .inp Files

**Status**: Accepted
**Date**: 2026-02-27
**Deciders**: Backend Engineer, Tech Lead

---

## Context

OpenCoulomb must parse Coulomb 3.4 `.inp` files. The `.inp` format is a legacy text format with the following characteristics:

- **No formal grammar**: the format is defined implicitly by the Coulomb 3.4 MATLAB source code.
- **Position-dependent sections**: some sections are identified by their position in the file, not by explicit keywords.
- **Multiple quirks** discovered during testing with real-world files:
  - Long-dash separators (em-dash `—` and en-dash `–`) used as section delimiters
  - Floating-point numbers written without a leading zero (`.NNN` instead of `0.NNN`)
  - `XSYM`/`YSYM` as aliases for `X_SYM`/`Y_SYM`
  - Mixed whitespace and fixed-column alignment
  - Optional sections (regional stress, cross-section) that may or may not be present
  - Blank lines and comment lines interspersed in some sections
- **Section order is fixed**: sections always appear in the same order, but the boundaries are implicit.

Three parsing approaches were evaluated:

**Option A — Line-by-line with regex**
Process the file line by line, using regex to identify each line's type and extract values. No explicit state tracking.

**Option B — Grammar-based parser (pyparsing or lark)**
Define a formal grammar and use a parser generator.

**Option C — Explicit state machine**
Model parsing as an enumerated set of states with explicit transitions.

---

## Decision

**Option C (explicit state machine)** was chosen.

---

## Rationale

### The format is inherently sequential and stateful

The `.inp` format cannot be parsed line-by-line in isolation because the meaning of a line depends on context:
- Lines 1–2 are always the title.
- Fault lines look identical regardless of whether they are source or receiver faults; only their position (before/after `n_fixed`) distinguishes them.
- Section boundaries are often detected by line count rather than keywords.

A state machine makes this sequentiality explicit and correct.

### Grammar-based parsers are over-engineered for this format

Option B would require writing a formal grammar for an undocumented format with multiple inconsistencies. Grammar generators produce excellent error messages for well-specified grammars; for an ad-hoc format full of quirks, the grammar itself becomes a maintenance burden. Additionally, adding a parser library (pyparsing, lark) introduces a runtime dependency.

### Regex-only is fragile at scale

Option A works for simple cases but becomes increasingly fragile as the number of quirks grows. Without explicit state tracking, it is easy to accidentally process a line in the wrong context. State transitions in the state machine are documented in code and can be unit-tested independently.

### State machine advantages

- **Explicit states** (implemented as a Python `Enum`) make each parser phase named and inspectable.
- **Transition logic** is concentrated in one place, not scattered across many regex conditions.
- **Error reporting** is precise: `ParseError(filename=..., line_number=N)` can identify the state at the time of failure.
- **Testability**: each state handler is a method that can be tested with a small set of input lines.
- **Extensibility**: adding a new optional section (e.g., a future Coulomb 3.5 section) means adding a new state and a transition, not restructuring the parser.

### Discovered quirks handled in the state machine

During development, the state machine approach allowed the following bugs to be fixed cleanly:

| Bug | Fix |
|-----|-----|
| `SIZE PARAMETERS` section not entered when line contains extra whitespace | Normalise line before checking state trigger |
| `XSYM`/`YSYM` not recognised | Add aliases in the `GRID_SPEC` state handler |
| `.NNN` floats rejected by `float()` | Pre-process: replace `^\.` with `0.` in numeric fields |
| Long-dash (`—`) separator lines not skipped | Add em-dash and en-dash to the skip-line set |

Each fix was localised to the relevant state handler with zero impact on other states.

---

## Consequences

**Positive:**
- Handles all 7 real-world Coulomb 3.4 `.inp` files without modification.
- Clear error messages with line numbers.
- Each state handler is independently unit-testable.
- No runtime dependency on a parser library.

**Negative:**
- More code than a simple line-by-line reader for simple files.
- State machine logic must be understood to add support for new format variants.

**Mitigations:**
- States are documented with docstrings explaining what they expect.
- The parser is tested with both synthetic edge-case files (in `tests/fixtures/inp_files/synthetic/`) and real files (in `tests/fixtures/inp_files/real/`).

---

## References

- Coulomb 3.4 source: Toda, S., Stein, R.S., et al. (2011). Coulomb 3.3 Graphic-Rich Deformation and Stress-Change Software for Earthquake, Tectonic, and Volcano Research and Teaching. USGS Open-File Report 2011-1060.
- Real `.inp` test files: `tests/fixtures/inp_files/real/` (7 files)
- Parser implementation: `src/opencoulomb/io/inp_parser.py`
