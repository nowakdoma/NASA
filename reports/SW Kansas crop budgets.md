# K-State 2027 budgets reset FieldShift's crop economics

For Finney County, use the **K-State 2027 Farm Management Guides (dated Nov-01-2026)** as the single source of yields, prices and variable costs. They are the newest official set. They cover every crop in `engine/params.py` except the rye cover crop and fallow, and their prices and costs share one vintage. With these budgets, irrigated corn is a **225 bu/ac (14.1 t/ha)** crop at **$4.88/bu (192 USD/t)** with **$531.79/ac (1,314 USD/ha)** of variable cost excluding pumping energy. Pumping on natural gas from a 300 ft well costs **$3.27 per acre-inch, or 0.318 USD per mm per ha**. The engine's current pumping placeholder of 0.95 USD/mm/ha is about three times too high. Other placeholders are also off. Fallow is too cheap at 70 USD/ha against a sourced build-up of about 170–198 USD/ha. Cotton and alfalfa costs are too low. The per-crop labour hours are about five times the K-State field-operation hours. Prices are the largest uncertainty. K-State's 2027 planning prices sit 20–60 % above USDA NASS's preliminary 2025 Kansas prices received. Wheat moved 33 % between the 2026 and 2027 budget editions. Sample price as a whole price year, using the 2020–2025 NASS range, rather than treating it as fixed. Three numbers have no published value for Finney County: actual well capacity, pumping lift, and fuel mix. Their recommended values are judgement and must carry `placeholder=true` and a `data_gaps` entry.

Conversions used throughout: 1 ac = 0.4047 ha. A corn or sorghum bushel is 56 lb (25.40 kg); a wheat or soybean bushel is 60 lb (27.22 kg). A short ton is 0.9072 t, and 1 cwt is 100 lb. 1 acre-inch is 102.8 m³, and USD per acre-inch ÷ 10.28 = USD per mm per ha. "Direct" means K-State "total direct expenses". These are operating costs including 7.6 % operating interest. They exclude cash rent and capital recovery, which K-State lists separately as "fixed".

## One budget vintage covers seven crops, and prices are its weak point

K-State's 2027 guides for Southwest Kansas assume middle yields on center pivots as follows. Corn is **225 bu/ac** on 15 in of water. Grain sorghum is **160 bu/ac** on 12 in. Soybeans are **65 bu/ac** on 11 in. Winter wheat is **70 bu/ac** on 6 in, but that budget is a *limited-irrigation* Western KS budget, not full irrigation ([irrigated corn][c27]; [sorghum][s27]; [soybeans][sb27]; [wheat][w27]). The minor crops come from the same release. Irrigated alfalfa yields **5.0 tons/ac/yr** on 19 in with 4 cuttings ([alfalfa][a27]). Cotton yields **1,500 lb lint/ac** on 8 in ([cotton][ct27]). Oil sunflower yields **24 cwt/ac** on 10 in ([sunflower][sf27]). Each guide also gives low and high yield levels, for example corn at 185 and 245 bu/ac. These are planning scenarios with their own water depths, not weather percentiles. If the UI shows them, label them "budget scenario range". Note that the low and high alfalfa and cotton budgets set custom operations to $0. That drops hay harvest and ginning, which is a K-State error, so use only the middle-yield cost columns ([alfalfa][a27]; [cotton][ct27]).

Observed yields temper the corn figure. NASS stopped publishing irrigated and non-irrigated county yields for Kansas after 2018 ([NASS Kansas county estimates][nassce]). Finney County itself is suppressed in the 2023 county release for all four grains. The published Southwest-district counties averaged **179 bu/ac corn (11.2 t/ha)**, ranging 150–211 bu/ac, all practices combined, in 2023 ([NASS Quick Stats, corn 2023][qscorn]). Irrigated soybeans averaged **57.8 bu/ac**. Since 225 bu/ac sits above the best published county, treat it as an attainable well-managed pivot yield, which is what FAO-33 `ym` means. Do not present it as a county average.

Prices conflict sharply across sources. The 2027 guides use corn **$4.88/bu**, sorghum **$4.56/bu**, soybeans **$12.04/bu** and irrigated wheat **$6.98/bu** ([c27]; [s27]; [sb27]; [w27]). They use alfalfa **$196.51/ton**, cotton lint **$0.77/lb** plus cottonseed at $0.12/lb, and sunflower **$19.50/cwt** ([a27]; [ct27]; [sf27]). The 2026 edition used wheat at $5.24–5.27 and soybeans at $10.08 ([DRY-WF-26][dwf26]; [irrigated soybeans 2026][sb26]). That is a **33 % and 19 % jump in one year**. NASS Kansas marketing-year prices received are lower. The 2025 preliminary prices were corn **$4.00**, sorghum **$6.10/cwt ($3.42/bu)**, wheat **$4.60**, soybeans **$9.95**, alfalfa **$121/ton**, cotton **$0.611/lb** and sunflower **$21.00/cwt** ([NASS Crop Values 2025 Summary][cv26]). The 2020–2024 means are corn $5.28, sorghum $5.33/bu, wheat $6.51, soybeans $11.97, alfalfa $190/ton, cotton $0.744 and sunflower $23.04/cwt ([cv26]; [Crop Values 2023][cv24]; [Crop Values 2022][cv23]). The NASS series shows that prices for all crops rise and fall together: 2021–2022 were high for every grain. Draw a whole price year jointly from 2020–2025 rather than sampling each crop independently. One structural point also matters. Kansas sorghum averaged roughly corn's per-bushel price over 2020–24 (ratio 1.01). K-State's 2027 discount of 7 % below corn is within the recent range, because sorghum fell below corn in 2024–25.

## Variable costs, net of pumping, run from 565 to 2,013 USD/ha

The table below gives the 2027 middle-yield figures. Column A subtracts only the "Irrigation energy (NG)" line from total direct cost. Column B also subtracts irrigation labour and irrigation repair and maintenance, so that every water-proportional cost can move into the per-mm pumping rate. Column B for corn, sorghum, soybeans and wheat comes straight from the budget lines ([c27]; [s27]; [sb27]; [w27]). For alfalfa, cotton and sunflower, I derived the irrigation R&M at the budget's $0.36 per acre-inch, and those Column B values are therefore derived. Crop-specific inclusions follow the table.

| Crop (irrigated, 2027) | Yield US | Yield t/ha | Price US | Price USD/t | Direct total $/ac | A: excl. energy $/ac (USD/ha) | B: excl. all irrigation items $/ac (USD/ha) | Water in (mm) |
|---|---|---|---|---|---|---|---|---|
| Corn | 225 bu/ac | 14.12 | $4.88/bu | 192.1 | 580.79 | 531.79 (1,314) | 513.01 (1,268) | 15 (381) |
| Grain sorghum | 160 bu/ac | 10.04 | $4.56/bu | 179.5 | 403.55 | 364.35 (900) | 349.33 (863) | 12 (305) |
| Soybeans | 65 bu/ac | 4.37 | $12.04/bu | 442.4 | 264.65 | 228.72 (565) | 214.95 (531) | 11 (279) |
| Winter wheat (limited irr.) | 70 bu/ac | 4.71 | $6.98/bu | 256.5 | 284.29 | 264.69 (654) | 257.18 (635) | 6 (152) |
| Alfalfa hay | 5.0 ton/ac | 11.21 | $196.51/ton | 216.6 | 544.66 | 482.60 (1,193) | 458.81 (1,134)* | 19 (483) |
| Cotton (lint) | 1,500 lb/ac | 1.68 | $0.77/lb | 1,697.5 | 840.59 | 814.46 (2,013) | 804.44 (1,988)* | 8 (203) |
| Oil sunflower | 2,400 lb/ac | 2.69 | $19.50/cwt | 429.9 | 356.24 | 323.57 (800) | 311.05 (769)* | 10 (254) |

\* Irrigation R&M derived at $0.36/ac-in.

What the costs include. Every budget covers seed, fertilizer, herbicide, insecticide and fungicide, crop insurance, consulting, diesel at $5.78/gal, machinery repairs, operator and hired labour, miscellaneous costs and 7.6 % operating interest. Some crops add crop-specific custom work:

- **Corn**: fertilizer $190.82 and seed $118.93 ([c27]).
- **Sorghum**: $46.56 of custom hauling ([s27]).
- **Alfalfa**: $231.68 of custom hay harvest. This is swathing and raking ×4 plus 7.6 large round bales at $17.50. Hauling and storage are excluded ([a27]). The rates match the [Kansas Custom Rates 2026][cr26] survey.
- **Cotton**: $222.00 of ginning at $0.148/lb lint ([ct27]). The custom-rates survey uses the same $0.148/lb figure, but as a *harvesting* charge ([cr26]). That is an unresolved labelling conflict.
- **Cotton revenue**: cottonseed brings **$243/ac (600 USD/ha)** of income, which belongs in `other_revenue_usd_ha`.

Dryland budgets matter because the engine prices a dryland wheat-sorghum-fallow strategy with the same per-crop costs as irrigated crops. That overstates dryland costs by about $100–300/ac, as the table below shows.

| Crop (dryland) | Yield | t/ha | Direct $/ac (USD/ha) | Labour h/ac (h/ha) | Source |
|---|---|---|---|---|---|
| Corn, W-C-F | 82 bu | 5.15 | 281.05 (694) | 0.37 (0.91) | [DRY-CORN-27][dc27] |
| Sorghum, W-S-F | 85 bu | 5.34 | 225.85 (558) | 0.37 (0.91) | [DRY-SORG-27][ds27] |
| Soybeans, W-SB-F | 25 bu | 1.68 | 168.12 (415) | 0.30 (0.74) | [DRY-SOY-27][dsb27] |
| Wheat, W-F (2026 edition, $5.27/bu) | 54 bu | 3.63 | 196.30 (485) | 0.49 (1.21) | [DRY-WF-26][dwf26] |
| Cotton, W-CT-F (no crop insurance) | 900 lb | 1.01 | 577.89 (1,428) | 0.71 (1.75) | [dryland cotton][dct27] |
| Sunflower, W-SF-F | 1,600 lb | 1.79 | 226.52 (560) | 0.29 (0.72) | [dryland sunflower][dsf27] |

Three caveats apply to these dryland budgets. First, no 2027 Southwest KS dryland wheat budget exists, so the 2026 edition is the only option, and its price is out of vintage. Second, the "non-irrigated" SW alfalfa budget (3.0 ton/ac, $275.15/ac) looks like sub-irrigated ground and should not be used for dryland uplands ([dryland alfalfa][da27]). Third, fixed costs are not part of variable cost. Irrigated fixed costs are $469–489/ac, including **$235.29/ac of pivot, well and power-unit capital** and $185/ac rent. Dryland fixed costs are $97–136/ac, with rent at $52.50/ac ([c27]; [dc27]). Fixed costs matter only to a strategy that retires a pivot.

**Rye cover crop and chemical fallow have no K-State budget.** They must be built from parts.

The rye build-up comes to **$52–59/ac (128–146 USD/ha)**:
- Seed: K-State's drilling rate is 55–60 lb/ac ([K-State MF3504][mf3504]). At an Ohio State seed price of $15–20 per 50-lb bag, that is $16.5–24/ac ([OSU CFAES][osu]); the price is not from Kansas.
- Drilling: Western-district custom no-till drilling costs $23.67/ac ([cr26]).
- Termination: glyphosate at about $4.18 ([DRY-SORG-27 glyphosate price][ds27]) plus SW ground application at $7.52 ([cr26]).

Chemical fallow comes to **$69–80/ac (170–198 USD/ha)** per fallow period. Southwest Kansas respondents reported fallow herbicide at **$46/ac** dryland and $50/ac irrigated in the 2022 input survey ([K-State 2022 Input Cost Survey][ics22]). On top of that come 3–4 ground passes at $7.52. The pass count is an assumption, and the survey had only 4–5 SW responses. One double-counting risk applies. The W-S-F sorghum budget already carries a **$25.13/ac burndown** that ends the post-wheat fallow ([ds27]). If fallow is costed separately, net out that amount.

## Pumping costs 0.32 USD per mm·ha on gas, and well capacity is the true unknown

Every 2027 irrigated budget uses the same pumping assumptions: **natural gas, 300 ft well, 0.71 Mcf per acre-inch at $4.58/Mcf, for $3.27 per acre-inch**. Irrigation repairs cost $0.36/ac-in, and irrigation labour runs about 0.04 h/ac-in at $22.30/h ([c27]). In metric terms, energy is **0.318 USD/mm·ha** (0.032 USD/m³). Repairs add 0.035 and labour 0.087, for an all-in variable cost of **0.44 USD/mm·ha ($4.52/ac-in)**. K-State publishes no current figure for electric or diesel wells.

The research notes derive electric and diesel figures from the Nebraska Pumping Plant Criteria in K-State MF-2360 (2006, still the K-State method). The method uses 1.551 kWh or 0.1098 gal of diesel per acre-foot per foot of head ([Rogers & Alam, MF-2360][mf2360]). The budget's 0.71 Mcf implies about 382 ft of total dynamic head at criteria efficiency. At that head, electric pumping needs about 49 kWh/ac-in, which costs **$3.95–6.41/ac-in (0.38–0.62 USD/mm·ha)** at $0.08–0.13/kWh, before demand charges. Those electricity prices are assumptions, not sourced Kansas tariffs. Diesel pumping costs $10.5–20.2/ac-in. A 2020 central Kansas sheet gives $1.52/ac-in at a 150 ft lift ([K-State Central KS Irrigation 2020][cki20]). That shows how strongly lift drives cost, and Finney lifts are unmapped.

Applied water per crop has two families of numbers. The planning budgets give corn 15 in, alfalfa 19, sorghum 12, soybeans 11, sunflower 10, cotton 8 and limited-irrigation wheat 6 (see the table above). Reported use is higher. Groundwater Management District 3 (GMD3) averaged **14.6 in/yr across all crops over 2005–2022**, the highest of the Ogallala districts ([KGS Technical Series 25, 2023][ts25]). Per-crop rates in GMD3 during the 2012 drought were corn **20.8 in**, alfalfa 22.6, soybeans 19.3, sorghum 12.2 and wheat 12.0. Finney County's 2008–2012 all-crop mean was 16.9 in ([KDA-DWR/USGS Kansas Irrigation Water Use 2012][dwr12]; pre-2020). The budget depths are reasonable normal-year p50 targets. The 2012 rates are a dry-year p90. Because the engine computes irrigation from FAO-56, these figures serve as validation targets rather than inputs. The engine's 150 mm "limited" cap matches K-State's 6-inch limited-irrigation wheat.

Well capacity has **no published distribution for Finney or GMD3**. K-State sizes pivots by capacity: in/day = gpm × 24 ÷ (450 × acres). Above 0.25 in/day is low risk on silt loams, sands need 0.30 or more, and peak corn demand reaches 0.35–0.50 in/day ([K-State L908][l908]; date unverified). For 125 acres, that means 300 / 500 / 600 / 800 gpm deliver **3.3 / 5.4 / 6.5 / 8.7 mm/day**. The engine's 6.4 mm/day corresponds to about 600 gpm, which is plausible but unsourced. The trend matters more than the level. GMD3 has lost **101 ft (45 %) of saturated thickness**, and the water table falls about 1.8 ft/yr since 1996 ([ts25]). It dropped 1.52 ft in 2024 alone ([Kansas Reflector, 2025][kr25]). A K-State study ties each 100 gpm loss of well yield to 0.47 in less water applied and a 3-point lower chance of planting corn ([K-State, "When the well runs slow"][krex]; seen only as a snippet).

## FAO-33 Ky ranks corn as the most water-sensitive crop

The FAO-33 seasonal yield response factors, as restated in FAO-66, are: maize **1.25**, alfalfa **1.10**, sunflower **0.95**, sorghum **0.90**, soybean **0.85**, cotton **0.85**, and wheat **1.05** overall, with **1.0 for winter wheat** and 1.15 for spring wheat ([FAO-66, Steduto et al. 2012][fao66]; [Moutonnet, FAO/IAEA][mout]). The engine currently uses 1.05 for winter wheat. The Moutonnet table lists 1.0. The FAO-66 summary that lists 1.05 was read through a search summary, not opened. Use 1.0, and use 1.05 as a sensitivity case. The values date from 1979 and are single-season linear approximations with no Kansas calibration. They belong in the "what we don't know" box.

## Recommended parameter set for `engine/params.py`

Each row below is labelled as one of three kinds. **S** values are taken directly from a source. **D** values are derived arithmetically from sources. **R** values are my recommendation or judgement and must stay `placeholder=true`. Prices and costs use the **K-State 2027 edition (Nov-01-2026) consistently**. Wheat at $6.98 is flagged because it is far above NASS 2025p ($4.60). For the price uncertainty band, sample whole NASS Kansas price years from 2020–2025, not ±10 %. Variable costs use Column B, together with an all-in per-mm irrigation cost. That way, irrigation labour, repairs and energy all scale with the water that FAO-56 computes.

| Parameter | Current | Recommended | Kind | Basis |
|---|---|---|---|---|
| `PUMPING_COST_USD_HA_MM` | 0.95 | **0.44** (p10 0.30, p90 0.70) | D / R band | $3.27 + 0.36 + 0.89 per ac-in ([c27]); band covers gas price, lift and electric |
| `IRRIGATION_LABOUR_H_PER_100MM` | 0.4 | **0.39** | D | 0.04 h/ac-in ([c27]) |
| `PIVOT_CAPACITY_MM_DAY` | 6.4 | **5.4** p50 (p10 3.3, p90 8.7) | R | 500 gpm / 125 ac via L908 formula; no Finney data |
| corn ym / price / cost | 12.9 / 180 / 1150 | **14.1 t/ha / 192 / 1,268** | S / S / D | [c27] |
| sorghum | 8.0 / 170 / 600 | **10.0 / 180 / 863** | S / S / D | [s27] |
| winter_wheat | 4.7 / 210 / 450 | **4.7 / 257 / 635**; Ky **1.00** | S / S (flag) / D | [w27]; [mout] |
| soybeans | 4.0 / 380 / 650 | **4.4 / 442 / 531** | S / S / D | [sb27] |
| alfalfa | 12.5 / 190 / 1400 | **11.2 / 217 / 1,134 + 49–89 stand top-up** (see note) ; cycles **4** | S / S / D / R | [a27] |
| cotton | 1.3 / 1500 / 850 | **1.68 / 1,698 / 1,988**; other revenue **600** | S / S / D / S | [ct27] |
| sunflower | 2.5 / 450 / 500 | **2.69 / 430 / 769** | S / S / D | [sf27] |
| rye_cover cost | 90 | **137** (128–146) | D / R | [mf3504], [osu], [cr26] |
| fallow cost | 70 | **185** (170–198) | D / R | [ics22], [cr26] |
| Labour h/ha (field ops, excl. irrigation) | 2.5–10 | corn **1.16**, sorghum **0.84**, soy **0.82**, wheat **1.21**, cotton **1.63**, sunflower **1.24**, alfalfa **0.59** | D | budget hours minus irrigation hours ([c27] etc.) |

Four notes on the table:

- **Alfalfa establishment.** K-State spreads establishment as a flat 3 lb/ac/yr seed charge ($29.12) and states no stand life ([a27]). A 15–20 lb/ac seeding at $9.71/lb costs $146–194/ac. Spread over the engine's 3-year stand, that is $49–65/ac/yr, so add **$20–36/ac (49–89 USD/ha)** to the K-State cost. The seeding rate was seen only in search snippets of K-State alfalfa guides, so mark this as R.
- **Labour scale.** The K-State labour hours exclude management and custom-hired work. Alfalfa's 0.59 h/ha therefore understates the work of coordinating 4 cuttings. If the labour slider must reflect that, add an explicit R term, for example 0.3–0.6 h/ac per cutting, which is unsourced. Rescale `LABOUR_HOURS_FULL_SCALE`, because 12 h/ha now exceeds every crop by about 7×.
- **Dryland costs.** Add a per-irrigation-level cost to the dryland strategies (see the dryland table), or flag that they are over-costed. This change belongs to the engine. Any contract change goes through `TASKS.md`.
- **Yields.** The `ym` values are budget middle yields, not stress-free maxima. Corn at 14.1 t/ha is about 26 % above observed 2023 SW county means.

## Conclusion

Swapping in the sourced numbers changes the ranking itself, not just the totals. Pumping becomes about a third as expensive, which narrows the water-saving advantage of limited and dryland strategies on the income axis. Fallow becomes more than twice as costly, and that weakens wheat-sorghum-fallow. Cotton and alfalfa carry the highest variable costs of any crop, so their appeal depends heavily on price, and their prices are the thinnest-based and most volatile in the NASS record. The decisive unknowns are farm-specific: well capacity, lift, fuel and price received. A farmer knows these and the model does not. That makes them the right items for the "verify locally" box, and natural candidates for user-adjustable inputs rather than hidden constants.

Several values are older than 2020 and should be flagged in `SOURCES`: FAO-33 Ky (1979), MF-2360 pumping criteria (2006), the KDA-DWR 2012 water-use rates and the undated L908 capacity guidance. The undated Ohio State rye seed price is also not from Kansas. None of them has a newer replacement in the notes.

## Sources

- [c27] K-State, *2027 Irrigated Corn (center-pivot) Cost-Return Budget, Southwest Kansas*, Nov-01-2026. https://www.agmanager.info/sites/default/files/wysiwyg/Irrigated%20Corn%20%28center-pivot%29%20Cost-Return%20Budget_Southwest%20Kansas%20_Nov-01-2026.pdf
- [s27] K-State, *2027 Irrigated Grain Sorghum (center-pivot), SW KS*, Nov-01-2026. https://www.agmanager.info/sites/default/files/wysiwyg/Irrigated%20Grain%20Sorghum%20%28center-pivot%29%20Cost-Return%20Budget_Southwest%20KS_Nov-01-2026.pdf
- [sb27] K-State, *2027 Irrigated Soybeans (center-pivot), SW KS*, Nov-01-2026. https://www.agmanager.info/sites/default/files/wysiwyg/Irrigated%20Soybeans%20%28center-pivot%29%20Cost-Return%20Budget_Southwest%20KS_Nov-01-2026.pdf
- [sb26] K-State, *2026 Irrigated Soybeans, SW KS*, Nov-01-2025. https://www.agmanager.info/sites/default/files/wysiwyg/Irrigated%20Soybeans%20%28center-pivot%29%20Cost-Return%20Budget_Southwest%20KS_Nov-01-2025.pdf
- [w27] K-State, *2027 Irrigated Wheat, Western KS, Limited irrigation*, Nov-01-2026. https://www.agmanager.info/sites/default/files/wysiwyg/Irrigated%20Wheat%20Cost-Return%20Budget%20in%20Western%20KS_Limited%20irrigation_Nov-01-2026.pdf
- [a27] K-State, *2027 Irrigated Alfalfa (Center-Pivot), Western Kansas*, Nov-01-2026. https://agmanager.info/sites/default/files/wysiwyg/Irrigated%20Alfalfa%20%28Center-Pivot%29%20Cost-Return%20Budget_Western%20Kansas_Nov-01-2026.pdf
- [da27] K-State, *2027 Alfalfa Cost-Return Budget in Southwest Kansas* (non-irrigated list), Nov-01-2026. https://agmanager.info/sites/default/files/wysiwyg/Alfalfa%20Cost-Return%20Budget%20in%20Southwest%20Kansas__Nov-01-2026.pdf
- [ct27] K-State, *2027 Irrigated Cotton (Center-Pivot), Southwest Kansas*, Nov-01-2026. https://agmanager.info/sites/default/files/wysiwyg/Irrigated%20Cotton%20%28Center-Pivot%29%20Cost-Return%20Budget_Southwest%20Kansas_Nov-01-2026.pdf
- [dct27] K-State, *2027 Cotton (W-CT-F), Southwest KS*, Nov-01-2026. https://agmanager.info/sites/default/files/wysiwyg/Cotton%20Cost-Return%20Budget%20%28W-CT-F%29_Southwest%20KS_Nov-01-2026.pdf
- [sf27] K-State, *2027 Irrigated Oil-Type Sunflowers (Center-Pivot), Western Kansas*, Nov-01-2026. https://agmanager.info/sites/default/files/wysiwyg/Irrigated%20Oil-Type%20Sunflowers%20%28Center-Pivot%29%20Cost-Return%20Budget_Western%20Kansas_Nov-01-2026.pdf
- [dsf27] K-State, *2027 Oil-Type Sunflowers (W-SF-F), Western KS*, Nov-01-2026. https://agmanager.info/sites/default/files/wysiwyg/Oil-Type%20Sunflowers%20Cost-Return%20Budget%20%28W-SF-F%29_Western%20KS%20_Nov-01-2026.pdf
- [dc27] K-State, *2027 Corn (W-C-F), Southwest Kansas*, Nov-01-2026. https://www.agmanager.info/sites/default/files/wysiwyg/Corn%20Cost-Return%20Budget%20%28W-C-F%20Rotation%29%20in%20Southwest%20Kansas__Nov-01-2026.pdf
- [ds27] K-State, *2027 Grain Sorghum (W-S-F), Southwest Kansas*, Nov-01-2026. https://www.agmanager.info/sites/default/files/wysiwyg/Grain%20Sorghum%20%28W-S-F%20Rotation%29%20Cost-Return%20Budget%20in%20Southwest%20Kansas__Nov-01-2026.pdf
- [dsb27] K-State, *2027 Soybean (W-SB-F), Southwest Kansas*, Nov-01-2026. https://www.agmanager.info/sites/default/files/wysiwyg/Soybean%20Cost-Return%20Budget%20%28W-SB-F%20Rotation%29%20in%20Southwest%20Kansas__Nov-01-2026.pdf
- [dwf26] K-State, *2026 Wheat (W-F), Southwest KS*, Nov-01-2025. https://www.agmanager.info/sites/default/files/wysiwyg/Wheat%20%28W-F%29%20Cost-Return%20Budget%20in%20Southwest%20KS__Nov-01-2025.pdf
- [cki20] K-State, *Central Kansas Irrigation (13.5 inches)*, Nov-01-2020. https://agmanager.info/sites/default/files/wysiwyg/Central%20Kansas%20Irrigation_13.5%20inches_Nov-01-2020.pdf
- [cr26] KDA / K-State, *Kansas Custom Rates 2026*. https://www.agmanager.info/sites/default/files/pdf/CustomRates_2026.pdf
- [ics22] Tsoodle & Li, *2022 Input Cost Survey in Kansas*, K-State, 2022. https://www.agmanager.info/sites/default/files/pdf/2022_InputCostReport.pdf
- [mf3504] K-State, *Post-corn going to soybean: use cereal rye*, MF3504 (year not verified). https://bookstore.ksre.ksu.edu/download/post-corn-going-to-soybean-use-cereal-rye_MF3504
- [osu] Ohio State CFAES, *Attributes and Considerations for the Use of Cereal Rye as a Cover Crop* (undated; not Kansas). https://cfaes.osu.edu/fact-sheet/attributes-and-considerations-use-cereal-rye-cover-crop
- [cv26] USDA NASS, *Crop Values 2025 Summary*, Feb 2026. https://esmis.nal.usda.gov/sites/default/release-files/795791/cpvl0226.pdf
- [cv24] USDA NASS, *Crop Values 2023 Summary*, Feb 2024. https://esmis.nal.usda.gov/sites/default/release-files/k35694332/g158d382b/0k226z97k/cpvl0224.txt
- [cv23] USDA NASS, *Crop Values 2022 Summary*, Feb 2023. https://esmis.nal.usda.gov/sites/default/release-files/k35694332/b85171637/x346fg88n/cpvl0223.txt
- [nassce] USDA NASS Kansas, *County Estimates* page. https://www.nass.usda.gov/Statistics_by_State/Kansas/Publications/County_Estimates/index.php
- [qscorn] USDA NASS Quick Stats, Kansas county corn 2023. https://quickstats.nass.usda.gov/results/B224666A-2A56-3AD1-9A44-9F21B4499620
- [mf2360] Rogers & Alam, *Comparing Irrigation Energy Costs*, K-State MF-2360, 2006 (**pre-2020**). https://bookstore.ksre.ksu.edu/download/comparing-irrigation-energy-costs_MF2360
- [ts25] Whittemore, Butler & Wilson, *2023 Status of the High Plains Aquifer in Kansas*, KGS Technical Series 25, Nov 2023. https://kgs.ku.edu/sites/kgs/files/files/TechSeriespdfs/TS25.pdf
- [dwr12] KDA-DWR & USGS, *Kansas Irrigation Water Use 2012* (**pre-2020**). https://kgi.contentdm.oclc.org/digital/api/collection/p16884coll5/id/228/download
- [l908] K-State, *Considerations for Nozzle Package Selection for Center Pivots*, L908 (date unverified). https://bookstore.ksre.ksu.edu/download/considerations-for-nozzle-package-selection-for-center-pivots_L908
- [krex] K-State K-REx, *When the well runs slow* (snippet only). https://krex.k-state.edu/items/6b441874-e9a1-4c0b-b165-5a3f64b48020
- [kr25] Kansas Reflector, Jan 28 2025. https://kansasreflector.com/2025/01/28/ogallala-aquifer-drops-by-more-than-a-foot-in-parts-of-western-kansas/
- [fao66] Steduto et al., *Crop yield response to water*, FAO I&D Paper 66, 2012 (restating FAO-33, 1979, **pre-2020**). https://fao.org/4/i2800e/i2800e.pdf
- [mout] Moutonnet, *Yield response factors of field crops to deficit irrigation*, FAO/IAEA (**pre-2020**). https://www.fao.org/4/Y3655E/y3655e04.htm

[c27]: https://www.agmanager.info/sites/default/files/wysiwyg/Irrigated%20Corn%20%28center-pivot%29%20Cost-Return%20Budget_Southwest%20Kansas%20_Nov-01-2026.pdf
[s27]: https://www.agmanager.info/sites/default/files/wysiwyg/Irrigated%20Grain%20Sorghum%20%28center-pivot%29%20Cost-Return%20Budget_Southwest%20KS_Nov-01-2026.pdf
[sb27]: https://www.agmanager.info/sites/default/files/wysiwyg/Irrigated%20Soybeans%20%28center-pivot%29%20Cost-Return%20Budget_Southwest%20KS_Nov-01-2026.pdf
[sb26]: https://www.agmanager.info/sites/default/files/wysiwyg/Irrigated%20Soybeans%20%28center-pivot%29%20Cost-Return%20Budget_Southwest%20KS_Nov-01-2025.pdf
[w27]: https://www.agmanager.info/sites/default/files/wysiwyg/Irrigated%20Wheat%20Cost-Return%20Budget%20in%20Western%20KS_Limited%20irrigation_Nov-01-2026.pdf
[a27]: https://agmanager.info/sites/default/files/wysiwyg/Irrigated%20Alfalfa%20%28Center-Pivot%29%20Cost-Return%20Budget_Western%20Kansas_Nov-01-2026.pdf
[da27]: https://agmanager.info/sites/default/files/wysiwyg/Alfalfa%20Cost-Return%20Budget%20in%20Southwest%20Kansas__Nov-01-2026.pdf
[ct27]: https://agmanager.info/sites/default/files/wysiwyg/Irrigated%20Cotton%20%28Center-Pivot%29%20Cost-Return%20Budget_Southwest%20Kansas_Nov-01-2026.pdf
[dct27]: https://agmanager.info/sites/default/files/wysiwyg/Cotton%20Cost-Return%20Budget%20%28W-CT-F%29_Southwest%20KS_Nov-01-2026.pdf
[sf27]: https://agmanager.info/sites/default/files/wysiwyg/Irrigated%20Oil-Type%20Sunflowers%20%28Center-Pivot%29%20Cost-Return%20Budget_Western%20Kansas_Nov-01-2026.pdf
[dsf27]: https://agmanager.info/sites/default/files/wysiwyg/Oil-Type%20Sunflowers%20Cost-Return%20Budget%20%28W-SF-F%29_Western%20KS%20_Nov-01-2026.pdf
[dc27]: https://www.agmanager.info/sites/default/files/wysiwyg/Corn%20Cost-Return%20Budget%20%28W-C-F%20Rotation%29%20in%20Southwest%20Kansas__Nov-01-2026.pdf
[ds27]: https://www.agmanager.info/sites/default/files/wysiwyg/Grain%20Sorghum%20%28W-S-F%20Rotation%29%20Cost-Return%20Budget%20in%20Southwest%20Kansas__Nov-01-2026.pdf
[dsb27]: https://www.agmanager.info/sites/default/files/wysiwyg/Soybean%20Cost-Return%20Budget%20%28W-SB-F%20Rotation%29%20in%20Southwest%20Kansas__Nov-01-2026.pdf
[dwf26]: https://www.agmanager.info/sites/default/files/wysiwyg/Wheat%20%28W-F%29%20Cost-Return%20Budget%20in%20Southwest%20KS__Nov-01-2025.pdf
[cki20]: https://agmanager.info/sites/default/files/wysiwyg/Central%20Kansas%20Irrigation_13.5%20inches_Nov-01-2020.pdf
[cr26]: https://www.agmanager.info/sites/default/files/pdf/CustomRates_2026.pdf
[ics22]: https://www.agmanager.info/sites/default/files/pdf/2022_InputCostReport.pdf
[mf3504]: https://bookstore.ksre.ksu.edu/download/post-corn-going-to-soybean-use-cereal-rye_MF3504
[osu]: https://cfaes.osu.edu/fact-sheet/attributes-and-considerations-use-cereal-rye-cover-crop
[cv26]: https://esmis.nal.usda.gov/sites/default/release-files/795791/cpvl0226.pdf
[cv24]: https://esmis.nal.usda.gov/sites/default/release-files/k35694332/g158d382b/0k226z97k/cpvl0224.txt
[cv23]: https://esmis.nal.usda.gov/sites/default/release-files/k35694332/b85171637/x346fg88n/cpvl0223.txt
[nassce]: https://www.nass.usda.gov/Statistics_by_State/Kansas/Publications/County_Estimates/index.php
[qscorn]: https://quickstats.nass.usda.gov/results/B224666A-2A56-3AD1-9A44-9F21B4499620
[mf2360]: https://bookstore.ksre.ksu.edu/download/comparing-irrigation-energy-costs_MF2360
[ts25]: https://kgs.ku.edu/sites/kgs/files/files/TechSeriespdfs/TS25.pdf
[dwr12]: https://kgi.contentdm.oclc.org/digital/api/collection/p16884coll5/id/228/download
[l908]: https://bookstore.ksre.ksu.edu/download/considerations-for-nozzle-package-selection-for-center-pivots_L908
[krex]: https://krex.k-state.edu/items/6b441874-e9a1-4c0b-b165-5a3f64b48020
[kr25]: https://kansasreflector.com/2025/01/28/ogallala-aquifer-drops-by-more-than-a-foot-in-parts-of-western-kansas/
[fao66]: https://fao.org/4/i2800e/i2800e.pdf
[mout]: https://www.fao.org/4/Y3655E/y3655e04.htm

## Addendum: the eight crops added in contracts v0.2

CDL records crops here that the K-State set does not cover. Two groups, handled differently.

**Modelled by documented proxy (5 codes, 50 of 60 fields reach the web).** Triticale and the
four double-crop rotations have no SW Kansas enterprise budget and, for triticale, no NASS
Kansas price series. They borrow the closest budgeted crop instead of inventing lines:
triticale → winter wheat (fall-sown small grain, identical machinery and operations);
`winwht_corn` and `triticale_corn` → corn; `winwht_sorghum` → sorghum; `winwht_soybeans` →
soybeans. Registered in `engine/params.py → PROXIED_CROPS`, so every strategy containing one
carries a `data_gaps` entry and a "verify locally" line naming the proxy. Double-cropped years
count only the summer crop (the contracts/crops.csv convention), which understates both income
and water use for those years.

**Not modelled (3 codes, 10 fields excluded).** Potatoes, other hay and "other crops" have no
K-State SW Kansas budget, and NASS publishes no Kansas potato price — only a US all-potato
average ($10.80/cwt, 2025, [pots0926]). The only Kansas potato yield reference found is
MF1115's vegetable-scale figure (200 × 100-lb bags/ac), which is not a pivot-scale budget
([mf1115]). Costs are the largest line in the model, so a proxy here would fabricate the
income metric rather than approximate it. `engine/export` therefore skips those fields and
prints their crop names. Filling them needs a KSRE potato/forage budget that does not exist
in the public set, or a placeholder cost explicitly approved as such.

[pots0926]: https://release.nass.usda.gov/reports/pots0926.pdf
[mf1115]: https://bookstore.ksre.ksu.edu/download/farming-a-few-acres-of-vegetables_MF1115
