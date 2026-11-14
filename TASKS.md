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

- **pipeline:** Earthdata credentials verified **working** — NSIDC SMAP listings
  (`daacdata.apps.nsidc.org/pub/SMAP/SPL3SMP_E/`) return 200 with them. Note EDL rejects
  HTTP Basic on `/api/users/self` by design, so a 401 there does not mean bad credentials.
- **pipeline:** LP DAAC cloud (`data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/`,
  where MOD13Q1 and SRTMGL1 now live) returns **401 for username/password** — protected
  data there needs an EDL bearer token + S3 credentials. Legacy `e4ftl01.cr.usgs.gov`
  paths are decommissioned (only `ASTT` remains). Workarounds verified: MOD13Q1 NDVI is
  readable anonymously from the Planetary Computer mirror via `/api/sas/v1/sign` (206),
  and SRTM GL1 needs no login at all from the public `elevation-tiles-prod` skadi bucket.
- **pipeline:** open question for person 1 — if the pitch should credit LP DAAC directly
  (rather than a mirror), someone with the account must generate an EDL token and we add
  `boto3` for S3 access.

## Decisions log

- Contracts v0.1: fields GeoJSON + strategies JSON + crops.csv (see `contracts/README.md`).
