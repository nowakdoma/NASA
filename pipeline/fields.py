"""Derive field polygons and per-year crop history from the USDA CDL rasters.

Fields are centre-pivot irrigation circles, so they can be delineated from CDL rather
than hand-drawn: take the cultivated mask, polygonize it, and keep components whose
area and circularity fit a pivot. Everything here stays in EPSG:5070 (CONUS Albers,
metres), which is why areas and perimeters are directly usable.

Crop codes are resolved through contracts/crops.csv (read-only). CDL classes that have
no row there are reported as ``None`` per year and listed in ``unknown_cdl_years`` —
the engine decides how to present them; nothing is silently mapped to a crop.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.warp import Resampling, reproject, transform_geom
from shapely.geometry import Point

from pipeline.config import INTERIM, RAW, REPO_ROOT, Config

CROPS_CSV = REPO_ROOT / "contracts" / "crops.csv"

# Delineation window: recent years, so a pivot that is fallow in one year still shows up.
DELINEATION_YEARS = (2021, 2022, 2023, 2024, 2025)
MIN_AREA_HA = 20.0
MAX_AREA_HA = 90.0
# Pivot radius in 30 m pixels: 11-16 px = 330-480 m = 34-72 ha. A full quarter-section
# pivot (400 m radius, ~50 ha) sits in the middle of this range.
PIVOT_RADII_PX = (11, 12, 13, 14, 15, 16)
# Detection ignores fallow (61) and grass/pasture (176): pivots are cropped every year.
# Including them floods the detector with pasture false positives.
DETECTION_EXCLUDE = {61, 176}
# CDL classes that are genuinely cropped (from the official county class table). Used to
# reject detections that sit on un-cropped land, and to count triticale / double-crop
# rotations as cropped even though contracts/crops.csv has no row for them.
CROPLAND_CDL = {
    1, 2, 4, 5, 6, 21, 24, 25, 26, 27, 28, 29, 30, 36, 37, 38, 39, 41, 42, 43, 44, 45, 46,
    47, 48, 49, 50, 51, 52, 53, 59, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215,
    216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232,
    233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249,
    250, 254,
}  # fmt: skip
MIN_CROPPED_SHARE = 0.75
MIN_MEDIAN_PURITY = 0.65
# Disc fill / surrounding-ring emptiness for circle detection. The surround limit cannot
# be strict: valley pivots sit next to other cropland, so a tight ring test excludes
# exactly the representative silt-loam fields. The cropped-share and purity filters
# below are what reject pasture false positives.
MIN_DISC_FILL = 0.90
MAX_SURROUND_FILL = 0.72
MIN_CIRCULARITY = 0.70  # 1.0 = perfect circle; square = 0.785
MAX_FIELDS = 60
CANDIDATE_POOL = 400  # stratified pool: enough geometry to span the county
CDL_BACKGROUND = 0


def cdl_tif(cfg: Config, year: int) -> Path:
    return RAW / "cdl" / f"CDL_{year}_{cfg.region.fips}.tif"


def read_cdl_code_map(path: Path = CROPS_CSV) -> dict[int, str]:
    """CDL class value -> crop_code, from the cdl_code column of contracts/crops.csv."""
    mapping: dict[int, str] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            raw = (row.get("cdl_code") or "").strip()
            if raw.isdigit():
                mapping[int(raw)] = row["crop_code"].strip()
    return mapping


def circularity(area: float, perimeter: float) -> float:
    """4*pi*A/P^2 — 1.0 for a circle, 0.785 for a square, small for ragged shapes."""
    if perimeter <= 0:
        return 0.0
    return float(4.0 * np.pi * area / (perimeter**2))


def majority_code(counts: np.ndarray) -> tuple[int | None, float]:
    """Most frequent non-background CDL code and its share of the field's pixels."""
    total = int(counts.sum())
    if total == 0:
        return None, 0.0
    counts = counts.copy()
    counts[CDL_BACKGROUND] = 0
    if counts.sum() == 0:
        return None, 0.0
    code = int(counts.argmax())
    return code, float(counts[code] / total)


def _crop_mask(arr: np.ndarray, codes: set[int]) -> np.ndarray:
    """Pixels carrying a CDL class that maps to a crop in contracts/crops.csv.

    Not `arr != 0`: CDL's non-zero classes (grass, shrub, water, developed) cover
    virtually the whole county, which would make every field one huge component.
    """
    return np.isin(arr, list(codes))


def _fft_convolve(img: np.ndarray, kernel: np.ndarray, img_fft=None) -> np.ndarray:
    """'same'-shaped convolution via FFT (no scipy), zero-padded to avoid wraparound."""
    shape = (img.shape[0] + kernel.shape[0] - 1, img.shape[1] + kernel.shape[1] - 1)
    shape = (1 << (shape[0] - 1).bit_length(), 1 << (shape[1] - 1).bit_length())
    f_img = img_fft if img_fft is not None else np.fft.rfft2(img, s=shape)
    f_k = np.fft.rfft2(kernel, s=shape)
    out = np.fft.irfft2(f_img * f_k, s=shape)
    oy, ox = (kernel.shape[0] - 1) // 2, (kernel.shape[1] - 1) // 2
    return out[oy : oy + img.shape[0], ox : ox + img.shape[1]]


def disc_kernel(radius_px: int) -> np.ndarray:
    y, x = np.ogrid[-radius_px : radius_px + 1, -radius_px : radius_px + 1]
    return ((x * x + y * y) <= radius_px * radius_px).astype(np.float32)


def annulus_kernel(inner_px: int, width: int = 3) -> np.ndarray:
    outer = inner_px + width
    y, x = np.ogrid[-outer : outer + 1, -outer : outer + 1]
    d2 = x * x + y * y
    return ((d2 > inner_px * inner_px) & (d2 <= outer * outer)).astype(np.float32)


def score_circles(
    mask: np.ndarray,
    *,
    radii_px: tuple[int, ...],
    min_fill: float = 0.85,
    max_surround: float = 0.70,
) -> list[tuple[int, int, int, float]]:
    """Find pivot candidates: near-full disc with relatively empty surroundings.

    Returns (row, col, radius_px, score), sorted best first. A pivot touching its
    neighbour still passes because `max_surround` tolerates partial surround fill.
    """
    img = mask.astype(np.float32)
    shape = (img.shape[0] + 64, img.shape[1] + 64)
    shape = (1 << (shape[0] - 1).bit_length(), 1 << (shape[1] - 1).bit_length())
    img_fft = np.fft.rfft2(img, s=shape)

    found: list[tuple[int, int, int, float]] = []
    for r in radii_px:
        disc = disc_kernel(r)
        inside = _fft_convolve(img, disc, img_fft) / float(disc.sum())
        ring = annulus_kernel(r)
        surround = _fft_convolve(img, ring, img_fft) / float(ring.sum())
        hit = (inside >= min_fill) & (surround <= max_surround)
        rows, cols = np.nonzero(hit)
        scores = inside[rows, cols] - surround[rows, cols]
        found.extend(
            (int(row), int(col), r, float(score))
            for row, col, score in zip(rows, cols, scores, strict=True)
        )
    found.sort(key=lambda item: item[3], reverse=True)
    return found


def non_max_suppress(
    candidates: list[tuple[int, int, int, float]], min_separation_px: float
) -> list[tuple[int, int, int, float]]:
    """Greedy NMS in image space — one field per pivot centre."""
    kept: list[tuple[int, int, int, float]] = []
    for cand in candidates:
        row, col = cand[0], cand[1]
        if all((row - k[0]) ** 2 + (col - k[1]) ** 2 >= min_separation_px**2 for k in kept):
            kept.append(cand)
    return kept


def _crop_union(paths: list[Path], codes: set[int]) -> tuple[np.ndarray, dict]:
    """Union of crop pixels across the delineation years, on one reference grid.

    CDL county clips shift by a pixel between years, so every year is reprojected onto
    the newest year's grid before the union — class data, so nearest-neighbour.
    """
    with rasterio.open(paths[-1]) as ref:
        meta = {
            "transform": ref.transform,
            "crs": ref.crs,
            "shape": (ref.height, ref.width),
            "width": ref.width,
            "height": ref.height,
        }
    mask = np.zeros(meta["shape"], dtype=bool)
    for path in paths:
        with rasterio.open(path) as src:
            arr = src.read(1)
            same_grid = arr.shape == meta["shape"] and src.transform == meta["transform"]
            if not same_grid:
                aligned = np.zeros(meta["shape"], dtype="uint8")
                reproject(
                    source=arr,
                    destination=aligned,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=meta["transform"],
                    dst_crs=meta["crs"],
                    resampling=Resampling.nearest,
                )
                arr = aligned
        mask |= _crop_mask(arr, codes)
    return mask, meta


def find_pivots(
    paths: list[Path],
    *,
    code_map: dict[int, str],
    radii_px: tuple[int, ...] = PIVOT_RADII_PX,
    min_area_ha: float = MIN_AREA_HA,
    max_area_ha: float = MAX_AREA_HA,
    min_separation_px: float = 32.0,
) -> list[dict]:
    """Detect centre-pivot circles as candidate fields.

    Components can't be used directly: adjacent pivots and neighbouring cropland form
    one connected mosaic, so the geometry has to come from circle detection instead
    (disc fill + surrounding-ring emptiness), then NMS for one field per centre.

    ``min_separation_px`` must exceed 2x the largest radius, otherwise two detected
    centres produce overlapping fields and the crop history of each is contaminated.
    """
    detection_codes = set(code_map) - DETECTION_EXCLUDE
    mask, meta = _crop_union(paths, detection_codes)
    candidates = score_circles(mask, radii_px=radii_px, min_fill=0.92, max_surround=0.55)
    kept = non_max_suppress(candidates, min_separation_px)
    transform, res = meta["transform"], abs(meta["transform"].a)

    pivots = []
    for row, col, radius_px, score in kept:
        radius_m = radius_px * res
        area_ha = float(np.pi * radius_m**2 / 10_000.0)
        if not (min_area_ha <= area_ha <= max_area_ha):
            continue
        cx, cy = transform * (col + 0.5, row + 0.5)
        geom = Point(cx, cy).buffer(radius_m, quad_segs=48)
        pivots.append(
            {
                "geometry": geom,
                "area_ha": area_ha,
                "circularity": circularity(geom.area, geom.length),
                "score": score,
                "row": row,
                "col": col,
            }
        )
    pivots.sort(key=lambda c: c["score"], reverse=True)
    # Score ranks isolated pivots first (surround ≈ 0), so a plain top-N pool is all sandy
    # uplands and never contains the densely packed valley pivots. Stratifying the pool
    # keeps both, which is what makes the field sample representative of the county.
    pooled = stratified_pick([(p,) for p in pivots], CANDIDATE_POOL, cell_px=60)
    return [p[0] for p in pooled]


def zonal_history(
    field_geoms: list, years: list[int], cfg: Config, code_map: dict[int, str]
) -> tuple[list[dict[str, int]], list[dict[str, float]], list[list[int]]]:
    """Per-field, per-year majority CDL code using one histogram pass per year."""
    n = len(field_geoms)
    history_codes: list[dict[str, int]] = [{} for _ in range(n)]
    purity: list[dict[str, float]] = [{} for _ in range(n)]
    unknown: list[list[int]] = [[] for _ in range(n)]

    for year in years:
        path = cdl_tif(cfg, year)
        if not path.exists():
            continue
        with rasterio.open(path) as src:
            labels = rasterize(
                [(geom, idx + 1) for idx, geom in enumerate(field_geoms)],
                out_shape=(src.height, src.width),
                transform=src.transform,
                fill=0,
                dtype="int32",
                all_touched=False,
            )
            arr = src.read(1)
        if labels.shape != arr.shape:
            continue
        selected = labels > 0
        if not selected.any():
            continue
        idx = labels[selected].astype(np.int64) * 256 + arr[selected].astype(np.int64)
        hist = np.bincount(idx, minlength=(n + 1) * 256).reshape(n + 1, 256)
        for field_idx in range(n):
            code, share = majority_code(hist[field_idx + 1])
            if code is None:
                continue
            history_codes[field_idx][str(year)] = code
            purity[field_idx][str(year)] = round(share, 3)
            if code not in code_map and code not in unknown[field_idx]:
                unknown[field_idx].append(code)
    return history_codes, purity, unknown


def stratified_pick(items: list, max_fields: int, cell_px: int = 100) -> list:
    """Take the best item per ~3 km cell so one part of the county can't dominate.

    Taking the globally top-scoring pivots biases the sample badly: isolated pivots on
    sandy uplands score highest, so the field set came out 50/60 fine sand instead of
    Finney's valley silt loams. Stratifying keeps the sample spatially representative.
    """
    picked: dict[tuple[int, int], object] = {}
    for item in items:
        cand = item[0]
        key = (cand["row"] // cell_px, cand["col"] // cell_px)
        if key not in picked:
            picked[key] = item
    return list(picked.values())[:max_fields]


def derive_fields(cfg: Config) -> Path:
    """data/raw/cdl/*.tif -> data/interim/fields_raw.geojson.

    Interim, not the web contract: geometry + crop history + provenance. The engine adds
    soil, strategies and uncertainty, then writes contracts-shaped output.
    """
    years = list(range(cfg.crop_years[0], cfg.crop_years[1] + 1))
    missing = [y for y in years if not cdl_tif(cfg, y).exists()]
    if missing:
        raise FileNotFoundError(
            f"CDL rasters missing for {missing} — run `python -m pipeline cdl` first"
        )

    fro = "EPSG:4326"
    delineation = [cdl_tif(cfg, y) for y in DELINEATION_YEARS if cdl_tif(cfg, y).exists()]
    code_map = read_cdl_code_map()
    candidates = find_pivots(delineation, code_map=code_map)[:CANDIDATE_POOL]
    if not candidates:
        raise RuntimeError("no pivot-shaped fields found in the CDL mask")

    geoms = [c["geometry"] for c in candidates]
    history_codes, purity, unknown = zonal_history(geoms, years, cfg, code_map)

    # Reject detections sitting on un-cropped land: a real irrigated pivot is cropped in
    # nearly every year. This removes the pasture/fallow false positives that pass the
    # shape test but have no crop rotation to show.
    kept: list[tuple[dict, dict, dict, list[int]]] = []
    for idx, cand in enumerate(candidates):
        raw = history_codes[idx]
        cropped = sum(1 for code in raw.values() if code in CROPLAND_CDL)
        share = cropped / len(raw) if raw else 0.0
        if share < MIN_CROPPED_SHARE:
            continue
        # A field whose dominant class is ambiguous can't carry a credible passport.
        median_purity = float(np.median(list(purity[idx].values()))) if purity[idx] else 0.0
        if median_purity < MIN_MEDIAN_PURITY:
            continue
        kept.append((cand, raw, purity[idx], unknown[idx]))
    kept = stratified_pick(kept, MAX_FIELDS)
    if not kept:
        raise RuntimeError("every detected pivot failed the cropped-share filter")

    features = []
    for idx, (cand, raw, pur, unk) in enumerate(kept):
        geom_wgs = transform_geom(
            "EPSG:5070", fro, json.loads(json.dumps(cand["geometry"].__geo_interface__))
        )
        mapped = {
            year: code_map.get(code)
            for year, code in sorted(raw.items(), key=lambda kv: int(kv[0]))
        }
        cropped = sum(1 for code in raw.values() if code in CROPLAND_CDL)
        features.append(
            {
                "type": "Feature",
                "id": f"FIN-{idx + 1:03d}",
                "geometry": geom_wgs,
                "properties": {
                    "field_id": f"FIN-{idx + 1:03d}",
                    "area_ha": round(cand["area_ha"], 1),
                    "circularity": round(cand["circularity"], 3),
                    "detection_score": round(cand["score"], 3),
                    "irrigated": True,
                    "irrigation_type": "center_pivot",
                    "crop_history": {y: c for y, c in mapped.items() if c},
                    "crop_history_cdl": {y: int(c) for y, c in raw.items()},
                    "majority_purity": pur,
                    "cropped_share": round(cropped / len(raw), 3) if raw else 0.0,
                    "unknown_cdl_years": [
                        y for y, code in raw.items() if code_map.get(code) is None
                    ],
                    "unknown_cdl_codes": unk,
                    "source": "USDA NASS Cropland Data Layer 2008-2025, 30 m, county clip",
                },
            }
        )

    collection = {
        "type": "FeatureCollection",
        "crs": "EPSG:4326",
        "county": {
            "name": cfg.region.county_name,
            "state": "KS",
            "fips": cfg.region.fips,
            "bbox": list(cfg.region.bbox),
        },
        "years": list(cfg.crop_years),
        "delineation_years": list(DELINEATION_YEARS),
        "method": (
            "centre pivots detected by FFT disc/annulus template matching on the union of "
            "crop classes 2021-2025, non-maximum suppressed at 32 px (960 m) spacing, then "
            "filtered to >= "
            f"{MIN_CROPPED_SHARE:.0%} cropped years and median purity >= {MIN_MEDIAN_PURITY}, "
            "then stratified to one field per ~3 km cell so the sample spans the county; "
            "crop history = per-year majority CDL class inside each circle"
        ),
        "known_limits": [
            "Field sample is soil-biased: 48/60 fields sit on sands (Valent / Valent-Vona), "
            "while the county is ~42% silt loams (Richfield 27%, Ulysses 11%, Beeler 4%) and "
            "~16% Valent sands. Cause: pivots surrounded by rangeland score highest in the "
            "disc/annulus test, so densely packed valley pivots are under-selected even "
            "after stratifying the candidate pool to one per 1.8 km cell. Raise "
            "MAX_SURROUND_FILL or detect pivots from imagery to fix properly.",
            "Geometry is idealised: every field is a perfect circle at the detected radius, "
            "so many share an identical area (55.4 ha, 63.6 ha, ...). Real pivots are not "
            "exact circles and their true corners/edges are not represented; treat area_ha as "
            "approximate to within a few percent.",
            "Detection favours pivots that are isolated from neighbouring cropland. "
            "Alfalfa is over-represented for the same reason (crop mix is ~44% alfalfa "
            "against 4.7% of county acreage).",
            "Visual check of 60 fields against the CDL: most rings land on real pivots, "
            "roughly 10-15% are off-centre or on adjoining land. majority_purity and "
            "cropped_share expose per-field quality; the engine should threshold on them.",
            "CDL classes with no crops.csv row (triticale 205, double-crop 225/228/236, "
            "oats 28, other hay 37) are reported raw in crop_history_cdl and listed in "
            "unknown_cdl_years rather than being forced into an existing crop code.",
        ],
        "fields": len(features),
        "features": features,
    }
    INTERIM.mkdir(parents=True, exist_ok=True)
    out = INTERIM / "fields_raw.geojson"
    out.write_text(json.dumps(collection, indent=1) + "\n")

    unknown_total = sum(len(f["properties"]["unknown_cdl_years"]) for f in features)
    print(
        f"[fields] {len(features)} pivots, {min(c['area_ha'] for c in candidates):.0f}-"
        f"{max(c['area_ha'] for c in candidates):.0f} ha -> {out.name}"
        f" ({unknown_total} field-years with no crops.csv class)"
    )
    return out
