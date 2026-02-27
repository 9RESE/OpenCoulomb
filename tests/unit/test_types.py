"""Unit tests for all opencoulomb.types modules.

Covers:
- FaultElement, Kode          (types/fault.py)
- GridSpec                    (types/grid.py)
- MaterialProperties          (types/material.py)
- PrincipalStress, RegionalStress, StressTensorComponents (types/stress.py)
- CoulombModel                (types/model.py)
- StressResult, CoulombResult, ElementResult (types/result.py)
- CrossSectionSpec, CrossSectionResult       (types/section.py)
- ValidationError             (exceptions.py)
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from opencoulomb.exceptions import ValidationError
from opencoulomb.types import (
    CoulombModel,
    CoulombResult,
    CrossSectionResult,
    CrossSectionSpec,
    ElementResult,
    FaultElement,
    GridSpec,
    Kode,
    MaterialProperties,
    PrincipalStress,
    RegionalStress,
    StressResult,
    StressTensorComponents,
)

# ---------------------------------------------------------------------------
# Helpers / shared factories
# ---------------------------------------------------------------------------


def make_fault(
    *,
    x_start: float = 0.0,
    y_start: float = 0.0,
    x_fin: float = 10.0,
    y_fin: float = 0.0,
    kode: Kode = Kode.STANDARD,
    slip_1: float = 1.0,
    slip_2: float = 0.0,
    dip: float = 45.0,
    top_depth: float = 0.0,
    bottom_depth: float = 10.0,
    label: str = "",
    element_index: int = 0,
) -> FaultElement:
    return FaultElement(
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


def make_grid(
    *,
    start_x: float = -50.0,
    start_y: float = -50.0,
    finish_x: float = 50.0,
    finish_y: float = 50.0,
    x_inc: float = 5.0,
    y_inc: float = 5.0,
    depth: float = 10.0,
) -> GridSpec:
    return GridSpec(
        start_x=start_x,
        start_y=start_y,
        finish_x=finish_x,
        finish_y=finish_y,
        x_inc=x_inc,
        y_inc=y_inc,
        depth=depth,
    )


def make_material(
    *,
    poisson: float = 0.25,
    young: float = 8.0e5,
    friction: float = 0.4,
    depth: float = 10.0,
) -> MaterialProperties:
    return MaterialProperties(poisson=poisson, young=young, friction=friction, depth=depth)


def make_stress_result(n: int = 6) -> StressResult:
    z = np.zeros(n)
    return StressResult(
        x=np.ones(n),
        y=np.ones(n),
        z=z,
        ux=z.copy(),
        uy=z.copy(),
        uz=z.copy(),
        sxx=z.copy(),
        syy=z.copy(),
        szz=z.copy(),
        syz=z.copy(),
        sxz=z.copy(),
        sxy=z.copy(),
    )


def make_coulomb_result(n_y: int = 3, n_x: int = 4) -> CoulombResult:
    n = n_y * n_x
    sr = make_stress_result(n)
    return CoulombResult(
        stress=sr,
        cfs=np.arange(n, dtype=float),
        shear=np.zeros(n),
        normal=np.zeros(n),
        receiver_strike=0.0,
        receiver_dip=90.0,
        receiver_rake=0.0,
        grid_shape=(n_y, n_x),
    )


# ---------------------------------------------------------------------------
# 1. Kode enum
# ---------------------------------------------------------------------------


class TestKode:
    def test_integer_values(self) -> None:
        assert int(Kode.STANDARD) == 100
        assert int(Kode.TENSILE_RL) == 200
        assert int(Kode.TENSILE_REV) == 300
        assert int(Kode.POINT_SOURCE) == 400
        assert int(Kode.TENSILE_INFL) == 500

    def test_all_members_exist(self) -> None:
        members = {k.value for k in Kode}
        assert members == {100, 200, 300, 400, 500}

    def test_is_int_enum(self) -> None:
        assert Kode.STANDARD == 100
        assert Kode.POINT_SOURCE > Kode.TENSILE_REV


# ---------------------------------------------------------------------------
# 2. FaultElement — construction and immutability
# ---------------------------------------------------------------------------


class TestFaultElementConstruction:
    def test_basic_construction(self) -> None:
        f = make_fault()
        assert f.x_start == 0.0
        assert f.y_start == 0.0
        assert f.x_fin == 10.0
        assert f.y_fin == 0.0
        assert f.kode == Kode.STANDARD
        assert f.slip_1 == pytest.approx(1.0)
        assert f.slip_2 == pytest.approx(0.0)
        assert f.dip == pytest.approx(45.0)
        assert f.top_depth == pytest.approx(0.0)
        assert f.bottom_depth == pytest.approx(10.0)
        assert f.label == ""
        assert f.element_index == 0

    def test_default_label_and_index(self) -> None:
        f = make_fault()
        assert f.label == ""
        assert f.element_index == 0

    def test_custom_label_and_index(self) -> None:
        f = make_fault(label="mainshock", element_index=3)
        assert f.label == "mainshock"
        assert f.element_index == 3

    def test_all_kode_values_accepted(self) -> None:
        for kode in Kode:
            f = make_fault(kode=kode)
            assert f.kode == kode

    def test_dip_zero_accepted(self) -> None:
        # dip=0 is valid — horizontal fault
        f = make_fault(dip=0.0, top_depth=0.0, bottom_depth=10.0)
        assert f.dip == 0.0

    def test_dip_ninety_accepted(self) -> None:
        f = make_fault(dip=90.0)
        assert f.dip == 90.0

    def test_top_depth_zero_accepted(self) -> None:
        f = make_fault(top_depth=0.0, bottom_depth=1.0)
        assert f.top_depth == 0.0

    def test_negative_slip_accepted(self) -> None:
        f = make_fault(slip_1=-2.0, slip_2=-1.0)
        assert f.slip_1 == pytest.approx(-2.0)
        assert f.slip_2 == pytest.approx(-1.0)

    def test_zero_slip_accepted(self) -> None:
        f = make_fault(slip_1=0.0, slip_2=0.0)
        assert f.slip_1 == 0.0
        assert f.slip_2 == 0.0


class TestFaultElementImmutability:
    def test_frozen_raises_on_x_start(self) -> None:
        f = make_fault()
        with pytest.raises(AttributeError):
            f.x_start = 99.0  # type: ignore[misc]

    def test_frozen_raises_on_slip_1(self) -> None:
        f = make_fault()
        with pytest.raises(AttributeError):
            f.slip_1 = 5.0  # type: ignore[misc]

    def test_frozen_raises_on_dip(self) -> None:
        f = make_fault()
        with pytest.raises(AttributeError):
            f.dip = 30.0  # type: ignore[misc]

    def test_frozen_raises_on_kode(self) -> None:
        f = make_fault()
        with pytest.raises(AttributeError):
            f.kode = Kode.TENSILE_RL  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 3. FaultElement — validation errors
# ---------------------------------------------------------------------------


class TestFaultElementValidation:
    def test_dip_negative_raises(self) -> None:
        with pytest.raises(ValidationError, match="Dip"):
            make_fault(dip=-1.0)

    def test_dip_above_90_raises(self) -> None:
        with pytest.raises(ValidationError, match="Dip"):
            make_fault(dip=90.1)

    def test_dip_exactly_90_ok(self) -> None:
        f = make_fault(dip=90.0)
        assert f.dip == 90.0

    def test_dip_exactly_0_ok(self) -> None:
        f = make_fault(dip=0.0)
        assert f.dip == 0.0

    def test_top_depth_negative_raises(self) -> None:
        with pytest.raises(ValidationError, match="depth"):
            make_fault(top_depth=-1.0, bottom_depth=5.0)

    def test_bottom_depth_equal_to_top_raises(self) -> None:
        with pytest.raises(ValidationError, match="depth"):
            make_fault(top_depth=5.0, bottom_depth=5.0)

    def test_bottom_depth_less_than_top_raises(self) -> None:
        with pytest.raises(ValidationError, match="depth"):
            make_fault(top_depth=10.0, bottom_depth=5.0)

    def test_bottom_depth_just_above_top_ok(self) -> None:
        f = make_fault(top_depth=5.0, bottom_depth=5.001)
        assert f.bottom_depth > f.top_depth


# ---------------------------------------------------------------------------
# 4. FaultElement — classification properties
# ---------------------------------------------------------------------------


class TestFaultElementProperties:
    def test_is_source_with_nonzero_slip_1(self) -> None:
        f = make_fault(slip_1=1.0, slip_2=0.0)
        assert f.is_source is True
        assert f.is_receiver is False

    def test_is_source_with_nonzero_slip_2(self) -> None:
        f = make_fault(slip_1=0.0, slip_2=1.0)
        assert f.is_source is True
        assert f.is_receiver is False

    def test_is_source_with_both_nonzero(self) -> None:
        f = make_fault(slip_1=1.0, slip_2=1.0)
        assert f.is_source is True

    def test_is_receiver_when_zero_slip(self) -> None:
        f = make_fault(slip_1=0.0, slip_2=0.0)
        assert f.is_receiver is True
        assert f.is_source is False

    def test_is_point_source_kode_400(self) -> None:
        f = make_fault(kode=Kode.POINT_SOURCE)
        assert f.is_point_source is True

    def test_is_point_source_kode_500(self) -> None:
        f = make_fault(kode=Kode.TENSILE_INFL)
        assert f.is_point_source is True

    def test_not_point_source_kode_100(self) -> None:
        f = make_fault(kode=Kode.STANDARD)
        assert f.is_point_source is False

    def test_not_point_source_kode_200(self) -> None:
        f = make_fault(kode=Kode.TENSILE_RL)
        assert f.is_point_source is False

    def test_not_point_source_kode_300(self) -> None:
        f = make_fault(kode=Kode.TENSILE_REV)
        assert f.is_point_source is False


# ---------------------------------------------------------------------------
# 5. FaultElement — computed geometry properties
# ---------------------------------------------------------------------------


class TestFaultElementGeometry:
    def test_strike_ew_fault(self) -> None:
        # x_fin > x_start, y unchanged => dx=10, dy=0 => atan2(10,0)=90
        f = make_fault(x_start=0.0, y_start=0.0, x_fin=10.0, y_fin=0.0)
        assert f.strike_deg == pytest.approx(90.0)

    def test_strike_ns_fault(self) -> None:
        # y_fin > y_start, x unchanged => dx=0, dy=10 => atan2(0,10)=0
        f = make_fault(x_start=0.0, y_start=0.0, x_fin=0.0, y_fin=10.0)
        assert f.strike_deg == pytest.approx(0.0)

    def test_strike_ne_fault(self) -> None:
        # dx=10, dy=10 => atan2(10,10)=45
        f = make_fault(x_start=0.0, y_start=0.0, x_fin=10.0, y_fin=10.0)
        assert f.strike_deg == pytest.approx(45.0)

    def test_strike_nw_fault(self) -> None:
        # dx=-10, dy=10 => atan2(-10,10)=-45 => %360 = 315
        f = make_fault(x_start=0.0, y_start=0.0, x_fin=-10.0, y_fin=10.0)
        assert f.strike_deg == pytest.approx(315.0)

    def test_strike_south(self) -> None:
        # dx=0, dy=-10 => atan2(0,-10)=180
        f = make_fault(x_start=0.0, y_start=0.0, x_fin=0.0, y_fin=-10.0)
        assert f.strike_deg == pytest.approx(180.0)

    def test_length_3_4_5_triangle(self) -> None:
        f = make_fault(x_start=0.0, y_start=0.0, x_fin=3.0, y_fin=4.0)
        assert f.length == pytest.approx(5.0)

    def test_length_ew_10km(self) -> None:
        f = make_fault(x_start=0.0, y_start=0.0, x_fin=10.0, y_fin=0.0)
        assert f.length == pytest.approx(10.0)

    def test_width_dip90(self) -> None:
        # width = (10-0)/sin(90) = 10
        f = make_fault(dip=90.0, top_depth=0.0, bottom_depth=10.0)
        assert f.width == pytest.approx(10.0)

    def test_width_dip45(self) -> None:
        # width = (10-0)/sin(45) = 10*sqrt(2)
        f = make_fault(dip=45.0, top_depth=0.0, bottom_depth=10.0)
        assert f.width == pytest.approx(10.0 * math.sqrt(2))

    def test_width_dip30(self) -> None:
        # width = (5-0)/sin(30) = 5/0.5 = 10
        f = make_fault(dip=30.0, top_depth=0.0, bottom_depth=5.0)
        assert f.width == pytest.approx(10.0)

    def test_width_horizontal_fault_is_zero(self) -> None:
        # dip=0 => no down-dip dimension
        f = make_fault(dip=0.0, top_depth=0.0, bottom_depth=10.0)
        assert f.width == pytest.approx(0.0)

    def test_center_x(self) -> None:
        f = make_fault(x_start=0.0, x_fin=10.0)
        assert f.center_x == pytest.approx(5.0)

    def test_center_y(self) -> None:
        f = make_fault(y_start=2.0, y_fin=8.0)
        assert f.center_y == pytest.approx(5.0)

    def test_center_depth(self) -> None:
        f = make_fault(top_depth=2.0, bottom_depth=12.0)
        assert f.center_depth == pytest.approx(7.0)

    def test_center_depth_surface_rupture(self) -> None:
        f = make_fault(top_depth=0.0, bottom_depth=10.0)
        assert f.center_depth == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# 6. FaultElement — rake computation
# ---------------------------------------------------------------------------


class TestFaultElementRake:
    def test_rake_pure_right_lateral(self) -> None:
        # slip_1=1 (RL+), slip_2=0 => atan2(0, -1) = 180
        f = make_fault(kode=Kode.STANDARD, slip_1=1.0, slip_2=0.0)
        assert f.rake_deg == pytest.approx(180.0)

    def test_rake_pure_reverse(self) -> None:
        # slip_1=0, slip_2=1 (reverse+) => atan2(1, 0) = 90
        f = make_fault(kode=Kode.STANDARD, slip_1=0.0, slip_2=1.0)
        assert f.rake_deg == pytest.approx(90.0)

    def test_rake_pure_left_lateral(self) -> None:
        # slip_1=-1, slip_2=0 => atan2(0, 1) = 0
        f = make_fault(kode=Kode.STANDARD, slip_1=-1.0, slip_2=0.0)
        assert f.rake_deg == pytest.approx(0.0)

    def test_rake_pure_normal(self) -> None:
        # slip_1=0, slip_2=-1 => atan2(-1, 0) = -90
        f = make_fault(kode=Kode.STANDARD, slip_1=0.0, slip_2=-1.0)
        assert f.rake_deg == pytest.approx(-90.0)

    def test_rake_for_point_source_kode400(self) -> None:
        f = make_fault(kode=Kode.POINT_SOURCE, slip_1=1.0, slip_2=0.0)
        assert f.rake_deg == pytest.approx(180.0)

    def test_rake_undefined_for_tensile(self) -> None:
        # For non-STANDARD, non-POINT_SOURCE kodes rake returns 0.0
        for kode in (Kode.TENSILE_RL, Kode.TENSILE_REV, Kode.TENSILE_INFL):
            f = make_fault(kode=kode)
            assert f.rake_deg == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 7. GridSpec — construction and immutability
# ---------------------------------------------------------------------------


class TestGridSpecConstruction:
    def test_basic_construction(self) -> None:
        g = make_grid()
        assert g.start_x == pytest.approx(-50.0)
        assert g.start_y == pytest.approx(-50.0)
        assert g.finish_x == pytest.approx(50.0)
        assert g.finish_y == pytest.approx(50.0)
        assert g.x_inc == pytest.approx(5.0)
        assert g.y_inc == pytest.approx(5.0)
        assert g.depth == pytest.approx(10.0)

    def test_default_depth(self) -> None:
        g = GridSpec(
            start_x=0.0, start_y=0.0,
            finish_x=10.0, finish_y=10.0,
            x_inc=1.0, y_inc=1.0,
        )
        assert g.depth == pytest.approx(10.0)

    def test_frozen_raises_on_x_inc(self) -> None:
        g = make_grid()
        with pytest.raises(AttributeError):
            g.x_inc = 1.0  # type: ignore[misc]

    def test_frozen_raises_on_start_x(self) -> None:
        g = make_grid()
        with pytest.raises(AttributeError):
            g.start_x = 0.0  # type: ignore[misc]


class TestGridSpecValidation:
    def test_finish_x_le_start_x_raises(self) -> None:
        with pytest.raises(ValidationError, match="finish_x"):
            make_grid(start_x=10.0, finish_x=10.0)

    def test_finish_x_lt_start_x_raises(self) -> None:
        with pytest.raises(ValidationError, match="finish_x"):
            make_grid(start_x=20.0, finish_x=10.0)

    def test_finish_y_le_start_y_raises(self) -> None:
        with pytest.raises(ValidationError, match="finish_y"):
            make_grid(start_y=10.0, finish_y=10.0)

    def test_finish_y_lt_start_y_raises(self) -> None:
        with pytest.raises(ValidationError, match="finish_y"):
            make_grid(start_y=20.0, finish_y=10.0)

    def test_x_inc_zero_raises(self) -> None:
        with pytest.raises(ValidationError, match=r"[Ii]ncrement"):
            make_grid(x_inc=0.0)

    def test_x_inc_negative_raises(self) -> None:
        with pytest.raises(ValidationError, match=r"[Ii]ncrement"):
            make_grid(x_inc=-1.0)

    def test_y_inc_zero_raises(self) -> None:
        with pytest.raises(ValidationError, match=r"[Ii]ncrement"):
            make_grid(y_inc=0.0)

    def test_y_inc_negative_raises(self) -> None:
        with pytest.raises(ValidationError, match=r"[Ii]ncrement"):
            make_grid(y_inc=-5.0)


class TestGridSpecProperties:
    def test_n_x_integer_spacing(self) -> None:
        # start=0, finish=10, inc=1 => floor(10/1)+1 = 11
        g = GridSpec(start_x=0, start_y=0, finish_x=10, finish_y=5, x_inc=1, y_inc=1)
        assert g.n_x == 11

    def test_n_y_integer_spacing(self) -> None:
        g = GridSpec(start_x=0, start_y=0, finish_x=10, finish_y=5, x_inc=1, y_inc=1)
        assert g.n_y == 6

    def test_n_points(self) -> None:
        g = GridSpec(start_x=0, start_y=0, finish_x=10, finish_y=5, x_inc=1, y_inc=1)
        assert g.n_points == g.n_x * g.n_y
        assert g.n_points == 66

    def test_n_x_non_integer_spacing(self) -> None:
        # start=0, finish=10, inc=3 => floor(10/3)+1=4
        g = GridSpec(start_x=0, start_y=0, finish_x=10, finish_y=10, x_inc=3, y_inc=5)
        assert g.n_x == 4  # 0, 3, 6, 9

    def test_n_x_n_y_symmetric_grid(self) -> None:
        g = GridSpec(start_x=-50, start_y=-50, finish_x=50, finish_y=50, x_inc=5, y_inc=5)
        assert g.n_x == 21
        assert g.n_y == 21
        assert g.n_points == 441

    def test_very_small_increment(self) -> None:
        g = GridSpec(start_x=0, start_y=0, finish_x=1, finish_y=1, x_inc=0.01, y_inc=0.01)
        assert g.n_x == 101
        assert g.n_y == 101
        assert g.n_points == 101 * 101

    def test_large_grid(self) -> None:
        g = GridSpec(start_x=-500, start_y=-500, finish_x=500, finish_y=500, x_inc=10, y_inc=10)
        assert g.n_x == 101
        assert g.n_y == 101


# ---------------------------------------------------------------------------
# 8. MaterialProperties — defaults and construction
# ---------------------------------------------------------------------------


class TestMaterialPropertiesConstruction:
    def test_default_values(self) -> None:
        m = MaterialProperties()
        assert m.poisson == pytest.approx(0.25)
        assert m.young == pytest.approx(8.0e5)
        assert m.friction == pytest.approx(0.4)
        assert m.depth == pytest.approx(10.0)

    def test_custom_values(self) -> None:
        m = MaterialProperties(poisson=0.3, young=5e5, friction=0.5, depth=5.0)
        assert m.poisson == pytest.approx(0.3)
        assert m.young == pytest.approx(5e5)
        assert m.friction == pytest.approx(0.5)
        assert m.depth == pytest.approx(5.0)

    def test_frozen_raises(self) -> None:
        m = MaterialProperties()
        with pytest.raises(AttributeError):
            m.poisson = 0.3  # type: ignore[misc]

    def test_zero_friction_accepted(self) -> None:
        m = MaterialProperties(friction=0.0)
        assert m.friction == pytest.approx(0.0)

    def test_zero_depth_accepted(self) -> None:
        m = MaterialProperties(depth=0.0)
        assert m.depth == pytest.approx(0.0)


class TestMaterialPropertiesValidation:
    def test_poisson_zero_raises(self) -> None:
        with pytest.raises(ValidationError, match=r"[Pp]oisson"):
            MaterialProperties(poisson=0.0)

    def test_poisson_half_raises(self) -> None:
        with pytest.raises(ValidationError, match=r"[Pp]oisson"):
            MaterialProperties(poisson=0.5)

    def test_poisson_above_half_raises(self) -> None:
        with pytest.raises(ValidationError, match=r"[Pp]oisson"):
            MaterialProperties(poisson=0.6)

    def test_poisson_negative_raises(self) -> None:
        with pytest.raises(ValidationError, match=r"[Pp]oisson"):
            MaterialProperties(poisson=-0.1)

    def test_young_zero_raises(self) -> None:
        with pytest.raises(ValidationError, match=r"[Yy]oung"):
            MaterialProperties(young=0.0)

    def test_young_negative_raises(self) -> None:
        with pytest.raises(ValidationError, match=r"[Yy]oung"):
            MaterialProperties(young=-1.0)

    def test_friction_negative_raises(self) -> None:
        with pytest.raises(ValidationError, match=r"[Ff]riction"):
            MaterialProperties(friction=-0.1)

    def test_depth_negative_raises(self) -> None:
        with pytest.raises(ValidationError, match=r"[Dd]epth"):
            MaterialProperties(depth=-1.0)


class TestMaterialPropertiesComputedProperties:
    def test_alpha_default_poisson(self) -> None:
        # alpha = 1/(2*(1-0.25)) = 1/1.5 = 2/3
        m = MaterialProperties()
        assert m.alpha == pytest.approx(2.0 / 3.0)

    def test_alpha_poisson_0_3(self) -> None:
        # alpha = 1/(2*(1-0.3)) = 1/1.4
        m = MaterialProperties(poisson=0.3)
        assert m.alpha == pytest.approx(1.0 / (2.0 * 0.7))

    def test_alpha_near_zero_poisson(self) -> None:
        m = MaterialProperties(poisson=0.001)
        assert m.alpha == pytest.approx(1.0 / (2.0 * 0.999))

    def test_shear_modulus_default(self) -> None:
        # shear = 8e5 / (2*(1+0.25)) = 8e5 / 2.5 = 320000
        m = MaterialProperties()
        assert m.shear_modulus == pytest.approx(320000.0)

    def test_shear_modulus_custom(self) -> None:
        m = MaterialProperties(poisson=0.3, young=1.0e6)
        expected = 1.0e6 / (2.0 * 1.3)
        assert m.shear_modulus == pytest.approx(expected)

    def test_lame_lambda_default(self) -> None:
        # lambda = 8e5 * 0.25 / ((1.25)*(0.5)) = 200000 / 0.625 = 320000
        m = MaterialProperties()
        nu = 0.25
        expected = 8e5 * nu / ((1 + nu) * (1 - 2 * nu))
        assert m.lame_lambda == pytest.approx(expected)

    def test_lame_lambda_custom(self) -> None:
        nu = 0.3
        E = 9.0e5
        m = MaterialProperties(poisson=nu, young=E)
        expected = E * nu / ((1 + nu) * (1 - 2 * nu))
        assert m.lame_lambda == pytest.approx(expected)

    def test_lame_relation(self) -> None:
        # Verify E = mu*(3*lambda + 2*mu) / (lambda + mu)
        m = MaterialProperties()
        mu = m.shear_modulus
        lam = m.lame_lambda
        E_reconstructed = mu * (3 * lam + 2 * mu) / (lam + mu)
        assert E_reconstructed == pytest.approx(m.young, rel=1e-10)


# ---------------------------------------------------------------------------
# 9. Stress types
# ---------------------------------------------------------------------------


class TestPrincipalStress:
    def test_construction(self) -> None:
        ps = PrincipalStress(direction=0.0, dip=90.0, intensity=100.0, gradient=5.0)
        assert ps.direction == pytest.approx(0.0)
        assert ps.dip == pytest.approx(90.0)
        assert ps.intensity == pytest.approx(100.0)
        assert ps.gradient == pytest.approx(5.0)

    def test_frozen(self) -> None:
        ps = PrincipalStress(direction=0.0, dip=0.0, intensity=0.0, gradient=0.0)
        with pytest.raises(AttributeError):
            ps.direction = 45.0  # type: ignore[misc]

    def test_negative_intensity_accepted(self) -> None:
        ps = PrincipalStress(direction=0.0, dip=0.0, intensity=-50.0, gradient=0.0)
        assert ps.intensity == pytest.approx(-50.0)


class TestRegionalStress:
    def _make_ps(self, direction: float = 0.0) -> PrincipalStress:
        return PrincipalStress(direction=direction, dip=0.0, intensity=100.0, gradient=5.0)

    def test_construction_three_axes(self) -> None:
        rs = RegionalStress(
            s1=self._make_ps(0.0),
            s2=self._make_ps(90.0),
            s3=self._make_ps(180.0),
        )
        assert rs.s1.direction == pytest.approx(0.0)
        assert rs.s2.direction == pytest.approx(90.0)
        assert rs.s3.direction == pytest.approx(180.0)

    def test_frozen(self) -> None:
        rs = RegionalStress(
            s1=self._make_ps(), s2=self._make_ps(), s3=self._make_ps()
        )
        with pytest.raises(AttributeError):
            rs.s1 = self._make_ps(45.0)  # type: ignore[misc]


class TestStressTensorComponents:
    def test_construction(self) -> None:
        stc = StressTensorComponents(
            sxx=1.0, syy=2.0, szz=3.0,
            syz=0.1, sxz=0.2, sxy=0.3,
        )
        assert stc.sxx == pytest.approx(1.0)
        assert stc.syy == pytest.approx(2.0)
        assert stc.szz == pytest.approx(3.0)
        assert stc.syz == pytest.approx(0.1)
        assert stc.sxz == pytest.approx(0.2)
        assert stc.sxy == pytest.approx(0.3)

    def test_frozen(self) -> None:
        stc = StressTensorComponents(
            sxx=0.0, syy=0.0, szz=0.0,
            syz=0.0, sxz=0.0, sxy=0.0,
        )
        with pytest.raises(AttributeError):
            stc.sxx = 1.0  # type: ignore[misc]

    def test_isotropic_tensor(self) -> None:
        p = 50.0
        stc = StressTensorComponents(
            sxx=p, syy=p, szz=p,
            syz=0.0, sxz=0.0, sxy=0.0,
        )
        assert stc.sxx == stc.syy == stc.szz

    def test_zero_tensor(self) -> None:
        stc = StressTensorComponents(
            sxx=0.0, syy=0.0, szz=0.0,
            syz=0.0, sxz=0.0, sxy=0.0,
        )
        for field in (stc.sxx, stc.syy, stc.szz, stc.syz, stc.sxz, stc.sxy):
            assert field == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 10. CoulombModel
# ---------------------------------------------------------------------------


class TestCoulombModel:
    def _make_model(
        self,
        n_sources: int = 2,
        n_receivers: int = 1,
    ) -> CoulombModel:
        material = make_material()
        grid = make_grid()
        sources = [make_fault(slip_1=1.0, element_index=i) for i in range(n_sources)]
        receivers = [make_fault(slip_1=0.0, slip_2=0.0, element_index=i + n_sources)
                     for i in range(n_receivers)]
        faults = sources + receivers
        return CoulombModel(
            title="Test model",
            material=material,
            faults=faults,
            grid=grid,
            n_fixed=n_sources,
        )

    def test_basic_construction(self) -> None:
        m = self._make_model()
        assert m.title == "Test model"
        assert isinstance(m.material, MaterialProperties)
        assert isinstance(m.grid, GridSpec)
        assert m.n_fixed == 2

    def test_regional_stress_defaults_none(self) -> None:
        m = self._make_model()
        assert m.regional_stress is None

    def test_symmetry_defaults(self) -> None:
        m = self._make_model()
        assert m.symmetry == 1
        assert m.x_sym == pytest.approx(0.0)
        assert m.y_sym == pytest.approx(0.0)

    def test_source_faults_slice(self) -> None:
        m = self._make_model(n_sources=2, n_receivers=1)
        assert len(m.source_faults) == 2

    def test_receiver_faults_slice(self) -> None:
        m = self._make_model(n_sources=2, n_receivers=3)
        assert len(m.receiver_faults) == 3

    def test_n_sources_property(self) -> None:
        m = self._make_model(n_sources=4, n_receivers=1)
        assert m.n_sources == 4

    def test_n_receivers_property(self) -> None:
        m = self._make_model(n_sources=2, n_receivers=5)
        assert m.n_receivers == 5

    def test_n_sources_plus_n_receivers_equals_faults(self) -> None:
        m = self._make_model(n_sources=3, n_receivers=4)
        assert m.n_sources + m.n_receivers == len(m.faults)

    def test_source_faults_indices(self) -> None:
        m = self._make_model(n_sources=2, n_receivers=1)
        assert m.source_faults[0].element_index == 0
        assert m.source_faults[1].element_index == 1

    def test_receiver_faults_indices(self) -> None:
        m = self._make_model(n_sources=2, n_receivers=2)
        # Receiver element_index was set to n_sources + i
        assert m.receiver_faults[0].element_index == 2
        assert m.receiver_faults[1].element_index == 3

    def test_no_sources(self) -> None:
        m = self._make_model(n_sources=0, n_receivers=3)
        assert m.n_sources == 0
        assert m.source_faults == []
        assert m.n_receivers == 3

    def test_no_receivers(self) -> None:
        m = self._make_model(n_sources=3, n_receivers=0)
        assert m.n_receivers == 0
        assert m.receiver_faults == []

    def test_with_regional_stress(self) -> None:
        material = make_material()
        grid = make_grid()
        ps = PrincipalStress(direction=0.0, dip=90.0, intensity=100.0, gradient=5.0)
        rs = RegionalStress(s1=ps, s2=ps, s3=ps)
        m = CoulombModel(
            title="Test",
            material=material,
            faults=[make_fault()],
            grid=grid,
            n_fixed=1,
            regional_stress=rs,
        )
        assert m.regional_stress is rs

    def test_mutable_fields(self) -> None:
        m = self._make_model()
        m.title = "Updated title"
        assert m.title == "Updated title"


# ---------------------------------------------------------------------------
# 11. StressResult
# ---------------------------------------------------------------------------


class TestStressResult:
    def test_basic_construction(self) -> None:
        sr = make_stress_result(n=10)
        assert sr.n_points == 10
        assert sr.x.shape == (10,)
        assert sr.sxx.shape == (10,)

    def test_n_points_matches_array_length(self) -> None:
        for n in (1, 5, 100, 1000):
            sr = make_stress_result(n=n)
            assert sr.n_points == n

    def test_all_arrays_present(self) -> None:
        sr = make_stress_result(n=4)
        for attr in ("x", "y", "z", "ux", "uy", "uz",
                     "sxx", "syy", "szz", "syz", "sxz", "sxy"):
            assert hasattr(sr, attr)
            arr = getattr(sr, attr)
            assert arr.shape == (4,)

    def test_mutable_not_frozen(self) -> None:
        sr = make_stress_result(n=3)
        new_val = np.array([10.0, 20.0, 30.0])
        sr.sxx = new_val  # mutable dataclass
        np.testing.assert_array_equal(sr.sxx, new_val)


# ---------------------------------------------------------------------------
# 12. CoulombResult
# ---------------------------------------------------------------------------


class TestCoulombResult:
    def test_basic_construction(self) -> None:
        cr = make_coulomb_result(n_y=3, n_x=4)
        assert cr.receiver_strike == pytest.approx(0.0)
        assert cr.receiver_dip == pytest.approx(90.0)
        assert cr.receiver_rake == pytest.approx(0.0)
        assert cr.grid_shape == (3, 4)

    def test_oops_defaults_none(self) -> None:
        cr = make_coulomb_result()
        assert cr.oops_strike is None
        assert cr.oops_dip is None
        assert cr.oops_rake is None

    def test_cfs_grid_shape(self) -> None:
        n_y, n_x = 5, 7
        cr = make_coulomb_result(n_y=n_y, n_x=n_x)
        grid = cr.cfs_grid()
        assert grid.shape == (n_y, n_x)

    def test_cfs_grid_values_preserved(self) -> None:
        n_y, n_x = 3, 4
        cr = make_coulomb_result(n_y=n_y, n_x=n_x)
        grid = cr.cfs_grid()
        # Flat CFS is arange(n), reshaped to (n_y, n_x)
        expected = np.arange(n_y * n_x, dtype=float).reshape(n_y, n_x)
        np.testing.assert_array_equal(grid, expected)

    def test_displacement_grid_shapes(self) -> None:
        n_y, n_x = 4, 6
        cr = make_coulomb_result(n_y=n_y, n_x=n_x)
        ux, uy, uz = cr.displacement_grid()
        assert ux.shape == (n_y, n_x)
        assert uy.shape == (n_y, n_x)
        assert uz.shape == (n_y, n_x)

    def test_displacement_grid_values(self) -> None:
        n_y, n_x = 2, 3
        n = n_y * n_x
        sr = make_stress_result(n=n)
        sr.ux = np.ones(n) * 2.5
        sr.uy = np.ones(n) * 3.0
        sr.uz = np.ones(n) * 0.5
        cr = CoulombResult(
            stress=sr,
            cfs=np.zeros(n),
            shear=np.zeros(n),
            normal=np.zeros(n),
            receiver_strike=45.0,
            receiver_dip=60.0,
            receiver_rake=90.0,
            grid_shape=(n_y, n_x),
        )
        ux, uy, uz = cr.displacement_grid()
        np.testing.assert_array_almost_equal(ux, np.full((n_y, n_x), 2.5))
        np.testing.assert_array_almost_equal(uy, np.full((n_y, n_x), 3.0))
        np.testing.assert_array_almost_equal(uz, np.full((n_y, n_x), 0.5))

    def test_with_oops_arrays(self) -> None:
        n_y, n_x = 2, 2
        n = n_y * n_x
        sr = make_stress_result(n=n)
        cr = CoulombResult(
            stress=sr,
            cfs=np.zeros(n),
            shear=np.zeros(n),
            normal=np.zeros(n),
            receiver_strike=0.0,
            receiver_dip=90.0,
            receiver_rake=0.0,
            grid_shape=(n_y, n_x),
            oops_strike=np.full(n, 45.0),
            oops_dip=np.full(n, 30.0),
            oops_rake=np.full(n, 0.0),
        )
        assert cr.oops_strike is not None
        assert cr.oops_strike.shape == (n,)


# ---------------------------------------------------------------------------
# 13. ElementResult
# ---------------------------------------------------------------------------


class TestElementResult:
    def test_construction(self) -> None:
        faults = [make_fault(slip_1=0.0, slip_2=0.0) for _ in range(3)]
        er = ElementResult(
            elements=faults,
            cfs=np.array([0.1, 0.2, 0.3]),
            shear=np.array([0.5, 0.6, 0.7]),
            normal=np.array([1.0, 1.1, 1.2]),
        )
        assert len(er.elements) == 3
        assert er.cfs.shape == (3,)
        assert er.shear.shape == (3,)
        assert er.normal.shape == (3,)

    def test_cfs_values(self) -> None:
        faults = [make_fault(slip_1=0.0, slip_2=0.0)]
        er = ElementResult(
            elements=faults,
            cfs=np.array([0.42]),
            shear=np.array([0.0]),
            normal=np.array([0.0]),
        )
        assert er.cfs[0] == pytest.approx(0.42)


# ---------------------------------------------------------------------------
# 14. CrossSectionSpec
# ---------------------------------------------------------------------------


class TestCrossSectionSpec:
    def test_construction(self) -> None:
        cs = CrossSectionSpec(
            start_x=0.0, start_y=0.0,
            finish_x=100.0, finish_y=0.0,
            depth_min=0.0, depth_max=20.0,
            z_inc=1.0,
        )
        assert cs.start_x == pytest.approx(0.0)
        assert cs.finish_x == pytest.approx(100.0)
        assert cs.depth_min == pytest.approx(0.0)
        assert cs.depth_max == pytest.approx(20.0)
        assert cs.z_inc == pytest.approx(1.0)

    def test_frozen(self) -> None:
        cs = CrossSectionSpec(
            start_x=0.0, start_y=0.0,
            finish_x=10.0, finish_y=0.0,
            depth_min=0.0, depth_max=10.0,
            z_inc=1.0,
        )
        with pytest.raises(AttributeError):
            cs.depth_max = 50.0  # type: ignore[misc]

    def test_diagonal_profile(self) -> None:
        cs = CrossSectionSpec(
            start_x=-50.0, start_y=-50.0,
            finish_x=50.0, finish_y=50.0,
            depth_min=0.0, depth_max=30.0,
            z_inc=2.0,
        )
        assert cs.start_x == pytest.approx(-50.0)
        assert cs.finish_y == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# 15. CrossSectionResult
# ---------------------------------------------------------------------------


class TestCrossSectionResult:
    def _make_section_result(
        self, n_horiz: int = 10, n_vert: int = 5
    ) -> CrossSectionResult:
        spec = CrossSectionSpec(
            start_x=0.0, start_y=0.0,
            finish_x=float(n_horiz - 1),
            finish_y=0.0,
            depth_min=0.0, depth_max=float(n_vert - 1),
            z_inc=1.0,
        )
        z2d = np.zeros((n_vert, n_horiz))
        return CrossSectionResult(
            distance=np.linspace(0, n_horiz - 1, n_horiz),
            depth=np.linspace(0, n_vert - 1, n_vert),
            cfs=z2d.copy(),
            shear=z2d.copy(),
            normal=z2d.copy(),
            ux=z2d.copy(),
            uy=z2d.copy(),
            uz=z2d.copy(),
            sxx=z2d.copy(),
            syy=z2d.copy(),
            szz=z2d.copy(),
            syz=z2d.copy(),
            sxz=z2d.copy(),
            sxy=z2d.copy(),
            spec=spec,
        )

    def test_construction(self) -> None:
        csr = self._make_section_result(n_horiz=10, n_vert=5)
        assert csr.distance.shape == (10,)
        assert csr.depth.shape == (5,)
        assert csr.cfs.shape == (5, 10)

    def test_2d_array_shapes(self) -> None:
        n_h, n_v = 8, 6
        csr = self._make_section_result(n_horiz=n_h, n_vert=n_v)
        for attr in ("cfs", "shear", "normal", "ux", "uy", "uz",
                     "sxx", "syy", "szz", "syz", "sxz", "sxy"):
            arr = getattr(csr, attr)
            assert arr.shape == (n_v, n_h), f"{attr} has wrong shape"

    def test_spec_attached(self) -> None:
        csr = self._make_section_result()
        assert isinstance(csr.spec, CrossSectionSpec)

    def test_mutable(self) -> None:
        csr = self._make_section_result()
        new_cfs = np.ones_like(csr.cfs) * 99.0
        csr.cfs = new_cfs
        assert np.all(csr.cfs == 99.0)


# ---------------------------------------------------------------------------
# 16. ValidationError
# ---------------------------------------------------------------------------


class TestValidationError:
    def test_is_exception(self) -> None:
        err = ValidationError("test message")
        assert isinstance(err, Exception)

    def test_message_preserved(self) -> None:
        err = ValidationError("invalid depth value")
        assert "invalid depth" in str(err)

    def test_raised_by_fault_validation(self) -> None:
        with pytest.raises(ValidationError):
            make_fault(dip=180.0)

    def test_raised_by_grid_validation(self) -> None:
        with pytest.raises(ValidationError):
            make_grid(x_inc=-1.0)

    def test_raised_by_material_validation(self) -> None:
        with pytest.raises(ValidationError):
            MaterialProperties(poisson=0.0)

    def test_raised_by_section_negative_depth_min(self) -> None:
        with pytest.raises(ValidationError, match="depth_min"):
            CrossSectionSpec(
                start_x=0, start_y=0, finish_x=10, finish_y=0,
                depth_min=-1.0, depth_max=10.0, z_inc=1.0,
            )

    def test_raised_by_section_inverted_depths(self) -> None:
        with pytest.raises(ValidationError, match="depth_max"):
            CrossSectionSpec(
                start_x=0, start_y=0, finish_x=10, finish_y=0,
                depth_min=10.0, depth_max=5.0, z_inc=1.0,
            )

    def test_raised_by_section_equal_depths(self) -> None:
        with pytest.raises(ValidationError, match="depth_max"):
            CrossSectionSpec(
                start_x=0, start_y=0, finish_x=10, finish_y=0,
                depth_min=5.0, depth_max=5.0, z_inc=1.0,
            )

    def test_raised_by_section_zero_z_inc(self) -> None:
        with pytest.raises(ValidationError, match="z_inc"):
            CrossSectionSpec(
                start_x=0, start_y=0, finish_x=10, finish_y=0,
                depth_min=0.0, depth_max=10.0, z_inc=0.0,
            )

    def test_raised_by_section_negative_z_inc(self) -> None:
        with pytest.raises(ValidationError, match="z_inc"):
            CrossSectionSpec(
                start_x=0, start_y=0, finish_x=10, finish_y=0,
                depth_min=0.0, depth_max=10.0, z_inc=-1.0,
            )


# ---------------------------------------------------------------------------
# 17. Property-based tests (Hypothesis)
# ---------------------------------------------------------------------------


VALID_DIP = st.floats(min_value=0.0, max_value=90.0, allow_nan=False, allow_infinity=False)
VALID_DEPTH_RANGE = st.tuples(
    st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False),
).map(lambda t: (t[0], t[0] + t[1]))  # (top, bottom) where bottom > top

VALID_COORD = st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
VALID_SLIP = st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False)


@given(dip=VALID_DIP, depths=VALID_DEPTH_RANGE)
@settings(max_examples=200)
def test_fault_valid_dip_never_raises(dip: float, depths: tuple[float, float]) -> None:
    top, bottom = depths
    # Should never raise ValidationError for valid dip and depth range
    f = make_fault(dip=dip, top_depth=top, bottom_depth=bottom)
    assert f.dip == dip


@given(dip=st.floats(min_value=90.01, max_value=360.0, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_fault_invalid_dip_always_raises(dip: float) -> None:
    with pytest.raises(ValidationError):
        make_fault(dip=dip)


@given(dip=st.floats(max_value=-0.01, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_fault_negative_dip_always_raises(dip: float) -> None:
    with pytest.raises(ValidationError):
        make_fault(dip=dip)


@given(
    dip=VALID_DIP,
    depths=VALID_DEPTH_RANGE,
    slip_1=VALID_SLIP,
    slip_2=VALID_SLIP,
)
@settings(max_examples=100)
def test_fault_center_depth_midpoint(
    dip: float,
    depths: tuple[float, float],
    slip_1: float,
    slip_2: float,
) -> None:
    top, bottom = depths
    f = make_fault(dip=dip, top_depth=top, bottom_depth=bottom, slip_1=slip_1, slip_2=slip_2)
    expected_center = (top + bottom) / 2.0
    assert f.center_depth == pytest.approx(expected_center)


@given(
    dip=st.floats(min_value=0.01, max_value=90.0, allow_nan=False, allow_infinity=False),
    depths=VALID_DEPTH_RANGE,
)
@settings(max_examples=100)
def test_fault_width_positive_for_nonzero_dip(
    dip: float, depths: tuple[float, float]
) -> None:
    top, bottom = depths
    f = make_fault(dip=dip, top_depth=top, bottom_depth=bottom)
    assert f.width > 0.0


@given(
    start_x=st.floats(min_value=-1000.0, max_value=999.0, allow_nan=False, allow_infinity=False),
    start_y=st.floats(min_value=-1000.0, max_value=999.0, allow_nan=False, allow_infinity=False),
    ext_x=st.floats(min_value=0.001, max_value=500.0, allow_nan=False, allow_infinity=False),
    ext_y=st.floats(min_value=0.001, max_value=500.0, allow_nan=False, allow_infinity=False),
    x_inc=st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False),
    y_inc=st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_grid_n_points_at_least_one(
    start_x: float,
    start_y: float,
    ext_x: float,
    ext_y: float,
    x_inc: float,
    y_inc: float,
) -> None:
    g = GridSpec(
        start_x=start_x, start_y=start_y,
        finish_x=start_x + ext_x, finish_y=start_y + ext_y,
        x_inc=x_inc, y_inc=y_inc,
    )
    assert g.n_points >= 1


@given(
    start_x=st.floats(min_value=-1000.0, max_value=999.0, allow_nan=False, allow_infinity=False),
    start_y=st.floats(min_value=-1000.0, max_value=999.0, allow_nan=False, allow_infinity=False),
    ext_x=st.floats(min_value=0.001, max_value=500.0, allow_nan=False, allow_infinity=False),
    ext_y=st.floats(min_value=0.001, max_value=500.0, allow_nan=False, allow_infinity=False),
    x_inc=st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False),
    y_inc=st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_grid_n_points_equals_n_x_times_n_y(
    start_x: float,
    start_y: float,
    ext_x: float,
    ext_y: float,
    x_inc: float,
    y_inc: float,
) -> None:
    g = GridSpec(
        start_x=start_x, start_y=start_y,
        finish_x=start_x + ext_x, finish_y=start_y + ext_y,
        x_inc=x_inc, y_inc=y_inc,
    )
    assert g.n_points == g.n_x * g.n_y


@given(
    poisson=st.floats(min_value=0.001, max_value=0.499, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_material_alpha_formula(poisson: float) -> None:
    m = MaterialProperties(poisson=poisson)
    expected = 1.0 / (2.0 * (1.0 - poisson))
    assert m.alpha == pytest.approx(expected, rel=1e-10)


@given(
    poisson=st.floats(min_value=0.001, max_value=0.499, allow_nan=False, allow_infinity=False),
    young=st.floats(min_value=1.0, max_value=1e8, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=100)
def test_material_shear_modulus_formula(poisson: float, young: float) -> None:
    m = MaterialProperties(poisson=poisson, young=young)
    expected = young / (2.0 * (1.0 + poisson))
    assert m.shear_modulus == pytest.approx(expected, rel=1e-10)


@given(
    strike_x=VALID_COORD,
    strike_y=VALID_COORD,
)
@settings(max_examples=100)
def test_fault_strike_in_range_0_360(strike_x: float, strike_y: float) -> None:
    assume(abs(strike_x) + abs(strike_y) > 0.001)  # avoid degenerate zero-length trace
    f = make_fault(x_start=0.0, y_start=0.0, x_fin=strike_x, y_fin=strike_y)
    # Allow a tiny tolerance: floating-point modulo can yield exactly 360.0
    # for subnormal negative dx (e.g. atan2(-1e-119, 1.0) % 360 == 360.0).
    # Such a value is numerically equivalent to 0 degrees and acceptable.
    assert -1e-12 <= f.strike_deg <= 360.0 + 1e-12
