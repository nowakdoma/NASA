"""Soil-conditioning index (NRCS SCI-style): proxy for soil organic matter trend.

SCI = w_om * OM + w_fo * FO + w_er * ER, roughly in [-1, 1]; > 0 suggests SOM increasing.
"""

from __future__ import annotations


def organic_matter_term(rotation: list[str], residue_t_ha: dict[str, float]) -> float:
    """OM sub-factor from mean annual residue returned by the rotation."""
    raise NotImplementedError


def field_operations_term(rotation: list[str], tillage: str = "reduced") -> float:
    """FO sub-factor from tillage intensity and number of passes."""
    raise NotImplementedError


def soil_conditioning_index(om: float, fo: float, er: float) -> float:
    """Combine sub-factors (NRCS weights 0.4 / 0.4 / 0.2). ``er`` is an erosion sub-factor."""
    return 0.4 * om + 0.4 * fo + 0.2 * er
