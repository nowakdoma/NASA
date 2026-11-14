# FieldShift — 3-minute pitch (7 slides)

Deck (web slides, present full screen; PDF/PPTX export from its Share menu):
https://claude.ai/artifact/5jxJkDPHP1LpFa72Gqy5zn — private until shared from its Share menu.

Rules for whoever presents: decision support, never "you should plant". Every number below is
from the app's current data (FIN-030, contracts v0.4). Do not add numbers that are not here.

| Time      | Slide                  | Say (short)                                                                                                                                                                                               |
| --------- | ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0:00–0:15 | 1 FieldShift           | Finney County, Kansas, pivots on the Ogallala. One question: what could a different rotation do for my field, with less water to pump?                                                                   |
| 0:15–0:40 | 2 Water from orbit     | NASA GRACE/GRACE-FO, 259 months: about −0.86 cm a year, ~21 cm since 2002 on the trend line (R² 0.80). Regional ~300 km signal, total water storage, not one well. Every rotation is now a water choice. |
| 0:40–1:00 | 3 Four steps           | Your field → what matters (incl. how much you can pump) → compare as ranges → adviser summary. We say "came out on top in about N of 10 weather runs", never "plant X".                                  |
| 1:00–1:25 | 4 Four NASA datasets   | POWER (weather, heat), MODIS (months without green cover), GRACE (water trend), SRTM (slope) + USDA crop map and soil. Each with where it can be wrong. FAO-56 + RUSLE, no black-box AI.                 |
| 1:25–1:55 | 5 Field 30             | Real pivot by the Arkansas River (satellite view). 18 years of crops, nine of alfalfa. No green cover: about 3 months a year in 2008–2012, under 1 in 2021–2025.                                           |
| 1:55–2:35 | 6 One constraint       | Balanced, no limit: alfalfa–corn on top in about 5 of 10 runs (needs ~18 in). Click. 14 in limit: sorghum–wheat–cover on top in about 8 of 10. Honest cost: ~$12,400 vs ~$54,000 typical-year net.       |
| 2:35–3:00 | 7 Ranges, not promises | 1-in-10 low/high on every value, "check locally" (water district, K-State, NRCS), "what we don't know". Next: whole weather years, validation, more counties. Supports judgment, never replaces it.       |

## Live demo path (if presenting the app instead of slides 5–6)

1. Start screen → "Try an example field (Field 30)".
2. Map → Satellite: the pivot by the Arkansas River.
3. Next → Balanced, water limit "Not sure / no limit" → Next: alfalfa–corn ~5/10.
4. Back → choose 14 in → Next: sorghum–wheat–cover ~8/10, the excluded list says why.
5. Next → adviser summary → Print or save as PDF.

## Q&A

- **Why no machine learning?** One crop cycle a year and 31 weather years is a small sample.
  Process models (FAO-56 water balance, RUSLE) stay physically bounded and explainable.
- **Is GRACE your groundwater?** No. It is total water storage over ~300 km, a regional
  signal; the app says so next to the chart.
- **Why only 50 fields?** Fields with crops we cannot cost honestly (potatoes, other hay) are
  left out rather than given invented income numbers.
- **What's uncertain?** Prices and costs are fixed K-State budgets; land rent and pivot/well
  costs are not subtracted; wind erosion is not modelled; weather is a ~50 km grid. All listed
  in "What we don't know" in the app and on the printout.
- **Scale?** All NASA inputs are global; soils and crop maps are national in the US. The app
  is static files, so a water district or extension office can host it at no running cost.
