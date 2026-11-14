"""Simplified RUSLE: A = R * K * LS * C * P  [t/ha/yr]. Water erosion only (no wind)."""

from __future__ import annotations

import numpy as np


def rainfall_erosivity(daily_precip_mm: np.ndarray) -> float:
    """Annual R factor [MJ mm / (ha h yr)] from daily precipitation (e.g. a Richardson-type
    daily erosivity model). Placeholder coefficients must be flagged in data_gaps."""
    raise NotImplementedError


def ls_factor(slope_pct: float, slope_length_m: float = 100.0) -> float:
    """LS factor (McCool et al. 1987/1989) from mean slope and an assumed slope length."""
    raise NotImplementedError


def cover_factor(rotation: list[str], bare_fraction: float) -> float:
    """Rotation-average C factor from crop residue and bare-soil fraction of the year."""
    raise NotImplementedError


def rusle_annual(r: float, k: float, ls: float, c: float, p: float = 1.0) -> float:
    """A = R*K*LS*C*P. All factors in SI-consistent units; returns t/ha/yr."""
    return r * k * ls * c * p
