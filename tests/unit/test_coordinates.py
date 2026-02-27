"""Unit tests for opencoulomb.core.coordinates.

Covers:
- direction_cosines: orthogonality, normalization, edge cases
- rotation_matrix: orthogonality (R @ R.T = I), determinant = 1
- geo_to_fault + fault_to_geo_displacement: roundtrip accuracy
- compute_fault_geometry: known geometries (E-W, N-S, diagonal)
- Hypothesis property-based tests for rotation matrix orthogonality
"""

from __future__ import annotations

import math
from typing import ClassVar

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from opencoulomb.core.coordinates import (
    compute_fault_geometry,
    direction_cosines,
    fault_to_geo_displacement,
    geo_to_fault,
    rotation_matrix,
    strike_dip_to_normal,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deg(deg: float) -> float:
    """Convert degrees to radians."""
    return math.radians(deg)


# ---------------------------------------------------------------------------
# direction_cosines
# ---------------------------------------------------------------------------


class TestDirectionCosines:
    """Test direction cosine vectors for various fault orientations."""

    ORIENTATIONS: ClassVar[list[tuple[float, float]]] = [
        (0.0, 45.0),     # N-striking, 45-dip
        (90.0, 45.0),    # E-striking, 45-dip
        (180.0, 45.0),   # S-striking
        (270.0, 45.0),   # W-striking
        (0.0, 90.0),     # vertical
        (0.0, 1.0),      # near-horizontal
        (45.0, 60.0),    # NE-striking
        (135.0, 30.0),   # SE-striking
    ]

    @pytest.mark.parametrize("strike_deg, dip_deg", ORIENTATIONS)
    def test_unit_vectors(self, strike_deg: float, dip_deg: float) -> None:
        """Each direction cosine vector must be a unit vector."""
        ls, lu, ln = direction_cosines(_deg(strike_deg), _deg(dip_deg))
        assert np.linalg.norm(ls) == pytest.approx(1.0, abs=1e-14)
        assert np.linalg.norm(lu) == pytest.approx(1.0, abs=1e-14)
        assert np.linalg.norm(ln) == pytest.approx(1.0, abs=1e-14)

    @pytest.mark.parametrize("strike_deg, dip_deg", ORIENTATIONS)
    def test_orthogonality(self, strike_deg: float, dip_deg: float) -> None:
        """Direction cosine vectors must be mutually orthogonal."""
        ls, lu, ln = direction_cosines(_deg(strike_deg), _deg(dip_deg))
        assert np.dot(ls, lu) == pytest.approx(0.0, abs=1e-14)
        assert np.dot(ls, ln) == pytest.approx(0.0, abs=1e-14)
        assert np.dot(lu, ln) == pytest.approx(0.0, abs=1e-14)

    def test_strike_zero_dip_45(self) -> None:
        """Strike=0 (North), dip=45: known analytical result."""
        ls, lu, ln = direction_cosines(_deg(0.0), _deg(45.0))
        c45 = math.cos(math.radians(45.0))
        s45 = math.sin(math.radians(45.0))
        # l_strike should be [sin(0), cos(0), 0] = [0, 1, 0] (pointing North)
        np.testing.assert_allclose(ls, [0.0, 1.0, 0.0], atol=1e-14)
        # l_updip should be [-cos(0)*cos(45), sin(0)*cos(45), sin(45)] = [-c45, 0, s45]
        np.testing.assert_allclose(lu, [-c45, 0.0, s45], atol=1e-14)
        # l_normal should be [cos(0)*sin(45), -sin(0)*sin(45), cos(45)] = [s45, 0, c45]
        np.testing.assert_allclose(ln, [s45, 0.0, c45], atol=1e-14)

    def test_vertical_fault_dip_90(self) -> None:
        """Vertical fault (dip=90): updip = [-cos(s), sin(s), 0], normal = [cos(s)*1, ...]."""
        ls, lu, ln = direction_cosines(_deg(45.0), _deg(90.0))
        # dip=90: cos(dip)=0, sin(dip)=1
        s = math.radians(45.0)
        ss, cs = math.sin(s), math.cos(s)
        np.testing.assert_allclose(ls, [ss, cs, 0.0], atol=1e-14)
        # l_updip = [-cs*0, ss*0, 1] = [0, 0, 1]
        np.testing.assert_allclose(lu, [0.0, 0.0, 1.0], atol=1e-14)
        # l_normal = [cs*1, -ss*1, 0] = [cs, -ss, 0]
        np.testing.assert_allclose(ln, [cs, -ss, 0.0], atol=1e-14)

    def test_near_horizontal_fault(self) -> None:
        """Near-horizontal fault (dip~0): normal points nearly upward."""
        _ls, _lu, ln = direction_cosines(_deg(0.0), _deg(0.01))
        # Normal should be nearly [0, 0, 1] for very shallow dip
        assert ln[2] == pytest.approx(1.0, abs=1e-4)
        assert abs(ln[0]) < 1e-3
        assert abs(ln[1]) < 1e-3

    def test_right_hand_rule(self) -> None:
        """l_normal = l_strike x l_updip (right-hand rule)."""
        ls, lu, ln = direction_cosines(_deg(30.0), _deg(60.0))
        cross = np.cross(ls, lu)
        np.testing.assert_allclose(cross, ln, atol=1e-14)


# ---------------------------------------------------------------------------
# rotation_matrix
# ---------------------------------------------------------------------------


class TestRotationMatrix:
    """Test rotation matrix properties."""

    ORIENTATIONS: ClassVar[list[tuple[float, float]]] = [
        (0.0, 45.0),
        (90.0, 90.0),
        (45.0, 30.0),
        (180.0, 60.0),
        (270.0, 15.0),
        (0.0, 1.0),
    ]

    @pytest.mark.parametrize("strike_deg, dip_deg", ORIENTATIONS)
    def test_orthogonality(self, strike_deg: float, dip_deg: float) -> None:
        """R @ R.T = I for any rotation matrix."""
        R = rotation_matrix(_deg(strike_deg), _deg(dip_deg))
        product = R @ R.T
        np.testing.assert_allclose(product, np.eye(3), atol=1e-14)

    @pytest.mark.parametrize("strike_deg, dip_deg", ORIENTATIONS)
    def test_determinant_positive_one(self, strike_deg: float, dip_deg: float) -> None:
        """det(R) = +1 (proper rotation, no reflection)."""
        R = rotation_matrix(_deg(strike_deg), _deg(dip_deg))
        assert np.linalg.det(R) == pytest.approx(1.0, abs=1e-14)

    @pytest.mark.parametrize("strike_deg, dip_deg", ORIENTATIONS)
    def test_transpose_equals_inverse(self, strike_deg: float, dip_deg: float) -> None:
        """R.T @ R = I (transpose is inverse for orthogonal matrices)."""
        R = rotation_matrix(_deg(strike_deg), _deg(dip_deg))
        product = R.T @ R
        np.testing.assert_allclose(product, np.eye(3), atol=1e-14)

    def test_rows_are_direction_cosines(self) -> None:
        """Rotation matrix rows match direction_cosines output."""
        strike, dip = _deg(30.0), _deg(60.0)
        R = rotation_matrix(strike, dip)
        ls, lu, ln = direction_cosines(strike, dip)
        np.testing.assert_allclose(R[0], ls, atol=1e-14)
        np.testing.assert_allclose(R[1], lu, atol=1e-14)
        np.testing.assert_allclose(R[2], ln, atol=1e-14)


# ---------------------------------------------------------------------------
# strike_dip_to_normal
# ---------------------------------------------------------------------------


class TestStrikeDipToNormal:
    """Test the normal vector computation shortcut."""

    def test_matches_direction_cosines(self) -> None:
        """Must return same as third output of direction_cosines."""
        strike, dip = _deg(120.0), _deg(50.0)
        _, _, ln_expected = direction_cosines(strike, dip)
        ln = strike_dip_to_normal(strike, dip)
        np.testing.assert_allclose(ln, ln_expected, atol=1e-14)


# ---------------------------------------------------------------------------
# geo_to_fault + fault_to_geo_displacement roundtrip
# ---------------------------------------------------------------------------


class TestCoordinateRoundtrip:
    """Test forward and inverse transforms for consistency."""

    ORIENTATIONS: ClassVar[list[tuple[float, float]]] = [
        (0.0, 45.0),
        (90.0, 90.0),
        (45.0, 30.0),
        (180.0, 60.0),
        (270.0, 15.0),
    ]

    @pytest.mark.parametrize("strike_deg, dip_deg", ORIENTATIONS)
    def test_displacement_roundtrip(self, strike_deg: float, dip_deg: float) -> None:
        """fault_to_geo(R @ v) recovers v for displacement vectors."""
        strike = _deg(strike_deg)
        dip = _deg(dip_deg)

        # Random displacement vector in geographic coords
        rng = np.random.default_rng(42)
        ux_geo = rng.standard_normal(10)
        uy_geo = rng.standard_normal(10)
        uz_geo = rng.standard_normal(10)

        # geo -> fault-local
        R = rotation_matrix(strike, dip)
        ux_local = R[0, 0] * ux_geo + R[0, 1] * uy_geo + R[0, 2] * uz_geo
        uy_local = R[1, 0] * ux_geo + R[1, 1] * uy_geo + R[1, 2] * uz_geo
        uz_local = R[2, 0] * ux_geo + R[2, 1] * uy_geo + R[2, 2] * uz_geo

        # fault-local -> geo
        ux_back, uy_back, uz_back = fault_to_geo_displacement(
            ux_local, uy_local, uz_local, strike, dip,
        )

        np.testing.assert_allclose(ux_back, ux_geo, atol=1e-12)
        np.testing.assert_allclose(uy_back, uy_geo, atol=1e-12)
        np.testing.assert_allclose(uz_back, uz_geo, atol=1e-12)

    def test_identity_at_origin(self) -> None:
        """Point at the fault reference point transforms to local origin."""
        strike, dip = _deg(45.0), _deg(60.0)
        fault_x, fault_y, fault_depth = 5.0, 10.0, 3.0

        x_geo = np.array([fault_x])
        y_geo = np.array([fault_y])
        z_geo = np.array([-fault_depth])

        xl, yl, zl = geo_to_fault(
            x_geo, y_geo, z_geo,
            fault_x, fault_y, fault_depth,
            strike, dip,
        )

        np.testing.assert_allclose(xl, 0.0, atol=1e-14)
        np.testing.assert_allclose(yl, 0.0, atol=1e-14)
        np.testing.assert_allclose(zl, 0.0, atol=1e-14)

    def test_geo_to_fault_vectorized(self) -> None:
        """geo_to_fault handles multiple observation points."""
        strike, dip = _deg(90.0), _deg(45.0)
        x_geo = np.array([1.0, 2.0, 3.0])
        y_geo = np.array([4.0, 5.0, 6.0])
        z_geo = np.array([-1.0, -2.0, -3.0])

        xl, yl, zl = geo_to_fault(
            x_geo, y_geo, z_geo, 0.0, 0.0, 5.0, strike, dip,
        )

        assert xl.shape == (3,)
        assert yl.shape == (3,)
        assert zl.shape == (3,)


# ---------------------------------------------------------------------------
# compute_fault_geometry
# ---------------------------------------------------------------------------


class TestComputeFaultGeometry:
    """Test derived fault geometry computation."""

    def test_east_west_fault(self) -> None:
        """E-W fault: strike = 90 degrees."""
        geom = compute_fault_geometry(
            x_start=-10.0, y_start=0.0,
            x_fin=10.0, y_fin=0.0,
            dip_deg=45.0, top_depth=0.0, bottom_depth=10.0,
        )
        assert geom["strike_rad"] == pytest.approx(_deg(90.0), abs=1e-10)
        assert geom["length"] == pytest.approx(20.0, abs=1e-10)
        assert geom["dip_rad"] == pytest.approx(_deg(45.0), abs=1e-10)

    def test_north_south_fault(self) -> None:
        """N-S fault: strike = 0 degrees."""
        geom = compute_fault_geometry(
            x_start=0.0, y_start=-10.0,
            x_fin=0.0, y_fin=10.0,
            dip_deg=60.0, top_depth=0.0, bottom_depth=10.0,
        )
        assert geom["strike_rad"] == pytest.approx(0.0, abs=1e-10)
        assert geom["length"] == pytest.approx(20.0, abs=1e-10)

    def test_symmetric_half_dimensions(self) -> None:
        """al1 + al2 = 0 and aw1 + aw2 = 0 (symmetric about center)."""
        geom = compute_fault_geometry(
            x_start=0.0, y_start=0.0,
            x_fin=10.0, y_fin=0.0,
            dip_deg=45.0, top_depth=5.0, bottom_depth=15.0,
        )
        assert geom["al1"] + geom["al2"] == pytest.approx(0.0, abs=1e-10)
        assert geom["aw1"] + geom["aw2"] == pytest.approx(0.0, abs=1e-10)
        assert geom["al2"] == pytest.approx(geom["length"] / 2.0, abs=1e-10)

    def test_width_vertical_fault(self) -> None:
        """Vertical fault (dip=90): width = bottom - top depth."""
        geom = compute_fault_geometry(
            x_start=-5.0, y_start=0.0,
            x_fin=5.0, y_fin=0.0,
            dip_deg=90.0, top_depth=2.0, bottom_depth=12.0,
        )
        assert geom["width"] == pytest.approx(10.0, abs=1e-10)

    def test_width_dipping_fault(self) -> None:
        """Dipping fault: width = depth_range / sin(dip)."""
        dip = 30.0
        top, bot = 5.0, 15.0
        geom = compute_fault_geometry(
            x_start=0.0, y_start=0.0,
            x_fin=20.0, y_fin=0.0,
            dip_deg=dip, top_depth=top, bottom_depth=bot,
        )
        expected_width = (bot - top) / math.sin(math.radians(dip))
        assert geom["width"] == pytest.approx(expected_width, abs=1e-10)

    def test_center_depth(self) -> None:
        """Center depth is the average of top and bottom."""
        geom = compute_fault_geometry(
            x_start=0.0, y_start=0.0,
            x_fin=10.0, y_fin=0.0,
            dip_deg=45.0, top_depth=3.0, bottom_depth=13.0,
        )
        assert geom["center_depth"] == pytest.approx(8.0, abs=1e-10)
        assert geom["depth"] == pytest.approx(8.0, abs=1e-10)

    def test_diagonal_fault(self) -> None:
        """45-degree diagonal fault: strike = atan2(dx, dy) = 45 degrees."""
        d = 10.0 / math.sqrt(2.0)
        geom = compute_fault_geometry(
            x_start=0.0, y_start=0.0,
            x_fin=d, y_fin=d,
            dip_deg=45.0, top_depth=0.0, bottom_depth=10.0,
        )
        assert geom["strike_rad"] == pytest.approx(_deg(45.0), abs=1e-10)
        assert geom["length"] == pytest.approx(10.0, abs=1e-10)


# ---------------------------------------------------------------------------
# Hypothesis property-based tests
# ---------------------------------------------------------------------------


class TestCoordinatesHypothesis:
    """Property-based tests using hypothesis."""

    @given(
        strike_deg=st.floats(min_value=0.0, max_value=360.0, allow_nan=False),
        dip_deg=st.floats(min_value=0.1, max_value=89.9, allow_nan=False),
    )
    @settings(max_examples=200)
    def test_rotation_matrix_orthogonal(
        self, strike_deg: float, dip_deg: float
    ) -> None:
        """Rotation matrix is orthogonal for any valid strike/dip."""
        R = rotation_matrix(_deg(strike_deg), _deg(dip_deg))
        product = R @ R.T
        np.testing.assert_allclose(product, np.eye(3), atol=1e-12)

    @given(
        strike_deg=st.floats(min_value=0.0, max_value=360.0, allow_nan=False),
        dip_deg=st.floats(min_value=0.1, max_value=89.9, allow_nan=False),
    )
    @settings(max_examples=200)
    def test_rotation_matrix_det_one(
        self, strike_deg: float, dip_deg: float
    ) -> None:
        """Determinant of rotation matrix is +1 for any valid strike/dip."""
        R = rotation_matrix(_deg(strike_deg), _deg(dip_deg))
        assert np.linalg.det(R) == pytest.approx(1.0, abs=1e-12)

    @given(
        strike_deg=st.floats(min_value=0.0, max_value=360.0, allow_nan=False),
        dip_deg=st.floats(min_value=0.1, max_value=89.9, allow_nan=False),
    )
    @settings(max_examples=200)
    def test_direction_cosines_orthonormal(
        self, strike_deg: float, dip_deg: float
    ) -> None:
        """Direction cosine vectors form an orthonormal basis."""
        ls, lu, ln = direction_cosines(_deg(strike_deg), _deg(dip_deg))
        # Unit length
        assert np.linalg.norm(ls) == pytest.approx(1.0, abs=1e-12)
        assert np.linalg.norm(lu) == pytest.approx(1.0, abs=1e-12)
        assert np.linalg.norm(ln) == pytest.approx(1.0, abs=1e-12)
        # Orthogonal
        assert np.dot(ls, lu) == pytest.approx(0.0, abs=1e-12)
        assert np.dot(ls, ln) == pytest.approx(0.0, abs=1e-12)
        assert np.dot(lu, ln) == pytest.approx(0.0, abs=1e-12)

    @given(
        strike_deg=st.floats(min_value=0.0, max_value=360.0, allow_nan=False),
        dip_deg=st.floats(min_value=0.1, max_value=89.9, allow_nan=False),
        vx=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False),
        vy=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False),
        vz=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False),
    )
    @settings(max_examples=200)
    def test_displacement_roundtrip_hypothesis(
        self,
        strike_deg: float,
        dip_deg: float,
        vx: float,
        vy: float,
        vz: float,
    ) -> None:
        """Forward + inverse displacement rotation is identity."""
        strike = _deg(strike_deg)
        dip = _deg(dip_deg)
        R = rotation_matrix(strike, dip)

        v_geo = np.array([vx, vy, vz])
        v_local = R @ v_geo

        ux_back, uy_back, uz_back = fault_to_geo_displacement(
            np.array([v_local[0]]),
            np.array([v_local[1]]),
            np.array([v_local[2]]),
            strike,
            dip,
        )

        np.testing.assert_allclose(ux_back[0], vx, atol=1e-10)
        np.testing.assert_allclose(uy_back[0], vy, atol=1e-10)
        np.testing.assert_allclose(uz_back[0], vz, atol=1e-10)
