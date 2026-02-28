"""Tests for 3D volume visualization."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from opencoulomb.types.grid import GridSpec, VolumeGridSpec
from opencoulomb.types.material import MaterialProperties
from opencoulomb.types.model import CoulombModel
from opencoulomb.types.fault import FaultElement, Kode
from opencoulomb.types.result import StressResult, VolumeResult


def _make_volume_result() -> tuple[VolumeResult, CoulombModel]:
    """Create a minimal VolumeResult for testing."""
    n_z, n_y, n_x = 5, 4, 4
    n_pts = n_z * n_y * n_x

    rng = np.random.default_rng(42)
    stress = StressResult(
        x=np.tile(np.linspace(-10, 10, n_x), n_z * n_y),
        y=np.tile(np.repeat(np.linspace(-10, 10, n_y), n_x), n_z),
        z=-np.repeat(np.linspace(2, 20, n_z), n_y * n_x),
        ux=np.zeros(n_pts), uy=np.zeros(n_pts), uz=np.zeros(n_pts),
        sxx=rng.standard_normal(n_pts) * 0.01,
        syy=rng.standard_normal(n_pts) * 0.01,
        szz=rng.standard_normal(n_pts) * 0.01,
        syz=rng.standard_normal(n_pts) * 0.01,
        sxz=rng.standard_normal(n_pts) * 0.01,
        sxy=rng.standard_normal(n_pts) * 0.01,
    )

    vol = VolumeResult(
        stress=stress,
        cfs=rng.standard_normal(n_pts) * 0.1,
        shear=rng.standard_normal(n_pts) * 0.08,
        normal=rng.standard_normal(n_pts) * 0.02,
        receiver_strike=45.0, receiver_dip=60.0, receiver_rake=90.0,
        volume_shape=(n_z, n_y, n_x),
        depths=np.linspace(2.0, 20.0, n_z),
    )

    source = FaultElement(
        x_start=-5, y_start=0, x_fin=5, y_fin=0,
        kode=Kode.STANDARD, slip_1=1.0, slip_2=0.0,
        dip=90.0, top_depth=0.0, bottom_depth=15.0,
    )
    model = CoulombModel(
        title="test", material=MaterialProperties(),
        faults=[source],
        grid=GridSpec(-10, -10, 10, 10, 5.0, 5.0, 10.0),
        n_fixed=1,
    )
    return vol, model


class TestPlotVolumeSlices:
    def test_returns_figure_and_axes(self):
        from opencoulomb.viz.volume import plot_volume_slices
        vol, model = _make_volume_result()
        fig, axes = plot_volume_slices(vol, model)
        assert fig is not None
        assert len(axes) == 5  # n_z = 5
        plt.close(fig)

    def test_specific_depth_indices(self):
        from opencoulomb.viz.volume import plot_volume_slices
        vol, model = _make_volume_result()
        fig, axes = plot_volume_slices(vol, model, depth_indices=[0, 2, 4])
        assert len(axes) == 3
        plt.close(fig)

    def test_custom_vmax(self):
        from opencoulomb.viz.volume import plot_volume_slices
        vol, model = _make_volume_result()
        fig, axes = plot_volume_slices(vol, model, vmax=0.5)
        plt.close(fig)

    def test_different_fields(self):
        from opencoulomb.viz.volume import plot_volume_slices
        vol, model = _make_volume_result()
        for field in ["cfs", "shear", "normal"]:
            fig, _ = plot_volume_slices(vol, model, field=field)
            plt.close(fig)

    def test_invalid_field_raises(self):
        from opencoulomb.viz.volume import plot_volume_slices
        vol, model = _make_volume_result()
        with pytest.raises(ValueError, match="Unknown field"):
            plot_volume_slices(vol, model, field="invalid")


class TestPlotVolumeCrossSections:
    def test_returns_figure(self):
        from opencoulomb.viz.volume import plot_volume_cross_sections
        vol, model = _make_volume_result()
        fig, axes = plot_volume_cross_sections(vol, model)
        assert fig is not None
        assert len(axes) >= 1
        plt.close(fig)

    def test_specific_y_indices(self):
        from opencoulomb.viz.volume import plot_volume_cross_sections
        vol, model = _make_volume_result()
        fig, axes = plot_volume_cross_sections(vol, model, y_indices=[1])
        assert len(axes) == 1
        plt.close(fig)


class TestExportVolumeGif:
    def test_creates_gif_file(self, tmp_path):
        from opencoulomb.viz.volume import export_volume_gif
        vol, model = _make_volume_result()
        gif_path = tmp_path / "test.gif"
        result = export_volume_gif(vol, model, gif_path, fps=2)
        assert result.exists()
        assert result.stat().st_size > 0

    def test_gif_with_different_fields(self, tmp_path):
        from opencoulomb.viz.volume import export_volume_gif
        vol, model = _make_volume_result()
        for field in ["cfs", "shear"]:
            gif_path = tmp_path / f"test_{field}.gif"
            export_volume_gif(vol, model, gif_path, field=field, fps=2)
            assert gif_path.exists()


class TestPlotCatalogOnVolume:
    def test_with_catalog(self):
        from opencoulomb.types.catalog import CatalogEvent, EarthquakeCatalog
        from opencoulomb.viz.volume import plot_catalog_on_volume
        vol, model = _make_volume_result()
        catalog = EarthquakeCatalog(events=[
            CatalogEvent(latitude=0.0, longitude=0.0, depth_km=10.0,
                        magnitude=5.0, time="2024-01-01"),
            CatalogEvent(latitude=5.0, longitude=-5.0, depth_km=5.0,
                        magnitude=6.0, time="2024-01-02"),
        ])
        fig, ax = plot_catalog_on_volume(vol, model, catalog)
        assert fig is not None
        plt.close(fig)

    def test_specific_depth_index(self):
        from opencoulomb.types.catalog import CatalogEvent, EarthquakeCatalog
        from opencoulomb.viz.volume import plot_catalog_on_volume
        vol, model = _make_volume_result()
        catalog = EarthquakeCatalog(events=[
            CatalogEvent(latitude=0.0, longitude=0.0, depth_km=10.0,
                        magnitude=5.0, time="2024-01-01"),
        ])
        fig, ax = plot_catalog_on_volume(vol, model, catalog, depth_index=0)
        plt.close(fig)

    def test_empty_catalog(self):
        from opencoulomb.types.catalog import EarthquakeCatalog
        from opencoulomb.viz.volume import plot_catalog_on_volume
        vol, model = _make_volume_result()
        catalog = EarthquakeCatalog(events=[])
        fig, ax = plot_catalog_on_volume(vol, model, catalog)
        plt.close(fig)
