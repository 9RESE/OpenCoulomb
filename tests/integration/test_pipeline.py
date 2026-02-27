"""Integration tests for opencoulomb.core.pipeline.

Covers:
- End-to-end: parse real .inp -> compute_grid -> verify results
- All 7 real .inp files compute without error
- compute_element_cfs returns None for no-receiver files
- Grid shape matches expected dimensions
- Performance: 100+ fault model computes in < 5s
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar

import numpy as np
import pytest

from opencoulomb.core.pipeline import compute_element_cfs, compute_grid
from opencoulomb.io import parse_inp_string, read_inp

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_inp(
    *,
    n_fixed: int = 1,
    faults: str | None = None,
    grid_x_inc: float = 5.0,
    grid_y_inc: float = 5.0,
) -> str:
    """Build a minimal .inp string for pipeline testing."""
    default_source = (
        "    1     -10.0       0.0      10.0       0.0  100       1.0"
        "       0.0    45.0     2.0    12.0  Source\n"
    )
    default_receiver = (
        "    2     -15.0       5.0      15.0       5.0  100       0.0"
        "       0.0    45.0     2.0    12.0  Receiver\n"
    )
    fault_block = faults if faults is not None else (default_source + "\n" + default_receiver)

    return (
        "Pipeline test model\n"
        "Integration test\n"
        f"#reg1=  0  #reg2=  0  #fixed=  {n_fixed}  sym=  1\n"
        " PR1=       0.250 PR2=       0.250 DEPTH=      10.000\n"
        "  E1=  0.800000E+06  E2=  0.800000E+06 XLIM=     0.000 YLIM=     0.000\n"
        "FRIC=       0.400\n"
        "  S1DR=  0.0000 S1DP=  0.0000 S1IN=  0.000  S1GD=   0.000\n"
        "  S3DR=  0.0000 S3DP=  0.0000 S3IN=  0.000  S3GD=   0.000\n"
        "  S2DR=  0.0000 S2DP=  0.0000 S2IN=  0.000  S2GD=   0.000\n"
        "\n"
        "  #   X-start    Y-start     X-fin      Y-fin   Kode  rt.lat  reverse"
        "   dip   top    bot\n"
        " xxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxx xxxxxxxxxx"
        " xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx xxxxxxxxxx\n"
        f"{fault_block}"
        "\n"
        "Grid Parameters\n"
        "  1  ---  Start-x =    -50.000\n"
        "  2  ---  Start-y =    -50.000\n"
        "  3  ---  Finish-x =    50.000\n"
        "  4  ---  Finish-y =    50.000\n"
        f"  5  ---  x-increment =   {grid_x_inc:.3f}\n"
        f"  6  ---  y-increment =   {grid_y_inc:.3f}\n"
    )


# ---------------------------------------------------------------------------
# End-to-end pipeline with synthetic model
# ---------------------------------------------------------------------------


class TestComputeGridSynthetic:
    """End-to-end pipeline test with a synthetic .inp model."""

    @pytest.fixture(scope="class")
    def model(self):
        inp_str = _make_inp(n_fixed=1, grid_x_inc=5.0, grid_y_inc=5.0)
        return parse_inp_string(inp_str)

    @pytest.fixture(scope="class")
    def result(self, model):
        return compute_grid(model)

    def test_result_not_none(self, result) -> None:
        assert result is not None

    def test_cfs_is_array(self, result) -> None:
        assert isinstance(result.cfs, np.ndarray)

    def test_no_nan_in_cfs(self, result) -> None:
        assert not np.any(np.isnan(result.cfs))

    def test_no_inf_in_cfs(self, result) -> None:
        assert not np.any(np.isinf(result.cfs))

    def test_nonzero_cfs(self, result) -> None:
        """A source fault with nonzero slip should produce nonzero CFS somewhere."""
        assert np.any(result.cfs != 0.0)

    def test_grid_shape(self, result) -> None:
        """Grid shape should match (n_y, n_x)."""
        n_y, n_x = result.grid_shape
        assert n_x > 0
        assert n_y > 0
        assert result.cfs.size == n_y * n_x

    def test_cfs_reshapes_to_grid(self, result) -> None:
        """CFS array can be reshaped to 2D grid."""
        cfs_2d = result.cfs_grid()
        assert cfs_2d.shape == result.grid_shape

    def test_displacement_arrays(self, result) -> None:
        """Displacement arrays must exist and be non-NaN."""
        stress = result.stress
        assert not np.any(np.isnan(stress.ux))
        assert not np.any(np.isnan(stress.uy))
        assert not np.any(np.isnan(stress.uz))

    def test_nonzero_displacement(self, result) -> None:
        """Source fault should produce nonzero displacement."""
        stress = result.stress
        total_disp = np.sqrt(stress.ux**2 + stress.uy**2 + stress.uz**2)
        assert np.max(total_disp) > 0.0

    def test_stress_arrays_finite(self, result) -> None:
        """All stress components must be finite."""
        stress = result.stress
        for attr in ("sxx", "syy", "szz", "syz", "sxz", "sxy"):
            arr = getattr(stress, attr)
            assert np.all(np.isfinite(arr)), f"{attr} has non-finite values"

    def test_receiver_angles_stored(self, result) -> None:
        """Receiver angles should be stored in result."""
        assert isinstance(result.receiver_strike, float)
        assert isinstance(result.receiver_dip, float)
        assert isinstance(result.receiver_rake, float)


# ---------------------------------------------------------------------------
# compute_element_cfs
# ---------------------------------------------------------------------------


class TestComputeElementCFS:
    """Test element-level CFS computation."""

    def test_with_receiver_returns_result(self) -> None:
        """Model with receivers returns an ElementResult."""
        model = parse_inp_string(_make_inp(n_fixed=1))
        result = compute_element_cfs(model)
        assert result is not None
        assert len(result.cfs) > 0

    def test_without_receiver_returns_none(self) -> None:
        """Model with no receivers (all sources) returns None."""
        source_only = (
            "    1     -10.0       0.0      10.0       0.0  100       1.0"
            "       0.0    45.0     2.0    12.0  Source\n"
        )
        model = parse_inp_string(_make_inp(n_fixed=1, faults=source_only))
        result = compute_element_cfs(model)
        assert result is None

    def test_element_cfs_finite(self) -> None:
        """Element CFS values must be finite."""
        model = parse_inp_string(_make_inp(n_fixed=1))
        result = compute_element_cfs(model)
        assert result is not None
        assert np.all(np.isfinite(result.cfs))
        assert np.all(np.isfinite(result.shear))
        assert np.all(np.isfinite(result.normal))

    def test_element_count_matches_receivers(self) -> None:
        """Number of element results should match number of receivers."""
        model = parse_inp_string(_make_inp(n_fixed=1))
        result = compute_element_cfs(model)
        assert result is not None
        assert len(result.cfs) == model.n_receivers
        assert len(result.elements) == model.n_receivers


# ---------------------------------------------------------------------------
# Real .inp file tests
# ---------------------------------------------------------------------------


class TestRealInpFiles:
    """Integration tests using all 7 real .inp files from Coulomb 3.4."""

    REAL_FILES: ClassVar[list[str]] = [
        "M6.5.inp",
        "M6p8.inp",
        "simple_receiver_bm.inp",
        "simplest_receiver.inp",
        "simple_subfaulted.inp",
        "test_case_receiver.inp",
        "test_case_subfaulted.inp",
    ]

    @pytest.mark.parametrize("filename", REAL_FILES)
    def test_compute_grid_no_error(
        self, filename: str, real_inp_files_dir: Path
    ) -> None:
        """Each real .inp file should compute without errors."""
        filepath = real_inp_files_dir / filename
        if not filepath.exists():
            pytest.skip(f"File not found: {filepath}")

        model = read_inp(filepath)
        result = compute_grid(model)

        assert result is not None
        assert not np.any(np.isnan(result.cfs))
        assert not np.any(np.isinf(result.cfs))

    @pytest.mark.parametrize("filename", REAL_FILES)
    def test_grid_shape_positive(
        self, filename: str, real_inp_files_dir: Path
    ) -> None:
        """Grid shape must have positive dimensions."""
        filepath = real_inp_files_dir / filename
        if not filepath.exists():
            pytest.skip(f"File not found: {filepath}")

        model = read_inp(filepath)
        result = compute_grid(model)

        n_y, n_x = result.grid_shape
        assert n_x > 0
        assert n_y > 0

    @pytest.mark.parametrize("filename", REAL_FILES)
    def test_displacement_finite(
        self, filename: str, real_inp_files_dir: Path
    ) -> None:
        """All displacement components must be finite."""
        filepath = real_inp_files_dir / filename
        if not filepath.exists():
            pytest.skip(f"File not found: {filepath}")

        model = read_inp(filepath)
        result = compute_grid(model)

        assert np.all(np.isfinite(result.stress.ux))
        assert np.all(np.isfinite(result.stress.uy))
        assert np.all(np.isfinite(result.stress.uz))


# ---------------------------------------------------------------------------
# No-receiver default behavior
# ---------------------------------------------------------------------------


class TestNoReceiverDefault:
    """Test pipeline behavior when there are no receiver faults."""

    def test_uses_source_orientation_as_default(self) -> None:
        """Without receivers, pipeline should use first source orientation."""
        source_only = (
            "    1     -10.0       0.0      10.0       0.0  100       1.0"
            "       0.0    45.0     2.0    12.0  Source\n"
        )
        model = parse_inp_string(_make_inp(n_fixed=1, faults=source_only))
        result = compute_grid(model)

        assert result is not None
        # Default rake should be 0.0 when using source orientation
        assert result.receiver_rake == pytest.approx(0.0, abs=1e-10)


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


class TestPipelinePerformance:
    """Test pipeline performance benchmarks."""

    def test_multi_fault_model_under_budget(self) -> None:
        """A 100+ fault model should compute in under 5 seconds.

        This creates 110 source faults and runs the pipeline with a
        modest grid size to test scaling.
        """
        # Build 110 source faults spread across the model
        fault_lines = []
        for i in range(110):
            x_start = -50.0 + (i % 10) * 10.0
            y_start = -50.0 + (i // 10) * 10.0
            x_fin = x_start + 5.0
            y_fin = y_start
            line = (
                f"    {i + 1}     {x_start:.1f}       {y_start:.1f}"
                f"      {x_fin:.1f}       {y_fin:.1f}  100       0.1"
                f"       0.0    45.0     5.0    15.0  Fault{i + 1}"
            )
            fault_lines.append(line)

        faults_str = "\n".join(fault_lines) + "\n"

        # Coarser grid for performance test
        inp_str = _make_inp(
            n_fixed=110,
            faults=faults_str,
            grid_x_inc=10.0,
            grid_y_inc=10.0,
        )
        model = parse_inp_string(inp_str)

        t0 = time.perf_counter()
        result = compute_grid(model)
        elapsed = time.perf_counter() - t0

        assert result is not None
        assert elapsed < 5.0, f"110-fault model took {elapsed:.2f}s (budget: 5s)"
        assert not np.any(np.isnan(result.cfs))


# ---------------------------------------------------------------------------
# Grid dimension consistency
# ---------------------------------------------------------------------------


class TestGridDimensionConsistency:
    """Verify grid dimensions match GridSpec expectations."""

    def test_grid_matches_spec(self) -> None:
        """Result grid points should match GridSpec n_x * n_y."""
        model = parse_inp_string(
            _make_inp(n_fixed=1, grid_x_inc=10.0, grid_y_inc=10.0)
        )
        result = compute_grid(model)

        n_y, n_x = result.grid_shape
        expected_nx = model.grid.n_x
        expected_ny = model.grid.n_y

        assert n_x == expected_nx
        assert n_y == expected_ny
        assert result.cfs.size == expected_nx * expected_ny


# ---------------------------------------------------------------------------
# KODE coverage: 200, 300, 400, 500
# ---------------------------------------------------------------------------


class TestPipelineKodeCoverage:
    """Test pipeline with all KODE types to cover dispatch branches."""

    def _make_kode_inp(self, kode: int, slip_1: float, slip_2: float) -> str:
        """Build .inp with a specific KODE source fault."""
        fault_line = (
            f"    1     -10.0       0.0      10.0       0.0  {kode}       {slip_1}"
            f"       {slip_2}    45.0     2.0    12.0  KodeTest\n"
        )
        return _make_inp(n_fixed=1, faults=fault_line, grid_x_inc=10.0, grid_y_inc=10.0)

    def test_kode_200_tensile_rl(self) -> None:
        """KODE 200: tensile + right-lateral."""
        model = parse_inp_string(self._make_kode_inp(200, 0.5, 1.0))
        result = compute_grid(model)
        assert result is not None
        assert not np.any(np.isnan(result.cfs))

    def test_kode_300_tensile_rev(self) -> None:
        """KODE 300: tensile + reverse."""
        model = parse_inp_string(self._make_kode_inp(300, 0.5, 1.0))
        result = compute_grid(model)
        assert result is not None
        assert not np.any(np.isnan(result.cfs))

    def test_kode_400_point_source(self) -> None:
        """KODE 400: point source."""
        model = parse_inp_string(self._make_kode_inp(400, 1.0, 0.0))
        result = compute_grid(model)
        assert result is not None
        assert not np.any(np.isnan(result.cfs))

    def test_kode_500_tensile_inflation(self) -> None:
        """KODE 500: tensile + inflation."""
        model = parse_inp_string(self._make_kode_inp(500, 0.5, 0.5))
        result = compute_grid(model)
        assert result is not None
        assert not np.any(np.isnan(result.cfs))
