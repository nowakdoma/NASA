"""Soil-conditioning index (NRCS SCI-style): proxy for soil organic matter trend.

SCI = 0.4 * OM + 0.4 * FO + 0.2 * ER, each sub-factor in [-1, 1]; > 0 suggests SOM is more
likely to increase than decrease. This is a simplified, uncalibrated version of the NRCS
tool: thresholds below are PLACEHOLDERS.
"""

from __future__ import annotations

import numpy as np

RESIDUE_NEUTRAL_T_HA = 4.0  # mean residue/yr at which OM term = 0 (PLACEHOLDER)
RESIDUE_SCALE_T_HA = 4.0  # +/- this much residue moves OM term by 1


def _clip(x: float) -> float:
    return float(np.clip(x, -1.0, 1.0))


def organic_matter_term(mean_residue_t_ha: float) -> float:
    """OM sub-factor from mean annual residue returned to the soil by the rotation."""
    return _clip((mean_residue_t_ha - RESIDUE_NEUTRAL_T_HA) / RESIDUE_SCALE_T_HA)


def field_operations_term(mean_disturbance: float) -> float:
    """FO sub-factor from mean soil disturbance (0 = none, 1 = intensive tillage every year)."""
    return _clip(1 - 2 * mean_disturbance)


def erosion_term(erosion_t_ha: float, tolerance_t_ha: float) -> float:
    """ER sub-factor: (T - A) / T, i.e. +1 with no erosion, 0 at the tolerable soil loss T."""
    return _clip((tolerance_t_ha - erosion_t_ha) / tolerance_t_ha)


def soil_conditioning_index(om: float, fo: float, er: float) -> float:
    """Combine sub-factors (NRCS weights 0.4 / 0.4 / 0.2)."""
    return 0.4 * om + 0.4 * fo + 0.2 * er
