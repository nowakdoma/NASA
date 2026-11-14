# Contract Change Proposal: `contracts/crops.csv` v0.2
**RFC: Expanding Finney County CDL Crop Coverage (Triticale, Double Crops, Oats, Other Hay)**

- **Date:** 2026-11-14
- **Author:** Person 3 (engine / decision support)
- **Status:** Proposed — awaiting sign-off from all 3 humans (Person 1, Person 2, Person 3)
- **Target Schema Version:** `0.2`

---

## 1. Context and Problem Statement

FieldShift's pipeline clips USDA Cropland Data Layer (CDL) rasters from 2008 to 2025 across Finney County, Kansas (FIPS 20055). Under the pipeline honesty rules (`pipeline/assemble.py`):
> *"A field is only emitted if its crop history is complete and fully mappable through `contracts/crops.csv`. Years whose CDL class has no crop_code (triticale, double-crop rotations) disqualify the field rather than being coerced to 'fallow'."*

In Finney County, agricultural reality features key forage, cereal, and double-crop systems that are absent from `contracts/crops.csv` v0.1:
1. **Triticale (CDL 205):** 23,709 acres in Finney County alone. Widely grown by Southwest Kansas beef cattle feedlots and dairies as winter forage, boot-stage silage, and feed grain.
2. **Double Crop Rotations:** Common High Plains intensification practices:
   - Winter Wheat / Corn (CDL 225)
   - Triticale / Corn (CDL 228)
   - Winter Wheat / Sorghum (CDL 236)
3. **Oats (CDL 28):** Spring cereal grown for hay, forage, or grain.
4. **Other Hay / Non-Alfalfa (CDL 37):** Sorghum-sudangrass, millet hay, and teff forage.

Because these CDL codes have no corresponding `crop_code`, **~7% of field-years currently have unmapped codes**, causing valid irrigated center pivots to be rejected during assembly.

---

## 2. Proposed Changes to `contracts/crops.csv`

The following 6 rows are proposed for addition to `contracts/crops.csv`:

```csv
triticale,Winter triticale,205,Poaceae,false,1.4,0.70,1.15,0.30,30,135,35,25,4.0,USDA NASS Kansas hay/forage price or feed grain (triticale),true,"FAO-56 Table 12 small grains; K-State MF3334 triticale production"
oats,Spring oats,28,Poaceae,false,1.1,0.30,1.15,0.25,20,30,40,25,3.0,USDA NASS Kansas annual price received (oats),false,"FAO-56 Table 12 (Oats); K-State spring oat management"
other_hay,Other hay / forage sorghum,37,Poaceae,false,1.2,0.40,0.95,0.75,15,30,45,20,2.2,USDA NASS Kansas other hay price,true,"FAO-56 Table 12 Sudan grass/hay; KS Extension forage budgets"
double_crop_wheat_corn,Double crop: Winter wheat / Corn,225,Poaceae,false,1.3,0.60,1.20,0.35,30,90,80,40,9.5,Composite: NASS Kansas wheat + corn proportional revenues,true,"Composite FAO-56 dual crop; K-State double-cropping guidelines"
double_crop_triticale_corn,Double crop: Triticale / Corn silage,228,Poaceae,false,1.3,0.60,1.20,0.45,30,85,80,40,8.5,Composite: NASS Kansas forage + corn silage price,true,"Composite FAO-56 dual forage-silage; K-State western KS dairies"
double_crop_wheat_sorghum,Double crop: Winter wheat / Sorghum,236,Poaceae,false,1.4,0.60,1.10,0.45,30,90,70,35,7.5,Composite: NASS Kansas wheat + sorghum proportional revenues,true,"Composite FAO-56 wheat-sorghum; K-State dryland double crop"
```

### Agronomic & Modeling Justification

| Crop Code | CDL Code | Root Depth | Kc ini/mid/end | Residue (t/ha) | Notes |
|:---|:---:|:---:|:---:|:---:|:---|
| `triticale` | 205 | 1.4 m | 0.70 / 1.15 / 0.30 | 4.0 | Overwintering spring greenup similar to winter wheat; harvested for forage in late May or grain in June. |
| `oats` | 28 | 1.1 m | 0.30 / 1.15 / 0.25 | 3.0 | Spring-sown small grain; lower water use than corn; FAO-56 Table 12 standard. |
| `other_hay` | 37 | 1.2 m | 0.40 / 0.95 / 0.75 | 2.2 | Covers summer annual forages (sorghum-sudan, teff); rapid early canopy closure. |
| `double_crop_wheat_corn` | 225 | 1.3 m | 0.60 / 1.20 / 0.35 | 9.5 | Represents combined 2-crop annual ET0 curve and aggregated stover/straw residue. |
| `double_crop_triticale_corn` | 228 | 1.3 m | 0.60 / 1.20 / 0.45 | 8.5 | High-intensity silage rotation common near Holcomb / Garden City feedlots. |
| `double_crop_wheat_sorghum` | 236 | 1.4 m | 0.60 / 1.10 / 0.45 | 7.5 | Water-conserving double crop; sorghum planted into wheat stubble with lower ET than corn. |

---

## 3. Double-Cropping Representation: Analysis of Options

### Option A: Composite Single-Year Codes (Recommended)
- Assign `double_crop_wheat_corn`, `double_crop_triticale_corn`, `double_crop_wheat_sorghum` as distinct `crop_code` rows in `crops.csv`.
- **Pros:** 
  - Zero structural changes to `contracts/fields.schema.json` (the contract expects `crop_history: { [year: string]: crop_code }`).
  - Seamlessly integrates with pipeline `CDL_TO_CROP` mapping and `pipeline/assemble.py`.
  - Fully backward-compatible with the frontend `FieldPanel.tsx` timeline and map styling.
- **Cons:** 
  - Crop stages in FAO-56 Kc calculation use composite seasonal approximations.

### Option B: Array of Crops per Year
- Change contract from `{ "2020": "corn" }` to `{ "2020": ["winter_wheat", "corn"] }`.
- **Pros:** Agronomically pure representation of discrete planting and harvest dates.
- **Cons:** Breaking change across all contracts, frontend timelines, deck.gl map shaders, and engine water balance calculations. Excessive risk 24 hours before Space Apps submission.

**Recommendation:** Proceed with **Option A** for schema v0.2.

---

## 4. Integration Impact Across Repositories

If approved, the integration requires updates across three components in a single commit:

1. **Contracts (`contracts/`):**
   - Append the 6 rows to `contracts/crops.csv`.
   - Bump `"schema_version": "0.2"` in `contracts/fields.schema.json` and `contracts/strategies.schema.json`.
   - Update `contracts/mock/fields.geojson` and `contracts/mock/strategies.json` schema version headers.

2. **Pipeline (`pipeline/`):**
   - In `pipeline/backends/us.py`, expand `CDL_TO_CROP`:
     ```python
     CDL_TO_CROP.update({
         28: "oats",
         37: "other_hay",
         205: "triticale",
         225: "double_crop_wheat_corn",
         228: "double_crop_triticale_corn",
         236: "double_crop_wheat_sorghum",
     })
     ```
   - Re-run `pipeline/assemble.py` (`make data`) to emit previously disqualified fields into `data/interim/fields.geojson`.

3. **Engine (`engine/`):**
   - In `engine/params.py`, add economic budgets (gross margins, tillage and variable irrigation cost) and RUSLE C-factors for the 6 new crops.

4. **Web Frontend (`web/`):**
   - In `web/src/lib/colors.ts`: Add human-readable names and earthy palette tokens:
     ```typescript
     triticale: { name: 'Triticale', color: '#c49a45' },
     oats: { name: 'Oats', color: '#d4c285' },
     other_hay: { name: 'Other Hay', color: '#9bb36c' },
     double_crop_wheat_corn: { name: 'Double: Wheat/Corn', color: '#d97736' },
     double_crop_triticale_corn: { name: 'Double: Trit/Corn', color: '#c76e2d' },
     double_crop_wheat_sorghum: { name: 'Double: Wheat/Sorghum', color: '#ba6025' },
     ```

---

## 5. Required Sign-Off Checklist (Per Rule 2 of `AGENTS.md`)

According to repo governance:
> *"contracts/ changes only with explicit human approval from all three people. Bump schema_version and update schema + mock + web/src/types/contracts.ts in the same commit."*

- [ ] **Human 1 Approval (Person 1 — UI/UX, pitch):** _____________________ Date: __________
- [ ] **Human 2 Approval (Person 2 — Pipeline):** _____________________ Date: __________
- [ ] **Human 3 Approval (Person 3 — Engine):** _____________________ Date: __________
