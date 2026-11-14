"""Assemble data/interim/fields.geojson in contracts/fields.schema.json shape.

This is the hand-off to the engine (`make export` reads it). The pipeline never writes to
web/public/data — that is engine.export's job — so this file is the last pipeline step.

Two honesty rules shape the output:

* A field is only emitted if its crop history is complete *and* fully mappable through
  contracts/crops.csv. Years whose CDL class has no crop_code (triticale, double-crop
  rotations) disqualify the field rather than being coerced to "fallow".
* Water-stress windows need SMAP, which is not wired up yet. The file therefore contains
  heat windows only and a heat-derived stress index; the gap is recorded in the sidecar
  `.meta.json`, because the contract has no place for provenance inside the document.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from pipeline.config import INTERIM, Config

SCHEMA_VERSION = "0.1"


def load_soil(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    return {row["field_id"]: row for row in csv.DictReader(path.open(encoding="utf-8"))}


def load_bare_periods(path: Path) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    if not path.exists():
        return grouped
    for row in csv.DictReader(path.open(encoding="utf-8")):
        grouped.setdefault(row["field_id"], []).append(
            {
                "year": int(row["year"]),
                "start": row["start"],
                "end": row["end"],
                "source": row["source"],
                "note": row["note"],
            }
        )
    return grouped


def load_heat_windows(path: Path, years: set[int]) -> list[dict]:
    if not path.exists():
        return []
    windows = []
    for row in csv.DictReader(path.open(encoding="utf-8")):
        if int(row["year"]) not in years:
            continue
        windows.append(
            {
                "year": int(row["year"]),
                "start": row["start"],
                "end": row["end"],
                "type": "heat",
                "severity": float(row["severity"]),
                "source": row["source"],
                "note": f"Tmax peak {row['tmax_peak_c']} C over {row['days']} days",
            }
        )
    return windows


def heat_index_by_year(windows: list[dict]) -> dict[str, float]:
    """Worst heat severity per year — the only stress signal we can defend today."""
    out: dict[str, float] = {}
    for window in windows:
        key = str(window["year"])
        out[key] = max(out.get(key, 0.0), round(window["severity"], 3))
    return out


def _soil_block(row: dict | None) -> dict | None:
    if not row or not row.get("texture") or row["texture"] == "unknown":
        return None
    try:
        return {
            "map_unit": row["map_unit"],
            "texture": row["texture"],
            "om_pct": float(row["om_pct"]),
            "kffact": float(row["kffact"]),
            "awc_mm": float(row["awc_mm"]),
            "slope_pct": float(row["slope_pct"]),
        }
    except (TypeError, ValueError):
        return None


def assemble(cfg: Config) -> tuple[Path, dict]:
    """Build fields.geojson from the interim layers; returns (path, metadata)."""
    raw = json.loads((INTERIM / "fields_raw.geojson").read_text())
    soil = load_soil(INTERIM / "field_soil.csv")
    bare = load_bare_periods(INTERIM / "field_bare_periods.csv")
    years = list(range(cfg.crop_years[0], cfg.crop_years[1] + 1))
    year_keys = {str(y) for y in years}
    heat = load_heat_windows(INTERIM / "heat_stress_windows.csv", set(years))
    stress_index = heat_index_by_year(heat)

    features, dropped = [], []
    for feature in raw["features"]:
        props = feature["properties"]
        history = props["crop_history"]
        fid = props["field_id"]

        missing_years = sorted(year_keys - set(history))
        if missing_years:
            dropped.append(
                {"field_id": fid, "reason": "unmapped CDL year(s)", "years": missing_years}
            )
            continue
        soil_block = _soil_block(soil.get(fid))
        if soil_block is None:
            dropped.append({"field_id": fid, "reason": "no usable SSURGO soil"})
            continue

        features.append(
            {
                "type": "Feature",
                "id": fid,
                "geometry": feature["geometry"],
                "properties": {
                    "field_id": fid,
                    "area_ha": props["area_ha"],
                    "irrigated": bool(props["irrigated"]),
                    "irrigation_type": props.get("irrigation_type", "unknown"),
                    "crop_history": {y: history[y] for y in sorted(history, key=int)},
                    "soil": soil_block,
                    "season_calendar": {
                        "bare_periods": sorted(
                            bare.get(fid, []), key=lambda b: (b["year"], b["start"])
                        ),
                        "stress_windows": heat,
                    },
                    "stress_index_by_year": {
                        y: stress_index.get(y, 0.0) for y in sorted(year_keys)
                    },
                },
            }
        )

    document = {
        "type": "FeatureCollection",
        "schema_version": SCHEMA_VERSION,
        "county": raw["county"],
        "years": [cfg.crop_years[0], cfg.crop_years[1]],
        "features": features,
    }
    out = INTERIM / "fields.geojson"
    out.write_text(json.dumps(document, indent=1) + "\n")

    meta = {
        "produced_by": "pipeline.assemble",
        "schema_version": SCHEMA_VERSION,
        "fields_emitted": len(features),
        "fields_dropped": dropped,
        "layers": {
            "geometry": "CDL-derived centre pivots (pipeline.fields)",
            "crop_history": "CDL majority per year, mapped via contracts/crops.csv",
            "soil": "SSURGO via Soil Data Access (dominant map unit at centroid)",
            "slope_pct": "SRTM GL1 30 m (skadi)",
            "bare_periods": "MODIS MOD13Q1 NDVI < 0.30 (Planetary Computer mirror)",
            "stress_windows": "NASA POWER Tmax >= 35 C, county grid cell",
        },
        "data_gaps": [
            "stress_windows contains HEAT only: SMAP soil moisture is not wired up, so there "
            "are no water-stress windows yet.",
            "stress_index_by_year is the worst heat severity of that year, not a combined "
            "water+heat index. Do not present it as combined.",
            "Weather and heat windows are one POWER grid cell (0.5 x 0.625 deg) for the whole "
            "county, identical for every field.",
            "Bare periods are 16-day composites, so window edges are accurate to about 8 days.",
        ],
    }
    (INTERIM / "fields.geojson.meta.json").write_text(json.dumps(meta, indent=1) + "\n")

    print(
        f"[assemble] {len(features)} fields -> {out.name} "
        f"({len(dropped)} dropped for incomplete/missing data)"
    )
    return out, meta


def derive_fields_contract(cfg: Config) -> Path:
    from pipeline.config import REPO_ROOT

    out, meta = assemble(cfg)
    # Validate against the contract ourselves rather than waiting for engine.export to fail.
    import jsonschema

    schema = json.loads((REPO_ROOT / "contracts" / "fields.schema.json").read_text())
    jsonschema.validate(json.loads(out.read_text()), schema)
    assert meta["fields_emitted"] > 0, "no fields survived assembly"
    print("[assemble] validates against contracts/fields.schema.json")
    return out
