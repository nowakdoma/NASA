"""Evaluate rotation strategies for a field over the weather record -> p10/p50/p90 metrics.

For a rotation of L years and weather years Y_1..Y_n, each start year s gives one sample:
the rotation is simulated continuously over weather years s, s+1, ..., s+L-1 (wrapping to the
start of the record), and every metric is averaged per year over the cycle. The p10/p50/p90 of
the n samples are the interval exported to strategies.json.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

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
    filled_cells: int = 0  # interpolated weather values (reported as a data gap)

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
            filled_cells=int(weather.attrs.get("filled_cells", 0)),
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


def data_gaps(
    rotation: list[str],
    irrigation: str,
    weather_synthetic: bool,
    filled_cells: int = 0,
    soil: dict | None = None,
) -> list[str]:
    gaps = []
    if filled_cells:
        gaps.append(f"{filled_cells} missing NASA POWER daily values were linearly "
                    "interpolated.")  # fmt: skip
    if soil is not None and soil.get("awc_mm", 0) < params.MIN_AWC_MM:
        gaps.append(f"SSURGO available water capacity missing or below "
                    f"{params.MIN_AWC_MM:.0f} mm; {params.MIN_AWC_MM:.0f} mm assumed.")  # fmt: skip
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
    proxied = [c for c in dict.fromkeys(rotation) if c in params.PROXIED_CROPS]
    if proxied:
        detail = "; ".join(f"{c} on the {params.PROXIED_CROPS[c]} budget" for c in proxied)
        gaps.append(
            f"Budget proxy: {detail}. No K-State SW Kansas budget exists for these crops, "
            "so their yield, price and costs are the proxy crop's. Double-cropped years also "
            "count only the summer crop, so their income and water use are understated."
        )  # fmt: skip
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
    proxied = [c for c in dict.fromkeys(rotation) if c in params.PROXIED_CROPS]
    if proxied:
        checks.append(
            f"Actual price and yield for {', '.join(proxied)}: the model uses the "
            f"{params.PROXIED_CROPS[proxied[0]]} budget as a proxy."
        )  # fmt: skip
    if "rye_cover" in rotation:
        checks.append("Cover crop seed cost and termination rules for crop insurance.")
    return checks


def derive_soil_health_traits(rotation: list[str], traits: pd.DataFrame) -> dict[str, Any]:
    """Calculate soil health and rotational break traits."""
    n_fixing_years = sum(
        1 for c in rotation if c in traits.index and bool(traits.loc[c, "n_fixing"])
    )
    families = {
        str(traits.loc[c, "family"]).strip()
        for c in rotation
        if c in traits.index and str(traits.loc[c, "family"]).strip().lower() not in ("none", "")
    }
    pest_break = len(families) >= 2
    forage = any(
        c in {"alfalfa", "triticale", "other_hay", "rye_cover"}
        or (
            c in traits.index
            and (
                "hay" in str(traits.loc[c, "name"]).lower()
                or "silage" in str(traits.loc[c, "name"]).lower()
            )
        )
        for c in rotation
    )
    return {
        "n_fixing_years": n_fixing_years,
        "pest_break": pest_break,
        "forage": forage,
    }


def why_considered(
    rotation: list[str],
    level: str,
    is_current: bool,
    props: dict,
    traits: pd.DataFrame,
) -> str:
    """Generate a field-specific rationale sentence tied to soil, history, and water."""
    soil = props["soil"]
    texture = soil.get("texture", "loam")
    awc = soil.get("awc_mm", 150)

    if is_current:
        crop_names = _crop_names(rotation, traits)
        return (
            f"Observed baseline rotation ({crop_names}) on {texture} soil "
            f"under {level} irrigation from USDA CDL history."
        )

    rot_set = set(rotation)
    if "rye_cover" in rot_set:
        return (
            f"Replaces winter bare-soil fallow with cereal rye cover to protect {texture} "
            f"topsoil from wind erosion and build soil organic matter."
        )
    if "fallow" in rot_set:
        return (
            f"Incorporates planned fallow on {texture} soil ({awc:.0f} mm AWC) to recharge "
            f"root-zone soil moisture for following dryland or limited crops."
        )
    if "sorghum" in rot_set and "corn" not in rot_set:
        return (
            f"Transitions from water-intensive corn to drought-tolerant grain sorghum to "
            f"curtail Ogallala pumping withdrawals on {texture} soil."
        )
    if "alfalfa" in rot_set:
        return (
            "Introduces deep-rooted perennial legume to fix atmospheric nitrogen and "
            "supply high-demand Southwest Kansas dairy and beef forage markets."
        )
    if "soybeans" in rot_set:
        return (
            "Introduces nitrogen-fixing soybeans to break continuous grass cereal cycles "
            "and reduce synthetic fertilizer inputs."
        )
    if level == "limited":
        return (
            f"Caps annual irrigation at {params.IRRIGATION_LEVELS['limited']:.0f} mm/yr to "
            f"extend well longevity and meet GMD3 water conservation targets."
        )
    if level == "dryland":
        return (
            f"Eliminates groundwater pumping entirely on {texture} acreage to avoid declining "
            f"well capacity and rising pumping fuel costs."
        )
    return (
        f"Diversifies the crop sequence on {texture} soil to balance seasonal machinery "
        f"workload and hedge against weather extremes."
    )


def benefits(
    rotation: list[str],
    level: str,
    is_current: bool,
    metrics: dict,
    current_metrics: dict | None,
    traits: pd.DataFrame,
    sht: dict,
    current_rotation: list[str] | None = None,
) -> list[str]:
    """Generate 2-3 concise, strictly favorable agronomic and resource benefits."""
    b: list[str] = []

    if is_current:
        b.append(
            "Established management routine with existing planter, chemical, and harvest equipment"
        )
        if sht["pest_break"]:
            b.append("Maintains multi-crop family rotation breaking single-crop disease cycles")
        else:
            b.append(
                "Direct access to established regional grain elevator and feed mill delivery bids"
            )
        b.append("Familiar baseline performance across 30-year historical weather conditions")
        return b[:3]

    cur_w = current_metrics["water_use_mm"]["p50"] if current_metrics else 0.0
    alt_w = metrics["water_use_mm"]["p50"]
    cur_er = current_metrics["erosion_t_ha"]["p50"] if current_metrics else 0.0
    alt_er = metrics["erosion_t_ha"]["p50"]
    cur_inc = current_metrics["income_usd_ha"]["p50"] if current_metrics else 0.0
    alt_inc = metrics["income_usd_ha"]["p50"]
    cur_lab = current_metrics["labour_index"]["p50"] if current_metrics else 1.0
    alt_lab = metrics["labour_index"]["p50"]
    cur_sci = current_metrics["soil_index"]["p50"] if current_metrics else 0.0
    alt_sci = metrics["soil_index"]["p50"]

    # 1. Water savings (only if strictly better)
    diff_w = cur_w - alt_w
    if diff_w >= 15.0 and cur_w > 0:
        pct_w = round((diff_w / cur_w) * 100)
        b.append(f"Cuts median irrigation pumping by {diff_w:.0f} mm/yr ({pct_w}% water savings)")
    elif alt_w == 0.0 and cur_w > 0:
        b.append("Zero groundwater pumping; eliminates irrigation withdrawals from Ogallala")

    # 2. Pest break / crop diversity
    families = {
        str(traits.loc[c, "family"]).strip()
        for c in rotation
        if c in traits.index and str(traits.loc[c, "family"]).strip().lower() not in ("none", "")
    }
    cur_families = set()
    if current_rotation:
        cur_families = {
            str(traits.loc[c, "family"]).strip()
            for c in current_rotation
            if c in traits.index
            and str(traits.loc[c, "family"]).strip().lower() not in ("none", "")
        }
    if sht["pest_break"] and len(families) > len(cur_families):
        b.append(
            "Breaks monoculture pest and weed cycles by adding broadleaf/legume to grass rotation"
        )
    elif sht["pest_break"] and len(families) >= 2:
        b.append(f"Suppresses pest and weed pressure across {len(families)} crop families")

    # 3. Nitrogen fixation (only if more N-fixing years than current)
    cur_n_fix = 0
    if current_rotation:
        cur_n_fix = sum(
            1 for c in current_rotation if c in traits.index and bool(traits.loc[c, "n_fixing"])
        )
    if sht["n_fixing_years"] > cur_n_fix:
        n_fix = sht["n_fixing_years"]
        b.append(
            f"Biological N fixation in {n_fix} of {len(rotation)} yr cuts synthetic fertilizer"
        )

    # 4. Wind erosion protection via cover crop
    if "rye_cover" in rotation and (not current_rotation or "rye_cover" not in current_rotation):
        b.append("Cereal rye cover shields topsoil from winter and spring High Plains wind erosion")

    # 5. Water erosion reduction (strictly less erosion than current rotation)
    diff_er = cur_er - alt_er
    if diff_er >= 0.05 and cur_er > 0:
        pct_er = round((diff_er / cur_er) * 100)
        if pct_er >= 10:
            b.append(
                f"~{pct_er}% less water erosion than current rotation ({alt_er:.2f} t/ha/yr p50)"
            )

    # 6. Forage production
    cur_forage = False
    if current_rotation:
        cur_forage = any(
            c in {"alfalfa", "triticale", "other_hay", "rye_cover"}
            or (
                c in traits.index
                and (
                    "hay" in str(traits.loc[c, "name"]).lower()
                    or "silage" in str(traits.loc[c, "name"]).lower()
                )
            )
            for c in current_rotation
        )
    if sht["forage"] and not cur_forage:
        b.append(
            "Produces high-demand forage or silage for Southwest Kansas cattle feedlots and dairies"
        )
    elif sht["forage"] and len(b) < 2:
        b.append("High-value forage/silage output aligned with local cattle feeding demand")

    # 7. Higher net return (only when strictly higher)
    diff_inc = alt_inc - cur_inc
    if diff_inc >= 25.0:
        b.append(f"Higher median return over variable costs (+${diff_inc:.0f}/ha/yr vs current)")

    # 8. Machinery labour reduction (only when strictly less)
    diff_lab = cur_lab - alt_lab
    if diff_lab >= 0.04 and cur_lab > 0:
        pct_lab = round((diff_lab / cur_lab) * 100)
        b.append(f"Reduces seasonal machinery and management hours by ~{pct_lab}%")

    # 9. Soil organic matter trend (only when strictly better)
    diff_sci = alt_sci - cur_sci
    if diff_sci >= 0.05:
        b.append(
            f"Improves Soil Conditioning Index ({alt_sci:+.2f} vs {cur_sci:+.2f} current), "
            "building organic matter"
        )

    # 10. Fallbacks if fewer than 2 benefits matched
    if len(b) < 2:
        if level == "dryland" and (not current_metrics or cur_w > 0):
            b.append("Eliminates electricity/fuel pumping costs and well maintenance risks")
        elif level == "limited":
            b.append("Preserves water allocation under GMD3 annual metering caps")
        elif len(rotation) >= 3:
            b.append(
                "Spreads weather and price risk across distinct seasonal planting/harvest windows"
            )
        else:
            b.append("Stable multi-year rotation adapted to Southwest Kansas climate variability")

    if len(b) < 2:
        b.append("Spreads production and market risk across diversified seasonal windows")

    return b[:3]


def field_strategies(
    props: dict,
    wy: WeatherYears,
    traits: pd.DataFrame,
    weather_synthetic: bool,
    weather_years: tuple[int, int],
    cache: dict | None = None,
) -> list[dict]:
    """The 4 strategies (current + 3 alternatives) for one field in contracts format.

    ``cache`` (shared across fields) memoises metrics by (rotation, level, soil inputs)."""
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
    cur_metrics = None
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
        soil = props["soil"]
        key = (tuple(rotation), level, soil["awc_mm"], soil["kffact"], soil["slope_pct"])
        if cache is None or key not in cache:
            metrics = summarise(evaluate(rotation, level, soil, wy, traits))
            if cache is not None:
                cache[key] = metrics
        metrics = copy.deepcopy(cache[key]) if cache is not None else metrics
        if entry is None:
            cur_metrics = metrics

        sht = derive_soil_health_traits(rotation, traits)
        why = why_considered(rotation, level, entry is None, props, traits)
        bens = benefits(
            rotation,
            level,
            entry is None,
            metrics,
            cur_metrics,
            traits,
            sht,
            current_rotation=current,
        )

        out.append(
            {
                "id": sid,
                "name": name,
                "description": desc,
                "why_considered": why,
                "benefits": bens,
                "soil_health_traits": sht,
                "is_current": entry is None,
                "rotation": rotation,
                "metrics": metrics,
                "evidence": evidence(weather_synthetic, weather_years, props["soil"]),
                "data_gaps": data_gaps(rotation, level, weather_synthetic, wy.filled_cells, soil),
                "verify_locally": verify_locally(rotation, level),
            }
        )
    return out
