"""Heat-window detection: run merging, gap handling and severity bounds."""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline import derive


def _daily(dates: list[str], tmax: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"date": pd.to_datetime(dates), "t2m_max_c": tmax})


def test_two_heat_waves_separated_by_cool_days_stay_two_windows():
    daily = _daily(
        ["2020-07-01", "2020-07-02", "2020-07-03", "2020-07-04", "2020-07-05", "2020-07-06"],
        [40.0, 41.0, 42.0, 20.0, 20.0, 36.0],
    )
    windows = derive.heat_windows(daily, min_days=1)
    assert len(windows) == 2
    assert list(windows["start"]) == ["2020-07-01", "2020-07-06"]
    assert list(windows["days"]) == [3, 1]


def test_single_day_spike_is_dropped_by_min_days():
    daily = _daily(["2021-08-01", "2021-08-02", "2021-08-03"], [20.0, 45.0, 20.0])
    assert derive.heat_windows(daily).empty


def test_missing_tmax_breaks_a_window():
    daily = _daily(
        ["2022-06-01", "2022-06-02", "2022-06-03", "2022-06-04"], [40.0, None, 40.0, 41.0]
    )
    windows = derive.heat_windows(daily)
    # The NaN day is neither hot nor cool: the 1-day run before it is dropped, the 2-day
    # run after it survives.
    assert len(windows) == 1
    assert windows.iloc[0]["start"] == "2022-06-03"
    assert windows.iloc[0]["days"] == 2


def test_year_boundary_splits_windows():
    daily = _daily(
        ["2020-12-30", "2020-12-31", "2021-01-01", "2021-01-02"], [40.0, 40.0, 40.0, 40.0]
    )
    windows = derive.heat_windows(daily)
    assert list(windows["year"]) == [2020, 2021]
    assert list(windows["days"]) == [2, 2]


def test_severity_is_bounded_and_grows_with_exceedance():
    mild = derive.heat_windows(_daily(["2020-07-01", "2020-07-02"], [36.0, 36.0]))
    severe = derive.heat_windows(_daily(["2020-07-01", "2020-07-02"], [44.0, 44.0]))
    assert mild.iloc[0]["severity"] == pytest.approx(0.1)
    assert severe.iloc[0]["severity"] == pytest.approx(0.9)
    assert 0.0 <= mild.iloc[0]["severity"] <= 1.0
    assert severe.iloc[0]["severity"] <= 1.0
    # Above the extreme anchor severity saturates instead of exceeding 1.
    beyond = derive.heat_windows(_daily(["2020-07-01", "2020-07-02"], [48.0, 48.0]))
    assert beyond.iloc[0]["severity"] == pytest.approx(1.0)


def test_window_records_peak_and_threshold():
    windows = derive.heat_windows(_daily(["2020-07-01", "2020-07-02"], [37.5, 43.25]))
    row = windows.iloc[0]
    assert row["end"] == "2020-07-02"
    assert row["tmax_peak_c"] == pytest.approx(43.25)
    assert row["threshold_c"] == derive.HEAT_THRESHOLD_C
    assert "POWER" in row["source"]


def test_derive_writes_csv_and_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(derive, "INTERIM", tmp_path)
    _daily(["2020-07-01", "2020-07-02", "2020-07-03"], [36.0, 37.0, 20.0]).to_csv(
        tmp_path / "weather_daily.csv", index=False, date_format="%Y-%m-%d"
    )
    out = derive.derive_heat_stress(derive.Config())
    assert out.exists()
    frame = pd.read_csv(out)
    assert len(frame) == 1 and int(frame.iloc[0]["days"]) == 2
    assert (tmp_path / "heat_stress_windows.meta.json").exists()


def test_derive_requires_power_first(tmp_path, monkeypatch):
    monkeypatch.setattr(derive, "INTERIM", tmp_path)
    with pytest.raises(FileNotFoundError, match="pipeline power"):
        derive.derive_heat_stress(derive.Config())
