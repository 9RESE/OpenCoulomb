"""End-to-end validation tests for OpenCoulomb.

Level 5 of the 6-level validation suite.
Tests the complete workflow: .inp file → CLI → output files → verify content.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from click.testing import CliRunner

from opencoulomb.cli.main import cli

TESTS_DIR = Path(__file__).parent.parent
REAL_INP_DIR = TESTS_DIR / "fixtures" / "inp_files" / "real"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def inp_file() -> Path:
    path = REAL_INP_DIR / "simplest_receiver.inp"
    if not path.exists():
        pytest.skip("Test fixture simplest_receiver.inp not available")
    return path


@pytest.mark.e2e
class TestEndToEndCompute:
    """Full pipeline: .inp → compute → output files → verify."""

    def test_compute_all_formats(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        """Compute with -f all should produce cou, csv, and dat files."""
        result = runner.invoke(cli, [
            "compute", str(inp_file), "-o", str(tmp_path), "-f", "all",
        ])
        assert result.exit_code == 0

        cou_files = list(tmp_path.glob("*_dcff.cou"))
        csv_files = list(tmp_path.glob("*.csv"))
        assert len(cou_files) >= 1
        assert len(csv_files) >= 1

    def test_csv_output_parseable(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        """CSV output should be parseable with numpy."""
        result = runner.invoke(cli, [
            "compute", str(inp_file), "-o", str(tmp_path), "-f", "csv",
        ])
        assert result.exit_code == 0

        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1

        data = np.genfromtxt(csv_files[0], delimiter=",", skip_header=1)
        assert data.ndim == 2
        assert data.shape[1] == 14  # x, y, z, ux, uy, uz, sxx-sxy, cfs, shear, normal
        assert not np.any(np.isnan(data))

    def test_cou_output_has_header_and_data(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        """COU output should have header lines and data rows."""
        result = runner.invoke(cli, [
            "compute", str(inp_file), "-o", str(tmp_path), "-f", "cou",
        ])
        assert result.exit_code == 0

        cou_files = list(tmp_path.glob("*_dcff.cou"))
        assert len(cou_files) == 1

        text = cou_files[0].read_text()
        lines = text.strip().split("\n")
        # At least header + data rows
        assert len(lines) > 10
        # File should contain column labels somewhere in header
        assert "X(km)" in text

    def test_dat_output_is_grid_matrix(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        """DAT output should be a loadable numerical matrix."""
        result = runner.invoke(cli, [
            "compute", str(inp_file), "-o", str(tmp_path), "-f", "dat",
        ])
        assert result.exit_code == 0

        dat_files = list(tmp_path.glob("*.dat"))
        assert len(dat_files) >= 1

        data = np.loadtxt(dat_files[0])
        assert data.ndim == 2
        assert data.shape[0] > 0
        assert data.shape[1] > 0


@pytest.mark.e2e
class TestEndToEndPlot:
    """Full pipeline: .inp → plot → image file."""

    def test_plot_produces_image(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")

        output = tmp_path / "cfs_map.png"
        result = runner.invoke(cli, [
            "plot", str(inp_file), "-o", str(output), "-t", "cfs",
        ])
        assert result.exit_code == 0
        assert output.exists()
        assert output.stat().st_size > 1000  # should be a real image


@pytest.mark.e2e
class TestEndToEndConvert:
    """Full pipeline: .inp → convert → single output format."""

    def test_convert_roundtrip_csv(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        """Convert to CSV, then verify the CSV is valid."""
        output = tmp_path / "converted.csv"
        result = runner.invoke(cli, [
            "convert", str(inp_file), "-f", "csv", "-o", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()

        data = np.genfromtxt(output, delimiter=",", skip_header=1)
        assert data.ndim == 2
        assert data.shape[0] > 0


@pytest.mark.e2e
class TestEndToEndValidate:
    """Full pipeline: validate → report."""

    def test_validate_produces_report(
        self, runner: CliRunner, inp_file: Path,
    ) -> None:
        result = runner.invoke(cli, ["validate", str(inp_file)])
        assert result.exit_code == 0
        assert "Model:" in result.output
        assert "Summary:" in result.output


@pytest.mark.e2e
class TestEndToEndInfo:
    """Full pipeline: info → summary."""

    def test_info_produces_summary(
        self, runner: CliRunner, inp_file: Path,
    ) -> None:
        result = runner.invoke(cli, ["info", str(inp_file)])
        assert result.exit_code == 0
        assert "Model:" in result.output
