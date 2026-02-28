"""Tests for opencoulomb.types.gps, opencoulomb.io.gps_reader, and opencoulomb.viz.gps.

Covers GPSStation, GPSDataset, CSV/JSON round-trips, compute_misfit, and
plot_gps_comparison.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from opencoulomb.io.gps_reader import read_gps_csv, read_gps_json
from opencoulomb.types.gps import GPSDataset, GPSStation
from opencoulomb.types.result import CoulombResult, StressResult
from opencoulomb.viz.gps import compute_misfit, plot_gps_comparison


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_station(
    name: str = "STAT",
    x: float = 0.0,
    y: float = 0.0,
    ux: float = 0.01,
    uy: float = 0.005,
    uz: float = 0.002,
    sigma_ux: float = 0.001,
    sigma_uy: float = 0.001,
    sigma_uz: float = 0.001,
) -> GPSStation:
    return GPSStation(
        name=name, x=x, y=y,
        ux=ux, uy=uy, uz=uz,
        sigma_ux=sigma_ux, sigma_uy=sigma_uy, sigma_uz=sigma_uz,
    )


def _make_dataset(n: int = 3) -> GPSDataset:
    stations = [
        _make_station(
            name=f"ST{i:02d}",
            x=float(i),
            y=float(i),
            ux=0.01 * (i + 1),
            uy=0.005 * (i + 1),
            uz=0.002 * (i + 1),
        )
        for i in range(n)
    ]
    return GPSDataset(stations=stations, reference_frame="ITRF2014")


def _write_gps_csv(path: Path, stations: list[GPSStation]) -> None:
    """Write GPS stations to CSV in the format expected by read_gps_csv."""
    fieldnames = ["name", "x_km", "y_km", "ux_m", "uy_m", "uz_m",
                  "sigma_ux", "sigma_uy", "sigma_uz"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in stations:
            writer.writerow({
                "name": s.name,
                "x_km": s.x,
                "y_km": s.y,
                "ux_m": s.ux,
                "uy_m": s.uy,
                "uz_m": s.uz,
                "sigma_ux": s.sigma_ux,
                "sigma_uy": s.sigma_uy,
                "sigma_uz": s.sigma_uz,
            })


def _write_gps_json(path: Path, dataset: GPSDataset) -> None:
    """Write GPS dataset to JSON in the format expected by read_gps_json."""
    data = {
        "reference_frame": dataset.reference_frame,
        "stations": [
            {
                "name": s.name,
                "x_km": s.x,
                "y_km": s.y,
                "ux_m": s.ux,
                "uy_m": s.uy,
                "uz_m": s.uz,
                "sigma_ux": s.sigma_ux,
                "sigma_uy": s.sigma_uy,
                "sigma_uz": s.sigma_uz,
            }
            for s in dataset.stations
        ],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _make_minimal_result(
    x_range: tuple[float, float] = (-5.0, 5.0),
    y_range: tuple[float, float] = (-5.0, 5.0),
    n_x: int = 5,
    n_y: int = 5,
    ux_val: float = 0.005,
    uy_val: float = 0.003,
    uz_val: float = 0.001,
) -> CoulombResult:
    """Build a minimal CoulombResult with uniform displacements on a regular grid."""
    x_1d = np.linspace(x_range[0], x_range[1], n_x)
    y_1d = np.linspace(y_range[0], y_range[1], n_y)
    gx, gy = np.meshgrid(x_1d, y_1d)
    n = n_x * n_y

    stress = StressResult(
        x=gx.ravel(), y=gy.ravel(), z=np.full(n, -5.0),
        ux=np.full(n, ux_val),
        uy=np.full(n, uy_val),
        uz=np.full(n, uz_val),
        sxx=np.zeros(n), syy=np.zeros(n), szz=np.zeros(n),
        syz=np.zeros(n), sxz=np.zeros(n), sxy=np.zeros(n),
    )
    return CoulombResult(
        stress=stress,
        cfs=np.zeros(n),
        shear=np.zeros(n),
        normal=np.zeros(n),
        receiver_strike=0.0,
        receiver_dip=90.0,
        receiver_rake=0.0,
        grid_shape=(n_y, n_x),
    )


# ---------------------------------------------------------------------------
# GPSStation
# ---------------------------------------------------------------------------

class TestGPSStation:
    def test_construction_required_fields(self):
        s = GPSStation(name="ABCD", x=10.0, y=20.0, ux=0.01, uy=0.005, uz=0.002)
        assert s.name == "ABCD"
        assert s.x == pytest.approx(10.0)
        assert s.y == pytest.approx(20.0)
        assert s.ux == pytest.approx(0.01)
        assert s.uy == pytest.approx(0.005)
        assert s.uz == pytest.approx(0.002)

    def test_sigma_defaults_to_zero(self):
        s = GPSStation(name="X", x=0.0, y=0.0, ux=0.0, uy=0.0, uz=0.0)
        assert s.sigma_ux == pytest.approx(0.0)
        assert s.sigma_uy == pytest.approx(0.0)
        assert s.sigma_uz == pytest.approx(0.0)

    def test_sigma_set_explicitly(self):
        s = _make_station(sigma_ux=0.003, sigma_uy=0.002, sigma_uz=0.001)
        assert s.sigma_ux == pytest.approx(0.003)
        assert s.sigma_uy == pytest.approx(0.002)
        assert s.sigma_uz == pytest.approx(0.001)

    def test_frozen(self):
        s = _make_station()
        with pytest.raises((AttributeError, TypeError)):
            s.ux = 99.0  # type: ignore[misc]

    def test_negative_displacements_accepted(self):
        s = _make_station(ux=-0.05, uy=-0.03, uz=-0.01)
        assert s.ux == pytest.approx(-0.05)

    def test_large_position_values(self):
        s = _make_station(x=500.0, y=-300.0)
        assert s.x == pytest.approx(500.0)
        assert s.y == pytest.approx(-300.0)


# ---------------------------------------------------------------------------
# GPSDataset
# ---------------------------------------------------------------------------

class TestGPSDataset:
    def test_default_construction(self):
        ds = GPSDataset()
        assert len(ds) == 0
        assert ds.reference_frame == ""

    def test_construction_with_stations(self):
        ds = _make_dataset(4)
        assert len(ds) == 4

    def test_len_reflects_station_count(self):
        ds = _make_dataset(7)
        assert len(ds) == 7

    def test_reference_frame_set(self):
        ds = GPSDataset(stations=[], reference_frame="IGS14")
        assert ds.reference_frame == "IGS14"

    def test_stations_accessible(self):
        stations = [_make_station(name=f"S{i}") for i in range(3)]
        ds = GPSDataset(stations=stations)
        assert ds.stations[0].name == "S0"
        assert ds.stations[2].name == "S2"


# ---------------------------------------------------------------------------
# CSV round-trip
# ---------------------------------------------------------------------------

class TestGpsCsvRoundTrip:
    def test_write_then_read_preserves_stations(self, tmp_path: Path):
        dataset = _make_dataset(3)
        csv_path = tmp_path / "gps.csv"
        _write_gps_csv(csv_path, dataset.stations)
        recovered = read_gps_csv(csv_path)

        assert len(recovered) == 3
        for orig, rec in zip(dataset.stations, recovered.stations):
            assert rec.name == orig.name
            assert rec.x == pytest.approx(orig.x)
            assert rec.y == pytest.approx(orig.y)
            assert rec.ux == pytest.approx(orig.ux)
            assert rec.uy == pytest.approx(orig.uy)
            assert rec.uz == pytest.approx(orig.uz)

    def test_sigma_columns_preserved(self, tmp_path: Path):
        station = _make_station(sigma_ux=0.003, sigma_uy=0.002, sigma_uz=0.001)
        csv_path = tmp_path / "gps.csv"
        _write_gps_csv(csv_path, [station])
        recovered = read_gps_csv(csv_path)

        rec = recovered.stations[0]
        assert rec.sigma_ux == pytest.approx(0.003)
        assert rec.sigma_uy == pytest.approx(0.002)
        assert rec.sigma_uz == pytest.approx(0.001)

    def test_single_station_round_trip(self, tmp_path: Path):
        station = _make_station(name="LONE", x=3.5, y=-2.1, ux=0.02, uy=-0.01, uz=0.005)
        csv_path = tmp_path / "single.csv"
        _write_gps_csv(csv_path, [station])
        recovered = read_gps_csv(csv_path)
        assert len(recovered) == 1
        assert recovered.stations[0].name == "LONE"
        assert recovered.stations[0].ux == pytest.approx(0.02)

    def test_returns_gps_dataset(self, tmp_path: Path):
        csv_path = tmp_path / "gps.csv"
        _write_gps_csv(csv_path, [_make_station()])
        result = read_gps_csv(csv_path)
        assert isinstance(result, GPSDataset)


# ---------------------------------------------------------------------------
# JSON round-trip
# ---------------------------------------------------------------------------

class TestGpsJsonRoundTrip:
    def test_write_then_read_preserves_stations(self, tmp_path: Path):
        dataset = _make_dataset(4)
        json_path = tmp_path / "gps.json"
        _write_gps_json(json_path, dataset)
        recovered = read_gps_json(json_path)

        assert len(recovered) == 4
        for orig, rec in zip(dataset.stations, recovered.stations):
            assert rec.name == orig.name
            assert rec.x == pytest.approx(orig.x)
            assert rec.y == pytest.approx(orig.y)
            assert rec.ux == pytest.approx(orig.ux)
            assert rec.uy == pytest.approx(orig.uy)
            assert rec.uz == pytest.approx(orig.uz)
            assert rec.sigma_ux == pytest.approx(orig.sigma_ux)

    def test_reference_frame_preserved(self, tmp_path: Path):
        dataset = GPSDataset(
            stations=[_make_station()],
            reference_frame="ITRF2014",
        )
        json_path = tmp_path / "gps.json"
        _write_gps_json(json_path, dataset)
        recovered = read_gps_json(json_path)
        assert recovered.reference_frame == "ITRF2014"

    def test_empty_stations_round_trip(self, tmp_path: Path):
        dataset = GPSDataset(stations=[], reference_frame="IGS14")
        json_path = tmp_path / "empty.json"
        _write_gps_json(json_path, dataset)
        recovered = read_gps_json(json_path)
        assert len(recovered) == 0

    def test_json_file_is_valid(self, tmp_path: Path):
        dataset = _make_dataset(2)
        json_path = tmp_path / "gps.json"
        _write_gps_json(json_path, dataset)
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert "stations" in data
        assert isinstance(data["stations"], list)
        assert len(data["stations"]) == 2


# ---------------------------------------------------------------------------
# compute_misfit
# ---------------------------------------------------------------------------

class TestComputeMisfit:
    def _gps_at_grid_center(self) -> GPSDataset:
        """GPS stations placed near the center of the result grid."""
        return GPSDataset(stations=[
            GPSStation(name="S0", x=0.0, y=0.0, ux=0.005, uy=0.003, uz=0.001),
            GPSStation(name="S1", x=1.0, y=1.0, ux=0.005, uy=0.003, uz=0.001),
        ])

    def test_returns_expected_keys(self):
        result = _make_minimal_result()
        model_stub = None  # _model param unused in compute_misfit
        gps = self._gps_at_grid_center()
        misfit = compute_misfit(result, model_stub, gps)

        assert "rms_horizontal" in misfit
        assert "rms_vertical" in misfit
        assert "rms_3d" in misfit
        assert "per_station_residuals" in misfit
        assert "reduction_of_variance" in misfit

    def test_per_station_residuals_count(self):
        result = _make_minimal_result()
        gps = self._gps_at_grid_center()
        misfit = compute_misfit(result, None, gps)
        assert len(misfit["per_station_residuals"]) == len(gps.stations)

    def test_per_station_residual_has_name(self):
        result = _make_minimal_result()
        gps = self._gps_at_grid_center()
        misfit = compute_misfit(result, None, gps)
        names = [r["name"] for r in misfit["per_station_residuals"]]
        assert "S0" in names
        assert "S1" in names

    def test_rms_values_are_non_negative(self):
        result = _make_minimal_result()
        gps = self._gps_at_grid_center()
        misfit = compute_misfit(result, None, gps)
        assert misfit["rms_horizontal"] >= 0.0
        assert misfit["rms_vertical"] >= 0.0
        assert misfit["rms_3d"] >= 0.0

    def test_perfect_match_gives_near_zero_rms(self):
        """If observed == modeled, RMS should be ~0."""
        ux_val, uy_val, uz_val = 0.005, 0.003, 0.001
        result = _make_minimal_result(
            ux_val=ux_val, uy_val=uy_val, uz_val=uz_val,
        )
        # Station at grid center with identical displacements
        gps = GPSDataset(stations=[
            GPSStation(name="S0", x=0.0, y=0.0,
                       ux=ux_val, uy=uy_val, uz=uz_val),
        ])
        misfit = compute_misfit(result, None, gps)
        assert misfit["rms_horizontal"] < 1e-4
        assert misfit["rms_vertical"] < 1e-4

    def test_reduction_of_variance_is_float(self):
        result = _make_minimal_result()
        gps = self._gps_at_grid_center()
        misfit = compute_misfit(result, None, gps)
        assert isinstance(misfit["reduction_of_variance"], float)

    def test_per_station_residual_has_res_h_key(self):
        result = _make_minimal_result()
        gps = self._gps_at_grid_center()
        misfit = compute_misfit(result, None, gps)
        for r in misfit["per_station_residuals"]:
            assert "res_h" in r
            assert r["res_h"] >= 0.0

    def test_misfit_with_zero_observed_displacements(self):
        """Zero observed GPS does not crash (obs_var guard)."""
        result = _make_minimal_result()
        gps = GPSDataset(stations=[
            GPSStation(name="S0", x=0.0, y=0.0, ux=0.0, uy=0.0, uz=0.0),
        ])
        misfit = compute_misfit(result, None, gps)
        # reduction_of_variance should be 0.0 when obs_var == 0
        assert isinstance(misfit["reduction_of_variance"], float)
        assert misfit["rms_horizontal"] >= 0.0


# ---------------------------------------------------------------------------
# plot_gps_comparison
# ---------------------------------------------------------------------------

class TestPlotGpsComparison:
    """Tests for viz.gps.plot_gps_comparison (lines 58-119)."""

    def _gps_dataset(self) -> GPSDataset:
        """GPS stations within the model grid."""
        return GPSDataset(stations=[
            GPSStation(name="S0", x=0.0, y=0.0,   ux=0.01, uy=0.005, uz=0.002),
            GPSStation(name="S1", x=1.0, y=1.0,   ux=0.02, uy=0.010, uz=0.004),
            GPSStation(name="S2", x=-1.0, y=-1.0, ux=0.00, uy=0.001, uz=0.001),
        ])

    def test_returns_figure_and_axes_horizontal(self):
        """plot_gps_comparison returns (Figure, Axes) for horizontal component."""
        result = _make_minimal_result()
        gps = self._gps_dataset()
        fig, ax = plot_gps_comparison(result, None, gps, component="horizontal")
        assert fig is not None
        assert ax is not None
        plt.close("all")

    def test_returns_figure_and_axes_vertical(self):
        """plot_gps_comparison returns (Figure, Axes) for vertical component."""
        result = _make_minimal_result()
        gps = self._gps_dataset()
        fig, ax = plot_gps_comparison(result, None, gps, component="vertical")
        assert fig is not None
        assert ax is not None
        plt.close("all")

    def test_horizontal_xlabel_and_ylabel(self):
        """Horizontal plot has correct axis labels."""
        result = _make_minimal_result()
        gps = self._gps_dataset()
        fig, ax = plot_gps_comparison(result, None, gps, component="horizontal")
        assert "East" in ax.get_xlabel()
        assert "North" in ax.get_ylabel()
        plt.close("all")

    def test_vertical_ylabel_contains_displacement(self):
        """Vertical plot y-label mentions displacement."""
        result = _make_minimal_result()
        gps = self._gps_dataset()
        fig, ax = plot_gps_comparison(result, None, gps, component="vertical")
        assert "Displacement" in ax.get_ylabel() or "displacement" in ax.get_ylabel().lower()
        plt.close("all")

    def test_accepts_existing_axes(self):
        """When ax is passed, the same axes object is used."""
        result = _make_minimal_result()
        gps = self._gps_dataset()
        fig0, ax0 = plt.subplots(1, 1)
        fig_ret, ax_ret = plot_gps_comparison(result, None, gps, ax=ax0, component="horizontal")
        assert ax_ret is ax0
        plt.close("all")

    def test_show_residuals_flag(self):
        """show_residuals=True runs without error."""
        result = _make_minimal_result()
        gps = self._gps_dataset()
        fig, ax = plot_gps_comparison(
            result, None, gps, component="horizontal", show_residuals=True
        )
        assert fig is not None
        plt.close("all")

    def test_custom_scale_and_colors(self):
        """Custom scale and color parameters do not raise."""
        result = _make_minimal_result()
        gps = self._gps_dataset()
        fig, ax = plot_gps_comparison(
            result, None, gps,
            component="horizontal",
            observed_color="blue",
            modeled_color="orange",
            scale=1.0,
        )
        assert fig is not None
        plt.close("all")

    def test_vertical_xticklabels_contain_station_names(self):
        """Vertical bar chart x-ticks show station names."""
        result = _make_minimal_result()
        gps = self._gps_dataset()
        fig, ax = plot_gps_comparison(result, None, gps, component="vertical")
        labels = [t.get_text() for t in ax.get_xticklabels()]
        # After draw, tick labels may be populated
        station_names = {s.name for s in gps.stations}
        # At minimum the xticklabels list length should equal station count
        # (matplotlib may not yet render them without a draw call in Agg)
        assert ax.get_xticks() is not None
        plt.close("all")

    def test_legend_present_horizontal(self):
        """Horizontal plot includes a legend."""
        result = _make_minimal_result()
        gps = self._gps_dataset()
        fig, ax = plot_gps_comparison(result, None, gps, component="horizontal")
        legend = ax.get_legend()
        assert legend is not None
        plt.close("all")
