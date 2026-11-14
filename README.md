# FieldShift

Decision support for crop-rotation strategies built on NASA data, for the
[NASA Space Apps 2026](https://www.spaceappschallenge.org/) challenge
**"Field Shift: Adapting Farms with NASA Data"**.

Study area: **Finney County, Kansas** (FIPS 20055, around Garden City).

> FieldShift supports farmer judgment. It does not replace it. Results are scores with
> uncertainty, not recommendations. Example: "under these priorities, strategy X scores
> highest in N % of weather/weight samples".

## What it does

- **Field map.** Irrigated fields coloured by crop, using USDA CDL history 2008–2025, with a
  year slider.
- **Field passport.** Crop history, bare-soil periods, water/heat stress windows and soil
  properties for each field.
- **Priority sliders.** Five farmer priorities: water, income, soil organic matter, erosion
  and labour.
- **Strategy comparison.** The current rotation plus 3 alternatives. Each metric is shown
  as a p10/p50/p90 interval from the 1995–2025 weather distribution, alongside **P(best)**
  under uncertain priorities and a **"what we don't know / verify locally"** box.

All computation runs offline. The web app only reads static JSON/GeoJSON from
`web/public/data/`.

> **Status: scaffold.** The web app renders realistic **mock** data from
> `contracts/mock/`. Pipeline downloads and engine models are still stubs (see
> [`TASKS.md`](TASKS.md)).

## Quick start

Requirements: **WSL2 Ubuntu** (or Linux/macOS), [uv](https://docs.astral.sh/uv/),
**Node 22** and **pnpm 9** (enable it with `corepack enable`), plus `make`. Keep the repo on
the Linux filesystem (`~/...`), not `/mnt/c`.

```bash
git clone https://github.com/nowakdoma/NASA fieldshift
cd fieldshift
make setup     # uv sync (Python 3.11) + pnpm install + pre-commit hook
make export    # validate mocks and copy them to web/public/data
make dev       # http://localhost:5173
```

Run `make help` to list all targets.

## Commands

| Command       | What it does                                                                     |
| ------------- | -------------------------------------------------------------------------------- |
| `make setup`  | Install Python deps (uv) and web deps (pnpm), and install the pre-commit hook   |
| `make data`   | Run the data pipeline (`python -m pipeline all`). Stubs for now                  |
| `make export` | Engine → `web/public/data/*.json`. Currently copies the validated mocks          |
| `make dev`    | Start the Vite dev server                                                        |
| `make check`  | ruff, pytest, contract validation, prettier, tsc, data check and web build. **Must pass before every commit** |

Useful direct commands:

```bash
uv run python -m pipeline --help            # pipeline CLI: power, ndvi, smap, srtm, cdl, ssurgo, all
uv run python -m pipeline power             # run one source
uv run python -m engine.validate            # validate contracts/mock/*
uv run python -m engine.validate web/public/data/fields.geojson web/public/data/strategies.json
uv run pytest

cd web
pnpm dev | pnpm build | pnpm preview | pnpm typecheck | pnpm format
```

### Credentials

MODIS, SMAP and SRTM downloads need a free
[NASA Earthdata](https://urs.earthdata.nasa.gov) account. NASA POWER needs no login.

```bash
cp .env.example .env   # then fill in EARTHDATA_USERNAME / EARTHDATA_PASSWORD
```

`.env` is gitignored. Never commit, print or log credentials.

## How the pieces fit

```
pipeline/  ──►  data/interim/*  ──►  engine/  ──►  python -m engine.export  ──►  web/public/data/*.json  ──►  web/
(download +       (gitignored)       (models)       (must validate against          (static files)           (React app)
 harmonise)                                           contracts/)
```

| Path         | Owner                     | Contents                                                                    |
| ------------ | ------------------------- | --------------------------------------------------------------------------- |
| `contracts/` | shared (all 3 approve)    | JSON Schemas, `crops.csv`, realistic mocks. **The integration point**       |
| `engine/`    | person 1 (engine/pitch)   | FAO-56 water balance, simplified RUSLE, soil-conditioning index, MCDA, export, validation |
| `pipeline/`  | person 2                  | NASA POWER, MODIS NDVI, SMAP, SRTM, USDA CDL, SSURGO download + harmonisation |
| `web/`       | person 3                  | Vite + React + TypeScript, MapLibre GL + deck.gl, Recharts                  |
| `notebooks/` | anyone                    | Exploration only (`# %%` percent-format `.py`). Nothing imports from here   |
| `data/`      | pipeline writes           | Raw + interim data, gitignored                                              |

### Contracts

Everything that crosses a team boundary is defined in [`contracts/`](contracts/README.md):

- `fields.schema.json` + `mock/fields.geojson`: field polygons with `crop_history`
  (2008–2025), `soil`, `season_calendar` (bare periods, stress windows) and
  `stress_index_by_year`.
- `strategies.schema.json` + `mock/strategies.json`: 4 strategies per field. Each metric
  (`water_use_mm`, `erosion_t_ha`, `soil_index`, `income_usd_ha`, `labour_index`) is a
  `{p10, p50, p90}` interval, with `evidence`, `data_gaps` and `verify_locally` entries.
- `crops.csv`: crop traits (FAO-56 Kc stages, N-fixing, root depth, residue, family, price
  source) with a `source` column. Uncertain values are marked `placeholder=true`.

Changing a contract requires approval from all three people. In the same commit, bump
`schema_version` and update the schema, the mock and `web/src/types/contracts.ts`.

### Swapping regions

The pipeline defines a backend interface (`get_crop_history()` and `get_soil()` in
`pipeline/interfaces.py`). The region and backend are set in `pipeline/config.py`. To support
another country, add a backend to `pipeline/backends/` instead of rewriting the US one.

## Contributing

The full rules are in [`AGENTS.md`](AGENTS.md). `CLAUDE.md` and `GEMINI.md` are symlinks to
it, so every coding agent reads the same rules. In short:

- Edit only your own directory. Put cross-team requests in `TASKS.md` under
  **Blockers / requests**.
- Run `make check` before every commit. Make small, frequent commits
  (`engine: add Kc curve`).
- Run `git pull --rebase` before `git push`. Never force-push `main`.
- Don't mass-reformat, don't add new dependencies without asking, and don't use deep
  learning.
- Mark placeholder numbers explicitly. Never present a placeholder as a measured value.

The board and the hackathon timeline are in [`TASKS.md`](TASKS.md). Key times: data ready
Sat 20:00, MVP frozen Sun 08:00, submission Sun 12:30.

## Data sources

NASA POWER (daily weather 1995–2025), MODIS MOD13Q1 NDVI, SMAP L3 soil moisture, SRTM 30 m
DEM, USDA NASS Cropland Data Layer 2008–2025, and USDA NRCS SSURGO soils.
