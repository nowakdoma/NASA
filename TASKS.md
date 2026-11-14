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
| `→P3` MCDA + Dirichlet weights, P(best) in export       | `done` MODIS NDVI → bare-soil periods per field-year        | `done` mobile layout / accessibility pass                       |
| `done` `engine.export` → contracts format                | `done` SMAP → water stress (superseded, see note)           | `done` "about the data" / uncertainty page                      |
| `done` pitch deck + demo script (in reports/)            | `done` heat-stress windows (POWER Tmax > threshold)         | `done` deploy static build                                      |
| `done` pitch deck (7 slides) + 3-min live demo script    |                                                             | `done` (from P1) P(best): closed live in web, engine/mcda.py synced |
|                                                          |                                                             | `done` (from P1) crops.csv v0.2 proposal in reports/CONTRACT_PROPOSAL_CROPS_V0.2.md |

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
- ~~**pipeline → person 3 (was person 1):** `contracts/crops.csv` has no row for crops that
  really grow here~~ — **resolved in v0.2** (all three approved). Added `triticale` (205),
  `potatoes` (43), `other_hay` (37), `other_crops` (44) and the four double-crop rotations
  (`winwht_corn` 225, `triticale_corn` 228, `winwht_sorghum` 236, `winwht_soybeans` 26),
  with a documented double-crop convention (summer crop only, winter phase not modelled,
  `placeholder=true`). The pipeline now emits **all 60 fields** with complete histories.
- **pipeline → person 1 (done, please review):** `engine/params.py` now covers 5 of the 8 new
  crops via documented budget proxies (`PROXIED_CROPS`): triticale → winter wheat, and the
  four double-crop rotations → their summer crop. Each proxy is surfaced in `data_gaps` and
  in `verify_locally`, so the UI says which budget it used. **50 of 60 fields now reach the
  web.** The remaining 10 need potatoes (9), other hay (1) and other crops (1): there is no
  K-State SW Kansas budget for them and NASS publishes no Kansas potato price (only the US
  average, $10.80/cwt 2025), so costing them would mean fabricating the income metric.
  `engine/export` skips those fields and names the crops. Details in the addendum to
  `reports/SW Kansas crop budgets.md`.

- ~~**pipeline → person 1:**~~ resolved — `fields.geojson` landed (26 fields). The contract requires every year in `crop_history` and requires
  `soil`, `season_calendar` and `stress_index_by_year` per field, so `fields.geojson` can
  only land once SSURGO/SRTM/NDVI/SMAP are in. `data/interim/fields_raw.geojson` (60 pivots,
  geometry + crop history + purity flags) already exists in the pipeline's own interim
  format if that helps you prototype — but do not treat it as contract-shaped.

- ~~**person 1 → person 2: NASA-data depth for judging ("Relevance" criterion)**~~ —
  **items 1 and 2 done (2026-11-14); item 3 not done (optional).**
  - GRACE-FO: `data/interim/grace_water_storage.json` — 259 months, 2002-04..2026-09, area
    mean over the county's 4 grid cells. Trend **-0.86 cm/yr TWS (R² 0.80)** full period,
    **-0.80 cm/yr** over the last 10 years (R² 0.52), so the decline is not an artifact of
    the start date. One 46 MB netCDF, no new dependency. **It is total water storage, not
    groundwater** — soil moisture, snow and surface water are included; splitting them out
    needs a land-surface model we do not run. Mascons are ~300 km, so treat it as regional.
  - Frost: `data/interim/frost_windows.json` + `.csv` — last spring / first fall frost and
    frost-free days per year, with p10/p50/p90 over 1995-2025, same shape as the heat
    windows. Caveat recorded in the file: a MERRA-2 cell smooths cold nights, so the season
    reads long (~199 d p50 vs ~155-170 documented for Garden City) — use it for relative
    risk between years, not absolute planting dates.
  - GPM IMERG (optional, item 3) not done — say the word.
  - **`Makefile` needs `grace`, `groundwater` and `frost` added to `PIPELINE_STEPS`** (root
    file, yours) or `make data` will not produce them.
- **pipeline: h5py added (approved) but GPM/SMAP status changed — read this before asking again.**
  `h5py==3.16.0` is installed, so HDF5/HDF-EOS5 products are now *readable*. Two consequences,
  both measured rather than assumed:
  - **SMAP is out on volume, not readability.** A single SPL3SMP_E daily granule is **704 MB**
    (measured, not the ~80 MB I guessed earlier), 1624 x 3856 x float32, so the 2002-2025
    record would be ~4.6 TB. Even sampling summer months for 10 years is ~150 GB. The one day
    I sampled (2022-07-05) also had **zero valid retrievals in the county box** — daily SMAP
    at one location is patchy by swath. Water stress stays with the engine's FAO-56 balance.
  - **GPM IMERG is blocked on authorisation, not data.** IMERG monthly is a sane 18 MB per
    month, but `data.gesdisc.earthdata.nasa.gov` returns **401 with username/password and 403
    with the EDL token** — the "NASA GES DISC" application is not authorised for this account,
    unlike LP DAAC and NSIDC which work. Approve it at Earthdata Login -> Applications ->
    Authorized Apps, then `python -m pipeline gpm` will work. Not built yet because I will not
    write an HDF5 parser I cannot test against a real file.
- **person 1 → person 2: NASA-data depth for judging ("Relevance" criterion)** — the brief
  names SMAP, GPM, GRACE/GRACE-FO, ECOSTRESS, Landsat; we currently show POWER, MODIS, SRTM.
  In priority order, each as a small static JSON in `data/interim/` (person 1 wires the UI):
  1. **GRACE-FO groundwater / TWS trend** for the Finney County area (e.g. JPL/CSR mascon
     2002–2025, monthly anomaly cm + linear trend cm/yr). One series is enough — it is the
     NASA hook for the Ogallala story on the start screen. Mark resolution (~300 km) as a gap.
  2. **Frost risk** from NASA POWER `T2M_MIN` (already downloaded): per year last spring frost
     and first fall frost (< 0 °C), plus p10/p50/p90 dates over 1995–2025. Same shape as
     heat-stress windows (`type: "frost"`) is ideal.
  3. Optional: **GPM IMERG** monthly precip for the county vs POWER — one sentence for the
     "satellite vs model data" box (brief asks to explain this).
- **person 1 → person 3: per-strategy "why / benefits / risks"** — the brief requires, per
  strategy: why suggested, evidence, benefits, information gaps, risks needing local review.
  `strategies.json` already has `description`, `evidence`, `data_gaps`, `verify_locally`.
  Missing: (a) `why_considered` — one sentence tied to this field (e.g. "bare 3–6 months most
  winters on fine sand → cover replaces fallow"); (b) `benefits` — 2–3 short strings;
  (c) soil-health traits per strategy for the brief's priorities: `n_fixing_years`,
  `pest_break` (true if ≥ 2 crop families), `forage` (bool). (a)–(c) need a contracts bump
  (3 humans). Fallback if no time: person 1 writes the copy statically in `web/`, labelled
  draft. Water-allocation constraint ("inches I can pump") will be done client-side in web
  from `water_use_mm` p50/p90 — no engine change needed.
- ~~**person 1 → person 2: `pipeline ndvi` pages leave the county**~~ — resolved in
  `6d41c21` (bare periods 2007–2025 in `fields.geojson`). Kept for reference: (`pipeline/ndvi.py`
  `search_items`). Page 1 is a POST with `bbox` + `collections` and returns the right tiles
  (100 × `h10v05`). The `rel=next` link is then fetched with a GET and no body, so later pages
  are unfiltered: global tiles (`h23v02`, `h35v09`, …) and even Aqua `MYD13Q1` items. Seen in
  a full `make data` run on 2026-11-14 (256 granules skipped, all `URLError`, most of them
  outside Kansas). Fix ideas: follow the next link with the method/body it specifies (STAC
  POST paging), or filter items by `collection` and tile/bbox before downloading. The
  `URLError`s on the in-county granules may be a separate signing/network issue.

- **pipeline → person 3 (web):** two observations from opening the dev server with real data.
  The 26 fields load correctly (legend tallies match: alfalfa 13, corn 7, wheat 2, fallow 2,
  sorghum 1, grass 1) and no mock banner shows, but at county zoom the fields read as small
  dots rather than visible circles — expected for an 800 m pivot in a 764 px viewport, so
  worth confirming they render as polygons when zoomed. Also: clicking the zoom control
  rapidly 6 times left the page blank with `body.innerText.length == 0` and no console error
  captured; may be my selector, but worth a look.
- **pipeline → all:** `county.name` was "Finney County, KS" which the UI renders as
  "Finney County, KS, KS". Fixed to the bare "Finney County" (contract/mock convention).

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
- 2026-11-14 17:15: P(best) closed as computed live in web client; engine/mcda.py augmented
  with rank_strategies and test parity. Contract proposal for crops.csv v0.2 (triticale, oats,
  other hay, double crops) documented in reports/CONTRACT_PROPOSAL_CROPS_V0.2.md. Pitch deck
  (7 slides) & 3-minute live demo script written in reports/PITCH_AND_DEMO_SCRIPT.md.
