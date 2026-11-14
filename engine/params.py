"""Engine-owned model parameters that are NOT in contracts/crops.csv.

Economics come from the K-State 2027 Farm Management Guides for (South)western Kansas
(AgManager.info, dated 2026-11-01), one edition for every crop so prices and costs are
consistent. Full citations and the derivations: reports/SW Kansas crop budgets.md.
Comment tags: [S] sourced, [D] derived from sources, [R] judgement = PLACEHOLDER.
Exported strategies list the remaining gaps (fixed prices, unsourced well capacity, ...).
"""

from __future__ import annotations

from dataclasses import dataclass

PLACEHOLDER = True  # some values are still [R]; see tags below

SOURCES = {
    "crop_econ": (
        "K-State 2027 Farm Management Guides, SW/Western Kansas (AgManager.info, 2026-11-01): "
        "middle-yield budgets, direct costs excluding all irrigation items; dryland costs from "
        "the W-C-F / W-S-F / W-SB-F / W-CT-F / W-SF-F budgets (wheat: 2026 edition)."
    ),
    "prices": (
        "K-State 2027 planning prices; 20-60 % above USDA NASS Kansas 2025 preliminary prices "
        "received (wheat $6.98/bu vs $4.60). Fixed, not sampled."
    ),
    "ky": "FAO-33 (Doorenbos & Kassam 1979; pre-2020) as restated in FAO-66, seasonal Ky.",
    "c_factor": "PLACEHOLDER annual RUSLE C, reduced tillage, from USDA AH-703 ranges.",
    "labour": (
        "Field-operation hours from K-State 2027 budgets (excl. custom work); alfalfa adds an "
        "unsourced per-cutting management term; rye/fallow/pasture hours are judgement."
    ),
    "irrigation": (
        "K-State 2027 budgets: natural gas, 300 ft well, $3.27/ac-in energy + $0.36 repairs + "
        "~0.04 h/ac-in labour. Well capacity: no Finney data (L908 sizing formula, judgement)."
    ),
    "cover_fallow": (
        "No K-State budget: rye = seed (K-State MF3504 rate, Ohio State price) + Kansas Custom "
        "Rates 2026 drilling + glyphosate termination; fallow = 2022 K-State Input Cost Survey "
        "SW herbicide + 3-4 custom spray passes."
    ),
    "site": "Garden City, KS (lat 37.97 N, ~880 m a.s.l.).",
}

# --- site -----------------------------------------------------------------------------------
LAT_DEG = 37.97
ELEVATION_M = 880.0

# --- water balance --------------------------------------------------------------------------
P_DEPLETION = 0.5  # FAO-56 p: stress starts when depletion > p * TAW
IRRIGATION_TRIGGER = 0.4  # irrigate when depletion > trigger * TAW (pivot can't catch up later)
PIVOT_CAPACITY_MM_DAY = 5.4  # [R] ~500 gpm on 125 ac (p10 3.3, p90 8.7); no Finney data
KC_BARE = 0.30  # bare/residue soil evaporation coefficient when wet (PLACEHOLDER)
NO_IRRIGATION_CROPS = frozenset({"fallow", "rye_cover", "grass_pasture"})

# Irrigation levels a strategy can use: seasonal cap in mm/yr (None = no cap, 0 = dryland).
IRRIGATION_LEVELS: dict[str, float | None] = {"full": None, "limited": 150.0, "dryland": 0.0}

# --- erosion --------------------------------------------------------------------------------
# Long-term mean R for Finney County, SI units MJ mm / (ha h yr). AH-703 isoerodent ~75
# US units x 17.02. PLACEHOLDER: yearly R is scaled by a daily-rain erosivity proxy.
R_MEAN_SI = 1280.0
EROSIVE_RAIN_MM = 12.7  # Richardson-type threshold
KFACT_US_TO_SI = 0.1317  # t ac h/(100 ac ft tonf in)  ->  t ha h/(ha MJ mm)
SLOPE_LENGTH_M = 100.0  # assumed; pivots are flat and long (PLACEHOLDER)
SOIL_LOSS_TOLERANCE_T_HA = 11.2  # NRCS T = 5 t/ac (upper bound) for SCI ER sub-factor

# --- economics ------------------------------------------------------------------------------
# [D] all-in variable irrigation cost: $4.52/ac-in = energy 0.318 + repairs 0.035 + labour
# 0.087 USD/mm/ha (natural gas, 300 ft well). Electric ~0.38-0.62, shallower wells cheaper.
PUMPING_COST_USD_HA_MM = 0.44
LABOUR_HOURS_FULL_SCALE = 6.0  # [R] h/ha/yr that maps to labour_index = 1 (~ irrigated alfalfa)
IRRIGATION_LABOUR_H_PER_100MM = 0.39  # [D] 0.04 h/ac-in (K-State 2027 budgets)


@dataclass(frozen=True)
class CropParams:
    plant_doy: int  # day of year of planting / green-up; fall-sown crops use the prior fall
    fall_sown: bool
    ky: float  # FAO-33 seasonal yield response factor
    ym_t_ha: float  # budget middle yield on a pivot, t/ha (hay: t/ha as sold); FAO-33 Ym
    price_usd_t: float
    var_cost_usd_ha: float  # irrigated direct costs EXCLUDING all irrigation items
    dry_var_cost_usd_ha: float  # dryland direct costs (used when irrigation level = dryland)
    other_revenue_usd_ha: float  # e.g. cottonseed, grazing value
    c_factor: float  # RUSLE annual cover-management factor for the crop year
    disturbance: float  # 0..1 soil disturbance (tillage passes, STIR-like) for SCI FO term
    labour_h_ha: float  # field operations (irrigation labour added from water applied)
    dry_labour_h_ha: float
    cycles: int = 1  # repeat the crops.csv Kc stages (alfalfa: one cycle per cutting)


# Values per crop: see reports/SW Kansas crop budgets.md ("Recommended parameter set").
CROPS: dict[str, CropParams] = {
    # [S] ym/price, [D] costs and hours from K-State 2027 SW KS budgets
    "corn": CropParams(
        120, False, ky=1.25, ym_t_ha=14.1, price_usd_t=192.0,
        var_cost_usd_ha=1268.0, dry_var_cost_usd_ha=694.0, other_revenue_usd_ha=0.0,
        c_factor=0.20, disturbance=0.35, labour_h_ha=1.16, dry_labour_h_ha=0.91,
    ),
    "sorghum": CropParams(
        145, False, ky=0.90, ym_t_ha=10.0, price_usd_t=180.0,
        var_cost_usd_ha=863.0, dry_var_cost_usd_ha=558.0, other_revenue_usd_ha=0.0,
        c_factor=0.22, disturbance=0.35, labour_h_ha=0.84, dry_labour_h_ha=0.91,
    ),
    # price from the limited-irrigation W KS budget ($6.98/bu) — flagged, far above NASS 2025p;
    # dryland cost from the 2026 W-F budget (no 2027 SW dryland wheat budget)
    "winter_wheat": CropParams(
        275, True, ky=1.00, ym_t_ha=4.7, price_usd_t=257.0,
        var_cost_usd_ha=635.0, dry_var_cost_usd_ha=485.0, other_revenue_usd_ha=0.0,
        c_factor=0.15, disturbance=0.40, labour_h_ha=1.21, dry_labour_h_ha=1.21,
    ),
    "soybeans": CropParams(
        135, False, ky=0.85, ym_t_ha=4.4, price_usd_t=442.0,
        var_cost_usd_ha=531.0, dry_var_cost_usd_ha=415.0, other_revenue_usd_ha=0.0,
        c_factor=0.35, disturbance=0.40, labour_h_ha=0.82, dry_labour_h_ha=0.74,
    ),
    # cost 1134 [D] + 69 [R] stand establishment over a 3-yr stand; labour 0.59 [D] + 3.0 [R]
    # management of 4 cuttings; dryland: no usable upland budget -> irrigated costs minus
    # harvest share [R]. crops.csv cycles are 75 d, so 3 cycles fit the Apr-Oct season.
    "alfalfa": CropParams(
        85, False, ky=1.10, ym_t_ha=11.2, price_usd_t=217.0,
        var_cost_usd_ha=1203.0, dry_var_cost_usd_ha=680.0, other_revenue_usd_ha=0.0,
        c_factor=0.02, disturbance=0.05, labour_h_ha=3.6, dry_labour_h_ha=2.0, cycles=3,
    ),
    # other revenue: cottonseed $243/ac [S]
    "cotton": CropParams(
        135, False, ky=0.85, ym_t_ha=1.68, price_usd_t=1698.0,
        var_cost_usd_ha=1988.0, dry_var_cost_usd_ha=1428.0, other_revenue_usd_ha=600.0,
        c_factor=0.40, disturbance=0.55, labour_h_ha=1.63, dry_labour_h_ha=1.75,
    ),
    "sunflower": CropParams(
        150, False, ky=0.95, ym_t_ha=2.69, price_usd_t=430.0,
        var_cost_usd_ha=769.0, dry_var_cost_usd_ha=560.0, other_revenue_usd_ha=0.0,
        c_factor=0.30, disturbance=0.40, labour_h_ha=1.24, dry_labour_h_ha=0.72,
    ),
    # [D/R] seed + custom drilling + glyphosate termination (128-146 USD/ha)
    "rye_cover": CropParams(
        285, True, ky=0.0, ym_t_ha=0.0, price_usd_t=0.0,
        var_cost_usd_ha=137.0, dry_var_cost_usd_ha=137.0, other_revenue_usd_ha=0.0,
        c_factor=0.10, disturbance=0.20, labour_h_ha=0.3, dry_labour_h_ha=0.3,
    ),
    # [D/R] SW herbicide $46/ac + 3-4 spray passes (170-198 USD/ha)
    "fallow": CropParams(
        1, False, ky=0.0, ym_t_ha=0.0, price_usd_t=0.0,
        var_cost_usd_ha=185.0, dry_var_cost_usd_ha=185.0, other_revenue_usd_ha=0.0,
        c_factor=0.45, disturbance=0.30, labour_h_ha=0.6, dry_labour_h_ha=0.6,
    ),
    # [R] no budget researched
    "grass_pasture": CropParams(
        90, False, ky=0.0, ym_t_ha=0.0, price_usd_t=0.0,
        var_cost_usd_ha=60.0, dry_var_cost_usd_ha=60.0, other_revenue_usd_ha=150.0,
        c_factor=0.01, disturbance=0.0, labour_h_ha=0.5, dry_labour_h_ha=0.5,
    ),
}  # fmt: skip


@dataclass(frozen=True)
class CatalogueEntry:
    id: str
    name: str
    rotation: tuple[str, ...]
    irrigation: str  # key of IRRIGATION_LEVELS
    description: str


# Rotations plausible in SW Kansas. Alternatives for each field are picked from here.
CATALOGUE: tuple[CatalogueEntry, ...] = (
    CatalogueEntry(
        "wsf_limited",
        "Wheat–sorghum–fallow (limited irrigation)",
        ("winter_wheat", "sorghum", "fallow"),
        "limited",
        "Lower-water rotation common in western Kansas; fallow year stores soil water.",
    ),
    CatalogueEntry(
        "wsf_dryland",
        "Wheat–sorghum–fallow (dryland)",
        ("winter_wheat", "sorghum", "fallow"),
        "dryland",
        "No irrigation; relies on fallow-stored soil water and rainfall.",
    ),
    CatalogueEntry(
        "corn_soy",
        "Corn–soybean (full irrigation)",
        ("corn", "soybeans"),
        "full",
        "Adds a nitrogen-fixing legume; breaks corn pest cycles.",
    ),
    CatalogueEntry(
        "corn_wheat_sorghum",
        "Corn–wheat–sorghum (full irrigation)",
        ("corn", "winter_wheat", "sorghum"),
        "full",
        "Three crops with different water peaks; spreads workload over the year.",
    ),
    CatalogueEntry(
        "sorghum_wheat_cover",
        "Sorghum–wheat–cover crop (limited irrigation)",
        ("sorghum", "winter_wheat", "rye_cover"),
        "limited",
        "Cover crop replaces fallow to protect soil; uses some stored water.",
    ),
    CatalogueEntry(
        "alfalfa_corn",
        "Alfalfa (3 yr)–corn (2 yr) (full irrigation)",
        ("alfalfa", "alfalfa", "alfalfa", "corn", "corn"),
        "full",
        "Perennial forage builds soil; needs hay market and more labour.",
    ),
)
