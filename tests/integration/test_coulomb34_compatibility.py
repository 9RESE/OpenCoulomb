"""Compatibility tests for all Coulomb 3.4 distribution example files.

Validates that every .inp file shipped with the official Coulomb 3.4
distribution (coulomb3402.zip) can be parsed and computed by OpenCoulomb.

Source: https://coulomb.s3.us-west-2.amazonaws.com/downloads/coulomb3402.zip
        coulomb3402/input_file/ (20 files)

Additionally tests 3 USGS finite-fault .inp files from the Earthquake
Hazards Program archive (https://earthquake.usgs.gov/data/finitefault/).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import numpy as np
import pytest

from opencoulomb.core.pipeline import compute_grid
from opencoulomb.io import read_inp

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Coulomb 3.4 distribution examples (20 files)
# ---------------------------------------------------------------------------


class TestCoulomb34Distribution:
    """Parse and compute all 20 Coulomb 3.4 distribution example files."""

    FILES: ClassVar[list[str]] = [
        "Example-1.inp",
        "Example-2_LL_.inp",
        "Example-2_LL__lonlat.inp",
        "Example-2_LL__surface.inp",
        "Example-2_TH_.inp",
        "Example-2_TH__lonlat.inp",
        "Example-2_TH__surface.inp",
        "Example_3.inp",
        "Example-6_200Kode_.inp",
        "Example-7_200-300kode_.inp",
        "Example-8_dike_.inp",
        "Example-9_Kode500_.inp",
        "Example-Kode400.inp",
        "Example-RL.inp",
        "Example-SFBayArea.inp",
        "Kobe_uniform_slip.inp",
        "Kobe_uniform_slip_receiver_faults.inp",
        "Kobe_variable_slip.inp",
        "Landers_uniform_slip.inp",
        "Landers_variable_slip.inp",
    ]

    @pytest.mark.parametrize("filename", FILES)
    def test_parses_without_error(
        self, filename: str, coulomb34_inp_dir: Path
    ) -> None:
        """File parses to a valid CoulombModel."""
        filepath = coulomb34_inp_dir / filename
        if not filepath.exists():
            pytest.skip(f"File not found: {filepath}")

        model = read_inp(filepath)
        assert model.n_sources > 0

    @pytest.mark.parametrize("filename", FILES)
    def test_compute_grid_no_error(
        self, filename: str, coulomb34_inp_dir: Path
    ) -> None:
        """Pipeline computes without NaN or Inf in CFS output."""
        filepath = coulomb34_inp_dir / filename
        if not filepath.exists():
            pytest.skip(f"File not found: {filepath}")

        model = read_inp(filepath)
        result = compute_grid(model)

        assert result is not None
        assert not np.any(np.isnan(result.cfs)), f"NaN in CFS for {filename}"
        assert not np.any(np.isinf(result.cfs)), f"Inf in CFS for {filename}"

    @pytest.mark.parametrize("filename", FILES)
    def test_grid_shape_positive(
        self, filename: str, coulomb34_inp_dir: Path
    ) -> None:
        """Grid shape has positive dimensions."""
        filepath = coulomb34_inp_dir / filename
        if not filepath.exists():
            pytest.skip(f"File not found: {filepath}")

        model = read_inp(filepath)
        result = compute_grid(model)

        n_y, n_x = result.grid_shape
        assert n_x > 0
        assert n_y > 0
        assert result.cfs.size == n_y * n_x

    @pytest.mark.parametrize("filename", FILES)
    def test_displacement_finite(
        self, filename: str, coulomb34_inp_dir: Path
    ) -> None:
        """All displacement components are finite."""
        filepath = coulomb34_inp_dir / filename
        if not filepath.exists():
            pytest.skip(f"File not found: {filepath}")

        model = read_inp(filepath)
        result = compute_grid(model)

        assert np.all(np.isfinite(result.stress.ux))
        assert np.all(np.isfinite(result.stress.uy))
        assert np.all(np.isfinite(result.stress.uz))


# ---------------------------------------------------------------------------
# USGS Finite-Fault archive files (3 files)
# ---------------------------------------------------------------------------


class TestUSGSFiniteFault:
    """Parse and compute USGS Earthquake Hazards Program finite-fault .inp files.

    These are real seismological inversions with hundreds of subfaults,
    testing parser robustness with large, complex models.
    """

    FILES: ClassVar[list[str]] = [
        "usgs_japan_M7.6.inp",
        "usgs_philippines_M7.4.inp",
        "usgs_russia_M7.8.inp",
    ]

    @pytest.mark.parametrize("filename", FILES)
    def test_parses_without_error(
        self, filename: str, usgs_ff_inp_dir: Path
    ) -> None:
        """USGS finite-fault file parses to a valid CoulombModel."""
        filepath = usgs_ff_inp_dir / filename
        if not filepath.exists():
            pytest.skip(f"File not found: {filepath}")

        model = read_inp(filepath)
        assert model.n_sources > 100  # these are large inversions

    @pytest.mark.parametrize("filename", FILES)
    def test_compute_grid_no_error(
        self, filename: str, usgs_ff_inp_dir: Path
    ) -> None:
        """Pipeline computes without NaN or Inf."""
        filepath = usgs_ff_inp_dir / filename
        if not filepath.exists():
            pytest.skip(f"File not found: {filepath}")

        model = read_inp(filepath)
        result = compute_grid(model)

        assert result is not None
        assert not np.any(np.isnan(result.cfs)), f"NaN in CFS for {filename}"
        assert not np.any(np.isinf(result.cfs)), f"Inf in CFS for {filename}"


# ---------------------------------------------------------------------------
# KODE coverage across Coulomb 3.4 distribution
# ---------------------------------------------------------------------------


class TestKodeCoverageAcrossDistribution:
    """Verify the distribution files collectively cover all KODE types."""

    def test_kode_100_present(self, coulomb34_inp_dir: Path) -> None:
        """At least one file uses KODE 100 (standard strike/dip-slip)."""
        self._assert_kode_present(coulomb34_inp_dir, 100)

    def test_kode_200_present(self, coulomb34_inp_dir: Path) -> None:
        """At least one file uses KODE 200 (tensile + right-lateral)."""
        self._assert_kode_present(coulomb34_inp_dir, 200)

    def test_kode_300_present(self, coulomb34_inp_dir: Path) -> None:
        """At least one file uses KODE 300 (tensile + reverse)."""
        self._assert_kode_present(coulomb34_inp_dir, 300)

    def test_kode_400_present(self, coulomb34_inp_dir: Path) -> None:
        """At least one file uses KODE 400 (point source)."""
        self._assert_kode_present(coulomb34_inp_dir, 400)

    def test_kode_500_present(self, coulomb34_inp_dir: Path) -> None:
        """At least one file uses KODE 500 (tensile/inflation)."""
        self._assert_kode_present(coulomb34_inp_dir, 500)

    def _assert_kode_present(self, dir_path: Path, kode_value: int) -> None:
        """Assert that at least one file in the directory uses the given KODE."""
        from opencoulomb.types.fault import Kode

        target_kode = Kode(kode_value)
        for f in sorted(dir_path.glob("*.inp")):
            model = read_inp(f)
            for fault in model.faults:
                if fault.kode == target_kode:
                    return  # found it
        pytest.fail(f"No file in {dir_path.name}/ uses KODE {kode_value}")
