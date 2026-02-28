"""Tests for beachball focal mechanism plotting."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from opencoulomb.types.fault import FaultElement, Kode
from opencoulomb.types.grid import GridSpec
from opencoulomb.types.material import MaterialProperties
from opencoulomb.types.model import CoulombModel
from opencoulomb.types.result import CoulombResult, StressResult
from opencoulomb.viz.beachball import plot_beachball, plot_beachballs_on_map


def _make_simple_result() -> tuple[CoulombResult, CoulombModel]:
    """Create a minimal CoulombResult and CoulombModel for testing."""
    n = 25
    x = np.linspace(-10, 10, 5)
    y = np.linspace(-10, 10, 5)
    gx, gy = np.meshgrid(x, y)
    xf = gx.ravel()
    yf = gy.ravel()

    stress = StressResult(
        x=xf, y=yf, z=np.full(n, -10.0),
        ux=np.zeros(n), uy=np.zeros(n), uz=np.zeros(n),
        sxx=np.zeros(n), syy=np.zeros(n), szz=np.zeros(n),
        syz=np.zeros(n), sxz=np.zeros(n), sxy=np.zeros(n),
    )
    cfs = np.random.default_rng(42).standard_normal(n) * 0.1

    result = CoulombResult(
        stress=stress, cfs=cfs,
        shear=cfs * 0.8, normal=cfs * 0.2,
        receiver_strike=45.0, receiver_dip=60.0, receiver_rake=90.0,
        grid_shape=(5, 5),
    )

    source = FaultElement(
        x_start=-5, y_start=0, x_fin=5, y_fin=0,
        kode=Kode.STANDARD, slip_1=1.0, slip_2=0.0,
        dip=90.0, top_depth=0.0, bottom_depth=15.0,
    )
    receiver = FaultElement(
        x_start=-3, y_start=5, x_fin=3, y_fin=5,
        kode=Kode.STANDARD, slip_1=0.0, slip_2=0.0,
        dip=60.0, top_depth=0.0, bottom_depth=15.0,
    )
    model = CoulombModel(
        title="test", material=MaterialProperties(),
        faults=[source, receiver],
        grid=GridSpec(-10, -10, 10, 10, 5.0, 5.0, 10.0),
        n_fixed=1,
    )
    return result, model


class TestPlotBeachball:
    def test_plot_beachball_creates_collection(self):
        fig, ax = plt.subplots()
        plot_beachball(0, 90, 0, (0, 0), ax, size=20)
        # Should add at least one collection or patch
        assert len(ax.collections) > 0 or len(ax.patches) > 0
        plt.close(fig)

    def test_strike_slip_beachball(self):
        fig, ax = plt.subplots()
        plot_beachball(0, 90, 0, (5, 5), ax, facecolor="red")
        plt.close(fig)

    def test_thrust_beachball(self):
        fig, ax = plt.subplots()
        plot_beachball(0, 45, 90, (0, 0), ax, facecolor="blue")
        plt.close(fig)

    def test_normal_fault_beachball(self):
        fig, ax = plt.subplots()
        plot_beachball(0, 45, -90, (0, 0), ax, facecolor="green")
        plt.close(fig)

    def test_custom_size_and_colors(self):
        fig, ax = plt.subplots()
        plot_beachball(30, 60, 45, (1, 2), ax, size=30, facecolor="orange", bgcolor="gray")
        plt.close(fig)


class TestPlotBeachballsOnMap:
    def test_no_catalog_plots_receivers(self):
        result, model = _make_simple_result()
        fig, ax = plot_beachballs_on_map(result, model)
        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_returns_figure_and_axes(self):
        result, model = _make_simple_result()
        fig, ax = plot_beachballs_on_map(result, model)
        assert hasattr(fig, "savefig")
        plt.close(fig)

    def test_with_existing_axes(self):
        result, model = _make_simple_result()
        fig, ax = plt.subplots()
        fig2, ax2 = plot_beachballs_on_map(result, model, ax=ax)
        assert ax2 is ax
        plt.close(fig)

    def test_with_catalog(self):
        from opencoulomb.types.catalog import CatalogEvent, EarthquakeCatalog
        result, model = _make_simple_result()
        catalog = EarthquakeCatalog(events=[
            CatalogEvent(latitude=0.0, longitude=0.0, depth_km=10.0,
                        magnitude=5.0, time="2024-01-01"),
            CatalogEvent(latitude=5.0, longitude=5.0, depth_km=15.0,
                        magnitude=6.0, time="2024-01-02"),
        ])
        fig, ax = plot_beachballs_on_map(result, model, catalog=catalog)
        assert fig is not None
        plt.close(fig)

    def test_color_by_cfs_false(self):
        result, model = _make_simple_result()
        fig, ax = plot_beachballs_on_map(result, model, color_by_cfs=False)
        plt.close(fig)

    def test_size_by_magnitude_false(self):
        from opencoulomb.types.catalog import CatalogEvent, EarthquakeCatalog
        result, model = _make_simple_result()
        catalog = EarthquakeCatalog(events=[
            CatalogEvent(latitude=0.0, longitude=0.0, depth_km=10.0,
                        magnitude=5.0, time="2024-01-01"),
        ])
        fig, ax = plot_beachballs_on_map(
            result, model, catalog=catalog, size_by_magnitude=False,
        )
        plt.close(fig)
