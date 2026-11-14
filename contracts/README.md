# contracts/ — the integration point

Everything that crosses a team boundary is defined here. **Changes need explicit approval
from all three humans** (see `AGENTS.md`). Current version: **0.1**.

| File                     | Producer                     | Consumer          |
| ------------------------ | ---------------------------- | ----------------- |
| `fields.schema.json`     | pipeline → engine.export     | web               |
| `strategies.schema.json` | engine.export                | web               |
| `crops.csv`              | humans (person 1)            | engine, pipeline  |
| `mock/fields.geojson`    | hand-tuned, `"mock": true`   | web, tests        |
| `mock/strategies.json`   | hand-tuned, `"mock": true`   | web, tests        |

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
