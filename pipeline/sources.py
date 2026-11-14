"""One function per dataset. Each writes to data/raw/<name>/ and is idempotent.
Scaffold: all stubs; nothing downloads yet."""

from __future__ import annotations

from pipeline.config import Config


def fetch_power(cfg: Config) -> None:
    """NASA POWER daily point data (T2M, T2M_MAX, T2M_MIN, RH2M, WS2M, ALLSKY_SFC_SW_DWN,
    PRECTOTCORR) for the region centroid, cfg.weather_years. No login needed."""
    raise NotImplementedError


def fetch_ndvi(cfg: Config) -> None:
    """MODIS MOD13Q1 250 m 16-day NDVI (Earthdata login) -> bare-soil periods."""
    raise NotImplementedError


def fetch_smap(cfg: Config) -> None:
    """SMAP L3 enhanced soil moisture SPL3SMP_E (Earthdata) -> water-stress windows."""
    raise NotImplementedError


def fetch_srtm(cfg: Config) -> None:
    """SRTM GL1 30 m DEM (Earthdata) -> slope per field."""
    raise NotImplementedError


def fetch_cdl(cfg: Config) -> None:
    """USDA CDL 2008-2025 clipped to cfg.region.bbox."""
    raise NotImplementedError


def fetch_ssurgo(cfg: Config) -> None:
    """SSURGO map units + component/horizon tables for the county."""
    raise NotImplementedError


SOURCES = {
    "power": fetch_power,
    "ndvi": fetch_ndvi,
    "smap": fetch_smap,
    "srtm": fetch_srtm,
    "cdl": fetch_cdl,
    "ssurgo": fetch_ssurgo,
}
