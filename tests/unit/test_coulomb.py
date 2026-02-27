"""Unit tests for opencoulomb.core.coulomb.

Covers:
- compute_cfs: CFS = shear + friction * normal
- resolve_stress_on_fault: known stress resolution on receiver planes
- compute_cfs_on_receiver: convenience function combining both
- Pure normal stress case
- Pure shear case
- Combined case
- Sign convention: positive CFS = failure promoted
- Edge cases: vertical fault, horizontal fault
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from opencoulomb.core.coulomb import (
    compute_cfs,
    compute_cfs_on_receiver,
    resolve_stress_on_fault,
)

# ---------------------------------------------------------------------------
# compute_cfs
# ---------------------------------------------------------------------------


class TestComputeCFS:
    """Test the basic CFS = shear + friction * normal formula."""

    def test_pure_shear(self) -> None:
        """CFS = shear when normal stress is zero."""
        shear = np.array([1.0, 2.0, -0.5])
        normal = np.zeros(3)
        friction = 0.4

        cfs = compute_cfs(shear, normal, friction)

        np.testing.assert_allclose(cfs, shear, atol=1e-14)

    def test_pure_normal(self) -> None:
        """CFS = friction * normal when shear is zero."""
        shear = np.zeros(3)
        normal = np.array([1.0, -2.0, 0.5])
        friction = 0.4

        cfs = compute_cfs(shear, normal, friction)

        np.testing.assert_allclose(cfs, friction * normal, atol=1e-14)

    def test_combined(self) -> None:
        """CFS = shear + friction * normal for known values."""
        shear = np.array([3.0])
        normal = np.array([5.0])
        friction = 0.6

        cfs = compute_cfs(shear, normal, friction)

        expected = 3.0 + 0.6 * 5.0  # 6.0
        assert cfs[0] == pytest.approx(expected, abs=1e-14)

    def test_zero_friction(self) -> None:
        """With friction=0, CFS = shear regardless of normal."""
        shear = np.array([2.5])
        normal = np.array([100.0])
        friction = 0.0

        cfs = compute_cfs(shear, normal, friction)

        assert cfs[0] == pytest.approx(2.5, abs=1e-14)

    def test_sign_convention_positive_promotes_failure(self) -> None:
        """Positive shear and positive normal (unclamping) both promote failure."""
        shear = np.array([1.0])
        normal = np.array([1.0])  # positive = unclamping
        friction = 0.4

        cfs = compute_cfs(shear, normal, friction)

        assert cfs[0] > 0.0, "Positive shear + unclamping should give positive CFS"

    def test_sign_convention_clamping_inhibits(self) -> None:
        """Clamping (negative normal) can overcome shear to inhibit failure."""
        shear = np.array([0.1])
        normal = np.array([-10.0])  # strong clamping
        friction = 0.4

        cfs = compute_cfs(shear, normal, friction)

        assert cfs[0] < 0.0, "Strong clamping should give negative CFS"


# ---------------------------------------------------------------------------
# resolve_stress_on_fault
# ---------------------------------------------------------------------------


class TestResolveStressOnFault:
    """Test stress resolution onto receiver fault planes."""

    def test_hydrostatic_stress_on_any_fault(self) -> None:
        """Hydrostatic stress: shear=0, normal=pressure on any fault.

        For sigma_ij = p * delta_ij:
        normal = p (pressure on any plane)
        shear = 0 (no shear on any plane)
        """
        n = 1
        p = 5.0
        sxx = np.array([p])
        syy = np.array([p])
        szz = np.array([p])
        syz = np.zeros(n)
        sxz = np.zeros(n)
        sxy = np.zeros(n)

        strike = math.radians(45.0)
        dip = math.radians(60.0)
        rake = math.radians(30.0)

        shear, normal = resolve_stress_on_fault(
            sxx, syy, szz, syz, sxz, sxy,
            strike, dip, rake,
        )

        assert normal[0] == pytest.approx(p, abs=1e-10)
        assert shear[0] == pytest.approx(0.0, abs=1e-10)

    def test_pure_sxx_on_ns_vertical_fault(self) -> None:
        """N-S vertical fault with pure sxx stress.

        Fault: strike=0, dip=90, rake=0 (pure strike-slip)
        Normal = [cos(s)*sin(d), -sin(s)*sin(d), cos(d)]
             = [cos(0)*1, 0, 0] = [1, 0, 0]
        sigma_n = nx^2 * sxx = 1 * sxx = sxx
        """
        sxx = np.array([10.0])
        syy = np.zeros(1)
        szz = np.zeros(1)
        syz = np.zeros(1)
        sxz = np.zeros(1)
        sxy = np.zeros(1)

        strike = math.radians(0.0)
        dip = math.radians(90.0)
        rake = math.radians(0.0)

        _shear, normal = resolve_stress_on_fault(
            sxx, syy, szz, syz, sxz, sxy,
            strike, dip, rake,
        )

        assert normal[0] == pytest.approx(10.0, abs=1e-10)

    def test_vectorized_multiple_points(self) -> None:
        """Multiple observation points should work."""
        n = 100
        rng = np.random.default_rng(42)
        sxx = rng.standard_normal(n)
        syy = rng.standard_normal(n)
        szz = rng.standard_normal(n)
        syz = rng.standard_normal(n)
        sxz = rng.standard_normal(n)
        sxy = rng.standard_normal(n)

        shear, normal = resolve_stress_on_fault(
            sxx, syy, szz, syz, sxz, sxy,
            math.radians(30.0), math.radians(45.0), math.radians(90.0),
        )

        assert shear.shape == (n,)
        assert normal.shape == (n,)
        assert np.all(np.isfinite(shear))
        assert np.all(np.isfinite(normal))

    def test_zero_stress_zero_resolved(self) -> None:
        """Zero stress tensor resolves to zero shear and normal."""
        n = 3
        zeros = np.zeros(n)

        shear, normal = resolve_stress_on_fault(
            zeros, zeros, zeros, zeros, zeros, zeros,
            math.radians(45.0), math.radians(60.0), math.radians(30.0),
        )

        np.testing.assert_allclose(shear, 0.0, atol=1e-14)
        np.testing.assert_allclose(normal, 0.0, atol=1e-14)


# ---------------------------------------------------------------------------
# compute_cfs_on_receiver
# ---------------------------------------------------------------------------


class TestComputeCFSOnReceiver:
    """Test convenience function combining resolution and CFS."""

    def test_returns_three_arrays(self) -> None:
        """Must return (cfs, shear, normal) tuple."""
        n = 5
        zeros = np.zeros(n)
        ones = np.ones(n)

        cfs, shear, normal = compute_cfs_on_receiver(
            ones, zeros, zeros, zeros, zeros, zeros,
            math.radians(0.0), math.radians(90.0), math.radians(0.0),
            friction=0.4,
        )

        assert cfs.shape == (n,)
        assert shear.shape == (n,)
        assert normal.shape == (n,)

    def test_consistency_with_separate_calls(self) -> None:
        """compute_cfs_on_receiver == resolve + compute_cfs."""
        n = 10
        rng = np.random.default_rng(123)
        sxx = rng.uniform(-5, 5, n)
        syy = rng.uniform(-5, 5, n)
        szz = rng.uniform(-5, 5, n)
        syz = rng.uniform(-2, 2, n)
        sxz = rng.uniform(-2, 2, n)
        sxy = rng.uniform(-2, 2, n)

        strike = math.radians(60.0)
        dip = math.radians(45.0)
        rake = math.radians(90.0)
        friction = 0.4

        # Combined
        cfs_c, shear_c, normal_c = compute_cfs_on_receiver(
            sxx, syy, szz, syz, sxz, sxy,
            strike, dip, rake, friction,
        )

        # Separate
        shear_s, normal_s = resolve_stress_on_fault(
            sxx, syy, szz, syz, sxz, sxy, strike, dip, rake,
        )
        cfs_s = compute_cfs(shear_s, normal_s, friction)

        np.testing.assert_allclose(cfs_c, cfs_s, atol=1e-14)
        np.testing.assert_allclose(shear_c, shear_s, atol=1e-14)
        np.testing.assert_allclose(normal_c, normal_s, atol=1e-14)

    def test_known_combined_case(self) -> None:
        """CFS = shear + friction * normal for a known stress state."""
        # Apply a known uniaxial stress sxx=10 on a 45-dip fault
        # and verify CFS = resolved_shear + friction * resolved_normal
        sxx = np.array([10.0])
        syy = np.zeros(1)
        szz = np.zeros(1)
        syz = np.zeros(1)
        sxz = np.zeros(1)
        sxy = np.zeros(1)

        friction = 0.4
        strike = math.radians(45.0)
        dip = math.radians(45.0)
        rake = math.radians(0.0)

        cfs, shear, normal = compute_cfs_on_receiver(
            sxx, syy, szz, syz, sxz, sxy,
            strike, dip, rake, friction,
        )

        # Verify CFS formula
        expected_cfs = shear + friction * normal
        np.testing.assert_allclose(cfs, expected_cfs, atol=1e-14)


# ---------------------------------------------------------------------------
# Edge cases: vertical and horizontal faults
# ---------------------------------------------------------------------------


class TestCFSEdgeCases:
    """Test CFS on extreme fault orientations."""

    def test_vertical_fault(self) -> None:
        """CFS on a vertical fault (dip=90) should be finite."""
        n = 5
        rng = np.random.default_rng(99)
        sxx = rng.uniform(-5, 5, n)
        syy = rng.uniform(-5, 5, n)
        szz = rng.uniform(-5, 5, n)
        syz = rng.uniform(-2, 2, n)
        sxz = rng.uniform(-2, 2, n)
        sxy = rng.uniform(-2, 2, n)

        cfs, shear, normal = compute_cfs_on_receiver(
            sxx, syy, szz, syz, sxz, sxy,
            math.radians(0.0), math.radians(90.0), math.radians(0.0),
            friction=0.4,
        )

        assert np.all(np.isfinite(cfs))
        assert np.all(np.isfinite(shear))
        assert np.all(np.isfinite(normal))

    def test_shallow_dip_fault(self) -> None:
        """CFS on a nearly horizontal fault (dip=5) should be finite."""
        n = 5
        rng = np.random.default_rng(77)
        sxx = rng.uniform(-5, 5, n)
        syy = rng.uniform(-5, 5, n)
        szz = rng.uniform(-5, 5, n)
        syz = rng.uniform(-2, 2, n)
        sxz = rng.uniform(-2, 2, n)
        sxy = rng.uniform(-2, 2, n)

        cfs, shear, normal = compute_cfs_on_receiver(
            sxx, syy, szz, syz, sxz, sxy,
            math.radians(90.0), math.radians(5.0), math.radians(90.0),
            friction=0.4,
        )

        assert np.all(np.isfinite(cfs))
        assert np.all(np.isfinite(shear))
        assert np.all(np.isfinite(normal))

    def test_different_receiver_orientations_give_different_cfs(self) -> None:
        """Different receiver orientations should produce different CFS."""
        sxx = np.array([10.0])
        syy = np.array([5.0])
        szz = np.array([3.0])
        syz = np.array([1.0])
        sxz = np.array([0.5])
        sxy = np.array([2.0])

        cfs_1, _, _ = compute_cfs_on_receiver(
            sxx, syy, szz, syz, sxz, sxy,
            math.radians(0.0), math.radians(45.0), math.radians(0.0),
            friction=0.4,
        )

        cfs_2, _, _ = compute_cfs_on_receiver(
            sxx, syy, szz, syz, sxz, sxy,
            math.radians(90.0), math.radians(45.0), math.radians(0.0),
            friction=0.4,
        )

        assert cfs_1[0] != pytest.approx(cfs_2[0], abs=1e-6), (
            "Different receivers should yield different CFS for non-hydrostatic stress"
        )
