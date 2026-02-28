"""Tests for opencoulomb.io.fsp_parser.

Covers parse_fsp (FSP format string) and parse_geojson_faults (GeoJSON dict).
All tests use in-memory data — no network or file I/O.
"""

from __future__ import annotations

import math

import pytest

from opencoulomb.io.fsp_parser import parse_fsp, parse_geojson_faults
from opencoulomb.types.fault import FaultElement, Kode


# ---------------------------------------------------------------------------
# Helpers: minimal but valid FSP strings
# ---------------------------------------------------------------------------

_FSP_HEADER = """\
% FINITE SOURCE RUPTURE MODEL
% EVENT: 2019 Ridgecrest M7.1
%
% STRIKE = 228.0  DIP = 85.0
%
% DEPTH (km): 8.0
%
% Lat   Lon    x(km) y(km) z(km) slip(m) rake  DipLen
"""

_FSP_ONE_ROW = _FSP_HEADER + (
    "35.77  -117.60   0.50   1.00   8.00   2.50  170.0   1.0\n"
)

_FSP_THREE_ROWS = _FSP_HEADER + (
    "35.77  -117.60   0.50   1.00   8.00   2.50  170.0   1.0\n"
    "35.78  -117.62   1.50   2.00   9.00   1.80   90.0   1.5\n"
    "35.79  -117.64   2.50   3.00  10.00   3.10  120.0   2.0\n"
)


# ---------------------------------------------------------------------------
# parse_fsp — basic parsing
# ---------------------------------------------------------------------------

class TestParseFspBasic:
    def test_single_row_returns_one_element(self):
        elements = parse_fsp(_FSP_ONE_ROW)
        assert len(elements) == 1

    def test_three_rows_returns_three_elements(self):
        elements = parse_fsp(_FSP_THREE_ROWS)
        assert len(elements) == 3

    def test_empty_string_returns_empty_list(self):
        assert parse_fsp("") == []

    def test_header_only_returns_empty_list(self):
        # No data rows — only comment lines starting with %
        content = "% STRIKE = 45.0  DIP = 60.0\n% another comment\n"
        assert parse_fsp(content) == []

    def test_returns_fault_elements(self):
        elements = parse_fsp(_FSP_ONE_ROW)
        assert all(isinstance(e, FaultElement) for e in elements)

    def test_kode_is_standard(self):
        elements = parse_fsp(_FSP_ONE_ROW)
        assert all(e.kode == Kode.STANDARD for e in elements)


# ---------------------------------------------------------------------------
# parse_fsp — geometry validation
# ---------------------------------------------------------------------------

class TestParseFspGeometry:
    def test_depth_range_valid(self):
        elements = parse_fsp(_FSP_ONE_ROW)
        for e in elements:
            assert e.top_depth >= 0.0
            assert e.bottom_depth > e.top_depth

    def test_dip_extracted_from_header(self):
        elements = parse_fsp(_FSP_ONE_ROW)
        # Header declares DIP = 85.0
        for e in elements:
            assert e.dip == pytest.approx(85.0)

    def test_strike_used_for_endpoint_offset(self):
        """Endpoints should differ from center by strike-directed offset."""
        elements = parse_fsp(_FSP_ONE_ROW)
        e = elements[0]
        # Center is midpoint of start/fin
        cx = (e.x_start + e.x_fin) / 2.0
        cy = (e.y_start + e.y_fin) / 2.0
        # x_km = 0.50, y_km = 1.00 from the row
        assert cx == pytest.approx(0.50, abs=0.01)
        assert cy == pytest.approx(1.00, abs=0.01)

    def test_label_has_fsp_prefix(self):
        elements = parse_fsp(_FSP_ONE_ROW)
        assert elements[0].label.startswith("fsp_")

    def test_element_index_sequential(self):
        elements = parse_fsp(_FSP_THREE_ROWS)
        for i, e in enumerate(elements, start=1):
            assert e.element_index == i

    def test_slip_components_from_rake(self):
        """slip_1 = -slip*cos(rake), slip_2 = slip*sin(rake)."""
        elements = parse_fsp(_FSP_ONE_ROW)
        e = elements[0]
        rake_rad = math.radians(170.0)
        slip_m = 2.50
        expected_s1 = -slip_m * math.cos(rake_rad)
        expected_s2 = slip_m * math.sin(rake_rad)
        assert e.slip_1 == pytest.approx(expected_s1, abs=1e-6)
        assert e.slip_2 == pytest.approx(expected_s2, abs=1e-6)


# ---------------------------------------------------------------------------
# parse_fsp — robustness
# ---------------------------------------------------------------------------

class TestParseFspRobustness:
    def test_malformed_rows_are_skipped(self):
        """Lines with too few columns are skipped without crashing."""
        content = _FSP_HEADER + "bad line\n" + "35.77  -117.60   0.50   1.00   8.00   2.50  170.0   1.0\n"
        elements = parse_fsp(content)
        assert len(elements) == 1

    def test_non_numeric_values_skip_row(self):
        content = _FSP_HEADER + "35.77  -117.60   abc   1.00   8.00   2.50  170.0   1.0\n"
        elements = parse_fsp(content)
        # z_km = 8.00 is at column index 4 (0-based), x_km at index 2 → 'abc' → skip
        assert len(elements) == 0

    def test_no_crash_on_random_text(self):
        content = "This is not an FSP file at all.\nJust random text.\n"
        result = parse_fsp(content)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# parse_geojson_faults — basic
# ---------------------------------------------------------------------------

class TestParseGeojsonFaults:
    def _point_feature(
        self,
        lon: float = 0.0,
        lat: float = 0.0,
        slip: float = 1.0,
        rake: float = 90.0,
        strike: float = 0.0,
        dip: float = 45.0,
        depth: float = 10.0,
    ) -> dict:
        return {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "slip": slip,
                "rake": rake,
                "strike": strike,
                "dip": dip,
                "depth": depth,
            },
        }

    def _linestring_feature(self) -> dict:
        return {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[-1.0, 0.0], [1.0, 0.0]],
            },
            "properties": {
                "slip": 2.0, "rake": 45.0, "strike": 90.0,
                "dip": 60.0, "depth": 5.0,
            },
        }

    def test_empty_geojson_returns_empty_list(self):
        assert parse_geojson_faults({}) == []
        assert parse_geojson_faults({"features": []}) == []

    def test_single_point_feature(self):
        geojson = {"features": [self._point_feature()]}
        elements = parse_geojson_faults(geojson)
        assert len(elements) == 1
        assert isinstance(elements[0], FaultElement)

    def test_multiple_features(self):
        geojson = {"features": [
            self._point_feature(lon=0.0, lat=0.0),
            self._point_feature(lon=1.0, lat=1.0),
            self._linestring_feature(),
        ]}
        elements = parse_geojson_faults(geojson)
        assert len(elements) == 3

    def test_kode_is_standard(self):
        geojson = {"features": [self._point_feature()]}
        elements = parse_geojson_faults(geojson)
        assert elements[0].kode == Kode.STANDARD

    def test_depth_range_valid(self):
        geojson = {"features": [self._point_feature(depth=10.0, dip=45.0)]}
        elements = parse_geojson_faults(geojson)
        e = elements[0]
        assert e.top_depth >= 0.0
        assert e.bottom_depth > e.top_depth

    def test_dip_preserved(self):
        geojson = {"features": [self._point_feature(dip=30.0)]}
        elements = parse_geojson_faults(geojson)
        assert elements[0].dip == pytest.approx(30.0)

    def test_label_has_geojson_prefix(self):
        geojson = {"features": [self._point_feature()]}
        elements = parse_geojson_faults(geojson)
        assert elements[0].label.startswith("geojson_")

    def test_element_index_sequential(self):
        geojson = {"features": [
            self._point_feature(), self._point_feature(),
        ]}
        elements = parse_geojson_faults(geojson)
        assert elements[0].element_index == 1
        assert elements[1].element_index == 2

    def test_unknown_geometry_type_skipped(self):
        feature = {
            "type": "Feature",
            "geometry": {"type": "MultiPolygon", "coordinates": []},
            "properties": {"slip": 1.0, "rake": 0.0, "strike": 0.0, "dip": 45.0, "depth": 5.0},
        }
        geojson = {"features": [feature]}
        result = parse_geojson_faults(geojson)
        assert result == []

    def test_slip_components_from_rake_and_strike(self):
        rake = 90.0
        slip = 1.0
        geojson = {"features": [self._point_feature(slip=slip, rake=rake, strike=0.0, dip=45.0)]}
        elements = parse_geojson_faults(geojson)
        e = elements[0]
        rake_rad = math.radians(rake)
        expected_s1 = -slip * math.cos(rake_rad)
        expected_s2 = slip * math.sin(rake_rad)
        assert e.slip_1 == pytest.approx(expected_s1, abs=1e-9)
        assert e.slip_2 == pytest.approx(expected_s2, abs=1e-9)
