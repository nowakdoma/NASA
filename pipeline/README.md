# pipeline/ — NASA data acquisition and derivation

Owner: person 2. Everything here writes to `data/` (gitignored) and hands off
`data/interim/fields.geojson` to `engine/`.

## The chain

Order matters — each step consumes the previous one's output.

```bash
uv run python -m pipeline power      # NASA POWER daily weather, 1995-2025
uv run python -m pipeline cdl        # USDA CDL county GeoTIFFs, 2008-2025
uv run python -m pipeline fields     # centre-pivot detection + crop history
uv run python -m pipeline srtm       # SRTM 30 m tiles (public, no login)
uv run python -m pipeline terrain    # slope + elevation per field
uv run python -m pipeline ssurgo     # SSURGO map units for the county
uv run python -m pipeline soil       # texture, OM, K, AWC per field
uv run python -m pipeline heat       # heat-stress windows from POWER Tmax
uv run python -m pipeline ndvi       # bare-soil periods from MODIS MOD13Q1
uv run python -m pipeline assemble   # contract-shaped fields.geojson
```

`make data` runs all of them; `make export` then hands the result to the web app.
Every step is idempotent: downloads skip existing files, SSURGO horizons are cached
per map unit, and NDVI composites are cached per date, so an interrupted run resumes.

## Outputs (all in `data/interim/`)

| File | Contents |
| --- | --- |
| `weather_daily.csv` + `.meta.json` | one row per day, unit-suffixed columns, missing days reported |
| `fields_raw.geojson` | 60 detected pivots + 18-year crop history + quality flags |
| `field_terrain.csv` | mean slope % and elevation per field (SRTM) |
| `field_soil.csv` | texture, OM %, K factor, AWC (SSURGO) + slope joined in |
| `heat_stress_windows.csv` | Tmax ≥ 35 °C runs, county-wide |
| `field_ndvi.json`, `field_bare_periods.csv` | NDVI series and bare windows per field |
| `fields.geojson` + `.meta.json` | **the hand-off**: validates against `contracts/fields.schema.json` |

## Rules this package follows

- Nothing is presented as measured when it is not: `-999` sentinels become empty cells,
  null `awc_r` horizons are counted not zeroed, unmapped CDL classes are reported raw.
- Weather and heat windows are one POWER grid cell (0.5 × 0.625°) for the whole county.
  They are identical for every field and must be described as county-scale.
- A field is only written to `fields.geojson` if its crop history is complete and every
  year maps to a `crops.csv` code. Anything else is dropped and listed in the sidecar.

## Access notes (learned the hard way)

| Source | Access |
| --- | --- |
| POWER | public, no key |
| CDL | public, no key (`nassgeodata` byfips GeoTIFF per year) |
| SRTM | public `elevation-tiles-prod` skadi bucket, no login |
| SSURGO | public Soil Data Access JSON (POST SQL) |
| MODIS NDVI | Planetary Computer COGs + anonymous SAS signing |
| NSIDC SMAP | Earthdata login — not used, see TASKS |

`rasterio`'s bundled GDAL has **no HDF4 or HDF5 driver**, so MOD13Q1 `.hdf` and SMAP
`.h5` cannot be opened with it at all. NDVI therefore reads the Planetary Computer's
COG mirror of the same MOD13Q1.061 collection.

Known limits of the field sample (soil bias, ~10-15% off-centre detections, missing
`crops.csv` classes) are recorded in `fields_raw.geojson → known_limits`.
