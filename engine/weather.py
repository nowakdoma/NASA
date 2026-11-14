"""Daily weather input for the engine.

Real input (written by ``python -m pipeline power``, person 2): ``data/interim/weather_daily.csv``
    NASA POWER daily for the region centroid, 1995..2025, community "AG". Columns used:
    date, t2m_max_c, t2m_min_c [°C], rh2m_pct [%], ws2m_ms [m/s at 2 m],
    sw_down_mj_m2_d [MJ/m²/day], precip_mm_d [mm/day]. POWER's -999 days are empty cells.
    Short gaps (<= MAX_GAP_DAYS) are interpolated here; longer gaps are an error.
    Internally the engine uses the POWER parameter names (T2M_MAX, ..., PRECTOTCORR).

Fallback: :func:`synthetic_weather` — a seeded stochastic generator with a rough Garden City,
KS climatology. It exists ONLY so the engine can run before real data arrives. Output built
on it must be flagged ``mock: true`` and list a data gap.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from engine import REPO_ROOT

WEATHER_DAILY = REPO_ROOT / "data" / "interim" / "weather_daily.csv"
# pipeline interim column -> internal POWER parameter name
PIPELINE_COLUMNS = {
    "t2m_max_c": "T2M_MAX",
    "t2m_min_c": "T2M_MIN",
    "rh2m_pct": "RH2M",
    "ws2m_ms": "WS2M",
    "sw_down_mj_m2_d": "ALLSKY_SFC_SW_DWN",
    "precip_mm_d": "PRECTOTCORR",
}
COLUMNS = list(PIPELINE_COLUMNS.values())
MAX_GAP_DAYS = 3


def load_weather_daily(path: Path = WEATHER_DAILY) -> pd.DataFrame:
    """Read the pipeline CSV, fill short gaps, return POWER-named columns indexed by date.

    ``df.attrs["filled_cells"]`` counts interpolated values (reported as a data gap).
    Raises ``ValueError`` on missing columns or gaps longer than MAX_GAP_DAYS.
    """
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    missing = [c for c in PIPELINE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    df = df[list(PIPELINE_COLUMNS)].rename(columns=PIPELINE_COLUMNS).astype(float)
    df = df[~df.index.duplicated()]
    df = df.reindex(pd.date_range(df.index[0], df.index[-1], freq="D", name="DATE"))
    df = df.mask(df <= -999)
    gaps = int(df.isna().sum().sum())
    df = df.interpolate(limit=MAX_GAP_DAYS, limit_area="inside")
    if df.isna().any().any():
        bad = df.isna().sum()
        raise ValueError(f"{path}: gaps longer than {MAX_GAP_DAYS} days: {bad[bad > 0].to_dict()}")
    df.attrs["filled_cells"] = gaps
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


def get_weather(first: int, last: int, path: Path = WEATHER_DAILY) -> tuple[pd.DataFrame, bool]:
    """Return (weather for [first, last], is_synthetic)."""
    if path.exists():
        df = load_weather_daily(path)
        df = df.loc[f"{first}-01-01" : f"{last}-12-31"]
        counts = df.groupby(df.index.year).size()
        short = {int(y): int(n) for y, n in counts.items() if n < 365}
        missing = sorted(set(range(first, last + 1)) - set(counts.index))
        if missing or short:
            raise ValueError(
                f"{path}: incomplete weather for {first}-{last}: missing years {missing}, "
                f"short years (days) {short}"
            )
        return df, False
    return synthetic_weather(first, last), True


def drop_feb29(df: pd.DataFrame) -> pd.DataFrame:
    """Drop 29 Feb so every year has 365 days (the rotation model works on 365-day years)."""
    idx = df.index
    return df[~((idx.month == 2) & (idx.day == 29))]
