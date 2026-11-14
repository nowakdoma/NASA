# contracts/ — the integration point

Everything that crosses a team boundary is defined here. **Changes need explicit approval
from all three humans** (see `AGENTS.md`). Current version: **0.3** (proposal, pending approval).

| File                            | Producer                         | Consumer           |
| ------------------------------- | -------------------------------- | ------------------ |
| `fields.schema.json`            | pipeline → engine.export         | web                |
| `strategies.schema.json`        | engine.export                    | web                |
| `crops.csv`                     | humans (person 1)                | engine, pipeline   |
| `mock/fields.geojson`           | hand-tuned, `"mock": true`       | web, tests         |
| `mock/strategies.json`          | hand-tuned, `"mock": true`       | web, tests         |
| `grace.schema.json`             | pipeline/grace.py → export       | web (start screen) |
| `mock/grace_water_storage.json` | yearly subsample, `"mock": true` | web, tests         |

Validate: `uv run python -m engine.validate [fields.geojson strategies.json]` (defaults to
the mocks). Same checks run on `web/public/data/` in `make check`.

## Conventions

- Coordinates WGS84 lon/lat. Dates ISO `YYYY-MM-DD`. Year keys are strings (`"2012"`).
- Crop codes are snake_case and **must exist in `crops.csv`** (`crop_code` column).
- Field ids: `FIN-001` (county prefix + 3 digits).
- Every metric is `{p10, p50, p90}` over weather years 1995–2025, with `p10 <= p50 <= p90`.
  Direction (`better: higher|lower`) and units live in `strategies.json → metric_meta`.
- Exactly 4 strategies per field, exactly one with `is_current: true`.
- Invented numbers: file-level `"mock": true`; uncertain trait values `placeholder=true` in
  `crops.csv`; known model limitations go into each strategy's `data_gaps`.

## Semantic checks beyond JSON Schema (engine/validate.py)

- every year in `fields.years` is present in each `crop_history`;
- all crop codes (history + rotations) exist in `crops.csv`;
- `fields` ids == `strategies.fields` keys; unique field ids;
- quantile ordering; exactly one current strategy; unique strategy ids per field;
- date ranges have `start <= end`;
- `crops.csv` has the required columns and unique `crop_code`s.

## crops.csv columns

`crop_code, name, cdl_code, family, n_fixing, root_depth_m, kc_ini, kc_mid, kc_end,
l_ini_d, l_dev_d, l_mid_d, l_late_d, residue_t_ha, price_source, placeholder, source`

Kc and stage lengths (days) follow FAO-56 Tables 11–12; `placeholder=true` rows still need
local calibration (K-State extension / KS NASS).

### v0.2 — CDL classes that were missing

Added `triticale`, `potatoes`, `other_hay`, `other_crops`, plus the four double-crop
rotations that really occur in Finney County: `winwht_corn` (CDL 225), `triticale_corn`
(228), `winwht_sorghum` (236), `winwht_soybeans` (26). Without these rows the pipeline had
to drop a field whose history contained one of them, which cost 34 of 60 fields.

**Double-crop convention:** one `crop_code` per field-year, so a double-cropped year is
represented by its **summer** crop only (corn/sorghum/soybeans), with Kc taken from that
crop. The winter-wheat/triticale phase is not separately modelled, which understates
water use for those years; they are `placeholder=true` and say so in `source`.

Non-crop CDL classes (shrubland 152, developed, water) are deliberately **not** added: a
year of shrubland is not a crop, and coercing it to one would falsify the rotation.

### v0.3 — regional water-storage trend (GRACE/GRACE-FO) — proposal

Adds `grace.schema.json` for `grace_water_storage.json` (written by `pipeline grace`), so the
web start screen can show the NASA groundwater story with a validated file. The file is
**total** water storage on ~300 km mascons: `data_gaps` must say so, and the UI labels it
"regional signal, not your well". Extra keys from the pipeline (`baseline`, `period`,
`trend_last_10_years`, …) are allowed. Needs: pipeline writes `schema_version: "0.3"`;
`engine.export` copies the file to `web/public/data/` and `engine.validate` checks it.
