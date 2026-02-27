"""Tests for the CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from opencoulomb.cli.main import cli

TESTS_DIR = Path(__file__).parent.parent
REAL_INP_DIR = TESTS_DIR / "fixtures" / "inp_files" / "real"


@pytest.fixture()
def runner() -> CliRunner:
    """CLI test runner."""
    return CliRunner()


@pytest.fixture()
def inp_file() -> Path:
    """Return path to a real .inp file for testing."""
    path = REAL_INP_DIR / "simplest_receiver.inp"
    if not path.exists():
        pytest.skip("Test fixture simplest_receiver.inp not available")
    return path


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


class TestCliGroup:
    def test_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "OpenCoulomb" in result.output

    def test_version(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

    def test_subcommands_listed(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--help"])
        assert "compute" in result.output
        assert "convert" in result.output
        assert "plot" in result.output
        assert "info" in result.output
        assert "validate" in result.output


# ---------------------------------------------------------------------------
# Info command
# ---------------------------------------------------------------------------


class TestInfoCommand:
    def test_info_output(self, runner: CliRunner, inp_file: Path) -> None:
        result = runner.invoke(cli, ["info", str(inp_file)])
        assert result.exit_code == 0
        assert "Model:" in result.output
        assert "Material:" in result.output
        assert "Grid:" in result.output
        assert "Faults:" in result.output

    def test_info_missing_file(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["info", "/nonexistent/file.inp"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Compute command
# ---------------------------------------------------------------------------


class TestComputeCommand:
    def test_compute_all(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        result = runner.invoke(cli, [
            "compute", str(inp_file),
            "-o", str(tmp_path),
            "-f", "all",
        ])
        assert result.exit_code == 0
        assert "Done" in result.output
        # Check that output files were created
        assert any(tmp_path.glob("*_dcff.cou"))
        assert any(tmp_path.glob("*.csv"))

    def test_compute_cou_only(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        result = runner.invoke(cli, [
            "compute", str(inp_file),
            "-o", str(tmp_path),
            "-f", "cou",
        ])
        assert result.exit_code == 0

    def test_compute_csv_only(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        result = runner.invoke(cli, [
            "compute", str(inp_file),
            "-o", str(tmp_path),
            "-f", "csv",
        ])
        assert result.exit_code == 0

    def test_compute_dat_only(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        result = runner.invoke(cli, [
            "compute", str(inp_file),
            "-o", str(tmp_path),
            "-f", "dat",
        ])
        assert result.exit_code == 0

    def test_compute_verbose(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        result = runner.invoke(cli, [
            "compute", str(inp_file),
            "-o", str(tmp_path),
            "-v",
        ])
        assert result.exit_code == 0

    def test_compute_missing_file(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["compute", "/nonexistent/file.inp"])
        assert result.exit_code != 0

    def test_compute_default_output_dir(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Copy inp file to tmp_path so outputs go there
        import shutil
        tmp_inp = tmp_path / inp_file.name
        shutil.copy(inp_file, tmp_inp)

        result = runner.invoke(cli, [
            "compute", str(tmp_inp),
            "-f", "csv",
        ])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Plot command
# ---------------------------------------------------------------------------


class TestPlotCommand:
    def test_plot_cfs(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")

        output = tmp_path / "cfs.png"
        result = runner.invoke(cli, [
            "plot", str(inp_file),
            "-o", str(output),
            "-t", "cfs",
        ])
        assert result.exit_code == 0
        assert output.exists()

    def test_plot_displacement(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")

        output = tmp_path / "disp.png"
        result = runner.invoke(cli, [
            "plot", str(inp_file),
            "-o", str(output),
            "-t", "displacement",
        ])
        assert result.exit_code == 0
        assert output.exists()

    def test_plot_with_vmax(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")

        output = tmp_path / "vmax.png"
        result = runner.invoke(cli, [
            "plot", str(inp_file),
            "-o", str(output),
            "--vmax", "1.0",
        ])
        assert result.exit_code == 0

    def test_plot_no_faults(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")

        output = tmp_path / "nofaults.png"
        result = runner.invoke(cli, [
            "plot", str(inp_file),
            "-o", str(output),
            "--no-faults",
        ])
        assert result.exit_code == 0

    def test_plot_default_output(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        import matplotlib
        matplotlib.use("Agg")

        import shutil
        tmp_inp = tmp_path / inp_file.name
        shutil.copy(inp_file, tmp_inp)

        result = runner.invoke(cli, ["plot", str(tmp_inp)])
        assert result.exit_code == 0

    def test_plot_missing_file(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["plot", "/nonexistent/file.inp"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# IO module exports
# ---------------------------------------------------------------------------


class TestIOExports:
    def test_all_exports(self) -> None:
        from opencoulomb import io
        expected = [
            "parse_inp_string", "read_inp",
            "write_coulomb_dat", "write_csv", "write_dcff_cou",
            "write_fault_surface_dat", "write_section_cou", "write_summary",
        ]
        for name in expected:
            assert hasattr(io, name), f"Missing export: {name}"


class TestVizExports:
    def test_all_exports(self) -> None:
        from opencoulomb import viz
        expected = [
            "plot_cfs_map", "plot_cross_section", "plot_displacement",
            "plot_fault_traces", "save_figure",
            "coulomb_cmap", "displacement_cmap", "stress_cmap", "symmetric_norm",
            "create_figure", "add_colorbar", "set_axis_labels", "finalize_figure",
            "publication_style", "screen_style",
            "PUBLICATION_RCPARAMS", "SCREEN_RCPARAMS",
        ]
        for name in expected:
            assert hasattr(viz, name), f"Missing export: {name}"


# ---------------------------------------------------------------------------
# Validate command
# ---------------------------------------------------------------------------


class TestValidateCommand:
    def test_validate_valid_file(self, runner: CliRunner, inp_file: Path) -> None:
        result = runner.invoke(cli, ["validate", str(inp_file)])
        assert result.exit_code == 0
        assert "Model:" in result.output
        assert "Summary:" in result.output

    def test_validate_missing_file(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["validate", "/nonexistent/file.inp"])
        assert result.exit_code != 0

    def test_validate_verbose(self, runner: CliRunner, inp_file: Path) -> None:
        result = runner.invoke(cli, ["validate", str(inp_file), "-v"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Convert command
# ---------------------------------------------------------------------------


class TestConvertCommand:
    def test_convert_to_csv(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        output = tmp_path / "output.csv"
        result = runner.invoke(cli, [
            "convert", str(inp_file), "-f", "csv", "-o", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()

    def test_convert_to_cou(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        output = tmp_path / "output.cou"
        result = runner.invoke(cli, [
            "convert", str(inp_file), "-f", "cou", "-o", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()

    def test_convert_to_dat(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        output = tmp_path / "output.dat"
        result = runner.invoke(cli, [
            "convert", str(inp_file), "-f", "dat", "-o", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()

    def test_convert_to_summary(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        output = tmp_path / "output.txt"
        result = runner.invoke(cli, [
            "convert", str(inp_file), "-f", "summary", "-o", str(output),
        ])
        assert result.exit_code == 0
        assert output.exists()

    def test_convert_default_output_path(
        self, runner: CliRunner, inp_file: Path, tmp_path: Path,
    ) -> None:
        import shutil

        tmp_inp = tmp_path / inp_file.name
        shutil.copy(inp_file, tmp_inp)
        result = runner.invoke(cli, [
            "convert", str(tmp_inp), "-f", "csv",
        ])
        assert result.exit_code == 0

    def test_convert_missing_format(self, runner: CliRunner, inp_file: Path) -> None:
        result = runner.invoke(cli, ["convert", str(inp_file)])
        assert result.exit_code != 0
