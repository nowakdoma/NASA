"""SSURGO parsing and soil arithmetic — the parts that must be right without the network."""

from __future__ import annotations

import pytest

from pipeline import soil


def _rows(*triples):
    """(top_cm, bottom_cm, awc_r, om_r, kffact) -> SDA-shaped dicts."""
    out = []
    for top, bottom, awc, om, k in triples:
        out.append(
            {
                "muname": "Valent fine sand, 5 to 20 percent slopes",
                "compname": "Valent",
                "comppct_r": "85",
                "hzdept_r": str(top),
                "hzdepb_r": str(bottom),
                "awc_r": None if awc is None else str(awc),
                "om_r": str(om),
                "kffact": str(k),
                "texdesc": "Fine sand",
            }
        )
    return out


def test_parse_columnname_payload_becomes_dicts():
    payload = '{"Table":[["mukey","muname"],["1152362","Valent fine sand"]]}'
    assert soil.parse_sda_payload(payload) == [{"mukey": "1152362", "muname": "Valent fine sand"}]


def test_parse_empty_table():
    assert soil.parse_sda_payload('{"Table":[]}') == []


def test_parse_raises_on_the_xml_error_page():
    """SDA answers SQL errors with XML and HTTP 400 — a bare json.loads would explode."""
    xml = '<?xml version="1.0"?><ServiceExceptionReport>column does not exist'
    with pytest.raises(soil.SoilDataError, match="non-JSON"):
        soil.parse_sda_payload(xml)


def test_wkt_and_centroid_of_a_square():
    geom = {
        "type": "Polygon",
        "coordinates": [[[0.0, 0.0], [2.0, 0.0], [2.0, 2.0], [0.0, 2.0], [0.0, 0.0]]],
    }
    assert soil.wkt_of(geom).startswith("POLYGON((0.000000 0.000000")
    assert soil.wkt_of(geom).count(" 0.000000") >= 1
    # The repeated closing vertex must not drag the centroid.
    assert soil.centroid_of(geom) == pytest.approx((1.0, 1.0))


def test_surface_horizon_is_the_topmost():
    rows = _rows((20, 50, 0.15, 0.5, 0.02), (0, 20, 0.07, 0.75, 0.02))
    assert soil.surface_horizon(rows)["hzdept_r"] == "0"


def test_profile_awc_sums_millimetres_and_clips_at_depth():
    rows = _rows(
        (0, 20, 0.20, 1.0, 0.3),  # 0.20 * 20 * 10 = 40 mm
        (20, 50, 0.15, 1.0, 0.3),  # 0.15 * 30 * 10 = 45 mm
        (50, 100, 0.10, 1.0, 0.3),  # 0.10 * 50 * 10 = 50 mm
        (100, 200, 0.05, 1.0, 0.3),  # clipped at 150 cm -> 0.05 * 50 * 10 = 25 mm
    )
    total, skipped = soil.profile_awc(rows, depth_cm=150.0)
    assert total == pytest.approx(160.0)
    assert skipped == 0
    # Only the top 100 cm.
    assert soil.profile_awc(rows, depth_cm=100.0)[0] == pytest.approx(135.0)


def test_null_awc_is_skipped_and_counted_not_treated_as_zero():
    rows = _rows((0, 20, 0.2, 1.0, 0.3), (20, 40, None, 1.0, 0.3), (40, 60, 0.1, 1.0, 0.3))
    total, skipped = soil.profile_awc(rows, depth_cm=150.0)
    assert skipped == 1
    # The bedrock horizon contributes nothing but does not zero the rest.
    assert total == pytest.approx(0.2 * 20 * 10 + 0.1 * 20 * 10)


def test_zero_awc_is_real_capacity_not_missing_data():
    rows = _rows((0, 20, 0.0, 0.1, 0.02))
    total, skipped = soil.profile_awc(rows)
    assert total == 0.0
    assert skipped == 0


def test_soil_from_rows_matches_the_field_contract_shape():
    rows = _rows((0, 20, 0.07, 0.75, 0.02), (20, 150, 0.06, 0.3, 0.02))
    result = soil.soil_from_rows(rows, depth_cm=150.0)
    assert result["texture"] == "fine sand"  # lowercased to match the mock convention
    assert result["om_pct"] == pytest.approx(0.75)
    assert result["kffact"] == pytest.approx(0.02)
    assert result["awc_mm"] == pytest.approx(0.07 * 20 * 10 + 0.06 * 130 * 10, rel=1e-3)
    assert result["map_unit"].startswith("Valent fine sand")
    assert result["component_pct"] == pytest.approx(85.0)


def test_soil_from_no_rows_is_explicitly_unknown():
    result = soil.soil_from_rows([])
    assert result["texture"] == "unknown"
    assert result["map_unit"] is None
    assert result["awc_mm"] == 0.0


def test_sda_query_retries_a_transient_connection_error(monkeypatch):
    """SDA drops connections under load; one reset must not abort a 120-request run."""
    import urllib.error
    import urllib.request

    calls = {"n": 0}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b'{"Table":[["mukey"],["123"]]}'

    def fake_urlopen(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            raise urllib.error.URLError("connection reset")
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)
    assert soil.sda_query("SELECT 1") == [{"mukey": "123"}]
    assert calls["n"] == 3


def test_sda_query_gives_up_and_raises_soil_error(monkeypatch):
    import urllib.error
    import urllib.request

    def always_fail(*args, **kwargs):
        raise urllib.error.URLError("down")

    monkeypatch.setattr(urllib.request, "urlopen", always_fail)
    monkeypatch.setattr("time.sleep", lambda *_a, **_k: None)
    with pytest.raises(soil.SoilDataError, match="unreachable after"):
        soil.sda_query("SELECT 1")


def test_sql_error_is_not_retried(monkeypatch):
    """A 400 means the SQL is wrong — retrying just triples the wait."""
    import urllib.error
    import urllib.request

    calls = {"n": 0}

    def bad_request(*args, **kwargs):
        calls["n"] += 1
        raise urllib.error.HTTPError(soil.SDA_URL, 400, "Bad Request", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", bad_request)
    with pytest.raises(soil.SoilDataError, match="HTTP 400"):
        soil.sda_query("SELECT nope")
    assert calls["n"] == 1
