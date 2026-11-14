"""NDVI compositing logic: field means, bare-run detection, year clipping."""

from __future__ import annotations

import numpy as np
import pytest

from pipeline import ndvi


def test_item_date_prefers_datetime_then_start():
    assert ndvi.item_date({"properties": {"datetime": "2022-07-28T00:00:00Z"}}) == "2022-07-28"
    # PC leaves datetime null for MOD13Q1; the date is in start_datetime.
    assert (
        ndvi.item_date({"properties": {"datetime": None, "start_datetime": "2022-07-28T00:00:00Z"}})
        == "2022-07-28"
    )


def test_field_means_ignores_outside_and_nan():
    labels = np.array([[0, 1, 1], [2, 2, 0]])
    values = np.array([[9.0, 0.5, 0.7], [np.nan, 0.2, 9.0]])
    means = ndvi.field_means(labels, values, 2)
    assert means[1] == pytest.approx(0.6)
    assert means[2] == pytest.approx(0.2)  # the NaN is excluded, not averaged in
    assert np.isnan(means[0])


def test_bare_run_needs_the_minimum_number_of_composites():
    dates = [f"2020-06-{d:02d}" for d in (2, 18, 26)]
    series = np.array([[0.2, 0.8, 0.2]])  # two isolated low readings, not a run
    assert ndvi.bare_periods(series, dates, ["FIN-001"]) == []


def test_two_consecutive_bare_composites_form_a_period():
    dates = ["2020-06-02", "2020-06-18", "2020-07-04"]
    series = np.array([[0.2, 0.25, 0.7]])
    periods = ndvi.bare_periods(series, dates, ["FIN-001"])
    assert len(periods) == 1
    assert periods[0]["start"] == "2020-06-02"
    assert periods[0]["end"] == "2020-06-18"
    assert periods[0]["composites"] == 2
    assert periods[0]["year"] == 2020
    assert periods[0]["ndvi_min"] == pytest.approx(0.2)


def test_nan_breaks_a_bare_run():
    """A cloudy composite is unknown, not bare — it must not bridge two dry spells."""
    dates = ["2020-06-02", "2020-06-18", "2020-07-04", "2020-07-20"]
    series = np.array([[0.2, np.nan, 0.2, 0.25]])
    periods = ndvi.bare_periods(series, dates, ["FIN-001"])
    assert len(periods) == 1
    assert periods[0]["start"] == "2020-07-04"


def test_period_is_clipped_at_the_year_boundary():
    """A run spanning New Year becomes one record per year, each needing its own minimum.

    The 2021 fragment here holds a single composite, so it is dropped rather than
    reported as a one-composite bare period.
    """
    dates = ["2020-12-11", "2020-12-27", "2021-01-12"]
    series = np.array([[0.2, 0.2, 0.2]])
    periods = ndvi.bare_periods(series, dates, ["FIN-001"])
    assert [p["year"] for p in periods] == [2020]
    assert periods[0]["end"] == "2020-12-27"


def test_both_sides_of_a_year_boundary_are_reported_when_well_populated():
    dates = ["2020-11-25", "2020-12-11", "2020-12-27", "2021-01-12", "2021-01-28"]
    series = np.array([[0.2, 0.2, 0.2, 0.2, 0.2]])
    periods = ndvi.bare_periods(series, dates, ["FIN-001"])
    assert [p["year"] for p in periods] == [2020, 2021]
    assert periods[0]["end"] == "2020-12-27"
    assert periods[1]["start"] == "2021-01-12"


def test_green_field_has_no_bare_period():
    dates = ["2021-06-01", "2021-06-17", "2021-07-03"]
    series = np.array([[0.75, 0.82, 0.68]])
    assert ndvi.bare_periods(series, dates, ["FIN-001"]) == []


def test_trailing_run_is_closed_at_the_last_composite():
    dates = ["2021-09-01", "2021-09-17", "2021-10-03"]
    series = np.array([[0.7, 0.2, 0.18]])
    periods = ndvi.bare_periods(series, dates, ["FIN-001"])
    assert len(periods) == 1
    assert periods[0]["end"] == "2021-10-03"


def test_bare_period_note_warns_that_ndvi_is_not_residue():
    """P4 in the test round: dormant alfalfa and standing stalks read as 'bare'."""
    dates = ["2020-12-11", "2020-12-27"]
    series = np.array([[0.2, 0.2]])
    periods = ndvi.bare_periods(series, dates, ["FIN-001"])
    note = periods[0]["note"]
    assert "NDVI" in note
    assert "dormant alfalfa" in note
    assert "residue" in note
