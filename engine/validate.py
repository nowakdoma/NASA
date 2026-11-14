"""Validate contract files: JSON Schema + cross-file semantic checks.

Usage:
    python -m engine.validate                            # contracts/mock/* and web/public/data/*
    python -m engine.validate FIELDS STRATEGIES [GRACE]  # any pair or trio, e.g. web/public/data/*
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from engine import CONTRACTS, WEB_DATA
from engine.crops import load_crop_traits


def _load(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def schema_errors(instance: dict, schema_name: str) -> list[str]:
    schema = _load(CONTRACTS / schema_name)
    validator = Draft202012Validator(schema)
    out = []
    for err in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        out.append(f"{schema_name}: {loc}: {err.message}")
    return out


def semantic_errors(fields: dict, strategies: dict, crop_codes: set[str]) -> list[str]:
    errs: list[str] = []
    first, last = fields.get("years", [0, -1])
    years = {str(y) for y in range(first, last + 1)}
    ids: list[str] = []
    for feat in fields.get("features", []):
        p = feat.get("properties", {})
        fid = p.get("field_id", "?")
        ids.append(fid)
        hist = p.get("crop_history", {})
        if missing := sorted(years - hist.keys()):
            errs.append(f"{fid}: crop_history missing years {missing}")
        if unknown := sorted(set(hist.values()) - crop_codes):
            errs.append(f"{fid}: crop_history uses crops not in crops.csv: {unknown}")
        cal = p.get("season_calendar", {})
        for kind in ("bare_periods", "stress_windows"):
            for w in cal.get(kind, []):
                if w.get("start", "") > w.get("end", ""):
                    errs.append(f"{fid}: {kind} start > end ({w.get('start')} > {w.get('end')})")
    if len(ids) != len(set(ids)):
        errs.append("fields: duplicate field_id")

    sfields = strategies.get("fields", {})
    if set(ids) != set(sfields):
        errs.append(
            f"field ids differ: only in fields={sorted(set(ids) - set(sfields))}, "
            f"only in strategies={sorted(set(sfields) - set(ids))}"
        )
    for fid, strats in sfields.items():
        if sum(bool(s.get("is_current")) for s in strats) != 1:
            errs.append(f"{fid}: need exactly one strategy with is_current=true")
        sids = [s.get("id") for s in strats]
        if len(sids) != len(set(sids)):
            errs.append(f"{fid}: duplicate strategy ids {sids}")
        for s in strats:
            if unknown := sorted(set(s.get("rotation", [])) - crop_codes):
                errs.append(f"{fid}/{s.get('id')}: rotation uses unknown crops {unknown}")
            for m, q in s.get("metrics", {}).items():
                if not q["p10"] <= q["p50"] <= q["p90"]:
                    errs.append(f"{fid}/{s.get('id')}/{m}: quantiles not ordered {q}")
    return errs


def grace_semantic_errors(grace: dict, fields: dict | None = None) -> list[str]:
    """Semantic validation for GRACE / GRACE-FO water storage trend contract."""
    errs: list[str] = []
    series = grace.get("series", [])
    dates = [r.get("date") for r in series if isinstance(r, dict)]
    if dates and dates != sorted(dates):
        errs.append("grace: series dates not strictly chronological")
    if fields is not None:
        county_fips = fields.get("county", {}).get("fips")
        grace_fips = grace.get("region", {}).get("fips")
        if county_fips and grace_fips and county_fips != grace_fips:
            errs.append(f"grace: region fips {grace_fips} != county fips {county_fips}")
    gaps_text = " ".join(grace.get("data_gaps", [])).lower()
    if "total" not in gaps_text or "groundwater" not in gaps_text:
        errs.append("grace: data_gaps must clarify total water storage vs groundwater")
    if "regional" not in gaps_text and "300" not in gaps_text:
        errs.append("grace: data_gaps must clarify regional (~300 km) resolution")
    return errs


def validate_all(
    fields_path: Path,
    strategies_path: Path,
    grace_path: Path | None = None,
) -> list[str]:
    """Return a list of human-readable errors (empty = valid)."""
    try:
        crops = load_crop_traits()
    except ValueError as e:
        return [f"crops.csv: {e}"]
    fields, strategies = _load(fields_path), _load(strategies_path)
    errs = schema_errors(fields, "fields.schema.json")
    errs += schema_errors(strategies, "strategies.schema.json")
    if not errs:  # semantic checks assume schema-valid shapes
        errs += semantic_errors(fields, strategies, set(crops.index))

    # Validate GRACE file if provided or if located in the same directory as fields
    gpath = grace_path
    if gpath is None:
        candidate = fields_path.parent / "grace_water_storage.json"
        if candidate.exists():
            gpath = candidate

    if gpath is not None and gpath.exists():
        grace = _load(gpath)
        g_errs = schema_errors(grace, "grace.schema.json")
        errs += g_errs
        if not g_errs:
            errs += grace_semantic_errors(grace, fields if not errs else None)

    return errs


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) in (2, 3):
        grace = Path(argv[2]) if len(argv) == 3 else None
        pairs = [(Path(argv[0]), Path(argv[1]), grace)]
    elif not argv:
        grace_mock = CONTRACTS / "mock" / "grace_water_storage.json"
        pairs = [
            (
                CONTRACTS / "mock" / "fields.geojson",
                CONTRACTS / "mock" / "strategies.json",
                grace_mock if grace_mock.exists() else None,
            )
        ]
        if (WEB_DATA / "fields.geojson").exists():
            grace_web = WEB_DATA / "grace_water_storage.json"
            pairs.append(
                (
                    WEB_DATA / "fields.geojson",
                    WEB_DATA / "strategies.json",
                    grace_web if grace_web.exists() else None,
                )
            )
    else:
        print(__doc__)
        return 2
    failed = False
    for f, s, g in pairs:
        errs = validate_all(f, s, g)
        file_list = [f.name, s.name]
        candidate_g = g or (f.parent / "grace_water_storage.json")
        if candidate_g.exists():
            file_list.append(candidate_g.name)
        label = f"{f.parent.name}/{{{', '.join(file_list)}}}"
        if errs:
            failed = True
            print(f"FAIL {label}")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"OK   {label}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
