import json

import pytest

from engine.export import FILES, export
from engine.weather import COLUMNS, POWER_DAILY, load_power_daily


@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    if POWER_DAILY.exists():
        pytest.skip("real power_daily.csv present; mock assumptions do not hold")
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


def _write_csv(path, rows, columns):
    lines = ["DATE," + ",".join(columns)]
    for d, vals in rows:
        lines.append(d + "," + ",".join(str(v) for v in vals))
    path.write_text("\n".join(lines) + "\n")


def test_load_power_daily_ok(tmp_path):
    p = tmp_path / "ok.csv"
    _write_csv(p, [("2020-01-01", [1] * 6), ("2020-01-02", [2] * 6)], COLUMNS)
    df = load_power_daily(p)
    assert list(df.columns) == COLUMNS and len(df) == 2


def test_load_power_daily_missing_column(tmp_path):
    p = tmp_path / "bad.csv"
    _write_csv(p, [("2020-01-01", [1] * 5)], COLUMNS[:-1])
    with pytest.raises(ValueError, match="missing columns"):
        load_power_daily(p)


def test_load_power_daily_fill_value(tmp_path):
    p = tmp_path / "fill.csv"
    _write_csv(p, [("2020-01-01", [1] * 6), ("2020-01-02", [-999, 1, 1, 1, 1, 1])], COLUMNS)
    with pytest.raises(ValueError, match="-999"):
        load_power_daily(p)


def test_load_power_daily_gap(tmp_path):
    p = tmp_path / "gap.csv"
    _write_csv(p, [("2020-01-01", [1] * 6), ("2020-01-04", [1] * 6)], COLUMNS)
    with pytest.raises(ValueError, match="missing days"):
        load_power_daily(p)
