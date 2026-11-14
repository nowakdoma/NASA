"""Daily weather input for the engine.

Real input (written by pipeline/, person 2): ``data/interim/power_daily.csv``
    one row per day for the region centroid, 1995-01-01 .. 2025-12-31, no gaps, no -999:
    DATE (YYYY-MM-DD), T2M_MAX [°C], T2M_MIN [°C], RH2M [%], WS2M [m/s at 2 m],
    ALLSKY_SFC_SW_DWN [MJ/m²/day], PRECTOTCORR [mm/day]
    (NASA POWER daily, community "AG"; parameter names kept as-is.)

Fallback: :func:`synthetic_weather` — a seeded stochastic generator with a rough Garden City,
KS climatology. It exists ONLY so the engine can run before real data arrives. Output built
on it must be flagged ``mock: true`` and list a data gap.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from engine import REPO_ROOT

POWER_DAILY = REPO_ROOT / "data" / "interim" / "power_daily.csv"
COLUMNS = ["T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR"]


def load_power_daily(path: Path = POWER_DAILY) -> pd.DataFrame:
    """Read the pipeline CSV, check columns/gaps, return a DataFrame indexed by date."""
    df = pd.read_csv(path, parse_dates=["DATE"]).set_index("DATE").sort_index()
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    df = df[COLUMNS].astype(float)
    if df.isna().any().any() or (df <= -999).any().any():
        raise ValueError(f"{path}: contains NaN or -999 fill values")
    full = pd.date_range(df.index[0], df.index[-1], freq="D")
    if len(full) != len(df):
        raise ValueError(f"{path}: {len(full) - len(df)} missing days")
    return df


def synthetic_weather(first: int, last: int, seed: int = 42) -> pd.DataFrame:
    """SYNTHETIC daily weather (rough SW Kansas climate: ~480 mm/yr rain peaking in June,
    hot windy summers). Year-to-year rainfall varies ±25 % to mimic wet/dry years."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(f"{first}-01-01", f"{last}-12-31", freq="D")
    doy = dates.dayofyear.to_numpy()
    season = np.sin(2 * np.pi * (doy - 105) / 365.25)  # +1 mid-July, -1 mid-January
    n = len(dates)

    tmax = 20.5 + 13.5 * season + rng.normal(0, 4.0, n)
    tmin = tmax - 15.0 + rng.normal(0, 2.0, n)
    # monthly rain: Jan ~12 mm, Jun ~80 mm -> wet-day probability and mean amount
    wet_p = 0.10 + 0.11 * (season + 1) / 2
    mean_amt = 5.0 + 6.0 * (season + 1) / 2
    year_factor = dict(
        zip(range(first, last + 1), rng.lognormal(0, 0.25, last - first + 1), strict=True)
    )
    yf = np.array([year_factor[y] for y in dates.year])
    wet = rng.random(n) < wet_p * yf
    rain = np.where(wet, rng.gamma(0.8, mean_amt / 0.8, n) * np.sqrt(yf), 0.0)

    ra_like = 20.0 + 10.0 * season  # MJ/m²/day, crude seasonal envelope of clear-sky Rs
    rs = ra_like * np.where(wet, 0.45, 0.85) * rng.uniform(0.9, 1.05, n)
    rh = np.clip(55 - 8 * season + np.where(wet, 20, 0) + rng.normal(0, 6, n), 15, 100)
    wind = np.clip(rng.gamma(6.0, 4.5 / 6.0, n), 0.5, None)
    return pd.DataFrame(
        {
            "T2M_MAX": tmax,
            "T2M_MIN": tmin,
            "RH2M": rh,
            "WS2M": wind,
            "ALLSKY_SFC_SW_DWN": rs,
            "PRECTOTCORR": rain,
        },
        index=pd.DatetimeIndex(dates, name="DATE"),
    )


def get_weather(first: int, last: int, path: Path = POWER_DAILY) -> tuple[pd.DataFrame, bool]:
    """Return (weather for [first, last], is_synthetic)."""
    if path.exists():
        df = load_power_daily(path)
        df = df.loc[f"{first}-01-01" : f"{last}-12-31"]
        years = set(df.index.year)
        if years != set(range(first, last + 1)):
            raise ValueError(f"{path}: years {sorted(years)} do not cover {first}-{last}")
        return df, False
    return synthetic_weather(first, last), True


def drop_feb29(df: pd.DataFrame) -> pd.DataFrame:
    """Drop 29 Feb so every year has 365 days (the rotation model works on 365-day years)."""
    idx = df.index
    return df[~((idx.month == 2) & (idx.day == 29))]
