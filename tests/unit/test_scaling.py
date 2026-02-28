"""Tests for opencoulomb.core.scaling — earthquake scaling relations."""

from __future__ import annotations

import math

import pytest
from click.testing import CliRunner

from opencoulomb.cli.main import cli
from opencoulomb.core.scaling import (
    FaultType,
    ScalingResult,
    blaser_2010,
    magnitude_to_fault,
    wells_coppersmith_1994,
)
from opencoulomb.types.fault import FaultElement, Kode


# ---------------------------------------------------------------------------
# FaultType enum
# ---------------------------------------------------------------------------


class TestFaultType:
    def test_all_members_accessible(self) -> None:
        assert FaultType.STRIKE_SLIP is not None
        assert FaultType.REVERSE is not None
        assert FaultType.NORMAL is not None
        assert FaultType.ALL is not None

    def test_value_strings(self) -> None:
        assert FaultType.STRIKE_SLIP.value == "strike_slip"
        assert FaultType.REVERSE.value == "reverse"
        assert FaultType.NORMAL.value == "normal"
        assert FaultType.ALL.value == "all"

    def test_lookup_by_value(self) -> None:
        assert FaultType("strike_slip") is FaultType.STRIKE_SLIP
        assert FaultType("reverse") is FaultType.REVERSE
        assert FaultType("normal") is FaultType.NORMAL
        assert FaultType("all") is FaultType.ALL

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            FaultType("thrust")


# ---------------------------------------------------------------------------
# ScalingResult dataclass
# ---------------------------------------------------------------------------


class TestScalingResult:
    def test_frozen(self) -> None:
        r = ScalingResult(
            length_km=40.0,
            width_km=17.0,
            area_km2=680.0,
            displacement_m=1.07,
            magnitude=7.0,
            fault_type=FaultType.ALL,
            relation="wells_coppersmith_1994",
        )
        with pytest.raises(Exception):
            r.length_km = 99.0  # type: ignore[misc]

    def test_fields_accessible(self) -> None:
        r = ScalingResult(
            length_km=10.0,
            width_km=5.0,
            area_km2=50.0,
            displacement_m=0.5,
            magnitude=6.0,
            fault_type=FaultType.REVERSE,
            relation="blaser_2010",
        )
        assert r.length_km == 10.0
        assert r.width_km == 5.0
        assert r.area_km2 == 50.0
        assert r.displacement_m == 0.5
        assert r.magnitude == 6.0
        assert r.fault_type is FaultType.REVERSE
        assert r.relation == "blaser_2010"


# ---------------------------------------------------------------------------
# Wells & Coppersmith (1994)
# ---------------------------------------------------------------------------


class TestWellsCoppersmith1994:
    def test_relation_name(self) -> None:
        r = wells_coppersmith_1994(7.0)
        assert r.relation == "wells_coppersmith_1994"

    def test_magnitude_stored(self) -> None:
        r = wells_coppersmith_1994(6.5)
        assert r.magnitude == 6.5

    def test_default_fault_type_is_all(self) -> None:
        r = wells_coppersmith_1994(7.0)
        assert r.fault_type is FaultType.ALL

    def test_m7_all_length_in_expected_range(self) -> None:
        # WC94 ALL M7: log10(L) = -3.22 + 0.69*7 = 1.61 → L = 40.74 km
        r = wells_coppersmith_1994(7.0, FaultType.ALL)
        assert 35.0 < r.length_km < 50.0

    def test_m7_all_numerical_values(self) -> None:
        r = wells_coppersmith_1994(7.0, FaultType.ALL)
        assert math.isclose(r.length_km, 40.738, rel_tol=1e-3)
        assert math.isclose(r.width_km, 16.982, rel_tol=1e-3)
        assert math.isclose(r.area_km2, 758.578, rel_tol=1e-3)
        assert math.isclose(r.displacement_m, 1.0715, rel_tol=1e-3)

    def test_all_fault_types_produce_positive_values(self) -> None:
        for ft in FaultType:
            r = wells_coppersmith_1994(7.0, ft)
            assert r.length_km > 0.0
            assert r.width_km > 0.0
            assert r.area_km2 > 0.0
            assert r.displacement_m > 0.0

    def test_monotonicity_m5_to_m8_all(self) -> None:
        results = [wells_coppersmith_1994(float(m), FaultType.ALL) for m in [5, 6, 7, 8]]
        for i in range(len(results) - 1):
            assert results[i].length_km < results[i + 1].length_km
            assert results[i].width_km < results[i + 1].width_km
            assert results[i].area_km2 < results[i + 1].area_km2
            assert results[i].displacement_m < results[i + 1].displacement_m

    def test_monotonicity_strike_slip(self) -> None:
        results = [wells_coppersmith_1994(float(m), FaultType.STRIKE_SLIP) for m in [5, 6, 7, 8]]
        for i in range(len(results) - 1):
            assert results[i].length_km < results[i + 1].length_km

    def test_m4_edge_case_small_but_positive(self) -> None:
        r = wells_coppersmith_1994(4.0, FaultType.ALL)
        assert r.length_km > 0.0
        assert r.length_km < 5.0  # should be sub-km to a few km

    def test_m9_edge_case_large(self) -> None:
        r = wells_coppersmith_1994(9.0, FaultType.ALL)
        # Should be well over 1000 km
        assert r.length_km > 500.0

    def test_strike_slip_returns_correct_type(self) -> None:
        r = wells_coppersmith_1994(7.0, FaultType.STRIKE_SLIP)
        assert r.fault_type is FaultType.STRIKE_SLIP
        assert math.isclose(r.length_km, 42.658, rel_tol=1e-3)

    def test_reverse_returns_correct_type(self) -> None:
        r = wells_coppersmith_1994(7.0, FaultType.REVERSE)
        assert r.fault_type is FaultType.REVERSE
        assert math.isclose(r.length_km, 35.481, rel_tol=1e-3)

    def test_normal_returns_correct_type(self) -> None:
        r = wells_coppersmith_1994(7.0, FaultType.NORMAL)
        assert r.fault_type is FaultType.NORMAL
        assert math.isclose(r.length_km, 30.903, rel_tol=1e-3)

    def test_returns_scaling_result_instance(self) -> None:
        r = wells_coppersmith_1994(6.0)
        assert isinstance(r, ScalingResult)


# ---------------------------------------------------------------------------
# Blaser et al. (2010)
# ---------------------------------------------------------------------------


class TestBlaser2010:
    def test_relation_name(self) -> None:
        r = blaser_2010(7.0)
        assert r.relation == "blaser_2010"

    def test_magnitude_stored(self) -> None:
        r = blaser_2010(6.5)
        assert r.magnitude == 6.5

    def test_default_fault_type_is_all(self) -> None:
        r = blaser_2010(7.0)
        assert r.fault_type is FaultType.ALL

    def test_m7_all_length_in_expected_range(self) -> None:
        # B10 ALL M7: log10(L) = -2.69 + 0.64*7 = 1.79 → L = 61.66 km
        r = blaser_2010(7.0, FaultType.ALL)
        assert 50.0 < r.length_km < 80.0

    def test_m7_all_numerical_values(self) -> None:
        r = blaser_2010(7.0, FaultType.ALL)
        assert math.isclose(r.length_km, 61.660, rel_tol=1e-3)
        assert math.isclose(r.width_km, 16.982, rel_tol=1e-3)
        assert math.isclose(r.area_km2, 758.578, rel_tol=1e-3)

    def test_displacement_estimated_from_seismic_moment(self) -> None:
        # D = M0 / (mu * A)  where M0 = 10^(1.5*M + 9.05), mu = 3e10
        r = blaser_2010(7.0, FaultType.ALL)
        m0 = 10.0 ** (1.5 * 7.0 + 9.05)
        mu = 3.0e10
        area_m2 = r.area_km2 * 1.0e6
        expected_disp = m0 / (mu * area_m2)
        assert math.isclose(r.displacement_m, expected_disp, rel_tol=1e-6)

    def test_displacement_positive(self) -> None:
        for ft in FaultType:
            r = blaser_2010(7.0, ft)
            assert r.displacement_m > 0.0

    def test_displacement_increases_with_magnitude(self) -> None:
        r5 = blaser_2010(5.0)
        r7 = blaser_2010(7.0)
        r9 = blaser_2010(9.0)
        assert r5.displacement_m < r7.displacement_m < r9.displacement_m

    def test_all_fault_types_produce_positive_values(self) -> None:
        for ft in FaultType:
            r = blaser_2010(7.0, ft)
            assert r.length_km > 0.0
            assert r.width_km > 0.0
            assert r.area_km2 > 0.0
            assert r.displacement_m > 0.0

    def test_monotonicity_m5_to_m8_all(self) -> None:
        results = [blaser_2010(float(m), FaultType.ALL) for m in [5, 6, 7, 8]]
        for i in range(len(results) - 1):
            assert results[i].length_km < results[i + 1].length_km
            assert results[i].width_km < results[i + 1].width_km
            assert results[i].area_km2 < results[i + 1].area_km2
            assert results[i].displacement_m < results[i + 1].displacement_m

    def test_m4_edge_case_small_but_positive(self) -> None:
        r = blaser_2010(4.0, FaultType.ALL)
        assert r.length_km > 0.0

    def test_m9_edge_case_large(self) -> None:
        r = blaser_2010(9.0, FaultType.ALL)
        assert r.length_km > 500.0

    def test_strike_slip_returns_correct_type(self) -> None:
        r = blaser_2010(7.0, FaultType.STRIKE_SLIP)
        assert r.fault_type is FaultType.STRIKE_SLIP

    def test_all_fault_types_accessible(self) -> None:
        for ft in FaultType:
            r = blaser_2010(7.0, ft)
            assert r.fault_type is ft

    def test_returns_scaling_result_instance(self) -> None:
        r = blaser_2010(6.0)
        assert isinstance(r, ScalingResult)


# ---------------------------------------------------------------------------
# magnitude_to_fault
# ---------------------------------------------------------------------------


class TestMagnitudeToFault:
    def test_returns_fault_element(self) -> None:
        fe = magnitude_to_fault(
            magnitude=7.0,
            center_x=0.0, center_y=0.0,
            strike=0.0, dip=90.0, rake=0.0,
            top_depth=0.0,
        )
        assert isinstance(fe, FaultElement)

    def test_kode_is_standard(self) -> None:
        fe = magnitude_to_fault(
            magnitude=7.0,
            center_x=0.0, center_y=0.0,
            strike=0.0, dip=90.0, rake=0.0,
            top_depth=0.0,
        )
        assert fe.kode is Kode.STANDARD

    def test_center_preserved(self) -> None:
        # For strike=0 (N), center should be midpoint of endpoints
        fe = magnitude_to_fault(
            magnitude=7.0,
            center_x=10.0, center_y=20.0,
            strike=0.0, dip=90.0, rake=0.0,
            top_depth=0.0,
        )
        assert math.isclose(fe.center_x, 10.0, abs_tol=1e-9)
        assert math.isclose(fe.center_y, 20.0, abs_tol=1e-9)

    def test_strike_zero_endpoints_aligned_ns(self) -> None:
        # Strike=0 means fault runs N-S; x_start==x_fin, y differs
        fe = magnitude_to_fault(
            magnitude=7.0,
            center_x=0.0, center_y=0.0,
            strike=0.0, dip=90.0, rake=0.0,
            top_depth=0.0,
        )
        assert math.isclose(fe.x_start, 0.0, abs_tol=1e-9)
        assert math.isclose(fe.x_fin, 0.0, abs_tol=1e-9)
        assert fe.y_fin > fe.y_start  # N endpoint is north of S endpoint

    def test_strike_90_endpoints_aligned_ew(self) -> None:
        # Strike=90 means fault runs E-W; y_start==y_fin, x differs
        fe = magnitude_to_fault(
            magnitude=7.0,
            center_x=0.0, center_y=0.0,
            strike=90.0, dip=90.0, rake=0.0,
            top_depth=0.0,
        )
        assert math.isclose(fe.y_start, 0.0, abs_tol=1e-9)
        assert math.isclose(fe.y_fin, 0.0, abs_tol=1e-9)
        assert fe.x_fin > fe.x_start

    def test_length_matches_scaling_result(self) -> None:
        fe = magnitude_to_fault(
            magnitude=7.0,
            center_x=0.0, center_y=0.0,
            strike=0.0, dip=90.0, rake=0.0,
            top_depth=0.0,
        )
        sr = wells_coppersmith_1994(7.0, FaultType.ALL)
        assert math.isclose(fe.length, sr.length_km, rel_tol=1e-6)

    def test_bottom_depth_from_width_and_dip(self) -> None:
        dip = 60.0
        top = 2.0
        fe = magnitude_to_fault(
            magnitude=7.0,
            center_x=0.0, center_y=0.0,
            strike=0.0, dip=dip, rake=0.0,
            top_depth=top,
        )
        sr = wells_coppersmith_1994(7.0, FaultType.ALL)
        expected_bottom = top + sr.width_km * math.sin(math.radians(dip))
        assert math.isclose(fe.bottom_depth, expected_bottom, rel_tol=1e-6)

    def test_pure_right_lateral_slip_components(self) -> None:
        # rake=0 → pure right-lateral; slip_1 negative (RL convention), slip_2=0
        fe = magnitude_to_fault(
            magnitude=7.0,
            center_x=0.0, center_y=0.0,
            strike=0.0, dip=90.0, rake=0.0,
            top_depth=0.0,
        )
        assert fe.slip_1 < 0.0
        assert math.isclose(fe.slip_2, 0.0, abs_tol=1e-9)

    def test_pure_reverse_slip_components(self) -> None:
        # rake=90 → pure reverse; slip_2 positive, slip_1 ≈ 0
        fe = magnitude_to_fault(
            magnitude=7.0,
            center_x=0.0, center_y=0.0,
            strike=0.0, dip=45.0, rake=90.0,
            top_depth=0.0,
        )
        assert math.isclose(fe.slip_1, 0.0, abs_tol=1e-9)
        assert fe.slip_2 > 0.0

    def test_wc94_relation_is_default(self) -> None:
        fe_default = magnitude_to_fault(7.0, 0.0, 0.0, 0.0, 90.0, 0.0, 0.0)
        fe_wc94 = magnitude_to_fault(
            7.0, 0.0, 0.0, 0.0, 90.0, 0.0, 0.0,
            relation="wells_coppersmith_1994",
        )
        assert math.isclose(fe_default.length, fe_wc94.length, rel_tol=1e-9)

    def test_blaser_relation_gives_different_length(self) -> None:
        fe_wc94 = magnitude_to_fault(
            7.0, 0.0, 0.0, 0.0, 90.0, 0.0, 0.0,
            relation="wells_coppersmith_1994",
        )
        fe_b10 = magnitude_to_fault(
            7.0, 0.0, 0.0, 0.0, 90.0, 0.0, 0.0,
            relation="blaser_2010",
        )
        assert not math.isclose(fe_wc94.length, fe_b10.length, rel_tol=1e-3)

    def test_invalid_relation_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown relation"):
            magnitude_to_fault(
                magnitude=7.0,
                center_x=0.0, center_y=0.0,
                strike=0.0, dip=90.0, rake=0.0,
                top_depth=0.0,
                relation="strasser_2010",
            )

    def test_label_contains_magnitude_and_relation(self) -> None:
        fe = magnitude_to_fault(
            magnitude=7.0,
            center_x=0.0, center_y=0.0,
            strike=0.0, dip=90.0, rake=0.0,
            top_depth=0.0,
            relation="wells_coppersmith_1994",
        )
        assert "7.0" in fe.label
        assert "wells_coppersmith_1994" in fe.label

    def test_larger_magnitude_gives_longer_fault(self) -> None:
        fe6 = magnitude_to_fault(6.0, 0.0, 0.0, 0.0, 90.0, 0.0, 0.0)
        fe7 = magnitude_to_fault(7.0, 0.0, 0.0, 0.0, 90.0, 0.0, 0.0)
        fe8 = magnitude_to_fault(8.0, 0.0, 0.0, 0.0, 90.0, 0.0, 0.0)
        assert fe6.length < fe7.length < fe8.length

    def test_larger_magnitude_gives_deeper_bottom(self) -> None:
        fe6 = magnitude_to_fault(6.0, 0.0, 0.0, 0.0, 45.0, 90.0, 0.0)
        fe7 = magnitude_to_fault(7.0, 0.0, 0.0, 0.0, 45.0, 90.0, 0.0)
        assert fe6.bottom_depth < fe7.bottom_depth


# ---------------------------------------------------------------------------
# CLI — scale command
# ---------------------------------------------------------------------------


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


class TestScaleCli:
    def test_basic_m7(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["scale", "7.0"])
        assert result.exit_code == 0
        assert "wells_coppersmith_1994" in result.output
        assert "7.0" in result.output

    def test_output_contains_all_fields(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["scale", "7.0"])
        assert "Length" in result.output
        assert "Width" in result.output
        assert "Area" in result.output
        assert "Displacement" in result.output

    def test_strike_slip_type(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["scale", "7.0", "--type", "strike_slip"])
        assert result.exit_code == 0
        assert "strike_slip" in result.output

    def test_reverse_type(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["scale", "7.0", "-t", "reverse"])
        assert result.exit_code == 0
        assert "reverse" in result.output

    def test_normal_type(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["scale", "6.5", "-t", "normal"])
        assert result.exit_code == 0
        assert "normal" in result.output

    def test_blaser_relation(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["scale", "7.0", "--relation", "blaser_2010"])
        assert result.exit_code == 0
        assert "blaser_2010" in result.output

    def test_blaser_short_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["scale", "7.0", "-r", "blaser_2010"])
        assert result.exit_code == 0
        assert "blaser_2010" in result.output

    def test_invalid_type_rejected(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["scale", "7.0", "--type", "thrust"])
        assert result.exit_code != 0

    def test_invalid_relation_rejected(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["scale", "7.0", "--relation", "unknown"])
        assert result.exit_code != 0

    def test_m5_produces_smaller_length_than_m8(self, runner: CliRunner) -> None:
        import re

        r5 = runner.invoke(cli, ["scale", "5.0"])
        r8 = runner.invoke(cli, ["scale", "8.0"])
        assert r5.exit_code == 0
        assert r8.exit_code == 0

        def extract_length(output: str) -> float:
            m = re.search(r"Length:\s+([\d.]+)", output)
            assert m is not None
            return float(m.group(1))

        assert extract_length(r5.output) < extract_length(r8.output)
