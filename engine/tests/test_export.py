import json

import pytest

from engine.export import FILES, export
from engine.weather import MAX_GAP_DAYS, PIPELINE_COLUMNS, WEATHER_DAILY, load_weather_daily


@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    if WEATHER_DAILY.exists():
        pytest.skip("real weather_daily.csv present; mock assumptions do not hold")
    out = tmp_path_factory.mktemp("export")
    errors = export(out_dir=out)
    return out, errors


def test_export_valid_and_files_written(exported):
    out, errors = exported
    assert errors == []
    for name in FILES:
        assert (out / name).exists()


def test_export_strategies_structure(exported):
    out, _ = exported
    s = json.loads((out / "strategies.json").read_text())
    assert s["mock"] is True
    assert s["fields"]
    for strategies in s["fields"].values():
        assert len(strategies) == 4
        assert sum(x["is_current"] for x in strategies) == 1
        assert len({x["id"] for x in strategies}) == 4
        for x in strategies:
            assert x["data_gaps"]
            for q in x["metrics"].values():
                assert q["p10"] <= q["p50"] <= q["p90"]


PIPE_COLS = list(PIPELINE_COLUMNS)


def _write_csv(path, rows, columns=PIPE_COLS):
    """Pipeline format: lowercase columns with units, missing values as empty cells."""
    lines = ["date," + ",".join(columns)]
    for d, vals in rows:
        lines.append(d + "," + ",".join("" if v is None else str(v) for v in vals))
    path.write_text("\n".join(lines) + "\n")


def test_load_weather_daily_ok(tmp_path):
    p = tmp_path / "ok.csv"
    _write_csv(p, [("2020-01-01", [1] * 6), ("2020-01-02", [2] * 6)])
    df = load_weather_daily(p)
    assert list(df.columns) == list(PIPELINE_COLUMNS.values()) and len(df) == 2
    assert df.attrs["filled_cells"] == 0


def test_load_weather_daily_missing_column(tmp_path):
    p = tmp_path / "bad.csv"
    _write_csv(p, [("2020-01-01", [1] * 5)], PIPE_COLS[:-1])
    with pytest.raises(ValueError, match="missing columns"):
        load_weather_daily(p)


def test_load_weather_daily_fills_short_gaps(tmp_path):
    p = tmp_path / "short.csv"
    rows = [
        ("2020-01-01", [1] * 6),
        ("2020-01-02", [None, 1, 1, 1, 1, -999]),  # empty cell + POWER fill value
        ("2020-01-04", [3] * 6),  # 2020-01-03 missing entirely
    ]
    _write_csv(p, rows)
    df = load_weather_daily(p)
    assert len(df) == 4 and not df.isna().any().any()
    assert df.loc["2020-01-03", "T2M_MAX"] == pytest.approx(7 / 3)  # 1 -> _ -> _ -> 3
    assert df.attrs["filled_cells"] == 8  # 2 cells on 01-02 + 6 on 01-03


def test_load_weather_daily_long_gap(tmp_path):
    p = tmp_path / "gap.csv"
    end = f"2020-01-{MAX_GAP_DAYS + 3:02d}"
    _write_csv(p, [("2020-01-01", [1] * 6), (end, [1] * 6)])
    with pytest.raises(ValueError, match="gaps longer"):
        load_weather_daily(p)
