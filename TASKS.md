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

- **pipeline:** Earthdata access fully verified. `EARTHDATA_TOKEN` unlocks the LP DAAC
  cloud protected buckets — MOD13Q1 granule range request returns 206 (HTTP Basic returns
  401 there). `EARTHDATA_USERNAME`/`PASSWORD` still covers NSIDC SMAP. EDL rejects Basic on
  `/api/users/self` by design, so a 401 there means nothing.
- **pipeline:** legacy `e4ftl01.cr.usgs.gov` pool is decommissioned (only `ASTT` remains) —
  ignore any tutorial that points at it. SRTM also has a no-login fallback from the public
  `elevation-tiles-prod` skadi bucket if LP DAAC is ever unavailable.
- **pipeline → person 1:** `.env.example` should document `EARTHDATA_TOKEN`, but it is a
  root file I do not own — please add, or tell me to.

## Decisions log

- Contracts v0.1: fields GeoJSON + strategies JSON + crops.csv (see `contracts/README.md`).
