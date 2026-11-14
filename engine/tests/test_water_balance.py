import numpy as np

from engine import params
from engine.crops import load_crop_traits
from engine.strategies import WeatherYears
from engine.water_balance import (
    et0_fao56_pm,
    extraterrestrial_radiation,
    kc_curve,
    rotation_timeline,
    simulate,
)
from engine.weather import synthetic_weather

TRAITS = load_crop_traits()


def _weather_for(rotation, first=2000):
    n = len(rotation)
    wy = WeatherYears.from_daily(synthetic_weather(first, first + n - 1))
    et0 = np.concatenate([wy.et0[y] for y in wy.years])
    precip = np.concatenate([wy.precip[y] for y in wy.years])
    return et0, precip


def test_et0_fao56_example18_brussels():
    et0 = et0_fao56_pm(
        np.array([21.5]),
        np.array([12.3]),
        np.array([73.5]),
        np.array([2.078]),
        np.array([22.07]),
        100.0,
        50.8,
        np.array([187]),
    )
    assert abs(et0[0] - 3.9) < 0.25


def test_extraterrestrial_radiation_example8():
    ra = extraterrestrial_radiation(-20.0, np.array([246]))
    assert abs(ra[0] - 32.2) < 0.2


def test_kc_curve_corn():
    t = TRAITS.loc["corn"]
    kc = kc_curve("corn", params.CROPS["corn"].plant_doy, TRAITS)
    assert kc.shape == (365,)
    lo = min(t.kc_ini, t.kc_end)
    active = kc[kc > 0]
    assert active.size > 0
    assert active.min() >= lo - 1e-9 and active.max() <= t.kc_mid + 1e-9
    assert np.all(kc[:119] == 0)  # before planting (doy 120)
    assert kc[-1] == 0


def test_kc_curve_winter_wheat_wraps():
    kc = kc_curve("winter_wheat", params.CROPS["winter_wheat"].plant_doy, TRAITS)
    assert kc.shape == (365,)
    assert kc[0] > 0 and kc[-1] > 0
    assert np.any(kc == 0)


def test_kc_curve_fallow_is_zero():
    assert np.all(kc_curve("fallow", 1, TRAITS) == 0)


def test_rotation_timeline_shapes_and_fallow():
    rot = ["winter_wheat", "sorghum", "fallow"]
    tl = rotation_timeline(rot, TRAITS)
    assert tl.kc.shape == tl.slot.shape == tl.irrigable.shape == (365 * 3,)
    fallow_year = slice(365 * 2, 365 * 3)
    assert np.all(tl.slot[365 * 2 : 365 * 2 + 250] == -1)
    # fall-sown wheat of year 0 wraps in at the end of the fallow year
    assert tl.slot[fallow_year][-1] == 0
    assert not tl.irrigable[tl.slot == -1].any()


def test_rotation_timeline_non_irrigable_crops():
    tl = rotation_timeline(["rye_cover", "corn"], TRAITS)
    rye = tl.slot == 0
    assert rye.any()
    assert not tl.irrigable[rye].any()
    assert tl.irrigable[tl.slot == 1].any()
    tl2 = rotation_timeline(["fallow", "corn"], TRAITS)
    assert not tl2.irrigable[tl2.slot == 0].any()


def test_simulate_irrigation_caps_and_yield_ratio():
    rot = ["corn", "winter_wheat", "fallow"]
    tl = rotation_timeline(rot, TRAITS)
    et0, precip = _weather_for(rot)
    ky = np.array([params.CROPS[c].ky for c in rot])

    dry = simulate(tl, et0, precip, 150.0, 0.0)
    lim = simulate(tl, et0, precip, 150.0, 150.0)
    full = simulate(tl, et0, precip, 150.0, None)

    assert np.all(dry.irrigation_mm == 0)
    assert np.all(lim.irrigation_mm <= 150.0 + 1e-9)
    assert full.irrigation_mm.sum() >= lim.irrigation_mm.sum()
    assert full.irrigation_mm.sum() > 0
    for res in (dry, lim, full):
        yr = res.yield_ratio(ky)
        assert np.all((yr >= 0) & (yr <= 1))
        assert np.all(res.eta_mm <= res.etc_mm + 1e-9)
        assert np.all(res.deep_perc_mm >= 0)
    # full irrigation should not be more stressed than dryland
    assert full.stress_days.sum() <= dry.stress_days.sum()
