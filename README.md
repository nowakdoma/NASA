# FieldShift

**What could a different crop rotation do for _your_ field, when there is less water to pump?**

FieldShift is a free web tool for farmers in Finney County, Kansas (FIPS 20055), built on NASA
Earth observation data for the [NASA Space Apps 2026](https://www.spaceappschallenge.org/)
challenge **"Field Shift: Adapting Farms with NASA Data"**.

| | |
| --- | --- |
| **Try the app** | **https://nowakdoma.github.io/NASA/** (no account, works on phone and desktop) |
| **Pitch deck** (7 slides) | https://www.figma.com/slides/BwBCfFOnQlypsikuAxev7I |
| **Source code** | this repository |

> FieldShift supports a farmer's judgment. It never replaces it. We show ranges and how often an
> option came out on top under the farmer's own priorities. We never say "you should plant X".

## Try it in 2 minutes

1. Open **https://nowakdoma.github.io/NASA/** and choose **"Try an example field (Field 30)"**.
2. **Your field:** switch the map to **Satellite** to see the real pivot by the Arkansas River.
   You get 18 years of crops and the months each year the soil had no green cover.
3. **What matters:** keep the priorities balanced and leave the water limit at "no limit".
   **Compare:** alfalfa–corn comes out on top in about **5 of 10** weather runs.
4. Go back and set the water limit to **14 in**. Now sorghum–wheat–cover crop comes out on top in
   about **8 of 10** runs, and the app explains why. It also shows the income cost of the change.
5. **Adviser summary:** print or save a one-page PDF to take to the water district or extension office.

## The problem

Finney County farms with **center pivots**: a long sprinkler arm that rotates around a well,
which is why the fields look like circles from space. The water comes from the **Ogallala
aquifer**, which refills far more slowly than it is pumped. NASA's GRACE/GRACE-FO satellites show
the region's stored water falling about **0.86 cm a year, roughly 21 cm since 2002**. Every
choice of what to plant is now also a choice about water, traded against income, soil health,
erosion and work. Farmers need to see those trade-offs for their own field before they commit a
season.

## How it works

```
NASA + USDA data  ──►  process models (per field, per rotation)  ──►  ranking under uncertainty
```

1. **Data.** Fields are detected automatically as pivot circles in the USDA crop map. Each field
   gets its crop history (2008–2025), bare-soil months (MODIS), soil (SSURGO), slope (SRTM) and
   31 years of daily weather (NASA POWER, 1995–2025). The current rotation is the shortest
   repeating crop cycle in the last 8 years, and three alternatives are added for comparison.
2. **Models.** These are physical, explainable models, not black-box AI:
   - **FAO-56 daily water balance:** Penman-Monteith reference evapotranspiration × crop
     coefficients, a soil water bucket, and pivot irrigation with the farmer's seasonal water
     limit. This gives **water use**.
   - **Yield response to water stress** (FAO-33 Ky) × prices − K-State crop budget costs −
     pumping cost. This gives **income**.
   - **RUSLE** (A = R·K·LS·C·P), with rainfall erosivity from POWER, soil erodibility from SSURGO
     and slope from SRTM. This gives **water erosion**.
   - **NRCS-style soil conditioning index:** residue, field operations and erosion. This gives the
     **soil organic matter trend**.
   - **Labour:** hours per hectare from the crop budgets.
3. **Ranges.** Every rotation is simulated starting from each weather year 1995–2025. Each
   result is shown as a **1-in-10 low, typical and 1-in-10 high year** (p10/p50/p90).
4. **Ranking.** A multi-criteria analysis runs **2,000 Monte Carlo draws** live in the browser.
   Priority weights are sampled from a Dirichlet distribution around the farmer's sliders, and
   outcomes are sampled from their ranges. "On top in N of 10 runs" is the share of draws in
   which a rotation scores highest. It updates instantly as the sliders move.

All heavy computation runs offline in Python. The web app only reads static JSON/GeoJSON files.

## What we don't know

Each result in the app has a "What we don't know / verify locally" box. The main limits:

- GRACE is a regional signal (~300 km) of total water storage, not one farmer's well.
- NASA POWER weather is a ~50 km grid and smooths local storms.
- MODIS has 250 m pixels; dormant alfalfa or standing stalks can read as bare soil.
- Wind erosion is not modelled. Fields are approximated as ideal circles.
- Prices and costs are fixed K-State budgets. Land rent and pivot/well costs are not subtracted.
- Some model parameters are marked as placeholders in the code and in the exported data.
- Only 50 fields are included. Fields with crops we cannot cost honestly are left out rather
  than given invented numbers.

## Data and resources

**NASA data**

- [NASA POWER](https://power.larc.nasa.gov/): daily weather 1995–2025 (water balance, heat
  stress, frost, rainfall erosivity)
- [MODIS MOD13Q1 v061 NDVI](https://lpdaac.usgs.gov/products/mod13q1v061/), read via
  [Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/dataset/modis-13Q1-061):
  months without green cover
- [GRACE/GRACE-FO JPL RL06.3 mascons](https://grace.jpl.nasa.gov/data/get-data/jpl_global_mascons/):
  regional water storage trend
- [SRTM GL1 30 m](https://lpdaac.usgs.gov/products/srtmgl1v003/), read via
  [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/): field slope

**Other data and methods**

- [USDA NASS Cropland Data Layer](https://www.nass.usda.gov/Research_and_Science/Cropland/SARS1a.php)
  2008–2025: field outlines and crop history
- [USDA NRCS SSURGO](https://sdmdataaccess.sc.egov.usda.gov/): soil water capacity, erodibility,
  organic matter
- [K-State Research and Extension](https://agmanager.info/farm-mgmt-guides): crop budgets, prices
  and irrigation costs
- [FAO-56](https://www.fao.org/4/x0490e/x0490e00.htm) (Allen et al., 1998) and
  [RUSLE, USDA Agriculture Handbook 703](https://www.ars.usda.gov/arsuserfiles/64080530/rusle/ah_703.pdf)
- Map imagery: [USGS The National Map](https://basemap.nationalmap.gov/) and
  [CARTO Positron](https://carto.com/basemaps). Icon: [Flaticon "yield"](https://www.flaticon.com/free-icons/yield)

## Built with

Python 3.11 (numpy, pandas, rasterio) for the data pipeline and models. TypeScript, React, Vite,
MapLibre GL, deck.gl and Recharts for the web app. JSON Schemas validate every file that passes
between the two. The app is hosted on **GitHub Pages**: no server, no database and no running
costs. A water district or extension office could host its own copy for free.

## Use of AI (Super Intelligence) tools

We used **Claude** (Anthropic), mainly through Claude Code, as a coding and writing assistant.
It helped with parts of the data pipeline, models, web app and tests, with documentation and the
pitch script, and with the slide layout. Commits where it contributed carry a
`Co-Authored-By: Claude` line. The team chose the methods and data, reviewed the code and checked
the numbers against the sources. **No images, video or audio in the project are AI-generated.**
Satellite imagery comes from USGS, and the screenshots are of our own app. No NASA logos or
branding are used.

---

## For developers

### Deployment

Every push to `main` builds `web/` and publishes it to GitHub Pages
([`.github/workflows/pages.yml`](.github/workflows/pages.yml)). The site is served under
`/NASA/`, and data paths use `import.meta.env.BASE_URL`.

### Run locally

Requirements: Linux, macOS or WSL2, [uv](https://docs.astral.sh/uv/), **Node 22** and **pnpm 9**
(`corepack enable`), plus `make`.

```bash
git clone https://github.com/nowakdoma/NASA fieldshift
cd fieldshift
make setup     # uv sync (Python 3.11) + pnpm install + pre-commit hook
make dev       # http://localhost:5173 (uses the data already in web/public/data)
```

| Command       | What it does                                                                        |
| ------------- | ----------------------------------------------------------------------------------- |
| `make setup`  | Install Python deps (uv) and web deps (pnpm), and install the pre-commit hook      |
| `make data`   | Run the data pipeline (`python -m pipeline all`). Needs Earthdata credentials       |
| `make export` | Run the engine → `web/public/data/*.json`                                           |
| `make dev`    | Start the Vite dev server                                                           |
| `make check`  | ruff, pytest, contract validation, prettier, tsc and web build. Must pass before commits |

Data downloads (MODIS, SRTM) need a free [NASA Earthdata](https://urs.earthdata.nasa.gov) token
in `.env` (template: `.env.example`, gitignored). NASA POWER needs no login.

### Repository layout

```
pipeline/  ──►  data/interim/*  ──►  engine/  ──►  python -m engine.export  ──►  web/public/data/*.json  ──►  web/
(download +       (gitignored)       (models)       (validated against             (static files)           (React app)
 harmonise)                                          contracts/)
```

| Path         | Contents                                                                         |
| ------------ | -------------------------------------------------------------------------------- |
| `contracts/` | JSON Schemas, `crops.csv`, mocks: the integration point between team members     |
| `pipeline/`  | Download and harmonise NASA POWER, MODIS, GRACE, SRTM, USDA CDL and SSURGO        |
| `engine/`    | FAO-56 water balance, RUSLE, soil conditioning index, rotations, MCDA, export     |
| `web/`       | Vite + React + TypeScript app, MapLibre GL + deck.gl, Recharts                    |
| `reports/`   | Pitch scripts (English and Polish) and research notes                             |

The pipeline uses a backend interface (`pipeline/interfaces.py`), so supporting another region
means adding a backend in `pipeline/backends/`, not rewriting the US one. Team working rules are
in [`AGENTS.md`](AGENTS.md).
