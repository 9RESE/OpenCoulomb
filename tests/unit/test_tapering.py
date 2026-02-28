"""Unit tests for opencoulomb.core.tapering.

Covers:
- TaperProfile enum: membership, values
- TaperSpec: valid construction, validation errors
- taper_function: center/edge values, zero-taper, known values,
  symmetry for all three profiles
- subdivide_fault: 1x1 identity, NxM count, area conservation,
  depth range tiling, slip/dip/kode preservation
- apply_taper: center subfaults have full slip, edges reduced,
  zero-fraction leaves slip unchanged, both slip components scaled
- subdivide_and_taper: end-to-end composition, moment reduction
- compute_grid with taper: None regression, tapered != untapered
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pytest

from opencoulomb.core.tapering import (
    TaperProfile,
    TaperSpec,
    apply_taper,
    subdivide_and_taper,
    subdivide_fault,
    taper_function,
)
from opencoulomb.types.fault import FaultElement, Kode

# ---------------------------------------------------------------------------
# Test fixture path
# ---------------------------------------------------------------------------

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "inp_files" / "real"
SIMPLEST_RECEIVER = FIXTURES / "simplest_receiver.inp"


# ---------------------------------------------------------------------------
# Shared factory helpers
# ---------------------------------------------------------------------------


def make_fault(
    *,
    x_start: float = -10.0,
    y_start: float = 0.0,
    x_fin: float = 10.0,
    y_fin: float = 0.0,
    kode: Kode = Kode.STANDARD,
    slip_1: float = 1.0,
    slip_2: float = 0.5,
    dip: float = 85.9,
    top_depth: float = 10.0,
    bottom_depth: float = 20.0,
    label: str = "test",
    element_index: int = 1,
) -> FaultElement:
    """Construct a FaultElement with convenient defaults."""
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


# ---------------------------------------------------------------------------
# 1. TaperProfile enum
# ---------------------------------------------------------------------------


class TestTaperProfile:
    """TaperProfile enum completeness and value types."""

    def test_cosine_exists(self) -> None:
        """COSINE member is accessible."""
        assert TaperProfile.COSINE is TaperProfile.COSINE

    def test_linear_exists(self) -> None:
        """LINEAR member is accessible."""
        assert TaperProfile.LINEAR is TaperProfile.LINEAR

    def test_elliptical_exists(self) -> None:
        """ELLIPTICAL member is accessible."""
        assert TaperProfile.ELLIPTICAL is TaperProfile.ELLIPTICAL

    def test_all_three_profiles_present(self) -> None:
        """Exactly three profiles exist."""
        names = {m.name for m in TaperProfile}
        assert names == {"COSINE", "LINEAR", "ELLIPTICAL"}

    def test_values_are_strings(self) -> None:
        """All profile enum values are strings."""
        for profile in TaperProfile:
            assert isinstance(profile.value, str), (
                f"{profile.name}.value should be str, got {type(profile.value)}"
            )

    def test_cosine_value(self) -> None:
        assert TaperProfile.COSINE.value == "cosine"

    def test_linear_value(self) -> None:
        assert TaperProfile.LINEAR.value == "linear"

    def test_elliptical_value(self) -> None:
        assert TaperProfile.ELLIPTICAL.value == "elliptical"


# ---------------------------------------------------------------------------
# 2. TaperSpec construction and validation
# ---------------------------------------------------------------------------


class TestTaperSpec:
    """TaperSpec dataclass validation."""

    def test_valid_default_construction(self) -> None:
        """Default TaperSpec is valid and has sensible values."""
        spec = TaperSpec()
        assert spec.profile == TaperProfile.COSINE
        assert spec.n_along_strike == 5
        assert spec.n_down_dip == 3
        assert spec.taper_width_fraction == 0.2

    def test_valid_custom_construction(self) -> None:
        """Explicit construction with valid parameters succeeds."""
        spec = TaperSpec(
            profile=TaperProfile.LINEAR,
            n_along_strike=10,
            n_down_dip=4,
            taper_width_fraction=0.35,
        )
        assert spec.profile == TaperProfile.LINEAR
        assert spec.n_along_strike == 10
        assert spec.n_down_dip == 4
        assert spec.taper_width_fraction == pytest.approx(0.35)

    def test_n_along_strike_minimum_one(self) -> None:
        """n_along_strike=1 is the valid minimum."""
        spec = TaperSpec(n_along_strike=1)
        assert spec.n_along_strike == 1

    def test_n_down_dip_minimum_one(self) -> None:
        """n_down_dip=1 is the valid minimum."""
        spec = TaperSpec(n_down_dip=1)
        assert spec.n_down_dip == 1

    def test_taper_width_fraction_zero_valid(self) -> None:
        """taper_width_fraction=0.0 is allowed (no taper)."""
        spec = TaperSpec(taper_width_fraction=0.0)
        assert spec.taper_width_fraction == 0.0

    def test_taper_width_fraction_half_valid(self) -> None:
        """taper_width_fraction=0.5 is allowed (full taper)."""
        spec = TaperSpec(taper_width_fraction=0.5)
        assert spec.taper_width_fraction == 0.5

    def test_n_along_strike_zero_raises(self) -> None:
        """n_along_strike < 1 raises ValueError."""
        with pytest.raises(ValueError, match="n_along_strike"):
            TaperSpec(n_along_strike=0)

    def test_n_along_strike_negative_raises(self) -> None:
        """Negative n_along_strike raises ValueError."""
        with pytest.raises(ValueError, match="n_along_strike"):
            TaperSpec(n_along_strike=-3)

    def test_n_down_dip_zero_raises(self) -> None:
        """n_down_dip < 1 raises ValueError."""
        with pytest.raises(ValueError, match="n_down_dip"):
            TaperSpec(n_down_dip=0)

    def test_n_down_dip_negative_raises(self) -> None:
        """Negative n_down_dip raises ValueError."""
        with pytest.raises(ValueError, match="n_down_dip"):
            TaperSpec(n_down_dip=-1)

    def test_taper_width_fraction_negative_raises(self) -> None:
        """taper_width_fraction < 0 raises ValueError."""
        with pytest.raises(ValueError, match="taper_width_fraction"):
            TaperSpec(taper_width_fraction=-0.1)

    def test_taper_width_fraction_above_half_raises(self) -> None:
        """taper_width_fraction > 0.5 raises ValueError."""
        with pytest.raises(ValueError, match="taper_width_fraction"):
            TaperSpec(taper_width_fraction=0.51)

    def test_frozen_immutability(self) -> None:
        """TaperSpec is frozen (cannot assign attributes)."""
        spec = TaperSpec()
        with pytest.raises((TypeError, AttributeError)):
            spec.n_along_strike = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 3. taper_function
# ---------------------------------------------------------------------------


class TestTaperFunction:
    """taper_function: weights at center, edge, and within taper zone."""

    # --- Center position always returns 1.0 ---

    @pytest.mark.parametrize("profile", list(TaperProfile))
    def test_center_returns_one_for_all_profiles(self, profile: TaperProfile) -> None:
        """xi=0.5 is in the untapered interior: weight must be 1.0."""
        weight = taper_function(0.5, profile, taper_fraction=0.2)
        assert weight == pytest.approx(1.0)

    @pytest.mark.parametrize("profile", list(TaperProfile))
    def test_center_returns_one_large_taper(self, profile: TaperProfile) -> None:
        """xi=0.5 with taper_fraction=0.5 gives 1.0 (exactly at boundary)."""
        weight = taper_function(0.5, profile, taper_fraction=0.5)
        assert weight == pytest.approx(1.0)

    # --- Edge position approaches 0 ---

    @pytest.mark.parametrize("profile", list(TaperProfile))
    def test_edge_start_approaches_zero(self, profile: TaperProfile) -> None:
        """xi=0.0 (start edge) gives 0.0 for all profiles when taper > 0."""
        weight = taper_function(0.0, profile, taper_fraction=0.2)
        assert weight == pytest.approx(0.0, abs=1e-14)

    @pytest.mark.parametrize("profile", list(TaperProfile))
    def test_edge_end_approaches_zero(self, profile: TaperProfile) -> None:
        """xi=1.0 (end edge) gives 0.0 for all profiles when taper > 0."""
        weight = taper_function(1.0, profile, taper_fraction=0.2)
        assert weight == pytest.approx(0.0, abs=1e-14)

    # --- Zero taper fraction always returns 1.0 ---

    @pytest.mark.parametrize("xi", [0.0, 0.1, 0.5, 0.9, 1.0])
    @pytest.mark.parametrize("profile", list(TaperProfile))
    def test_zero_taper_fraction_always_one(
        self, profile: TaperProfile, xi: float
    ) -> None:
        """taper_fraction=0 disables tapering: weight is always 1.0."""
        weight = taper_function(xi, profile, taper_fraction=0.0)
        assert weight == pytest.approx(1.0)

    # --- Known values for each profile ---

    def test_cosine_at_taper_midpoint(self) -> None:
        """Cosine at t=0.5 (xi=0.1, tw=0.2): 0.5*(1-cos(pi*0.5)) = 0.5."""
        weight = taper_function(0.1, TaperProfile.COSINE, taper_fraction=0.2)
        expected = 0.5 * (1.0 - math.cos(math.pi * 0.5))
        assert weight == pytest.approx(expected, rel=1e-12)

    def test_cosine_at_three_quarter_taper(self) -> None:
        """Cosine at t=0.75 (xi=0.15, tw=0.2): 0.5*(1-cos(pi*0.75))."""
        weight = taper_function(0.15, TaperProfile.COSINE, taper_fraction=0.2)
        expected = 0.5 * (1.0 - math.cos(math.pi * 0.75))
        assert weight == pytest.approx(expected, rel=1e-12)

    def test_linear_proportional_to_position(self) -> None:
        """Linear taper: weight = t = edge_dist / taper_fraction."""
        # xi=0.1, tw=0.2 -> edge_dist=0.1, t=0.5
        weight = taper_function(0.1, TaperProfile.LINEAR, taper_fraction=0.2)
        assert weight == pytest.approx(0.5, rel=1e-12)

    def test_linear_three_quarter(self) -> None:
        """Linear at t=0.75 (xi=0.15, tw=0.2): weight=0.75."""
        weight = taper_function(0.15, TaperProfile.LINEAR, taper_fraction=0.2)
        assert weight == pytest.approx(0.75, rel=1e-12)

    def test_elliptical_at_taper_midpoint(self) -> None:
        """Elliptical at t=0.5: sqrt(1-(1-0.5)^2) = sqrt(0.75)."""
        weight = taper_function(0.1, TaperProfile.ELLIPTICAL, taper_fraction=0.2)
        expected = math.sqrt(1.0 - (1.0 - 0.5) ** 2)
        assert weight == pytest.approx(expected, rel=1e-12)

    def test_elliptical_three_quarter(self) -> None:
        """Elliptical at t=0.75 (xi=0.15, tw=0.2): sqrt(1-(0.25)^2)."""
        weight = taper_function(0.15, TaperProfile.ELLIPTICAL, taper_fraction=0.2)
        expected = math.sqrt(1.0 - (1.0 - 0.75) ** 2)
        assert weight == pytest.approx(expected, rel=1e-12)

    # --- Symmetry ---

    @pytest.mark.parametrize("xi", [0.05, 0.1, 0.15, 0.18])
    @pytest.mark.parametrize("profile", list(TaperProfile))
    def test_symmetry_about_center(
        self, profile: TaperProfile, xi: float
    ) -> None:
        """taper_function is symmetric: f(xi) == f(1-xi) for all profiles."""
        w_left = taper_function(xi, profile, taper_fraction=0.2)
        w_right = taper_function(1.0 - xi, profile, taper_fraction=0.2)
        assert w_left == pytest.approx(w_right, rel=1e-12)

    # --- At the taper boundary ---

    @pytest.mark.parametrize("profile", list(TaperProfile))
    def test_at_taper_boundary_returns_one(self, profile: TaperProfile) -> None:
        """xi=0.2 with tw=0.2: edge_dist exactly equals taper_fraction -> 1.0."""
        weight = taper_function(0.2, profile, taper_fraction=0.2)
        assert weight == pytest.approx(1.0)

    # --- Weight is bounded in [0, 1] ---

    @pytest.mark.parametrize("xi", [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 0.9, 1.0])
    @pytest.mark.parametrize("profile", list(TaperProfile))
    def test_weight_in_unit_interval(
        self, profile: TaperProfile, xi: float
    ) -> None:
        """All weights are in [0, 1]."""
        weight = taper_function(xi, profile, taper_fraction=0.3)
        assert 0.0 <= weight <= 1.0 + 1e-12


# ---------------------------------------------------------------------------
# 4. subdivide_fault
# ---------------------------------------------------------------------------


class TestSubdivideFault:
    """subdivide_fault: identity case, count, area, depths, and geometry."""

    def test_1x1_returns_original_fault(self) -> None:
        """1x1 subdivision returns a list containing exactly the original fault."""
        fault = make_fault()
        result = subdivide_fault(fault, n_strike=1, n_dip=1)
        assert len(result) == 1
        assert result[0] is fault

    def test_nxm_returns_correct_count(self) -> None:
        """NxM subdivision returns N*M subfaults."""
        fault = make_fault()
        for n_s in (2, 3, 5):
            for n_d in (1, 2, 4):
                subs = subdivide_fault(fault, n_strike=n_s, n_dip=n_d)
                assert len(subs) == n_s * n_d, (
                    f"Expected {n_s * n_d} subfaults for {n_s}x{n_d}, "
                    f"got {len(subs)}"
                )

    def test_area_conservation_3x2(self) -> None:
        """Total subfault area approximately equals original fault area."""
        fault = make_fault()
        subs = subdivide_fault(fault, n_strike=3, n_dip=2)
        orig_area = fault.length * fault.width
        sub_area = sum(s.length * s.width for s in subs)
        assert sub_area == pytest.approx(orig_area, rel=1e-6)

    def test_area_conservation_5x4(self) -> None:
        """Area conservation holds for a finer subdivision (5x4)."""
        fault = make_fault()
        subs = subdivide_fault(fault, n_strike=5, n_dip=4)
        orig_area = fault.length * fault.width
        sub_area = sum(s.length * s.width for s in subs)
        assert sub_area == pytest.approx(orig_area, rel=1e-6)

    def test_depth_ranges_tile_original(self) -> None:
        """Dip-row depth ranges tile the original [top, bottom] range."""
        fault = make_fault(top_depth=10.0, bottom_depth=20.0)
        n_dip = 4
        subs = subdivide_fault(fault, n_strike=3, n_dip=n_dip)
        sub_depth_range = (fault.bottom_depth - fault.top_depth) / n_dip
        # Check all unique (top, bottom) pairs
        unique_depths = sorted({(s.top_depth, s.bottom_depth) for s in subs})
        assert len(unique_depths) == n_dip
        for idx, (top, bottom) in enumerate(unique_depths):
            expected_top = fault.top_depth + idx * sub_depth_range
            expected_bot = expected_top + sub_depth_range
            assert top == pytest.approx(expected_top, rel=1e-10)
            assert bottom == pytest.approx(expected_bot, rel=1e-10)

    def test_top_depth_matches_original_top_for_first_row(self) -> None:
        """Shallowest subfaults share the original top depth."""
        fault = make_fault(top_depth=5.0, bottom_depth=15.0)
        subs = subdivide_fault(fault, n_strike=4, n_dip=3)
        first_row = subs[:4]  # dip index j=0
        for s in first_row:
            assert s.top_depth == pytest.approx(5.0, rel=1e-10)

    def test_bottom_depth_matches_original_bottom_for_last_row(self) -> None:
        """Deepest subfaults share the original bottom depth."""
        fault = make_fault(top_depth=5.0, bottom_depth=15.0)
        subs = subdivide_fault(fault, n_strike=4, n_dip=3)
        last_row = subs[-4:]  # dip index j=2
        for s in last_row:
            assert s.bottom_depth == pytest.approx(15.0, rel=1e-10)

    def test_slip_and_kode_preserved(self) -> None:
        """Slip components, kode, and dip are copied unchanged to subfaults."""
        fault = make_fault(slip_1=2.5, slip_2=1.3, dip=60.0, kode=Kode.STANDARD)
        subs = subdivide_fault(fault, n_strike=3, n_dip=2)
        for s in subs:
            assert s.slip_1 == pytest.approx(fault.slip_1)
            assert s.slip_2 == pytest.approx(fault.slip_2)
            assert s.kode == fault.kode
            assert s.dip == fault.dip

    def test_subfault_labels_carry_index(self) -> None:
        """Each subfault label encodes a sub-index derived from the original label."""
        fault = make_fault(label="myfault")
        subs = subdivide_fault(fault, n_strike=2, n_dip=2)
        for i, s in enumerate(subs, start=1):
            assert f"sub{i}" in s.label

    def test_unlabeled_fault_subfault_label_contains_sub(self) -> None:
        """Subfaults of an unlabeled fault still get a sub-index label."""
        fault = make_fault(label="")
        subs = subdivide_fault(fault, n_strike=2, n_dip=1)
        for s in subs:
            assert "sub" in s.label


# ---------------------------------------------------------------------------
# 5. apply_taper
# ---------------------------------------------------------------------------


class TestApplyTaper:
    """apply_taper: slip reduction, center vs. edge, zero-fraction passthrough."""

    def _make_subs_and_spec(
        self,
        n_s: int = 5,
        n_d: int = 3,
        tw: float = 0.2,
        profile: TaperProfile = TaperProfile.COSINE,
    ) -> tuple[list[FaultElement], list[FaultElement], TaperSpec]:
        fault = make_fault(slip_1=1.0, slip_2=0.5)
        spec = TaperSpec(
            profile=profile,
            n_along_strike=n_s,
            n_down_dip=n_d,
            taper_width_fraction=tw,
        )
        subs = subdivide_fault(fault, n_s, n_d)
        tapered = apply_taper(subs, spec)
        return subs, tapered, spec

    def test_center_subfault_has_full_slip(self) -> None:
        """The center subfault (j=1, i=2 for 5x3) must have weight 1.0."""
        subs, tapered, _ = self._make_subs_and_spec(n_s=5, n_d=3, tw=0.2)
        center_idx = 1 * 5 + 2  # j=1, i=2
        center = tapered[center_idx]
        assert center.slip_1 == pytest.approx(1.0, rel=1e-12)
        assert center.slip_2 == pytest.approx(0.5, rel=1e-12)

    def test_corner_subfault_has_reduced_slip(self) -> None:
        """The corner subfault (j=0, i=0) has slip reduced below the original."""
        subs, tapered, _ = self._make_subs_and_spec(n_s=5, n_d=3, tw=0.2)
        corner = tapered[0]
        assert corner.slip_1 < 1.0
        assert corner.slip_2 < 0.5

    def test_both_slip_components_scaled_equally(self) -> None:
        """slip_1 and slip_2 are both scaled by the same taper weight."""
        subs, tapered, _ = self._make_subs_and_spec(n_s=5, n_d=3, tw=0.2)
        for orig, t in zip(subs, tapered):
            if orig.slip_1 != 0.0:
                ratio = t.slip_1 / orig.slip_1
                if orig.slip_2 != 0.0:
                    assert t.slip_2 / orig.slip_2 == pytest.approx(ratio, rel=1e-12)

    def test_zero_taper_fraction_leaves_slip_unchanged(self) -> None:
        """taper_width_fraction=0 must not alter any slip values."""
        fault = make_fault(slip_1=2.0, slip_2=0.8)
        spec = TaperSpec(
            n_along_strike=4, n_down_dip=2, taper_width_fraction=0.0
        )
        subs = subdivide_fault(fault, 4, 2)
        tapered = apply_taper(subs, spec)
        for s, t in zip(subs, tapered):
            assert t.slip_1 == pytest.approx(s.slip_1, rel=1e-14)
            assert t.slip_2 == pytest.approx(s.slip_2, rel=1e-14)

    def test_slip_never_exceeds_original(self) -> None:
        """Tapered slip is always <= original subfault slip."""
        subs, tapered, _ = self._make_subs_and_spec(n_s=5, n_d=3, tw=0.3)
        for orig, t in zip(subs, tapered):
            assert t.slip_1 <= orig.slip_1 + 1e-14
            assert t.slip_2 <= orig.slip_2 + 1e-14

    def test_geometry_unchanged_by_taper(self) -> None:
        """apply_taper preserves x/y endpoints, depths, dip, kode, and label."""
        subs, tapered, _ = self._make_subs_and_spec(n_s=3, n_d=2, tw=0.2)
        for orig, t in zip(subs, tapered):
            assert t.x_start == pytest.approx(orig.x_start)
            assert t.y_start == pytest.approx(orig.y_start)
            assert t.x_fin == pytest.approx(orig.x_fin)
            assert t.y_fin == pytest.approx(orig.y_fin)
            assert t.top_depth == pytest.approx(orig.top_depth)
            assert t.bottom_depth == pytest.approx(orig.bottom_depth)
            assert t.dip == orig.dip
            assert t.kode == orig.kode
            assert t.label == orig.label

    def test_edge_slip_less_than_adjacent(self) -> None:
        """Edge subfaults have smaller slip than their interior neighbors."""
        subs, tapered, _ = self._make_subs_and_spec(n_s=5, n_d=3, tw=0.2)
        # Compare j=0 row: i=0 (edge) vs i=2 (center)
        row0_edge = tapered[0]       # j=0, i=0
        row0_center = tapered[2]     # j=0, i=2
        assert row0_edge.slip_1 < row0_center.slip_1

    def test_correct_corner_weight_cosine_5x3(self) -> None:
        """Verify exact corner weight for n_s=5, n_d=3, tw=0.2, cosine profile.

        xi_s = 0.5/5 = 0.1, t_s = 0.5, w_s = 0.5*(1-cos(pi*0.5)) = 0.5
        xi_d = 0.5/3 = 0.1667, t_d = 0.8333, w_d = 0.5*(1-cos(pi*0.8333)) ~ 0.9330
        weight = w_s * w_d ~ 0.4665
        """
        _, tapered, _ = self._make_subs_and_spec(n_s=5, n_d=3, tw=0.2)
        corner = tapered[0]  # j=0, i=0
        xi_s = 0.5 / 5
        xi_d = 0.5 / 3
        t_s = xi_s / 0.2
        t_d = xi_d / 0.2
        w_s = 0.5 * (1.0 - math.cos(math.pi * t_s))
        w_d = 0.5 * (1.0 - math.cos(math.pi * t_d))
        expected = w_s * w_d
        assert corner.slip_1 == pytest.approx(expected, rel=1e-10)


# ---------------------------------------------------------------------------
# 6. subdivide_and_taper (combined)
# ---------------------------------------------------------------------------


class TestSubdivideAndTaper:
    """subdivide_and_taper: composition correctness and moment reduction."""

    def test_returns_n_strike_times_n_dip_subfaults(self) -> None:
        """Result count equals n_along_strike * n_down_dip."""
        fault = make_fault()
        spec = TaperSpec(n_along_strike=4, n_down_dip=2, taper_width_fraction=0.2)
        result = subdivide_and_taper(fault, spec)
        assert len(result) == 4 * 2

    def test_1x1_returns_single_tapered_fault(self) -> None:
        """1x1 subdivision with taper returns exactly one element."""
        fault = make_fault()
        spec = TaperSpec(n_along_strike=1, n_down_dip=1, taper_width_fraction=0.2)
        result = subdivide_and_taper(fault, spec)
        assert len(result) == 1

    def test_tapered_seismic_moment_less_than_untapered(self) -> None:
        """Tapered total moment (sum of slip*area) < untapered moment."""
        fault = make_fault(slip_1=2.0, slip_2=0.0)
        spec = TaperSpec(
            profile=TaperProfile.COSINE,
            n_along_strike=4,
            n_down_dip=2,
            taper_width_fraction=0.2,
        )
        tapered_subs = subdivide_and_taper(fault, spec)
        untapered_subs = subdivide_fault(fault, spec.n_along_strike, spec.n_down_dip)

        tapered_moment = sum(s.slip_1 * s.length * s.width for s in tapered_subs)
        untapered_moment = sum(s.slip_1 * s.length * s.width for s in untapered_subs)

        assert tapered_moment < untapered_moment

    def test_zero_taper_moment_equals_original(self) -> None:
        """With taper_width_fraction=0, moment is conserved vs untapered."""
        fault = make_fault(slip_1=3.0, slip_2=1.0)
        spec = TaperSpec(
            n_along_strike=3, n_down_dip=2, taper_width_fraction=0.0
        )
        tapered_subs = subdivide_and_taper(fault, spec)
        untapered_subs = subdivide_fault(fault, 3, 2)

        def moment(subs: list[FaultElement]) -> float:
            return sum(s.slip_1 * s.length * s.width for s in subs)

        assert moment(tapered_subs) == pytest.approx(moment(untapered_subs), rel=1e-10)

    @pytest.mark.parametrize("profile", list(TaperProfile))
    def test_all_profiles_produce_valid_results(self, profile: TaperProfile) -> None:
        """All three taper profiles run without error and return correct count."""
        fault = make_fault()
        spec = TaperSpec(
            profile=profile, n_along_strike=3, n_down_dip=2, taper_width_fraction=0.2
        )
        result = subdivide_and_taper(fault, spec)
        assert len(result) == 6
        for s in result:
            assert math.isfinite(s.slip_1)
            assert math.isfinite(s.slip_2)

    def test_slip_values_are_non_negative(self) -> None:
        """After tapering a fault with positive slip, all slips are >= 0."""
        fault = make_fault(slip_1=1.0, slip_2=0.5)
        spec = TaperSpec(n_along_strike=5, n_down_dip=3, taper_width_fraction=0.4)
        result = subdivide_and_taper(fault, spec)
        for s in result:
            assert s.slip_1 >= 0.0
            assert s.slip_2 >= 0.0


# ---------------------------------------------------------------------------
# 7. compute_grid with taper parameter
# ---------------------------------------------------------------------------


class TestComputeGridTaper:
    """compute_grid: regression for taper=None; different CFS with taper."""

    @pytest.fixture(scope="class")
    def model(self):
        """Load the simplest_receiver model once per class."""
        from opencoulomb.io.inp_parser import read_inp

        return read_inp(SIMPLEST_RECEIVER)

    @pytest.fixture(scope="class")
    def result_no_taper(self, model):
        """CFS result with taper=None (baseline)."""
        from opencoulomb.core.pipeline import compute_grid

        return compute_grid(model)

    def test_taper_none_is_regression_baseline(self, model, result_no_taper) -> None:
        """compute_grid(taper=None) produces the same result as the no-taper call."""
        from opencoulomb.core.pipeline import compute_grid

        result_explicit_none = compute_grid(model, taper=None)
        np.testing.assert_array_equal(result_no_taper.cfs, result_explicit_none.cfs)

    def test_taper_produces_different_cfs(self, model, result_no_taper) -> None:
        """A non-trivial taper spec changes the CFS values compared to no taper."""
        from opencoulomb.core.pipeline import compute_grid

        spec = TaperSpec(
            profile=TaperProfile.COSINE,
            n_along_strike=4,
            n_down_dip=2,
            taper_width_fraction=0.3,
        )
        result_taper = compute_grid(model, taper=spec)
        assert not np.allclose(result_no_taper.cfs, result_taper.cfs), (
            "Taper should alter CFS values but got identical arrays"
        )

    def test_taper_result_has_no_nan(self, model) -> None:
        """CFS values with tapering are all finite (no NaN or Inf)."""
        from opencoulomb.core.pipeline import compute_grid

        spec = TaperSpec(
            profile=TaperProfile.LINEAR,
            n_along_strike=3,
            n_down_dip=2,
            taper_width_fraction=0.2,
        )
        result = compute_grid(model, taper=spec)
        assert np.all(np.isfinite(result.cfs)), "Expected all-finite CFS with taper"

    def test_taper_result_grid_shape_preserved(self, model, result_no_taper) -> None:
        """Tapering does not alter the output grid shape."""
        from opencoulomb.core.pipeline import compute_grid

        spec = TaperSpec(n_along_strike=3, n_down_dip=2, taper_width_fraction=0.2)
        result_taper = compute_grid(model, taper=spec)
        assert result_taper.cfs.shape == result_no_taper.cfs.shape
        assert result_taper.grid_shape == result_no_taper.grid_shape

    def test_1x1_taper_matches_no_taper(self, model, result_no_taper) -> None:
        """1x1 taper spec (no subdivision, trivial taper) is identical to baseline."""
        from opencoulomb.core.pipeline import compute_grid

        spec = TaperSpec(
            n_along_strike=1, n_down_dip=1, taper_width_fraction=0.2
        )
        result_1x1 = compute_grid(model, taper=spec)
        np.testing.assert_allclose(result_no_taper.cfs, result_1x1.cfs, rtol=1e-12)
