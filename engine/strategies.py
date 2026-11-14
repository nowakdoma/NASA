"""Evaluate rotation strategies for a field over the weather record -> p10/p50/p90 metrics.

For a rotation of L years and weather years Y_1..Y_n, each start year s gives one sample:
the rotation is simulated continuously over weather years s, s+1, ..., s+L-1 (wrapping to the
start of the record), and every metric is averaged per year over the cycle. The p10/p50/p90 of
the n samples are the interval exported to strategies.json.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from engine import params
from engine.erosion import cover_factor, k_factor_si, ls_factor, r_factor_by_year, rusle_annual
from engine.rotation import detect_rotation, select_alternatives
from engine.soil_index import (
    erosion_term,
    field_operations_term,
    organic_matter_term,
    soil_conditioning_index,
)
from engine.water_balance import et0_from_weather, rotation_timeline, simulate
from engine.weather import drop_feb29

METRICS = ("water_use_mm", "erosion_t_ha", "soil_index", "income_usd_ha", "labour_index")
ROUND = {
    "water_use_mm": 0,
    "erosion_t_ha": 2,
    "soil_index": 2,
    "income_usd_ha": 0,
    "labour_index": 2,
}


@dataclass
class WeatherYears:
    """Weather split into 365-day years, with ET0 and R precomputed."""

    years: list[int]
    et0: dict[int, np.ndarray]
    precip: dict[int, np.ndarray]
    r_factor: dict[int, float]

    @classmethod
    def from_daily(cls, weather: pd.DataFrame) -> WeatherYears:
        w = drop_feb29(weather)
        et0 = et0_from_weather(w)
        years = sorted(set(w.index.year))
        yr = w.index.year.to_numpy()
        return cls(
            years=years,
            et0={y: et0[yr == y] for y in years},
            precip={y: w["PRECTOTCORR"].to_numpy()[yr == y] for y in years},
            r_factor=r_factor_by_year(w["PRECTOTCORR"]),
        )


def evaluate(
    rotation: list[str] | tuple[str, ...],
    irrigation: str,
    soil: dict,
    wy: WeatherYears,
    traits: pd.DataFrame,
) -> dict[str, np.ndarray]:
    """Per-start-year samples of every metric (arrays of length n_weather_years)."""
    rotation = list(rotation)
    n_rot = len(rotation)
    tl = rotation_timeline(rotation, traits)
    cps = [params.CROPS[c] for c in rotation]
    ky = np.array([cp.ky for cp in cps])
    cap = params.IRRIGATION_LEVELS[irrigation]
    k_si = k_factor_si(soil["kffact"])
    ls = ls_factor(soil["slope_pct"])
    residue = np.array([float(traits.loc[c, "residue_t_ha"]) for c in rotation])
    disturbance = float(np.mean([cp.disturbance for cp in cps]))
    dry = irrigation == "dryland"
    labour_h = sum(cp.dry_labour_h_ha if dry else cp.labour_h_ha for cp in cps)
    var_cost = sum(cp.dry_var_cost_usd_ha if dry else cp.var_cost_usd_ha for cp in cps)

    out = {m: [] for m in METRICS}
    n_w = len(wy.years)
    for i in range(n_w):
        ys = [wy.years[(i + k) % n_w] for k in range(n_rot)]
        res = simulate(
            tl,
            np.concatenate([wy.et0[y] for y in ys]),
            np.concatenate([wy.precip[y] for y in ys]),
            soil["awc_mm"],
            cap,
        )
        ratio = res.yield_ratio(ky)
        irr_total = res.irrigation_mm.sum()

        revenue = sum(cp.ym_t_ha * r * cp.price_usd_t + cp.other_revenue_usd_ha
                      for cp, r in zip(cps, ratio, strict=True))  # fmt: skip
        costs = var_cost + irr_total * params.PUMPING_COST_USD_HA_MM
        erosion = np.mean([rusle_annual(wy.r_factor[y], k_si, ls, cover_factor(c))
                           for y, c in zip(ys, rotation, strict=True)])  # fmt: skip
        # residue scales with how well the crop grew (yield ratio; 1 for non-yield crops)
        sci = soil_conditioning_index(
            organic_matter_term(float(np.mean(residue * ratio))),
            field_operations_term(disturbance),
            erosion_term(erosion, params.SOIL_LOSS_TOLERANCE_T_HA),
        )
        hours = labour_h + irr_total / 100 * params.IRRIGATION_LABOUR_H_PER_100MM

        out["water_use_mm"].append(irr_total / n_rot)
        out["erosion_t_ha"].append(erosion)
        out["soil_index"].append(sci)
        out["income_usd_ha"].append((revenue - costs) / n_rot)
        out["labour_index"].append(min(1.0, hours / n_rot / params.LABOUR_HOURS_FULL_SCALE))
    return {m: np.asarray(v) for m, v in out.items()}


def summarise(samples: dict[str, np.ndarray]) -> dict[str, dict[str, float]]:
    """p10/p50/p90 per metric, rounded (rounding keeps p10 <= p50 <= p90)."""
    out = {}
    for m, v in samples.items():
        q = np.percentile(v, [10, 50, 90])
        q = np.round(q, ROUND[m]) + 0.0  # + 0.0 turns -0.0 into 0.0
        out[m] = {"p10": float(q[0]), "p50": float(q[1]), "p90": float(q[2])}
    return out


def _crop_names(rotation: list[str], traits: pd.DataFrame) -> str:
    return "–".join(str(traits.loc[c, "name"]).split(" (")[0] for c in rotation)


def evidence(weather_synthetic: bool, weather_years: tuple[int, int], soil: dict) -> list[dict]:
    w0, w1 = weather_years
    weather = (
        {
            "dataset": "SYNTHETIC weather (placeholder for NASA POWER)",
            "note": f"Stochastic generator {w0}-{w1}; real NASA POWER daily not yet available.",
        }
        if weather_synthetic
        else {
            "dataset": f"NASA POWER daily {w0}-{w1}",
            "note": "T2M_MAX/MIN, RH2M, WS2M, ALLSKY_SFC_SW_DWN → FAO-56 ET0; "
            "PRECTOTCORR → soil water balance and RUSLE R.",
            "url": "https://power.larc.nasa.gov/",
        }
    )
    return [
        weather,
        {
            "dataset": "USDA NASS Cropland Data Layer 2008-2025",
            "note": "Current rotation = repeating cycle in the most recent CDL years.",
        },
        {
            "dataset": "USDA NRCS SSURGO",
            "note": f"{soil.get('map_unit', soil['texture'])}: AWC {soil['awc_mm']} mm, "
            f"K {soil['kffact']}, slope {soil['slope_pct']} %.",
        },
        {
            "dataset": "FAO-56 / FAO-33 / RUSLE (AH-703)",
            "note": "Crop coefficients (contracts/crops.csv), yield response Ky, LS and C factors.",
        },
    ]


def data_gaps(rotation: list[str], irrigation: str, weather_synthetic: bool) -> list[str]:
    gaps = []
    if weather_synthetic:
        gaps.append("Weather is SYNTHETIC until NASA POWER data is loaded: intervals are "
                    "illustrative only.")  # fmt: skip
    gaps += [
        "Prices, yields and costs are fixed K-State 2027 planning budgets (SW Kansas); their "
        "prices are 20-60 % above USDA NASS 2025 Kansas prices and price risk is not in the "
        "intervals.",
        "Income is return over direct (variable) costs: land rent and pivot/well capital "
        "(~$470/ac/yr irrigated, ~$100-140 dryland, K-State 2027) are not subtracted.",
        "Well capacity (assumed ~500 gpm per quarter-section pivot) and pumping lift/fuel "
        "(natural gas, 300 ft) are not known for this field.",
        "Wind erosion not modelled (RUSLE is water-only); in SW Kansas wind erosion can "
        "dominate on bare soil.",
        "Single soil bucket, no runoff; water use is irrigation need, not metered pumping.",
        "Ogallala aquifer saturated thickness / well capacity and water-right limits "
        "(Kansas WIMAS) not considered.",
        "Soil index is a simplified, uncalibrated version of the NRCS Soil Conditioning Index.",
    ]
    if irrigation == "limited":
        gaps.append(f"Limited irrigation assumed capped at "
                    f"{params.IRRIGATION_LEVELS['limited']:.0f} mm/yr.")  # fmt: skip
    if "rye_cover" in rotation:
        gaps.append("Cover crop modelled as a winter rye season; termination timing and its "
                    "effect on the next crop's water are simplified.")  # fmt: skip
    return gaps


def verify_locally(rotation: list[str], irrigation: str) -> list[str]:
    checks = [
        "Local elevator or contract prices and basis.",
        "Herbicide carryover restrictions between the crops in this sequence.",
    ]
    if irrigation != "dryland":
        checks.insert(0, "Does your water right / well capacity support this rotation in a "
                         "dry year?")  # fmt: skip
    if "fallow" in rotation:
        checks.append("How you will keep residue on the fallow to limit wind erosion.")
    if "alfalfa" in rotation:
        checks.append("Hay buyers, storage and haul distance; stand establishment cost.")
    if "soybeans" in rotation:
        checks.append("Soybean yield on your soil (iron-deficiency chlorosis on high-pH soils).")
    if "rye_cover" in rotation:
        checks.append("Cover crop seed cost and termination rules for crop insurance.")
    return checks


def field_strategies(
    props: dict,
    wy: WeatherYears,
    traits: pd.DataFrame,
    weather_synthetic: bool,
    weather_years: tuple[int, int],
) -> list[dict]:
    """The 4 strategies (current + 3 alternatives) for one field in contracts format."""
    irrigated = bool(props.get("irrigated", True))
    current = detect_rotation(props["crop_history"])
    cur_level = "full" if irrigated else "dryland"
    options = [("current", None, current, cur_level)] + [
        (e.id if level == e.irrigation else e.id.removesuffix("_limited") + "_dryland",
         e, list(e.rotation), level)
        for e, level in select_alternatives(current, cur_level, irrigated)
    ]  # fmt: skip
    out = []
    used_ids = set()
    for sid, entry, rotation, level in options:
        while sid in used_ids:
            sid += "_b"
        used_ids.add(sid)
        if entry is None:
            name = f"Current: {_crop_names(rotation, traits)}"
            desc = "Rotation observed in CDL over recent years"
            desc += " (irrigated, full)." if irrigated else " (dryland)."
        else:
            name = entry.name if level == entry.irrigation else (
                f"{_crop_names(rotation, traits)} (dryland)")  # fmt: skip
            desc = entry.description
        metrics = summarise(evaluate(rotation, level, props["soil"], wy, traits))
        out.append(
            {
                "id": sid,
                "name": name,
                "description": desc,
                "is_current": entry is None,
                "rotation": rotation,
                "metrics": metrics,
                "evidence": evidence(weather_synthetic, weather_years, props["soil"]),
                "data_gaps": data_gaps(rotation, level, weather_synthetic),
                "verify_locally": verify_locally(rotation, level),
            }
        )
    return out
