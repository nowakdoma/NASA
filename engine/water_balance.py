"""FAO-56 daily water balance: ET0 (Penman-Monteith) x Kc -> crop water use, irrigation need.

Reference: Allen et al. (1998) FAO Irrigation and Drainage Paper 56.
Inputs come from NASA POWER daily (T2M_MAX, T2M_MIN, RH2M, WS2M, ALLSKY_SFC_SW_DWN, PRECTOTCORR).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def et0_fao56_pm(
    tmax_c: np.ndarray,
    tmin_c: np.ndarray,
    rh_mean_pct: np.ndarray,
    wind_2m_ms: np.ndarray,
    rs_mj_m2_day: np.ndarray,
    elevation_m: float,
    lat_deg: float,
    doy: np.ndarray,
) -> np.ndarray:
    """Daily reference evapotranspiration ET0 [mm/day], FAO-56 eq. 6.

    Arrays are aligned daily series. Net radiation from Rs via FAO-56 eqs. 37-40.
    """
    raise NotImplementedError


def kc_curve(crop_code: str, planting_doy: int, traits: pd.DataFrame) -> np.ndarray:
    """Daily single crop coefficient (FAO-56 Fig. 25, linear interpolation between stages).

    Returns an array of length 365 with 0 outside the season (caller handles fallow Ke).
    Stage lengths and Kc values come from contracts/crops.csv.
    """
    raise NotImplementedError


def crop_water_use(
    et0_mm: np.ndarray,
    kc: np.ndarray,
    precip_mm: np.ndarray,
    awc_mm: float,
    p_depletion: float = 0.5,
) -> dict[str, float]:
    """Run a daily root-zone bucket model for one season.

    Returns ``{"etc_mm", "irrigation_mm", "deep_perc_mm", "stress_days"}`` where irrigation
    refills the bucket to field capacity when depletion exceeds ``p_depletion * awc_mm``.
    """
    raise NotImplementedError
