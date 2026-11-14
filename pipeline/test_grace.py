"""GRACE helpers: grid windowing, CF time decoding, and the trend fit."""

from __future__ import annotations

import numpy as np
import pytest
from rasterio.transform import from_origin

from pipeline import grace


def test_bbox_window_covers_the_county_cells():
    # 0.5 degree global grid, origin at (-180, 90)
    transform = from_origin(-180.0, 90.0, 0.5, 0.5)
    row0, row1, col0, col1 = grace.bbox_window(
        transform, (-101.103, 37.737, -100.652, 38.264), (360, 720)
    )
    assert (row0, row1) == (103, 105)
    assert (col0, col1) == (157, 159)
    assert (row1 - row0) * (col1 - col0) == 4


def test_bbox_window_handles_a_zero_to_360_grid():
    """The GRACE netCDF x origin is 0, so -101 deg is column 518, not a negative index."""
    transform = from_origin(0.0, 90.0, 0.5, 0.5)
    row0, row1, col0, col1 = grace.bbox_window(
        transform, (-101.103, 37.737, -100.652, 38.264), (360, 720)
    )
    assert (row0, row1) == (103, 105)
    assert (col0, col1) == (517, 519)


def test_bbox_outside_the_grid_raises():
    transform = from_origin(-180.0, 90.0, 0.5, 0.5)
    with pytest.raises(ValueError, match="outside the grid"):
        grace.bbox_window(transform, (200.0, 37.0, 201.0, 38.0), (360, 720))


def test_days_to_dates_uses_the_cf_epoch():
    assert grace.days_to_dates(np.array([106.5]))[0] == "2002-04-17"
    assert grace.days_to_dates(np.array([0.0]))[0] == "2002-01-01"


def test_decimal_years_are_fractional():
    years = grace.decimal_years(["2002-01-01", "2002-07-02", "2003-01-01"])
    assert years[0] == pytest.approx(2002.0, abs=1e-6)
    assert 2002.49 < years[1] < 2002.51
    assert years[2] == pytest.approx(2003.0, abs=1e-6)


def test_linear_trend_recovers_a_known_slope():
    years = np.arange(2002.0, 2023.0, 1 / 12)
    values = -0.75 * (years - 2002) + 3.0
    trend = grace.linear_trend(years, values)
    assert trend["cm_per_year"] == pytest.approx(-0.75, abs=1e-6)
    assert trend["r2"] == pytest.approx(1.0, abs=1e-6)
    assert trend["months"] == years.size


def test_linear_trend_ignores_nan_months():
    years = np.arange(2002.0, 2006.0, 1 / 12)
    values = -0.5 * (years - 2002)
    values[5] = np.nan
    values[13] = np.nan
    trend = grace.linear_trend(years, values)
    assert trend["cm_per_year"] == pytest.approx(-0.5, abs=1e-6)
    assert trend["months"] == years.size - 2


def test_linear_trend_needs_three_points():
    assert (
        grace.linear_trend(np.array([2002.0, 2003.0]), np.array([1.0, 2.0]))["cm_per_year"] is None
    )


def test_flat_series_has_zero_slope_not_a_crash():
    years = np.arange(2002.0, 2005.0, 1 / 12)
    trend = grace.linear_trend(years, np.full(years.shape, 4.0))
    assert trend["cm_per_year"] == pytest.approx(0.0, abs=1e-9)
    # R2 is 0/0 when the series is constant; it must not be NaN.
    assert trend["r2"] == 0.0


def test_one_per_month_keeps_the_mid_month_epoch():
    rows = [
        {"date": "2012-01-01", "tws_cm": -4.55, "uncertainty_cm": 1.0},
        {"date": "2012-01-16", "tws_cm": -4.35, "uncertainty_cm": 1.0},
        {"date": "2012-02-15", "tws_cm": -5.04, "uncertainty_cm": 1.0},
    ]
    kept, dropped = grace.one_per_month(rows)
    assert dropped == 1
    assert [r["date"] for r in kept] == ["2012-01-16", "2012-02-15"]
    assert kept[0]["tws_cm"] == -4.35


def test_one_per_month_preserves_order_and_handles_single_epochs():
    rows = [
        {"date": "2002-04-17", "tws_cm": 6.31, "uncertainty_cm": 3.0},
        {"date": "2002-05-10", "tws_cm": 6.0, "uncertainty_cm": 3.0},
    ]
    kept, dropped = grace.one_per_month(rows)
    assert dropped == 0
    assert [r["date"] for r in kept] == ["2002-04-17", "2002-05-10"]
