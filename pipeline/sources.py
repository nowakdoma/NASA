"""One function per dataset. Each writes to data/raw/<name>/ and is idempotent.

``power`` is implemented (public API, no login). The raster sources still raise
``NotImplementedError`` and need the geospatial dependency decision in AGENTS.md.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import rasterio

from pipeline.config import INTERIM, RAW, Config
from pipeline.fields import cdl_tif
from pipeline.net import download
from pipeline.terrain import fetch_srtm as terrain_fetch_srtm

# POWER daily point API: one row per day, DOY-indexed, no date column.
POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
POWER_PARAMS = (
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "WS2M",
    "ALLSKY_SFC_SW_DWN",
    "PRECTOTCORR",
)
POWER_MISSING = -999.0

# POWER column -> (interim column, unit). Names carry the unit on purpose: the
# engine must never guess whether a number is C or K, mm or kg/m2.
POWER_COLUMNS = {
    "t2m": ("t2m_c", "degC"),
    "t2m_max": ("t2m_max_c", "degC"),
    "t2m_min": ("t2m_min_c", "degC"),
    "rh2m": ("rh2m_pct", "percent"),
    "ws2m": ("ws2m_ms", "m/s"),
    "allsky_sfc_sw_dwn": ("sw_down_mj_m2_d", "MJ/m2/day"),
    "prectotcorr": ("precip_mm_d", "mm/day"),
}


def _power_raw_path(cfg: Config) -> Path:
    lon, lat = cfg.region.centroid
    y0, y1 = cfg.weather_years
    return RAW / "power" / f"power_daily_{lat:.3f}_{lon:.3f}_{y0}-{y1}.csv"


def power_request_url(cfg: Config) -> str:
    """Daily POWER request for the region centroid over cfg.weather_years."""
    lon, lat = cfg.region.centroid
    y0, y1 = cfg.weather_years
    params = ",".join(POWER_PARAMS)
    return (
        f"{POWER_URL}?parameters={params}&community=AG"
        f"&longitude={lon}&latitude={lat}"
        f"&start={y0}0101&end={y1}1231&format=CSV"
    )


def _read_power_csv(path: Path) -> pd.DataFrame:
    """Parse a POWER CSV: skip the ``-BEGIN HEADER-`` block, keep the data table."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for idx, line in enumerate(lines):
        if line.startswith("YEAR,"):
            frame = pd.read_csv(path, skiprows=idx)
            break
    else:
        raise ValueError(f"no 'YEAR,' header found in {path}")
    frame.columns = [str(c).strip().lower() for c in frame.columns]
    return frame


def fetch_power(cfg: Config, *, force: bool = False) -> Path:
    """NASA POWER daily point data (T2M, T2M_MAX, T2M_MIN, RH2M, WS2M, ALLSKY_SFC_SW_DWN,
    PRECTOTCORR) for the region centroid, cfg.weather_years. No login needed.

    Writes ``data/raw/power/*.csv`` (as delivered) and a tidy
    ``data/interim/weather_daily.csv`` plus ``weather_daily.meta.json`` recording
    provenance and per-column missing counts.
    """
    raw = download(power_request_url(cfg), _power_raw_path(cfg), force=force)
    frame = _read_power_csv(raw)

    # POWER parameter names arrive uppercase; _read_power_csv lowercases the header.
    missing = {
        col: int((frame[col] == POWER_MISSING).sum())
        for col in (p.lower() for p in POWER_PARAMS)
        if col in frame.columns
    }
    numeric = [col for col in POWER_COLUMNS if col in frame.columns]
    values = frame[numeric].apply(pd.to_numeric, errors="coerce").astype("float64")
    frame[numeric] = values.mask(values == POWER_MISSING)

    dates = pd.to_datetime(
        frame["year"].astype(str) + frame["doy"].astype(str).str.zfill(3), format="%Y%j"
    )
    tidy = pd.DataFrame({"date": dates, "year": frame["year"].astype(int), "doy": frame["doy"]})
    for src, (dst, _unit) in POWER_COLUMNS.items():
        if src in frame.columns:
            tidy[dst] = frame[src].to_numpy()

    tidy = tidy.drop_duplicates("date").sort_values("date").reset_index(drop=True)
    INTERIM.mkdir(parents=True, exist_ok=True)
    out = INTERIM / "weather_daily.csv"
    tidy.to_csv(out, index=False, date_format="%Y-%m-%d")

    y0, y1 = cfg.weather_years
    expected = (pd.Timestamp(f"{y1}-12-31") - pd.Timestamp(f"{y0}-01-01")).days + 1
    meta = {
        "source": "NASA POWER (MERRA-2 / CERES SYN1deg), daily point, community=AG",
        "url": power_request_url(cfg),
        "raw_file": str(raw.relative_to(INTERIM.parent)),
        "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "region": {
            "name": cfg.region.name,
            "fips": cfg.region.fips,
            "centroid_lon": cfg.region.centroid[0],
            "centroid_lat": cfg.region.centroid[1],
        },
        "years": [y0, y1],
        "rows": len(tidy),
        "days_expected": expected,
        "days_missing": expected - len(tidy),
        "columns": {dst: unit for dst, unit in POWER_COLUMNS.values() if dst in tidy.columns},
        "missing_by_column": missing,
        "note": (
            "POWER returns -999 for days it cannot compute; those are written as empty "
            "cells, not zeros. Grid cell is 0.5 x 0.625 deg, so county-scale weather is "
            "one representative series, not a per-field measurement."
        ),
    }
    (INTERIM / "weather_daily.meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(
        f"[power] {len(tidy):,} days {tidy['date'].min():%Y-%m-%d}..{tidy['date'].max():%Y-%m-%d}"
        f" -> {out.relative_to(INTERIM.parent)}"
        f" ({meta['days_missing']} missing, {sum(missing.values())} flagged cells)"
    )
    return out


def fetch_ndvi(cfg: Config) -> None:
    """MODIS MOD13Q1 250 m 16-day NDVI (Earthdata login) -> bare-soil periods."""
    raise NotImplementedError


def fetch_smap(cfg: Config) -> None:
    """SMAP L3 enhanced soil moisture SPL3SMP_E (Earthdata) -> water-stress windows."""
    raise NotImplementedError


def fetch_srtm(cfg: Config, *, force: bool = False) -> list[Path]:
    """SRTM GL1 30 m DEM for the region — public skadi bucket, no credentials needed."""
    return terrain_fetch_srtm(cfg, force=force)


def fetch_cdl(cfg: Config, *, force: bool = False) -> list[Path]:
    """USDA CDL 2008-2025 clipped to cfg.region.bbox.

    The NASS service returns a county-clipped 30 m GeoTIFF per year (EPSG:5070), which
    is why no clipping is needed here. Grids shift by fractions of a pixel between
    years, so consumers must work in coordinates, never pixel indices.
    """
    y0, y1 = cfg.crop_years
    out = []
    for year in range(y0, y1 + 1):
        dest = cdl_tif(cfg, year)
        download(
            f"https://nassgeodata.gmu.edu/webservice/nass_data_cache/byfips/CDL_{year}_{cfg.region.fips}.tif",
            dest,
            timeout=300,
            force=force,
        )
        out.append(dest)
    with rasterio.open(out[-1]) as src:
        if src.crs is None:
            raise RuntimeError(f"{out[-1].name} has no CRS")
        crs, res = str(src.crs), src.res
    total_mb = sum(p.stat().st_size for p in out) / 1e6
    print(f"[cdl] {len(out)} years {y0}-{y1}, {crs} {res[0]:.0f} m, {total_mb:.0f} MB")
    return out


def fetch_ssurgo(cfg: Config) -> None:
    """SSURGO map units + component/horizon tables for the county."""
    raise NotImplementedError


SOURCES = {
    "power": fetch_power,
    "ndvi": fetch_ndvi,
    "smap": fetch_smap,
    "srtm": fetch_srtm,
    "cdl": fetch_cdl,
    "ssurgo": fetch_ssurgo,
}
