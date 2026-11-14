"""Assembly rules: which fields survive, and how layers become contract shape."""

from __future__ import annotations

import json

import pytest

from pipeline import assemble
from pipeline.config import Config

SOIL_ROW = {
    "field_id": "FIN-001",
    "map_unit": "Ulysses silt loam, 1 to 3 percent slopes",
    "texture": "silt loam",
    "om_pct": "1.8",
    "kffact": "0.43",
    "awc_mm": "190.0",
    "slope_pct": "1.2",
}


def _field(fid="FIN-001", years=("2008", "2009"), history=None):
    return {
        "type": "Feature",
        "id": fid,
        "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]]},
        "properties": {
            "field_id": fid,
            "area_ha": 50.0,
            "irrigated": True,
            "irrigation_type": "center_pivot",
            "crop_history": history if history is not None else dict.fromkeys(years, "corn"),
        },
    }


def test_soil_block_requires_a_real_texture():
    assert assemble._soil_block(SOIL_ROW)["texture"] == "silt loam"
    assert assemble._soil_block({**SOIL_ROW, "texture": "unknown"}) is None
    assert assemble._soil_block(None) is None


def test_heat_index_takes_the_worst_severity_per_year():
    windows = [
        {"year": 2022, "severity": 0.2},
        {"year": 2022, "severity": 0.51},
        {"year": 2021, "severity": 0.3},
    ]
    assert assemble.heat_index_by_year(windows) == {"2022": 0.51, "2021": 0.3}


def test_bare_periods_group_by_field(tmp_path):
    path = tmp_path / "bare.csv"
    path.write_text(
        "field_id,year,start,end,composites,ndvi_min,ndvi_mean,source,note\n"
        "FIN-001,2021,2021-01-01,2021-02-01,3,0.1,0.15,NDVI,low\n"
        "FIN-002,2021,2021-03-01,2021-04-01,2,0.2,0.25,NDVI,low\n"
    )
    grouped = assemble.load_bare_periods(path)
    assert set(grouped) == {"FIN-001", "FIN-002"}
    assert grouped["FIN-001"][0]["year"] == 2021


def test_heat_windows_are_filtered_to_crop_years(tmp_path):
    path = tmp_path / "heat.csv"
    path.write_text(
        "year,start,end,days,severity,tmax_peak_c,threshold_c,source\n"
        "1999,1999-07-01,1999-07-05,5,0.4,39.0,35.0,POWER\n"
        "2010,2010-07-01,2010-07-05,5,0.5,40.0,35.0,POWER\n"
    )
    windows = assemble.load_heat_windows(path, {2010})
    assert len(windows) == 1
    assert windows[0]["year"] == 2010
    assert windows[0]["type"] == "heat"


def _write_interim(tmp_path, monkeypatch, features, soil_rows=(SOIL_ROW,)):
    monkeypatch.setattr(assemble, "INTERIM", tmp_path)
    raw = {
        "type": "FeatureCollection",
        "county": {
            "name": "Finney County",
            "state": "KS",
            "fips": "20055",
            "bbox": [-101.103, 37.737, -100.652, 38.264],
        },
        "years": [2008, 2009],
        "features": features,
    }
    (tmp_path / "fields_raw.geojson").write_text(json.dumps(raw))
    import csv as _csv

    with (tmp_path / "field_soil.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = _csv.DictWriter(fh, fieldnames=list(soil_rows[0]))
        writer.writeheader()
        writer.writerows(soil_rows)
    (tmp_path / "heat_stress_windows.csv").write_text(
        "year,start,end,days,severity,tmax_peak_c,threshold_c,source\n"
        "2008,2008-07-01,2008-07-05,5,0.4,39.0,35.0,POWER\n"
    )


def test_incomplete_crop_history_drops_the_field(tmp_path, monkeypatch):
    """A year whose CDL class has no crops.csv code must drop the field, not fudge it."""
    cfg = Config()
    cfg = Config()  # crop_years 2008..2025
    fields = [_field("FIN-001", years=("2008",)), _field("FIN-002", years=("2008", "2009"))]
    _write_interim(
        tmp_path,
        monkeypatch,
        fields,
        soil_rows=(SOIL_ROW, {**SOIL_ROW, "field_id": "FIN-002"}),
    )
    # Both fields lack most of 2008-2025, so both are dropped and that must be explicit.
    from pipeline import assemble as mod

    out, meta = mod.assemble(cfg)
    assert meta["fields_emitted"] == 0
    assert len(meta["fields_dropped"]) == 2
    assert json.loads(out.read_text())["features"] == []


def test_every_year_is_present_in_emitted_crop_history(tmp_path, monkeypatch):
    cfg = Config()
    complete = {str(y): "corn" for y in range(cfg.crop_years[0], cfg.crop_years[1] + 1)}
    _write_interim(tmp_path, monkeypatch, [_field("FIN-001", history=complete)])
    out, meta = assemble.assemble(cfg)
    assert meta["fields_emitted"] == 1
    feature = json.loads(out.read_text())["features"][0]
    assert set(feature["properties"]["crop_history"]) == set(complete)
    assert feature["properties"]["soil"]["awc_mm"] == pytest.approx(190.0)
    # Heat-only windows, and the index is populated for every year.
    assert all(
        w["type"] == "heat" for w in feature["properties"]["season_calendar"]["stress_windows"]
    )
    assert len(feature["properties"]["stress_index_by_year"]) == len(complete)
    assert meta["data_gaps"]
