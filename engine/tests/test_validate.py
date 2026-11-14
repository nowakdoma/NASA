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


def _grace_mock():
    return json.loads((MOCK / "grace_water_storage.json").read_text())


def test_grace_mock_is_valid():
    fields, strategies = _mocks()
    assert validate_all(MOCK / "fields.geojson", MOCK / "strategies.json") == []


def test_grace_schema_violation_detected(tmp_path):
    fields, strategies = _mocks()
    f, s = _write(tmp_path, fields, strategies)
    grace = _grace_mock()
    grace["trend"]["r2"] = 1.5  # must be <= 1
    g = tmp_path / "grace_water_storage.json"
    g.write_text(json.dumps(grace))
    errs = validate_all(f, s, g)
    assert any("r2" in e or "grace.schema.json" in e for e in errs)


def test_grace_dates_not_chronological_detected(tmp_path):
    fields, strategies = _mocks()
    f, s = _write(tmp_path, fields, strategies)
    grace = _grace_mock()
    # swap first two series items to violate chronological order
    grace["series"][0], grace["series"][1] = grace["series"][1], grace["series"][0]
    g = tmp_path / "grace_water_storage.json"
    g.write_text(json.dumps(grace))
    errs = validate_all(f, s, g)
    assert any("chronological" in e for e in errs)


def test_grace_duplicate_dates_detected(tmp_path):
    fields, strategies = _mocks()
    f, s = _write(tmp_path, fields, strategies)
    grace = _grace_mock()
    grace["series"][1]["date"] = grace["series"][0]["date"]
    g = tmp_path / "grace_water_storage.json"
    g.write_text(json.dumps(grace))
    errs = validate_all(f, s, g)
    assert any("duplicate dates" in e or "chronological" in e for e in errs)


def test_grace_fips_mismatch_detected(tmp_path):
    fields, strategies = _mocks()
    f, s = _write(tmp_path, fields, strategies)
    grace = _grace_mock()
    grace["region"]["fips"] = "99999"
    g = tmp_path / "grace_water_storage.json"
    g.write_text(json.dumps(grace))
    errs = validate_all(f, s, g)
    assert any("fips" in e for e in errs)


def test_grace_data_gaps_explanation_detected(tmp_path):
    fields, strategies = _mocks()
    f, s = _write(tmp_path, fields, strategies)
    grace = _grace_mock()
    grace["data_gaps"] = ["Generic note without required context."]
    g = tmp_path / "grace_water_storage.json"
    g.write_text(json.dumps(grace))
    errs = validate_all(f, s, g)
    assert any("total water storage" in e or "data_gaps" in e for e in errs)
