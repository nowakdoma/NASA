"""Frost risk from NASA POWER daily T2M_MIN.

Per year: the last spring frost (last sub-zero minimum before mid-year) and the first fall
frost (first sub-zero minimum after it), plus the frost-free season between them. Then the
p10/p50/p90 of the frost dates and season length over 1995-2025.

Two definitions that matter and are easy to get wrong:
- A "frost" is Tmin < 0 C at the POWER grid cell, i.e. a screen-height air frost. Ground
  frost happens at warmer air temperatures (~2-3 C), so this understates ground frost.
- Missing days are skipped, never treated as frost-free. A year with a month of missing
  minima in April must not silently report a late spring frost.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.config import INTERIM, Config

FROST_THRESHOLD_C = 0.0
# Window edges. A frost in the July gap is neither a spring nor a fall frost; it is counted
# separately instead of being silently attached to the wrong end of the season.
SPRING_END_DOY = 182  # 30 June
FALL_START_DOY = 213  # 1 August


def frost_dates(daily: pd.DataFrame, *, threshold_c: float = FROST_THRESHOLD_C) -> pd.DataFrame:
    """Last spring frost and first fall frost per calendar year.

    ``daily`` needs ``date`` and ``t2m_min_c``. Rows with a missing minimum are ignored.
    """
    frame = daily.loc[:, ["date", "t2m_min_c"]].copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.dropna(subset=["t2m_min_c"]).sort_values("date").reset_index(drop=True)
    frame["year"] = frame["date"].dt.year
    frame["doy"] = frame["date"].dt.dayofyear
    frosty = frame["t2m_min_c"] < threshold_c

    rows = []
    for year, group in frame.assign(frost=frosty).groupby("year", sort=True):
        spring = group[(group["doy"] <= SPRING_END_DOY) & group["frost"]]
        autumn = group[(group["doy"] >= FALL_START_DOY) & group["frost"]]
        midsummer = group[
            (group["doy"] > SPRING_END_DOY) & (group["doy"] < FALL_START_DOY) & group["frost"]
        ]
        last_spring = spring["date"].max() if not spring.empty else pd.NaT
        first_fall = autumn["date"].min() if not autumn.empty else pd.NaT
        season = (
            int((first_fall - last_spring).days)
            if pd.notna(last_spring) and pd.notna(first_fall)
            else None
        )
        rows.append(
            {
                "year": int(year),
                "last_spring_frost": last_spring.date().isoformat()
                if pd.notna(last_spring)
                else "",
                "first_fall_frost": first_fall.date().isoformat() if pd.notna(first_fall) else "",
                "spring_doy": int(last_spring.dayofyear) if pd.notna(last_spring) else None,
                "fall_doy": int(first_fall.dayofyear) if pd.notna(first_fall) else None,
                "frost_free_days": season,
                "min_tmin_c": round(float(group["t2m_min_c"].min()), 1),
                "days_observed": int(len(group)),
                "summer_frost_days": int(len(midsummer)),
            }
        )
    return pd.DataFrame(rows)


def _doy_to_date(year: int, doy: float) -> str:
    return (
        (pd.Timestamp(year=year, month=1, day=1) + pd.Timedelta(days=int(round(doy)) - 1))
        .date()
        .isoformat()
    )


def frost_summary(per_year: pd.DataFrame, *, reference_year: int | None = None) -> dict:
    """p10/p50/p90 of the spring and fall frost dates and the frost-free season."""
    ref = reference_year or int(per_year["year"].max())
    out: dict = {"reference_year": ref, "years": int(per_year["year"].nunique())}
    for key, column in (("spring", "spring_doy"), ("fall", "fall_doy")):
        values = per_year[column].dropna().to_numpy(dtype=float)
        if values.size:
            p10, p50, p90 = np.percentile(values, [10, 50, 90])
            out[key] = {
                "p10": _doy_to_date(ref, p10),
                "p50": _doy_to_date(ref, p50),
                "p90": _doy_to_date(ref, p90),
                "p10_doy": round(float(p10), 1),
                "p50_doy": round(float(p50), 1),
                "p90_doy": round(float(p90), 1),
            }
    season = per_year["frost_free_days"].dropna().to_numpy(dtype=float)
    if season.size:
        p10, p50, p90 = np.percentile(season, [10, 50, 90])
        out["frost_free_days"] = {
            "p10": int(round(p10)),
            "p50": int(round(p50)),
            "p90": int(round(p90)),
        }
    return out


def derive_frost(cfg: Config) -> Path:
    """data/interim/weather_daily.csv -> frost_windows.csv + frost_windows.json."""
    weather = INTERIM / "weather_daily.csv"
    if not weather.exists():
        raise FileNotFoundError(f"{weather} is missing — run `python -m pipeline power` first")
    daily = pd.read_csv(weather, parse_dates=["date"])

    per_year = frost_dates(daily)
    out = INTERIM / "frost_windows.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(per_year.columns))
        writer.writeheader()
        writer.writerows(per_year.to_dict("records"))

    summary = frost_summary(per_year)
    y0, y1 = cfg.weather_years
    payload = {
        "source": "NASA POWER daily T2M_MIN (MERRA-2), county grid cell",
        "threshold_c": FROST_THRESHOLD_C,
        "definition": (
            "air frost: daily minimum below 0 C. Ground frost occurs at warmer air "
            "temperatures, so this understates ground frost risk."
        ),
        "years": [y0, y1],
        "summary": summary,
        "per_year": per_year.to_dict("records"),
        "note": (
            "One POWER grid cell (0.5 x 0.625 deg) for the whole county; not a field "
            "measurement. Missing days are skipped, not assumed frost-free."
        ),
        "bias": (
            "A MERRA-2 grid cell averages over ~50 km, which smooths cold nights. Expect the "
            "last spring frost to read EARLY and the first fall frost LATE, so the frost-free "
            "season is overstated — here about 199 d p50 against a documented Garden City "
            "range nearer 155-170 d. Use these as relative risk between years, not as "
            "absolute planting dates; a farmer's own on-farm records will be sharper."
        ),
    }
    json_out = INTERIM / "frost_windows.json"
    json_out.write_text(json.dumps(payload, indent=1) + "\n")

    season = summary.get("frost_free_days", {})
    print(
        f"[frost] {len(per_year)} years, last spring frost p50 {summary.get('spring', {}).get('p50', '?')}"
        f", first fall frost p50 {summary.get('fall', {}).get('p50', '?')}, frost-free "
        f"p10-p90 {season.get('p10', '?')}-{season.get('p90', '?')} d -> {json_out.name}"
    )
    return json_out
