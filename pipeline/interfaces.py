"""Region-agnostic interfaces. A backend (US: CDL + SSURGO; later e.g. EU: LPIS + SoilGrids)
implements these so engine/ never depends on a specific national dataset."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

# GeoJSON-like geometry dict ({"type": "Polygon", "coordinates": [...]}) in WGS84.
Geometry = dict[str, Any]


@dataclass(frozen=True)
class SoilProperties:
    """Mirrors contracts/fields.schema.json -> soil."""

    texture: str
    om_pct: float
    kffact: float
    awc_mm: float
    slope_pct: float
    map_unit: str | None = None


@runtime_checkable
class CropHistorySource(Protocol):
    def get_crop_history(self, field_geom: Geometry, years: range) -> dict[str, str]:
        """Dominant crop per year as ``{"2008": "corn", ...}`` using crop codes from
        contracts/crops.csv. Years without data are omitted (caller decides)."""
        ...


@runtime_checkable
class SoilSource(Protocol):
    def get_soil(self, field_geom: Geometry) -> SoilProperties:
        """Area-weighted (or dominant-component) soil properties for the field."""
        ...
