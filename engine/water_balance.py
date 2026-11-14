"""FAO-56 daily water balance: ET0 (Penman-Monteith) x Kc -> crop water use, irrigation need.

Reference: Allen et al. (1998) FAO Irrigation and Drainage Paper 56.
Inputs come from NASA POWER daily (T2M_MAX, T2M_MIN, RH2M, WS2M, ALLSKY_SFC_SW_DWN, PRECTOTCORR).

Simplifications (listed as data gaps in the export):
- one soil bucket per field with TAW = SSURGO ``awc_mm`` (root depth not used);
- no runoff, no capillary rise; all rain infiltrates, excess drains (deep percolation);
- bare soil evaporation = KC_BARE * ET0, shrinking as the bucket dries;
- irrigation: center pivot refills at most PIVOT_CAPACITY_MM_DAY when depletion exceeds a
  trigger, optionally capped per year (limited irrigation / dryland).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from engine import params

SIGMA = 4.903e-9  # Stefan-Boltzmann, MJ K-4 m-2 day-1


def _sat_vp(t_c: np.ndarray) -> np.ndarray:
    """Saturation vapour pressure e°(T) [kPa], FAO-56 eq. 11."""
    return 0.6108 * np.exp(17.27 * t_c / (t_c + 237.3))


def extraterrestrial_radiation(lat_deg: float, doy: np.ndarray) -> np.ndarray:
    """Ra [MJ m-2 day-1], FAO-56 eqs. 21-25."""
    phi = np.deg2rad(lat_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    decl = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(decl), -1, 1))
    return (
        24 * 60 / np.pi * 0.0820 * dr
        * (ws * np.sin(phi) * np.sin(decl) + np.cos(phi) * np.cos(decl) * np.sin(ws))
    )  # fmt: skip


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

    Arrays are aligned daily series. ``ea`` from mean RH (eq. 19), net radiation from Rs via
    FAO-56 eqs. 37-40, soil heat flux G = 0 for daily steps.
    """
    tmax, tmin = np.asarray(tmax_c, float), np.asarray(tmin_c, float)
    tmean = (tmax + tmin) / 2
    pres = 101.3 * ((293 - 0.0065 * elevation_m) / 293) ** 5.26
    gamma = 0.665e-3 * pres
    es = (_sat_vp(tmax) + _sat_vp(tmin)) / 2
    ea = np.asarray(rh_mean_pct, float) / 100 * es
    delta = 4098 * _sat_vp(tmean) / (tmean + 237.3) ** 2

    rs = np.asarray(rs_mj_m2_day, float)
    ra = extraterrestrial_radiation(lat_deg, np.asarray(doy))
    rso = (0.75 + 2e-5 * elevation_m) * ra
    rel = np.clip(np.divide(rs, rso, out=np.ones_like(rs), where=rso > 0), 0.25, 1.0)
    rnl = (
        SIGMA * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2
        * (0.34 - 0.14 * np.sqrt(np.maximum(ea, 0))) * (1.35 * rel - 0.35)
    )  # fmt: skip
    rn = 0.77 * rs - rnl
    u2 = np.asarray(wind_2m_ms, float)
    num = 0.408 * delta * rn + gamma * 900 / (tmean + 273) * u2 * (es - ea)
    return np.maximum(num / (delta + gamma * (1 + 0.34 * u2)), 0.0)


def et0_from_weather(weather: pd.DataFrame) -> np.ndarray:
    """ET0 [mm/day] for a POWER-format daily DataFrame (see engine.weather)."""
    return et0_fao56_pm(
        weather["T2M_MAX"].to_numpy(),
        weather["T2M_MIN"].to_numpy(),
        weather["RH2M"].to_numpy(),
        weather["WS2M"].to_numpy(),
        weather["ALLSKY_SFC_SW_DWN"].to_numpy(),
        params.ELEVATION_M,
        params.LAT_DEG,
        weather.index.dayofyear.to_numpy(),
    )


def kc_stages(crop_code: str, traits: pd.DataFrame, cycles: int = 1) -> np.ndarray:
    """Kc for each day of the season (FAO-56 Fig. 25, linear between stages), length =
    cycles x (L_ini + L_dev + L_mid + L_late). Empty for crops without a season (fallow)."""
    t = traits.loc[crop_code]
    li, ld, lm, ll = (int(t[c]) for c in ("l_ini_d", "l_dev_d", "l_mid_d", "l_late_d"))
    if li + ld + lm + ll == 0:
        return np.zeros(0)
    one = np.concatenate(
        [
            np.full(li, t.kc_ini),
            np.linspace(t.kc_ini, t.kc_mid, ld, endpoint=False),
            np.full(lm, t.kc_mid),
            np.linspace(t.kc_mid, t.kc_end, ll),
        ]
    )
    return np.tile(one, cycles)


def kc_curve(crop_code: str, planting_doy: int, traits: pd.DataFrame, cycles: int = 1):
    """Daily single crop coefficient over one 365-day year, wrapping past 31 Dec.

    Returns an array of length 365 with 0 outside the season (caller handles bare-soil
    evaporation). Stage lengths and Kc values come from contracts/crops.csv.
    """
    season = kc_stages(crop_code, traits, cycles)[:365]
    out = np.zeros(365)
    idx = (planting_doy - 1 + np.arange(len(season))) % 365
    out[idx] = season
    return out


@dataclass
class Timeline:
    """Daily crop calendar of a cyclic rotation of length L years (365 * L days)."""

    kc: np.ndarray  # crop coefficient, 0 when no crop
    slot: np.ndarray  # rotation position 0..L-1 of the crop on this day, -1 when bare
    irrigable: np.ndarray  # bool: crop that a farmer would irrigate is in the field


def rotation_timeline(rotation: list[str] | tuple[str, ...], traits: pd.DataFrame) -> Timeline:
    """Lay the rotation out on a cyclic calendar. Fall-sown crops for year k start in the
    autumn of year k-1 (wrapping to the end of the cycle for k = 0)."""
    n_years = len(rotation)
    n = 365 * n_years
    kc = np.zeros(n)
    slot = np.full(n, -1)
    for k, crop in enumerate(rotation):
        cp = params.CROPS[crop]
        season = kc_stages(crop, traits, cp.cycles)
        if season.size == 0:
            continue
        start = 365 * (k - 1 if cp.fall_sown else k) + cp.plant_doy - 1
        idx = (start + np.arange(min(season.size, n))) % n
        take = season[: idx.size] >= kc[idx]  # overlapping seasons: higher Kc wins
        kc[idx[take]] = season[: idx.size][take]
        slot[idx[take]] = k
    crops = np.array(rotation)
    irrigable = (slot >= 0) & ~np.isin(crops[np.maximum(slot, 0)], list(params.NO_IRRIGATION_CROPS))
    return Timeline(kc=kc, slot=slot, irrigable=irrigable)


@dataclass
class WaterResult:
    irrigation_mm: np.ndarray  # per rotation year (L,)
    deep_perc_mm: np.ndarray  # per rotation year (L,)
    etc_mm: np.ndarray  # potential crop ET per rotation slot (L,)
    eta_mm: np.ndarray  # actual crop ET per rotation slot (L,)
    stress_days: np.ndarray  # days with Ks < 1 per rotation slot (L,)

    def yield_ratio(self, ky: np.ndarray) -> np.ndarray:
        """FAO-33: 1 - Ya/Ym = Ky (1 - ETa/ETc); clipped to [0, 1]; 1 where no crop."""
        rel = np.divide(self.eta_mm, self.etc_mm, out=np.ones(len(ky)), where=self.etc_mm > 0)
        return np.clip(1 - ky * (1 - rel), 0.0, 1.0)


def simulate(
    timeline: Timeline,
    et0: np.ndarray,
    precip: np.ndarray,
    awc_mm: float,
    irrigation_cap_mm: float | None,
    initial_depletion: float = 0.5,
) -> WaterResult:
    """Daily root-zone bucket (FAO-56 ch. 8) over one rotation cycle.

    ``et0``/``precip`` are aligned with the timeline (365 * L days). Irrigation refills
    up to the pivot capacity when depletion exceeds IRRIGATION_TRIGGER * TAW, limited to
    ``irrigation_cap_mm`` per calendar year (None = unlimited, 0 = dryland).
    """
    n_years = len(timeline.kc) // 365
    taw = float(awc_mm)
    raw = params.P_DEPLETION * taw
    trigger = params.IRRIGATION_TRIGGER * taw
    cap = np.inf if irrigation_cap_mm is None else float(irrigation_cap_mm)

    irr = np.zeros(n_years)
    dp = np.zeros(n_years)
    etc_s = np.zeros(n_years)
    eta_s = np.zeros(n_years)
    stress = np.zeros(n_years)
    dr = initial_depletion * taw
    kc_l, slot_l, irr_l = timeline.kc.tolist(), timeline.slot.tolist(), timeline.irrigable.tolist()
    et0_l, p_l = et0.tolist(), precip.tolist()
    for d in range(len(kc_l)):
        y = d // 365
        s = slot_l[d]
        if irr_l[d] and dr > trigger and irr[y] < cap:
            amt = min(dr, params.PIVOT_CAPACITY_MM_DAY, cap - irr[y])
            irr[y] += amt
            dr -= amt
        if s >= 0:
            etc = kc_l[d] * et0_l[d]
            ks = 1.0 if dr <= raw else max(0.0, (taw - dr) / (taw - raw))
            eta = ks * etc
            etc_s[s] += etc
            eta_s[s] += eta
            if ks < 1.0:
                stress[s] += 1
        else:
            eta = params.KC_BARE * et0_l[d] * (1 - dr / taw) ** 2
        dr = dr - p_l[d] + eta
        if dr < 0:
            dp[y] -= dr
            dr = 0.0
        dr = min(dr, taw)
    return WaterResult(irr, dp, etc_s, eta_s, stress)
