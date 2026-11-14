"""MODIS MOD13Q1 NDVI -> per-field bare-soil periods.

Why not LP DAAC directly: MOD13Q1 ships as HDF4, and the GDAL that ships inside the
rasterio wheels has no HDF4 driver, so `rasterio.open("<granule>.hdf")` fails even with a
valid Earthdata token. The Planetary Computer hosts the same MOD13Q1.061 collection as
cloud-optimised GeoTIFFs, which rasterio can range-read over HTTPS with an anonymous SAS
signature — same NASA data, readable without a local HDF toolchain.

Bare soil = NDVI below BARE_NDVI_MAX on consecutive 16-day composites, keeping only
composites whose VI QA says good/marginal. Composites are 16-day totals, so a "period"
is only accurate to about half a composite.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize

from pipeline.config import INTERIM, Config

PC_ROOT = "https://planetarycomputer.microsoft.com"
PC = f"{PC_ROOT}/api/stac/v1"
COLLECTION = "modis-13Q1-061"
NDVI_ASSET = "250m_16_days_NDVI"
QA_ASSET = "250m_16_days_VI_Quality"
NDVI_SCALE = 1e-4
NDVI_FILL = -3000
BARE_NDVI_MAX = 0.30
MIN_BARE_COMPOSITES = 2  # one 16-day composite below threshold is weather noise
QA_MAX_OK = 1  # SummaryQA bits 0-1: 0 good, 1 marginal, 2 snow/ice, 3 cloudy

# Per-composite cache. A full 2008-2025 run is ~414 composites x 2 assets and does not fit
# in one execution window, so each finished composite is appended here and later runs skip
# it. Keyed by field_id so a changed field set invalidates naturally.
CACHE_NAME = "composite_means.jsonl"

# The SAS signing endpoint rate-limits (HTTP 429). Pace calls and back off on 429 rather
# than treating it as a per-asset failure, which silently drops composites.
SIGN_MIN_INTERVAL_S = 0.35
_last_sign_at = 0.0

# Signed URLs are reusable for the whole run; re-signing per read is what trips the
# endpoint into transient 404s under bursts.
_SIGNED: dict[str, str] = {}


def _get(url: str, data: bytes | None = None, timeout: float = 120.0) -> dict:
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json", "User-Agent": "FieldShift/0.1"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def search_items(cfg: Config, *, start: str, end: str, limit: int = 2000) -> list[dict]:
    """All MOD13Q1 items intersecting the region over [start, end).

    Queried one year at a time on purpose. PC's POST search returns a ``next`` link with no
    token and no pagination field, so a single wide query silently stops at the first page
    (100 items); following the link with GET drops the bbox filter and returns the whole
    planet. A year is ~23 composites, comfortably under the page limit.
    """
    from shapely.geometry import box, shape

    first_year = int(start[:4])
    last_year = int(end[:4])
    region = box(*cfg.region.bbox)
    items: list[dict] = []
    for year in range(first_year, last_year + 1):
        query = {
            "collections": [COLLECTION],
            "bbox": list(cfg.region.bbox),
            "datetime": f"{year}-01-01/{year}-12-31",
            "limit": 100,
        }
        page = _get(f"{PC}/search", data=json.dumps(query).encode())
        for item in page.get("features", []):
            geometry = item.get("geometry")
            if geometry and not shape(geometry).intersects(region):
                continue
            items.append(item)

    # Terra only: the collection also serves Aqua (MYD13Q1), whose composites interleave
    # with Terra's and whose assets this signing endpoint does not sign.
    items = [item for item in items if item["id"].startswith("MOD13Q1")]
    # One granule per composite date: reprocessed versions share a date and would
    # otherwise be counted twice.
    items.sort(key=item_date)
    unique: dict[str, dict] = {}
    for item in items:
        unique.setdefault(item_date(item), item)
    return list(unique.values())[:limit]


def item_date(item: dict) -> str:
    """Composite start date. PC leaves properties.datetime null for this collection."""
    props = item["properties"]
    stamp = props.get("datetime") or props.get("start_datetime") or ""
    return stamp[:10]


def sign(href: str, *, retries: int = 4) -> str:
    """SAS-sign an asset URL (anonymous, no account required).

    NOTE: the signing API lives at the host root, not under /api/stac/v1 — building it from
    the STAC base URL yields a 404 that looks exactly like a missing asset.
    """
    global _last_sign_at
    cached = _SIGNED.get(href)
    if cached:
        return cached
    url = f"{PC_ROOT}/api/sas/v1/sign?href={urllib.parse.quote(href, safe='')}"
    last: Exception | None = None
    for attempt in range(retries):
        wait = SIGN_MIN_INTERVAL_S - (time.monotonic() - _last_sign_at)
        if wait > 0:
            time.sleep(wait)
        try:
            signed = _get(url)["href"]
            _SIGNED[href] = signed
            return signed
        except urllib.error.HTTPError as err:
            last = err
            if err.code not in (404, 429):
                raise
            retry_after = err.headers.get("Retry-After") if err.headers else None
            try:
                delay = float(retry_after)
            except (TypeError, ValueError):
                delay = 5.0 * (attempt + 1)
            time.sleep(min(delay, 60.0))
        finally:
            _last_sign_at = time.monotonic()
    raise RuntimeError(f"could not sign {href[:80]}") from last


def read_band(url: str, bounds: tuple[float, float, float, float], dtype: str = "int16"):
    """Read just the window covering WGS84 ``bounds``; returns (array, transform, crs).

    The bounds are lon/lat but MOD13Q1 is in MODIS sinusoidal metres, so they must be
    reprojected before the pixel window is computed — otherwise the window is empty.
    """
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds

    # Without these, GDAL probes the remote COG with directory listings on every open,
    # which dominates the runtime across hundreds of composites.
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
        GDAL_HTTP_MULTIPLEX="YES",
    ):
        with rasterio.open(url) as src:
            native = transform_bounds("EPSG:4326", src.crs, *bounds)
            window = from_bounds(*native, transform=src.transform)
            arr = src.read(1, window=window, boundless=True, fill_value=0)
            transform = src.window_transform(window)
            return arr.astype(dtype), transform, src.crs


def field_means(labels: np.ndarray, values: np.ndarray, n_fields: int) -> np.ndarray:
    """Mean valid value per field label (0 = outside any field)."""
    means = np.full(n_fields + 1, np.nan)
    for label in range(1, n_fields + 1):
        mask = (labels == label) & np.isfinite(values)
        if mask.any():
            means[label] = float(values[mask].mean())
    return means


def load_cache(cfg: Config) -> dict[str, dict]:
    """date -> {"field_id": mean} from previous runs."""
    from pipeline.config import RAW

    path = RAW / "ndvi" / CACHE_NAME
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        out[row["date"]] = row["fields"]
    return out


def append_cache(cfg: Config, date: str, means: dict[str, float | None]) -> None:
    from pipeline.config import RAW

    path = RAW / "ndvi" / CACHE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"date": date, "fields": means}) + "\n")


def ndvi_series(
    fields: list[dict],
    cfg: Config,
    years: list[int],
    *,
    progress: bool = False,
    force: bool = False,
) -> tuple[np.ndarray, list[str]]:
    """NDVI per field per composite, newest composites first.

    Resumable and rate-limit aware: composites already cached are skipped, and the newest
    uncached ones are fetched first so a partial run still covers the recent years that the
    passport actually shows.
    """
    items = search_items(cfg, start=f"{years[0]}-01-01", end=f"{years[-1]}-12-31")
    field_ids = [f["properties"]["field_id"] for f in fields]
    cache = {} if force else load_cache(cfg)

    results: dict[str, list[float]] = {}
    todo: list[dict] = []
    for item in items:
        if NDVI_ASSET not in item["assets"]:
            continue
        date = item_date(item)
        cached = cache.get(date)
        if cached and all(fid in cached for fid in field_ids):
            results[date] = [cached.get(fid, np.nan) for fid in field_ids]
        else:
            todo.append(item)
    todo.sort(key=item_date, reverse=True)

    if progress:
        already = len(results)
        print(f"[ndvi] {already} cached, {len(todo)} to fetch (newest first)", flush=True)

    labels = None
    for idx, item in enumerate(todo):
        date = item_date(item)
        try:
            signed_ndvi = sign(item["assets"][NDVI_ASSET]["href"])
            # One signature covers the whole container, so the QA band rides on it.
            query = signed_ndvi.split("?", 1)[1] if "?" in signed_ndvi else ""
            qa_url = item["assets"][QA_ASSET]["href"] + (f"?{query}" if query else "")
            ndvi_raw, transform, crs = read_band(signed_ndvi, cfg.region.bbox)
            qa_raw, _, _ = read_band(qa_url, cfg.region.bbox)
        except Exception as err:  # noqa: BLE001 - one bad composite must not kill the run
            print(f"[ndvi] skip {item['id']}: {type(err).__name__} {str(err)[:70]}", flush=True)
            continue
        if labels is None:
            from rasterio.warp import transform_geom

            shapes = [
                (transform_geom("EPSG:4326", crs, f["geometry"]), i + 1)
                for i, f in enumerate(fields)
            ]
            labels = rasterize(
                shapes, out_shape=ndvi_raw.shape, transform=transform, fill=0, dtype="int32"
            )
        ndvi = np.where(ndvi_raw == NDVI_FILL, np.nan, ndvi_raw * NDVI_SCALE)
        ndvi = np.where((qa_raw & 0b11) <= QA_MAX_OK, ndvi, np.nan)
        means = field_means(labels, ndvi, len(fields))
        results[date] = list(means[1:])
        append_cache(
            cfg,
            date,
            {
                fid: (None if not np.isfinite(means[i + 1]) else round(float(means[i + 1]), 4))
                for i, fid in enumerate(field_ids)
            },
        )
        if progress and idx % 10 == 0:
            print(f"[ndvi] {idx + 1}/{len(todo)} fetched ({date})", flush=True)

    dates = sorted(results)
    series = np.array([results[d] for d in dates], dtype=float).T
    return series, dates


def bare_periods(
    series: np.ndarray,
    dates: list[str],
    field_ids: list[str],
    *,
    threshold: float = BARE_NDVI_MAX,
    min_composites: int = MIN_BARE_COMPOSITES,
) -> list[dict]:
    """Runs of low-NDVI composites, grouped by field and calendar year."""
    out: list[dict] = []
    for field_index, field_id in enumerate(field_ids):
        row = series[field_index]
        run_start = None
        for date_idx, value in enumerate(row):
            bare = np.isfinite(value) and value < threshold
            if bare and run_start is None:
                run_start = date_idx
            elif not bare and run_start is not None:
                out.extend(
                    _emit(field_id, row, dates, run_start, date_idx - 1, threshold, min_composites)
                )
                run_start = None
        if run_start is not None:
            out.extend(
                _emit(field_id, row, dates, run_start, len(row) - 1, threshold, min_composites)
            )
    return out


def _emit(
    field_id: str,
    row: np.ndarray,
    dates: list[str],
    start_idx: int,
    end_idx: int,
    threshold: float,
    min_composites: int,
) -> list[dict]:
    """One record per (field, year) touched by the run, clipped at year boundaries."""
    count = end_idx - start_idx + 1
    if count < min_composites:
        return []
    records = []
    for year in sorted({dates[i][:4] for i in range(start_idx, end_idx + 1)}):
        idxs = [i for i in range(start_idx, end_idx + 1) if dates[i][:4] == year]
        if len(idxs) < min_composites:
            continue
        values = row[idxs]
        records.append(
            {
                "field_id": field_id,
                "year": int(year),
                "start": dates[idxs[0]],
                "end": dates[idxs[-1]],
                "composites": len(idxs),
                "ndvi_min": round(float(np.nanmin(values)), 3),
                "ndvi_mean": round(float(np.nanmean(values)), 3),
                "source": "MODIS MOD13Q1 NDVI 16-day 250 m (Planetary Computer mirror)",
                "note": f"NDVI < {threshold} on {len(idxs)} consecutive composites",
            }
        )
    return records


def derive_ndvi(cfg: Config) -> Path:
    """data/interim/fields_raw.geojson -> field_ndvi.json + field_bare_periods.csv."""
    import csv

    src = INTERIM / "fields_raw.geojson"
    if not src.exists():
        raise FileNotFoundError(f"{src.name} is missing — run `python -m pipeline fields` first")
    fields = json.loads(src.read_text())["features"]
    field_ids = [f["properties"]["field_id"] for f in fields]
    years = list(range(cfg.crop_years[0], cfg.crop_years[1] + 1))

    series, dates = ndvi_series(fields, cfg, years, progress=True)
    if not dates:
        raise RuntimeError("no MODIS composites could be read")

    series_path = INTERIM / "field_ndvi.json"
    series_path.write_text(
        json.dumps(
            {
                "unit": "NDVI (MOD13Q1 250 m, 16-day composites)",
                "qa_filter": f"VI QA SummaryQA <= {QA_MAX_OK}",
                "dates": dates,
                "fields": {
                    fid: [None if not np.isfinite(v) else round(float(v), 3) for v in series[i]]
                    for i, fid in enumerate(field_ids)
                },
            },
            indent=1,
        )
        + "\n"
    )

    periods = bare_periods(series, dates, field_ids)
    out = INTERIM / "field_bare_periods.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "field_id",
                "year",
                "start",
                "end",
                "composites",
                "ndvi_min",
                "ndvi_mean",
                "source",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(periods)

    print(
        f"[ndvi] {len(dates)} composites {dates[0]}..{dates[-1]}, "
        f"{len(periods)} bare periods over {len(field_ids)} fields -> {out.name}"
    )
    return out
