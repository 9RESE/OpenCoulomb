"""Parser for Coulomb 3.4 .inp files.

Implements a state-machine parser that reads the .inp text format
and produces a :class:`CoulombModel` instance.

Public API
----------
- :func:`read_inp` -- read from a file path
- :func:`parse_inp_string` -- parse from a string
"""

from __future__ import annotations

import re
from collections.abc import Callable
from enum import Enum, auto
from pathlib import Path

from opencoulomb.exceptions import ParseError
from opencoulomb.types.fault import FaultElement, Kode
from opencoulomb.types.grid import GridSpec
from opencoulomb.types.material import MaterialProperties
from opencoulomb.types.model import CoulombModel
from opencoulomb.types.section import CrossSectionSpec
from opencoulomb.types.stress import PrincipalStress, RegionalStress

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def read_inp(path: str | Path) -> CoulombModel:
    """Parse a Coulomb 3.4 .inp file from disk.

    Parameters
    ----------
    path : str or Path
        Path to the .inp file.

    Returns
    -------
    CoulombModel
        Fully populated model ready for computation.

    Raises
    ------
    ParseError
        If the file cannot be read or the format is invalid.
    """
    p = Path(path)
    if not p.exists():
        raise ParseError(f"File not found: {p}", filename=str(p))
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = p.read_text(encoding="latin-1")
    except OSError as exc:
        raise ParseError(f"Cannot read file: {exc}", filename=str(p)) from exc
    return parse_inp_string(text, filename=str(p))


def parse_inp_string(text: str, filename: str = "<string>") -> CoulombModel:
    """Parse .inp format from a string.

    Parameters
    ----------
    text : str
        Full contents of a .inp file.
    filename : str
        Display name for error messages. Default: ``"<string>"``.

    Returns
    -------
    CoulombModel
        Fully populated model.

    Raises
    ------
    ParseError
        If the format is invalid.
    """
    parser = _InpParser(text, filename)
    return parser.parse()


# ---------------------------------------------------------------------------
# Internal: state machine
# ---------------------------------------------------------------------------

# Regex for extracting KEY=VALUE pairs from parameter lines.
# Handles integers, floats, and scientific notation (e.g. 0.800000E+06).
# Also handles values without leading digit (e.g. .250, .000).
_KV_RE = re.compile(
    r"([#\w]+)\s*=\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)"
)

# Regex for grid/cross-section numbered parameter lines:
#   "  1  ---  Start-x =    -100.000"
#   "  1  ----------------------------  Start-x =     -127.2099991"
# Uses -+ to match variable numbers of dashes.
_GRID_LINE_RE = re.compile(
    r"^\s*(\d+)\s+-+\s+(.+?)\s*=\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*$"
)

# Column header detector -- line starts with # and contains "X-start"
_COLUMN_HEADER_RE = re.compile(r"^\s*#\s+X-start", re.IGNORECASE)

# "xxx" placeholder line that appears right after the column header
_PLACEHOLDER_RE = re.compile(r"^\s*xxx\s")


class _ParserState(Enum):
    """States for the .inp parser state machine."""

    START = auto()
    TITLE_LINE2 = auto()
    PARAMS = auto()
    FAULTS_HEADER = auto()
    SOURCE_FAULTS = auto()
    RECEIVER_HEADER = auto()
    RECEIVER_FAULTS = auto()
    GRID = auto()
    CROSS_SECTION = auto()
    MAP_INFO = auto()
    DONE = auto()


class _InpParser:
    """State-machine parser for .inp files."""

    def __init__(self, text: str, filename: str) -> None:
        self._filename = filename
        self._lines = text.splitlines()
        self._lineno = 0  # 1-based, updated as we consume lines
        self._state = _ParserState.START

        # Accumulated results
        self._title_lines: list[str] = []
        self._param_text = ""  # concatenated parameter lines
        self._params: dict[str, str] = {}
        self._faults: list[FaultElement] = []
        self._grid_params: dict[int, float] = {}
        self._cross_section_params: dict[int, float] = {}
        self._n_fixed: int = 0

        # State dispatch table (built once, not per-line)
        _handler_t = dict[_ParserState, Callable[[str], None]]
        self._handlers: _handler_t = {
            _ParserState.START: self._on_start,
            _ParserState.TITLE_LINE2: self._on_title_line2,
            _ParserState.PARAMS: self._on_params,
            _ParserState.FAULTS_HEADER: self._on_faults_header,
            _ParserState.SOURCE_FAULTS: self._on_source_faults,
            _ParserState.RECEIVER_HEADER: self._on_receiver_header,
            _ParserState.RECEIVER_FAULTS: self._on_receiver_faults,
            _ParserState.GRID: self._on_grid,
            _ParserState.CROSS_SECTION: self._on_cross_section,
            _ParserState.MAP_INFO: self._on_map_info,
            _ParserState.DONE: lambda _line: None,
        }

    # -- helpers ----------------------------------------------------------

    def _error(self, msg: str) -> ParseError:
        return ParseError(msg, filename=self._filename, line_number=self._lineno)

    def _is_blank(self, line: str) -> bool:
        return line.strip() == ""

    def _is_column_header(self, line: str) -> bool:
        return bool(_COLUMN_HEADER_RE.search(line))

    def _is_placeholder_line(self, line: str) -> bool:
        return bool(_PLACEHOLDER_RE.match(line))

    # -- main driver ------------------------------------------------------

    def parse(self) -> CoulombModel:
        """Run the state machine and return a CoulombModel."""
        if not self._lines:
            raise ParseError("Empty input", filename=self._filename)

        self._lineno = 0
        self._state = _ParserState.START

        for idx, line in enumerate(self._lines):
            self._lineno = idx + 1  # 1-based
            self._dispatch(line)
            if self._state == _ParserState.DONE:
                break

        # Build the model from accumulated data
        return self._build_model()

    def _dispatch(self, line: str) -> None:
        """Dispatch a single line to the current state handler."""
        self._handlers[self._state](line)

    # -- state handlers ---------------------------------------------------

    def _on_start(self, line: str) -> None:
        self._title_lines.append(line.strip())
        self._state = _ParserState.TITLE_LINE2

    def _on_title_line2(self, line: str) -> None:
        self._title_lines.append(line.strip())
        self._state = _ParserState.PARAMS

    def _on_params(self, line: str) -> None:
        """Accumulate parameter lines until we hit a blank line or column header."""
        stripped = line.strip()

        # A blank line after parameters signals transition to looking for
        # the fault column header.
        if self._is_blank(line):
            # Only transition if we have accumulated some params
            if self._param_text:
                self._extract_params()
                self._state = _ParserState.FAULTS_HEADER
            return

        # Column header encountered directly (no blank line separator)
        if self._is_column_header(line):
            if self._param_text:
                self._extract_params()
            self._state = _ParserState.SOURCE_FAULTS
            return

        self._param_text += " " + stripped

    def _on_faults_header(self, line: str) -> None:
        """Waiting for the column header line for source faults."""
        if self._is_blank(line):
            return  # skip extra blank lines
        if self._is_column_header(line):
            self._state = _ParserState.SOURCE_FAULTS
            return
        # Could be the "Grid Parameters" keyword if there are no faults
        if line.strip().lower().startswith("grid parameters"):
            self._state = _ParserState.GRID
            return
        # If we see a numeric fault line without a header, parse it
        if self._looks_like_fault_line(line):
            self._parse_fault_line(line)
            self._state = _ParserState.SOURCE_FAULTS
            return
        # Otherwise skip (might be extra header text)

    def _on_source_faults(self, line: str) -> None:
        """Parse source fault element lines."""
        if self._is_blank(line):
            # Blank line ends the source fault block
            self._state = _ParserState.RECEIVER_HEADER
            return
        if self._is_column_header(line) or self._is_placeholder_line(line):
            return  # skip column header / placeholder lines
        if line.strip().lower().startswith("grid parameters"):
            self._state = _ParserState.GRID
            return
        self._parse_fault_line(line)

    def _on_receiver_header(self, line: str) -> None:
        """Waiting for receiver fault column header or grid parameters."""
        if self._is_blank(line):
            return
        if self._is_column_header(line):
            self._state = _ParserState.RECEIVER_FAULTS
            return
        if self._is_placeholder_line(line):
            return  # skip placeholder rows
        if line.strip().lower().startswith("grid parameters"):
            self._state = _ParserState.GRID
            return
        # Numeric fault line without separate header
        if self._looks_like_fault_line(line):
            self._parse_fault_line(line)
            self._state = _ParserState.RECEIVER_FAULTS
            return

    def _on_receiver_faults(self, line: str) -> None:
        """Parse receiver fault element lines."""
        if self._is_blank(line):
            # Blank line ends the receiver block -- next is grid
            self._state = _ParserState.GRID
            return
        if self._is_column_header(line) or self._is_placeholder_line(line):
            return
        if line.strip().lower().startswith("grid parameters"):
            self._state = _ParserState.GRID
            return
        self._parse_fault_line(line)

    def _on_grid(self, line: str) -> None:
        """Parse grid parameter lines.

        Stays in GRID state across blank lines so that "Size Parameters"
        sections (which appear between Grid Parameters and Cross Section)
        are consumed without premature state transition.
        """
        stripped = line.strip()
        if not stripped:
            return
        if stripped.lower().startswith("grid parameters"):
            return  # skip the keyword line itself
        if stripped.lower().startswith("cross section"):
            self._state = _ParserState.CROSS_SECTION
            return
        # "Size Parameters" section appears between Grid Parameters and
        # Cross Section in real Coulomb files.  Stay in GRID state -- the
        # numbered lines (1,2,3) are harmlessly skipped by the idx guard
        # because grid indices 1-6 are already populated.
        if stripped.lower().startswith("size parameters"):
            return
        if stripped.lower().startswith("map info"):
            self._state = _ParserState.MAP_INFO
            return

        m = _GRID_LINE_RE.match(line)
        if m:
            idx = int(m.group(1))
            val = float(m.group(3))
            # Only capture grid params (indices 1-6), not Size Parameters
            if idx <= 6 and idx not in self._grid_params:
                self._grid_params[idx] = val

    def _on_cross_section(self, line: str) -> None:
        """Parse cross-section parameter lines."""
        stripped = line.strip()
        if not stripped:
            if self._cross_section_params:
                self._state = _ParserState.MAP_INFO
            return
        if stripped.lower().startswith("cross section"):
            return  # skip keyword line
        if stripped.lower().startswith("map info"):
            self._state = _ParserState.MAP_INFO
            return

        m = _GRID_LINE_RE.match(line)
        if m:
            idx = int(m.group(1))
            val = float(m.group(3))
            self._cross_section_params[idx] = val

    def _on_map_info(self, line: str) -> None:
        """Skip map info lines (not used in computation)."""
        # We just consume lines until EOF
        pass

    # -- fault parsing ----------------------------------------------------

    def _looks_like_fault_line(self, line: str) -> bool:
        """Quick heuristic: does this line start with a number?"""
        tokens = line.split()
        if len(tokens) < 11:
            return False
        try:
            int(tokens[0])
            return True
        except ValueError:
            return False

    def _parse_fault_line(self, line: str) -> None:
        """Parse one fault element line into a FaultElement."""
        tokens = line.split()
        if len(tokens) < 11:
            raise self._error(
                f"Fault line has {len(tokens)} tokens, expected at least 11"
            )

        try:
            element_index = int(tokens[0])
            x_start = float(tokens[1])
            y_start = float(tokens[2])
            x_fin = float(tokens[3])
            y_fin = float(tokens[4])
            kode_raw = int(tokens[5])
            slip_1 = float(tokens[6])
            slip_2 = float(tokens[7])
            dip = float(tokens[8])
            top_depth = float(tokens[9])
            bottom_depth = float(tokens[10])
        except (ValueError, IndexError) as exc:
            raise self._error(f"Cannot parse fault element: {exc}") from exc

        # Remaining tokens form the label
        label = " ".join(tokens[11:]) if len(tokens) > 11 else ""

        # Validate kode
        try:
            kode = Kode(kode_raw)
        except ValueError as exc:
            raise self._error(
                f"Invalid fault element kode {kode_raw}; "
                f"valid values: {[k.value for k in Kode]}"
            ) from exc

        try:
            fault = FaultElement(
                x_start=x_start,
                y_start=y_start,
                x_fin=x_fin,
                y_fin=y_fin,
                kode=kode,
                slip_1=slip_1,
                slip_2=slip_2,
                dip=dip,
                top_depth=top_depth,
                bottom_depth=bottom_depth,
                label=label,
                element_index=element_index,
            )
        except Exception as exc:
            raise self._error(f"Invalid fault element: {exc}") from exc

        self._faults.append(fault)

    # -- parameter extraction ---------------------------------------------

    def _extract_params(self) -> None:
        """Extract all key=value pairs from the concatenated parameter text."""
        for m in _KV_RE.finditer(self._param_text):
            key = m.group(1).upper()
            value = m.group(2)
            self._params[key] = value

    def _float_param(self, key: str, default: float | None = None) -> float:
        upper = key.upper()
        if upper in self._params:
            try:
                return float(self._params[upper])
            except ValueError as exc:
                raise self._error(
                    f"Cannot parse float for {key}={self._params[upper]}"
                ) from exc
        if default is not None:
            return default
        raise self._error(f"Required parameter '{key}' not found")

    def _int_param(self, key: str, default: int | None = None) -> int:
        upper = key.upper()
        if upper in self._params:
            try:
                return int(float(self._params[upper]))
            except ValueError as exc:
                raise self._error(
                    f"Cannot parse int for {key}={self._params[upper]}"
                ) from exc
        if default is not None:
            return default
        raise self._error(f"Required parameter '{key}' not found")

    # -- model construction -----------------------------------------------

    def _build_material(self) -> MaterialProperties:
        return MaterialProperties(
            poisson=self._float_param("PR1", 0.25),
            young=self._float_param("E1", 8.0e5),
            friction=self._float_param("FRIC", 0.4),
            depth=self._float_param("DEPTH", 10.0),
        )

    def _build_regional_stress(self) -> RegionalStress | None:
        """Build RegionalStress if S1/S2/S3 parameters are present."""
        # Check if we have at least the S1 parameters
        if "S1DR" not in self._params:
            return None

        s1 = PrincipalStress(
            direction=self._float_param("S1DR"),
            dip=self._float_param("S1DP"),
            intensity=self._float_param("S1IN"),
            gradient=self._float_param("S1GD"),
        )
        s3 = PrincipalStress(
            direction=self._float_param("S3DR"),
            dip=self._float_param("S3DP"),
            intensity=self._float_param("S3IN"),
            gradient=self._float_param("S3GD"),
        )
        s2 = PrincipalStress(
            direction=self._float_param("S2DR"),
            dip=self._float_param("S2DP"),
            intensity=self._float_param("S2IN"),
            gradient=self._float_param("S2GD"),
        )
        return RegionalStress(s1=s1, s2=s2, s3=s3)

    def _build_grid(self) -> GridSpec:
        """Build GridSpec from numbered grid parameters."""
        if not self._grid_params:
            raise self._error("No grid parameters found")

        required = {1, 2, 3, 4, 5, 6}
        missing = required - set(self._grid_params)
        if missing:
            raise self._error(f"Missing grid parameters: {sorted(missing)}")

        return GridSpec(
            start_x=self._grid_params[1],
            start_y=self._grid_params[2],
            finish_x=self._grid_params[3],
            finish_y=self._grid_params[4],
            x_inc=self._grid_params[5],
            y_inc=self._grid_params[6],
            depth=self._float_param("DEPTH", 10.0),
        )

    def _build_cross_section(self) -> CrossSectionSpec | None:
        """Build CrossSectionSpec if cross-section parameters are present."""
        if not self._cross_section_params:
            return None

        required = {1, 2, 3, 4, 5, 6, 7}
        missing = required - set(self._cross_section_params)
        if missing:
            raise self._error(f"Missing cross-section parameters: {sorted(missing)}")

        # Coulomb 3.4 cross-section parameters:
        #   1-4: Start/finish XY coordinates of the profile line
        #   5: Distance increment along profile (horizontal spacing)
        #   6: Z-depth (maximum depth; negative = below surface in C3.4 convention)
        #   7: Z-increment (vertical spacing)
        # Our CrossSectionSpec uses depth_min=0 (surface) and positive depth_max.
        z_depth = self._cross_section_params[6]
        return CrossSectionSpec(
            start_x=self._cross_section_params[1],
            start_y=self._cross_section_params[2],
            finish_x=self._cross_section_params[3],
            finish_y=self._cross_section_params[4],
            depth_min=0.0,
            depth_max=abs(z_depth),
            z_inc=abs(self._cross_section_params[7]),
        )

    def _build_model(self) -> CoulombModel:
        """Assemble everything into a CoulombModel."""
        title = "\n".join(self._title_lines)
        material = self._build_material()
        grid = self._build_grid()
        regional_stress = self._build_regional_stress()

        n_fixed = self._int_param("#FIXED", 0)

        # Validate n_fixed against number of faults
        if n_fixed > len(self._faults):
            raise self._error(
                f"#fixed={n_fixed} but only {len(self._faults)} fault elements found"
            )

        symmetry = self._int_param("SYM", 1)
        # Real Coulomb files use XSYM/YSYM; some use XLIM/YLIM.
        x_sym = self._float_param("XSYM", None) if "XSYM" in self._params else self._float_param("XLIM", 0.0)
        y_sym = self._float_param("YSYM", None) if "YSYM" in self._params else self._float_param("YLIM", 0.0)

        model = CoulombModel(
            title=title,
            material=material,
            faults=self._faults,
            grid=grid,
            n_fixed=n_fixed,
            regional_stress=regional_stress,
            cross_section=self._build_cross_section(),
            symmetry=symmetry,
            x_sym=x_sym,
            y_sym=y_sym,
        )

        return model
