"""Crop trait table loader (contracts/crops.csv)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from engine import CONTRACTS

REQUIRED_COLUMNS = [
    "crop_code",
    "name",
    "cdl_code",
    "family",
    "n_fixing",
    "root_depth_m",
    "kc_ini",
    "kc_mid",
    "kc_end",
    "l_ini_d",
    "l_dev_d",
    "l_mid_d",
    "l_late_d",
    "residue_t_ha",
    "price_source",
    "placeholder",
    "source",
]


def load_crop_traits(path: Path | None = None) -> pd.DataFrame:
    """Load crops.csv indexed by ``crop_code``.

    Booleans (``n_fixing``, ``placeholder``) are parsed from ``true``/``false``.
    Raises ``ValueError`` if a required column is missing or ``crop_code`` is not unique.
    """
    df = pd.read_csv(path or CONTRACTS / "crops.csv", true_values=["true"], false_values=["false"])
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"crops.csv missing columns: {missing}")
    if df["crop_code"].duplicated().any():
        raise ValueError("crops.csv has duplicate crop_code values")
    return df.set_index("crop_code")
