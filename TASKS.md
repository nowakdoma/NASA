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

| Person 1 — engine → **web UI/UX, pitch, slides**         | Person 2 — pipeline                                         | Person 3 — web → **engine** + P1 leftovers                      |
| -------------------------------------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------- |
| `done` scaffold, contracts v0.1, mocks                   | `done` Earthdata login + `.env`                             | `done` scaffold renders mocks                                   |
| `done` FAO-56 ET0 (POWER daily) + Kc curves → water_use  | `done` NASA POWER daily 1995–2025 for county centroid       | `done` map polish: legend, hover tooltip, county outline        |
| `done` simplified RUSLE (R from POWER precip, K, LS, C)  | `done` CDL 2008–2025 clip to Finney + field polygons        | `done` passport: timeline of bare/stress windows                |
| `done` soil-conditioning index (residue, OM, tillage)    | `done` SSURGO soil props per field (texture, OM, K, AWC)    | `done` strategy comparison: interval chart per metric           |
| `done` income model (price source per crop, placeholder) | `done` SRTM slope per field                                 | `done` P(best) + "verify locally" box copy                      |
| `→P3` MCDA + Dirichlet weights, P(best) in export       | `todo` MODIS NDVI → bare-soil periods per field-year        | `done` mobile layout / accessibility pass                       |
| `done` `engine.export` → contracts format                | `todo` SMAP soil moisture → water-stress windows            | `done` "about the data" / uncertainty page                      |
| `todo` pitch deck + demo script                          | `done` heat-stress windows (POWER Tmax > threshold)         | `done` deploy static build                                      |
| `todo` pitch only (rest reassigned to person 3, 2026-11-14)  |                                                             | `todo` (from P1) P(best): close as "computed live in web", keep `engine/mcda.py` in sync with `src/lib/ranking.ts` |
|                                                          |                                                             | `todo` (from P1) crops.csv contract proposal for triticale, double crops, oats, other hay (see Blockers) |

## Blockers / requests

- **pipeline:** Earthdata access fully verified. `EARTHDATA_TOKEN` unlocks the LP DAAC
  cloud protected buckets — MOD13Q1 granule range request returns 206 (HTTP Basic returns
  401 there). `EARTHDATA_USERNAME`/`PASSWORD` still covers NSIDC SMAP. EDL rejects Basic on
  `/api/users/self` by design, so a 401 there means nothing.
- **pipeline:** legacy `e4ftl01.cr.usgs.gov` pool is decommissioned (only `ASTT` remains) —
  ignore any tutorial that points at it. SRTM also has a no-login fallback from the public
  `elevation-tiles-prod` skadi bucket if LP DAAC is ever unavailable.
- ~~**pipeline → person 1:** `.env.example` should document `EARTHDATA_TOKEN`~~ — done
  (person 1).
- ~~**person 1 → person 2: engine inputs**~~ — done: real `fields.geojson` + weather landed,
  `make export` gives `mock: false` (2026-11-14). Kept for reference:
  - weather: engine reads `data/interim/weather_daily.csv` as written by `pipeline power`
    (no change needed). Gaps up to 3 days are interpolated; longer gaps fail the export.
  - `data/interim/fields.geojson`: real fields in `contracts/fields.schema.json` format.
    `make export` reads it, adds `strategies.json`, writes both to `web/public/data/` and
    validates them.
- **pipeline → person 3 (was person 1):** `contracts/crops.csv` has no row for crops that really grow here:
  triticale (CDL 205, 23,709 ac in this county), double-crop rotations (225 winwht/corn,
  228 triticale/corn, 236 winwht/sorghum), oats (28), other hay (37). They are currently
  reported raw in `crop_history_cdl` + `unknown_cdl_years` instead of being forced into an
  existing code. Adding them needs contracts approval (3 humans) and a `schema_version`
  bump — until then ~7% of field-years have no crop_code.
- ~~**pipeline → person 1:**~~ resolved — `fields.geojson` landed (26 fields). The contract requires every year in `crop_history` and requires
  `soil`, `season_calendar` and `stress_index_by_year` per field, so `fields.geojson` can
  only land once SSURGO/SRTM/NDVI/SMAP are in. `data/interim/fields_raw.geojson` (60 pivots,
  geometry + crop history + purity flags) already exists in the pipeline's own interim
  format if that helps you prototype — but do not treat it as contract-shaped.

- **person 1 → person 2: `pipeline ndvi` pages leave the county** (`pipeline/ndvi.py`
  `search_items`). Page 1 is a POST with `bbox` + `collections` and returns the right tiles
  (100 × `h10v05`). The `rel=next` link is then fetched with a GET and no body, so later pages
  are unfiltered: global tiles (`h23v02`, `h35v09`, …) and even Aqua `MYD13Q1` items. Seen in
  a full `make data` run on 2026-11-14 (256 granules skipped, all `URLError`, most of them
  outside Kansas). Fix ideas: follow the next link with the method/body it specifies (STAC
  POST paging), or filter items by `collection` and tile/bbox before downloading. The
  `URLError`s on the in-county granules may be a separate signing/network issue.

## Decisions log

- 2026-11-14 16:20: person 1 hands remaining engine-side tasks except the pitch to person 3
  (P(best) closure, crops.csv contract proposal). Contract changes still need all three humans.
- 2026-11-14 16:30: **ownership swap** — `web/` → person 1 (UI/UX + pitch + slides),
  `engine/` → person 3. AGENTS.md table updated. Person 3: pull before touching `engine/`; any
  open web edits of yours, push them first or hand them to person 1.
- Contracts v0.1: fields GeoJSON + strategies JSON + crops.csv (see `contracts/README.md`).
- Engine economics/labour/C-factor values live in `engine/params.py` (PLACEHOLDER, not a
  contract change). Alternatives = 3 most different entries of `params.CATALOGUE` per field.
- `make export` now runs the engine; `python -m engine.export --mock` copies the hand mocks.
- `make data` = `pipeline all` (downloads) + derivations `heat fields terrain soil ndvi
  assemble` (person 2 request); change the order in `PIPELINE_STEPS` in the Makefile.
