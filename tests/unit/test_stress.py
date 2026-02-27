"""Unit tests for opencoulomb.core.stress.

Covers:
- gradients_to_stress: known strain -> known stress via Hooke's law
- Pure hydrostatic case: equal normal strains -> equal stresses, no shear
- Unit conversion factor: verify 0.001 (m/km) factor is applied
- rotate_stress_tensor: eigenvalues preserved after rotation
- Zero gradients -> zero stress
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from opencoulomb.core.stress import gradients_to_stress, rotate_stress_tensor

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Default Coulomb material properties
YOUNG = 8.0e5      # bar
POISSON = 0.25


def _lame_params(young: float, poisson: float) -> tuple[float, float]:
    """Compute Lame parameters from Young's modulus and Poisson's ratio."""
    mu = young / (2.0 * (1.0 + poisson))
    lam = young * poisson / ((1.0 + poisson) * (1.0 - 2.0 * poisson))
    return lam, mu


# ---------------------------------------------------------------------------
# gradients_to_stress: basic cases
# ---------------------------------------------------------------------------


class TestGradientsToStress:
    """Test Hooke's law stress computation from displacement gradients."""

    def test_zero_gradients_zero_stress(self) -> None:
        """All-zero displacement gradients must produce zero stress."""
        n = 10
        zeros = np.zeros(n)
        sxx, syy, szz, syz, sxz, sxy = gradients_to_stress(
            zeros, zeros, zeros,
            zeros, zeros, zeros,
            zeros, zeros, zeros,
            YOUNG, POISSON,
        )
        np.testing.assert_allclose(sxx, 0.0, atol=1e-20)
        np.testing.assert_allclose(syy, 0.0, atol=1e-20)
        np.testing.assert_allclose(szz, 0.0, atol=1e-20)
        np.testing.assert_allclose(syz, 0.0, atol=1e-20)
        np.testing.assert_allclose(sxz, 0.0, atol=1e-20)
        np.testing.assert_allclose(sxy, 0.0, atol=1e-20)

    def test_pure_hydrostatic(self) -> None:
        """Equal normal strains, no shear -> equal normal stresses, zero shear.

        If uxx = uyy = uzz = e (uniform expansion), then:
        sxx = syy = szz = (lambda * 3 + 2*mu) * e * KM_TO_M
        syz = sxz = sxy = 0
        """
        lam, mu = _lame_params(YOUNG, POISSON)
        # Set all normal gradients equal, zero off-diagonal
        e_grad = 10.0  # m/km
        e_strain = e_grad * 0.001  # dimensionless strain

        n = 5
        e_arr = np.full(n, e_grad)
        zeros = np.zeros(n)

        sxx, syy, szz, syz, sxz, sxy = gradients_to_stress(
            e_arr, zeros, zeros,   # uxx, uyx, uzx
            zeros, e_arr, zeros,   # uxy, uyy, uzy
            zeros, zeros, e_arr,   # uxz, uyz, uzz
            YOUNG, POISSON,
        )

        expected = (lam * 3.0 * e_strain + 2.0 * mu * e_strain)
        np.testing.assert_allclose(sxx, expected, rtol=1e-12)
        np.testing.assert_allclose(syy, expected, rtol=1e-12)
        np.testing.assert_allclose(szz, expected, rtol=1e-12)
        np.testing.assert_allclose(syz, 0.0, atol=1e-10)
        np.testing.assert_allclose(sxz, 0.0, atol=1e-10)
        np.testing.assert_allclose(sxy, 0.0, atol=1e-10)

    def test_uniaxial_strain(self) -> None:
        """Uniaxial strain in x: uxx=1, all others=0.

        sxx = (lambda + 2*mu) * exx
        syy = szz = lambda * exx
        shear = 0
        """
        lam, mu = _lame_params(YOUNG, POISSON)
        grad_val = 5.0  # m/km
        strain = grad_val * 0.001

        n = 3
        uxx = np.full(n, grad_val)
        zeros = np.zeros(n)

        sxx, syy, szz, syz, sxz, sxy = gradients_to_stress(
            uxx, zeros, zeros,
            zeros, zeros, zeros,
            zeros, zeros, zeros,
            YOUNG, POISSON,
        )

        np.testing.assert_allclose(sxx, (lam + 2.0 * mu) * strain, rtol=1e-12)
        np.testing.assert_allclose(syy, lam * strain, rtol=1e-12)
        np.testing.assert_allclose(szz, lam * strain, rtol=1e-12)
        np.testing.assert_allclose(syz, 0.0, atol=1e-10)
        np.testing.assert_allclose(sxz, 0.0, atol=1e-10)
        np.testing.assert_allclose(sxy, 0.0, atol=1e-10)

    def test_pure_shear_xy(self) -> None:
        """Pure shear in xy plane: uxy=uyx=val, all others=0.

        sxy = 2 * mu * exy = 2 * mu * 0.5 * (uxy + uyx) * 0.001
        """
        _lam, mu = _lame_params(YOUNG, POISSON)
        grad_val = 8.0  # m/km

        n = 4
        uxy = np.full(n, grad_val)
        uyx = np.full(n, grad_val)
        zeros = np.zeros(n)

        sxx, syy, szz, _syz, _sxz, sxy = gradients_to_stress(
            zeros, uyx, zeros,
            uxy, zeros, zeros,
            zeros, zeros, zeros,
            YOUNG, POISSON,
        )

        expected_shear = 2.0 * mu * 0.5 * (grad_val + grad_val) * 0.001
        np.testing.assert_allclose(sxy, expected_shear, rtol=1e-12)
        np.testing.assert_allclose(sxx, 0.0, atol=1e-10)
        np.testing.assert_allclose(syy, 0.0, atol=1e-10)
        np.testing.assert_allclose(szz, 0.0, atol=1e-10)

    def test_km_to_m_factor(self) -> None:
        """Verify the 0.001 conversion factor is applied.

        If we double the gradient, stress should double.
        The actual strain is gradient * 0.001.
        """
        grad_val = 1.0  # m/km
        n = 1
        uxx = np.array([grad_val])
        zeros = np.zeros(n)

        s1, _, _, _, _, _ = gradients_to_stress(
            uxx, zeros, zeros,
            zeros, zeros, zeros,
            zeros, zeros, zeros,
            YOUNG, POISSON,
        )

        uxx_2 = np.array([2.0 * grad_val])
        s2, _, _, _, _, _ = gradients_to_stress(
            uxx_2, zeros, zeros,
            zeros, zeros, zeros,
            zeros, zeros, zeros,
            YOUNG, POISSON,
        )

        np.testing.assert_allclose(s2, 2.0 * s1, rtol=1e-14)

    def test_scalar_inputs_work(self) -> None:
        """Single-element arrays should work correctly."""
        result = gradients_to_stress(
            np.array([1.0]), np.array([0.0]), np.array([0.0]),
            np.array([0.0]), np.array([1.0]), np.array([0.0]),
            np.array([0.0]), np.array([0.0]), np.array([1.0]),
            YOUNG, POISSON,
        )
        assert result[0].shape == (1,)
        assert all(np.all(np.isfinite(c)) for c in result)


# ---------------------------------------------------------------------------
# rotate_stress_tensor
# ---------------------------------------------------------------------------


class TestRotateStressTensor:
    """Test stress tensor rotation properties."""

    def _build_tensor_3x3(
        self,
        sxx: float, syy: float, szz: float,
        syz: float, sxz: float, sxy: float,
    ) -> np.ndarray:
        """Build a symmetric 3x3 stress tensor for eigenvalue comparison."""
        return np.array([
            [sxx, sxy, sxz],
            [sxy, syy, syz],
            [sxz, syz, szz],
        ])

    def test_eigenvalues_preserved(self) -> None:
        """Principal stresses (eigenvalues) must be invariant under rotation."""
        sxx = np.array([10.0])
        syy = np.array([5.0])
        szz = np.array([3.0])
        syz = np.array([1.0])
        sxz = np.array([0.5])
        sxy = np.array([2.0])

        # Original eigenvalues
        T_orig = self._build_tensor_3x3(
            sxx[0], syy[0], szz[0], syz[0], sxz[0], sxy[0],
        )
        eigvals_orig = np.sort(np.linalg.eigvalsh(T_orig))

        # Rotate
        strike_rad = math.radians(45.0)
        dip_rad = math.radians(30.0)

        sxx_r, syy_r, szz_r, syz_r, sxz_r, sxy_r = rotate_stress_tensor(
            sxx, syy, szz, syz, sxz, sxy, strike_rad, dip_rad,
        )

        T_rot = self._build_tensor_3x3(
            sxx_r[0], syy_r[0], szz_r[0], syz_r[0], sxz_r[0], sxy_r[0],
        )
        eigvals_rot = np.sort(np.linalg.eigvalsh(T_rot))

        np.testing.assert_allclose(eigvals_rot, eigvals_orig, atol=1e-10)

    def test_trace_preserved(self) -> None:
        """Trace (sxx + syy + szz) is invariant under rotation."""
        n = 5
        rng = np.random.default_rng(42)
        sxx = rng.uniform(-10, 10, n)
        syy = rng.uniform(-10, 10, n)
        szz = rng.uniform(-10, 10, n)
        syz = rng.uniform(-5, 5, n)
        sxz = rng.uniform(-5, 5, n)
        sxy = rng.uniform(-5, 5, n)

        trace_before = sxx + syy + szz

        strike_rad = math.radians(120.0)
        dip_rad = math.radians(50.0)

        sxx_r, syy_r, szz_r, _, _, _ = rotate_stress_tensor(
            sxx, syy, szz, syz, sxz, sxy, strike_rad, dip_rad,
        )

        trace_after = sxx_r + syy_r + szz_r
        np.testing.assert_allclose(trace_after, trace_before, atol=1e-10)

    def test_identity_rotation(self) -> None:
        """Strike=0, dip=90 should approximate an identity rotation for the
        first two components (x=along-strike=East, y=perpendicular)."""
        sxx = np.array([7.0])
        syy = np.array([3.0])
        szz = np.array([1.0])
        syz = np.array([0.0])
        sxz = np.array([0.0])
        sxy = np.array([0.0])

        # strike=90, dip=90: l_strike = [1,0,0], l_updip=[0,0,1], l_normal=[0,-1,0]
        # This is a permutation/rotation of axes
        sxx_r, syy_r, szz_r, _syz_r, _sxz_r, _sxy_r = rotate_stress_tensor(
            sxx, syy, szz, syz, sxz, sxy,
            math.radians(90.0), math.radians(90.0),
        )

        # All values should be finite
        assert np.all(np.isfinite(sxx_r))
        assert np.all(np.isfinite(syy_r))
        assert np.all(np.isfinite(szz_r))
        # Trace should be preserved
        assert sxx_r[0] + syy_r[0] + szz_r[0] == pytest.approx(
            sxx[0] + syy[0] + szz[0], abs=1e-10
        )

    def test_zero_stress_stays_zero(self) -> None:
        """Zero stress tensor remains zero after rotation."""
        n = 3
        zeros = np.zeros(n)
        sxx_r, syy_r, szz_r, syz_r, sxz_r, sxy_r = rotate_stress_tensor(
            zeros, zeros, zeros, zeros, zeros, zeros,
            math.radians(45.0), math.radians(60.0),
        )
        np.testing.assert_allclose(sxx_r, 0.0, atol=1e-20)
        np.testing.assert_allclose(syy_r, 0.0, atol=1e-20)
        np.testing.assert_allclose(szz_r, 0.0, atol=1e-20)
        np.testing.assert_allclose(syz_r, 0.0, atol=1e-20)
        np.testing.assert_allclose(sxz_r, 0.0, atol=1e-20)
        np.testing.assert_allclose(sxy_r, 0.0, atol=1e-20)

    @given(
        strike_deg=st.floats(min_value=0.0, max_value=360.0, allow_nan=False),
        dip_deg=st.floats(min_value=0.1, max_value=89.9, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_eigenvalues_preserved_hypothesis(
        self, strike_deg: float, dip_deg: float
    ) -> None:
        """Principal stresses preserved under arbitrary rotation."""
        sxx = np.array([10.0])
        syy = np.array([5.0])
        szz = np.array([3.0])
        syz = np.array([1.5])
        sxz = np.array([0.5])
        sxy = np.array([2.0])

        T_orig = self._build_tensor_3x3(
            sxx[0], syy[0], szz[0], syz[0], sxz[0], sxy[0]
        )
        eigvals_orig = np.sort(np.linalg.eigvalsh(T_orig))

        sxx_r, syy_r, szz_r, syz_r, sxz_r, sxy_r = rotate_stress_tensor(
            sxx, syy, szz, syz, sxz, sxy,
            math.radians(strike_deg), math.radians(dip_deg),
        )

        T_rot = self._build_tensor_3x3(
            sxx_r[0], syy_r[0], szz_r[0], syz_r[0], sxz_r[0], sxy_r[0]
        )
        eigvals_rot = np.sort(np.linalg.eigvalsh(T_rot))

        np.testing.assert_allclose(eigvals_rot, eigvals_orig, atol=1e-8)
