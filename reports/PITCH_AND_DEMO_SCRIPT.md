# FieldShift — NASA Space Apps Challenge 2026
## Pitch Deck (7 Slides) & 3-Minute Live Demo Script

> **Challenge:** Field Shift: Adapting Farms with NASA Data  
> **Target Region:** Finney County, Kansas (FIPS 20055) · Groundwater Management District No. 3 (GMD3)  
> **Core Ethos:** *Decision support with uncertainty, never prescriptive recommendations.*

---

# Part 1: The 7-Slide Pitch Deck

### Slide 1: The Ticking Clock on High Plains Agriculture
- **Headline:** 15 Years of Pumping Left: Adapting Finney County with NASA Earth Observation
- **Visual:** High-contrast satellite view of Finney County center pivots with Ogallala aquifer saturated thickness depletion overlay (KGS data: water table dropping 0.5–1.0 m/yr).
- **Core Message:**
  - In Finney County, Kansas, irrigated agriculture sustains the regional economy, but the Ogallala Aquifer is in steep decline.
  - Farmers are squeezed between GMD3 pumping restrictions and climate volatility (extreme summer heat spikes and prolonged drought).
  - To adapt, producers need to shift crop rotations—moving from high-water continuous corn to drought-hardy grain sorghum, winter wheat, and cover crops.
  - **The Problem:** Agtech tools tell farmers what to plant using opaque "AI recommendations." Farmers reject them because black-box advice fails to account for market risk, weather extremes, and individual priority trade-offs.

---

### Slide 2: The Antidote to Black-Box Advice: Honest Decision Support
- **Headline:** Decision Support, Not Prescriptions: Honoring Farmer Judgment
- **Visual:** Side-by-side comparison:
  - *Left (Broken Pattern):* "AI Bot: You should plant Sorghum-Rye in 2026." (Ignored by growers).
  - *Right (FieldShift):* "Under water-conservation priorities, Strategy B scores highest in 84% of 1995–2025 weather scenarios. Here are the $p_{10}–p_{90}$ interval spans and local items to verify."
- **Core Message:**
  - FieldShift never tells a farmer "what to plant."
  - Farming is risk management under deep uncertainty.
  - FieldShift quantifies trade-offs across 5 core dimensions: **Irrigation Water, Net Return, Soil Organic Matter, Erosion Control, and Machinery Labour.**
  - Every metric is shown with empirical 30-year uncertainty intervals ($p_{10}, p_{50}, p_{90}$) and live Monte Carlo probability of scoring highest ($P(\text{best})$).

---

### Slide 3: The NASA Earth Observation Engine
- **Headline:** Grounded in NASA Satellites & Decadal Climate Records
- **Visual:** Multi-layer GIS stack diagram connecting NASA instruments directly to field-level biophysical models:
  - **NASA POWER:** 30 years (1995–2025) of daily precipitation, solar radiation, wind speed, and air temperature $\to$ FAO-56 Reference Evapotranspiration ($ET_0$) + Heat stress windows ($T_{max} > 35^\circ\text{C}$).
  - **MODIS (Terra/Aqua 250m NDVI):** Multi-year vegetation dynamics identifying vulnerable bare-soil fallow periods $\to$ RUSLE soil erosion risk.
  - **SMAP (Root-Zone Soil Moisture):** Root-zone water depletion $\to$ Critical crop moisture stress windows.
  - **SRTM (30m Elevation):** Field slope gradient and length ($LS$-factor) for topographical erosion modeling.
  - **USDA CDL & SSURGO:** 17-year field crop history (2008–2025) and soil texture/organic matter baseline.
- **Key Technical Feat:** 100% offline, reproducible scientific pipeline. No reliance on expensive real-time API gateways during field operations.

---

### Slide 4: How FieldShift Models the Future
- **Headline:** Process-Based Agronomy Meets Conformal Decision Analysis
- **Visual:** Flowchart showing the three-tier computational engine:
  1. **Tier 1 — Biophysical Simulation:** Daily FAO-56 dual crop coefficient water balance ($K_c$ growth curves) driven by historical climate distributions.
  2. **Tier 2 — Agro-Ecological Metrics:** Simplified RUSLE water erosion modeling + USDA Soil Conditioning Index (SCI) residue tracking + K-State Southwest Extension enterprise budgets.
  3. **Tier 3 — Interactive Dirichlet MCDA:** Live Monte Carlo engine (Dirichlet-sampled priority weights $\times$ split-normal metric distributions) evaluating 2,000 synthetic futures in <10 milliseconds directly inside the web client.

---

### Slide 5: The Field Passport & Live Exploration
- **Headline:** Instant Visibility into Every Center Pivot
- **Visual:** Screenshot of the interactive FieldShift web dashboard:
  - County-wide vector map of 26 verified Finney County center pivots with USDA CDL historical crop timeline (2008–2025).
  - Multi-track seasonal timeline displaying bare-soil exposure windows (MODIS), water stress windows (SMAP), and heat stress spikes (NASA POWER).
  - Historical 10-year climate stress index tracking field resilience across severe historical droughts (such as 2011–2012).

---

### Slide 6: Radical Scientific Humility — "What We Don't Know"
- **Headline:** Bridging Space Data to the County Extension Office
- **Visual:** Callout card from the app: *"Verify Locally (GMD3 · K-State · NRCS)"* alongside explicit data gap disclosures.
- **Core Message:**
  - Satellite data cannot see local well pump lift decline, caliche hardpan depth, or elevator cash basis bids.
  - FieldShift explicitly presents a **"Verify Locally"** checklist:
    - *GMD3 (Garden City):* Verify authorized annual acre-inch allocation and metering regulations.
    - *K-State Southwest Research-Extension Center:* Check local hybrid trial performance and disease pressure.
    - *USDA NRCS:* Review EQIP / CSP cost-share programs for reduced-tillage cover crops.
  - Transparently flags model assumptions: RUSLE models sheet/rill water erosion; High Plains wind erosion must be evaluated locally.

---

### Slide 7: Scalable, Sustainable, Open-Source Impact
- **Headline:** Zero Cloud Cost, Immediate Global Applicability
- **Visual:** Roadmap showing progression from Finney County $\to$ High Plains Ogallala $\to$ Global Drylands.
- **Core Message:**
  - **Architecture:** 100% static JSON/GeoJSON web application. Fast, responsive, works on slow rural cellular connections or offline on tablets.
  - **Exportability:** 1-click printable 1-page Field Dossier (PDF) designed for kitchen-table family discussions, bank loan meetings, or NRCS conservation planning.
  - **Reproducibility:** Strict contracts architecture (`contracts/`), fully tested pipeline (`pytest`, `ruff`), and verifiable NASA data pipelines ready for expansion to all 105 Kansas counties and global semi-arid agricultural basins.

---

# Part 2: Timed 3-Minute Live Demo Script

### **[0:00 – 0:45] The Hook & The Field Passport**
*(Presenter stands before the screen showing the FieldShift web application at http://localhost:5173)*

> **Speaker:**  
> *"Good morning. We are looking at Finney County, Kansas—one of the most productive agricultural counties in the United States, and the epicenter of Ogallala Aquifer groundwater depletion. Water tables here are dropping up to three feet every year.*
> 
> *Producers here don't need an AI bot telling them what to do. They need honest, transparent tools that reveal the trade-offs of shifting crop rotations.*
> 
> *Let's select Field `KS_FIN_001` in southern Finney County. Immediately, FieldShift displays the **Field Passport**. Using 17 years of USDA Cropland Data Layer rasters harmonized with NASA satellites, we see this pivot's real crop history—from continuous corn to grain sorghum.*
> 
> *Notice the seasonal calendar below: NASA MODIS 250m NDVI identifies exact bare-soil periods when topsoil is exposed to erosion, while NASA POWER weather reveals extreme heat-stress windows where temperatures exceeded 35°C."*

---

### **[0:45 – 1:45] The Decision Priority Sliders & Live MCDA**
*(Presenter scrolls down to the 'Decision Priorities' panel and clicks preset chips)*

> **Speaker:**  
> *"Every farm family has different goals. A young producer carrying equipment debt might focus on near-term cash flow; a multi-generational grower facing strict water allocations from Kansas GMD3 might prioritize preserving their water right.*
> 
> *Look at our **Decision Priorities** sliders. We evaluate five critical dimensions: Irrigation Water, Net Return, Soil Organic Matter, Erosion Control, and Machinery Labour.*
> 
> *Watch what happens when I switch from **'Maximize Return'** to **'Save Water'**:*
> *(Presenter clicks the 'Save Water' preset chip)*
> 
> *In less than 10 milliseconds, our in-browser Monte Carlo engine executes 2,000 simulated draws across 30 years of NASA POWER historical weather. Notice our language:*
> **'Under active priorities, Sorghum-Wheat-Cover scores highest in 82% of weather and weight scenarios.'**
> *Not 'you should plant this,' but an honest, probabilistic assessment of risk."*

---

### **[1:45 – 2:30] Interval Charts & Scientific Humility**
*(Presenter hovers over the Metric Interval plots and expands the 'Verify Locally' accordion)*

> **Speaker:**  
> *"Single-number yield predictions are dangerous. That's why FieldShift displays empirical $p_{10}, p_{50}$, and $p_{90}$ climate intervals. Across 30 years of Kansas climate history, we show the full spread: what happens in a severe 2011-style drought versus a high-rainfall year.*
> 
> *Furthermore, we practice radical scientific humility. We don't pretend satellites know everything.*
> *(Presenter clicks open 'Verify Locally (GMD3 · K-State · NRCS)')*
> *Right here in the interface, we prompt the grower to check their flow meter allocation with GMD3 in Garden City, check hybrid trials with the K-State Southwest Extension Center, and apply for NRCS EQIP cost-share incentives."*

---

### **[2:30 – 3:00] The Printable Dossier & Closing Call**
*(Presenter clicks the top-right 'Print Dossier' button, bringing up the print preview dialog)*

> **Speaker:**  
> *"Finally, real farm decisions don't happen in the cloud—they happen at the kitchen table with family, lenders, and agronomists. With one click, FieldShift generates an ink-friendly, 1-page Field Dossier PDF summarizing the field passport, 30-year climate bounds, and local verification steps.*
> 
> *By combining NASA Earth observation with process-based agronomic modeling and transparent decision support, FieldShift empowers growers to preserve the Ogallala Aquifer for the next generation.*
> 
> *Thank you, and we welcome your questions."*

---

# Part 3: Pitch Q&A Preparation (Anticipated Judge Inquiries)

1. **Q: Why don't you use Machine Learning or Deep Learning for yield prediction?**  
   *Answer:* High Plains agriculture suffers from high climate volatility and small sample sizes (one crop cycle per year). Process-based biophysical models (FAO-56 water balance, RUSLE erosion) calibrated to 30 years of NASA POWER weather provide physically bounded, interpretable, and reproducible ranges without the hallucination or out-of-distribution failure risks of deep learning models.

2. **Q: How does FieldShift make money or sustain itself?**  
   *Answer:* FieldShift is built as a zero-infrastructure static client. Groundwater Management Districts (like Kansas GMD3), County Extension Offices, and conservation NGOs can host and distribute it with zero recurring cloud database costs.

3. **Q: Can this scale outside Finney County?**  
   *Answer:* Yes. All pipeline data sources (NASA POWER, MODIS, SMAP, SRTM) are global datasets. The backend interfaces are designed so that connecting new regional soil and crop statistics extends FieldShift to any drought-vulnerable agricultural basin worldwide.
