interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export function AboutModal({ isOpen, onClose }: Props) {
  if (!isOpen) return null;

  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="about-modal-title"
    >
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className="modal-tag">NASA Space Apps 2026</span>
            <h2 id="about-modal-title">About the Data, Modeling & Uncertainty</h2>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          {/* Section 1: Challenge & Context */}
          <section className="modal-section">
            <h3>Finney County, Kansas & The Ogallala Aquifer</h3>
            <p>
              Finney County (FIPS 20055) in Southwest Kansas is a vital agricultural hub for grain
              sorghum, winter wheat, and corn, anchored by the Ogallala (High Plains) Aquifer.
              Declining water tables, extreme summer heat, and recurring semi-arid droughts demand
              rotational adaptability.
            </p>
            <p>
              <strong>FieldShift</strong> harnesses NASA Earth observation data to provide
              transparent, uncertainty-aware decision support for farmers evaluating alternative
              crop rotations.
            </p>
          </section>

          {/* Section 2: Decision Support with Uncertainty */}
          <section className="modal-section highlight-box">
            <h3>Decision Support Philosophy: Why Uncertainty Matters</h3>
            <p>
              <strong>
                FieldShift provides decision support, never prescriptive recommendations.
              </strong>
            </p>
            <p>
              In semi-arid dryland and deficit-irrigated farming, a single &quot;average&quot;
              number is dangerous. Rainfall in Finney County can range from under 10 inches in a
              drought year (such as 2012) to over 28 inches in a wet cycle.
            </p>
            <p>
              Every rotation strategy is evaluated against{' '}
              <strong>30 years of NASA POWER historical weather (1995–2025)</strong>, reporting 10th
              percentile (p10), median (p50), and 90th percentile (p90) intervals. When farmer
              priorities are adjusted, the system simulates 2,000 Monte Carlo draws sampling both
              weather variance and priority uncertainty to determine <strong>P(best)</strong>—the
              probability that a strategy delivers the highest composite performance.
            </p>
          </section>

          {/* Section 3: NASA & USDA Datasets */}
          <section className="modal-section">
            <h3>Earth Observation & Agricultural Datasets</h3>
            <div className="dataset-grid">
              <div className="dataset-card">
                <div className="dataset-badge nasa">NASA POWER</div>
                <h4>Daily Agroclimatology (1995–2025)</h4>
                <p>
                  Daily solar insolation (ALLSKY_SFC_SW_DWN), 2m temperatures (T2M, Tmax, Tmin),
                  relative humidity, wind speed, and precipitation at county scale.
                </p>
                <div className="dataset-use">
                  <strong>Used for:</strong> Daily FAO-56 Penman-Monteith reference ET (ET0),
                  heat-stress windows (Tmax &gt; 35°C), and rainfall erosivity (R).
                </div>
              </div>

              <div className="dataset-card">
                <div className="dataset-badge nasa">NASA SMAP</div>
                <h4>Soil Moisture Active Passive</h4>
                <p>
                  SPL3SMP_E enhanced 9km passive soil moisture product monitoring root-zone moisture
                  anomalies.
                </p>
                <div className="dataset-use">
                  <strong>Used for:</strong> Identifying critical soil moisture deficit periods
                  during reproductive stages (water stress windows).
                </div>
              </div>

              <div className="dataset-card">
                <div className="dataset-badge nasa">NASA MODIS</div>
                <h4>MOD13Q1 250m NDVI Composites</h4>
                <p>
                  16-day Normalized Difference Vegetation Index tracking vegetation canopy
                  development and bare-soil exposure.
                </p>
                <div className="dataset-use">
                  <strong>Used for:</strong> Detecting bare-soil exposure windows between harvest
                  and canopy closure where wind and water erosion risks peak.
                </div>
              </div>

              <div className="dataset-card">
                <div className="dataset-badge nasa">NASA SRTM</div>
                <h4>30m Digital Elevation Model</h4>
                <p>
                  Topographic elevation and slope calculations across Finney County&apos;s terrain.
                </p>
                <div className="dataset-use">
                  <strong>Used for:</strong> Deriving field slope gradient and topographic factor
                  (LS) in the RUSLE erosion model.
                </div>
              </div>

              <div className="dataset-card">
                <div className="dataset-badge usda">USDA CDL</div>
                <h4>Cropland Data Layer (2008–2025)</h4>
                <p>
                  30m annual satellite-derived crop classification by USDA NASS, tracking 18 years
                  of field rotations.
                </p>
                <div className="dataset-use">
                  <strong>Used for:</strong> Establishing baseline crop history, identifying
                  center-pivot footprints, and validating local rotation feasibility.
                </div>
              </div>

              <div className="dataset-card">
                <div className="dataset-badge usda">USDA SSURGO</div>
                <h4>Soil Survey Geographic Database</h4>
                <p>
                  Authoritative NRCS soil survey data providing dominant soil texture, organic
                  matter content (OM%), erodibility factor (Kf factor), and available water capacity
                  (AWC).
                </p>
                <div className="dataset-use">
                  <strong>Used for:</strong> Field-specific soil water retention limits and soil
                  conditioning baseline.
                </div>
              </div>
            </div>
          </section>

          {/* Section 4: Process-Based Modeling */}
          <section className="modal-section">
            <h3>Process-Based Modeling Engines</h3>
            <div className="model-list">
              <div className="model-item">
                <h4>1. FAO-56 Dual Crop Coefficient Water Balance</h4>
                <p>
                  Computes daily crop evapotranspiration (ETc = Kc × ET0) across initial, vegetative
                  development, mid-season reproductive, and late-season maturation stages. Accounts
                  for effective precipitation and irrigation deficits.
                </p>
              </div>
              <div className="model-item">
                <h4>2. Simplified RUSLE (Soil Erosion)</h4>
                <p>
                  Estimates annual sheet and rill water erosion (A = R × K × LS × C × P) based on
                  POWER rainfall energy (R), SSURGO erodibility (K), SRTM slope (LS), and crop
                  canopy/residue cover (C).
                </p>
              </div>
              <div className="model-item">
                <h4>3. Soil Conditioning Index (SCI)</h4>
                <p>
                  Assesses whether a rotation maintains or depletes Soil Organic Matter (SOM) based
                  on organic residue biomass returns, tillage disturbance intensity, and erosion
                  loss.
                </p>
              </div>
              <div className="model-item">
                <h4>4. Multi-Criteria Decision Analysis (MCDA)</h4>
                <p>
                  Combines normalized scores across water conservation, net income, soil organic
                  matter, erosion prevention, and labour requirements, weighting by farmer
                  preference sliders with Dirichlet uncertainty sampling.
                </p>
              </div>
            </div>
          </section>

          {/* Section 5: Local Verification & Known Gaps */}
          <section className="modal-section">
            <h3>Ground-Truthing & What We Don’t Know</h3>
            <p>
              Satellite data and macro-level models have inherent boundaries. Local ground-truthing
              is indispensable:
            </p>
            <ul className="guidance-list">
              <li>
                <strong>Ogallala Well Capacity:</strong> Satellite datasets cannot measure real-time
                well flow rates (GPM/acre) or dropping regional pumping levels. Consult Southwest
                Kansas Groundwater Management District No. 3 (GMD3).
              </li>
              <li>
                <strong>Wind Erosion:</strong> In Southwest Kansas, wind erosion can exceed water
                erosion on dry sandy soils. FieldShift flags bare-soil periods from MODIS, but
                farmers should maintain standing residue or winter cover.
              </li>
              <li>
                <strong>Local Agronomy:</strong> Check with the Kansas State University Southwest
                Research-Extension Center in Garden City for locally calibrated hybrid trials,
                seeding dates, and herbicide carryover intervals.
              </li>
            </ul>
          </section>
        </div>

        <div className="modal-footer">
          <span className="muted-text">
            All processing is offline; data validated against contracts v0.1.
          </span>
          <button type="button" className="btn-primary" onClick={onClose}>
            Close & Return to Map
          </button>
        </div>
      </div>
    </div>
  );
}
