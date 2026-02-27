"""Tests for output file writers (cou, csv, dat)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from opencoulomb.types.fault import FaultElement, Kode
from opencoulomb.types.grid import GridSpec
from opencoulomb.types.material import MaterialProperties
from opencoulomb.types.model import CoulombModel
from opencoulomb.types.result import CoulombResult, StressResult
from opencoulomb.types.section import CrossSectionResult, CrossSectionSpec

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def model_and_result() -> tuple[CoulombModel, CoulombResult]:
    """Minimal model + result pair for writer testing."""
    model = CoulombModel(
        title="Writer Test",
        material=MaterialProperties(poisson=0.25, young=8e5, friction=0.4),
        faults=[
            FaultElement(
                x_start=-5, y_start=0, x_fin=5, y_fin=0,
                kode=Kode.STANDARD, slip_1=1.0, slip_2=0.0,
                dip=90.0, top_depth=0.1, bottom_depth=10.0,
                label="Source",
            ),
        ],
        grid=GridSpec(
            start_x=-10, start_y=-10, finish_x=10, finish_y=10,
            x_inc=5.0, y_inc=5.0, depth=5.0,
        ),
        n_fixed=1,
    )
    grid = model.grid
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
    result = CoulombResult(
        stress=stress,
        cfs=rng.normal(0, 0.5, n),
        shear=rng.normal(0, 0.3, n),
        normal=rng.normal(0, 0.2, n),
        receiver_strike=0.0, receiver_dip=90.0, receiver_rake=0.0,
        grid_shape=(n_y, n_x),
    )
    return model, result


@pytest.fixture()
def section_result() -> CrossSectionResult:
    """Synthetic cross-section result."""
    n_horiz, n_vert = 6, 4
    rng = np.random.default_rng(99)
    shape = (n_vert, n_horiz)
    return CrossSectionResult(
        distance=np.linspace(0, 30, n_horiz),
        depth=np.linspace(0, 15, n_vert),
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
            start_x=0, start_y=0, finish_x=30, finish_y=0,
            depth_min=0, depth_max=15, z_inc=5.0,
        ),
    )


# ---------------------------------------------------------------------------
# COU writer
# ---------------------------------------------------------------------------


class TestDcffCouWriter:
    def test_creates_file(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
    ) -> None:
        from opencoulomb.io.cou_writer import write_dcff_cou

        model, result = model_and_result
        path = tmp_path / "dcff.cou"
        write_dcff_cou(result, model, path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_header_content(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
    ) -> None:
        from opencoulomb.io.cou_writer import write_dcff_cou

        model, result = model_and_result
        path = tmp_path / "dcff.cou"
        write_dcff_cou(result, model, path)
        text = path.read_text()
        assert "Writer Test" in text
        assert "friction" in text
        assert "X(km)" in text

    def test_row_count(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
    ) -> None:
        from opencoulomb.io.cou_writer import write_dcff_cou

        model, result = model_and_result
        path = tmp_path / "dcff.cou"
        write_dcff_cou(result, model, path)
        lines = path.read_text().strip().split("\n")
        # 3 header lines + n data lines
        assert len(lines) == 3 + result.stress.n_points


class TestSectionCouWriter:
    def test_creates_file(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
        section_result: CrossSectionResult,
    ) -> None:
        from opencoulomb.io.cou_writer import write_section_cou

        model, _ = model_and_result
        path = tmp_path / "section.cou"
        write_section_cou(section_result, model, path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_header_has_profile(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
        section_result: CrossSectionResult,
    ) -> None:
        from opencoulomb.io.cou_writer import write_section_cou

        model, _ = model_and_result
        path = tmp_path / "section.cou"
        write_section_cou(section_result, model, path)
        text = path.read_text()
        assert "Profile:" in text
        assert "Dist(km)" in text

    def test_row_count(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
        section_result: CrossSectionResult,
    ) -> None:
        from opencoulomb.io.cou_writer import write_section_cou

        model, _ = model_and_result
        path = tmp_path / "section.cou"
        write_section_cou(section_result, model, path)
        lines = path.read_text().strip().split("\n")
        n_vert, n_horiz = section_result.cfs.shape
        assert len(lines) == 3 + n_vert * n_horiz


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------


class TestCsvWriter:
    def test_creates_file(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
    ) -> None:
        from opencoulomb.io.csv_writer import write_csv

        _, result = model_and_result
        path = tmp_path / "output.csv"
        write_csv(result, path)
        assert path.exists()

    def test_header_row(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
    ) -> None:
        from opencoulomb.io.csv_writer import write_csv

        _, result = model_and_result
        path = tmp_path / "output.csv"
        write_csv(result, path)
        header = path.read_text().split("\n")[0]
        assert "x_km" in header
        assert "cfs_bar" in header

    def test_row_count(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
    ) -> None:
        from opencoulomb.io.csv_writer import write_csv

        _, result = model_and_result
        path = tmp_path / "output.csv"
        write_csv(result, path)
        lines = [line for line in path.read_text().strip().split("\n") if line]
        # 1 header + n data rows
        assert len(lines) == 1 + result.stress.n_points

    def test_column_count(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
    ) -> None:
        from opencoulomb.io.csv_writer import write_csv

        _, result = model_and_result
        path = tmp_path / "output.csv"
        write_csv(result, path)
        lines = path.read_text().strip().split("\n")
        # Check data row has 14 columns
        data_cols = lines[1].split(",")
        assert len(data_cols) == 14


class TestSummaryWriter:
    def test_creates_file(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
    ) -> None:
        from opencoulomb.io.csv_writer import write_summary

        model, result = model_and_result
        path = tmp_path / "summary.txt"
        write_summary(result, model, path)
        assert path.exists()

    def test_contains_model_info(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
    ) -> None:
        from opencoulomb.io.csv_writer import write_summary

        model, result = model_and_result
        path = tmp_path / "summary.txt"
        write_summary(result, model, path)
        text = path.read_text()
        assert "Writer Test" in text
        assert "Poisson" in text
        assert "CFS Results" in text
        assert "Displacement" in text


# ---------------------------------------------------------------------------
# DAT writer
# ---------------------------------------------------------------------------


class TestDatWriter:
    def test_coulomb_dat_creates_file(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
    ) -> None:
        from opencoulomb.io.dat_writer import write_coulomb_dat

        _, result = model_and_result
        path = tmp_path / "cfs.dat"
        write_coulomb_dat(result, path, field="cfs")
        assert path.exists()

    def test_coulomb_dat_shape(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
    ) -> None:
        from opencoulomb.io.dat_writer import write_coulomb_dat

        _, result = model_and_result
        path = tmp_path / "cfs.dat"
        write_coulomb_dat(result, path, field="cfs")
        data = np.loadtxt(path)
        n_y, n_x = result.grid_shape
        assert data.shape == (n_y, n_x)

    def test_coulomb_dat_fields(
        self, tmp_path: Path,
        model_and_result: tuple[CoulombModel, CoulombResult],
    ) -> None:
        from opencoulomb.io.dat_writer import write_coulomb_dat

        _, result = model_and_result
        for field in ("cfs", "shear", "normal", "ux", "uy", "uz"):
            path = tmp_path / f"{field}.dat"
            write_coulomb_dat(result, path, field=field)
            assert path.exists()

    def test_fault_surface_dat(self, tmp_path: Path) -> None:
        from opencoulomb.io.dat_writer import write_fault_surface_dat

        faults = [
            FaultElement(
                x_start=-5, y_start=0, x_fin=5, y_fin=0,
                kode=Kode.STANDARD, slip_1=1.0, slip_2=0.0,
                dip=90.0, top_depth=0.1, bottom_depth=10.0,
                label="Test Fault",
            ),
        ]
        path = tmp_path / "faults.dat"
        write_fault_surface_dat(faults, path)
        assert path.exists()
        text = path.read_text()
        assert "Test Fault" in text
        assert ">" in text  # GMT segment marker

    def test_fault_surface_dat_multiple(self, tmp_path: Path) -> None:
        from opencoulomb.io.dat_writer import write_fault_surface_dat

        faults = [
            FaultElement(
                x_start=-5, y_start=0, x_fin=5, y_fin=0,
                kode=Kode.STANDARD, slip_1=1.0, slip_2=0.0,
                dip=90.0, top_depth=0.1, bottom_depth=10.0,
            ),
            FaultElement(
                x_start=0, y_start=-5, x_fin=0, y_fin=5,
                kode=Kode.STANDARD, slip_1=0.5, slip_2=0.0,
                dip=45.0, top_depth=0.1, bottom_depth=8.0,
            ),
        ]
        path = tmp_path / "faults2.dat"
        write_fault_surface_dat(faults, path)
        text = path.read_text()
        # Should have 2 segment markers
        assert text.count("> ") == 2

    def test_fault_polygon_vertical_dip(self, tmp_path: Path) -> None:
        """Vertical fault polygon should collapse to trace (4 corners on trace)."""
        from opencoulomb.io.dat_writer import _fault_polygon_corners

        fault = FaultElement(
            x_start=-5, y_start=0, x_fin=5, y_fin=0,
            kode=Kode.STANDARD, slip_1=1.0, slip_2=0.0,
            dip=90.0, top_depth=0.0, bottom_depth=10.0,
        )
        corners = _fault_polygon_corners(fault)
        assert len(corners) == 4
        # All y-coords should be 0 (no offset for vertical dip)
        for _cx, cy in corners:
            assert cy == pytest.approx(0.0, abs=1e-9)

    def test_fault_polygon_45_dip(self, tmp_path: Path) -> None:
        """45-degree dipping fault should have bottom corners offset perpendicular to strike."""
        from opencoulomb.io.dat_writer import _fault_polygon_corners

        fault = FaultElement(
            x_start=0, y_start=0, x_fin=10, y_fin=0,
            kode=Kode.STANDARD, slip_1=1.0, slip_2=0.0,
            dip=45.0, top_depth=0.0, bottom_depth=10.0,
        )
        corners = _fault_polygon_corners(fault)
        assert len(corners) == 4
        # Top corners (idx 0,1) should be on trace (y=0)
        assert corners[0][1] == pytest.approx(0.0, abs=1e-9)
        assert corners[1][1] == pytest.approx(0.0, abs=1e-9)
        # Bottom corners (idx 2,3) should be offset by ~10 km (depth/tan(45°)=10)
        assert corners[2][1] == pytest.approx(-10.0, abs=1e-6)
        assert corners[3][1] == pytest.approx(-10.0, abs=1e-6)

    def test_fault_polygon_closed(self, tmp_path: Path) -> None:
        """Written polygon should be closed (last point == first point)."""
        from opencoulomb.io.dat_writer import write_fault_surface_dat

        faults = [
            FaultElement(
                x_start=0, y_start=0, x_fin=10, y_fin=0,
                kode=Kode.STANDARD, slip_1=1.0, slip_2=0.0,
                dip=60.0, top_depth=0.0, bottom_depth=10.0,
            ),
        ]
        path = tmp_path / "poly.dat"
        write_fault_surface_dat(faults, path)
        lines = path.read_text().strip().split("\n")
        # Skip comments and segment marker; data lines are the polygon
        data_lines = [ln for ln in lines if not ln.startswith("#") and not ln.startswith(">")]
        # 4 corners + 1 closing point = 5 data lines
        assert len(data_lines) == 5
        assert data_lines[0] == data_lines[-1]
