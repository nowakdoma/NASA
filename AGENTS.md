# FieldShift — instructions for all coding agents and humans

> `CLAUDE.md` and `GEMINI.md` are symlinks to this file. Edit only `AGENTS.md`.

## Goal

FieldShift is a decision-support tool for the NASA Space Apps 2026 challenge
"Field Shift: Adapting Farms with NASA Data". For **Finney County, Kansas** (FIPS 20055)
it shows:

- a map of irrigated fields coloured by crop (USDA CDL history 2008–2025) with a year slider;
- a per-field "passport": crop history, bare-soil periods, water/heat stress windows, soil;
- five farmer priority sliders: water, income, soil organic matter, erosion, labour;
- a comparison of 4 rotation strategies (current + 3 alternatives) with p10/p50/p90 intervals
  from the 1995–2025 weather distribution, a "P(best)" under uncertain priorities, and a
  "what we don't know / verify locally" box.

**Results are decision support with uncertainty, never recommendations.** The tool supports,
not replaces, farmer judgment. In code, UI copy, docs and the pitch: say "under these
priorities, strategy X scores highest in N % of weather/weight samples", never "you should
plant X". Always show intervals and data gaps next to point values.

All computation is offline. The web app reads only static JSON/GeoJSON from `web/public/data/`.

## Layout and ownership

| Path          | Owner                          | What lives there                                                                 |
| ------------- | ------------------------------ | -------------------------------------------------------------------------------- |
| `contracts/`  | **shared — human approval**    | JSON Schemas, `crops.csv`, realistic mocks. The integration point.               |
| `engine/`     | person 1 (engine/design/pitch) | FAO-56 water balance, simplified RUSLE, soil-conditioning index, MCDA, export    |
| `pipeline/`   | person 2                       | Download + harmonise NASA POWER, MODIS NDVI, SMAP, SRTM, CDL, SSURGO             |
| `web/`        | person 3                       | Vite + React + TS, MapLibre GL + deck.gl, Recharts                               |
| `notebooks/`  | anyone                         | Exploration only, small cells (`# %%` percent format). Nothing imports from here |
| `data/`       | pipeline writes                | gitignored raw + interim. Only small processed outputs go to `web/public/data/`  |
| root files    | person 1                       | `AGENTS.md`, `TASKS.md`, `Makefile`, `pyproject.toml`                            |

Rules:

1. **An agent edits only its owner's directory.** If you need a change elsewhere, write it
   in `TASKS.md` under "Blockers / requests" and tell your human.
2. **`contracts/` changes only with explicit human approval** from all three people. Bump
   `schema_version` and update schema + mock + `web/src/types/contracts.ts` in the same commit.
3. Data flow: `pipeline/` → `data/interim/*` → `engine/` → `python -m engine.export` →
   `web/public/data/*.json` (must validate against `contracts/`).

## Commands

```bash
make setup    # uv sync + pnpm install + pre-commit install
make data     # run pipeline (stubs for now; downloads need .env Earthdata creds)
make export   # engine → web/public/data (currently copies contracts/mock)
make dev      # Vite dev server on http://localhost:5173
make check    # ruff, pytest, contract validation, prettier, tsc, web build — must pass
```

Python: `uv run python -m engine.validate`, `uv run pytest`, `uv run python -m pipeline --help`.
Web: `cd web && pnpm dev | pnpm build | pnpm typecheck | pnpm format`.

## Working rules

- **Run `make check` before every commit.** Do not commit with a failing check.
- **Small, frequent commits** with clear messages (`engine: add Kc curve`, `web: field panel`).
- **`git pull --rebase` before `git push`.** Never force-push `main`.
- **Do not mass-reformat or refactor.** Format only the files you changed. No renames or moves
  of other people's code. No drive-by "cleanups".
- **Secrets only in `.env`** (gitignored; template in `.env.example`). Never print, log or
  commit credentials.
- **No new dependencies without asking the humans.** Current allow-list is in
  `pyproject.toml` and `web/package.json`.
- **No deep learning.** Modelling is statistical/process-based. LightGBM + conformal
  intervals are a later optional step, only if time allows.
- Do not download large data into the repo; `data/` is gitignored.
- Mark placeholder or uncertain numbers explicitly (`placeholder=true`, `"mock": true`, or a
  `data_gaps` entry). Never present a placeholder as a measured value.
- Environment: WSL2 Ubuntu, LF line endings (`.gitattributes`), Python 3.11 via uv, Node 22
  + pnpm 9 (corepack). Keep the repo inside the Linux filesystem (`~/...`), not `/mnt/c`.
  On WSL1 the Makefile sets `UV_LINK_MODE=copy UV_CONCURRENT_INSTALLS=1` (uv otherwise fails
  with ENOMEM) and numpy prints a harmless `longdouble` warning.

## Timeline (Space Apps 2026 weekend)

- **Sat 20:00** — real data ready in contract format
- **Sun 08:00** — MVP frozen (only bug fixes + pitch after this)
- **Sun 12:30** — submission (hard deadline 13:30)
