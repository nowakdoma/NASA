"""Export engine results to contracts format in web/public/data/.

    python -m engine.export           # run the engine (fields + weather -> strategies.json)
    python -m engine.export --mock    # just copy the validated contracts/mock/* files

Inputs:
- fields: ``data/interim/fields.geojson`` (contracts/fields.schema.json, written by pipeline/),
  falling back to ``contracts/mock/fields.geojson``;
- weather: ``data/interim/power_daily.csv`` (see engine.weather), falling back to SYNTHETIC.
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

from engine import CONTRACTS, REPO_ROOT, WEB_DATA
from engine.crops import load_crop_traits
from engine.strategies import WeatherYears, field_strategies
from engine.validate import validate_all
from engine.weather import get_weather

FILES = ("fields.geojson", "strategies.json")
INTERIM_FIELDS = REPO_ROOT / "data" / "interim" / "fields.geojson"
WEATHER_YEARS = (1995, 2025)
SCHEMA_VERSION = "0.1"


def export_mock(out_dir: Path = WEB_DATA) -> None:
    """Validate the mocks and copy them to web/public/data."""
    errors = validate_all(CONTRACTS / "mock" / FILES[0], CONTRACTS / "mock" / FILES[1])
    if errors:
        raise SystemExit("mock data invalid:\n" + "\n".join(errors))
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copyfile(CONTRACTS / "mock" / name, out_dir / name)
        print(f"exported {name} -> {out_dir / name}")


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
    for feat in fields["features"]:
        props = feat["properties"]
        per_field[props["field_id"]] = field_strategies(props, wy, traits, synthetic, WEATHER_YEARS)
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
    src = fields_path or (INTERIM_FIELDS if INTERIM_FIELDS.exists() else mock_fields)
    print(f"fields: {src.relative_to(REPO_ROOT) if src.is_relative_to(REPO_ROOT) else src}")
    fields, strategies = build(src)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / FILES[0]).write_text(json.dumps(fields, ensure_ascii=False, indent=1) + "\n")
    (out_dir / FILES[1]).write_text(json.dumps(strategies, ensure_ascii=False, indent=1) + "\n")
    errors = validate_all(out_dir / FILES[0], out_dir / FILES[1])
    status = "INVALID" if errors else "valid"
    print(f"exported {FILES} -> {out_dir} ({status}, mock={strategies['mock']})")
    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m engine.export", description=__doc__)
    ap.add_argument("--mock", action="store_true", help="copy contracts/mock/* instead")
    ap.add_argument("--out", type=Path, default=WEB_DATA)
    args = ap.parse_args(argv)
    if args.mock:
        export_mock(args.out)
        return 0
    errors = export(args.out)
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
