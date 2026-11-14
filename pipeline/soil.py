"""SSURGO soil properties per field via USDA Soil Data Access (SDA).

SDA is a plain JSON-over-HTTP SQL endpoint with no key and no auth, and it accepts WKT
polygons directly, so no map-unit shapefile or geometry library is needed:

    POST https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest
    {"query": "<SQL>", "format": "JSON+COLUMNNAME"}

Notes that cost time to discover, kept here so nobody repeats it:
- ``format`` must be ``JSON+COLUMNNAME`` or rows come back without a header and column
  order silently becomes load-bearing.
- Errors return **XML** with HTTP 400, so a JSON parse without a check explodes on typos.
- ``chorizon`` has no texture column; texture lives in ``chtexturegrp`` (~2 rows per
  horizon — filter ``rvindicator = 'Yes'``).
- ``SDA_Get_Mukey_from_intersection_with_WktWgs84`` takes POLYGON as well as POINT.
- AWC is a *rate* (cm water per cm soil): mm = sum(awc_r * thickness_cm * 10).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from pipeline.config import INTERIM, Config

SDA_URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
# Rooting depth for the profile AWC. 150 cm covers the deepest crop in crops.csv
# (wheat/alfalfa/sunflower at 1.5 m) without crediting water below any crop's roots.
PROFILE_DEPTH_CM = 150.0
SOIL_SOURCE = "USDA NRCS SSURGO via Soil Data Access"

HORIZON_SQL = """
SELECT mu.mukey, mu.muname, c.compname, c.comppct_r, ch.hzdept_r, ch.hzdepb_r,
       ch.om_r, ch.kffact, ch.awc_r, tx.texdesc
FROM mapunit mu
JOIN component c ON c.mukey = mu.mukey
JOIN chorizon ch ON ch.cokey = c.cokey
LEFT JOIN chtexturegrp tx ON tx.chkey = ch.chkey AND tx.rvindicator = 'Yes'
WHERE mu.mukey = '{mukey}'
  AND c.comppct_r = (SELECT MAX(c2.comppct_r) FROM component c2 WHERE c2.mukey = mu.mukey)
ORDER BY ch.hzdept_r
"""

POINT_SQL = (
    "SELECT mukey FROM "
    "SDA_Get_Mukey_from_intersection_with_WktWgs84('POINT({lon:.6f} {lat:.6f})')"
)


class SoilDataError(RuntimeError):
    """SDA returned an error page or an unparseable body."""


def parse_sda_payload(text: str) -> list[dict]:
    """Rows from an SDA response. Raises on the XML error page SDA sends with HTTP 400."""
    stripped = text.lstrip()
    if not stripped.startswith("{"):
        raise SoilDataError(f"SDA returned non-JSON: {text[:200]}")
    table = json.loads(stripped).get("Table", [])
    if not table:
        return []
    header, rows = table[0], table[1:]
    return [dict(zip(header, row, strict=False)) for row in rows]


def wkt_of(geometry: dict) -> str:
    ring = geometry["coordinates"][0]
    pts = ", ".join(f"{x:.6f} {y:.6f}" for x, y in ring)
    return f"POLYGON(({pts}))"


def centroid_of(geometry: dict) -> tuple[float, float]:
    ring = geometry["coordinates"][0][:-1]  # drop the repeated closing vertex
    return (
        sum(p[0] for p in ring) / len(ring),
        sum(p[1] for p in ring) / len(ring),
    )


def _num(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def surface_horizon(rows: list[dict]) -> dict | None:
    """Topmost horizon of the dominant component."""
    if not rows:
        return None
    with_depth = []
    for row in rows:
        depth = _num(row.get("hzdept_r"))
        if depth is not None:
            with_depth.append((depth, row))
    if not with_depth:
        return None
    return min(with_depth, key=lambda item: item[0])[1]


def profile_awc(rows: list[dict], depth_cm: float = PROFILE_DEPTH_CM) -> tuple[float, int]:
    """Available water in mm from the surface down to ``depth_cm``.

    ``awc_r`` is cm of water per cm of soil, so each horizon contributes
    ``awc_r * thickness * 10`` millimetres. Null ``awc_r`` (bedrock, water) is skipped
    and counted — never treated as zero-capacity soil, which would silently dry the field.
    """
    total = 0.0
    skipped = 0
    for row in rows:
        top = _num(row.get("hzdept_r"))
        bottom = _num(row.get("hzdepb_r"))
        awc = _num(row.get("awc_r"))
        if top is None or bottom is None:
            continue
        if top >= depth_cm:
            break
        if awc is None:
            skipped += 1
            continue
        thickness = min(bottom, depth_cm) - top
        if thickness > 0:
            total += awc * thickness * 10.0
    return total, skipped


def normalise_texture(texdesc: str | None) -> str:
    """'Silt loam' -> 'silt loam', matching the lowercase convention used in the mock."""
    if not texdesc:
        return "unknown"
    return texdesc.strip().lower()


def soil_from_rows(rows: list[dict], *, depth_cm: float = PROFILE_DEPTH_CM) -> dict:
    """Soil properties from one map unit's dominant-component horizons."""
    surface = surface_horizon(rows)
    awc_mm, awc_skipped = profile_awc(rows, depth_cm)
    awc_100, _ = profile_awc(rows, 100.0)
    return {
        "map_unit": surface.get("muname") if surface else None,
        "texture": normalise_texture(surface.get("texdesc") if surface else None),
        "om_pct": _num(surface.get("om_r")) if surface else None,
        "kffact": _num(surface.get("kffact")) if surface else None,
        "awc_mm": round(awc_mm, 1),
        "awc_100cm_mm": round(awc_100, 1),
        "component": surface.get("compname") if surface else None,
        "component_pct": _num(surface.get("comppct_r")) if surface else None,
        "awc_null_horizons": awc_skipped,
    }


def sda_query(sql: str, *, timeout: float = 120.0) -> list[dict]:
    """Run one SDA SQL statement and return rows as dicts."""
    import urllib.error
    import urllib.request

    body = json.dumps({"query": sql, "format": "JSON+COLUMNNAME"}).encode()
    request = urllib.request.Request(
        SDA_URL,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return parse_sda_payload(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as err:
        raise SoilDataError(
            f"HTTP {err.code}: {err.read().decode('utf-8', 'replace')[:200]}"
        ) from err


def dominant_mukey(geometry: dict) -> str | None:
    """Map unit under the field centroid (server-side point-in-polygon)."""
    lon, lat = centroid_of(geometry)
    rows = sda_query(POINT_SQL.format(lon=lon, lat=lat))
    return rows[0]["mukey"] if rows else None


def intersection_mukeys(geometry: dict) -> list[str]:
    rows = sda_query(
        "SELECT mukey FROM SDA_Get_Mukey_from_intersection_with_WktWgs84(" f"'{wkt_of(geometry)}')"
    )
    return sorted({row["mukey"] for row in rows})


def horizons_for(mukey: str, cfg: Config, *, force: bool = False) -> list[dict]:
    """Dominant-component horizons for a map unit, cached under data/raw/ssurgo/."""
    from pipeline.config import RAW

    cache = RAW / "ssurgo" / f"horizons_{mukey}.json"
    if cache.exists() and not force:
        return json.loads(cache.read_text())
    rows = sda_query(HORIZON_SQL.format(mukey=mukey))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(rows, indent=1) + "\n")
    return rows


def fetch_ssurgo(cfg: Config, *, force: bool = False) -> Path:
    """Cache the survey area's map units (legend KS055) for the region."""
    from pipeline.config import RAW

    rows = sda_query(
        "SELECT mu.mukey, mu.musym, mu.muname, lg.areasymbol "
        "FROM mapunit mu JOIN legend lg ON lg.lkey = mu.lkey "
        f"WHERE lg.areasymbol = 'KS{cfg.region.fips[2:]}' ORDER BY mu.mukey"
    )
    out = RAW / "ssurgo" / f"mapunits_KS{cfg.region.fips[2:]}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=1) + "\n")
    print(f"[ssurgo] {len(rows)} map units in KS{cfg.region.fips[2:]} -> {out.name}")
    return out


def derive_soil(cfg: Config) -> Path:
    """data/interim/fields_raw.geojson -> data/interim/field_soil.csv (+ SRTM slope)."""
    src = INTERIM / "fields_raw.geojson"
    if not src.exists():
        raise FileNotFoundError(f"{src.name} is missing — run `python -m pipeline fields` first")
    fields = json.loads(src.read_text())["features"]

    terrain_path = INTERIM / "field_terrain.csv"
    terrain = {}
    if terrain_path.exists():
        terrain = {
            row["field_id"]: row for row in csv.DictReader(terrain_path.open(encoding="utf-8"))
        }

    out_rows = []
    for feature in fields:
        fid = feature["properties"]["field_id"]
        geometry = feature["geometry"]
        try:
            mukeys = intersection_mukeys(geometry)
            mukey = dominant_mukey(geometry)
            rows = horizons_for(mukey, cfg) if mukey else []
            soil = soil_from_rows(rows)
        except SoilDataError as err:
            print(f"[ssurgo] {fid}: {err}")
            soil = {"texture": "unknown", "awc_mm": None}
            mukeys, mukey = [], None
        out_rows.append(
            {
                "field_id": fid,
                "mukey": mukey or "",
                "mukeys_intersected": len(mukeys),
                "slope_pct": terrain.get(fid, {}).get("slope_pct", ""),
                "elevation_m": terrain.get(fid, {}).get("elevation_m", ""),
                "source": SOIL_SOURCE,
                **soil,
            }
        )

    out = INTERIM / "field_soil.csv"
    fields_order = [
        "field_id",
        "map_unit",
        "texture",
        "om_pct",
        "kffact",
        "awc_mm",
        "awc_100cm_mm",
        "slope_pct",
        "elevation_m",
        "component",
        "component_pct",
        "mukey",
        "mukeys_intersected",
        "awc_null_horizons",
        "source",
    ]
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields_order, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out_rows)

    textures = {row["texture"] for row in out_rows}
    missing = sum(1 for row in out_rows if not row.get("map_unit"))
    print(
        f"[soil] {len(out_rows)} fields, {len(textures)} texture classes, "
        f"{missing} without a map unit -> {out.name}"
    )
    return out
