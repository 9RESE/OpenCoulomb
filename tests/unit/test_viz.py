"""Tests for the visualization module."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # non-interactive backend — must be before pyplot import
import matplotlib.pyplot as plt
import numpy as np
import pytest

from opencoulomb.types.fault import FaultElement, Kode
from opencoulomb.types.grid import GridSpec
from opencoulomb.types.material import MaterialProperties
from opencoulomb.types.model import CoulombModel
from opencoulomb.types.result import CoulombResult, StressResult
from opencoulomb.types.section import CrossSectionResult, CrossSectionSpec

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def simple_model() -> CoulombModel:
    """Minimal model for viz testing."""
    return CoulombModel(
        title="Test Model",
        material=MaterialProperties(poisson=0.25, young=8e5, friction=0.4),
        faults=[
            FaultElement(
                x_start=-10, y_start=0, x_fin=10, y_fin=0,
                kode=Kode.STANDARD, slip_1=1.0, slip_2=0.0,
                dip=90.0, top_depth=0.1, bottom_depth=15.0,
                label="Source 1",
            ),
            FaultElement(
                x_start=5, y_start=-5, x_fin=5, y_fin=5,
                kode=Kode.STANDARD, slip_1=0.0, slip_2=0.0,
                dip=45.0, top_depth=0.1, bottom_depth=10.0,
                label="Receiver 1",
            ),
        ],
        grid=GridSpec(
            start_x=-20, start_y=-20, finish_x=20, finish_y=20,
            x_inc=5.0, y_inc=5.0, depth=5.0,
        ),
        n_fixed=1,
    )


@pytest.fixture()
def simple_result(simple_model: CoulombModel) -> CoulombResult:
    """Synthetic CoulombResult for viz testing."""
    grid = simple_model.grid
    n_x = grid.n_x
    n_y = grid.n_y
    n = n_x * n_y

    rng = np.random.default_rng(42)
    x = np.linspace(grid.start_x, grid.finish_x, n_x)
    y = np.linspace(grid.start_y, grid.finish_y, n_y)
    gx, gy = np.meshgrid(x, y)

    stress = StressResult(
        x=gx.ravel(), y=gy.ravel(), z=np.full(n, -5.0),
        ux=rng.normal(0, 0.01, n), uy=rng.normal(0, 0.01, n),
        uz=rng.normal(0, 0.001, n),
        sxx=rng.normal(0, 1, n), syy=rng.normal(0, 1, n),
        szz=rng.normal(0, 1, n), syz=rng.normal(0, 0.5, n),
        sxz=rng.normal(0, 0.5, n), sxy=rng.normal(0, 0.5, n),
    )
    return CoulombResult(
        stress=stress,
        cfs=rng.normal(0, 0.5, n),
        shear=rng.normal(0, 0.3, n),
        normal=rng.normal(0, 0.2, n),
        receiver_strike=0.0, receiver_dip=45.0, receiver_rake=0.0,
        grid_shape=(n_y, n_x),
    )


@pytest.fixture()
def simple_section() -> CrossSectionResult:
    """Synthetic CrossSectionResult for viz testing."""
    n_horiz, n_vert = 10, 8
    rng = np.random.default_rng(99)
    shape = (n_vert, n_horiz)
    return CrossSectionResult(
        distance=np.linspace(0, 50, n_horiz),
        depth=np.linspace(0, 20, n_vert),
        cfs=rng.normal(0, 0.5, shape),
        shear=rng.normal(0, 0.3, shape),
        normal=rng.normal(0, 0.2, shape),
        ux=rng.normal(0, 0.01, shape),
        uy=rng.normal(0, 0.01, shape),
        uz=rng.normal(0, 0.001, shape),
        sxx=rng.normal(0, 1, shape),
        syy=rng.normal(0, 1, shape),
        szz=rng.normal(0, 1, shape),
        syz=rng.normal(0, 0.5, shape),
        sxz=rng.normal(0, 0.5, shape),
        sxy=rng.normal(0, 0.5, shape),
        spec=CrossSectionSpec(
            start_x=-10, start_y=0, finish_x=40, finish_y=0,
            depth_min=0, depth_max=20, z_inc=2.5,
        ),
    )


# ---------------------------------------------------------------------------
# Base utilities
# ---------------------------------------------------------------------------


class TestBase:
    def test_create_figure(self) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz._base import create_figure

        fig, ax = create_figure(figsize=(8, 6), dpi=100)
        assert fig is not None
        assert ax is not None

    def test_add_colorbar(self) -> None:
        import matplotlib
        matplotlib.use("Agg")

        from opencoulomb.viz._base import add_colorbar

        _fig, ax = plt.subplots()
        im = ax.imshow([[0, 1], [2, 3]])
        cbar = add_colorbar(im, ax, label="Test")
        assert cbar is not None

    def test_finalize_figure(self) -> None:
        import matplotlib
        matplotlib.use("Agg")

        from opencoulomb.viz._base import finalize_figure

        fig, _ = plt.subplots()
        result = finalize_figure(fig, title="Test Title")
        assert result is fig


# ---------------------------------------------------------------------------
# Colormaps
# ---------------------------------------------------------------------------


class TestColormaps:
    def test_coulomb_cmap(self) -> None:
        from opencoulomb.viz.colormaps import coulomb_cmap
        cmap = coulomb_cmap()
        assert cmap.name == "RdBu_r"

    def test_displacement_cmap(self) -> None:
        from opencoulomb.viz.colormaps import displacement_cmap
        cmap = displacement_cmap()
        assert cmap.name == "viridis"

    def test_symmetric_norm(self) -> None:
        from opencoulomb.viz.colormaps import symmetric_norm
        data = np.array([-2.0, 0.5, 3.0])
        norm = symmetric_norm(data)
        assert norm.vmin == -3.0
        assert norm.vmax == 3.0

    def test_symmetric_norm_explicit_vmax(self) -> None:
        from opencoulomb.viz.colormaps import symmetric_norm
        data = np.array([-2.0, 0.5, 3.0])
        norm = symmetric_norm(data, vmax=5.0)
        assert norm.vmin == -5.0
        assert norm.vmax == 5.0

    def test_symmetric_norm_all_zero(self) -> None:
        from opencoulomb.viz.colormaps import symmetric_norm
        data = np.zeros(5)
        norm = symmetric_norm(data)
        assert norm.vmax == 1.0  # fallback


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------


class TestStyles:
    def test_publication_style(self) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.styles import publication_style

        with publication_style():
            from matplotlib import rcParams
            assert rcParams["figure.dpi"] == 300

    def test_screen_style(self) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.styles import screen_style

        with screen_style():
            from matplotlib import rcParams
            assert rcParams["figure.dpi"] == 150


# ---------------------------------------------------------------------------
# Maps
# ---------------------------------------------------------------------------


class TestCfsMap:
    def test_plot_returns_fig_ax(
        self, simple_result: CoulombResult, simple_model: CoulombModel,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.maps import plot_cfs_map

        fig, ax = plot_cfs_map(simple_result, simple_model)
        assert fig is not None
        assert ax is not None

    def test_plot_with_existing_axes(
        self, simple_result: CoulombResult, simple_model: CoulombModel,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")

        from opencoulomb.viz.maps import plot_cfs_map

        _, existing_ax = plt.subplots()
        _fig, ax = plot_cfs_map(simple_result, simple_model, ax=existing_ax)
        assert ax is existing_ax

    def test_plot_no_faults(
        self, simple_result: CoulombResult, simple_model: CoulombModel,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.maps import plot_cfs_map

        fig, _ax = plot_cfs_map(simple_result, simple_model, show_faults=False)
        assert fig is not None

    def test_plot_with_vmax(
        self, simple_result: CoulombResult, simple_model: CoulombModel,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.maps import plot_cfs_map

        fig, _ax = plot_cfs_map(simple_result, simple_model, vmax=1.0)
        assert fig is not None


# ---------------------------------------------------------------------------
# Faults
# ---------------------------------------------------------------------------


class TestFaultTraces:
    def test_plot_returns_fig_ax(self, simple_model: CoulombModel) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.faults import plot_fault_traces

        fig, ax = plot_fault_traces(simple_model)
        assert fig is not None
        assert ax is not None

    def test_plot_on_existing_axes(self, simple_model: CoulombModel) -> None:
        import matplotlib
        matplotlib.use("Agg")

        from opencoulomb.viz.faults import plot_fault_traces

        _, existing_ax = plt.subplots()
        _fig, ax = plot_fault_traces(simple_model, ax=existing_ax)
        assert ax is existing_ax

    def test_no_labels(self, simple_model: CoulombModel) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.faults import plot_fault_traces

        fig, _ax = plot_fault_traces(simple_model, show_labels=False)
        assert fig is not None


# ---------------------------------------------------------------------------
# Cross-section plot
# ---------------------------------------------------------------------------


class TestCrossSectionPlot:
    def test_plot_cfs(self, simple_section: CrossSectionResult) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.sections import plot_cross_section

        fig, ax = plot_cross_section(simple_section, field="cfs")
        assert fig is not None
        assert ax is not None

    def test_plot_shear(self, simple_section: CrossSectionResult) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.sections import plot_cross_section

        fig, _ax = plot_cross_section(simple_section, field="shear")
        assert fig is not None

    def test_plot_normal(self, simple_section: CrossSectionResult) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.sections import plot_cross_section

        fig, _ax = plot_cross_section(simple_section, field="normal")
        assert fig is not None

    def test_depth_inverted(self, simple_section: CrossSectionResult) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.sections import plot_cross_section

        _, ax = plot_cross_section(simple_section)
        # y-axis should be inverted (depth increases downward)
        assert ax.yaxis_inverted()

    def test_existing_axes_used(self, simple_section: CrossSectionResult) -> None:
        """When ax is passed, it is used and fig is extracted from it (lines 37-40)."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from opencoulomb.viz.sections import plot_cross_section

        fig0, ax0 = plt.subplots(1, 1)
        fig_ret, ax_ret = plot_cross_section(simple_section, ax=ax0)
        assert ax_ret is ax0
        assert fig_ret is fig0
        plt.close("all")

    def test_unknown_field_raises(self, simple_section: CrossSectionResult) -> None:
        """Unknown field name raises ValueError (line 44)."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from opencoulomb.viz.sections import plot_cross_section

        with pytest.raises(ValueError, match="Unknown field"):
            plot_cross_section(simple_section, field="invalid_field")
        plt.close("all")


# ---------------------------------------------------------------------------
# Displacement
# ---------------------------------------------------------------------------


class TestDisplacement:
    def test_horizontal_quiver(
        self, simple_result: CoulombResult, simple_model: CoulombModel,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.displacement import plot_displacement

        fig, _ax = plot_displacement(simple_result, simple_model, component="horizontal")
        assert fig is not None

    def test_vertical_contour(
        self, simple_result: CoulombResult, simple_model: CoulombModel,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.displacement import plot_displacement

        fig, _ax = plot_displacement(simple_result, simple_model, component="vertical")
        assert fig is not None

    def test_no_faults(
        self, simple_result: CoulombResult, simple_model: CoulombModel,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from opencoulomb.viz.displacement import plot_displacement

        fig, _ax = plot_displacement(
            simple_result, simple_model, show_faults=False,
        )
        assert fig is not None


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


class TestExport:
    def test_save_png(
        self, tmp_path: object, simple_result: CoulombResult,
        simple_model: CoulombModel,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from pathlib import Path

        from opencoulomb.viz.export import save_figure
        from opencoulomb.viz.maps import plot_cfs_map

        fig, _ = plot_cfs_map(simple_result, simple_model)
        out = save_figure(fig, Path(str(tmp_path)) / "test.png")
        assert out.exists()
        assert out.suffix == ".png"

    def test_save_pdf(
        self, tmp_path: object, simple_result: CoulombResult,
        simple_model: CoulombModel,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from pathlib import Path

        from opencoulomb.viz.export import save_figure
        from opencoulomb.viz.maps import plot_cfs_map

        fig, _ = plot_cfs_map(simple_result, simple_model)
        out = save_figure(fig, Path(str(tmp_path)) / "test.pdf")
        assert out.exists()

    def test_save_svg(
        self, tmp_path: object, simple_result: CoulombResult,
        simple_model: CoulombModel,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from pathlib import Path

        from opencoulomb.viz.export import save_figure
        from opencoulomb.viz.maps import plot_cfs_map

        fig, _ = plot_cfs_map(simple_result, simple_model)
        out = save_figure(fig, Path(str(tmp_path)) / "test.svg")
        assert out.exists()

    def test_unsupported_format(self) -> None:
        import matplotlib
        matplotlib.use("Agg")

        from opencoulomb.viz.export import save_figure

        fig, _ = plt.subplots()
        with pytest.raises(ValueError, match="Unsupported format"):
            save_figure(fig, "test_file.xyz")

    def test_save_with_dpi(
        self, tmp_path: object,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")
        from pathlib import Path

        from opencoulomb.viz.export import save_figure

        fig, _ = plt.subplots()
        out = save_figure(fig, Path(str(tmp_path)) / "test_dpi.png", dpi=72)
        assert out.exists()
