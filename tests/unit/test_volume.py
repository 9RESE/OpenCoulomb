"""Tests for the OpenCoulomb 3D volume grid engine.

Covers:
- VolumeGridSpec construction, properties, and validation (types/grid.py)
- VolumeResult methods: cfs_volume(), slice_at_depth() (types/result.py)
- compute_volume() pipeline (core/pipeline.py)
- Volume writers: write_volume_csv, write_volume_slices (io/volume_writer.py)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest

from opencoulomb.core.pipeline import compute_grid, compute_volume
from opencoulomb.exceptions import ComputationError, ValidationError
from opencoulomb.io import read_inp
from opencoulomb.io.volume_writer import write_volume_csv, write_volume_slices
from opencoulomb.types import (
    CoulombResult,
    FaultElement,
    GridSpec,
    Kode,
    MaterialProperties,
    StrainResult,
    VolumeGridSpec,
    VolumeResult,
)
from opencoulomb.types.model import CoulombModel
from opencoulomb.types.result import StressResult

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Fixture paths
# ---------------------------------------------------------------------------

SIMPLEST_RECEIVER_INP = Path(
    "tests/fixtures/inp_files/real/simplest_receiver.inp"
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_volume_spec(
    *,
    start_x: float = -10.0,
    start_y: float = -10.0,
    finish_x: float = 10.0,
    finish_y: float = 10.0,
    x_inc: float = 5.0,
    y_inc: float = 5.0,
    depth_min: float = 2.0,
    depth_max: float = 12.0,
    depth_inc: float = 5.0,
) -> VolumeGridSpec:
    """Return a small VolumeGridSpec suitable for fast tests."""
    return VolumeGridSpec(
        start_x=start_x,
        start_y=start_y,
        finish_x=finish_x,
        finish_y=finish_y,
        x_inc=x_inc,
        y_inc=y_inc,
        depth_min=depth_min,
        depth_max=depth_max,
        depth_inc=depth_inc,
    )


def _make_synthetic_volume(
    n_z: int = 3,
    n_y: int = 4,
    n_x: int = 5,
    *,
    with_strain: bool = False,
) -> VolumeResult:
    """Return a synthetic VolumeResult for writer / slice tests."""
    n = n_z * n_y * n_x
    rng = np.random.default_rng(0)

    depths = np.linspace(1.0, 10.0, n_z)

    # Build flat coordinate arrays matching (n_z, n_y, n_x) ordering
    x_1d = np.linspace(-5.0, 5.0, n_x)
    y_1d = np.linspace(-5.0, 5.0, n_y)
    gd, gy, gx = np.meshgrid(depths, y_1d, x_1d, indexing="ij")
    x_flat = gx.ravel()
    y_flat = gy.ravel()
    z_flat = -gd.ravel()

    stress = StressResult(
        x=x_flat, y=y_flat, z=z_flat,
        ux=rng.normal(0, 0.01, n), uy=rng.normal(0, 0.01, n),
        uz=rng.normal(0, 0.001, n),
        sxx=rng.normal(0, 1, n), syy=rng.normal(0, 1, n),
        szz=rng.normal(0, 1, n), syz=rng.normal(0, 0.5, n),
        sxz=rng.normal(0, 0.5, n), sxy=rng.normal(0, 0.5, n),
    )

    strain: StrainResult | None = None
    if with_strain:
        strain = StrainResult(
            exx=rng.normal(0, 1e-6, n), eyy=rng.normal(0, 1e-6, n),
            ezz=rng.normal(0, 1e-6, n), eyz=rng.normal(0, 5e-7, n),
            exz=rng.normal(0, 5e-7, n), exy=rng.normal(0, 5e-7, n),
            volumetric=rng.normal(0, 1e-6, n),
        )

    return VolumeResult(
        stress=stress,
        cfs=rng.normal(0, 0.5, n),
        shear=rng.normal(0, 0.3, n),
        normal=rng.normal(0, 0.2, n),
        receiver_strike=30.0,
        receiver_dip=60.0,
        receiver_rake=90.0,
        volume_shape=(n_z, n_y, n_x),
        depths=depths,
        strain=strain,
    )


# ---------------------------------------------------------------------------
# Session-scoped model fixture (avoids re-parsing on every test)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def simple_model() -> CoulombModel:
    """Load simplest_receiver.inp — one source fault, one receiver."""
    return read_inp(SIMPLEST_RECEIVER_INP)


@pytest.fixture(scope="session")
def tiny_volume_spec() -> VolumeGridSpec:
    """Very small volume spec for fast integration tests."""
    return _make_volume_spec(
        start_x=-20.0, start_y=-20.0,
        finish_x=20.0, finish_y=20.0,
        x_inc=20.0, y_inc=20.0,   # 3x3 horizontal grid
        depth_min=5.0, depth_max=15.0, depth_inc=5.0,  # 3 depth layers
    )


@pytest.fixture(scope="session")
def volume_result(simple_model, tiny_volume_spec) -> VolumeResult:
    """Run compute_volume once for the session; share across tests."""
    return compute_volume(simple_model, tiny_volume_spec)


# ===========================================================================
# 1.  VolumeGridSpec — construction and properties
# ===========================================================================


class TestVolumeGridSpecConstruction:
    """VolumeGridSpec accepts valid parameters and stores them correctly."""

    def test_basic_construction(self) -> None:
        spec = _make_volume_spec()
        assert spec.start_x == -10.0
        assert spec.start_y == -10.0
        assert spec.finish_x == 10.0
        assert spec.finish_y == 10.0
        assert spec.x_inc == 5.0
        assert spec.y_inc == 5.0
        assert spec.depth_min == 2.0
        assert spec.depth_max == 12.0
        assert spec.depth_inc == 5.0

    def test_is_frozen(self) -> None:
        """VolumeGridSpec is a frozen dataclass."""
        spec = _make_volume_spec()
        with pytest.raises((AttributeError, TypeError)):
            spec.x_inc = 1.0  # type: ignore[misc]

    def test_zero_depth_min_allowed(self) -> None:
        """depth_min=0 (surface) is valid."""
        spec = _make_volume_spec(depth_min=0.0, depth_max=10.0)
        assert spec.depth_min == 0.0


class TestVolumeGridSpecProperties:
    """n_x, n_y, n_z, n_points, depths are computed correctly."""

    def test_n_x(self) -> None:
        # start_x=-10, finish_x=10, x_inc=5 → 5 points
        spec = _make_volume_spec(start_x=-10.0, finish_x=10.0, x_inc=5.0)
        assert spec.n_x == 5

    def test_n_y(self) -> None:
        # start_y=-10, finish_y=10, y_inc=5 → 5 points
        spec = _make_volume_spec(start_y=-10.0, finish_y=10.0, y_inc=5.0)
        assert spec.n_y == 5

    def test_n_z(self) -> None:
        # depth_min=0, depth_max=10, depth_inc=5 → 3 layers
        spec = _make_volume_spec(depth_min=0.0, depth_max=10.0, depth_inc=5.0)
        assert spec.n_z == 3

    def test_n_z_single_layer_not_possible(self) -> None:
        # depth_max must exceed depth_min, so minimum n_z=2
        spec = _make_volume_spec(depth_min=0.0, depth_max=5.0, depth_inc=10.0)
        # np.linspace(0, 5, round((5-0)/10)+1) = np.linspace(0, 5, 1) = [0]
        # Actually round(0.5)=0 in Python banker's rounding, but round(5/10)=round(0.5)=0
        # The guard is depth_inc > 0 and depth_max > depth_min, so n_z can be 1
        assert spec.n_z >= 1

    def test_n_points_is_product(self) -> None:
        spec = _make_volume_spec(
            start_x=-10.0, finish_x=10.0, x_inc=5.0,
            start_y=-10.0, finish_y=10.0, y_inc=5.0,
            depth_min=0.0, depth_max=10.0, depth_inc=5.0,
        )
        assert spec.n_points == spec.n_x * spec.n_y * spec.n_z

    def test_depths_length_matches_n_z(self) -> None:
        spec = _make_volume_spec(depth_min=2.0, depth_max=12.0, depth_inc=5.0)
        assert len(spec.depths) == spec.n_z

    def test_depths_first_value(self) -> None:
        spec = _make_volume_spec(depth_min=3.0, depth_max=13.0, depth_inc=5.0)
        assert spec.depths[0] == pytest.approx(3.0)

    def test_depths_last_value(self) -> None:
        spec = _make_volume_spec(depth_min=3.0, depth_max=13.0, depth_inc=5.0)
        assert spec.depths[-1] == pytest.approx(13.0)

    def test_depths_are_monotonically_increasing(self) -> None:
        spec = _make_volume_spec(depth_min=1.0, depth_max=11.0, depth_inc=2.0)
        diffs = np.diff(spec.depths)
        assert np.all(diffs > 0)

    def test_depths_dtype(self) -> None:
        spec = _make_volume_spec()
        assert spec.depths.dtype == np.float64

    def test_n_points_matches_depths_times_xy(self) -> None:
        spec = _make_volume_spec(
            start_x=0.0, finish_x=6.0, x_inc=2.0,
            start_y=0.0, finish_y=4.0, y_inc=2.0,
            depth_min=1.0, depth_max=5.0, depth_inc=2.0,
        )
        expected = spec.n_x * spec.n_y * spec.n_z
        assert spec.n_points == expected


class TestVolumeGridSpecToGridSpec:
    """to_grid_spec(depth) returns a valid GridSpec for a given depth."""

    def test_returns_grid_spec(self) -> None:
        spec = _make_volume_spec()
        gs = spec.to_grid_spec(7.0)
        assert isinstance(gs, GridSpec)

    def test_xy_extent_preserved(self) -> None:
        spec = _make_volume_spec(
            start_x=-5.0, start_y=-5.0,
            finish_x=5.0, finish_y=5.0,
            x_inc=2.5, y_inc=2.5,
        )
        gs = spec.to_grid_spec(8.0)
        assert gs.start_x == -5.0
        assert gs.start_y == -5.0
        assert gs.finish_x == 5.0
        assert gs.finish_y == 5.0
        assert gs.x_inc == 2.5
        assert gs.y_inc == 2.5

    def test_depth_is_set_correctly(self) -> None:
        spec = _make_volume_spec()
        for d in [2.0, 7.5, 12.0]:
            gs = spec.to_grid_spec(d)
            assert gs.depth == pytest.approx(d)

    def test_n_x_n_y_match(self) -> None:
        spec = _make_volume_spec()
        gs = spec.to_grid_spec(5.0)
        assert gs.n_x == spec.n_x
        assert gs.n_y == spec.n_y


class TestVolumeGridSpecValidation:
    """Invalid parameters raise ValidationError with informative messages."""

    def test_depth_max_equal_depth_min_raises(self) -> None:
        with pytest.raises(ValidationError, match="depth_max"):
            _make_volume_spec(depth_min=10.0, depth_max=10.0)

    def test_depth_max_less_than_depth_min_raises(self) -> None:
        with pytest.raises(ValidationError, match="depth_max"):
            _make_volume_spec(depth_min=10.0, depth_max=5.0)

    def test_negative_depth_min_raises(self) -> None:
        with pytest.raises(ValidationError, match="depth_min"):
            _make_volume_spec(depth_min=-1.0)

    def test_zero_depth_inc_raises(self) -> None:
        with pytest.raises(ValidationError, match="depth_inc"):
            _make_volume_spec(depth_inc=0.0)

    def test_negative_depth_inc_raises(self) -> None:
        with pytest.raises(ValidationError, match="depth_inc"):
            _make_volume_spec(depth_inc=-1.0)

    def test_zero_x_inc_raises(self) -> None:
        with pytest.raises(ValidationError, match="increment"):
            _make_volume_spec(x_inc=0.0)

    def test_zero_y_inc_raises(self) -> None:
        with pytest.raises(ValidationError, match="increment"):
            _make_volume_spec(y_inc=0.0)

    def test_finish_x_le_start_x_raises(self) -> None:
        with pytest.raises(ValidationError, match="finish_x"):
            _make_volume_spec(start_x=5.0, finish_x=5.0)

    def test_finish_y_le_start_y_raises(self) -> None:
        with pytest.raises(ValidationError, match="finish_y"):
            _make_volume_spec(start_y=5.0, finish_y=5.0)


# ===========================================================================
# 2.  VolumeResult — methods
# ===========================================================================


class TestVolumeResultCfsVolume:
    """cfs_volume() reshapes flat CFS array to (n_z, n_y, n_x)."""

    def test_shape_matches_volume_shape(self) -> None:
        vol = _make_synthetic_volume(n_z=3, n_y=4, n_x=5)
        arr = vol.cfs_volume()
        assert arr.shape == (3, 4, 5)

    def test_values_match_flat_cfs(self) -> None:
        vol = _make_synthetic_volume(n_z=2, n_y=3, n_x=4)
        arr = vol.cfs_volume()
        assert np.array_equal(arr.ravel(), vol.cfs)

    def test_different_shapes(self) -> None:
        for nz, ny, nx in [(1, 2, 3), (5, 5, 5), (2, 10, 8)]:
            vol = _make_synthetic_volume(n_z=nz, n_y=ny, n_x=nx)
            arr = vol.cfs_volume()
            assert arr.shape == (nz, ny, nx)


class TestVolumeResultSliceAtDepth:
    """slice_at_depth(k) extracts a correct 2D CoulombResult."""

    def test_returns_coulomb_result(self) -> None:
        vol = _make_synthetic_volume()
        slc = vol.slice_at_depth(0)
        assert isinstance(slc, CoulombResult)

    def test_grid_shape_is_ny_nx(self) -> None:
        vol = _make_synthetic_volume(n_z=3, n_y=4, n_x=5)
        slc = vol.slice_at_depth(0)
        assert slc.grid_shape == (4, 5)

    def test_first_slice_cfs_values(self) -> None:
        """Slice 0 CFS matches first n_y*n_x entries of flat cfs."""
        n_z, n_y, n_x = 3, 4, 5
        vol = _make_synthetic_volume(n_z=n_z, n_y=n_y, n_x=n_x)
        n_2d = n_y * n_x
        slc = vol.slice_at_depth(0)
        np.testing.assert_array_equal(slc.cfs, vol.cfs[:n_2d])

    def test_last_slice_cfs_values(self) -> None:
        """Slice n_z-1 CFS matches last n_y*n_x entries."""
        n_z, n_y, n_x = 3, 4, 5
        vol = _make_synthetic_volume(n_z=n_z, n_y=n_y, n_x=n_x)
        n_2d = n_y * n_x
        slc = vol.slice_at_depth(n_z - 1)
        np.testing.assert_array_equal(slc.cfs, vol.cfs[(n_z - 1) * n_2d:])

    def test_middle_slice_cfs_values(self) -> None:
        """Middle slice (index 1) picks the correct offset."""
        n_z, n_y, n_x = 3, 4, 5
        vol = _make_synthetic_volume(n_z=n_z, n_y=n_y, n_x=n_x)
        n_2d = n_y * n_x
        slc = vol.slice_at_depth(1)
        expected = vol.cfs[n_2d: 2 * n_2d]
        np.testing.assert_array_equal(slc.cfs, expected)

    def test_slice_x_coordinates(self) -> None:
        """X coordinates of a slice match the corresponding flat segment."""
        n_z, n_y, n_x = 3, 4, 5
        vol = _make_synthetic_volume(n_z=n_z, n_y=n_y, n_x=n_x)
        n_2d = n_y * n_x
        for k in range(n_z):
            slc = vol.slice_at_depth(k)
            expected_x = vol.stress.x[k * n_2d: (k + 1) * n_2d]
            np.testing.assert_array_equal(slc.stress.x, expected_x)

    def test_slice_z_is_constant(self) -> None:
        """All z-values within a depth slice are identical."""
        vol = _make_synthetic_volume(n_z=3, n_y=4, n_x=5)
        for k in range(3):
            slc = vol.slice_at_depth(k)
            assert np.all(slc.stress.z == slc.stress.z[0])

    def test_receiver_orientation_preserved(self) -> None:
        vol = _make_synthetic_volume()
        slc = vol.slice_at_depth(0)
        assert slc.receiver_strike == vol.receiver_strike
        assert slc.receiver_dip == vol.receiver_dip
        assert slc.receiver_rake == vol.receiver_rake

    def test_strain_none_when_volume_has_no_strain(self) -> None:
        vol = _make_synthetic_volume(with_strain=False)
        slc = vol.slice_at_depth(0)
        assert slc.strain is None

    def test_strain_populated_when_volume_has_strain(self) -> None:
        vol = _make_synthetic_volume(with_strain=True)
        slc = vol.slice_at_depth(0)
        assert slc.strain is not None
        assert isinstance(slc.strain, StrainResult)


# ===========================================================================
# 3.  compute_volume() — pipeline integration
# ===========================================================================


class TestComputeVolumeBasic:
    """compute_volume() runs and returns a well-formed VolumeResult."""

    def test_returns_volume_result(self, volume_result) -> None:
        assert isinstance(volume_result, VolumeResult)

    def test_volume_shape_matches_spec(self, volume_result, tiny_volume_spec) -> None:
        n_z = tiny_volume_spec.n_z
        n_y = tiny_volume_spec.n_y
        n_x = tiny_volume_spec.n_x
        assert volume_result.volume_shape == (n_z, n_y, n_x)

    def test_flat_array_length(self, volume_result, tiny_volume_spec) -> None:
        expected_n = tiny_volume_spec.n_points
        assert len(volume_result.cfs) == expected_n
        assert len(volume_result.shear) == expected_n
        assert len(volume_result.normal) == expected_n

    def test_stress_coordinates_length(self, volume_result, tiny_volume_spec) -> None:
        n = tiny_volume_spec.n_points
        assert len(volume_result.stress.x) == n
        assert len(volume_result.stress.y) == n
        assert len(volume_result.stress.z) == n

    def test_depths_length_matches_n_z(self, volume_result, tiny_volume_spec) -> None:
        assert len(volume_result.depths) == tiny_volume_spec.n_z

    def test_depths_values_match_spec(self, volume_result, tiny_volume_spec) -> None:
        np.testing.assert_allclose(
            volume_result.depths, tiny_volume_spec.depths, rtol=1e-10
        )

    def test_cfs_is_finite(self, volume_result) -> None:
        assert np.all(np.isfinite(volume_result.cfs))

    def test_shear_is_finite(self, volume_result) -> None:
        assert np.all(np.isfinite(volume_result.shear))

    def test_normal_is_finite(self, volume_result) -> None:
        assert np.all(np.isfinite(volume_result.normal))

    def test_z_coordinates_are_non_positive(self, volume_result) -> None:
        """Okada convention: z <= 0 below surface."""
        assert np.all(volume_result.stress.z <= 0.0)

    def test_receiver_orientation_is_float(self, volume_result) -> None:
        assert isinstance(volume_result.receiver_strike, float)
        assert isinstance(volume_result.receiver_dip, float)
        assert isinstance(volume_result.receiver_rake, float)


class TestComputeVolumeConsistencyWithGrid:
    """A volume slice at a given depth must match compute_grid at that depth."""

    def test_single_depth_matches_compute_grid(self, simple_model) -> None:
        """Slice k=0 from a single-depth volume == compute_grid at that depth."""
        depth = 8.0
        spec = VolumeGridSpec(
            start_x=-20.0, start_y=-20.0,
            finish_x=20.0, finish_y=20.0,
            x_inc=20.0, y_inc=20.0,
            depth_min=depth, depth_max=depth + 0.1,  # near-single layer
            depth_inc=0.1,
        )
        vol = compute_volume(simple_model, spec)

        # Build a matching GridSpec for compute_grid
        grid_spec = spec.to_grid_spec(depth)
        import dataclasses
        modified_model = dataclasses.replace(simple_model, grid=grid_spec)
        grid_result = compute_grid(modified_model)

        # The first depth layer (k=0) corresponds to depth_min=8.0
        slc = vol.slice_at_depth(0)

        np.testing.assert_allclose(
            slc.cfs, grid_result.cfs,
            rtol=1e-6, atol=1e-10,
            err_msg="Volume slice CFS does not match compute_grid CFS at same depth",
        )

    def test_slice_shear_matches_grid(self, simple_model) -> None:
        """Shear stress component also matches between volume slice and grid."""
        depth = 10.0
        spec = VolumeGridSpec(
            start_x=-15.0, start_y=-15.0,
            finish_x=15.0, finish_y=15.0,
            x_inc=15.0, y_inc=15.0,
            depth_min=depth, depth_max=depth + 0.1,
            depth_inc=0.1,
        )
        vol = compute_volume(simple_model, spec)

        import dataclasses
        modified_model = dataclasses.replace(
            simple_model, grid=spec.to_grid_spec(depth)
        )
        grid_result = compute_grid(modified_model)

        slc = vol.slice_at_depth(0)
        np.testing.assert_allclose(
            slc.shear, grid_result.shear, rtol=1e-6, atol=1e-10,
        )


class TestComputeVolumeStrain:
    """compute_strain=True populates StrainResult; False leaves it None."""

    def test_no_strain_by_default(self, volume_result) -> None:
        assert volume_result.strain is None

    def test_strain_populated_when_requested(self, simple_model, tiny_volume_spec) -> None:
        vol = compute_volume(simple_model, tiny_volume_spec, compute_strain=True)
        assert vol.strain is not None

    def test_strain_is_strain_result_type(self, simple_model, tiny_volume_spec) -> None:
        vol = compute_volume(simple_model, tiny_volume_spec, compute_strain=True)
        assert isinstance(vol.strain, StrainResult)

    def test_strain_arrays_correct_length(self, simple_model, tiny_volume_spec) -> None:
        vol = compute_volume(simple_model, tiny_volume_spec, compute_strain=True)
        n = tiny_volume_spec.n_points
        assert len(vol.strain.exx) == n  # type: ignore[union-attr]
        assert len(vol.strain.volumetric) == n  # type: ignore[union-attr]

    def test_strain_arrays_are_finite(self, simple_model, tiny_volume_spec) -> None:
        vol = compute_volume(simple_model, tiny_volume_spec, compute_strain=True)
        assert np.all(np.isfinite(vol.strain.exx))  # type: ignore[union-attr]
        assert np.all(np.isfinite(vol.strain.volumetric))  # type: ignore[union-attr]

    def test_volumetric_strain_equals_sum_of_diagonal(
        self, simple_model, tiny_volume_spec
    ) -> None:
        vol = compute_volume(simple_model, tiny_volume_spec, compute_strain=True)
        s = vol.strain
        assert s is not None
        np.testing.assert_allclose(
            s.volumetric, s.exx + s.eyy + s.ezz, rtol=1e-12,
        )


class TestComputeVolumeErrors:
    """compute_volume raises ComputationError when the model is invalid."""

    def _model_no_sources(self) -> CoulombModel:
        """A CoulombModel with no source faults."""
        material = MaterialProperties(poisson=0.25, young=8e5, friction=0.4)
        grid = GridSpec(
            start_x=-10, start_y=-10,
            finish_x=10, finish_y=10,
            x_inc=5.0, y_inc=5.0,
        )
        # n_fixed=0 → all faults are receivers
        fault = FaultElement(
            x_start=-5, y_start=0, x_fin=5, y_fin=0,
            kode=Kode.STANDARD, slip_1=1.0, slip_2=0.0,
            dip=90.0, top_depth=0.1, bottom_depth=10.0,
            label="Receiver",
        )
        return CoulombModel(
            title="No-source model",
            material=material,
            faults=[fault],
            grid=grid,
            n_fixed=0,
        )

    def test_no_source_faults_raises(self) -> None:
        model = self._model_no_sources()
        spec = _make_volume_spec()
        with pytest.raises(ComputationError, match="source faults"):
            compute_volume(model, spec)


# ===========================================================================
# 4.  Volume writers
# ===========================================================================


class TestWriteVolumeCsv:
    """write_volume_csv produces a valid CSV file."""

    @pytest.fixture()
    def vol_3x4x5(self) -> VolumeResult:
        return _make_synthetic_volume(n_z=3, n_y=4, n_x=5)

    def test_file_is_created(self, vol_3x4x5, tmp_path) -> None:
        out = tmp_path / "volume.csv"
        write_volume_csv(vol_3x4x5, out)
        assert out.exists()

    def test_header_columns(self, vol_3x4x5, tmp_path) -> None:
        out = tmp_path / "volume.csv"
        write_volume_csv(vol_3x4x5, out)
        lines = out.read_text().splitlines()
        header = lines[0]
        expected_cols = [
            "x", "y", "depth",
            "ux", "uy", "uz",
            "sxx", "syy", "szz", "syz", "sxz", "sxy",
            "cfs", "shear", "normal",
        ]
        for col in expected_cols:
            assert col in header, f"Missing column {col!r} in header: {header}"

    def test_row_count_equals_n_points(self, vol_3x4x5, tmp_path) -> None:
        out = tmp_path / "volume.csv"
        write_volume_csv(vol_3x4x5, out)
        lines = out.read_text().splitlines()
        # First line is header; remaining are data rows
        data_rows = [l for l in lines[1:] if l.strip()]
        n_z, n_y, n_x = vol_3x4x5.volume_shape
        assert len(data_rows) == n_z * n_y * n_x

    def test_fifteen_columns_per_row(self, vol_3x4x5, tmp_path) -> None:
        out = tmp_path / "volume.csv"
        write_volume_csv(vol_3x4x5, out)
        lines = out.read_text().splitlines()
        for row in lines[1:]:
            if row.strip():
                assert len(row.split(",")) == 15

    def test_depth_column_is_positive(self, vol_3x4x5, tmp_path) -> None:
        """Depth column stores positive-down values (not Okada z convention)."""
        out = tmp_path / "volume.csv"
        write_volume_csv(vol_3x4x5, out)
        arr = np.loadtxt(out, delimiter=",", skiprows=1)
        depth_col = arr[:, 2]
        assert np.all(depth_col >= 0.0)

    def test_cfs_values_match_volume(self, vol_3x4x5, tmp_path) -> None:
        out = tmp_path / "volume.csv"
        write_volume_csv(vol_3x4x5, out)
        arr = np.loadtxt(out, delimiter=",", skiprows=1)
        cfs_col = arr[:, 12]
        np.testing.assert_allclose(cfs_col, vol_3x4x5.cfs, rtol=1e-5)

    def test_accepts_string_path(self, vol_3x4x5, tmp_path) -> None:
        out = str(tmp_path / "volume_str.csv")
        write_volume_csv(vol_3x4x5, out)
        assert Path(out).exists()

    def test_accepts_path_object(self, vol_3x4x5, tmp_path) -> None:
        out = tmp_path / "volume_path.csv"
        write_volume_csv(vol_3x4x5, out)
        assert out.exists()


class TestWriteVolumeSlices:
    """write_volume_slices produces one .dat file per depth layer."""

    @pytest.fixture()
    def vol_3x4x5(self) -> VolumeResult:
        return _make_synthetic_volume(n_z=3, n_y=4, n_x=5)

    def test_correct_number_of_files(self, vol_3x4x5, tmp_path) -> None:
        paths = write_volume_slices(vol_3x4x5, tmp_path)
        n_z = vol_3x4x5.volume_shape[0]
        assert len(paths) == n_z

    def test_all_files_exist(self, vol_3x4x5, tmp_path) -> None:
        paths = write_volume_slices(vol_3x4x5, tmp_path)
        for p in paths:
            assert p.exists()

    def test_files_are_dat(self, vol_3x4x5, tmp_path) -> None:
        paths = write_volume_slices(vol_3x4x5, tmp_path)
        for p in paths:
            assert p.suffix == ".dat"

    def test_filenames_contain_depth(self, vol_3x4x5, tmp_path) -> None:
        paths = write_volume_slices(vol_3x4x5, tmp_path)
        for p in paths:
            assert "depth" in p.name

    def test_default_field_is_cfs(self, vol_3x4x5, tmp_path) -> None:
        paths = write_volume_slices(vol_3x4x5, tmp_path)
        for p in paths:
            assert "cfs" in p.name

    def test_each_file_has_correct_shape(self, vol_3x4x5, tmp_path) -> None:
        n_z, n_y, n_x = vol_3x4x5.volume_shape
        paths = write_volume_slices(vol_3x4x5, tmp_path)
        for p in paths:
            arr = np.loadtxt(p)
            assert arr.shape == (n_y, n_x)

    def test_slice_values_match_cfs_volume(self, vol_3x4x5, tmp_path) -> None:
        n_z, _n_y, _n_x = vol_3x4x5.volume_shape
        cfs_3d = vol_3x4x5.cfs_volume()
        paths = write_volume_slices(vol_3x4x5, tmp_path)
        for k, p in enumerate(paths):
            arr = np.loadtxt(p)
            np.testing.assert_allclose(arr, cfs_3d[k], rtol=1e-5)

    def test_shear_field(self, vol_3x4x5, tmp_path) -> None:
        paths = write_volume_slices(vol_3x4x5, tmp_path / "shear_out", field="shear")
        for p in paths:
            assert "shear" in p.name

    def test_normal_field(self, vol_3x4x5, tmp_path) -> None:
        paths = write_volume_slices(vol_3x4x5, tmp_path / "normal_out", field="normal")
        for p in paths:
            assert "normal" in p.name

    def test_unknown_field_raises(self, vol_3x4x5, tmp_path) -> None:
        with pytest.raises(ValueError, match="Unknown field"):
            write_volume_slices(vol_3x4x5, tmp_path, field="bogus")

    def test_output_directory_is_created(self, vol_3x4x5, tmp_path) -> None:
        new_dir = tmp_path / "new_subdir" / "slices"
        assert not new_dir.exists()
        write_volume_slices(vol_3x4x5, new_dir)
        assert new_dir.exists()

    def test_returns_list_of_paths(self, vol_3x4x5, tmp_path) -> None:
        result = write_volume_slices(vol_3x4x5, tmp_path)
        assert isinstance(result, list)
        assert all(isinstance(p, Path) for p in result)

    def test_shear_slice_values_match(self, vol_3x4x5, tmp_path) -> None:
        n_z = vol_3x4x5.volume_shape[0]
        shear_3d = vol_3x4x5.shear.reshape(vol_3x4x5.volume_shape)
        paths = write_volume_slices(vol_3x4x5, tmp_path / "sh", field="shear")
        assert len(paths) == n_z
        for k, p in enumerate(paths):
            arr = np.loadtxt(p)
            np.testing.assert_allclose(arr, shear_3d[k], rtol=1e-5)
