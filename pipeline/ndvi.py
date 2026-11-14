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

PC = "https://planetarycomputer.microsoft.com/api/stac/v1"
COLLECTION = "modis-13Q1-061"
NDVI_ASSET = "250m_16_days_NDVI"
QA_ASSET = "250m_16_days_VI_Quality"
NDVI_SCALE = 1e-4
NDVI_FILL = -3000
BARE_NDVI_MAX = 0.30
MIN_BARE_COMPOSITES = 2  # one 16-day composite below threshold is weather noise
QA_MAX_OK = 1  # SummaryQA bits 0-1: 0 good, 1 marginal, 2 snow/ice, 3 cloudy

# Signed URLs are reusable for the whole run; re-signing per read is what trips the
# endpoint into transient 404s under bursts.
_SIGNED: dict[str, str] = {}


def _get(url: str, data: bytes | None = None, timeout: float = 120.0) -> dict:
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json", "User-Agent": "FieldShift/0.1"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def search_items(cfg: Config, *, start: str, end: str, limit: int = 500) -> list[dict]:
    """All MOD13Q1 items intersecting the region over [start, end)."""
    query = {
        "collections": [COLLECTION],
        "bbox": list(cfg.region.bbox),
        "datetime": f"{start}/{end}",
        "limit": 100,
    }
    url = f"{PC}/search"
    items: list[dict] = []
    while url and len(items) < limit:
        page = _get(url, data=json.dumps(query).encode() if url == f"{PC}/search" else None)
        items.extend(page.get("features", []))
        url = next(
            (link["href"] for link in page.get("links", []) if link.get("rel") == "next"), None
        )
        if url and "limit" not in url:
            url += "&limit=100"
    return items[:limit]


def item_date(item: dict) -> str:
    """Composite start date. PC leaves properties.datetime null for this collection."""
    props = item["properties"]
    stamp = props.get("datetime") or props.get("start_datetime") or ""
    return stamp[:10]


def sign(href: str, *, retries: int = 4) -> str:
    """SAS-sign an asset URL (anonymous, no account required).

    The signing endpoint intermittently 404s on assets it has just listed, so retry a
    couple of times before treating it as a real failure.
    """
    cached = _SIGNED.get(href)
    if cached:
        return cached
    url = f"{PC}/api/sas/v1/sign?href={urllib.parse.quote(href, safe='')}"
    last: Exception | None = None
    for attempt in range(retries):
        try:
            signed = _get(url)["href"]
            _SIGNED[href] = signed
            return signed
        except urllib.error.HTTPError as err:
            last = err
            if err.code != 404:
                raise
            time.sleep(2.0 * (attempt + 1) ** 2)  # 2 s, 8 s, 18 s
    raise RuntimeError(f"could not sign {href[:80]}") from last


def read_band(url: str, bounds: tuple[float, float, float, float], dtype: str = "int16"):
    """Read just the window covering bounds; returns (array, transform, crs)."""
    from rasterio.windows import from_bounds

    with rasterio.open(url) as src:
        window = from_bounds(*bounds, transform=src.transform)
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


def ndvi_series(
    fields: list[dict], cfg: Config, years: list[int], *, progress: bool = False
) -> tuple[np.ndarray, list[str]]:
    """NDVI per field per 16-day composite. Returns (n_fields x n_dates, date strings)."""
    items = search_items(cfg, start=f"{years[0]}-01-01", end=f"{years[-1]}-12-31")
    items.sort(key=lambda item: item_date(item))
    bounds = cfg.region.bbox

    labels = None
    values = []
    dates = []
    for idx, item in enumerate(items):
        if NDVI_ASSET not in item["assets"]:
            continue
        try:
            ndvi_raw, transform, crs = read_band(sign(item["assets"][NDVI_ASSET]["href"]), bounds)
            qa_raw, _, _ = read_band(sign(item["assets"][QA_ASSET]["href"]), bounds)
        except Exception as err:  # noqa: BLE001 - one bad composite must not kill the run
            print(f"[ndvi] skip {item['id']}: {type(err).__name__}")
            continue
        if labels is None:
            from rasterio.warp import transform_geom

            shapes = [
                (transform_geom("EPSG:4326", crs, f["geometry"]), i + 1)
                for i, f in enumerate(fields)
            ]
            labels = rasterize(
                shapes,
                out_shape=ndvi_raw.shape,
                transform=transform,
                fill=0,
                dtype="int32",
            )
        ndvi = np.where(ndvi_raw == NDVI_FILL, np.nan, ndvi_raw * NDVI_SCALE)
        qa = qa_raw & 0b11
        ndvi = np.where(qa <= QA_MAX_OK, ndvi, np.nan)
        values.append(field_means(labels, ndvi, len(fields)))
        dates.append(item_date(item))
        if progress and idx % 50 == 0:
            print(f"[ndvi] {idx}/{len(items)} composites")

    return np.array(values).T, dates  # shape (n_fields, n_dates)


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
