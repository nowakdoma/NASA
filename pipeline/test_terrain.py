"""SRTM tile naming, HGT decoding and slope arithmetic."""

from __future__ import annotations

import gzip
import math

import numpy as np
import pytest

from pipeline import terrain


def test_tiles_cover_the_finney_county_bbox():
    bbox = (-101.103, 37.737, -100.652, 38.264)
    assert terrain.tiles_for_bbox(bbox) == ["N37W102", "N37W101", "N38W102", "N38W101"]


def test_srtm_url_has_no_duplicated_path_segment():
    """Regression: 'skadi/N37/N37W102/N37W102.hgt.gz' returns 404 from the bucket."""
    url = terrain.srtm_url("N37W102")
    assert url == "https://s3.amazonaws.com/elevation-tiles-prod/skadi/N37/N37W102.hgt.gz"
    assert url.count("/N37W102") == 1


def test_negative_degrees_use_S_and_W():
    assert terrain.tiles_for_bbox((-1.5, -1.5, -0.5, -0.5)) == [
        "S02W002",
        "S02W001",
        "S01W002",
        "S01W001",
    ]


def _write_hgt(path, elev):
    data = np.asarray(elev, dtype=">i2").tobytes()
    with gzip.open(path, "wb") as fh:
        fh.write(data)


def test_read_hgt_rejects_wrong_size(tmp_path):
    path = tmp_path / "tiny.hgt.gz"
    _write_hgt(path, np.zeros((10, 10)))
    with pytest.raises(ValueError, match="expected"):
        terrain.read_hgt(path)


def test_read_hgt_maps_nodata_to_nan(tmp_path):
    grid = np.full((terrain.GRID, terrain.GRID), 100, dtype=">i2")
    grid[0, 0] = terrain.NODATA
    path = tmp_path / "N00E000.hgt.gz"
    _write_hgt(path, grid)
    elev = terrain.read_hgt(path)
    assert np.isnan(elev[0, 0])
    assert elev[1, 1] == pytest.approx(100.0)


def test_flat_ground_has_zero_slope():
    flat = np.full((20, 20), 900.0, dtype=np.float32)
    assert np.allclose(terrain.slope_percent(flat, lat=38.0), 0.0)


def test_slope_of_a_uniform_eastward_ramp():
    """1 m rise per pixel east = 1 / (30.87 * cos(lat)) * 100 percent."""
    elev = np.tile(np.arange(20, dtype=np.float32), (20, 1))
    lat = 38.0
    slope = terrain.slope_percent(elev, lat=lat)
    expected = 100.0 / (terrain.ARC_SEC_M * math.cos(math.radians(lat)))
    assert slope[10, 10] == pytest.approx(expected, rel=1e-6)
    # A north-south ramp uses the full 30.87 m spacing, so it is shallower.
    elev_ns = np.tile(np.arange(20, dtype=np.float32).reshape(-1, 1), (1, 20))
    assert terrain.slope_percent(elev_ns, lat=lat)[10, 10] == pytest.approx(
        100.0 / terrain.ARC_SEC_M, rel=1e-6
    )
