"""Frost detection: which date counts, missing data, and the percentile summary."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline import frost


def _daily(pairs):
    dates = pd.to_datetime([p[0] for p in pairs])
    return pd.DataFrame({"date": dates, "t2m_min_c": [p[1] for p in pairs]})


def test_last_spring_and_first_fall_frost():
    daily = _daily(
        [
            ("2020-03-10", -2.0),
            ("2020-04-20", -1.5),  # last spring frost
            ("2020-05-01", 3.0),
            ("2020-10-05", 2.0),
            ("2020-10-12", -0.5),  # first fall frost
            ("2020-11-01", -4.0),
        ]
    )
    row = frost.frost_dates(daily).iloc[0]
    assert row["last_spring_frost"] == "2020-04-20"
    assert row["first_fall_frost"] == "2020-10-12"
    assert row["frost_free_days"] == (pd.Timestamp("2020-10-12") - pd.Timestamp("2020-04-20")).days


def test_exactly_zero_is_not_a_frost():
    daily = _daily([("2021-04-01", 0.0), ("2021-10-01", -0.1)])
    row = frost.frost_dates(daily).iloc[0]
    assert row["last_spring_frost"] == ""  # 0.0 C is not below the threshold
    assert row["first_fall_frost"] == "2021-10-01"


def test_missing_minimum_is_skipped_not_treated_as_frost_free():
    """A NaN in April must not become 'no spring frost' or a fabricated date."""
    daily = _daily([("2022-03-15", -3.0), ("2022-04-15", None), ("2022-10-20", -1.0)])
    row = frost.frost_dates(daily).iloc[0]
    assert row["last_spring_frost"] == "2022-03-15"
    assert row["days_observed"] == 2


def test_year_without_fall_frost_reports_no_season():
    daily = _daily([("2023-04-10", -1.0), ("2023-11-30", 2.0)])
    row = frost.frost_dates(daily).iloc[0]
    assert row["first_fall_frost"] == ""
    assert pd.isna(row["frost_free_days"]) or row["frost_free_days"] is None


def test_july_frost_is_counted_separately_not_attached_to_either_end():
    """A July frost is neither a spring nor a fall frost; mislabelling it produces a
    nonsense season (1 May -> 5 July). It is counted in summer_frost_days instead."""
    daily = _daily([("2024-05-01", -1.0), ("2024-07-05", -2.0), ("2024-09-20", -0.5)])
    row = frost.frost_dates(daily).iloc[0]
    assert row["last_spring_frost"] == "2024-05-01"
    assert row["first_fall_frost"] == "2024-09-20"
    assert row["summer_frost_days"] == 1


def test_summary_percentiles_and_reference_year():
    per_year = pd.DataFrame(
        {
            "year": [2018, 2019, 2020, 2021, 2022],
            "spring_doy": [100, 110, 120, 130, 140],
            "fall_doy": [280, 290, 300, 310, 320],
            "frost_free_days": [180, 180, 180, 180, 180],
        }
    )
    summary = frost.frost_summary(per_year, reference_year=2022)
    assert summary["years"] == 5
    assert summary["spring"]["p50_doy"] == pytest.approx(120.0)
    assert summary["spring"]["p50"] == frost._doy_to_date(2022, 120)
    assert summary["frost_free_days"]["p50"] == 180
    # p10 < p50 < p90 for a monotonically increasing series
    assert (
        summary["spring"]["p10_doy"] < summary["spring"]["p50_doy"] < summary["spring"]["p90_doy"]
    )


def test_summary_of_a_constant_series_has_equal_percentiles():
    per_year = pd.DataFrame(
        {
            "year": [2020, 2021],
            "spring_doy": [110, 110],
            "fall_doy": [290, 290],
            "frost_free_days": [180, 180],
        }
    )
    summary = frost.frost_summary(per_year)
    assert summary["spring"]["p10_doy"] == summary["spring"]["p90_doy"] == 110.0


def test_nan_percentiles_do_not_leak():
    per_year = pd.DataFrame(
        {
            "year": [2020, 2021],
            "spring_doy": [110, np.nan],
            "fall_doy": [np.nan, 290],
            "frost_free_days": [np.nan, np.nan],
        }
    )
    summary = frost.frost_summary(per_year)
    assert summary["spring"]["p50_doy"] == 110.0
    assert summary["fall"]["p50_doy"] == 290.0
    assert "frost_free_days" not in summary
