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

## Test round 1 — judges, farmer, adviser (2026-11-14 ~19:00)

Three scripted testers drove the live app in Edge: a judge panel (scores Impact 4 · Creativity 4 ·
**Validity 2.5** · Relevance 3.5 · Presentation 4), "Dale" (Garden City irrigator, desktop + phone)
and "Maria" (K-State crop adviser, checked numbers against `strategies.json` / `engine/params.py`).
Shared top finding: **on the example field the current rotation wins under every preset, even
"Save Water" with a 14 in or dryland limit** — the demo answers "what could a different rotation
do?" with "nothing". Priority order within each owner = list order. `[ ]` open, `[x]` done.

### Person 1 — web
- [x] **W1 Water limit counts in the ranking** (`lib/ranking.ts`): a sample where a rotation
  exceeds the limit cannot be "best"; headline adds why the winner wins ("mainly on soil score
  and labour; alfalfa–corn needs ~17 in, over your 8 in"). Small tolerance (±5 %) before
  flagging (459 mm vs 457 mm limit was flagged).
- [x] **W2 US units** on cards, compare and print: in/yr, $/ac, t/ac; "≈ $X for this N-ac field";
  label net return "before land rent & pivot/well costs". Metric in print footnote.
- [x] **W3 Plain wording**: "came out on top in about 5 of every 10 runs" (not "49 % of
  samples"); "months without green cover" (NDVI < 0.3 includes dormant alfalfa and standing
  stalks) instead of "bare soil … most erodible state"; drop "every number comes from open
  data" (cover factors, pivot capacity, SCI thresholds, labour are judgement values); GRACE
  card must not say "every month measured" while showing the mock; jargon list (FIN-001 →
  "Field 1 (137 ac)", CDL → USDA crop map, p10/p90 → bad/typical/good year, AWC → "holds ~4 in
  of water", index units, GMD3/WIMAS explained); no "%" on an index that can go negative;
  consistent decimals.
- [ ] **W4 Navigation**: browser/Android Back goes to previous step (`pushState` on step change,
  `lib/flow.ts:49` uses `replaceState`); phone reload/share link opens the saved step tab, not
  the map; no scroll-zoom on the map until tapped; header + stepper + tabs use ~215/844 px on
  phone.
- [ ] **W5 Finding your field**: satellite/labelled basemap toggle, zoom to selected field,
  hint above the map (dots cover it), "50 sample pivots — if yours isn't here pick one with
  similar soil".
- [ ] **W6 Clean leftovers**: "Season-by-season detail" still has a second field dropdown, a
  second "Print Dossier", an empty "Water Deficit" row and overlapping heat pills; print view
  clips date/URL and Labour column on the right; "%" wraps on phone; targets < 44 px (crop-year
  cells 16×24, zoom 29×29, "How we know" 31 px); county label covers zoom buttons on phone.
- [ ] **W7 Example field**: switch "Try an example" from FIN-001 to a field where an
  alternative wins (FIN-026: alfalfa–corn 47 % under Soil Stewardship) — re-check after W1.
- [ ] W8 (later) Ranking samples whole weather years once the engine exports per-year results
  (now each metric × strategy is drawn independently, so a 2012-type year never hits all four
  at once; normalising over only 4 options turns 0.11 vs 0.57 into worst vs best).

### Person 3 — engine (then `make export`)
- [ ] **E1 Soil index rates alfalfa as bad for soil**: continuous alfalfa 0.26 vs continuous
  corn 0.64 (FIN-017), alfalfa–corn 0.41 < corn–wheat–sorghum 0.48; sorghum–wheat–rye cover
  0.27 < current 0.57 on FIN-001. OM term counts only above-ground residue (`crops.csv`
  alfalfa residue 1.0 t/ha, hay removed). Add root/crown biomass for perennials and cover
  (~3–5 t/ha/yr) or NRCS SCI biomass values. This drives "Save Water" picking the current
  rotation.
- [ ] **E2 Irrigated wheat uses as much water as corn**: continuous wheat 404–405 mm
  (FIN-025, FIN-004) vs corn 400 mm (FIN-017); budgets report says 6 in (limited) / 12 in
  (2012 drought). Likely Kc_ini 0.70 through dormancy + full refill at 40 % depletion. Use Kc
  ~0.4 over dormancy and deficit irrigation for wheat; target p50 ≈ 8–12 in. Also inflates
  corn–wheat–sorghum (378 mm).
- [ ] **E3 Limited irrigation earns less than dryland on every field**: sorghum–wheat–cover
  $119/ha vs dryland $128 (FIN-001), $240 vs $324 (FIN-032), p10 −$7. Limited option pays full
  irrigated direct costs with deficit yields (`strategies.py:85`). Use limited-irrigation
  budget lines or scale inputs to yield. Its water is a flat 100 mm with no range while gaps
  text says "capped at 150 mm" — make consistent.
- [ ] **E4 Rye cover claims vs model**: "Forage" trait and "silage for feedlots" benefit, but
  the rye is costed as glyphosate-terminated with no revenue; "shields topsoil from wind
  erosion" on fields where modelled erosion is higher than current (FIN-022 0.49 vs 0.21,
  FIN-026, FIN-032 1.32 vs 1.06, FIN-034, FIN-045). (The old "Low water erosion" contradiction
  is fixed — testers confirmed.)
- [ ] **E5 Trade-offs per strategy**: benefits are one-sided boilerplate ("established
  elevator access" on every current rotation); add `risks`/drawbacks (e.g. corn–soybean on
  FIN-005 has 14× the erosion of alfalfa). "Why it's here" says "under full irrigation from
  USDA CDL history" — CDL does not say how much was irrigated.
- [ ] **E6 Identical net returns** for alfalfa–corn, sorghum–wheat–cover and dryland on
  FIN-001 and FIN-026 — check field-specific yield response.
- [ ] E9 (info) Web ranking now applies the farmer's water limit (`rankWithLimit` in
  `web/src/lib/ranking.ts`); `engine/mcda.py` parity holds only for the no-limit case.
- [ ] E7 (later) Export per-weather-year metrics so web can sample whole years (see W8).
- [ ] E8 (later, adviser asks) Yield & price assumptions per crop (bu/ac, t/ac) and transition
  costs (breaking/establishing alfalfa, N credit) visible in data for the printout.

### Person 2 — pipeline
- [x] **P1 GRACE `schema_version: "0.3"`** — the pipeline was already writing 0.3; what was
  stale was the export, so `web/public/data/grace_water_storage.json` still held the 22-month
  mock. Re-ran `engine.export`: web now carries the real **259-month** series,
  `mock: false`, trend -0.86 cm/yr. Committed with the regenerated web data.
- [x] **P2 Heat-stress days identical for every field / idealised circles** — every
  `stress_window.note` now says "COUNTY-LEVEL: one NASA POWER grid cell (0.5 x 0.625 deg,
  ~50 km) for all fields ... not a field measurement". The idealised-circle caveat cannot go
  in the contract (feature `properties` are closed) so it is in
  `fields_raw.geojson -> known_limits`; **person 3 (engine)**: to surface it in the UI it
  needs a `data_gaps` line in `strategies.json`, e.g. "Field shape is an idealised circle at
  the detected radius; area is approximate to a few percent."
- [x] P3 Frost windows into contracts — **contracts v0.4** (approved by all three, 2026-11-14).
  `stress_window.type` now allows `"frost"`; every field carries 18 frost windows (one per
  crop year, 2008-2025) spanning last spring frost -> first fall frost, with severity =
  how much shorter the season was than the 1995-2025 median (0 = median or longer, 1 = p10).
  `web/public/data` regenerated at 0.4, `engine.validate` and `check:data` clean.
  **person 1 (web):** the passport timeline can now render `type: "frost"` as a band — the
  two frost dates and the climatology are already in each window's `note`.
- [x] P4 "Bare" definition — every bare period's `note` now carries the caveat: NDVI sees
  green canopy, not ground cover, so dormant alfalfa, standing stalks and residue-covered
  soil all read as "bare" even when the surface is protected from wind erosion.

### Not doing before the freeze (decided)
- ECOSTRESS / Landsat / SMAP / GPM integration (mention in "How we know" only).
- Forage and N-fixing as weightable priorities (shown as traits instead).

## Blockers / requests

- ~~**person 1 → person 3: "Low water erosion" benefit contradicts the metrics**~~ —
  resolved (person 3): `engine/strategies.py` now enforces strict relative comparison against
  the baseline rotation (`current_metrics` and `current_rotation`). A water erosion reduction
  benefit is only emitted when `alt_erosion < cur_erosion` by at least 0.05 t/ha/yr and ≥10%
  (phrased as "~X% less water erosion than current rotation"). If water erosion is higher (e.g.
  dryland fallow), it highlights groundwater elimination, Ogallala protection, pumping cost
  savings, and machinery labour reductions instead. Similar strict delta checks applied to
  water, income, labour, SCI, and N-fixation. Regenerated and validated across all 50 fields (0
  contradictions).

- **contracts v0.3 (GRACE) — approved by all three, merged to `main` (2026-11-14).** Was
  branch `contracts-v0.3-grace`. Adds `contracts/grace.schema.json` + mock, bumps mocks to 0.3, adds
  `GraceFile` to `web/src/types/contracts.ts`. The web start screen already shows the GRACE
  card whenever `web/public/data/grace_water_storage.json` exists, and hides it otherwise.
  After approval:
  - ~~**person 2:** `pipeline grace` writes `"schema_version": "0.3"` at the top level.~~ —
    **done**: `pipeline/grace.py` and `pipeline/assemble.py` write `schema_version = "0.3"`
    and `mock = False`. Blocker resolved.
  - ~~**person 3:** `engine.export` copies `data/interim/grace_water_storage.json` to
    `web/public/data/`; `engine.validate` checks it against `grace.schema.json` in
    `make check`; `SCHEMA_VERSION = "0.3"`.~~ — **done (person 3)**: `engine.export`
    handles `grace_water_storage.json` with interim + mock fallback; `engine.validate`
    runs schema and semantic validation on GRACE; `SCHEMA_VERSION = "0.3"`. Tested & passing.
  - `Makefile` `PIPELINE_STEPS` now includes `grace groundwater frost` (done, person 1).

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
- **pipeline → person 3 (engine owner after the swap; done, please review):** `engine/params.py` now covers 5 of the 8 new
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
- **pipeline: SMAP and GPM IMERG are CLOSED — do not re-open without a new decision.**
  Both were investigated to the point of a measured answer, and the team chose not to
  pursue either (2026-11-14). The findings, so nobody repeats the work:
  - **SMAP is out on volume.** One SPL3SMP_E daily granule is **704 MB** (measured: 1624 x
    3856 float32, ~822k valid retrievals), so 2002-2025 would be ~4.6 TB. The sampled day
    (2022-07-05) also had zero valid retrievals inside the county box — daily SMAP at one
    location is patchy by swath. Water stress therefore stays with the engine's FAO-56
    balance (`stress_days` from Ks < 1), which needs no SMAP.
  - **GPM IMERG is blocked on authorisation, not data.** IMERG monthly is a workable 18 MB
    per month, but GES DISC returns 401/403 for this account (MERRA-2 too, so it is
    account-level): the "GES DISC" application is not approved at Earthdata Login. If it is
    ever approved, the "satellite vs model" sentence becomes a small job.
  - `h5py` was added for this work and **removed again** once both were dropped, so the
    dependency allow-list stays truthful. Nothing imports it.
- ~~**person 1 → person 2: NASA-data depth for judging ("Relevance" criterion)**~~ —
  **items 1 and 2 delivered (2026-11-14); item 3 dropped by team decision.**
  1. **GRACE-FO TWS trend** — done, `data/interim/grace_water_storage.json`, contracts
     **v0.3** (`contracts/grace.schema.json`), wired into the start screen by person 1/3.
     259 months 2002-04..2026-09, trend **-0.86 cm/yr (R² 0.80)** full period and -0.80 over
     the last 10 years. Marked as TOTAL water storage (not groundwater) on ~300 km mascons.
  2. **Frost risk** — done, `data/interim/frost_windows.json` + `.csv`: spring/fall frost
     dates and p10/p50/p90 (1995-2025). Caveat in the file: MERRA-2 smoothing makes the
     season read long (~199 d vs ~155-170 documented), so use it for relative risk.
  3. **GPM IMERG** — dropped; see the SMAP/IMERG entry above (GES DISC not authorised).

  Verified after the ownership swap and the v0.3 edits (2026-11-14): `assemble` and
  `groundwater` still run, `fields.geojson` (60 fields) and `grace_water_storage.json`
  (259 months) both validate at 0.3 with `mock: false`.
- ~~**pipeline → person 1 / person 3: frost data is produced but NOTHING consumes it.**~~
  **Resolved at contracts v0.4** — frost is now part of `fields.geojson` as
  `type: "frost"` windows, so nothing is stranded. Remaining work is on the web side: render
  it on the passport timeline.
- ~~**person 1 → person 3: per-strategy "why / benefits / risks"**~~ — resolved (person 3):
  `contracts/strategies.schema.json` and `web/src/types/contracts.ts` gained `why_considered`
  (field-specific rationale tied to soil/history/water), `benefits` (2–3 quantified strings),
  and `soil_health_traits` (`n_fixing_years`, `pest_break`, `forage`). Implemented and tested
  in `engine/strategies.py`; all fields in `engine.export` populate them dynamically.
- ~~**person 1 → person 2: `pipeline ndvi` pages leave the county**~~ — resolved in
  `6d41c21` (bare periods 2007–2025 in `fields.geojson`). Kept for reference: (`pipeline/ndvi.py`
  `search_items`). Page 1 is a POST with `bbox` + `collections` and returns the right tiles
  (100 × `h10v05`). The `rel=next` link is then fetched with a GET and no body, so later pages
  are unfiltered: global tiles (`h23v02`, `h35v09`, …) and even Aqua `MYD13Q1` items. Seen in
  a full `make data` run on 2026-11-14 (256 granules skipped, all `URLError`, most of them
  outside Kansas). Fix ideas: follow the next link with the method/body it specifies (STAC
  POST paging), or filter items by `collection` and tile/bbox before downloading. The
  `URLError`s on the in-county granules may be a separate signing/network issue.
  **Re-verified 2026-11-14 after the fix:** 2024-05..08 returns 22 items, all `MOD13Q1`
  (Terra), and 8/8 sign+read attempts succeed, so both symptoms came from the bad pages.
  The remaining failure mode is HTTP 429 rate limiting on the PC signing endpoint, which
  the code now paces, honours `Retry-After` for, and resumes around via the per-composite
  cache — a fresh `make data` may need a second `pipeline ndvi` pass to finish, by design.

- **pipeline → person 1 (web owner after the swap):** two observations from opening the dev server with real data.
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
- 2026-11-14 17:48: per-strategy why_considered, benefits, and soil_health_traits (n_fixing_years,
  pest_break, forage) added to contracts/strategies.schema.json, web/src/types/contracts.ts,
  and engine/strategies.py. Export and validation passing.
- 2026-11-14 18:20: fixed strategy benefits generation in engine/strategies.py to evaluate
  all claims strictly relative to current field rotation and metrics. Eliminated spurious "low
  water erosion" benefits on dryland fallow rotations; added relative % improvements and
  groundwater/cost savings alternatives. All 50 real fields and mocks pass with 0 contradictions.
- 2026-11-14 18:27: contracts v0.3 engine follow-up completed (person 3): SCHEMA_VERSION = "0.3"
  in engine/export.py; engine.export copies grace_water_storage.json (interim or mock fallback);
  engine.validate checks grace.schema.json and semantic constraints (chronological dates, FIPS match,
  data gaps); test suite augmented and make check green.
- 2026-11-14 18:52: pipeline fix applied (approved by user): pipeline/grace.py and pipeline/assemble.py
  updated to SCHEMA_VERSION = "0.3" and mock = False. Unblocks real GRACE series in data/interim/ and export.
