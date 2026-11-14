# TASKS

Status legend: `todo` · `doing` · `done` · `blocked`. Update your own column only; add
cross-team needs under **Blockers / requests**.

## Timeline

| When       | Milestone                                                     |
| ---------- | ------------------------------------------------------------- |
| Sat 20:00  | **Data ready** — real `fields.geojson` + inputs for engine    |
| Sun 08:00  | **MVP frozen** — bug fixes, copy, pitch only                  |
| Sun 12:30  | **Submission** (hard deadline **13:30**)                      |

## Board

| Person 1 — engine / design / pitch                       | Person 2 — pipeline                                         | Person 3 — web                                                  |
| -------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------- |
| `done` scaffold, contracts v0.1, mocks                   | `todo` Earthdata login + `.env`                             | `done` scaffold renders mocks                                   |
| `todo` FAO-56 ET0 (POWER daily) + Kc curves → water_use  | `done` NASA POWER daily 1995–2025 for county centroid       | `todo` map polish: legend, hover tooltip, county outline        |
| `todo` simplified RUSLE (R from POWER precip, K, LS, C)  | `todo` CDL 2008–2025 clip to Finney + field polygons        | `todo` passport: timeline of bare/stress windows                |
| `todo` soil-conditioning index (residue, OM, tillage)    | `todo` SSURGO soil props per field (texture, OM, K, AWC)    | `todo` strategy comparison: interval chart per metric           |
| `todo` income model (price source per crop, placeholder) | `todo` SRTM slope per field                                 | `todo` P(best) + "verify locally" box copy                      |
| `todo` MCDA + Dirichlet weights, P(best) in export       | `todo` MODIS NDVI → bare-soil periods per field-year        | `todo` mobile layout / accessibility pass                       |
| `todo` `engine.export` → contracts format                | `todo` SMAP soil moisture → water-stress windows            | `todo` "about the data" / uncertainty page                      |
| `todo` pitch deck + demo script                          | `done` heat-stress windows (POWER Tmax > threshold)         | `todo` deploy static build                                      |

## Blockers / requests

- **pipeline:** `rasterio==1.4.4` + `pyproj==3.7.2` + `shapely==2.2.0` approved and added
  (GDAL 3.10.3 wheels import cleanly on Windows). CDL zonal stats, SSURGO and SRTM are
  unblocked.
- **pipeline:** MODIS NDVI + SMAP + SRTM downloads still need `EARTHDATA_USERNAME` /
  `EARTHDATA_PASSWORD` in `.env`. POWER and SSURGO (Soil Data Access JSON) need no login.

## Decisions log

- Contracts v0.1: fields GeoJSON + strategies JSON + crops.csv (see `contracts/README.md`).
