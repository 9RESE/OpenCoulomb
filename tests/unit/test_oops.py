"""Unit tests for the OOPs (Optimally Oriented Planes) module.

Tests cover:
- Regional stress tensor construction
- Mohr-Coulomb optimal angle
- Eigendecomposition and optimal plane finding
- Normal-to-strike/dip/rake conversion
- Edge cases (hydrostatic, uniaxial, zero friction)
"""

from __future__ import annotations

import math

import numpy as np

from opencoulomb.core.oops import (
    _build_stress_matrices,
    _normal_to_strike_dip_rake,
    compute_regional_stress_tensor,
    find_optimal_planes,
    mohr_coulomb_angle,
)
from opencoulomb.types.stress import PrincipalStress, RegionalStress

# ---------------------------------------------------------------------------
# Mohr-Coulomb angle
# ---------------------------------------------------------------------------


class TestMohrCoulombAngle:
    """Test the Mohr-Coulomb optimal failure plane angle."""

    def test_standard_friction(self) -> None:
        """beta = 0.5 * atan(1/mu) for mu=0.4."""
        beta = mohr_coulomb_angle(0.4)
        expected = 0.5 * math.atan(1.0 / 0.4)
        assert abs(beta - expected) < 1e-12

    def test_zero_friction(self) -> None:
        """beta = pi/4 for frictionless fault."""
        beta = mohr_coulomb_angle(0.0)
        assert abs(beta - math.pi / 4.0) < 1e-12

    def test_high_friction(self) -> None:
        """beta approaches 0 as friction -> infinity."""
        beta = mohr_coulomb_angle(100.0)
        assert beta > 0
        assert beta < math.radians(1.0)

    def test_typical_friction_values(self) -> None:
        """Verify angle for common friction coefficients."""
        # mu=0.4 -> beta ~34.1 deg
        beta_04 = math.degrees(mohr_coulomb_angle(0.4))
        assert abs(beta_04 - 34.1) < 0.1

        # mu=0.6 -> beta ~29.5 deg
        beta_06 = math.degrees(mohr_coulomb_angle(0.6))
        assert abs(beta_06 - 29.5) < 0.1

        # mu=0.8 -> beta ~25.7 deg
        beta_08 = math.degrees(mohr_coulomb_angle(0.8))
        assert abs(beta_08 - 25.7) < 0.1


# ---------------------------------------------------------------------------
# Regional stress tensor construction
# ---------------------------------------------------------------------------


class TestRegionalStressTensor:
    """Test construction of 6-component stress tensor from principal stresses."""

    def test_single_axis_north(self) -> None:
        """s1 pointing North at surface produces syy = intensity."""
        rs = RegionalStress(
            s1=PrincipalStress(direction=0.0, dip=0.0, intensity=100.0, gradient=0.0),
            s2=PrincipalStress(direction=90.0, dip=0.0, intensity=0.0, gradient=0.0),
            s3=PrincipalStress(direction=0.0, dip=90.0, intensity=0.0, gradient=0.0),
        )
        depth = np.array([0.0])
        sxx, syy, szz, _syz, _sxz, _sxy = compute_regional_stress_tensor(rs, depth)
        assert abs(syy[0] - 100.0) < 1e-10
        assert abs(sxx[0]) < 1e-10
        assert abs(szz[0]) < 1e-10

    def test_single_axis_east(self) -> None:
        """s2 pointing East at surface produces sxx = intensity."""
        rs = RegionalStress(
            s1=PrincipalStress(direction=0.0, dip=0.0, intensity=0.0, gradient=0.0),
            s2=PrincipalStress(direction=90.0, dip=0.0, intensity=50.0, gradient=0.0),
            s3=PrincipalStress(direction=0.0, dip=90.0, intensity=0.0, gradient=0.0),
        )
        depth = np.array([0.0])
        sxx, syy, _szz, _syz, _sxz, _sxy = compute_regional_stress_tensor(rs, depth)
        assert abs(sxx[0] - 50.0) < 1e-10
        assert abs(syy[0]) < 1e-10

    def test_vertical_axis(self) -> None:
        """s3 pointing vertically downward produces szz = intensity."""
        rs = RegionalStress(
            s1=PrincipalStress(direction=0.0, dip=0.0, intensity=0.0, gradient=0.0),
            s2=PrincipalStress(direction=90.0, dip=0.0, intensity=0.0, gradient=0.0),
            s3=PrincipalStress(direction=0.0, dip=90.0, intensity=30.0, gradient=0.0),
        )
        depth = np.array([0.0])
        sxx, syy, szz, _syz, _sxz, _sxy = compute_regional_stress_tensor(rs, depth)
        assert abs(szz[0] - 30.0) < 1e-10
        assert abs(sxx[0]) < 1e-10
        assert abs(syy[0]) < 1e-10

    def test_depth_gradient(self) -> None:
        """Stress increases linearly with depth."""
        rs = RegionalStress(
            s1=PrincipalStress(direction=0.0, dip=0.0, intensity=100.0, gradient=10.0),
            s2=PrincipalStress(direction=90.0, dip=0.0, intensity=0.0, gradient=0.0),
            s3=PrincipalStress(direction=0.0, dip=90.0, intensity=0.0, gradient=0.0),
        )
        depth = np.array([0.0, 5.0, 10.0])
        _, syy, _, _, _, _ = compute_regional_stress_tensor(rs, depth)
        np.testing.assert_allclose(syy, [100.0, 150.0, 200.0], atol=1e-10)

    def test_hydrostatic_stress(self) -> None:
        """Equal principal stresses in all directions = isotropic tensor."""
        rs = RegionalStress(
            s1=PrincipalStress(direction=0.0, dip=0.0, intensity=100.0, gradient=0.0),
            s2=PrincipalStress(direction=90.0, dip=0.0, intensity=100.0, gradient=0.0),
            s3=PrincipalStress(direction=0.0, dip=90.0, intensity=100.0, gradient=0.0),
        )
        depth = np.array([0.0])
        sxx, syy, szz, syz, sxz, sxy = compute_regional_stress_tensor(rs, depth)
        np.testing.assert_allclose(sxx, [100.0], atol=1e-10)
        np.testing.assert_allclose(syy, [100.0], atol=1e-10)
        np.testing.assert_allclose(szz, [100.0], atol=1e-10)
        np.testing.assert_allclose(syz, [0.0], atol=1e-10)
        np.testing.assert_allclose(sxz, [0.0], atol=1e-10)
        np.testing.assert_allclose(sxy, [0.0], atol=1e-10)

    def test_off_diagonal_from_oblique_axis(self) -> None:
        """Oblique principal axis produces off-diagonal stress components."""
        # s1 at 45 deg azimuth, horizontal
        rs = RegionalStress(
            s1=PrincipalStress(direction=45.0, dip=0.0, intensity=100.0, gradient=0.0),
            s2=PrincipalStress(direction=135.0, dip=0.0, intensity=0.0, gradient=0.0),
            s3=PrincipalStress(direction=0.0, dip=90.0, intensity=0.0, gradient=0.0),
        )
        depth = np.array([0.0])
        sxx, syy, szz, _syz, _sxz, sxy = compute_regional_stress_tensor(rs, depth)
        # At 45 deg: vx = sin(45)*1 = 0.707, vy = cos(45)*1 = 0.707
        # sxx = 100 * 0.5, syy = 100 * 0.5, sxy = 100 * 0.5
        np.testing.assert_allclose(sxx, [50.0], atol=1e-10)
        np.testing.assert_allclose(syy, [50.0], atol=1e-10)
        np.testing.assert_allclose(sxy, [50.0], atol=1e-10)
        np.testing.assert_allclose(szz, [0.0], atol=1e-10)


# ---------------------------------------------------------------------------
# Stress matrix construction
# ---------------------------------------------------------------------------


class TestBuildStressMatrices:
    """Test the _build_stress_matrices helper."""

    def test_shape(self) -> None:
        n = 5
        S = _build_stress_matrices(
            np.ones(n), np.ones(n) * 2, np.ones(n) * 3,
            np.ones(n) * 4, np.ones(n) * 5, np.ones(n) * 6,
        )
        assert S.shape == (5, 3, 3)

    def test_symmetry(self) -> None:
        n = 3
        S = _build_stress_matrices(
            np.ones(n), np.ones(n) * 2, np.ones(n) * 3,
            np.ones(n) * 4, np.ones(n) * 5, np.ones(n) * 6,
        )
        for i in range(n):
            np.testing.assert_array_equal(S[i], S[i].T)

    def test_values(self) -> None:
        S = _build_stress_matrices(
            np.array([1.0]), np.array([2.0]), np.array([3.0]),
            np.array([4.0]), np.array([5.0]), np.array([6.0]),
        )
        expected = np.array([[1, 6, 5], [6, 2, 4], [5, 4, 3]], dtype=float)
        np.testing.assert_array_equal(S[0], expected)


# ---------------------------------------------------------------------------
# Find optimal planes
# ---------------------------------------------------------------------------


class TestFindOptimalPlanes:
    """Test the complete OOP solver."""

    def test_uniaxial_compression_x(self) -> None:
        """Pure compression in x-direction: optimal plane dips steeply."""
        n = 3
        sxx = np.full(n, 10.0)
        syy = np.zeros(n)
        szz = np.zeros(n)
        syz = np.zeros(n)
        sxz = np.zeros(n)
        sxy = np.zeros(n)

        strike, dip, rake, cfs = find_optimal_planes(
            sxx, syy, szz, syz, sxz, sxy, 0.4,
        )

        assert strike.shape == (n,)
        assert dip.shape == (n,)
        assert rake.shape == (n,)
        assert cfs.shape == (n,)
        # CFS should be positive (promotes failure)
        assert np.all(cfs > 0)
        # Dip should be steep (plane at angle to sigma1)
        assert np.all(dip > 30)

    def test_uniform_stress_gives_consistent_results(self) -> None:
        """All grid points with same stress should get same orientation."""
        n = 10
        sxx = np.full(n, 20.0)
        syy = np.full(n, 5.0)
        szz = np.full(n, 0.0)
        syz = np.zeros(n)
        sxz = np.zeros(n)
        sxy = np.zeros(n)

        strike, dip, _rake, cfs = find_optimal_planes(
            sxx, syy, szz, syz, sxz, sxy, 0.4,
        )

        # All points should have same orientation (within tolerance)
        np.testing.assert_allclose(strike, strike[0], atol=0.01)
        np.testing.assert_allclose(dip, dip[0], atol=0.01)
        np.testing.assert_allclose(cfs, cfs[0], atol=1e-10)

    def test_hydrostatic_stress_zero_cfs(self) -> None:
        """Under hydrostatic stress (all equal), shear=0 so CFS depends only on normal."""
        n = 3
        p = 100.0
        sxx = np.full(n, p)
        syy = np.full(n, p)
        szz = np.full(n, p)
        syz = np.zeros(n)
        sxz = np.zeros(n)
        sxy = np.zeros(n)

        _strike, _dip, _rake, cfs = find_optimal_planes(
            sxx, syy, szz, syz, sxz, sxy, 0.4,
        )

        # Under hydrostatic stress, traction on any plane = p*n
        # Normal stress = p, shear = 0
        # CFS = 0 + mu * p = mu * p
        # Since all eigenvalues are equal, the OOP degeneracy means
        # shear is zero and CFS = friction * p
        expected_cfs = 0.4 * p
        np.testing.assert_allclose(np.abs(cfs), expected_cfs, atol=1e-6)

    def test_strike_range(self) -> None:
        """Strike should be in [0, 360)."""
        n = 5
        rng = np.random.default_rng(42)
        sxx = rng.uniform(-10, 10, n)
        syy = rng.uniform(-10, 10, n)
        szz = rng.uniform(-10, 10, n)
        syz = rng.uniform(-5, 5, n)
        sxz = rng.uniform(-5, 5, n)
        sxy = rng.uniform(-5, 5, n)

        strike, _dip, _rake, _cfs = find_optimal_planes(
            sxx, syy, szz, syz, sxz, sxy, 0.4,
        )

        assert np.all(strike >= 0)
        assert np.all(strike < 360)

    def test_dip_range(self) -> None:
        """Dip should be in [0, 90]."""
        n = 5
        rng = np.random.default_rng(123)
        sxx = rng.uniform(-10, 10, n)
        syy = rng.uniform(-10, 10, n)
        szz = rng.uniform(-10, 10, n)
        syz = rng.uniform(-5, 5, n)
        sxz = rng.uniform(-5, 5, n)
        sxy = rng.uniform(-5, 5, n)

        _strike, dip, _rake, _cfs = find_optimal_planes(
            sxx, syy, szz, syz, sxz, sxy, 0.4,
        )

        assert np.all(dip >= 0)
        assert np.all(dip <= 90 + 1e-10)

    def test_single_point(self) -> None:
        """Works with a single grid point."""
        strike, _dip, _rake, cfs = find_optimal_planes(
            np.array([10.0]), np.array([0.0]), np.array([0.0]),
            np.array([0.0]), np.array([0.0]), np.array([0.0]),
            0.4,
        )
        assert strike.shape == (1,)
        assert cfs[0] > 0


# ---------------------------------------------------------------------------
# Normal to strike/dip/rake conversion
# ---------------------------------------------------------------------------


class TestNormalToStrikeDipRake:
    """Test conversion from fault normal to strike/dip/rake."""

    def test_vertical_normal(self) -> None:
        """Vertical normal = horizontal plane (dip=0)."""
        n = np.array([0.0, 0.0, 1.0])
        S = np.diag([10.0, 5.0, 0.0])
        _strike, dip, _rake = _normal_to_strike_dip_rake(n, S)
        assert abs(dip) < 1e-6

    def test_north_dipping_normal(self) -> None:
        """Normal pointing North-Up at 45 deg = dip ~45 deg."""
        n = np.array([0.0, 1.0, 1.0])
        n = n / np.linalg.norm(n)
        S = np.diag([10.0, 5.0, 0.0])
        _strike, dip, _rake = _normal_to_strike_dip_rake(n, S)
        assert abs(dip - 45.0) < 1.0

    def test_east_dipping_normal(self) -> None:
        """Normal pointing East-Up at 45 deg = dip ~45 deg."""
        n = np.array([1.0, 0.0, 1.0])
        n = n / np.linalg.norm(n)
        S = np.diag([10.0, 5.0, 0.0])
        _strike, dip, _rake = _normal_to_strike_dip_rake(n, S)
        assert abs(dip - 45.0) < 1.0

    def test_flipped_normal(self) -> None:
        """Downward-pointing normal gets flipped to maintain dip 0-90."""
        n = np.array([0.0, 0.0, -1.0])
        S = np.diag([10.0, 5.0, 0.0])
        _strike, dip, _rake = _normal_to_strike_dip_rake(n, S)
        assert dip >= 0
        assert dip <= 90


# ---------------------------------------------------------------------------
# Integration: OOPs in pipeline
# ---------------------------------------------------------------------------


class TestOOPsInPipeline:
    """Test OOPs integration with the compute_grid pipeline."""

    def test_no_regional_stress_no_oops(self) -> None:
        """Without regional_stress, OOP fields are None."""
        from opencoulomb.core.pipeline import compute_grid
        from opencoulomb.io import read_inp

        model = read_inp("tests/fixtures/inp_files/real/simplest_receiver.inp")
        # Clear regional stress to test the no-OOP path
        model.regional_stress = None

        result = compute_grid(model)
        assert result.oops_strike is None
        assert result.oops_dip is None
        assert result.oops_rake is None

    def test_with_regional_stress_has_oops(self) -> None:
        """With regional_stress, OOP fields are populated."""
        from opencoulomb.core.pipeline import compute_grid
        from opencoulomb.io import read_inp

        model = read_inp("tests/fixtures/inp_files/real/simplest_receiver.inp")

        # Inject regional stress
        rs = RegionalStress(
            s1=PrincipalStress(direction=0.0, dip=0.0, intensity=100.0, gradient=10.0),
            s2=PrincipalStress(direction=90.0, dip=0.0, intensity=50.0, gradient=5.0),
            s3=PrincipalStress(direction=0.0, dip=90.0, intensity=20.0, gradient=2.0),
        )
        model.regional_stress = rs

        result = compute_grid(model)
        assert result.oops_strike is not None
        assert result.oops_dip is not None
        assert result.oops_rake is not None
        assert result.oops_strike.shape == result.cfs.shape
        assert np.all(np.isfinite(result.oops_strike))
        assert np.all(np.isfinite(result.oops_dip))
        assert np.all(result.oops_dip >= 0)
        assert np.all(result.oops_dip <= 90 + 1e-10)
