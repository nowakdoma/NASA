import numpy as np
import pytest

from engine import params
from engine.erosion import k_factor_si, ls_factor, r_factor_by_year, rusle_annual
from engine.soil_index import (
    erosion_term,
    field_operations_term,
    organic_matter_term,
    soil_conditioning_index,
)
from engine.weather import synthetic_weather


def test_ls_factor_increases_with_slope():
    vals = [ls_factor(s) for s in (0.5, 1, 2, 4, 6, 8, 12, 16)]
    assert all(b > a for a, b in zip(vals, vals[1:], strict=False))


def test_ls_factor_increases_with_length():
    assert ls_factor(3, 200) > ls_factor(3, 50)


def test_r_factor_mean_matches_params():
    w = synthetic_weather(2000, 2009)
    r = r_factor_by_year(w["PRECTOTCORR"])
    assert sorted(r) == list(range(2000, 2010))
    assert np.isclose(np.mean(list(r.values())), params.R_MEAN_SI, rtol=1e-9)


def test_k_factor_si():
    assert k_factor_si(0.43) == pytest.approx(0.0566, abs=1e-4)


def test_rusle_is_product():
    assert rusle_annual(2, 3, 4, 5) == 120
    assert rusle_annual(2, 3, 4, 5, 0.5) == 60


def test_erosion_term_anchors():
    t = params.SOIL_LOSS_TOLERANCE_T_HA
    assert erosion_term(0, t) == 1
    assert erosion_term(t, t) == 0
    assert erosion_term(100 * t, t) == -1


def test_sci_terms_clipped():
    for x in (-50.0, 0.0, 4.0, 50.0):
        assert -1 <= organic_matter_term(x) <= 1
    for x in (-5.0, 0.0, 0.5, 5.0):
        assert -1 <= field_operations_term(x) <= 1
    assert organic_matter_term(1e6) == 1 and organic_matter_term(-1e6) == -1


def test_sci_weights():
    assert soil_conditioning_index(1, 1, 1) == pytest.approx(1.0)
    assert soil_conditioning_index(-1, -1, -1) == pytest.approx(-1.0)
    assert soil_conditioning_index(1, 0, 0) == pytest.approx(0.4)
    assert soil_conditioning_index(0, 0, 1) == pytest.approx(0.2)
