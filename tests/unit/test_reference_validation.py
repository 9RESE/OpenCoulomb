"""Coulomb 3.4 reference validation tests.

These tests compare OpenCoulomb's full pipeline output against known
Coulomb 3.4 results for benchmark .inp files. They are marked with
``pytest.mark.reference`` and ``pytest.mark.skip`` until reference
values are extracted from Coulomb 3.4 MATLAB runs.

Finding 3 of the Phase C/D code review.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

TESTS_DIR = Path(__file__).parent.parent
REAL_INP_DIR = TESTS_DIR / "fixtures" / "inp_files" / "real"

reference = pytest.mark.reference


def _skip_if_missing(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"Fixture not available: {path.name}")


# ---------------------------------------------------------------------------
# Grid CFS reference validation
# ---------------------------------------------------------------------------


@reference
class TestGridCFSReference:
    """Compare compute_grid CFS output against Coulomb 3.4 reference values."""

    @pytest.mark.skip(reason="Awaiting Coulomb 3.4 reference CFS values for simplest_receiver.inp")
    def test_simplest_receiver_cfs_peak(self) -> None:
        """Peak CFS value at grid center should match Coulomb 3.4 within 1e-6 bar."""
        from opencoulomb.core import compute_grid
        from opencoulomb.io import read_inp

        inp_path = REAL_INP_DIR / "simplest_receiver.inp"
        _skip_if_missing(inp_path)

        model = read_inp(inp_path)
        result = compute_grid(model)

        # TODO: Replace with actual Coulomb 3.4 reference value
        expected_peak_cfs = 0.0  # placeholder
        assert np.max(np.abs(result.cfs)) == pytest.approx(expected_peak_cfs, abs=1e-6)

    @pytest.mark.skip(reason="Awaiting Coulomb 3.4 reference CFS values for simple_receiver_bm.inp")
    def test_simple_receiver_bm_cfs_range(self) -> None:
        """CFS min/max should match Coulomb 3.4 within 1e-6 bar."""
        from opencoulomb.core import compute_grid
        from opencoulomb.io import read_inp

        inp_path = REAL_INP_DIR / "simple_receiver_bm.inp"
        _skip_if_missing(inp_path)

        model = read_inp(inp_path)
        result = compute_grid(model)

        # TODO: Replace with actual Coulomb 3.4 reference values
        expected_min_cfs = 0.0  # placeholder
        expected_max_cfs = 0.0  # placeholder
        assert np.min(result.cfs) == pytest.approx(expected_min_cfs, abs=1e-6)
        assert np.max(result.cfs) == pytest.approx(expected_max_cfs, abs=1e-6)

    @pytest.mark.skip(reason="Awaiting Coulomb 3.4 reference displacement values")
    def test_simplest_receiver_displacement(self) -> None:
        """Peak displacement should match Coulomb 3.4 within 1e-8 m."""
        from opencoulomb.core import compute_grid
        from opencoulomb.io import read_inp

        inp_path = REAL_INP_DIR / "simplest_receiver.inp"
        _skip_if_missing(inp_path)

        model = read_inp(inp_path)
        result = compute_grid(model)

        # TODO: Replace with actual Coulomb 3.4 reference values
        expected_peak_ux = 0.0  # placeholder
        expected_peak_uy = 0.0  # placeholder
        expected_peak_uz = 0.0  # placeholder
        assert np.max(np.abs(result.stress.ux)) == pytest.approx(expected_peak_ux, abs=1e-8)
        assert np.max(np.abs(result.stress.uy)) == pytest.approx(expected_peak_uy, abs=1e-8)
        assert np.max(np.abs(result.stress.uz)) == pytest.approx(expected_peak_uz, abs=1e-8)


# ---------------------------------------------------------------------------
# Cross-section reference validation
# ---------------------------------------------------------------------------


@reference
class TestCrossSectionReference:
    """Compare compute_cross_section output against Coulomb 3.4 reference."""

    @pytest.mark.skip(reason="Awaiting Coulomb 3.4 cross-section CFS reference values")
    def test_cross_section_cfs(self) -> None:
        """Cross-section CFS should match Coulomb 3.4 at selected depth slices."""
        from opencoulomb.core import compute_cross_section
        from opencoulomb.io import read_inp

        inp_path = REAL_INP_DIR / "simplest_receiver.inp"
        _skip_if_missing(inp_path)

        model = read_inp(inp_path)
        # Only models with cross_section spec can be tested
        if model.cross_section is None:
            pytest.skip("Model has no cross-section spec")

        cs_result = compute_cross_section(model)

        # TODO: Replace with actual Coulomb 3.4 cross-section reference values
        # Check CFS at center of cross-section
        mid_h = cs_result.cfs.shape[1] // 2
        mid_v = cs_result.cfs.shape[0] // 2
        expected_center_cfs = 0.0  # placeholder
        assert cs_result.cfs[mid_v, mid_h] == pytest.approx(expected_center_cfs, abs=1e-6)

    @pytest.mark.skip(reason="Awaiting Coulomb 3.4 cross-section stress reference values")
    def test_cross_section_stress_components(self) -> None:
        """Cross-section stress tensor components should match Coulomb 3.4."""
        from opencoulomb.core import compute_cross_section
        from opencoulomb.io import read_inp

        inp_path = REAL_INP_DIR / "simplest_receiver.inp"
        _skip_if_missing(inp_path)

        model = read_inp(inp_path)
        if model.cross_section is None:
            pytest.skip("Model has no cross-section spec")

        cs_result = compute_cross_section(model)

        # TODO: Replace with Coulomb 3.4 reference stress tensor values
        # Verify at a known point (e.g., shallow depth directly above fault)
        expected_sxx = 0.0  # placeholder
        assert cs_result.sxx[0, cs_result.cfs.shape[1] // 2] == pytest.approx(
            expected_sxx, abs=1e-6
        )


# ---------------------------------------------------------------------------
# OOPs (Optimally Oriented Planes) reference validation
# ---------------------------------------------------------------------------


@reference
class TestOOPsReference:
    """Compare OOPs-derived receiver orientations against Coulomb 3.4."""

    @pytest.mark.skip(reason="Awaiting Coulomb 3.4 OOPs reference values")
    def test_oops_max_cfs(self) -> None:
        """OOPs CFS (no fixed receiver) should match Coulomb 3.4."""
        from opencoulomb.core import compute_grid
        from opencoulomb.io import read_inp

        inp_path = REAL_INP_DIR / "simplest_receiver.inp"
        _skip_if_missing(inp_path)

        model = read_inp(inp_path)
        # OOPs = compute with no receiver (uses optimally-oriented planes)
        result = compute_grid(model, receiver_index=None)

        # TODO: Replace with Coulomb 3.4 OOPs peak CFS
        expected_peak_oops = 0.0  # placeholder
        assert np.max(np.abs(result.cfs)) == pytest.approx(expected_peak_oops, abs=1e-6)

    @pytest.mark.skip(reason="Awaiting Coulomb 3.4 multi-fault reference values")
    def test_multi_fault_cfs(self) -> None:
        """Multi-fault model CFS should match Coulomb 3.4."""
        from opencoulomb.core import compute_grid
        from opencoulomb.io import read_inp

        inp_path = REAL_INP_DIR / "M6.5.inp"
        _skip_if_missing(inp_path)

        model = read_inp(inp_path)
        result = compute_grid(model)

        # TODO: Replace with Coulomb 3.4 reference values for M6.5
        expected_peak_cfs = 0.0  # placeholder
        assert np.max(np.abs(result.cfs)) == pytest.approx(expected_peak_cfs, abs=1e-6)
