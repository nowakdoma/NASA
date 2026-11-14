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
| `done` FAO-56 ET0 (POWER daily) + Kc curves → water_use  | `done` NASA POWER daily 1995–2025 for county centroid       | `todo` map polish: legend, hover tooltip, county outline        |
| `done` simplified RUSLE (R from POWER precip, K, LS, C)  | `todo` CDL 2008–2025 clip to Finney + field polygons        | `todo` passport: timeline of bare/stress windows                |
| `done` soil-conditioning index (residue, OM, tillage)    | `todo` SSURGO soil props per field (texture, OM, K, AWC)    | `todo` strategy comparison: interval chart per metric           |
| `done` income model (price source per crop, placeholder) | `todo` SRTM slope per field                                 | `todo` P(best) + "verify locally" box copy                      |
| `todo` MCDA + Dirichlet weights, P(best) in export       | `todo` MODIS NDVI → bare-soil periods per field-year        | `todo` mobile layout / accessibility pass                       |
| `done` `engine.export` → contracts format                | `todo` SMAP soil moisture → water-stress windows            | `todo` "about the data" / uncertainty page                      |
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
- **person 1 → person 2: engine input formats** (engine runs on fallbacks until these exist;
  output is then flagged `"mock": true`):
  - `data/interim/power_daily.csv`: NASA POWER daily for the county centroid, 1995-01-01 to
    2025-12-31, one row per day, no gaps, no `-999`. Columns: `DATE` (YYYY-MM-DD), `T2M_MAX`,
    `T2M_MIN` (°C), `RH2M` (%), `WS2M` (m/s at 2 m), `ALLSKY_SFC_SW_DWN` (MJ/m²/day),
    `PRECTOTCORR` (mm/day). Checked by `engine.weather.load_power_daily`.
  - `data/interim/fields.geojson`: real fields in `contracts/fields.schema.json` format.
    `make export` reads it, adds `strategies.json`, writes both to `web/public/data/` and
    validates them.

## Decisions log

- Contracts v0.1: fields GeoJSON + strategies JSON + crops.csv (see `contracts/README.md`).
- Engine economics/labour/C-factor values live in `engine/params.py` (PLACEHOLDER, not a
  contract change). Alternatives = 3 most different entries of `params.CATALOGUE` per field.
- `make export` now runs the engine; `python -m engine.export --mock` copies the hand mocks.
