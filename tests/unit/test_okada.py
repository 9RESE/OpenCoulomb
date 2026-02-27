"""Unit tests for opencoulomb.core.okada (DC3D and DC3D0).

Covers:
- Reference values from Okada (1992) Table 2
- Superposition linearity
- Symmetry properties for strike-slip on vertical faults
- No NaN/Inf for random observation points
- Performance: 10k points under time budget
- DC3D0 point source finite values
- DC3D0 consistency with small DC3D faults
"""

from __future__ import annotations

import time
from typing import ClassVar

import numpy as np

from opencoulomb.core.okada import dc3d, dc3d0

# ---------------------------------------------------------------------------
# Okada (1992) Table 2 Reference Values
# ---------------------------------------------------------------------------


class TestDC3DReferenceCase:
    """Validate against Okada (1992) Table 2 reference values.

    Case: alpha=2/3, x=2, y=3, z=0, depth=4, dip=70,
          al1=0, al2=3, aw1=0, aw2=2.
    """

    # Okada Table 2 reference for strike-slip (disl1=1, disl2=0, disl3=0)
    # u: ux, uy, uz (displacements in meters * 10^-2)
    # Values transcribed from Okada (1992), Table 2, Case I
    ALPHA: ClassVar[float] = 2.0 / 3.0
    X: ClassVar[float] = 2.0
    Y: ClassVar[float] = 3.0
    Z: ClassVar[float] = 0.0
    DEPTH: ClassVar[float] = 4.0
    DIP: ClassVar[float] = 70.0
    AL1: ClassVar[float] = 0.0
    AL2: ClassVar[float] = 3.0
    AW1: ClassVar[float] = 0.0
    AW2: ClassVar[float] = 2.0

    def _run_strike_slip(self) -> tuple:
        """Run the reference strike-slip case."""
        return dc3d(
            self.ALPHA, self.X, self.Y, self.Z,
            self.DEPTH, self.DIP,
            self.AL1, self.AL2, self.AW1, self.AW2,
            disl1=1.0, disl2=0.0, disl3=0.0,
        )

    def test_returns_twelve_components(self) -> None:
        """DC3D must return exactly 12 arrays (3 disp + 9 gradients)."""
        result = self._run_strike_slip()
        assert len(result) == 12

    def test_all_components_finite(self) -> None:
        """All 12 output components must be finite."""
        result = self._run_strike_slip()
        for i, arr in enumerate(result):
            assert np.all(np.isfinite(arr)), f"Component {i} has non-finite values"


# ---------------------------------------------------------------------------
# Full Table 2 validation (all 12 components x 3 slip types)
# ---------------------------------------------------------------------------


class TestOkadaTable2FullValidation:
    """Validate all 12 output components against Okada (1992) Table 2.

    Reference: Okada, Y. (1992), Table 2.
    Case: alpha=2/3, x=2, y=3, z=0, depth=4, dip=70,
          al1=0, al2=3, aw1=0, aw2=2.

    Published values have 4 significant figures. We validate at relative
    tolerance 5e-4 (matching the table precision), then additionally store
    regression fixtures at full numerical precision (≤1e-10 relative error).
    """

    ALPHA: ClassVar[float] = 2.0 / 3.0
    X: ClassVar[float] = 2.0
    Y: ClassVar[float] = 3.0
    Z: ClassVar[float] = 0.0
    DEPTH: ClassVar[float] = 4.0
    DIP: ClassVar[float] = 70.0
    AL1: ClassVar[float] = 0.0
    AL2: ClassVar[float] = 3.0
    AW1: ClassVar[float] = 0.0
    AW2: ClassVar[float] = 2.0

    LABELS: ClassVar[list[str]] = [
        "ux", "uy", "uz", "uxx", "uyx", "uzx",
        "uxy", "uyy", "uzy", "uxz", "uyz", "uzz",
    ]

    # Okada (1992) Table 2: Case I (strike-slip, disl1=1)
    # Values in meters (displacement) or dimensionless (gradients x km)
    TABLE2_STRIKE_SLIP: ClassVar[list[float]] = [
        -8.689e-3, -4.298e-3, -2.747e-3,   # ux, uy, uz
        -1.220e-3, -8.191e-3, -5.175e-3,   # uxx, uyx, uzx
        -7.035e-3,  1.741e-3, -5.506e-4,   # uxy, uyy, uzy
         1.193e-3,  6.503e-4,  2.567e-4,   # uxz, uyz, uzz
    ]

    # Okada (1992) Table 2: Case II (dip-slip, disl2=1)
    TABLE2_DIP_SLIP: ClassVar[list[float]] = [
        -4.682e-3, -3.527e-2, -3.564e-2,
        -8.867e-3,  4.057e-3,  4.088e-3,
        -1.519e-4, -1.035e-2,  2.626e-3,
        -4.088e-3, -2.626e-3,  6.407e-3,
    ]

    # Okada (1992) Table 2: Case III (tensile, disl3=1)
    TABLE2_TENSILE: ClassVar[list[float]] = [
        -2.660e-4,  1.056e-2,  3.214e-3,
        -5.655e-4, -1.066e-3, -3.730e-4,
        -4.782e-4,  1.230e-2,  1.040e-2,
        -6.325e-4, -1.040e-2, -3.911e-3,
    ]

    # Regression fixtures at full computation precision
    REGRESSION_STRIKE_SLIP: ClassVar[list[float]] = [
        -8.6891650043e-03, -4.2975821897e-03, -2.7474058276e-03,
        -1.2204386753e-03, -8.1913728793e-03, -5.1749686957e-03,
        -7.0352896574e-03,  1.7405219243e-03, -5.5057060356e-04,
         1.1934037606e-03,  6.5032393833e-04,  2.5671009500e-04,
    ]

    REGRESSION_DIP_SLIP: ClassVar[list[float]] = [
        -4.6823487628e-03, -3.5267267969e-02, -3.5638557673e-02,
        -8.8672455279e-03,  4.0565856176e-03,  4.0881284900e-03,
        -1.5185823218e-04, -1.0354876542e-02,  2.6262547875e-03,
        -4.0881284900e-03, -2.6262547875e-03,  6.4073740234e-03,
    ]

    REGRESSION_TENSILE: ClassVar[list[float]] = [
        -2.6599600964e-04,  1.0564074877e-02,  3.2141931142e-03,
        -5.6549547621e-04, -1.0662137960e-03, -3.7302193517e-04,
        -4.7819145692e-04,  1.2297109857e-02,  1.0400955547e-02,
        -6.3248016088e-04, -1.0400955547e-02, -3.9105381268e-03,
    ]

    def _run(self, disl1: float, disl2: float, disl3: float) -> tuple:
        return dc3d(
            self.ALPHA, self.X, self.Y, self.Z,
            self.DEPTH, self.DIP,
            self.AL1, self.AL2, self.AW1, self.AW2,
            disl1=disl1, disl2=disl2, disl3=disl3,
        )

    def _check_table2(
        self, result: tuple, ref: list[float], case_name: str,
    ) -> None:
        """Check against Table 2 published values (4 sig fig, ~5e-4 rtol)."""
        for i, (lbl, ref_val) in enumerate(zip(self.LABELS, ref, strict=True)):
            computed = float(result[i][0])
            if abs(ref_val) > 1e-15:
                rel_err = abs((computed - ref_val) / ref_val)
                assert rel_err < 5e-4, (
                    f"{case_name} {lbl}: computed={computed:.6e}, "
                    f"ref={ref_val:.3e}, rel_err={rel_err:.2e}"
                )

    def _check_regression(
        self, result: tuple, ref: list[float], case_name: str,
    ) -> None:
        """Check against regression fixtures at ≤1e-10 relative error."""
        for i, (lbl, ref_val) in enumerate(zip(self.LABELS, ref, strict=True)):
            computed = float(result[i][0])
            if abs(ref_val) > 1e-15:
                rel_err = abs((computed - ref_val) / ref_val)
                assert rel_err < 1e-10, (
                    f"{case_name} {lbl}: computed={computed:.12e}, "
                    f"regression={ref_val:.12e}, rel_err={rel_err:.2e}"
                )

    def test_strike_slip_table2(self) -> None:
        """Strike-slip (Case I): all 12 components vs Table 2."""
        result = self._run(1.0, 0.0, 0.0)
        self._check_table2(result, self.TABLE2_STRIKE_SLIP, "Strike-slip")

    def test_dip_slip_table2(self) -> None:
        """Dip-slip (Case II): all 12 components vs Table 2."""
        result = self._run(0.0, 1.0, 0.0)
        self._check_table2(result, self.TABLE2_DIP_SLIP, "Dip-slip")

    def test_tensile_table2(self) -> None:
        """Tensile (Case III): all 12 components vs Table 2."""
        result = self._run(0.0, 0.0, 1.0)
        self._check_table2(result, self.TABLE2_TENSILE, "Tensile")

    def test_strike_slip_regression(self) -> None:
        """Strike-slip (Case I): all 12 components at ≤1e-10 rel error."""
        result = self._run(1.0, 0.0, 0.0)
        self._check_regression(result, self.REGRESSION_STRIKE_SLIP, "Strike-slip")

    def test_dip_slip_regression(self) -> None:
        """Dip-slip (Case II): all 12 components at ≤1e-10 rel error."""
        result = self._run(0.0, 1.0, 0.0)
        self._check_regression(result, self.REGRESSION_DIP_SLIP, "Dip-slip")

    def test_tensile_regression(self) -> None:
        """Tensile (Case III): all 12 components at ≤1e-10 rel error."""
        result = self._run(0.0, 0.0, 1.0)
        self._check_regression(result, self.REGRESSION_TENSILE, "Tensile")


# ---------------------------------------------------------------------------
# Superposition (linearity)
# ---------------------------------------------------------------------------


class TestDC3DLinearity:
    """Verify the Okada solution obeys linear superposition."""

    def test_strike_slip_superposition(self) -> None:
        """dc3d(disl1=2) == 2 * dc3d(disl1=1)."""
        alpha = 2.0 / 3.0
        x, y, z = 5.0, 3.0, 0.0
        depth, dip = 4.0, 70.0
        al1, al2 = -3.0, 3.0
        aw1, aw2 = -2.0, 2.0

        r1 = dc3d(alpha, x, y, z, depth, dip, al1, al2, aw1, aw2,
                   disl1=1.0, disl2=0.0, disl3=0.0)
        r2 = dc3d(alpha, x, y, z, depth, dip, al1, al2, aw1, aw2,
                   disl1=2.0, disl2=0.0, disl3=0.0)

        for i in range(12):
            np.testing.assert_allclose(
                r2[i], 2.0 * r1[i], atol=1e-15,
                err_msg=f"Component {i} fails linearity",
            )

    def test_dip_slip_superposition(self) -> None:
        """dc3d(disl2=3) == 3 * dc3d(disl2=1)."""
        alpha = 2.0 / 3.0
        x, y, z = 2.0, 4.0, 0.0
        depth, dip = 5.0, 45.0
        al1, al2 = -5.0, 5.0
        aw1, aw2 = -3.0, 3.0

        r1 = dc3d(alpha, x, y, z, depth, dip, al1, al2, aw1, aw2,
                   disl1=0.0, disl2=1.0, disl3=0.0)
        r3 = dc3d(alpha, x, y, z, depth, dip, al1, al2, aw1, aw2,
                   disl1=0.0, disl2=3.0, disl3=0.0)

        for i in range(12):
            np.testing.assert_allclose(
                r3[i], 3.0 * r1[i], atol=1e-14,
                err_msg=f"Component {i} fails dip-slip linearity",
            )

    def test_component_superposition(self) -> None:
        """Strike + dip-slip == separate strike-slip + separate dip-slip."""
        alpha = 2.0 / 3.0
        x, y, z = 3.0, 5.0, 0.0
        depth, dip = 6.0, 60.0
        al1, al2 = -4.0, 4.0
        aw1, aw2 = -2.0, 2.0

        r_ss = dc3d(alpha, x, y, z, depth, dip, al1, al2, aw1, aw2,
                     disl1=1.0, disl2=0.0, disl3=0.0)
        r_ds = dc3d(alpha, x, y, z, depth, dip, al1, al2, aw1, aw2,
                     disl1=0.0, disl2=1.0, disl3=0.0)
        r_both = dc3d(alpha, x, y, z, depth, dip, al1, al2, aw1, aw2,
                       disl1=1.0, disl2=1.0, disl3=0.0)

        for i in range(12):
            np.testing.assert_allclose(
                r_both[i], r_ss[i] + r_ds[i], atol=1e-14,
                err_msg=f"Component {i} fails component superposition",
            )


# ---------------------------------------------------------------------------
# Symmetry properties
# ---------------------------------------------------------------------------


class TestDC3DSymmetry:
    """Test symmetry properties of the Okada solution."""

    def test_strike_slip_vertical_antisymmetry(self) -> None:
        """Pure strike-slip on vertical fault: ux antisymmetric about y=0.

        For a vertical fault with pure left-lateral slip,
        ux(x, y, z) = -ux(x, -y, z) (antisymmetric in y).
        """
        alpha = 2.0 / 3.0
        depth, dip = 5.0, 90.0
        al1, al2 = -5.0, 5.0
        aw1, aw2 = -3.0, 3.0

        x_pts = np.array([2.0, 4.0, 6.0])
        y_pos = np.array([3.0, 5.0, 7.0])
        y_neg = -y_pos
        z_pts = np.zeros(3)

        r_pos = dc3d(alpha, x_pts, y_pos, z_pts, depth, dip,
                      al1, al2, aw1, aw2, disl1=1.0, disl2=0.0, disl3=0.0)
        r_neg = dc3d(alpha, x_pts, y_neg, z_pts, depth, dip,
                      al1, al2, aw1, aw2, disl1=1.0, disl2=0.0, disl3=0.0)

        # ux should be antisymmetric
        np.testing.assert_allclose(r_pos[0], -r_neg[0], atol=1e-12)

    def test_zero_dislocation_zero_output(self) -> None:
        """Zero dislocation must produce zero displacement and gradients."""
        alpha = 2.0 / 3.0
        x, y, z = 5.0, 3.0, 0.0
        depth, dip = 4.0, 45.0
        al1, al2 = -3.0, 3.0
        aw1, aw2 = -2.0, 2.0

        result = dc3d(alpha, x, y, z, depth, dip, al1, al2, aw1, aw2,
                       disl1=0.0, disl2=0.0, disl3=0.0)

        for i in range(12):
            np.testing.assert_allclose(
                result[i], 0.0, atol=1e-20,
                err_msg=f"Component {i} not zero for zero dislocation",
            )


# ---------------------------------------------------------------------------
# Robustness (no NaN/Inf)
# ---------------------------------------------------------------------------


class TestDC3DRobustness:
    """Test that dc3d returns finite values for diverse inputs."""

    def test_random_observation_points(self) -> None:
        """No NaN or Inf for 1000 random observation points."""
        rng = np.random.default_rng(12345)
        n = 1000
        alpha = 2.0 / 3.0
        x = rng.uniform(-50.0, 50.0, n)
        y = rng.uniform(-50.0, 50.0, n)
        z = rng.uniform(-20.0, 0.0, n)
        depth, dip = 10.0, 45.0
        al1, al2 = -10.0, 10.0
        aw1, aw2 = -5.0, 5.0

        result = dc3d(alpha, x, y, z, depth, dip, al1, al2, aw1, aw2,
                       disl1=1.0, disl2=0.5, disl3=0.0)

        for i, arr in enumerate(result):
            assert np.all(np.isfinite(arr)), (
                f"Component {i}: {np.sum(~np.isfinite(arr))} non-finite values"
            )

    def test_surface_observation_z_zero(self) -> None:
        """Surface observation (z=0) returns finite values."""
        alpha = 2.0 / 3.0
        x = np.linspace(-10, 10, 50)
        y = np.linspace(-10, 10, 50)
        z = np.zeros(50)

        result = dc3d(alpha, x, y, z, 5.0, 60.0, -5.0, 5.0, -3.0, 3.0,
                       disl1=1.0, disl2=0.0, disl3=0.0)

        for i, arr in enumerate(result):
            assert np.all(np.isfinite(arr)), f"Component {i} has non-finite at surface"


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


class TestDC3DPerformance:
    """Test computational performance of dc3d."""

    def test_10k_points_under_budget(self) -> None:
        """10,000 observation points must compute in under 0.2 seconds."""
        alpha = 2.0 / 3.0
        n = 10_000
        rng = np.random.default_rng(99)
        x = rng.uniform(-50, 50, n)
        y = rng.uniform(-50, 50, n)
        z = rng.uniform(-20, 0, n)

        t0 = time.perf_counter()
        dc3d(alpha, x, y, z, 10.0, 45.0, -5.0, 5.0, -3.0, 3.0,
             disl1=1.0, disl2=0.0, disl3=0.0)
        elapsed = time.perf_counter() - t0

        # Allow generous budget; NumPy vectorized should be fast
        assert elapsed < 0.2, f"10k points took {elapsed:.3f}s (budget: 0.2s)"


# ---------------------------------------------------------------------------
# DC3D0 point source
# ---------------------------------------------------------------------------


class TestDC3D0:
    """Test Okada DC3D0 point source implementation."""

    def test_returns_finite_values(self) -> None:
        """DC3D0 must return all-finite 12-component output."""
        alpha = 2.0 / 3.0
        x, y, z = 5.0, 3.0, 0.0
        depth, dip = 4.0, 70.0

        result = dc3d0(alpha, x, y, z, depth, dip,
                        pot1=1.0, pot2=0.0, pot3=0.0, pot4=0.0)

        assert len(result) == 12
        for i, arr in enumerate(result):
            assert np.all(np.isfinite(arr)), f"DC3D0 component {i} non-finite"

    def test_zero_potency_zero_output(self) -> None:
        """Zero potency produces zero output."""
        result = dc3d0(2.0 / 3.0, 5.0, 3.0, 0.0, 4.0, 45.0,
                        pot1=0.0, pot2=0.0, pot3=0.0, pot4=0.0)
        for i, arr in enumerate(result):
            np.testing.assert_allclose(
                arr, 0.0, atol=1e-20,
                err_msg=f"Component {i} not zero for zero potency",
            )

    def test_linearity(self) -> None:
        """dc3d0(pot1=2) == 2 * dc3d0(pot1=1)."""
        alpha = 2.0 / 3.0
        x, y, z = 5.0, 3.0, 0.0
        depth, dip = 4.0, 45.0

        r1 = dc3d0(alpha, x, y, z, depth, dip,
                    pot1=1.0, pot2=0.0, pot3=0.0, pot4=0.0)
        r2 = dc3d0(alpha, x, y, z, depth, dip,
                    pot1=2.0, pot2=0.0, pot3=0.0, pot4=0.0)

        for i in range(12):
            np.testing.assert_allclose(
                r2[i], 2.0 * r1[i], atol=1e-15,
                err_msg=f"DC3D0 component {i} fails linearity",
            )

    def test_random_points_finite(self) -> None:
        """DC3D0 returns finite for random observation points."""
        rng = np.random.default_rng(777)
        n = 500
        x = rng.uniform(-20, 20, n)
        y = rng.uniform(-20, 20, n)
        z = rng.uniform(-10, 0, n)

        result = dc3d0(2.0 / 3.0, x, y, z, 5.0, 60.0,
                        pot1=1.0, pot2=0.5, pot3=0.0, pot4=0.0)

        for i, arr in enumerate(result):
            assert np.all(np.isfinite(arr)), f"DC3D0 component {i} non-finite"


# ---------------------------------------------------------------------------
# DC3D0 consistency with small DC3D faults
# ---------------------------------------------------------------------------


class TestDC3D0ConsistencyWithDC3D:
    """A very small finite fault should approximate a point source."""

    def test_small_fault_approaches_point_source(self) -> None:
        """dc3d (small fault) ~ dc3d0 * area for displacement (within 5%).

        This is a rough consistency check since they are different
        mathematical formulations that converge as fault size -> 0.
        """
        alpha = 2.0 / 3.0
        depth, dip = 10.0, 45.0

        # Observation point far from the source (far-field)
        x_obs, y_obs, z_obs = 30.0, 30.0, 0.0

        # Small fault
        half_l = 0.05  # 50 m half-length
        half_w = 0.05
        area = (2 * half_l) * (2 * half_w)  # 0.01 km^2

        # Finite fault: disl1 = 1 m strike-slip
        r_finite = dc3d(
            alpha, x_obs, y_obs, z_obs, depth, dip,
            -half_l, half_l, -half_w, half_w,
            disl1=1.0, disl2=0.0, disl3=0.0,
        )

        # Point source: pot1 = disl1 * area (potency = slip * area)
        r_point = dc3d0(
            alpha, x_obs, y_obs, z_obs, depth, dip,
            pot1=1.0 * area, pot2=0.0, pot3=0.0, pot4=0.0,
        )

        # Compare displacements (first 3 components)
        for i in range(3):
            finite_val = float(r_finite[i][0])
            point_val = float(r_point[i][0])
            if abs(finite_val) > 1e-15:
                relative_error = abs((point_val - finite_val) / finite_val)
                assert relative_error < 0.05, (
                    f"Component {i}: finite={finite_val:.6e}, "
                    f"point={point_val:.6e}, rel_err={relative_error:.3f}"
                )


# ---------------------------------------------------------------------------
# Tensile dislocation coverage (disl3 branches)
# ---------------------------------------------------------------------------


class TestDC3DTensile:
    """Test DC3D with tensile dislocation (disl3 != 0) to cover tensile branches."""

    def test_pure_tensile_finite(self) -> None:
        """Pure tensile dislocation returns finite results."""
        alpha = 2.0 / 3.0
        x = np.array([2.0, 5.0, 10.0])
        y = np.array([3.0, 6.0, -5.0])
        z = np.array([0.0, -1.0, -2.0])

        result = dc3d(alpha, x, y, z, 5.0, 45.0, -5.0, 5.0, -3.0, 3.0,
                       disl1=0.0, disl2=0.0, disl3=1.0)

        for i, arr in enumerate(result):
            assert np.all(np.isfinite(arr)), f"Tensile component {i} non-finite"

    def test_tensile_nonzero(self) -> None:
        """Tensile dislocation should produce nonzero output."""
        result = dc3d(2.0 / 3.0, 5.0, 3.0, 0.0, 4.0, 60.0,
                       -3.0, 3.0, -2.0, 2.0,
                       disl1=0.0, disl2=0.0, disl3=1.0)

        # At least some displacement components should be nonzero
        total = sum(float(np.max(np.abs(arr))) for arr in result[:3])
        assert total > 0.0

    def test_tensile_superposition(self) -> None:
        """dc3d(disl3=2) == 2 * dc3d(disl3=1)."""
        alpha = 2.0 / 3.0
        x, y, z = 5.0, 3.0, 0.0

        r1 = dc3d(alpha, x, y, z, 5.0, 45.0, -5.0, 5.0, -3.0, 3.0,
                   disl1=0.0, disl2=0.0, disl3=1.0)
        r2 = dc3d(alpha, x, y, z, 5.0, 45.0, -5.0, 5.0, -3.0, 3.0,
                   disl1=0.0, disl2=0.0, disl3=2.0)

        for i in range(12):
            np.testing.assert_allclose(r2[i], 2.0 * r1[i], atol=1e-14)

    def test_combined_all_three_dislocations(self) -> None:
        """All three dislocations active simultaneously."""
        alpha = 2.0 / 3.0
        rng = np.random.default_rng(555)
        n = 200
        x = rng.uniform(-30, 30, n)
        y = rng.uniform(-30, 30, n)
        z = rng.uniform(-10, 0, n)

        result = dc3d(alpha, x, y, z, 8.0, 50.0, -6.0, 6.0, -4.0, 4.0,
                       disl1=1.0, disl2=0.5, disl3=0.3)

        for i, arr in enumerate(result):
            assert np.all(np.isfinite(arr)), f"Combined component {i} non-finite"


# ---------------------------------------------------------------------------
# DC3D0 all potency types
# ---------------------------------------------------------------------------


class TestDC3D0AllPotencyTypes:
    """Test DC3D0 with all four potency types to cover all branches."""

    def test_dip_slip_potency(self) -> None:
        """DC3D0 with pot2 (dip-slip) returns finite values."""
        result = dc3d0(2.0 / 3.0, 5.0, 3.0, 0.0, 4.0, 45.0,
                        pot1=0.0, pot2=1.0, pot3=0.0, pot4=0.0)
        for i, arr in enumerate(result):
            assert np.all(np.isfinite(arr)), f"DC3D0 pot2 component {i} non-finite"

    def test_tensile_potency(self) -> None:
        """DC3D0 with pot3 (tensile) returns finite values."""
        result = dc3d0(2.0 / 3.0, 5.0, 3.0, 0.0, 4.0, 45.0,
                        pot1=0.0, pot2=0.0, pot3=1.0, pot4=0.0)
        for i, arr in enumerate(result):
            assert np.all(np.isfinite(arr)), f"DC3D0 pot3 component {i} non-finite"

    def test_inflation_potency(self) -> None:
        """DC3D0 with pot4 (inflation) returns finite values."""
        result = dc3d0(2.0 / 3.0, 5.0, 3.0, 0.0, 4.0, 45.0,
                        pot1=0.0, pot2=0.0, pot3=0.0, pot4=1.0)
        for i, arr in enumerate(result):
            assert np.all(np.isfinite(arr)), f"DC3D0 pot4 component {i} non-finite"

    def test_all_potencies_combined(self) -> None:
        """DC3D0 with all four potencies active."""
        rng = np.random.default_rng(888)
        n = 100
        x = rng.uniform(-20, 20, n)
        y = rng.uniform(-20, 20, n)
        z = rng.uniform(-10, 0, n)

        result = dc3d0(2.0 / 3.0, x, y, z, 5.0, 60.0,
                        pot1=1.0, pot2=0.5, pot3=0.3, pot4=0.2)

        for i, arr in enumerate(result):
            assert np.all(np.isfinite(arr)), f"DC3D0 all-pot component {i} non-finite"
