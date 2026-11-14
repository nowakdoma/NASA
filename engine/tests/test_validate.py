import copy
import json

from engine import CONTRACTS
from engine.validate import validate_all

MOCK = CONTRACTS / "mock"


def _write(tmp_path, fields, strategies):
    f, s = tmp_path / "fields.geojson", tmp_path / "strategies.json"
    f.write_text(json.dumps(fields))
    s.write_text(json.dumps(strategies))
    return f, s


def _mocks():
    return (
        json.loads((MOCK / "fields.geojson").read_text()),
        json.loads((MOCK / "strategies.json").read_text()),
    )


def test_mocks_are_valid():
    assert validate_all(MOCK / "fields.geojson", MOCK / "strategies.json") == []


def test_schema_violation_detected(tmp_path):
    fields, strategies = _mocks()
    del fields["features"][0]["properties"]["soil"]["om_pct"]
    assert any("om_pct" in e for e in validate_all(*_write(tmp_path, fields, strategies)))


def test_unordered_quantiles_detected(tmp_path):
    fields, strategies = _mocks()
    s = copy.deepcopy(strategies)
    first = next(iter(s["fields"].values()))[0]["metrics"]["income_usd_ha"]
    first["p10"], first["p90"] = first["p90"], first["p10"]
    assert any("quantiles not ordered" in e for e in validate_all(*_write(tmp_path, fields, s)))


def test_unknown_crop_detected(tmp_path):
    fields, strategies = _mocks()
    fields["features"][0]["properties"]["crop_history"]["2010"] = "kale"
    assert any("not in crops.csv" in e for e in validate_all(*_write(tmp_path, fields, strategies)))


def test_missing_strategy_field_detected(tmp_path):
    fields, strategies = _mocks()
    strategies["fields"].pop(next(iter(strategies["fields"])))
    assert any("field ids differ" in e for e in validate_all(*_write(tmp_path, fields, strategies)))
