"""Export engine results to contracts format in web/public/data/.

    python -m engine.export           # run the engine (fields + weather -> strategies.json)
    python -m engine.export --mock    # just copy the validated contracts/mock/* files

Inputs:
- fields: ``data/interim/fields.geojson`` (contracts/fields.schema.json, written by pipeline/),
  falling back to ``contracts/mock/fields.geojson``;
- weather: ``data/interim/weather_daily.csv`` (pipeline power; see engine.weather), else SYNTHETIC.
Anything built on a fallback is written with ``"mock": true``.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

from engine import CONTRACTS, REPO_ROOT, WEB_DATA, params
from engine.crops import load_crop_traits
from engine.strategies import WeatherYears, field_strategies
from engine.validate import validate_all
from engine.weather import get_weather

FILES = ("fields.geojson", "strategies.json")
GRACE_FILE = "grace_water_storage.json"
INTERIM_FIELDS = REPO_ROOT / "data" / "interim" / "fields.geojson"
INTERIM_GRACE = REPO_ROOT / "data" / "interim" / GRACE_FILE
MOCK_GRACE = CONTRACTS / "mock" / GRACE_FILE
WEATHER_YEARS = (1995, 2025)
SCHEMA_VERSION = "0.3"


def export_mock(out_dir: Path = WEB_DATA) -> None:
    """Validate the mocks and copy them to web/public/data."""
    all_mock_files = [
        CONTRACTS / "mock" / name
        for name in (*FILES, GRACE_FILE)
        if (CONTRACTS / "mock" / name).exists()
    ]
    grace_mock = MOCK_GRACE if MOCK_GRACE.exists() else None
    errors = validate_all(CONTRACTS / "mock" / FILES[0], CONTRACTS / "mock" / FILES[1], grace_mock)
    if errors:
        raise SystemExit("mock data invalid:\n" + "\n".join(errors))
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in all_mock_files:
        shutil.copyfile(src, out_dir / src.name)
        print(f"exported {src.name} -> {out_dir / src.name}")


def _git_rev() -> str:
    try:
        rev = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return rev.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def build(fields_path: Path, weather_path: Path | None = None) -> tuple[dict, dict]:
    """Run the engine. Returns (fields GeoJSON, strategies JSON) in contracts format."""
    fields = json.loads(fields_path.read_text(encoding="utf-8"))
    kwargs = {"path": weather_path} if weather_path else {}
    weather, synthetic = get_weather(*WEATHER_YEARS, **kwargs)
    wy = WeatherYears.from_daily(weather)
    traits = load_crop_traits()
    mock = synthetic or bool(fields.get("mock", False))

    per_field = {}
    cache: dict = {}  # identical (rotation, irrigation, soil) -> metrics
    # The engine can only model crops it has parameters for (engine/params.py). A crop that
    # exists in contracts/crops.csv but not in params must not crash the export, and must not
    # be silently kept either — its metrics would be invented. Such fields are excluded and
    # reported, so fields and strategies stay consistent for the contract validator.
    modelled = set(params.CROPS)
    supported, unsupported = [], []
    for feat in fields["features"]:
        codes = set(feat["properties"]["crop_history"].values())
        (supported if codes <= modelled else unsupported).append(feat)
    if unsupported:
        missing = sorted(
            {c for feat in unsupported for c in feat["properties"]["crop_history"].values()}
            - modelled
        )
        print(
            f"  skipped {len(unsupported)} field(s): no engine parameters for {missing} "
            f"(add them to engine/params.py to include these fields)"
        )
    fields["features"] = supported
    fields["schema_version"] = SCHEMA_VERSION

    for feat in fields["features"]:
        props = feat["properties"]
        per_field[props["field_id"]] = field_strategies(
            props, wy, traits, synthetic, WEATHER_YEARS, cache
        )
        print(f"  {props['field_id']}: {[s['id'] for s in per_field[props['field_id']]]}")

    meta_src = json.loads((CONTRACTS / "mock" / "strategies.json").read_text(encoding="utf-8"))
    strategies = {
        "schema_version": SCHEMA_VERSION,
        "mock": mock,
        "generated_by": f"engine.export {_git_rev()}"
        + (" (SYNTHETIC weather)" if synthetic else "")
        + (" (mock fields)" if fields.get("mock") else ""),
        "generated_at": dt.date.today().isoformat(),
        "weather_years": list(WEATHER_YEARS),
        "metric_meta": copy.deepcopy(meta_src["metric_meta"]),
        "fields": per_field,
    }
    return fields, strategies


def export(out_dir: Path = WEB_DATA, fields_path: Path | None = None) -> list[str]:
    """Build, write and validate. Returns validation errors (empty = OK)."""
    mock_fields = CONTRACTS / "mock" / FILES[0]
    if fields_path:
        src = fields_path
    elif INTERIM_FIELDS.exists():
        src = INTERIM_FIELDS
    elif (out_dir / FILES[0]).exists() and not json.loads(
        (out_dir / FILES[0]).read_text(encoding="utf-8")
    ).get("mock", False):
        src = out_dir / FILES[0]
    else:
        src = mock_fields
    print(f"fields: {src.relative_to(REPO_ROOT) if src.is_relative_to(REPO_ROOT) else src}")
    fields, strategies = build(src)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / FILES[0]).write_text(
        json.dumps(fields, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (out_dir / FILES[1]).write_text(
        json.dumps(strategies, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    if INTERIM_GRACE.exists():
        shutil.copyfile(INTERIM_GRACE, out_dir / GRACE_FILE)
        print(f"copied {INTERIM_GRACE.relative_to(REPO_ROOT)} -> {out_dir / GRACE_FILE}")
    elif MOCK_GRACE.exists() and not (out_dir / GRACE_FILE).exists():
        shutil.copyfile(MOCK_GRACE, out_dir / GRACE_FILE)
        print(f"copied {MOCK_GRACE.relative_to(REPO_ROOT)} (fallback) -> {out_dir / GRACE_FILE}")

    grace_path = out_dir / GRACE_FILE if (out_dir / GRACE_FILE).exists() else None
    errors = validate_all(out_dir / FILES[0], out_dir / FILES[1], grace_path)
    status = "INVALID" if errors else "valid"
    exported_files = list(FILES) + ([GRACE_FILE] if grace_path else [])
    print(f"exported {tuple(exported_files)} -> {out_dir} ({status}, mock={strategies['mock']})")
    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m engine.export", description=__doc__)
    ap.add_argument("--mock", action="store_true", help="copy contracts/mock/* instead")
    ap.add_argument("--fields", type=Path, default=None, help="path to input fields.geojson")
    ap.add_argument("--out", type=Path, default=WEB_DATA)
    args = ap.parse_args(argv)
    if args.mock:
        export_mock(args.out)
        return 0
    errors = export(args.out, fields_path=args.fields)
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
