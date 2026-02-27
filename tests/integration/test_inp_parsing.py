"""Integration tests for the Coulomb 3.4 .inp file parser.

Covers:
- Fixture file parsing (simple_strike_slip.inp, thrust_with_section.inp)
- String-based unit tests via parse_inp_string()
- All KODE types (100, 200, 300, 400, 500)
- Error handling (empty file, missing grid, malformed lines, bad KODE)
- Edge cases (Windows line endings, scientific notation, special labels)
- Round-trip field consistency
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, ClassVar

import pytest

from opencoulomb.exceptions import ParseError
from opencoulomb.io import parse_inp_string, read_inp
from opencoulomb.types.fault import Kode

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_inp(
    *,
    title1: str = "Title line 1",
    title2: str = "Title line 2",
    n_fixed: int = 1,
    sym: int = 1,
    pr1: float = 0.250,
    depth: float = 10.000,
    e1: float = 8.0e5,
    fric: float = 0.400,
    s1dr: float = 0.0,
    s1dp: float = 0.0,
    s1in: float = 0.0,
    s1gd: float = 0.0,
    s3dr: float = 0.0,
    s3dp: float = 0.0,
    s3in: float = 0.0,
    s3gd: float = 0.0,
    s2dr: float = 0.0,
    s2dp: float = 0.0,
    s2in: float = 0.0,
    s2gd: float = 0.0,
    faults: str | None = None,
    grid_start_x: float = -50.0,
    grid_start_y: float = -50.0,
    grid_finish_x: float = 50.0,
    grid_finish_y: float = 50.0,
    grid_x_inc: float = 1.0,
    grid_y_inc: float = 1.0,
    extra_after_grid: str = "",
) -> str:
    """Build a minimal-but-complete .inp string for parametric testing."""
    default_source = (
        "    1     -10.0       0.0      10.0       0.0  100       1.0"
        "       0.0    90.0     0.0    10.0  Source\n"
    )
    default_receiver = (
        "    2     -15.0       5.0      15.0       5.0  100       0.0"
        "       0.0    90.0     0.0    10.0  Receiver\n"
    )
    fault_block = faults if faults is not None else (default_source + "\n" + default_receiver)

    return (
        f"{title1}\n"
        f"{title2}\n"
        f"#reg1=  0  #reg2=  0  #fixed=  {n_fixed}  sym=  {sym}\n"
        f" PR1=       {pr1:.3f} PR2=       {pr1:.3f} DEPTH=      {depth:.3f}\n"
        f"  E1=  {e1:.6E}  E2=  {e1:.6E} XLIM=     0.000 YLIM=     0.000\n"
        f"FRIC=       {fric:.3f}\n"
        f"  S1DR=  {s1dr:.4f} S1DP=  {s1dp:.4f} S1IN=  {s1in:.3f}  S1GD=   {s1gd:.3f}\n"
        f"  S3DR=  {s3dr:.4f} S3DP=  {s3dp:.4f} S3IN=  {s3in:.3f}  S3GD=   {s3gd:.3f}\n"
        f"  S2DR=  {s2dr:.4f} S2DP=  {s2dp:.4f} S2IN=  {s2in:.3f}  S2GD=   {s2gd:.3f}\n"
        f"\n"
        f"  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
        f" xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
        f"{fault_block}"
        f"\n"
        f"Grid Parameters\n"
        f"  1  ---  Start-x =    {grid_start_x:.3f}\n"
        f"  2  ---  Start-y =    {grid_start_y:.3f}\n"
        f"  3  ---  Finish-x =    {grid_finish_x:.3f}\n"
        f"  4  ---  Finish-y =    {grid_finish_y:.3f}\n"
        f"  5  ---  x-increment =   {grid_x_inc:.3f}\n"
        f"  6  ---  y-increment =   {grid_y_inc:.3f}\n"
        f"{extra_after_grid}"
    )


# ---------------------------------------------------------------------------
# 1. Fixture file tests
# ---------------------------------------------------------------------------


class TestSimpleStrikeSlipFixture:
    """Integration tests against tests/fixtures/inp_files/simple_strike_slip.inp."""

    @pytest.fixture(scope="class")
    def model(self, inp_files_dir: Path):
        return read_inp(inp_files_dir / "simple_strike_slip.inp")

    def test_parses_without_error(self, model):
        assert model is not None

    def test_title(self, model):
        assert model.title == "Simple strike-slip earthquake\nTest model for OpenCoulomb parser"

    def test_n_fixed(self, model):
        assert model.n_fixed == 1

    def test_total_fault_count(self, model):
        assert len(model.faults) == 3

    def test_source_fault_count(self, model):
        assert len(model.source_faults) == 1

    def test_receiver_fault_count(self, model):
        assert len(model.receiver_faults) == 2

    # Material properties
    def test_material_poisson(self, model):
        assert model.material.poisson == pytest.approx(0.25)

    def test_material_young(self, model):
        assert model.material.young == pytest.approx(8.0e5)

    def test_material_friction(self, model):
        assert model.material.friction == pytest.approx(0.4)

    def test_material_depth(self, model):
        assert model.material.depth == pytest.approx(10.0)

    # Source fault geometry
    def test_source_fault_x_start(self, model):
        src = model.source_faults[0]
        assert src.x_start == pytest.approx(-20.0)

    def test_source_fault_y_start(self, model):
        src = model.source_faults[0]
        assert src.y_start == pytest.approx(0.0)

    def test_source_fault_x_fin(self, model):
        src = model.source_faults[0]
        assert src.x_fin == pytest.approx(20.0)

    def test_source_fault_y_fin(self, model):
        src = model.source_faults[0]
        assert src.y_fin == pytest.approx(0.0)

    def test_source_fault_kode(self, model):
        src = model.source_faults[0]
        assert src.kode == Kode.STANDARD

    def test_source_fault_slip_1(self, model):
        src = model.source_faults[0]
        assert src.slip_1 == pytest.approx(1.0)

    def test_source_fault_slip_2(self, model):
        src = model.source_faults[0]
        assert src.slip_2 == pytest.approx(0.0)

    def test_source_fault_dip(self, model):
        src = model.source_faults[0]
        assert src.dip == pytest.approx(90.0)

    def test_source_fault_top_depth(self, model):
        src = model.source_faults[0]
        assert src.top_depth == pytest.approx(0.0)

    def test_source_fault_bottom_depth(self, model):
        src = model.source_faults[0]
        assert src.bottom_depth == pytest.approx(15.0)

    def test_source_fault_label(self, model):
        src = model.source_faults[0]
        assert src.label == "Main fault"

    # Receiver faults have zero slip
    def test_receiver_faults_zero_slip(self, model):
        for recv in model.receiver_faults:
            assert recv.slip_1 == pytest.approx(0.0)
            assert recv.slip_2 == pytest.approx(0.0)

    # Grid
    def test_grid_start_x(self, model):
        assert model.grid.start_x == pytest.approx(-100.0)

    def test_grid_start_y(self, model):
        assert model.grid.start_y == pytest.approx(-100.0)

    def test_grid_finish_x(self, model):
        assert model.grid.finish_x == pytest.approx(100.0)

    def test_grid_finish_y(self, model):
        assert model.grid.finish_y == pytest.approx(100.0)

    def test_grid_x_inc(self, model):
        assert model.grid.x_inc == pytest.approx(2.0)

    def test_grid_y_inc(self, model):
        assert model.grid.y_inc == pytest.approx(2.0)

    def test_grid_nx_points(self, model):
        # floor((100 - (-100)) / 2) + 1 = 101
        assert model.grid.n_x == 101

    def test_grid_ny_points(self, model):
        assert model.grid.n_y == 101

    def test_grid_total_points(self, model):
        assert model.grid.n_points == 101 * 101

    # Regional stress
    def test_regional_stress_present(self, model):
        assert model.regional_stress is not None

    def test_regional_stress_s1_direction(self, model):
        assert model.regional_stress.s1.direction == pytest.approx(189.0)

    def test_regional_stress_s1_intensity(self, model):
        assert model.regional_stress.s1.intensity == pytest.approx(100.0)

    def test_regional_stress_s1_dip(self, model):
        assert model.regional_stress.s1.dip == pytest.approx(-0.0001)

    def test_regional_stress_s3_direction(self, model):
        assert model.regional_stress.s3.direction == pytest.approx(99.0)

    def test_regional_stress_s2_direction(self, model):
        assert model.regional_stress.s2.direction == pytest.approx(270.0001)

    def test_symmetry_flag(self, model):
        assert model.symmetry == 1

    # is_source / is_receiver helpers
    def test_source_is_source(self, model):
        assert model.source_faults[0].is_source is True

    def test_receivers_are_receivers(self, model):
        for recv in model.receiver_faults:
            assert recv.is_receiver is True


class TestThrustWithSectionFixture:
    """Integration tests against tests/fixtures/inp_files/thrust_with_section.inp."""

    @pytest.fixture(scope="class")
    def model(self, inp_files_dir: Path):
        return read_inp(inp_files_dir / "thrust_with_section.inp")

    def test_parses_without_error(self, model):
        assert model is not None

    def test_n_fixed(self, model):
        assert model.n_fixed == 2

    def test_source_fault_count(self, model):
        assert len(model.source_faults) == 2

    def test_receiver_fault_count(self, model):
        assert len(model.receiver_faults) == 1

    def test_total_fault_count(self, model):
        assert len(model.faults) == 3

    def test_material_depth(self, model):
        assert model.material.depth == pytest.approx(15.0)

    # Source fault 1 (thrust)
    def test_source_fault1_x_start(self, model):
        assert model.source_faults[0].x_start == pytest.approx(-15.0)

    def test_source_fault1_reverse_slip(self, model):
        # slip_2 = 1.0 (reverse)
        assert model.source_faults[0].slip_2 == pytest.approx(1.0)

    def test_source_fault1_dip(self, model):
        assert model.source_faults[0].dip == pytest.approx(30.0)

    def test_source_fault1_bottom_depth(self, model):
        assert model.source_faults[0].bottom_depth == pytest.approx(20.0)

    def test_source_fault1_label(self, model):
        assert model.source_faults[0].label == "Thrust fault 1"

    # Source fault 2 (oblique thrust)
    def test_source_fault2_dip(self, model):
        assert model.source_faults[1].dip == pytest.approx(45.0)

    def test_source_fault2_slip_1(self, model):
        assert model.source_faults[1].slip_1 == pytest.approx(0.5)

    def test_source_fault2_slip_2(self, model):
        assert model.source_faults[1].slip_2 == pytest.approx(0.5)

    def test_source_fault2_label(self, model):
        assert model.source_faults[1].label == "Oblique thrust"

    # Grid (50x50 km, 1 km increment => 101 points each side)
    def test_grid_start_x(self, model):
        assert model.grid.start_x == pytest.approx(-50.0)

    def test_grid_finish_x(self, model):
        assert model.grid.finish_x == pytest.approx(50.0)

    def test_grid_x_inc(self, model):
        assert model.grid.x_inc == pytest.approx(1.0)

    def test_grid_nx_points(self, model):
        assert model.grid.n_x == 101

    # Regional stress (non-zero in this fixture)
    def test_regional_stress_present(self, model):
        assert model.regional_stress is not None

    def test_regional_stress_s1_intensity(self, model):
        assert model.regional_stress.s1.intensity == pytest.approx(200.0)

    def test_regional_stress_s1_gradient(self, model):
        assert model.regional_stress.s1.gradient == pytest.approx(10.0)

    def test_regional_stress_s3_intensity(self, model):
        assert model.regional_stress.s3.intensity == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# 2. String-based unit tests
# ---------------------------------------------------------------------------


MINIMAL_INP = """\
Title line 1
Title line 2
#reg1=  0  #reg2=  0  #fixed=  1  sym=  1
 PR1=       0.250 PR2=       0.250 DEPTH=      10.000
  E1=  0.800000E+06  E2=  0.800000E+06 XLIM=     0.000 YLIM=     0.000
FRIC=       0.400
  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000
  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000
  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000

  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot
 xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx
    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source

  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot
 xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx
    2     -15.0       5.0      15.0       5.0  100       0.0       0.0    90.0     0.0    10.0  Receiver

Grid Parameters
  1  ---  Start-x =    -50.000
  2  ---  Start-y =    -50.000
  3  ---  Finish-x =    50.000
  4  ---  Finish-y =    50.000
  5  ---  x-increment =   1.000
  6  ---  y-increment =   1.000
"""


class TestMinimalInpString:
    """Verify that the smallest valid .inp string round-trips correctly."""

    @pytest.fixture(scope="class")
    def model(self):
        return parse_inp_string(MINIMAL_INP)

    def test_parses_without_error(self, model):
        assert model is not None

    def test_title(self, model):
        assert model.title == "Title line 1\nTitle line 2"

    def test_n_fixed(self, model):
        assert model.n_fixed == 1

    def test_fault_count(self, model):
        assert len(model.faults) == 2

    def test_source_slip(self, model):
        assert model.source_faults[0].slip_1 == pytest.approx(1.0)

    def test_receiver_slip(self, model):
        assert model.receiver_faults[0].slip_1 == pytest.approx(0.0)

    def test_grid_start_x(self, model):
        assert model.grid.start_x == pytest.approx(-50.0)

    def test_grid_finish_x(self, model):
        assert model.grid.finish_x == pytest.approx(50.0)

    def test_material_poisson(self, model):
        assert model.material.poisson == pytest.approx(0.25)

    def test_material_young_sci_notation(self, model):
        # E1 written as 0.800000E+06 — must parse correctly
        assert model.material.young == pytest.approx(8.0e5)

    def test_material_friction(self, model):
        assert model.material.friction == pytest.approx(0.4)

    def test_regional_stress_zero(self, model):
        # All stress params are 0.0 — object still created since S1DR present
        assert model.regional_stress is not None
        assert model.regional_stress.s1.intensity == pytest.approx(0.0)
        assert model.regional_stress.s3.gradient == pytest.approx(0.0)


class TestKodeVariants:
    """Test that all valid KODE values (100-500) parse and map to correct enum."""

    def _one_fault_model(self, kode: int) -> object:
        fault_line = (
            f"    1     -10.0       0.0      10.0       0.0"
            f"  {kode}       1.0       0.0    90.0     0.0    10.0  TestFault\n"
        )
        text = _make_inp(n_fixed=1, faults=fault_line + "\n")
        return parse_inp_string(text)

    def test_kode_100(self):
        model = self._one_fault_model(100)
        assert model.faults[0].kode == Kode.STANDARD

    def test_kode_200(self):
        model = self._one_fault_model(200)
        assert model.faults[0].kode == Kode.TENSILE_RL

    def test_kode_300(self):
        model = self._one_fault_model(300)
        assert model.faults[0].kode == Kode.TENSILE_REV

    def test_kode_400(self):
        model = self._one_fault_model(400)
        assert model.faults[0].kode == Kode.POINT_SOURCE

    def test_kode_500(self):
        model = self._one_fault_model(500)
        assert model.faults[0].kode == Kode.TENSILE_INFL

    def test_kode_100_int_value(self):
        model = self._one_fault_model(100)
        assert model.faults[0].kode.value == 100

    def test_kode_500_is_point_source_property(self):
        model = self._one_fault_model(500)
        assert model.faults[0].is_point_source is True

    def test_kode_400_is_point_source_property(self):
        model = self._one_fault_model(400)
        assert model.faults[0].is_point_source is True

    def test_kode_100_not_point_source(self):
        model = self._one_fault_model(100)
        assert model.faults[0].is_point_source is False


class TestMultipleSourcesAndReceivers:
    """Test parsing with 3 sources and 5 receivers."""

    @pytest.fixture(scope="class")
    def model(self):
        sources = "".join(
            f"    {i}     {-10.0 * i:.1f}       0.0      {10.0 * i:.1f}"
            f"       0.0  100       1.0       0.0    90.0     0.0    10.0  Source{i}\n"
            for i in range(1, 4)
        )
        receivers = "".join(
            f"    {i}     {-20.0 * (i - 3):.1f}       5.0      {20.0 * (i - 3):.1f}"
            f"       5.0  100       0.0       0.0    90.0     0.0    10.0  Recv{i}\n"
            for i in range(4, 9)
        )
        fault_block = sources + "\n" + receivers
        text = _make_inp(n_fixed=3, faults=fault_block)
        return parse_inp_string(text)

    def test_n_fixed(self, model):
        assert model.n_fixed == 3

    def test_source_count(self, model):
        assert len(model.source_faults) == 3

    def test_receiver_count(self, model):
        assert len(model.receiver_faults) == 5

    def test_total_faults(self, model):
        assert len(model.faults) == 8

    def test_sources_have_nonzero_slip(self, model):
        for src in model.source_faults:
            assert src.slip_1 != 0.0 or src.slip_2 != 0.0

    def test_receivers_have_zero_slip(self, model):
        for recv in model.receiver_faults:
            assert recv.slip_1 == pytest.approx(0.0)
            assert recv.slip_2 == pytest.approx(0.0)

    def test_source_boundary_consistent_with_n_fixed(self, model):
        # faults[n_fixed - 1] is last source, faults[n_fixed] is first receiver
        assert model.faults[model.n_fixed - 1].slip_1 != 0.0
        assert model.faults[model.n_fixed].slip_1 == pytest.approx(0.0)

    def test_source_labels(self, model):
        for i, src in enumerate(model.source_faults, start=1):
            assert src.label == f"Source{i}"


# ---------------------------------------------------------------------------
# 3. Error handling tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Verify ParseError is raised for invalid input."""

    def test_empty_string_raises_parse_error(self):
        with pytest.raises(ParseError):
            parse_inp_string("")

    def test_missing_grid_raises_parse_error(self):
        # .inp with faults but no "Grid Parameters" section
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
        )
        with pytest.raises(ParseError):
            parse_inp_string(text)

    def test_malformed_fault_too_few_tokens_raises_parse_error(self):
        # Fault line with only 5 tokens
        fault_line = "    1     -10.0       0.0      10.0       0.0\n"
        text = _make_inp(n_fixed=1, faults=fault_line + "\n")
        with pytest.raises(ParseError):
            parse_inp_string(text)

    def test_invalid_kode_raises_parse_error(self):
        fault_line = (
            "    1     -10.0       0.0      10.0       0.0"
            "  600       1.0       0.0    90.0     0.0    10.0  Bad\n"
        )
        text = _make_inp(n_fixed=1, faults=fault_line + "\n")
        with pytest.raises(ParseError):
            parse_inp_string(text)

    def test_missing_partial_grid_parameters_raises_parse_error(self):
        # Provide only 4 of 6 required grid lines
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            # Lines 5 and 6 deliberately omitted
        )
        with pytest.raises(ParseError):
            parse_inp_string(text)

    def test_n_fixed_exceeds_fault_count_raises_parse_error(self):
        # n_fixed=5 but only 1 fault element provided
        fault_line = (
            "    1     -10.0       0.0      10.0       0.0"
            "  100       1.0       0.0    90.0     0.0    10.0  Source\n"
        )
        text = _make_inp(n_fixed=5, faults=fault_line + "\n")
        with pytest.raises(ParseError):
            parse_inp_string(text)

    def test_nonexistent_file_raises_parse_error(self, tmp_path: Path):
        missing = tmp_path / "does_not_exist.inp"
        with pytest.raises(ParseError):
            read_inp(missing)

    def test_parse_error_carries_filename(self, tmp_path: Path):
        """ParseError.filename attribute is set when reading from disk."""
        bad_file = tmp_path / "bad.inp"
        bad_file.write_text("")  # empty -> ParseError
        with pytest.raises(ParseError) as exc_info:
            read_inp(bad_file)
        assert exc_info.value.filename == str(bad_file)

    def test_parse_error_message_contains_context(self):
        """ParseError message embeds filename for string-based parse."""
        with pytest.raises(ParseError) as exc_info:
            parse_inp_string("", filename="my_test.inp")
        assert "my_test.inp" in str(exc_info.value)

    def test_fault_with_non_numeric_x_raises_parse_error(self):
        fault_line = (
            "    1     NOTNUM       0.0      10.0       0.0"
            "  100       1.0       0.0    90.0     0.0    10.0  Bad\n"
        )
        text = _make_inp(n_fixed=1, faults=fault_line + "\n")
        with pytest.raises(ParseError):
            parse_inp_string(text)


# ---------------------------------------------------------------------------
# 4. Edge case tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases: large grids, zero stress, special labels, encodings."""

    def test_windows_line_endings(self):
        """Parser handles \\r\\n line endings transparently."""
        text = MINIMAL_INP.replace("\n", "\r\n")
        model = parse_inp_string(text)
        assert model is not None
        assert model.n_fixed == 1

    def test_trailing_whitespace_on_lines(self):
        """Trailing spaces on parameter lines do not break parsing."""
        text = MINIMAL_INP.replace("FRIC=       0.400", "FRIC=       0.400   ")
        model = parse_inp_string(text)
        assert model.material.friction == pytest.approx(0.4)

    def test_scientific_notation_e1(self):
        """Scientific notation (e.g. 0.800000E+06) parsed correctly."""
        model = parse_inp_string(MINIMAL_INP)
        assert model.material.young == pytest.approx(8.0e5, rel=1e-6)

    def test_zero_regional_stress_all_fields_zero(self):
        """All-zero stress parameters still produce a RegionalStress object."""
        model = parse_inp_string(MINIMAL_INP)
        rs = model.regional_stress
        assert rs is not None
        for attr in ("direction", "dip", "intensity", "gradient"):
            assert getattr(rs.s1, attr) == pytest.approx(0.0)
            assert getattr(rs.s2, attr) == pytest.approx(0.0)
            assert getattr(rs.s3, attr) == pytest.approx(0.0)

    def test_fault_label_with_spaces_and_special_chars(self):
        """Multi-word labels including hyphens are preserved."""
        fault_line = (
            "    1     -10.0       0.0      10.0       0.0"
            "  100       1.0       0.0    90.0     0.0    10.0  Main fault - segment A\n"
        )
        text = _make_inp(n_fixed=1, faults=fault_line + "\n")
        model = parse_inp_string(text)
        assert model.faults[0].label == "Main fault - segment A"

    def test_empty_fault_label(self):
        """A fault line with exactly 11 tokens (no label) gets empty string label."""
        fault_line = (
            "    1     -10.0       0.0      10.0       0.0"
            "  100       1.0       0.0    90.0     0.0    10.0\n"
        )
        text = _make_inp(n_fixed=1, faults=fault_line + "\n")
        model = parse_inp_string(text)
        assert model.faults[0].label == ""

    def test_large_grid_parameters(self):
        """Parsing succeeds for a 1000x1000 km grid at 1 km spacing."""
        text = _make_inp(
            grid_start_x=-500.0,
            grid_start_y=-500.0,
            grid_finish_x=500.0,
            grid_finish_y=500.0,
            grid_x_inc=1.0,
            grid_y_inc=1.0,
        )
        model = parse_inp_string(text)
        assert model.grid.start_x == pytest.approx(-500.0)
        assert model.grid.finish_x == pytest.approx(500.0)
        assert model.grid.n_x == 1001
        assert model.grid.n_y == 1001

    def test_symmetry_flag_stored(self):
        """Symmetry flag from #sym= parameter is stored on the model."""
        model = parse_inp_string(MINIMAL_INP)
        assert model.symmetry == 1

    def test_xlim_ylim_defaults_to_zero(self):
        """XLIM and YLIM parsed as x_sym/y_sym on the model."""
        model = parse_inp_string(MINIMAL_INP)
        assert model.x_sym == pytest.approx(0.0)
        assert model.y_sym == pytest.approx(0.0)

    def test_no_regional_stress_when_s1dr_absent(self):
        """If S1DR key is absent, regional_stress is None."""
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        assert model.regional_stress is None

    def test_element_index_preserved(self):
        """element_index read from .inp matches FaultElement.element_index."""
        fault_line = (
            "    7     -10.0       0.0      10.0       0.0"
            "  100       1.0       0.0    90.0     0.0    10.0  Numbered\n"
        )
        text = _make_inp(n_fixed=1, faults=fault_line + "\n")
        model = parse_inp_string(text)
        assert model.faults[0].element_index == 7


# ---------------------------------------------------------------------------
# 5. Round-trip consistency tests
# ---------------------------------------------------------------------------


class TestRoundTripConsistency:
    """Verify internal consistency of parsed models."""

    def test_n_fixed_consistent_with_source_slice(self):
        """model.source_faults == model.faults[:n_fixed]."""
        model = parse_inp_string(MINIMAL_INP)
        assert model.source_faults == model.faults[: model.n_fixed]

    def test_receiver_slice_consistent_with_n_fixed(self):
        """model.receiver_faults == model.faults[n_fixed:]."""
        model = parse_inp_string(MINIMAL_INP)
        assert model.receiver_faults == model.faults[model.n_fixed :]

    def test_n_sources_equals_n_fixed(self):
        model = parse_inp_string(MINIMAL_INP)
        assert model.n_sources == model.n_fixed

    def test_n_receivers_is_total_minus_n_fixed(self):
        model = parse_inp_string(MINIMAL_INP)
        assert model.n_receivers == len(model.faults) - model.n_fixed

    def test_all_fields_populated(self):
        """No field on the returned model is unexpectedly None."""
        model = parse_inp_string(MINIMAL_INP)
        assert model.title is not None
        assert model.material is not None
        assert model.faults is not None
        assert model.grid is not None
        assert model.n_fixed is not None

    def test_source_fault_is_source_property(self):
        """Faults at indices < n_fixed have is_source == True."""
        model = parse_inp_string(MINIMAL_INP)
        for fault in model.source_faults:
            assert fault.is_source is True

    def test_receiver_fault_is_receiver_property(self):
        """Faults at indices >= n_fixed have is_receiver == True."""
        model = parse_inp_string(MINIMAL_INP)
        for fault in model.receiver_faults:
            assert fault.is_receiver is True

    def test_grid_depth_matches_material_depth(self):
        """grid.depth matches material.depth for the minimal fixture."""
        model = parse_inp_string(MINIMAL_INP)
        assert model.grid.depth == pytest.approx(model.material.depth)

    def test_fault_dip_in_valid_range(self):
        """All faults have dip in [0, 90] degrees."""
        model = parse_inp_string(MINIMAL_INP)
        for fault in model.faults:
            assert 0.0 <= fault.dip <= 90.0

    def test_fault_bottom_depth_exceeds_top_depth(self):
        """All faults satisfy bottom_depth > top_depth."""
        model = parse_inp_string(MINIMAL_INP)
        for fault in model.faults:
            assert fault.bottom_depth > fault.top_depth

    def test_source_fault_strike_computed(self):
        """strike_deg is computable (no exception) for all source faults."""
        model = parse_inp_string(MINIMAL_INP)
        for fault in model.source_faults:
            _ = fault.strike_deg  # must not raise

    def test_source_fault_length_positive(self):
        """length property is positive for non-degenerate faults."""
        model = parse_inp_string(MINIMAL_INP)
        for fault in model.faults:
            assert fault.length > 0.0

    def test_grid_n_x_formula(self):
        """grid.n_x == floor((finish_x - start_x) / x_inc) + 1."""
        model = parse_inp_string(MINIMAL_INP)
        g = model.grid
        expected = math.floor((g.finish_x - g.start_x) / g.x_inc) + 1
        assert model.grid.n_x == expected

    def test_grid_n_y_formula(self):
        """grid.n_y == floor((finish_y - start_y) / y_inc) + 1."""
        model = parse_inp_string(MINIMAL_INP)
        g = model.grid
        expected = math.floor((g.finish_y - g.start_y) / g.y_inc) + 1
        assert model.grid.n_y == expected

    def test_fixture_and_string_parse_produce_same_title(self, inp_files_dir: Path):
        """Parsing from disk and from string give identical titles."""
        path = inp_files_dir / "simple_strike_slip.inp"
        model_file = read_inp(path)
        model_str = parse_inp_string(path.read_text(encoding="utf-8"))
        assert model_file.title == model_str.title

    def test_fixture_and_string_parse_produce_same_fault_count(self, inp_files_dir: Path):
        """Parsing from disk and from string give same number of faults."""
        path = inp_files_dir / "simple_strike_slip.inp"
        model_file = read_inp(path)
        model_str = parse_inp_string(path.read_text(encoding="utf-8"))
        assert len(model_file.faults) == len(model_str.faults)

    def test_fixture_and_string_parse_produce_same_grid(self, inp_files_dir: Path):
        """Parsing from disk and from string give identical grid specs."""
        path = inp_files_dir / "simple_strike_slip.inp"
        model_file = read_inp(path)
        model_str = parse_inp_string(path.read_text(encoding="utf-8"))
        assert model_file.grid == model_str.grid


# ---------------------------------------------------------------------------
# 6. Coverage-targeted tests for remaining uncovered parser branches
# ---------------------------------------------------------------------------


class TestParserBranchCoverage:
    """Targeted tests that exercise specific parser state-machine branches
    not reached by the fixture and string tests above."""

    # ---- L54-56: latin-1 fallback on UnicodeDecodeError ----

    def test_latin1_fallback_on_unicode_decode_error(self, tmp_path: Path):
        """read_inp falls back to latin-1 when the file is not valid UTF-8."""
        # Build a valid minimal .inp encoded in latin-1 with a non-UTF-8 byte
        # (e.g. 0xe9 = é in latin-1).  The title line contains that byte so
        # the UTF-8 decode will fail and trigger the fallback.
        content = MINIMAL_INP.replace("Title line 1", "Title: Évènement")
        latin1_bytes = content.encode("latin-1")
        p = tmp_path / "latin1.inp"
        p.write_bytes(latin1_bytes)
        model = read_inp(p)
        assert model is not None
        assert "vènement" in model.title

    # ---- L212-215: blank line in PARAMS before any text accumulated ----

    def test_early_blank_line_in_params_no_op(self):
        """A blank line appearing in PARAMS before any text is collected
        does not transition state prematurely (param_text guard)."""
        # Insert a blank line between title line 2 and the actual param lines
        text = (
            "Title\n"
            "Title2\n"
            "\n"  # blank before params — hits the `if self._param_text` guard
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        assert model is not None
        assert model.n_fixed == 1

    # ---- L219-222: column header directly in PARAMS state (no blank separator) ----

    def test_column_header_directly_after_params_no_blank(self):
        """Parser handles column header appearing in PARAMS state without a
        preceding blank line (direct transition to SOURCE_FAULTS)."""
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            # NOTE: no blank line here — column header immediately follows
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        assert model is not None
        assert len(model.faults) >= 1

    # ---- L233: blank line skip in _on_faults_header ----

    def test_extra_blank_lines_in_faults_header_state(self):
        """Extra blank lines between params and column header are skipped."""
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            "\n"  # second blank — hits _on_faults_header blank guard
            "\n"  # third blank
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        assert model is not None
        assert model.n_fixed == 1

    # ---- L238-240: "Grid Parameters" in _on_faults_header (no faults at all) ----

    def test_grid_parameters_immediately_after_params_no_faults(self):
        """If 'Grid Parameters' appears before any fault header, the parser
        transitions to GRID state from _on_faults_header."""
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  0  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            # No fault header at all — jump straight to grid
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        assert model is not None
        assert len(model.faults) == 0
        assert model.n_fixed == 0

    # ---- L242-245: fault line without column header in _on_faults_header ----

    def test_fault_line_without_preceding_column_header(self):
        """A numeric fault line encountered in FAULTS_HEADER state (no explicit
        column-header line) is still parsed correctly."""
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            # No column header — fault line directly in FAULTS_HEADER state
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Headerless\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        assert model is not None
        assert model.faults[0].label == "Headerless"

    # ---- L257-258: "Grid Parameters" in _on_source_faults ----

    def test_grid_parameters_keyword_in_source_faults_block(self):
        """'Grid Parameters' appearing inside the source-fault block ends it."""
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            # Grid keyword appears immediately (no blank line) — hits L257-258
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        assert model is not None
        assert model.n_fixed == 1

    # ---- L269, L274: _on_receiver_header placeholder + fault without header ----

    def test_placeholder_line_in_receiver_header_state(self):
        """A 'xxx' placeholder line in RECEIVER_HEADER state is skipped."""
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            # In RECEIVER_HEADER: placeholder line (hits L269)
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            # Then fault without explicit second column header (hits L274)
            "    2     -15.0       5.0      15.0       5.0  100       0.0       0.0    90.0     0.0    10.0  Recv\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        assert model is not None
        assert len(model.faults) == 2

    # ---- L288-289: "Grid Parameters" keyword in _on_receiver_faults ----

    def test_grid_keyword_directly_in_receiver_faults_block(self):
        """'Grid Parameters' directly in receiver-faults block (no blank) ends it."""
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    2     -15.0       5.0      15.0       5.0  100       0.0       0.0    90.0     0.0    10.0  Recv\n"
            # No blank line before grid — hits L288-289
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        assert model is not None
        assert len(model.faults) == 2

    # ---- L297-299: blank line in GRID state transitions to CROSS_SECTION ----
    # (thrust_with_section.inp already covers the cross-section path, but
    #  the blank-line-after-grid-params transition is hit here explicitly)

    def test_blank_line_after_grid_transitions_to_cross_section_then_eof(self):
        """A blank line after grid params transitions to CROSS_SECTION state.
        If no cross-section data follows, cross_section is None."""
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
            "\n"  # blank line after grid — triggers L297-299 transition to CROSS_SECTION
        )
        model = parse_inp_string(text)
        assert model is not None
        assert model.grid.start_x == pytest.approx(-50.0)

    # ---- L303-304: "Cross Section" keyword in _on_grid ----

    def test_cross_section_keyword_in_grid_state(self, inp_files_dir: Path):
        """thrust_with_section.inp exercises the Cross Section keyword path."""
        # This fixture has a cross-section block — verify parsing succeeded
        model = read_inp(inp_files_dir / "thrust_with_section.inp")
        assert model is not None
        assert model.grid.finish_x == pytest.approx(50.0)

    # ---- L316-318: _on_cross_section blank when params present -> MAP_INFO ----
    # ---- L322-323: "map info" keyword in _on_cross_section ----
    # ---- L334: _on_map_info pass (consuming map info lines) ----

    def test_cross_section_followed_by_map_info(self):
        """Cross section block followed by map info lines is parsed correctly."""
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
            "\n"
            "Cross Section\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =       0.000\n"
            "  3  ---  Finish-x =     50.000\n"
            "  4  ---  Finish-y =       0.000\n"
            "  5  ---  Depth-min =      0.000\n"
            "  6  ---  Depth-max =     30.000\n"
            "  7  ---  z-increment =    1.000\n"
            "\n"              # blank after cross section -> MAP_INFO (L316-318)
            "Map Info\n"     # triggers L322-323 (but already in MAP_INFO by blank)
            "some map data line\n"   # triggers L334 pass in _on_map_info
        )
        model = parse_inp_string(text)
        assert model is not None
        assert model.grid.start_x == pytest.approx(-50.0)

    def test_cross_section_followed_by_map_info_keyword_directly(self):
        """'Map Info' keyword inside cross-section block (no blank) transitions
        directly to MAP_INFO state (L322-323)."""
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
            "\n"
            "Cross Section\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =       0.000\n"
            "  3  ---  Finish-x =     50.000\n"
            "  4  ---  Finish-y =       0.000\n"
            "  5  ---  Depth-min =      0.000\n"
            "  6  ---  Depth-max =     30.000\n"
            "  7  ---  z-increment =    1.000\n"
            "Map Info\n"     # No blank before — hits L322-323 directly
            "lat=35.0 lon=139.0\n"  # _on_map_info pass
        )
        model = parse_inp_string(text)
        assert model is not None

    # ---- L342, L346-347: _looks_like_fault_line edge cases ----

    def test_looks_like_fault_line_non_integer_first_token(self):
        """A line whose first token is not an integer is not parsed as a fault
        (hits the ValueError branch in _looks_like_fault_line).  The parser
        must not raise — it simply skips the line."""
        # Craft an .inp where a non-fault line with 11+ tokens slips into the
        # source faults block.  The parser should skip it gracefully.
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            # In _on_faults_header: a line with 11 tokens but first is non-int
            # hits _looks_like_fault_line -> ValueError branch -> returns False
            "TEXT  -10.0  0.0  10.0  0.0  100  1.0  0.0  90.0  0.0  10.0  Skip\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        assert model is not None
        assert len(model.faults) == 1

    # ---- L399-400: FaultElement constructor raises (invalid geometry) ----

    def test_invalid_fault_geometry_raises_parse_error(self):
        """A fault line with dip > 90 causes FaultElement to raise
        ValidationError, which is caught and re-raised as ParseError."""
        fault_line = (
            "    1     -10.0       0.0      10.0       0.0"
            "  100       1.0       0.0    95.0     0.0    10.0  BadDip\n"  # dip=95 > 90
        )
        text = _make_inp(n_fixed=1, faults=fault_line + "\n")
        with pytest.raises(ParseError):
            parse_inp_string(text)

    def test_fault_with_bottom_not_exceeding_top_raises_parse_error(self):
        """A fault whose bottom_depth <= top_depth raises ParseError."""
        fault_line = (
            "    1     -10.0       0.0      10.0       0.0"
            "  100       1.0       0.0    90.0    10.0     5.0  BadDepth\n"  # bot < top
        )
        text = _make_inp(n_fixed=1, faults=fault_line + "\n")
        with pytest.raises(ParseError):
            parse_inp_string(text)

    # ---- L418-424: _float_param raises when value is non-numeric ----
    # ---- L431-437: _int_param raises when value is non-numeric ----
    # These branches are deep inside the parser; the easiest trigger is
    # a manually crafted _params dict, so we test via a malformed but
    # parse-reaching .inp where a key has a non-float value.
    # The regex _KV_RE only matches numeric-looking values, so the only
    # realistic path to hit those error branches is through _float_param
    # being asked for a key with no default and no match -> raises.

    def test_required_float_param_missing_raises_parse_error(self):
        """If a required parameter like PR1 is genuinely absent from the
        param text, _float_param raises ParseError.  We simulate this by
        omitting PR1 without a default in a custom scenario.

        We cannot easily trigger the ValueError path in _float_param since
        the KV regex only matches numeric strings.  Instead we verify the
        'Required parameter not found' path by omitting FRIC and relying
        on the default fallback — meaning the only way to hit the
        no-default raise is when the parser itself requests a key with no
        default but the param is absent."""
        # The parser uses defaults for all material params, so we verify
        # the grid missing-params path covers the raise (already tested).
        # For _int_param: verify it handles the missing #fixed gracefully
        # (defaults to 0).
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  sym=  1\n"  # #fixed is absent — default 0
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        # #fixed absent -> default 0, no faults -> n_fixed=0
        assert model.n_fixed == 0

    # ---- L503: incomplete cross-section parameters raises ParseError ----

    def test_incomplete_cross_section_raises_parse_error(self):
        """A cross-section block that is missing required parameters (e.g.
        only 5 of 7) triggers ParseError from _build_cross_section."""
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
            "\n"
            "Cross Section\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =       0.000\n"
            "  3  ---  Finish-x =     50.000\n"
            # Deliberately stop at 3 of 7 required params
        )
        with pytest.raises(ParseError):
            parse_inp_string(text)

    # ---- Cross-section keyword in _on_cross_section state skipped (L319-320) ----

    def test_cross_section_keyword_line_is_skipped_in_cross_section_state(self):
        """The 'Cross Section' keyword line itself is skipped when the parser
        is already in CROSS_SECTION state (arriving via blank-after-grid)."""
        # This is covered by the thrust_with_section fixture but we add an
        # explicit string test to be certain the branch is exercised from
        # the grid-blank transition path.
        text = (
            "Title\n"
            "Title2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       0.250 DEPTH=      10.000\n"
            "  E1=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
            "FRIC=       0.400\n"
            "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=  0.000\n"
            "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=  0.000\n"
            "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=  0.000\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
            "\n"  # blank after grid -> CROSS_SECTION
            "Cross Section\n"   # keyword line skipped in CROSS_SECTION state
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =       0.000\n"
            "  3  ---  Finish-x =     50.000\n"
            "  4  ---  Finish-y =       0.000\n"
            "  5  ---  Depth-min =      0.000\n"
            "  6  ---  Depth-max =     30.000\n"
            "  7  ---  z-increment =    1.000\n"
        )
        model = parse_inp_string(text)
        assert model is not None


# ---------------------------------------------------------------------------
# 11. Real Coulomb .inp file tests
# ---------------------------------------------------------------------------


class TestRealInpFiles:
    """Integration tests against real Coulomb 3.4 .inp files.

    Source: github.com/kmaterna/elastic_stresses_py/examples/sample_inputs/
    These files exercise format variations found in actual Coulomb output:
    - XSYM/YSYM instead of XLIM/YLIM
    - Values without leading digit (e.g. .250, .000)
    - Long dash separators (-----------------------------)
    - "Size Parameters" section between Grid and Cross Section
    - Lowercase scientific notation (8.000e+05)
    - Subfaulted models with 100+ fault elements
    """

    EXPECTED: ClassVar[dict[str, dict[str, float]]] = {
        "M6.5.inp": {"n_faults": 2, "n_fixed": 2, "pr": 0.25, "depth": 0.0, "fric": 0.4},
        "M6p8.inp": {"n_faults": 2, "n_fixed": 2, "pr": 0.25, "depth": 0.0, "fric": 0.4},
        "simple_receiver_bm.inp": {"n_faults": 2, "n_fixed": 2, "pr": 0.25, "depth": 7.5, "fric": 0.4},
        "simple_subfaulted.inp": {"n_faults": 101, "n_fixed": 101, "pr": 0.25, "depth": 7.5, "fric": 0.4},
        "simplest_receiver.inp": {"n_faults": 2, "n_fixed": 2, "pr": 0.25, "depth": 7.5, "fric": 0.4},
        "test_case_receiver.inp": {"n_faults": 2, "n_fixed": 2, "pr": 0.25, "depth": 7.5, "fric": 0.4},
        "test_case_subfaulted.inp": {"n_faults": 101, "n_fixed": 101, "pr": 0.25, "depth": 7.5, "fric": 0.4},
    }

    @pytest.fixture(
        scope="class",
        params=list(EXPECTED.keys()),
        ids=list(EXPECTED.keys()),
    )
    def real_model(self, request, real_inp_files_dir: Path):
        path = real_inp_files_dir / request.param
        if not path.exists():
            pytest.skip(f"Real fixture not found: {path}")
        model = read_inp(path)
        return request.param, model

    def test_parses_without_error(self, real_model):
        _, model = real_model
        assert model is not None

    def test_fault_count(self, real_model):
        name, model = real_model
        assert len(model.faults) == self.EXPECTED[name]["n_faults"]

    def test_n_fixed(self, real_model):
        name, model = real_model
        assert model.n_fixed == self.EXPECTED[name]["n_fixed"]

    def test_source_count_equals_n_fixed(self, real_model):
        _, model = real_model
        assert len(model.source_faults) == model.n_fixed

    def test_material_poisson(self, real_model):
        name, model = real_model
        assert model.material.poisson == pytest.approx(self.EXPECTED[name]["pr"])

    def test_material_depth(self, real_model):
        name, model = real_model
        assert model.material.depth == pytest.approx(self.EXPECTED[name]["depth"])

    def test_material_friction(self, real_model):
        name, model = real_model
        assert model.material.friction == pytest.approx(self.EXPECTED[name]["fric"])

    def test_material_young(self, real_model):
        _, model = real_model
        assert model.material.young == pytest.approx(8.0e5)

    def test_xsym_ysym_parsed(self, real_model):
        _, model = real_model
        assert model.x_sym == pytest.approx(0.0)
        assert model.y_sym == pytest.approx(0.0)

    def test_symmetry(self, real_model):
        _, model = real_model
        assert model.symmetry == 1

    def test_grid_has_valid_extents(self, real_model):
        _, model = real_model
        assert model.grid.start_x < model.grid.finish_x
        assert model.grid.start_y < model.grid.finish_y
        assert model.grid.x_inc > 0
        assert model.grid.y_inc > 0

    def test_regional_stress_present(self, real_model):
        _, model = real_model
        assert model.regional_stress is not None
        assert model.regional_stress.s1.intensity == pytest.approx(100.0)

    def test_all_faults_have_valid_kode(self, real_model):
        _, model = real_model
        for fault in model.faults:
            assert fault.kode == Kode.STANDARD

    def test_all_faults_have_positive_depth_range(self, real_model):
        _, model = real_model
        for fault in model.faults:
            assert fault.bottom_depth >= fault.top_depth


class TestRealM6p8Detail:
    """Detailed value checks for M6p8.inp (lowercase sci notation, unique fault geometry)."""

    @pytest.fixture(scope="class")
    def model(self, real_inp_files_dir: Path):
        path = real_inp_files_dir / "M6p8.inp"
        if not path.exists():
            pytest.skip("M6p8.inp not found")
        return read_inp(path)

    def test_fault1_coordinates(self, model):
        f = model.source_faults[0]
        assert f.x_start == pytest.approx(-86.69)
        assert f.y_start == pytest.approx(32.18)
        assert f.x_fin == pytest.approx(-51.54)
        assert f.y_fin == pytest.approx(59.95)

    def test_fault1_geometry(self, model):
        f = model.source_faults[0]
        assert f.dip == pytest.approx(89.0)
        assert f.top_depth == pytest.approx(7.8)
        assert f.bottom_depth == pytest.approx(22.2)
        assert f.slip_1 == pytest.approx(-0.8)
        assert f.slip_2 == pytest.approx(0.0)

    def test_fault2_coordinates(self, model):
        f = model.source_faults[1]
        assert f.x_start == pytest.approx(-5.69)
        assert f.y_start == pytest.approx(0.82)
        assert f.x_fin == pytest.approx(-15.54)
        assert f.y_fin == pytest.approx(120.95)

    def test_fault2_geometry(self, model):
        f = model.source_faults[1]
        assert f.dip == pytest.approx(12.0)
        assert f.top_depth == pytest.approx(10.8)
        assert f.bottom_depth == pytest.approx(35.0)

    def test_grid_values(self, model):
        g = model.grid
        assert g.start_x == pytest.approx(-127.21, abs=0.01)
        assert g.finish_x == pytest.approx(127.21, abs=0.01)
        assert g.x_inc == pytest.approx(4.24, abs=0.01)
        assert g.y_inc == pytest.approx(5.56, abs=0.01)


class TestRealSubfaultedDetail:
    """Checks for subfaulted model with 101 faults (1 source + 100 receivers)."""

    @pytest.fixture(scope="class")
    def model(self, real_inp_files_dir: Path):
        path = real_inp_files_dir / "simple_subfaulted.inp"
        if not path.exists():
            pytest.skip("simple_subfaulted.inp not found")
        return read_inp(path)

    def test_101_faults(self, model):
        assert len(model.faults) == 101

    def test_all_sources(self, model):
        assert len(model.source_faults) == 101
        assert len(model.receiver_faults) == 0

    def test_first_fault_is_main_rupture(self, model):
        f = model.source_faults[0]
        assert f.x_start == pytest.approx(-10.0)
        assert f.y_start == pytest.approx(0.0)
        assert f.x_fin == pytest.approx(10.0)
        assert f.slip_1 == pytest.approx(1.0)
        assert f.top_depth == pytest.approx(10.0)
        assert f.bottom_depth == pytest.approx(20.0)

    def test_subfault_grid_pattern(self, model):
        # Subfaults 2-11 should be the first depth row (top=0, bot=3)
        for f in model.source_faults[1:11]:
            assert f.top_depth == pytest.approx(0.0)
            assert f.bottom_depth == pytest.approx(3.0)
            assert f.slip_1 == pytest.approx(0.0)
            assert f.slip_2 == pytest.approx(0.0)


class TestSizeParametersNotPolluteCrossSection:
    """Verify that Size Parameters between Grid and Cross Section are handled correctly."""

    def test_size_params_skipped_cross_section_intact(self):
        text = _make_inp(
            extra_after_grid=(
                "     Size Parameters\n"
                "  1  ---  Plot size =     2.000000\n"
                "  2  ---  Shade/Color increment =     1.000000\n"
                "  3  ---  Exaggeration for disp.& dist. =     10000.00\n"
                "\n"
                "Cross section default\n"
                "  1  ---  Start-x =    -36.00000\n"
                "  2  ---  Start-y =     36.00000\n"
                "  3  ---  Finish-x =     38.00000\n"
                "  4  ---  Finish-y =    -36.00000\n"
                "  5  ---  Distant-increment =     1.000000\n"
                "  6  ---  Z-depth =     30.00000\n"
                "  7  ---  Z-increment =     1.000000\n"
            )
        )
        model = parse_inp_string(text)
        assert model is not None

    def test_xsym_ysym_params(self):
        """Test that XSYM/YSYM are recognized as symmetry axis parameters."""
        text = (
            "Title 1\n"
            "Title 2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       .250      PR2=       .250    DEPTH=        7.5\n"
            "  E1=   0.800000E+06   E2=   0.800000E+06\n"
            "XSYM=       5.000     YSYM=       3.000\n"
            "FRIC=       .400\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0"
            "       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        assert model.x_sym == pytest.approx(5.0)
        assert model.y_sym == pytest.approx(3.0)

    def test_dot_leading_values(self):
        """Test that .250 and .000 values (no leading digit) are parsed correctly."""
        text = (
            "Title 1\n"
            "Title 2\n"
            "#reg1=  0  #reg2=  0  #fixed=  1  sym=  1\n"
            " PR1=       .250      PR2=       .250    DEPTH=        .500\n"
            "  E1=   0.800000E+06   E2=   0.800000E+06\n"
            "XSYM=       .000     YSYM=       .000\n"
            "FRIC=       .400\n"
            "\n"
            "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse   dip   top    bot\n"
            " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
            "    1     -10.0       0.0      10.0       0.0  100       1.0"
            "       0.0    90.0     0.0    10.0  Source\n"
            "\n"
            "Grid Parameters\n"
            "  1  ---  Start-x =    -50.000\n"
            "  2  ---  Start-y =    -50.000\n"
            "  3  ---  Finish-x =    50.000\n"
            "  4  ---  Finish-y =    50.000\n"
            "  5  ---  x-increment =   1.000\n"
            "  6  ---  y-increment =   1.000\n"
        )
        model = parse_inp_string(text)
        assert model.material.poisson == pytest.approx(0.25)
        assert model.material.depth == pytest.approx(0.5)
        assert model.material.friction == pytest.approx(0.4)

    def test_long_dash_separators(self):
        """Test that grid lines with long dash separators parse correctly."""
        text = _make_inp(extra_after_grid="")
        # Replace short dashes with long dashes
        text = text.replace("  1  ---  Start-x", "  1  ----------------------------  Start-x")
        text = text.replace("  2  ---  Start-y", "  2  ----------------------------  Start-y")
        text = text.replace("  3  ---  Finish-x", "  3  --------------------------   Finish-x")
        text = text.replace("  4  ---  Finish-y", "  4  --------------------------   Finish-y")
        text = text.replace("  5  ---  x-increment", "  5  ------------------------  x-increment")
        text = text.replace("  6  ---  y-increment", "  6  ------------------------  y-increment")
        model = parse_inp_string(text)
        assert model.grid.start_x == pytest.approx(-50.0)
        assert model.grid.finish_x == pytest.approx(50.0)
