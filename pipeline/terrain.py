"""SRTM 30 m elevation -> per-field mean slope.

Tiles come from the public `elevation-tiles-prod` skadi bucket: no login, no token, which
is why this works even if the LP DAAC mirror is unavailable. Each tile is a gzipped
big-endian int16 grid of 3601x3601 samples at 1 arc-second, rows north-to-south.
"""

from __future__ import annotations

import gzip
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import shape

from pipeline.config import INTERIM, RAW, Config
from pipeline.net import download

SKADI = "https://s3.amazonaws.com/elevation-tiles-prod/skadi/{ns}/{quad}.hgt.gz"
ARC_SEC_M = 30.87  # metres per arc-second of latitude at the equator-ish scale
NODATA = -32768
GRID = 3601  # SRTM1: 1 arc-second, inclusive endpoints


def tiles_for_bbox(bbox: tuple[float, float, float, float]) -> list[str]:
    """Quad names covering bbox = (min_lon, min_lat, max_lon, max_lat)."""
    min_lon, min_lat, max_lon, max_lat = bbox
    names = []
    for lat in range(math.floor(min_lat), math.floor(max_lat) + 1):
        for lon in range(math.floor(min_lon), math.floor(max_lon) + 1):
            ns = "N" if lat >= 0 else "S"
            ew = "E" if lon >= 0 else "W"
            names.append(f"{ns}{abs(lat):02d}{ew}{abs(lon):03d}")
    return names


def tile_path(cfg: Config, quad: str) -> Path:
    return RAW / "srtm" / f"{quad}.hgt.gz"


def srtm_url(quad: str) -> str:
    return SKADI.format(ns=quad[:3], quad=quad)


def fetch_srtm(cfg: Config, *, force: bool = False) -> list[Path]:
    """Download the SRTM tiles covering the region. No credentials required."""
    out = []
    for quad in tiles_for_bbox(cfg.region.bbox):
        out.append(download(srtm_url(quad), tile_path(cfg, quad), timeout=300, force=force))
    mb = sum(p.stat().st_size for p in out) / 1e6
    print(f"[srtm] {len(out)} tiles ({', '.join(p.name for p in out)}), {mb:.0f} MB")
    return out


def read_hgt(path: Path) -> np.ndarray:
    """Read a .hgt.gz tile as a float elevation array with nodata as NaN."""
    with gzip.open(path, "rb") as fh:
        raw = fh.read()
    expected = GRID * GRID * 2
    if len(raw) != expected:
        raise ValueError(f"{path.name}: expected {expected} bytes, got {len(raw)}")
    elev = np.frombuffer(raw, dtype=">i2").reshape(GRID, GRID).astype(np.float32)
    elev[elev == NODATA] = np.nan
    return elev


def slope_percent(elev: np.ndarray, *, lat: float) -> np.ndarray:
    """Slope in percent from a 1 arc-second grid (py = 30.87 m, px shrinks with cos(lat))."""
    dy = ARC_SEC_M
    dx = ARC_SEC_M * math.cos(math.radians(lat))
    grad_y, grad_x = np.gradient(elev, dy, dx)
    return 100.0 * np.hypot(grad_x, grad_y)


def field_slopes(fields_geojson: Path, cfg: Config) -> dict[str, dict[str, float]]:
    """Mean slope (%) and elevation (m) per field, sampled from all covering tiles."""
    data = json.loads(fields_geojson.read_text())
    fields = data["features"]
    slopes: dict[str, list[float]] = {f["properties"]["field_id"]: [] for f in fields}
    elevs: dict[str, list[float]] = {f["properties"]["field_id"]: [] for f in fields}

    for quad in tiles_for_bbox(cfg.region.bbox):
        path = tile_path(cfg, quad)
        if not path.exists():
            continue
        lat0 = int(quad[1:3]) * (1 if quad[0] == "N" else -1)
        lon0 = int(quad[4:7]) * (1 if quad[3] == "E" else -1)
        elev = read_hgt(path)
        slope = slope_percent(elev, lat=lat0 + 0.5)

        for feat in fields:
            geom = shape(feat["geometry"])
            min_lon, min_lat, max_lon, max_lat = geom.bounds
            # Tile covers [lon0, lon0+1) x [lat0, lat0+1); skip non-overlapping fields.
            if max_lon < lon0 or min_lon > lon0 + 1 or max_lat < lat0 or min_lat > lat0 + 1:
                continue
            row0 = int((lat0 + 1 - min(max_lat, lat0 + 1)) / (1 / (GRID - 1)))
            row1 = int((lat0 + 1 - max(min_lat, lat0)) / (1 / (GRID - 1))) + 1
            col0 = int((max(min_lon, lon0) - lon0) / (1 / (GRID - 1)))
            col1 = int((min(max_lon, lon0 + 1) - lon0) / (1 / (GRID - 1))) + 1
            win_s = slope[max(0, row0) : row1, max(0, col0) : col1]
            win_e = elev[max(0, row0) : row1, max(0, col0) : col1]
            if win_s.size == 0:
                continue
            fid = feat["properties"]["field_id"]
            slopes[fid].append(float(np.nanmean(win_s)))
            elevs[fid].append(float(np.nanmean(win_e)))

    out = {}
    for fid, vals in slopes.items():
        if not vals:
            continue
        out[fid] = {
            "slope_pct": round(float(np.mean(vals)), 2),
            "elevation_m": round(float(np.mean(elevs[fid])), 1),
        }
    return out


def derive_terrain(cfg: Config) -> Path:
    """data/interim/fields_raw.geojson -> data/interim/field_terrain.csv."""
    import csv

    src = INTERIM / "fields_raw.geojson"
    if not src.exists():
        raise FileNotFoundError(f"{src.name} is missing — run `python -m pipeline fields` first")
    per_field = field_slopes(src, cfg)
    if not per_field:
        raise RuntimeError("no SRTM tiles matched the fields — run `python -m pipeline srtm`")

    out = INTERIM / "field_terrain.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["field_id", "slope_pct", "elevation_m"], extrasaction="ignore"
        )
        writer.writeheader()
        for fid, vals in sorted(per_field.items()):
            writer.writerow({"field_id": fid, **vals})

    vals = [v["slope_pct"] for v in per_field.values()]
    print(
        f"[terrain] {len(per_field)} fields, slope {min(vals):.2f}-{max(vals):.2f} % "
        f"(median {np.median(vals):.2f}) -> {out.name}"
    )
    return out
