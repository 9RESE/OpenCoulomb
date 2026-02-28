"""Tests for opencoulomb.types.catalog, opencoulomb.io.catalog_io, and
opencoulomb.io.isc_client.

Covers CatalogEvent, EarthquakeCatalog, CSV/JSON round-trips, catalog_from_obspy,
query_isc, and query_usgs_catalog (with mocked ObsPy).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from opencoulomb.io.catalog_io import (
    read_catalog_csv,
    read_catalog_json,
    write_catalog_csv,
    write_catalog_json,
)
from opencoulomb.io.isc_client import catalog_from_obspy, query_isc, query_usgs_catalog
from opencoulomb.types.catalog import CatalogEvent, EarthquakeCatalog


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_event(
    lat: float = 35.77,
    lon: float = -117.60,
    depth: float = 8.0,
    mag: float = 7.1,
    time: str = "2019-07-06T03:19:53Z",
    event_id: str = "us7000abcd",
    mag_type: str = "Mw",
) -> CatalogEvent:
    return CatalogEvent(
        latitude=lat,
        longitude=lon,
        depth_km=depth,
        magnitude=mag,
        time=time,
        event_id=event_id,
        magnitude_type=mag_type,
    )


def _make_catalog(n: int = 3) -> EarthquakeCatalog:
    events = [
        _make_event(
            lat=30.0 + i,
            lon=-100.0 + i,
            depth=5.0 * (i + 1),
            mag=5.0 + i * 0.5,
            event_id=f"ev{i:04d}",
        )
        for i in range(n)
    ]
    return EarthquakeCatalog(events=events, source="test")


# ---------------------------------------------------------------------------
# CatalogEvent
# ---------------------------------------------------------------------------

class TestCatalogEvent:
    def test_construction_required_fields(self):
        ev = CatalogEvent(
            latitude=35.77,
            longitude=-117.60,
            depth_km=8.0,
            magnitude=7.1,
            time="2019-07-06T03:19:53Z",
        )
        assert ev.latitude == pytest.approx(35.77)
        assert ev.longitude == pytest.approx(-117.60)
        assert ev.depth_km == pytest.approx(8.0)
        assert ev.magnitude == pytest.approx(7.1)
        assert ev.time == "2019-07-06T03:19:53Z"

    def test_defaults_for_optional_fields(self):
        ev = CatalogEvent(
            latitude=0.0, longitude=0.0, depth_km=10.0,
            magnitude=5.0, time="",
        )
        assert ev.event_id == ""
        assert ev.magnitude_type == ""

    def test_optional_fields_set(self):
        ev = _make_event(event_id="us123", mag_type="Mw")
        assert ev.event_id == "us123"
        assert ev.magnitude_type == "Mw"

    def test_frozen(self):
        ev = _make_event()
        with pytest.raises((AttributeError, TypeError)):
            ev.magnitude = 9.9  # type: ignore[misc]

    def test_negative_longitude_accepted(self):
        ev = _make_event(lon=-180.0)
        assert ev.longitude == pytest.approx(-180.0)

    def test_deep_event(self):
        ev = _make_event(depth=700.0)
        assert ev.depth_km == pytest.approx(700.0)


# ---------------------------------------------------------------------------
# EarthquakeCatalog construction and __len__
# ---------------------------------------------------------------------------

class TestEarthquakeCatalog:
    def test_default_construction(self):
        cat = EarthquakeCatalog()
        assert len(cat) == 0
        assert cat.source == ""

    def test_construction_with_events(self):
        events = [_make_event() for _ in range(3)]
        cat = EarthquakeCatalog(events=events, source="USGS")
        assert len(cat) == 3
        assert cat.source == "USGS"

    def test_len_reflects_event_count(self):
        cat = _make_catalog(7)
        assert len(cat) == 7

    def test_empty_catalog_len_zero(self):
        cat = EarthquakeCatalog(events=[])
        assert len(cat) == 0


# ---------------------------------------------------------------------------
# filter_by_magnitude
# ---------------------------------------------------------------------------

class TestFilterByMagnitude:
    def test_keeps_events_in_range(self):
        cat = _make_catalog(5)  # mags: 5.0, 5.5, 6.0, 6.5, 7.0
        filtered = cat.filter_by_magnitude(min_mag=5.5, max_mag=6.5)
        assert all(5.5 <= e.magnitude <= 6.5 for e in filtered.events)

    def test_excludes_events_outside_range(self):
        cat = _make_catalog(5)
        filtered = cat.filter_by_magnitude(min_mag=5.5, max_mag=6.5)
        assert len(filtered) == 3

    def test_source_preserved(self):
        cat = _make_catalog(3)
        filtered = cat.filter_by_magnitude(min_mag=5.0)
        assert filtered.source == cat.source

    def test_no_events_pass_tight_filter(self):
        cat = _make_catalog(3)
        filtered = cat.filter_by_magnitude(min_mag=9.0)
        assert len(filtered) == 0

    def test_returns_new_catalog(self):
        cat = _make_catalog(3)
        filtered = cat.filter_by_magnitude()
        assert filtered is not cat


# ---------------------------------------------------------------------------
# filter_by_depth
# ---------------------------------------------------------------------------

class TestFilterByDepth:
    def test_keeps_events_in_depth_range(self):
        cat = _make_catalog(5)  # depths: 5, 10, 15, 20, 25
        filtered = cat.filter_by_depth(min_depth=8.0, max_depth=18.0)
        assert all(8.0 <= e.depth_km <= 18.0 for e in filtered.events)

    def test_excludes_shallow_events(self):
        cat = _make_catalog(5)
        filtered = cat.filter_by_depth(min_depth=12.0)
        assert all(e.depth_km >= 12.0 for e in filtered.events)

    def test_empty_when_no_match(self):
        cat = _make_catalog(3)
        filtered = cat.filter_by_depth(min_depth=500.0)
        assert len(filtered) == 0


# ---------------------------------------------------------------------------
# filter_by_region
# ---------------------------------------------------------------------------

class TestFilterByRegion:
    def test_keeps_events_in_bounding_box(self):
        # Events: lat=30,31,32; lon=-100,-99,-98
        cat = _make_catalog(3)
        filtered = cat.filter_by_region(
            min_lat=30.5, max_lat=31.5,
            min_lon=-99.5, max_lon=-98.5,
        )
        # Only lat=31, lon=-99 should survive
        assert len(filtered) == 1
        assert filtered.events[0].latitude == pytest.approx(31.0)

    def test_all_events_pass_wide_box(self):
        cat = _make_catalog(5)
        filtered = cat.filter_by_region(
            min_lat=-90.0, max_lat=90.0,
            min_lon=-180.0, max_lon=180.0,
        )
        assert len(filtered) == len(cat)

    def test_no_events_pass_empty_box(self):
        cat = _make_catalog(3)
        filtered = cat.filter_by_region(
            min_lat=80.0, max_lat=89.0,
            min_lon=170.0, max_lon=179.0,
        )
        assert len(filtered) == 0

    def test_source_preserved(self):
        cat = _make_catalog(2)
        filtered = cat.filter_by_region()
        assert filtered.source == cat.source


# ---------------------------------------------------------------------------
# to_arrays
# ---------------------------------------------------------------------------

class TestToArrays:
    def test_returns_dict_with_required_keys(self):
        cat = _make_catalog(3)
        arrays = cat.to_arrays()
        assert set(arrays.keys()) >= {"latitude", "longitude", "depth_km", "magnitude"}

    def test_correct_values(self):
        events = [
            CatalogEvent(latitude=10.0, longitude=20.0, depth_km=5.0, magnitude=6.0, time=""),
            CatalogEvent(latitude=11.0, longitude=21.0, depth_km=10.0, magnitude=7.0, time=""),
        ]
        cat = EarthquakeCatalog(events=events)
        arrays = cat.to_arrays()
        np.testing.assert_array_almost_equal(arrays["latitude"], [10.0, 11.0])
        np.testing.assert_array_almost_equal(arrays["longitude"], [20.0, 21.0])
        np.testing.assert_array_almost_equal(arrays["depth_km"], [5.0, 10.0])
        np.testing.assert_array_almost_equal(arrays["magnitude"], [6.0, 7.0])

    def test_arrays_are_float64(self):
        cat = _make_catalog(2)
        arrays = cat.to_arrays()
        for arr in arrays.values():
            assert arr.dtype == np.float64

    def test_correct_length(self):
        cat = _make_catalog(5)
        arrays = cat.to_arrays()
        for arr in arrays.values():
            assert len(arr) == 5

    def test_empty_catalog_returns_empty_arrays(self):
        cat = EarthquakeCatalog(events=[])
        arrays = cat.to_arrays()
        for arr in arrays.values():
            assert len(arr) == 0
            assert arr.dtype == np.float64


# ---------------------------------------------------------------------------
# CSV round-trip
# ---------------------------------------------------------------------------

class TestCsvRoundTrip:
    def test_write_then_read_preserves_data(self, tmp_path: Path):
        cat = _make_catalog(3)
        csv_path = tmp_path / "catalog.csv"
        write_catalog_csv(cat, csv_path)
        recovered = read_catalog_csv(csv_path)

        assert len(recovered) == len(cat)
        for orig, rec in zip(cat.events, recovered.events):
            assert rec.latitude == pytest.approx(orig.latitude)
            assert rec.longitude == pytest.approx(orig.longitude)
            assert rec.depth_km == pytest.approx(orig.depth_km)
            assert rec.magnitude == pytest.approx(orig.magnitude)
            assert rec.time == orig.time
            assert rec.event_id == orig.event_id
            assert rec.magnitude_type == orig.magnitude_type

    def test_csv_has_correct_header(self, tmp_path: Path):
        cat = _make_catalog(1)
        csv_path = tmp_path / "catalog.csv"
        write_catalog_csv(cat, csv_path)
        first_line = csv_path.read_text(encoding="utf-8").splitlines()[0]
        assert "latitude" in first_line
        assert "longitude" in first_line
        assert "magnitude" in first_line

    def test_empty_catalog_round_trip(self, tmp_path: Path):
        cat = EarthquakeCatalog(events=[], source="empty")
        csv_path = tmp_path / "empty.csv"
        write_catalog_csv(cat, csv_path)
        recovered = read_catalog_csv(csv_path)
        assert len(recovered) == 0

    def test_source_in_recovered_catalog(self, tmp_path: Path):
        cat = _make_catalog(2)
        csv_path = tmp_path / "catalog.csv"
        write_catalog_csv(cat, csv_path)
        recovered = read_catalog_csv(csv_path)
        # source is derived from filename on read
        assert "catalog.csv" in recovered.source


# ---------------------------------------------------------------------------
# JSON round-trip
# ---------------------------------------------------------------------------

class TestJsonRoundTrip:
    def test_write_then_read_preserves_data(self, tmp_path: Path):
        cat = _make_catalog(4)
        json_path = tmp_path / "catalog.json"
        write_catalog_json(cat, json_path)
        recovered = read_catalog_json(json_path)

        assert len(recovered) == len(cat)
        for orig, rec in zip(cat.events, recovered.events):
            assert rec.latitude == pytest.approx(orig.latitude)
            assert rec.longitude == pytest.approx(orig.longitude)
            assert rec.depth_km == pytest.approx(orig.depth_km)
            assert rec.magnitude == pytest.approx(orig.magnitude)
            assert rec.time == orig.time
            assert rec.event_id == orig.event_id
            assert rec.magnitude_type == orig.magnitude_type

    def test_source_preserved_in_json(self, tmp_path: Path):
        cat = EarthquakeCatalog(events=[], source="MySource")
        json_path = tmp_path / "catalog.json"
        write_catalog_json(cat, json_path)
        recovered = read_catalog_json(json_path)
        assert recovered.source == "MySource"

    def test_empty_catalog_json_round_trip(self, tmp_path: Path):
        cat = EarthquakeCatalog(events=[], source="empty")
        json_path = tmp_path / "empty.json"
        write_catalog_json(cat, json_path)
        recovered = read_catalog_json(json_path)
        assert len(recovered) == 0

    def test_json_file_is_valid_json(self, tmp_path: Path):
        import json as _json
        cat = _make_catalog(2)
        json_path = tmp_path / "catalog.json"
        write_catalog_json(cat, json_path)
        data = _json.loads(json_path.read_text(encoding="utf-8"))
        assert "events" in data
        assert isinstance(data["events"], list)


# ---------------------------------------------------------------------------
# Helpers for ObsPy mocking
# ---------------------------------------------------------------------------

def _make_obspy_origin(lat: float, lon: float, depth_m: float, time_str: str) -> MagicMock:
    """Build a mock ObsPy Origin."""
    origin = MagicMock()
    origin.latitude = lat
    origin.longitude = lon
    origin.depth = depth_m          # ObsPy stores depth in metres
    origin.time = time_str
    return origin


def _make_obspy_magnitude(mag: float, mag_type: str) -> MagicMock:
    """Build a mock ObsPy Magnitude."""
    m = MagicMock()
    m.mag = mag
    m.magnitude_type = mag_type
    return m


def _make_obspy_event(
    lat: float = 35.0,
    lon: float = -120.0,
    depth_m: float = 10_000.0,
    mag: float = 5.0,
    mag_type: str = "Mw",
    time_str: str = "2024-01-01T00:00:00",
    event_id: str = "quakeml:isc.ac.uk/event/123",
) -> MagicMock:
    """Build a minimal mock ObsPy Event."""
    event = MagicMock()
    origin = _make_obspy_origin(lat, lon, depth_m, time_str)
    magnitude = _make_obspy_magnitude(mag, mag_type)

    event.preferred_origin.return_value = origin
    event.preferred_magnitude.return_value = magnitude
    event.origins = [origin]
    event.magnitudes = [magnitude]

    resource_id = MagicMock()
    resource_id.__str__ = lambda self: event_id  # type: ignore[method-assign]
    event.resource_id = resource_id

    return event


def _make_obspy_catalog(events: list[MagicMock]) -> MagicMock:
    """Build a mock ObsPy Catalog that iterates over events."""
    cat = MagicMock()
    cat.__iter__ = MagicMock(return_value=iter(events))
    return cat


# ---------------------------------------------------------------------------
# catalog_from_obspy
# ---------------------------------------------------------------------------

class TestCatalogFromObspy:
    """Tests for isc_client.catalog_from_obspy."""

    def test_converts_single_event(self):
        events = [_make_obspy_event(lat=35.0, lon=-120.0, depth_m=10_000.0,
                                    mag=5.5, mag_type="Mw")]
        cat = catalog_from_obspy(_make_obspy_catalog(events), source="ISC")
        assert len(cat) == 1
        ev = cat.events[0]
        assert ev.latitude == pytest.approx(35.0)
        assert ev.longitude == pytest.approx(-120.0)
        assert ev.depth_km == pytest.approx(10.0)   # metres → km
        assert ev.magnitude == pytest.approx(5.5)
        assert ev.magnitude_type == "Mw"
        assert cat.source == "ISC"

    def test_converts_multiple_events(self):
        events = [_make_obspy_event(lat=30.0 + i, lon=-100.0 + i, mag=5.0 + i)
                  for i in range(4)]
        cat = catalog_from_obspy(_make_obspy_catalog(events), source="USGS")
        assert len(cat) == 4
        assert cat.source == "USGS"

    def test_skips_event_with_no_origin(self):
        """Events without an origin should be silently skipped."""
        no_origin = MagicMock()
        no_origin.preferred_origin.return_value = None
        no_origin.origins = []

        good = _make_obspy_event()
        cat = catalog_from_obspy(_make_obspy_catalog([no_origin, good]))
        assert len(cat) == 1

    def test_event_with_no_preferred_origin_uses_first_origin(self):
        """Falls back to origins[0] when preferred_origin returns None."""
        event = _make_obspy_event(lat=10.0, lon=20.0, depth_m=5_000.0, mag=4.0)
        event.preferred_origin.return_value = None  # force fallback

        cat = catalog_from_obspy(_make_obspy_catalog([event]))
        assert len(cat) == 1
        assert cat.events[0].latitude == pytest.approx(10.0)

    def test_event_with_no_magnitude_gives_zero(self):
        """Missing magnitude results in magnitude=0.0, mag_type=''."""
        event = _make_obspy_event()
        event.preferred_magnitude.return_value = None
        event.magnitudes = []

        cat = catalog_from_obspy(_make_obspy_catalog([event]))
        ev = cat.events[0]
        assert ev.magnitude == pytest.approx(0.0)
        assert ev.magnitude_type == ""

    def test_depth_none_becomes_zero(self):
        """origin.depth=None becomes depth_km=0.0."""
        event = _make_obspy_event()
        event.preferred_origin.return_value.depth = None

        cat = catalog_from_obspy(_make_obspy_catalog([event]))
        assert cat.events[0].depth_km == pytest.approx(0.0)

    def test_latitude_none_becomes_zero(self):
        """origin.latitude=None becomes latitude=0.0."""
        event = _make_obspy_event()
        event.preferred_origin.return_value.latitude = None

        cat = catalog_from_obspy(_make_obspy_catalog([event]))
        assert cat.events[0].latitude == pytest.approx(0.0)

    def test_longitude_none_becomes_zero(self):
        """origin.longitude=None becomes longitude=0.0."""
        event = _make_obspy_event()
        event.preferred_origin.return_value.longitude = None

        cat = catalog_from_obspy(_make_obspy_catalog([event]))
        assert cat.events[0].longitude == pytest.approx(0.0)

    def test_time_none_becomes_empty_string(self):
        """origin.time=None becomes time=''."""
        event = _make_obspy_event()
        event.preferred_origin.return_value.time = None

        cat = catalog_from_obspy(_make_obspy_catalog([event]))
        assert cat.events[0].time == ""

    def test_event_id_extracted_from_resource_id(self):
        """event_id is the last path segment of resource_id."""
        event = _make_obspy_event(event_id="quakeml:isc.ac.uk/event/456789")
        cat = catalog_from_obspy(_make_obspy_catalog([event]))
        assert cat.events[0].event_id == "456789"

    def test_empty_catalog_produces_empty_result(self):
        cat = catalog_from_obspy(_make_obspy_catalog([]), source="test")
        assert len(cat) == 0
        assert cat.source == "test"

    def test_default_source_is_empty_string(self):
        cat = catalog_from_obspy(_make_obspy_catalog([]))
        assert cat.source == ""

    def test_returns_earthquake_catalog(self):
        cat = catalog_from_obspy(_make_obspy_catalog([_make_obspy_event()]))
        assert isinstance(cat, EarthquakeCatalog)


# ---------------------------------------------------------------------------
# _get_obspy_client — ImportError path
# ---------------------------------------------------------------------------

class TestGetObspyClientImportError:
    def test_raises_import_error_when_obspy_missing(self):
        """_get_obspy_client raises ImportError with helpful message when obspy absent."""
        import opencoulomb.io.isc_client as isc_mod

        with patch.dict("sys.modules", {"obspy.clients.fdsn": None, "obspy": None}):
            with pytest.raises(ImportError, match="ObsPy is required"):
                isc_mod._get_obspy_client("ISC")


# ---------------------------------------------------------------------------
# query_isc (mocked)
# ---------------------------------------------------------------------------

class TestQueryIsc:
    def test_query_isc_returns_catalog(self):
        events = [_make_obspy_event(lat=35.0, lon=-120.0, mag=6.0)]
        with patch("opencoulomb.io.isc_client._get_obspy_client") as mock_get_client:
            mock_client_inst = MagicMock()
            mock_client_inst.get_events.return_value = _make_obspy_catalog(events)
            mock_get_client.return_value = mock_client_inst

            mock_obspy = MagicMock()
            mock_obspy.UTCDateTime = MagicMock(side_effect=lambda s: s)
            with patch.dict("sys.modules", {"obspy": mock_obspy}):
                result = query_isc(
                    start_time="2024-01-01",
                    end_time="2024-02-01",
                    min_magnitude=4.0,
                )
        assert isinstance(result, EarthquakeCatalog)
        assert len(result) == 1
        assert result.source == "ISC"

    def test_query_isc_passes_optional_geographic_params(self):
        """Optional lat/lon/depth params are forwarded to get_events."""
        events = [_make_obspy_event()]
        with patch("opencoulomb.io.isc_client._get_obspy_client") as mock_get_client:
            mock_client_inst = MagicMock()
            mock_client_inst.get_events.return_value = _make_obspy_catalog(events)
            mock_get_client.return_value = mock_client_inst

            mock_obspy = MagicMock()
            mock_obspy.UTCDateTime = MagicMock(side_effect=lambda s: s)
            with patch.dict("sys.modules", {"obspy": mock_obspy}):
                result = query_isc(
                    start_time="2024-01-01",
                    end_time="2024-02-01",
                    min_magnitude=3.0,
                    min_latitude=30.0,
                    max_latitude=40.0,
                    min_longitude=-120.0,
                    max_longitude=-110.0,
                    max_depth=50.0,
                )
            # Verify get_events was called with the geographic kwargs
            call_kwargs = mock_client_inst.get_events.call_args[1]
            assert "minlatitude" in call_kwargs
            assert "maxlatitude" in call_kwargs
            assert "minlongitude" in call_kwargs
            assert "maxlongitude" in call_kwargs
            assert "maxdepth" in call_kwargs
            assert isinstance(result, EarthquakeCatalog)

    def test_query_isc_no_optional_params_not_forwarded(self):
        """None optional params are NOT added to get_events kwargs."""
        events = [_make_obspy_event()]
        with patch("opencoulomb.io.isc_client._get_obspy_client") as mock_get_client:
            mock_client_inst = MagicMock()
            mock_client_inst.get_events.return_value = _make_obspy_catalog(events)
            mock_get_client.return_value = mock_client_inst

            mock_obspy = MagicMock()
            mock_obspy.UTCDateTime = MagicMock(side_effect=lambda s: s)
            with patch.dict("sys.modules", {"obspy": mock_obspy}):
                query_isc("2024-01-01", "2024-02-01")

            call_kwargs = mock_client_inst.get_events.call_args[1]
            assert "minlatitude" not in call_kwargs
            assert "maxlatitude" not in call_kwargs
            assert "maxdepth" not in call_kwargs


# ---------------------------------------------------------------------------
# query_usgs_catalog (mocked)
# ---------------------------------------------------------------------------

class TestQueryUsgsCatalog:
    def test_query_usgs_returns_catalog(self):
        events = [_make_obspy_event(lat=37.0, lon=-122.0, mag=5.5)]
        with patch("opencoulomb.io.isc_client._get_obspy_client") as mock_get_client:
            mock_client_inst = MagicMock()
            mock_client_inst.get_events.return_value = _make_obspy_catalog(events)
            mock_get_client.return_value = mock_client_inst

            mock_obspy = MagicMock()
            mock_obspy.UTCDateTime = MagicMock(side_effect=lambda s: s)
            with patch.dict("sys.modules", {"obspy": mock_obspy}):
                result = query_usgs_catalog("2024-01-01", "2024-06-01")

        assert isinstance(result, EarthquakeCatalog)
        assert result.source == "USGS"
        assert len(result) == 1

    def test_query_usgs_uses_usgs_source(self):
        """_get_obspy_client is called with 'USGS'."""
        events = [_make_obspy_event()]
        with patch("opencoulomb.io.isc_client._get_obspy_client") as mock_get_client:
            mock_client_inst = MagicMock()
            mock_client_inst.get_events.return_value = _make_obspy_catalog(events)
            mock_get_client.return_value = mock_client_inst

            mock_obspy = MagicMock()
            mock_obspy.UTCDateTime = MagicMock(side_effect=lambda s: s)
            with patch.dict("sys.modules", {"obspy": mock_obspy}):
                query_usgs_catalog("2024-01-01", "2024-06-01")

            mock_get_client.assert_called_once_with("USGS")

    def test_query_usgs_geographic_params_forwarded(self):
        """Optional geographic params are forwarded for USGS."""
        events = [_make_obspy_event()]
        with patch("opencoulomb.io.isc_client._get_obspy_client") as mock_get_client:
            mock_client_inst = MagicMock()
            mock_client_inst.get_events.return_value = _make_obspy_catalog(events)
            mock_get_client.return_value = mock_client_inst

            mock_obspy = MagicMock()
            mock_obspy.UTCDateTime = MagicMock(side_effect=lambda s: s)
            with patch.dict("sys.modules", {"obspy": mock_obspy}):
                query_usgs_catalog(
                    "2024-01-01", "2024-02-01",
                    min_latitude=35.0, max_latitude=40.0,
                    min_longitude=-125.0, max_longitude=-115.0,
                )

            call_kwargs = mock_client_inst.get_events.call_args[1]
            assert "minlatitude" in call_kwargs
            assert "maxlatitude" in call_kwargs

    def test_query_usgs_no_optional_params(self):
        """None geographic params are not forwarded for USGS."""
        events = []
        with patch("opencoulomb.io.isc_client._get_obspy_client") as mock_get_client:
            mock_client_inst = MagicMock()
            mock_client_inst.get_events.return_value = _make_obspy_catalog(events)
            mock_get_client.return_value = mock_client_inst

            mock_obspy = MagicMock()
            mock_obspy.UTCDateTime = MagicMock(side_effect=lambda s: s)
            with patch.dict("sys.modules", {"obspy": mock_obspy}):
                result = query_usgs_catalog("2024-01-01", "2024-06-01")

            call_kwargs = mock_client_inst.get_events.call_args[1]
            assert "minlatitude" not in call_kwargs
            assert len(result) == 0
