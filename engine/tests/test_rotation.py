import pytest

from engine import params
from engine.crops import load_crop_traits
from engine.rotation import detect_rotation, select_alternatives
from engine.strategies import benefits, derive_soil_health_traits, why_considered


def _history(seq, first=2008, last=2025):
    return {str(y): seq[(y - first) % len(seq)] for y in range(first, last + 1)}


def test_detect_alternating():
    cyc = detect_rotation(_history(["corn", "soybeans"]))
    assert len(cyc) == 2 and set(cyc) == {"corn", "soybeans"}
    # ordered by most recent years: 2025 is last position (2025-2008 = 17 -> soybeans)
    assert cyc[-1] == "soybeans"


def test_detect_constant():
    assert detect_rotation(_history(["corn"])) == ["corn"]


def test_detect_three_cycle():
    cyc = detect_rotation(_history(["winter_wheat", "sorghum", "fallow"]))
    assert len(cyc) == 3 and set(cyc) == {"winter_wheat", "sorghum", "fallow"}


def test_detect_tolerates_one_odd_year():
    h = _history(["corn", "soybeans"])
    h["2020"] = "sorghum"
    assert set(detect_rotation(h)) == {"corn", "soybeans"}


def test_select_alternatives_distinct_and_not_current():
    cur = ["corn", "soybeans"]
    alts = select_alternatives(cur, "full")
    assert len(alts) == 3
    keys = [(e.rotation, lvl) for e, lvl in alts]
    assert len(set(keys)) == 3
    assert (tuple(cur), "full") not in keys


def test_select_alternatives_excludes_catalogue_twin_of_current():
    e = next(c for c in params.CATALOGUE if c.id == "wsf_limited")
    alts = select_alternatives(list(e.rotation), "limited")
    assert all((x.rotation, lvl) != (e.rotation, "limited") for x, lvl in alts)


def test_select_alternatives_dryland_field():
    alts = select_alternatives(["winter_wheat", "fallow"], "dryland", irrigated=False)
    assert len(alts) == 3
    assert all(lvl == "dryland" for _, lvl in alts)
    keys = [(e.rotation, lvl) for e, lvl in alts]
    assert len(set(keys)) == 3


def test_detect_rotation_empty_history_raises():
    with pytest.raises(ValueError, match="empty crop_history"):
        detect_rotation({})


def test_strategy_why_benefits_soil_traits():
    traits = load_crop_traits()

    # Monoculture corn
    traits_corn = derive_soil_health_traits(["corn"], traits)
    assert traits_corn["n_fixing_years"] == 0
    assert traits_corn["pest_break"] is False
    assert traits_corn["forage"] is False

    # Alfalfa (forage, n-fixing, 2 families with corn)
    traits_alfalfa = derive_soil_health_traits(["alfalfa", "alfalfa", "corn"], traits)
    assert traits_alfalfa["n_fixing_years"] == 2
    assert traits_alfalfa["pest_break"] is True
    assert traits_alfalfa["forage"] is True

    # Why considered
    props = {
        "soil": {"texture": "silt loam", "awc_mm": 180, "kffact": 0.37, "slope_pct": 0.5},
        "crop_history": {"2024": "corn", "2025": "corn"},
    }
    why_cur = why_considered(["corn"], "full", True, props, traits)
    assert "baseline" in why_cur and "silt loam" in why_cur

    why_alt = why_considered(
        ["sorghum", "winter_wheat", "rye_cover"], "limited", False, props, traits
    )
    assert "cereal rye" in why_alt or "erosion" in why_alt

    # Benefits
    alt_m = {
        "water_use_mm": {"p50": 180},
        "erosion_t_ha": {"p50": 1.2},
        "income_usd_ha": {"p50": 320},
        "labour_index": {"p50": 0.3},
        "soil_index": {"p50": 0.4},
    }
    cur_m = {
        "water_use_mm": {"p50": 420},
        "erosion_t_ha": {"p50": 2.5},
        "income_usd_ha": {"p50": 350},
        "labour_index": {"p50": 0.5},
        "soil_index": {"p50": 0.1},
    }
    bens = benefits(
        ["sorghum", "winter_wheat", "rye_cover"],
        "limited",
        False,
        alt_m,
        cur_m,
        traits,
        derive_soil_health_traits(["sorghum", "winter_wheat", "rye_cover"], traits),
        current_rotation=["corn"],
    )
    assert 2 <= len(bens) <= 3
    assert any("water savings" in b or "irrigation" in b for b in bens)

    # Contradiction check: higher erosion than baseline must never claim lower water erosion
    alt_higher_erosion = {
        "water_use_mm": {"p50": 0.0},
        "erosion_t_ha": {"p50": 0.63},  # higher than cur_m (0.50)
        "income_usd_ha": {"p50": 120},
        "labour_index": {"p50": 0.15},
        "soil_index": {"p50": -0.1},
    }
    cur_baseline = {
        "water_use_mm": {"p50": 380},
        "erosion_t_ha": {"p50": 0.50},
        "income_usd_ha": {"p50": 350},
        "labour_index": {"p50": 0.40},
        "soil_index": {"p50": 0.10},
    }
    bens_dryland = benefits(
        ["winter_wheat", "sorghum", "fallow"],
        "dryland",
        False,
        alt_higher_erosion,
        cur_baseline,
        traits,
        derive_soil_health_traits(["winter_wheat", "sorghum", "fallow"], traits),
        current_rotation=["corn"],
    )
    assert 2 <= len(bens_dryland) <= 3
    assert not any("erosion" in b.lower() and "less" in b.lower() for b in bens_dryland)
    assert not any("low water erosion" in b.lower() for b in bens_dryland)


def test_rye_cover_traits_and_tradeoffs():
    from engine.strategies import verify_locally

    traits = load_crop_traits()
    # E4: rye_cover must NOT be marked as forage
    sht_rye = derive_soil_health_traits(["sorghum", "winter_wheat", "rye_cover"], traits)
    assert sht_rye["forage"] is False

    cur_m = {
        "water_use_mm": {"p50": 350.0},
        "erosion_t_ha": {"p50": 0.25},
        "income_usd_ha": {"p50": 800.0},
        "labour_index": {"p50": 0.40},
        "soil_index": {"p50": 0.50},
    }
    # Case 1: alternative erosion is higher than baseline -> cannot claim wind erosion shielding
    alt_m_higher_er = {
        "water_use_mm": {"p50": 100.0},
        "erosion_t_ha": {"p50": 0.45},
        "income_usd_ha": {"p50": 200.0},
        "labour_index": {"p50": 0.20},
        "soil_index": {"p50": 0.40},
    }
    bens = benefits(
        ["sorghum", "winter_wheat", "rye_cover"],
        "limited",
        False,
        alt_m_higher_er,
        cur_m,
        traits,
        sht_rye,
        current_rotation=["corn"],
    )
    assert not any("wind erosion" in b.lower() for b in bens)
    assert any("root biomass" in b.lower() for b in bens)

    # E5: verify_locally trade-offs
    checks = verify_locally(
        ["sorghum", "winter_wheat", "rye_cover"],
        "limited",
        metrics=alt_m_higher_er,
        current_metrics=cur_m,
    )
    assert any("modelled water erosion" in c.lower() for c in checks)
    assert any("median net return is lower" in c.lower() for c in checks)
