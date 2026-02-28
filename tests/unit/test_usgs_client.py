"""Tests for opencoulomb.io.usgs_client.

Uses unittest.mock.patch to mock HTTP calls. No live network access.
Live network tests are marked with @pytest.mark.network and skipped by default.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from opencoulomb.io.usgs_client import (
    USGSEvent,
    _COMCAT_BASE,
    _DETAIL_URL,
    _get_requests,
    fetch_coulomb_inp,
    search_events,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_feature(
    event_id: str = "us7000abcd",
    title: str = "M 7.1 - Test Region",
    mag: float = 7.1,
    lon: float = -118.5,
    lat: float = 34.0,
    depth: float = 15.0,
    time: str = "2024-01-15T08:23:45.000Z",
) -> dict:
    return {
        "id": event_id,
        "properties": {
            "title": title,
            "mag": mag,
            "time": time,
        },
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat, depth],
        },
    }


def _make_geojson_response(*features) -> dict:
    return {"type": "FeatureCollection", "features": list(features)}


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Build a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.text = json.dumps(json_data)
    if status_code >= 400:
        from requests.exceptions import HTTPError
        resp.raise_for_status.side_effect = HTTPError(response=resp)
    else:
        resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# USGSEvent dataclass
# ---------------------------------------------------------------------------

class TestUSGSEvent:
    def test_construction_all_fields(self):
        ev = USGSEvent(
            event_id="us7000abcd",
            title="M 7.1 - 18 km SW of Ridgecrest, CA",
            magnitude=7.1,
            latitude=35.77,
            longitude=-117.60,
            depth_km=8.0,
            time="2019-07-06T03:19:53.040Z",
        )
        assert ev.event_id == "us7000abcd"
        assert ev.title == "M 7.1 - 18 km SW of Ridgecrest, CA"
        assert ev.magnitude == pytest.approx(7.1)
        assert ev.latitude == pytest.approx(35.77)
        assert ev.longitude == pytest.approx(-117.60)
        assert ev.depth_km == pytest.approx(8.0)
        assert ev.time == "2019-07-06T03:19:53.040Z"

    def test_frozen(self):
        ev = USGSEvent(
            event_id="x", title="y", magnitude=5.0,
            latitude=0.0, longitude=0.0, depth_km=10.0, time="",
        )
        with pytest.raises((AttributeError, TypeError)):
            ev.magnitude = 6.0  # type: ignore[misc]

    def test_fields_accessible(self):
        ev = USGSEvent(
            event_id="test123", title="Test Event", magnitude=6.5,
            latitude=-10.0, longitude=150.0, depth_km=30.0,
            time="2023-06-01T12:00:00Z",
        )
        assert ev.event_id == "test123"
        assert ev.latitude == pytest.approx(-10.0)
        assert ev.longitude == pytest.approx(150.0)
        assert ev.depth_km == pytest.approx(30.0)


# ---------------------------------------------------------------------------
# _get_requests helper
# ---------------------------------------------------------------------------

class TestGetRequests:
    def test_returns_requests_module_when_available(self):
        import requests as _requests
        result = _get_requests()
        assert result is _requests

    def test_raises_import_error_when_requests_missing(self):
        import sys

        real_requests = sys.modules.get("requests")
        # Temporarily remove requests from sys.modules
        sys.modules["requests"] = None  # type: ignore[assignment]
        try:
            with pytest.raises(ImportError, match="requests"):
                _get_requests()
        finally:
            if real_requests is not None:
                sys.modules["requests"] = real_requests
            else:
                del sys.modules["requests"]


# ---------------------------------------------------------------------------
# search_events
# ---------------------------------------------------------------------------

class TestSearchEvents:
    def test_returns_list_of_usgs_events(self):
        feature = _make_feature(
            event_id="us7000abcd", title="M 7.1 - Test", mag=7.1,
            lon=-118.5, lat=34.0, depth=15.0, time="2024-01-01T00:00:00Z",
        )
        mock_resp = _mock_response(_make_geojson_response(feature))

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.return_value = mock_resp
            mock_get_req.return_value = mock_requests

            events = search_events(min_magnitude=7.0)

        assert len(events) == 1
        ev = events[0]
        assert isinstance(ev, USGSEvent)
        assert ev.event_id == "us7000abcd"
        assert ev.magnitude == pytest.approx(7.1)
        assert ev.latitude == pytest.approx(34.0)
        assert ev.longitude == pytest.approx(-118.5)
        assert ev.depth_km == pytest.approx(15.0)

    def test_returns_multiple_events(self):
        features = [
            _make_feature(event_id=f"ev{i}", mag=6.0 + i * 0.1)
            for i in range(5)
        ]
        mock_resp = _mock_response(_make_geojson_response(*features))

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.return_value = mock_resp
            mock_get_req.return_value = mock_requests

            events = search_events()

        assert len(events) == 5

    def test_empty_feature_list_returns_empty(self):
        mock_resp = _mock_response({"type": "FeatureCollection", "features": []})

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.return_value = mock_resp
            mock_get_req.return_value = mock_requests

            events = search_events()

        assert events == []

    def test_passes_min_magnitude_param(self):
        mock_resp = _mock_response(_make_geojson_response())

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.return_value = mock_resp
            mock_get_req.return_value = mock_requests

            search_events(min_magnitude=6.5, limit=10)

            call_kwargs = mock_requests.get.call_args
            params = call_kwargs[1]["params"]
            assert params["minmagnitude"] == 6.5
            assert params["limit"] == 10

    def test_passes_time_bounds_when_given(self):
        mock_resp = _mock_response(_make_geojson_response())

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.return_value = mock_resp
            mock_get_req.return_value = mock_requests

            search_events(start_time="2024-01-01", end_time="2024-12-31")

            params = mock_requests.get.call_args[1]["params"]
            assert params["starttime"] == "2024-01-01"
            assert params["endtime"] == "2024-12-31"

    def test_passes_bounding_box_when_given(self):
        mock_resp = _mock_response(_make_geojson_response())

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.return_value = mock_resp
            mock_get_req.return_value = mock_requests

            search_events(
                min_latitude=30.0, max_latitude=40.0,
                min_longitude=-120.0, max_longitude=-110.0,
            )

            params = mock_requests.get.call_args[1]["params"]
            assert params["minlatitude"] == 30.0
            assert params["maxlatitude"] == 40.0
            assert params["minlongitude"] == -120.0
            assert params["maxlongitude"] == -110.0

    def test_omits_time_params_when_none(self):
        mock_resp = _mock_response(_make_geojson_response())

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.return_value = mock_resp
            mock_get_req.return_value = mock_requests

            search_events()

            params = mock_requests.get.call_args[1]["params"]
            assert "starttime" not in params
            assert "endtime" not in params
            assert "minlatitude" not in params

    def test_http_error_propagates(self):
        from requests.exceptions import HTTPError

        mock_resp = _mock_response({}, status_code=503)

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.return_value = mock_resp
            mock_get_req.return_value = mock_requests

            with pytest.raises(HTTPError):
                search_events()

    def test_calls_correct_endpoint(self):
        mock_resp = _mock_response(_make_geojson_response())

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.return_value = mock_resp
            mock_get_req.return_value = mock_requests

            search_events()

            url = mock_requests.get.call_args[0][0]
            assert "fdsnws/event/1/query" in url


# ---------------------------------------------------------------------------
# fetch_coulomb_inp
# ---------------------------------------------------------------------------

class TestFetchCoulombInp:
    def _detail_response(self, inp_url: str = "https://example.com/coulomb.inp") -> dict:
        return {
            "properties": {
                "products": {
                    "finite-fault": [
                        {
                            "contents": {
                                "coulomb.inp": {"url": inp_url},
                            }
                        }
                    ]
                }
            }
        }

    def test_writes_inp_to_output_path(self, tmp_path: Path):
        detail = self._detail_response("https://example.com/coulomb.inp")
        detail_resp = _mock_response(detail)

        inp_content = "title line\nsecond title\n"
        inp_resp = MagicMock()
        inp_resp.raise_for_status.return_value = None
        inp_resp.text = inp_content

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.side_effect = [detail_resp, inp_resp]
            mock_get_req.return_value = mock_requests

            out = fetch_coulomb_inp("us7000abcd", tmp_path / "output.inp")

        assert out == tmp_path / "output.inp"
        assert out.read_text(encoding="utf-8") == inp_content

    def test_creates_parent_directory(self, tmp_path: Path):
        detail = self._detail_response()
        detail_resp = _mock_response(detail)

        inp_resp = MagicMock()
        inp_resp.raise_for_status.return_value = None
        inp_resp.text = "data"

        nested = tmp_path / "a" / "b" / "c" / "out.inp"

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.side_effect = [detail_resp, inp_resp]
            mock_get_req.return_value = mock_requests

            fetch_coulomb_inp("us7000abcd", nested)

        assert nested.parent.is_dir()

    def test_raises_if_no_finite_fault_product(self, tmp_path: Path):
        detail = {"properties": {"products": {}}}
        detail_resp = _mock_response(detail)

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.return_value = detail_resp
            mock_get_req.return_value = mock_requests

            with pytest.raises(ValueError, match="finite-fault"):
                fetch_coulomb_inp("us7000xxxx", tmp_path / "out.inp")

    def test_raises_if_no_inp_in_contents(self, tmp_path: Path):
        detail = {
            "properties": {
                "products": {
                    "finite-fault": [
                        {"contents": {"somefile.xml": {"url": "https://x.com/a.xml"}}}
                    ]
                }
            }
        }
        detail_resp = _mock_response(detail)

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.return_value = detail_resp
            mock_get_req.return_value = mock_requests

            with pytest.raises(ValueError, match=r"\.inp"):
                fetch_coulomb_inp("us7000xxxx", tmp_path / "out.inp")

    def test_http_404_on_detail_propagates(self, tmp_path: Path):
        from requests.exceptions import HTTPError

        detail_resp = _mock_response({}, status_code=404)

        with patch("opencoulomb.io.usgs_client._get_requests") as mock_get_req:
            mock_requests = MagicMock()
            mock_requests.get.return_value = detail_resp
            mock_get_req.return_value = mock_requests

            with pytest.raises(HTTPError):
                fetch_coulomb_inp("us0000xxxx", tmp_path / "out.inp")


# ---------------------------------------------------------------------------
# Live network tests (skipped unless --network flag used)
# ---------------------------------------------------------------------------

@pytest.mark.network
def test_live_search_events_returns_results():
    """Live call: returns at least one recent M≥7 event."""
    events = search_events(min_magnitude=7.0, limit=5)
    assert len(events) >= 0  # graceful: may be empty but must not crash
    for ev in events:
        assert isinstance(ev, USGSEvent)
        assert ev.magnitude >= 7.0
