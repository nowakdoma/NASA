"""Derivations on top of downloaded sources: data/raw/* -> data/interim/*.

Kept separate from ``sources`` so a re-download never invalidates a derivation, and
so the modelling assumptions in each derivation are visible in one place.

The severity rule here is a documented heuristic, not a physical index. It is
deliberately simple and linear in exceedance so the engine can replace it later
without touching the detected windows.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from pipeline.config import INTERIM, Config
from pipeline.fields import derive_fields
from pipeline.terrain import derive_terrain

# Thresholds for heat stress on the Finney County crops in contracts/crops.csv.
# 35 C is the commonly used maize/sorghum grain-fill heat threshold; 45 C is used
# only to scale severity to 1.0 (2012-06-27 hit 44.7 C at this centroid).
HEAT_THRESHOLD_C = 35.0
HEAT_EXTREME_C = 45.0
HEAT_MIN_DAYS = 2  # single-day spikes are noise at the POWER grid scale


def heat_windows(
    daily: pd.DataFrame,
    *,
    threshold_c: float = HEAT_THRESHOLD_C,
    extreme_c: float = HEAT_EXTREME_C,
    min_days: int = HEAT_MIN_DAYS,
) -> pd.DataFrame:
    """Merge consecutive days with Tmax >= threshold into windows, per calendar year.

    ``daily`` needs ``date`` and ``t2m_max_c``. Days with missing Tmax break a window
    rather than being treated as cool.
    """
    frame = daily.loc[:, ["date", "t2m_max_c"]].copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values("date").reset_index(drop=True)

    hot = (frame["t2m_max_c"] >= threshold_c).fillna(False).to_numpy()
    dates = frame["date"].tolist()

    rows = []
    idx, total = 0, len(frame)
    while idx < total:
        if not hot[idx]:
            idx += 1
            continue
        start = idx
        # Extend while the next day exists, is hot, is the next calendar day and stays
        # in the same year. Comparing hotness (not just date continuity) is what keeps
        # two heat waves separated by cool days as two windows.
        while (
            idx + 1 < total
            and hot[idx + 1]
            and (dates[idx + 1] - dates[idx]).days == 1
            and dates[idx + 1].year == dates[start].year
        ):
            idx += 1
        end = idx
        idx = end + 1
        span = frame.iloc[start : end + 1]
        if len(span) < min_days:
            continue
        exceedance = ((span["t2m_max_c"] - threshold_c) / (extreme_c - threshold_c)).clip(0.0, 1.0)
        rows.append(
            {
                "year": int(dates[start].year),
                "start": dates[start].date().isoformat(),
                "end": dates[end].date().isoformat(),
                "days": len(span),
                "severity": round(float(exceedance.mean()), 3),
                "tmax_peak_c": round(float(span["t2m_max_c"].max()), 2),
                "threshold_c": threshold_c,
                "source": "NASA POWER T2M_MAX daily (MERRA-2)",
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "year",
            "start",
            "end",
            "days",
            "severity",
            "tmax_peak_c",
            "threshold_c",
            "source",
        ],
    )


def derive_heat_stress(cfg: Config) -> Path:
    """data/interim/weather_daily.csv -> data/interim/heat_stress_windows.csv."""
    weather = INTERIM / "weather_daily.csv"
    if not weather.exists():
        raise FileNotFoundError(f"{weather} is missing — run `python -m pipeline power` first")
    daily = pd.read_csv(weather, parse_dates=["date"])
    windows = heat_windows(daily)

    out = INTERIM / "heat_stress_windows.csv"
    windows.to_csv(out, index=False)

    per_year = windows.groupby("year")["days"].sum()
    meta = {
        "source": "derived from data/interim/weather_daily.csv (NASA POWER T2M_MAX)",
        "rule": (
            f"consecutive days with T2M_MAX >= {HEAT_THRESHOLD_C} C lasting >= "
            f"{HEAT_MIN_DAYS} days"
        ),
        "severity_rule": (
            f"mean clip((Tmax - {HEAT_THRESHOLD_C}) / ({HEAT_EXTREME_C} - "
            f"{HEAT_THRESHOLD_C}), 0, 1) over the window; heuristic scale, not a "
            "physical index"
        ),
        "windows": len(windows),
        "years_with_windows": int(per_year.size),
        "hot_days_total": int(per_year.sum()),
        "years": [cfg.weather_years[0], cfg.weather_years[1]],
        "note": (
            "Single POWER grid cell (0.5 x 0.625 deg): one representative series for the "
            "county, not a per-field measurement. Missing Tmax breaks a window."
        ),
    }
    (INTERIM / "heat_stress_windows.meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    worst = per_year.sort_values(ascending=False).head(3)
    print(
        f"[heat] {len(windows)} windows, {meta['hot_days_total']} hot days over "
        f"{meta['years_with_windows']} years -> {out.name}"
        f" (worst: {', '.join(f'{y}:{d}d' for y, d in worst.items())})"
    )
    return out


DERIVATIONS = {"heat": derive_heat_stress, "fields": derive_fields, "terrain": derive_terrain}
