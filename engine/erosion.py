"""Simplified RUSLE: A = R * K * LS * C * P  [t/ha/yr]. Water erosion only (no wind).

Wind erosion is often the bigger risk in SW Kansas on bare soil; it is listed as a data gap.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine import params


def erosivity_proxy(daily_precip_mm: np.ndarray) -> float:
    """Richardson-type daily erosivity proxy: sum of P^1.81 over days with P > 12.7 mm."""
    p = np.asarray(daily_precip_mm, float)
    return float(np.sum(np.where(p > params.EROSIVE_RAIN_MM, p, 0.0) ** 1.81))


def r_factor_by_year(precip: pd.Series) -> dict[int, float]:
    """Annual R [MJ mm / (ha h yr)] per calendar year.

    The proxy only sets the year-to-year *shape*; the level is scaled so the mean equals the
    county's long-term R (params.R_MEAN_SI, PLACEHOLDER from the AH-703 isoerodent map).
    """
    proxy = {int(y): erosivity_proxy(g.to_numpy()) for y, g in precip.groupby(precip.index.year)}
    mean = np.mean(list(proxy.values()))
    if mean <= 0:
        return {y: params.R_MEAN_SI for y in proxy}
    return {y: params.R_MEAN_SI * v / mean for y, v in proxy.items()}


def k_factor_si(kffact_us: float) -> float:
    """SSURGO kffact (US customary) -> SI t ha h / (ha MJ mm)."""
    return kffact_us * params.KFACT_US_TO_SI


def ls_factor(slope_pct: float, slope_length_m: float = params.SLOPE_LENGTH_M) -> float:
    """LS factor (McCool et al. 1987, 1989; RUSLE AH-703 eqs. 4-1..4-5) from mean slope and
    an assumed slope length (moderate rill/interrill ratio)."""
    theta = np.arctan(slope_pct / 100)
    sin_t = np.sin(theta)
    beta = (sin_t / 0.0896) / (3 * sin_t**0.8 + 0.56)
    m = beta / (1 + beta)
    l_fac = (slope_length_m / 22.13) ** m
    s_fac = 10.8 * sin_t + 0.03 if slope_pct < 9 else 16.8 * sin_t - 0.50
    return float(l_fac * s_fac)


def cover_factor(crop: str) -> float:
    """Annual C factor for a crop year (params.CROPS, PLACEHOLDER, reduced tillage)."""
    return params.CROPS[crop].c_factor


def rusle_annual(r: float, k: float, ls: float, c: float, p: float = 1.0) -> float:
    """A = R*K*LS*C*P. All factors in SI-consistent units; returns t/ha/yr."""
    return r * k * ls * c * p
