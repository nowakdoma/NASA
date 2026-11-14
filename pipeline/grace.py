"""GRACE / GRACE-FO terrestrial water storage for the county — the Ogallala hook.

Product: JPL RL06.3Mv04 mascon (CRI filtered), TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4.
PO.DAAC publishes the whole 2002-2026 series as ONE ~46 MB netCDF file, so this needs a
single download rather than ~280 monthly granules. GDAL's netCDF driver opens it (unlike
the HDF4/HDF5 SMAP products), so no extra dependency.

What the number means, and what it does not:
- `lwe_thickness` is **total** water storage anomaly in cm of equivalent water: groundwater
  plus soil moisture, snow, surface water and canopy. It is NOT groundwater alone. Splitting
  out the groundwater share needs a land-surface model (GLDAS/Noah) to subtract the other
  terms, which this pipeline does not do — so call it "water storage", never "groundwater".
- The solution is built on equal-area ~3 degree mascons (~300 km). The signal is regional:
  it says nothing about one pivot or one field, and the value for Finney County is an
  interpolation of a much coarser field.
- Values are anomalies against the 2004.000-2009.999 mean, so the level is arbitrary and
  only the shape and trend are meaningful.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import rasterio

from pipeline.config import INTERIM, RAW, Config

COLLECTION_ID = "C3195527175-POCLOUD"
PRODUCT = "TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4 (JPL RL06.3Mv04)"
CMR_GRANULES = "https://cmr.earthdata.nasa.gov/search/granules.json"
TIME_EPOCH = date(2002, 1, 1)
TIME_UNITS_DAYS = "days since 2002-01-01"
SCHEMA_VERSION = "0.4"


def grace_file(cfg: Config) -> Path | None:
    files = sorted((RAW / "grace").glob("*.nc"))
    return files[-1] if files else None


def fetch_grace(cfg: Config, *, force: bool = False) -> Path:
    """Download the newest GRACE/GRACE-FO mascon netCDF (one file, whole series)."""
    from pipeline.config import earthdata_auth_header as _auth
    from pipeline.net import download

    request = urllib.request.Request(
        f"{CMR_GRANULES}?collection_concept_id={COLLECTION_ID}&page_size=1&sort_key=-start_date",
        headers={"User-Agent": "FieldShift/0.1"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        feed = json.load(response)
    entry = feed["feed"]["entry"][0]
    href = next(
        link["href"]
        for link in entry["links"]
        if "podaac-ops-cumulus-protected" in link.get("href", "")
    )
    dest = RAW / "grace" / href.rsplit("/", 1)[-1]
    path = download(href, dest, headers=_auth(), timeout=600, force=force)
    size_mb = path.stat().st_size / 1e6
    start = entry["time_start"][:10]
    print(f"[grace] {path.name} ({size_mb:.0f} MB), granule {start}")
    return path


def _column(lon: float, transform, width: int) -> int:
    """Column for a longitude, tolerating both -180..180 and 0..360 grids.

    The GRACE netCDF is stored 0..360 (x origin 0), which silently yields negative column
    indices if you assume the usual -180 convention.
    """
    col = int((lon - transform.c) / transform.a)
    if col < 0:
        col = int((lon + 360.0 - transform.c) / transform.a)
    return col


def bbox_window(transform, bbox: tuple[float, float, float, float], shape: tuple[int, int]):
    """Row/col slice covering a lon/lat bbox on a north-up grid."""
    min_lon, min_lat, max_lon, max_lat = bbox
    width = shape[1]
    cols = sorted([_column(min_lon, transform, width), _column(max_lon, transform, width)])
    rows = sorted(
        [
            int((max_lat - transform.f) / transform.e),
            int((min_lat - transform.f) / transform.e),
        ]
    )
    row0, row1 = max(0, rows[0]), min(shape[0], rows[1] + 1)
    col0, col1 = max(0, cols[0]), min(shape[1], cols[1] + 1)
    if row0 >= row1 or col0 >= col1:
        raise ValueError(f"bbox {bbox} falls outside the grid")
    return row0, row1, col0, col1


def days_to_dates(values: np.ndarray, epoch: date = TIME_EPOCH) -> list[str]:
    """CF 'days since' values -> ISO dates (mid-month values land on the 16th)."""
    return [(epoch + timedelta(days=float(v))).isoformat() for v in values]


def decimal_years(iso_dates: list[str]) -> np.ndarray:
    return np.array(
        [d.year + (d.timetuple().tm_yday - 1) / 365.25 for d in map(date.fromisoformat, iso_dates)]
    )


def one_per_month(rows: list[dict]) -> tuple[list[dict], int]:
    """Keep a single record per calendar month, preferring the one nearest mid-month.

    GRACE solution epochs are not evenly spaced (median 30.5 d, but gaps of 11-370 d), so a
    calendar month occasionally carries two epochs. Averaging the whole series as-is
    double-counts those months.
    """
    best: dict[str, dict] = {}
    for row in rows:
        month = row["date"][:7]
        closeness = abs(int(row["date"][8:10]) - 15)
        current = best.get(month)
        if current is None or closeness < abs(int(current["date"][8:10]) - 15):
            best[month] = row
    kept = [best[m] for m in sorted(best)]
    return kept, len(rows) - len(kept)


def linear_trend(years: np.ndarray, values: np.ndarray) -> dict:
    """Least-squares slope in cm/yr with R² and the slope standard error."""
    mask = np.isfinite(years) & np.isfinite(values)
    x, y = years[mask], values[mask]
    if x.size < 3:
        return {"cm_per_year": None, "note": "fewer than 3 valid months"}
    slope, intercept = np.polyfit(x, y, 1)
    predicted = slope * x + intercept
    ss_res = float(np.sum((y - predicted) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    dof = max(1, x.size - 2)
    stderr = float(np.sqrt(ss_res / dof / np.sum((x - x.mean()) ** 2)))
    return {
        "cm_per_year": round(float(slope), 3),
        "r2": round(r2, 3),
        "stderr_cm_per_year": round(stderr, 3),
        "months": int(x.size),
    }


def read_series(cfg: Config, path: Path) -> dict:
    """Area-mean TWS anomaly per month over the county bbox."""
    with rasterio.open(f"NETCDF:{path}:lwe_thickness") as src:
        window = bbox_window(src.transform, cfg.region.bbox, (src.height, src.width))
        row0, row1, col0, col1 = window
        data = src.read(window=((row0, row1), (col0, col1))).astype(float)
        nodata = src.nodata
        transform = src.transform
    with rasterio.open(f"NETCDF:{path}:uncertainty") as src_u:
        unc = src_u.read(window=((row0, row1), (col0, col1))).astype(float)
    with rasterio.open(f"NETCDF:{path}:time") as src_t:
        times = src_t.read(1).ravel()
        units = src_t.tags(1).get("units", TIME_UNITS_DAYS)
    if "2002-01-01" not in units:
        raise ValueError(f"unexpected time units: {units}")

    if nodata is not None:
        data[data == nodata] = np.nan
        unc[unc == nodata] = np.nan
    series = np.nanmean(data.reshape(data.shape[0], -1), axis=1)
    errors = np.sqrt(np.nansum(unc.reshape(unc.shape[0], -1) ** 2, axis=1)) / max(
        1, data.shape[1] * data.shape[2]
    )
    return {
        "dates": days_to_dates(times),
        "tws_cm": series,
        "uncertainty_cm": errors,
        "cells": int((row1 - row0) * (col1 - col0)),
        "cell_extent": [float(transform.a), float(abs(transform.e))],
    }


def derive_grace(cfg: Config) -> Path:
    """data/raw/grace/*.nc -> data/interim/grace_water_storage.json."""
    path = grace_file(cfg)
    if path is None:
        raise FileNotFoundError("no GRACE file in data/raw/grace — run `python -m pipeline grace`")
    series = read_series(cfg, path)
    raw_rows = [
        {
            "date": d,
            "tws_cm": None if not np.isfinite(v) else round(float(v), 2),
            "uncertainty_cm": None if not np.isfinite(u) else round(float(u), 2),
        }
        for d, v, u in zip(
            series["dates"], series["tws_cm"], series["uncertainty_cm"], strict=False
        )
    ]
    rows, duplicates = one_per_month(raw_rows)
    dates = [r["date"] for r in rows]
    values = np.array([np.nan if r["tws_cm"] is None else r["tws_cm"] for r in rows], dtype=float)
    years = decimal_years(dates)
    trend = linear_trend(years, values)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "mock": False,
        "source": f"NASA/JPL GRACE & GRACE-FO mascon, {PRODUCT}",
        "file": path.name,
        "units": "cm equivalent water thickness anomaly",
        "baseline": "2004.000-2009.999 mean removed",
        "region": {
            "name": cfg.region.name,
            "fips": cfg.region.fips,
            "bbox": list(cfg.region.bbox),
            "grid_cells": series["cells"],
            "grid_resolution_deg": series["cell_extent"],
        },
        "months": len(dates),
        "period": [dates[0], dates[-1]],
        "trend": trend,
        "trend_last_10_years": linear_trend(years[-120:], values[-120:]),
        "duplicate_epochs_dropped": duplicates,
        "series": rows,
        "data_gaps": [
            "This is TOTAL water storage (groundwater + soil moisture + snow + surface water). "
            "It is not groundwater: separating the groundwater share needs a land-surface "
            "model to subtract the other terms, which is not done here.",
            "The solution is built on ~3 degree (~300 km) mascons. Treat the county value as a "
            "regional signal that has been interpolated to this location, not a local measurement.",
            "Anomalies are relative to the 2004-2009 mean, so the level is arbitrary; only the "
            "shape and the trend carry information.",
            "Trend length matters: this period spans a wet 2019 and dry 2012-2013 and 2022, and "
            "starting or ending on a drought year moves the slope. Read it with the series.",
            "GRACE and GRACE-FO have a data gap between missions (2017-2018); no months are "
            "interpolated across it.",
        ],
    }
    out = INTERIM / "grace_water_storage.json"
    out.write_text(json.dumps(payload, indent=1) + "\n")
    print(
        f"[grace] {len(dates)} months {dates[0]}..{dates[-1]}, trend "
        f"{trend['cm_per_year']} cm/yr (R2 {trend.get('r2')}), "
        f"{series['cells']} cells -> {out.name}"
    )
    return out
