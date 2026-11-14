"""Power-of-attorney tests for the POWER fetch: parsing, missing-value handling and
provenance. No network access — the download is stubbed."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from pipeline import sources
from pipeline.config import Config

POWER_FIXTURE = """-BEGIN HEADER-
NASA/POWER Source Native Resolution Daily Data
parameter(s):
T2M                   MERRA-2 Temperature at 2 Meters (C)
-END HEADER-
YEAR,DOY,T2M,T2M_MAX,T2M_MIN,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR
2020,183,28.05,34.81,21.06,52.15,4.52,28.83,1.28
2020,184,-999,-999,22.10,58.56,2.99,22.73,-999
2020,185,26.95,33.87,19.50,58.53,2.59,27.93,3.44
"""


def test_request_url_carries_centroid_years_and_parameters():
    url = sources.power_request_url(Config())
    assert "longitude=-100.874" in url and "latitude=38.0" in url
    assert "start=19950101" in url and "end=20251231" in url
    assert "format=CSV" in url
    for param in sources.POWER_PARAMS:
        assert param in url


def test_read_power_csv_skips_the_header_block(tmp_path):
    path = tmp_path / "power.csv"
    path.write_text(POWER_FIXTURE)
    frame = sources._read_power_csv(path)
    assert list(frame.columns)[:2] == ["year", "doy"]
    assert len(frame) == 3


def test_fetch_power_writes_tidy_interim_and_flags_missing(tmp_path, monkeypatch):
    raw_dir, interim_dir = tmp_path / "raw", tmp_path / "interim"
    monkeypatch.setattr(sources, "RAW", raw_dir)
    monkeypatch.setattr(sources, "INTERIM", interim_dir)

    def fake_download(url, dest, **kwargs):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(POWER_FIXTURE)
        return dest

    monkeypatch.setattr(sources, "download", fake_download)
    out = sources.fetch_power(Config())

    tidy = pd.read_csv(out, parse_dates=["date"])
    assert list(tidy["date"].dt.strftime("%Y-%m-%d")) == ["2020-07-01", "2020-07-02", "2020-07-03"]
    # -999 is a sentinel for "cannot be computed": it must become NaN, never 0.
    assert tidy.loc[1, "t2m_c"] != tidy.loc[1, "t2m_c"]
    assert tidy.loc[1, "precip_mm_d"] != tidy.loc[1, "precip_mm_d"]
    assert tidy.loc[0, "precip_mm_d"] == pytest.approx(1.28)
    assert tidy["t2m_max_c"].max() == pytest.approx(34.81)

    meta = json.loads((interim_dir / "weather_daily.meta.json").read_text())
    assert meta["missing_by_column"]["t2m"] == 1
    assert meta["missing_by_column"]["prectotcorr"] == 1
    assert meta["rows"] == 3
    assert meta["days_expected"] == 11323  # 1995-01-01 .. 2025-12-31
    assert meta["days_missing"] == 11320
    assert meta["columns"]["precip_mm_d"] == "mm/day"
