import pytest

from engine import params
from engine.rotation import detect_rotation, select_alternatives


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
