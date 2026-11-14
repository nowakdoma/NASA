"""Static configuration: region, years, paths, credentials (from .env)."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"


@dataclass(frozen=True)
class Region:
    name: str = "Finney County, KS"
    fips: str = "20055"
    bbox: tuple[float, float, float, float] = (-101.103, 37.737, -100.652, 38.264)
    centroid: tuple[float, float] = (-100.874, 38.000)  # lon, lat
    backend: str = "us"  # key into pipeline.backends.REGISTRY


@dataclass(frozen=True)
class Config:
    region: Region = field(default_factory=Region)
    crop_years: tuple[int, int] = (2008, 2025)
    weather_years: tuple[int, int] = (1995, 2025)


def load_env(path: Path = REPO_ROOT / ".env") -> None:
    """Minimal .env reader (KEY=VALUE lines) into os.environ; never logs values."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def earthdata_credentials() -> tuple[str, str]:
    """Return (username, password) from env; raise if missing."""
    load_env()
    user, pwd = os.environ.get("EARTHDATA_USERNAME"), os.environ.get("EARTHDATA_PASSWORD")
    if not user or not pwd:
        raise RuntimeError("EARTHDATA_USERNAME / EARTHDATA_PASSWORD not set (see .env.example)")
    return user, pwd


def earthdata_token() -> str | None:
    """Personal Access Token from ``EARTHDATA_TOKEN``, or None.

    Prefer this over username/password: EDL tokens authenticate against Earthdata
    Cloud protected buckets (LP DAAC MOD13Q1, SRTMGL1), where HTTP Basic returns 401.
    Tokens also survive 2FA on the account.
    """
    load_env()
    token = (os.environ.get("EARTHDATA_TOKEN") or "").strip()
    return token or None


def earthdata_auth_header() -> dict[str, str]:
    """``Authorization`` header for Earthdata requests: Bearer, else Basic.

    Bearer (token) covers every DAAC we use. Basic works for NSIDC SMAP and GES DISC
    but is rejected by the LP DAAC cloud buckets, so it is only the fallback.
    """
    token = earthdata_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    user, pwd = earthdata_credentials()
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{pwd}".encode()).decode()}
