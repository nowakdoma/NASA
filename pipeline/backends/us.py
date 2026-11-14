"""US backend: USDA NASS Cropland Data Layer + USDA NRCS SSURGO (+ SRTM slope)."""

from __future__ import annotations

from pipeline.interfaces import Geometry, SoilProperties

# CDL raster value -> crops.csv crop_code (extend as needed; keep in sync with crops.csv)
CDL_TO_CROP = {
    1: "corn",
    2: "cotton",
    4: "sorghum",
    5: "soybeans",
    6: "sunflower",
    24: "winter_wheat",
    27: "rye_cover",
    36: "alfalfa",
    61: "fallow",
    176: "grass_pasture",
}


class CdlCropHistory:
    """Crop history from CDL rasters in data/raw/cdl/ (one GeoTIFF per year)."""

    def get_crop_history(self, field_geom: Geometry, years: range) -> dict[str, str]:
        raise NotImplementedError("CDL zonal majority per field: TODO (person 2)")


class SsurgoSoil:
    """Soil properties from SSURGO (gSSURGO / Soil Data Access) + SRTM slope."""

    def get_soil(self, field_geom: Geometry) -> SoilProperties:
        raise NotImplementedError("SSURGO + SRTM per field: TODO (person 2)")
