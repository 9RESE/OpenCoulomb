"""Unit tests for the OpenCoulomb strain output feature.

Covers:
1. gradients_to_strain — zero input, known values, symmetry, shape preservation
2. gradients_to_stress regression — refactor through gradients_to_strain must not
   change stress results
3. compute_grid with compute_strain=True — real .inp file, StrainResult populated,
   volumetric identity, correct array shape
4. compute_grid with compute_strain=False (default) — backward compatibility
5. StrainResult construction and field access
"""

from __future__ import annotations

import pathlib

import numpy as np
import pytest

from opencoulomb.core.stress import gradients_to_strain, gradients_to_stress
from opencoulomb.core.pipeline import compute_grid
from opencoulomb.io import read_inp
from opencoulomb.types.result import CoulombResult, StrainResult

# ---------------------------------------------------------------------------
# Paths and material constants
# ---------------------------------------------------------------------------

FIXTURES_DIR = pathlib.Path(__file__).parent.parent / "fixtures" / "inp_files" / "real"
SIMPLEST_RECEIVER_INP = FIXTURES_DIR / "simplest_receiver.inp"

# Default Coulomb material properties (match simplest_receiver.inp)
YOUNG = 8.0e5       # bar  (E1 = 0.800000E+06)
POISSON = 0.25      # PR1 = 0.250
KM_TO_M = 0.001     # Okada gradient unit conversion factor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lame_params(young: float, poisson: float) -> tuple[float, float]:
    """Return (lambda, mu) from Young's modulus and Poisson's ratio."""
    mu = young / (2.0 * (1.0 + poisson))
    lam = young * poisson / ((1.0 + poisson) * (1.0 - 2.0 * poisson))
    return lam, mu


# ---------------------------------------------------------------------------
# 1. gradients_to_strain
# ---------------------------------------------------------------------------


class TestGradientsToStrain:
    """Tests for gradients_to_strain()."""

    # ------------------------------------------------------------------
    # 1a. Zero gradients produce zero strain
    # ------------------------------------------------------------------

    def test_zero_gradients_zero_strain(self) -> None:
        """All-zero displacement gradients must produce zero strain in all components."""
        n = 8
        zeros = np.zeros(n)
        exx, eyy, ezz, eyz, exz, exy = gradients_to_strain(
            zeros, zeros, zeros,
            zeros, zeros, zeros,
            zeros, zeros, zeros,
        )
        for name, arr in [
            ("exx", exx), ("eyy", eyy), ("ezz", ezz),
            ("eyz", eyz), ("exz", exz), ("exy", exy),
        ]:
            np.testing.assert_array_equal(arr, 0.0, err_msg=f"{name} should be zero")

    # ------------------------------------------------------------------
    # 1b. Known input → expected strain values
    # ------------------------------------------------------------------

    def test_normal_strains_apply_km_to_m_factor(self) -> None:
        """Normal strains: eii = u_ii * 0.001 (unit conversion from m/km to dimensionless)."""
        n = 5
        val = 10.0  # m/km
        # Only diagonal gradients non-zero; set each independently
        uxx = np.full(n, val)
        uyy = np.full(n, val * 2.0)
        uzz = np.full(n, val * 3.0)
        zeros = np.zeros(n)

        exx, eyy, ezz, eyz, exz, exy = gradients_to_strain(
            uxx, zeros, zeros,   # uxx, uyx, uzx
            zeros, uyy, zeros,   # uxy, uyy, uzy
            zeros, zeros, uzz,   # uxz, uyz, uzz
        )

        np.testing.assert_allclose(exx, val * KM_TO_M, rtol=1e-14)
        np.testing.assert_allclose(eyy, val * 2.0 * KM_TO_M, rtol=1e-14)
        np.testing.assert_allclose(ezz, val * 3.0 * KM_TO_M, rtol=1e-14)
        # Off-diagonal should be zero when only diagonal gradients are set
        np.testing.assert_allclose(eyz, 0.0, atol=1e-20)
        np.testing.assert_allclose(exz, 0.0, atol=1e-20)
        np.testing.assert_allclose(exy, 0.0, atol=1e-20)

    def test_uniaxial_extension_in_x(self) -> None:
        """Single non-zero gradient uxx=1 → exx=0.001, all others zero."""
        n = 3
        uxx = np.ones(n)
        zeros = np.zeros(n)

        exx, eyy, ezz, eyz, exz, exy = gradients_to_strain(
            uxx, zeros, zeros,
            zeros, zeros, zeros,
            zeros, zeros, zeros,
        )

        np.testing.assert_allclose(exx, KM_TO_M, rtol=1e-14)
        np.testing.assert_allclose(eyy, 0.0, atol=1e-20)
        np.testing.assert_allclose(ezz, 0.0, atol=1e-20)
        np.testing.assert_allclose(eyz, 0.0, atol=1e-20)
        np.testing.assert_allclose(exz, 0.0, atol=1e-20)
        np.testing.assert_allclose(exy, 0.0, atol=1e-20)

    # ------------------------------------------------------------------
    # 1c. Symmetry: exy = 0.5*(uxy + uyx)*0.001
    # ------------------------------------------------------------------

    def test_shear_xy_symmetry(self) -> None:
        """exy must be the symmetric part: 0.5*(uxy + uyx) * 0.001."""
        n = 6
        uxy_val = 4.0   # m/km
        uyx_val = 6.0   # m/km (different from uxy to test averaging)
        zeros = np.zeros(n)
        uxy = np.full(n, uxy_val)
        uyx = np.full(n, uyx_val)

        _exx, _eyy, _ezz, _eyz, _exz, exy = gradients_to_strain(
            zeros, uyx, zeros,   # uxx, uyx, uzx
            uxy, zeros, zeros,   # uxy, uyy, uzy
            zeros, zeros, zeros, # uxz, uyz, uzz
        )

        expected_exy = 0.5 * (uxy_val + uyx_val) * KM_TO_M
        np.testing.assert_allclose(exy, expected_exy, rtol=1e-14)

    def test_shear_yz_symmetry(self) -> None:
        """eyz must be the symmetric part: 0.5*(uyz + uzy) * 0.001."""
        n = 4
        uyz_val = 3.0
        uzy_val = 7.0
        zeros = np.zeros(n)
        uyz = np.full(n, uyz_val)
        uzy = np.full(n, uzy_val)

        _exx, _eyy, _ezz, eyz, _exz, _exy = gradients_to_strain(
            zeros, zeros, zeros,
            zeros, zeros, uzy,   # uxy, uyy, uzy
            zeros, uyz, zeros,   # uxz, uyz, uzz
        )

        expected_eyz = 0.5 * (uyz_val + uzy_val) * KM_TO_M
        np.testing.assert_allclose(eyz, expected_eyz, rtol=1e-14)

    def test_shear_xz_symmetry(self) -> None:
        """exz must be the symmetric part: 0.5*(uxz + uzx) * 0.001."""
        n = 4
        uxz_val = 2.0
        uzx_val = 8.0
        zeros = np.zeros(n)
        uxz = np.full(n, uxz_val)
        uzx = np.full(n, uzx_val)

        _exx, _eyy, _ezz, _eyz, exz, _exy = gradients_to_strain(
            zeros, zeros, uzx,   # uxx, uyx, uzx
            zeros, zeros, zeros,
            uxz, zeros, zeros,   # uxz, uyz, uzz
        )

        expected_exz = 0.5 * (uxz_val + uzx_val) * KM_TO_M
        np.testing.assert_allclose(exz, expected_exz, rtol=1e-14)

    def test_antisymmetric_shear_produces_half(self) -> None:
        """uxy = -uyx → exy = 0 (pure rotation, no shear strain)."""
        n = 3
        val = 5.0
        zeros = np.zeros(n)
        uxy = np.full(n, val)
        uyx = np.full(n, -val)

        _exx, _eyy, _ezz, _eyz, _exz, exy = gradients_to_strain(
            zeros, uyx, zeros,
            uxy, zeros, zeros,
            zeros, zeros, zeros,
        )

        # Pure rotation: symmetric strain = 0
        np.testing.assert_allclose(exy, 0.0, atol=1e-20)

    # ------------------------------------------------------------------
    # 1d. Shape preservation: arrays in, same-shape arrays out
    # ------------------------------------------------------------------

    def test_shape_preserved_1d(self) -> None:
        """Output arrays have the same shape as input arrays."""
        n = 12
        rng = np.random.default_rng(0)
        grads = [rng.standard_normal(n) for _ in range(9)]

        result = gradients_to_strain(*grads)

        assert len(result) == 6
        for comp in result:
            assert comp.shape == (n,), f"Expected shape ({n},), got {comp.shape}"

    def test_shape_preserved_scalar_array(self) -> None:
        """Single-element input arrays produce single-element output."""
        ones = np.ones(1)
        zeros = np.zeros(1)
        result = gradients_to_strain(
            ones, zeros, zeros,
            zeros, ones, zeros,
            zeros, zeros, ones,
        )
        for comp in result:
            assert comp.shape == (1,)

    def test_output_dtype_float64(self) -> None:
        """Output components should be float64."""
        n = 4
        grads = [np.ones(n, dtype=np.float64) for _ in range(9)]
        result = gradients_to_strain(*grads)
        for comp in result:
            assert comp.dtype == np.float64


# ---------------------------------------------------------------------------
# 2. gradients_to_stress regression (refactor must not change results)
# ---------------------------------------------------------------------------


class TestGradientsToStressRegression:
    """Regression tests ensuring the gradients_to_stress refactor (which now
    delegates to gradients_to_strain internally) produces identical results
    to the expected analytical values.
    """

    def test_zero_input_still_zero(self) -> None:
        """Zero gradients → zero stress, same as before refactor."""
        n = 5
        zeros = np.zeros(n)
        sxx, syy, szz, syz, sxz, sxy = gradients_to_stress(
            zeros, zeros, zeros,
            zeros, zeros, zeros,
            zeros, zeros, zeros,
            YOUNG, POISSON,
        )
        for name, arr in [
            ("sxx", sxx), ("syy", syy), ("szz", szz),
            ("syz", syz), ("sxz", sxz), ("sxy", sxy),
        ]:
            np.testing.assert_allclose(arr, 0.0, atol=1e-20, err_msg=name)

    def test_uniaxial_x_hookes_law(self) -> None:
        """uxx=grad_val, all others zero → analytical Hooke's law result.

        This acts as a regression test: the result must equal the hand-computed
        values regardless of whether gradients_to_stress calls gradients_to_strain
        internally or implements the strain inline.
        """
        lam, mu = _lame_params(YOUNG, POISSON)
        grad_val = 5.0
        strain = grad_val * KM_TO_M

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
        np.testing.assert_allclose(syz, 0.0, atol=1e-15)
        np.testing.assert_allclose(sxz, 0.0, atol=1e-15)
        np.testing.assert_allclose(sxy, 0.0, atol=1e-15)

    def test_pure_shear_xy_hookes_law(self) -> None:
        """uxy=uyx=v → sxy = 2*mu * exy, normal stresses zero."""
        _lam, mu = _lame_params(YOUNG, POISSON)
        val = 8.0
        n = 4
        uxy = np.full(n, val)
        uyx = np.full(n, val)
        zeros = np.zeros(n)

        _sxx, _syy, _szz, _syz, _sxz, sxy = gradients_to_stress(
            zeros, uyx, zeros,
            uxy, zeros, zeros,
            zeros, zeros, zeros,
            YOUNG, POISSON,
        )

        expected = 2.0 * mu * 0.5 * (val + val) * KM_TO_M
        np.testing.assert_allclose(sxy, expected, rtol=1e-12)

    def test_stress_consistent_with_strain(self) -> None:
        """Verify stress and strain are consistent via Hooke's law.

        sigma = lambda*tr(e)*I + 2*mu*e.  Test with a general gradient set.
        """
        lam, mu = _lame_params(YOUNG, POISSON)
        n = 7
        rng = np.random.default_rng(42)
        grads = [rng.uniform(-5.0, 5.0, n) for _ in range(9)]
        uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz = grads

        exx, eyy, ezz, eyz, exz, exy = gradients_to_strain(
            uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz,
        )
        sxx, syy, szz, syz, sxz, sxy = gradients_to_stress(
            uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz,
            YOUNG, POISSON,
        )

        vol = exx + eyy + ezz
        np.testing.assert_allclose(sxx, lam * vol + 2.0 * mu * exx, rtol=1e-12)
        np.testing.assert_allclose(syy, lam * vol + 2.0 * mu * eyy, rtol=1e-12)
        np.testing.assert_allclose(szz, lam * vol + 2.0 * mu * ezz, rtol=1e-12)
        np.testing.assert_allclose(syz, 2.0 * mu * eyz, rtol=1e-12)
        np.testing.assert_allclose(sxz, 2.0 * mu * exz, rtol=1e-12)
        np.testing.assert_allclose(sxy, 2.0 * mu * exy, rtol=1e-12)

    def test_invalid_poisson_still_raises(self) -> None:
        """gradients_to_stress must still validate Poisson's ratio."""
        n = 2
        zeros = np.zeros(n)
        with pytest.raises(ValueError, match="Poisson"):
            gradients_to_stress(
                zeros, zeros, zeros,
                zeros, zeros, zeros,
                zeros, zeros, zeros,
                YOUNG, 0.6,  # invalid: > 0.5
            )

    def test_invalid_young_still_raises(self) -> None:
        """gradients_to_stress must still validate Young's modulus."""
        n = 2
        zeros = np.zeros(n)
        with pytest.raises(ValueError, match="Young"):
            gradients_to_stress(
                zeros, zeros, zeros,
                zeros, zeros, zeros,
                zeros, zeros, zeros,
                -1.0, POISSON,
            )


# ---------------------------------------------------------------------------
# 3. compute_grid with compute_strain=True
# ---------------------------------------------------------------------------


class TestComputeGridWithStrain:
    """Integration tests for compute_grid(model, compute_strain=True).

    Uses the real simplest_receiver.inp fixture so that the full pipeline
    (parse → Okada → stress → CFS → strain) is exercised end-to-end.
    """

    @pytest.fixture(scope="class")
    def model(self):
        """Load and cache the simplest_receiver model once for the test class."""
        return read_inp(SIMPLEST_RECEIVER_INP)

    @pytest.fixture(scope="class")
    def result_with_strain(self, model):
        """Run compute_grid with compute_strain=True."""
        return compute_grid(model, compute_strain=True)

    def test_strain_not_none_when_requested(self, result_with_strain: CoulombResult) -> None:
        """CoulombResult.strain must not be None when compute_strain=True."""
        assert result_with_strain.strain is not None

    def test_strain_is_strain_result_instance(self, result_with_strain: CoulombResult) -> None:
        """The strain attribute must be a StrainResult dataclass instance."""
        assert isinstance(result_with_strain.strain, StrainResult)

    def test_volumetric_equals_sum_of_normals(self, result_with_strain: CoulombResult) -> None:
        """volumetric strain must equal exx + eyy + ezz at every grid point."""
        s = result_with_strain.strain
        assert s is not None
        np.testing.assert_allclose(
            s.volumetric,
            s.exx + s.eyy + s.ezz,
            rtol=1e-12,
            err_msg="volumetric != exx + eyy + ezz",
        )

    def test_strain_arrays_have_correct_shape(self, result_with_strain: CoulombResult) -> None:
        """All strain arrays must have the same flat shape as the grid."""
        s = result_with_strain.strain
        assert s is not None
        n_y, n_x = result_with_strain.grid_shape
        expected_n = n_y * n_x
        for field in ("exx", "eyy", "ezz", "eyz", "exz", "exy", "volumetric"):
            arr = getattr(s, field)
            assert arr.shape == (expected_n,), (
                f"strain.{field}: expected shape ({expected_n},), got {arr.shape}"
            )

    def test_strain_arrays_are_finite(self, result_with_strain: CoulombResult) -> None:
        """All strain components must be finite (no NaN or Inf)."""
        s = result_with_strain.strain
        assert s is not None
        for field in ("exx", "eyy", "ezz", "eyz", "exz", "exy", "volumetric"):
            arr = getattr(s, field)
            assert np.all(np.isfinite(arr)), f"strain.{field} contains non-finite values"

    def test_strain_not_all_zero(self, result_with_strain: CoulombResult) -> None:
        """Strain should have non-trivial values near the source fault."""
        s = result_with_strain.strain
        assert s is not None
        # At least one component should have a non-negligible magnitude
        max_strain = max(
            np.max(np.abs(s.exx)),
            np.max(np.abs(s.eyy)),
            np.max(np.abs(s.ezz)),
        )
        assert max_strain > 1e-20, "All strain components are effectively zero"

    def test_strain_matches_inverse_hookes_law(self, result_with_strain: CoulombResult) -> None:
        """Strain from inverse Hooke's law must be self-consistent with the stress field.

        Verify: exx + eyy + ezz = (1 - 2*nu)/E * (sxx + syy + szz).
        This is the trace relationship from isotropic linear elasticity.
        """
        s = result_with_strain.strain
        stress = result_with_strain.stress
        assert s is not None

        nu = POISSON
        e = YOUNG
        sigma_kk = stress.sxx + stress.syy + stress.szz
        expected_vol = (1.0 - 2.0 * nu) / e * sigma_kk

        np.testing.assert_allclose(
            s.volumetric,
            expected_vol,
            rtol=1e-10,
            err_msg="Volumetric strain inconsistent with inverse Hooke's law",
        )


# ---------------------------------------------------------------------------
# 4. compute_grid with compute_strain=False (default) — backward compatibility
# ---------------------------------------------------------------------------


class TestComputeGridWithoutStrain:
    """Ensure that strain output is optional and off by default."""

    @pytest.fixture(scope="class")
    def model(self):
        return read_inp(SIMPLEST_RECEIVER_INP)

    def test_strain_is_none_by_default(self, model) -> None:
        """When compute_strain is not passed, result.strain must be None."""
        result = compute_grid(model)
        assert result.strain is None

    def test_strain_is_none_when_explicitly_false(self, model) -> None:
        """When compute_strain=False is explicit, result.strain must be None."""
        result = compute_grid(model, compute_strain=False)
        assert result.strain is None

    def test_cfs_unaffected_by_compute_strain_flag(self, model) -> None:
        """CFS values must be identical whether or not compute_strain is True."""
        result_no_strain = compute_grid(model, compute_strain=False)
        result_with_strain = compute_grid(model, compute_strain=True)

        np.testing.assert_array_equal(
            result_no_strain.cfs,
            result_with_strain.cfs,
            err_msg="CFS changed when compute_strain flag was toggled",
        )


# ---------------------------------------------------------------------------
# 5. StrainResult construction and field access
# ---------------------------------------------------------------------------


class TestStrainResultDataclass:
    """Tests for the StrainResult dataclass itself."""

    def test_construction_with_numpy_arrays(self) -> None:
        """StrainResult can be constructed with NumPy arrays."""
        n = 10
        rng = np.random.default_rng(99)
        arrs = {
            "exx": rng.standard_normal(n),
            "eyy": rng.standard_normal(n),
            "ezz": rng.standard_normal(n),
            "eyz": rng.standard_normal(n),
            "exz": rng.standard_normal(n),
            "exy": rng.standard_normal(n),
            "volumetric": rng.standard_normal(n),
        }
        sr = StrainResult(**arrs)
        assert isinstance(sr, StrainResult)

    def test_all_fields_accessible(self) -> None:
        """All seven fields of StrainResult must be individually accessible."""
        n = 4
        exx = np.array([1.0, 2.0, 3.0, 4.0])
        eyy = np.array([0.1, 0.2, 0.3, 0.4])
        ezz = np.array([-1.0, -2.0, -3.0, -4.0])
        eyz = np.array([0.5, 0.6, 0.7, 0.8])
        exz = np.array([-0.5, -0.6, -0.7, -0.8])
        exy = np.array([0.01, 0.02, 0.03, 0.04])
        vol = exx + eyy + ezz

        sr = StrainResult(exx=exx, eyy=eyy, ezz=ezz, eyz=eyz, exz=exz, exy=exy, volumetric=vol)

        np.testing.assert_array_equal(sr.exx, exx)
        np.testing.assert_array_equal(sr.eyy, eyy)
        np.testing.assert_array_equal(sr.ezz, ezz)
        np.testing.assert_array_equal(sr.eyz, eyz)
        np.testing.assert_array_equal(sr.exz, exz)
        np.testing.assert_array_equal(sr.exy, exy)
        np.testing.assert_array_equal(sr.volumetric, vol)

    def test_strain_result_is_not_frozen(self) -> None:
        """StrainResult uses slots=True but is not declared frozen, so attributes
        can be reassigned — this test just confirms construction works with any
        shape of array."""
        n = 1
        z = np.zeros(n)
        sr = StrainResult(exx=z, eyy=z, ezz=z, eyz=z, exz=z, exy=z, volumetric=z)
        assert sr.exx.shape == (n,)

    def test_coulomb_result_strain_field_default_none(self) -> None:
        """CoulombResult.strain defaults to None when not provided."""
        from opencoulomb.types.result import StressResult

        n = 2
        z = np.zeros(n)
        stress = StressResult(
            x=z, y=z, z=z,
            ux=z, uy=z, uz=z,
            sxx=z, syy=z, szz=z,
            syz=z, sxz=z, sxy=z,
        )
        result = CoulombResult(
            stress=stress,
            cfs=z,
            shear=z,
            normal=z,
            receiver_strike=0.0,
            receiver_dip=90.0,
            receiver_rake=0.0,
            grid_shape=(1, 2),
        )
        assert result.strain is None
