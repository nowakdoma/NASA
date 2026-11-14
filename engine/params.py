"""Engine-owned model parameters that are NOT in contracts/crops.csv.

EVERY value here is a PLACEHOLDER (ballpark for irrigated SW Kansas, ~2020-2024) unless the
comment says otherwise. They are good enough to rank rotations roughly, not to plan a farm.
Each strategy exported by the engine lists these as data gaps. Replace with K-State
Farm Management Guides / USDA NASS values when time allows, and keep the `SOURCES` note in sync.
"""

from __future__ import annotations

from dataclasses import dataclass

PLACEHOLDER = True

SOURCES = {
    "crop_econ": (
        "PLACEHOLDER ballpark from K-State Farm Management Guides (SW Kansas, irrigated) and "
        "USDA NASS Kansas prices received ~2020-2024; not calibrated."
    ),
    "ky": "FAO Irrigation & Drainage Paper 33 (Doorenbos & Kassam 1979), seasonal Ky.",
    "c_factor": "PLACEHOLDER annual RUSLE C, reduced tillage, from USDA AH-703 ranges.",
    "labour": "PLACEHOLDER machine + management hours per ha, rough extension-budget values.",
    "site": "Garden City, KS (lat 37.97 N, ~880 m a.s.l.).",
}

# --- site -----------------------------------------------------------------------------------
LAT_DEG = 37.97
ELEVATION_M = 880.0

# --- water balance --------------------------------------------------------------------------
P_DEPLETION = 0.5  # FAO-56 p: stress starts when depletion > p * TAW
IRRIGATION_TRIGGER = 0.4  # irrigate when depletion > trigger * TAW (pivot can't catch up later)
PIVOT_CAPACITY_MM_DAY = 6.4  # ~600 gpm on 125 ac center pivot (PLACEHOLDER)
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
PUMPING_COST_USD_HA_MM = 0.95  # ~$10 per acre-inch (natural gas / electric) (PLACEHOLDER)
LABOUR_HOURS_FULL_SCALE = 12.0  # hours/ha/yr that maps to labour_index = 1
IRRIGATION_LABOUR_H_PER_100MM = 0.4  # pivot checks, repairs, scheduling


@dataclass(frozen=True)
class CropParams:
    plant_doy: int  # day of year of planting / green-up; fall-sown crops use the prior fall
    fall_sown: bool
    ky: float  # FAO-33 seasonal yield response factor
    ym_t_ha: float  # attainable yield without water stress (irrigated), t/ha (dry matter for hay)
    price_usd_t: float
    var_cost_usd_ha: float  # variable costs excl. pumping (alfalfa incl. amortised stand)
    other_revenue_usd_ha: float  # e.g. grazing value
    c_factor: float  # RUSLE annual cover-management factor for the crop year
    disturbance: float  # 0..1 soil disturbance (tillage passes, STIR-like) for SCI FO term
    labour_h_ha: float
    cycles: int = 1  # repeat the crops.csv Kc stages (alfalfa: one cycle per cutting)


CROPS: dict[str, CropParams] = {
    # code            doy  fall   ky    ym     price  cost  other  C     dist  lab
    "corn": CropParams(120, False, 1.25, 12.9, 180.0, 1150.0, 0.0, 0.20, 0.35, 6.0),
    "sorghum": CropParams(145, False, 0.90, 8.0, 170.0, 600.0, 0.0, 0.22, 0.35, 3.5),
    "winter_wheat": CropParams(275, True, 1.05, 4.7, 210.0, 450.0, 0.0, 0.15, 0.40, 2.5),
    "soybeans": CropParams(135, False, 0.85, 4.0, 380.0, 650.0, 0.0, 0.35, 0.40, 3.5),
    "alfalfa": CropParams(85, False, 1.10, 12.5, 190.0, 1400.0, 0.0, 0.02, 0.05, 10.0, cycles=3),
    "cotton": CropParams(135, False, 0.85, 1.3, 1500.0, 850.0, 0.0, 0.40, 0.55, 6.0),
    "sunflower": CropParams(150, False, 0.95, 2.5, 450.0, 500.0, 0.0, 0.30, 0.40, 3.5),
    "rye_cover": CropParams(285, True, 0.0, 0.0, 0.0, 90.0, 0.0, 0.10, 0.20, 1.5),
    "fallow": CropParams(1, False, 0.0, 0.0, 0.0, 70.0, 0.0, 0.45, 0.30, 1.0),
    "grass_pasture": CropParams(90, False, 0.0, 0.0, 0.0, 60.0, 150.0, 0.01, 0.0, 1.5),
}


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
