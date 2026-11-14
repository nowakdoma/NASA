import { IconClose, IconSatellite, IconSprout } from './Icons';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export function AboutModal({ isOpen, onClose }: Props) {
  if (!isOpen) return null;

  return (
    <div
      className="modal-backdrop no-print"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="about-modal-title"
    >
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-title">
            <div className="modal-tag">
              <IconSatellite />
              <span>NASA Space Apps 2026</span>
            </div>
            <h2 id="about-modal-title">About the Data, Modeling & Uncertainty</h2>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close modal"
          >
            <IconClose />
          </button>
        </div>

        <div className="modal-body">
          {/* Section 1: Challenge & Context */}
          <section className="modal-section">
            <div className="section-head">
              <IconSprout className="sec-icon" />
              <h3>Finney County, Kansas & The Ogallala Aquifer</h3>
            </div>
            <p>
              Finney County (FIPS 20055) in Southwest Kansas is a high-volume agricultural center
              for grain sorghum, winter wheat, and corn, anchored by the Ogallala (High Plains)
              Aquifer. Declining groundwater levels, extreme summer temperatures, and recurring
              drought cycles require adaptive rotational strategies.
            </p>
            <p>
              <strong>FieldShift</strong> leverages NASA Earth observation data to deliver
              transparent, uncertainty-aware decision support for agricultural producers evaluating
              multi-year crop rotations.
            </p>
          </section>

          {/* Section 2: Decision Support Philosophy */}
          <section className="modal-section highlight-box">
            <h3>Decision Support Philosophy: Why Uncertainty Matters</h3>
            <p>
              <strong>FieldShift delivers decision support, never prescriptive advice.</strong>
            </p>
            <p>
              In semi-arid dryland and deficit-irrigated farming, a single average value can be
              misleading. Annual precipitation in Finney County fluctuates from under 10 inches in
              severe drought years (e.g. 2012) to over 28 inches in wet cycles.
            </p>
            <p>
              Every rotation strategy is simulated against{' '}
              <strong>30 years of NASA POWER historical weather (1995–2025)</strong>, generating
              10th percentile (p10), median (p50), and 90th percentile (p90) performance intervals.
              When farmer priorities are adjusted, the decision engine draws 2,000 Monte Carlo
              samples combining weather variance with Dirichlet-distributed preference weights to
              calculate <strong>P(best)</strong>—the probability that a rotation yields the highest
              overall performance.
            </p>
          </section>

          {/* Section 3: Earth Observation Datasets */}
          <section className="modal-section">
            <h3>NASA & USDA Earth Observation Datasets</h3>
            <div className="dataset-grid">
              <div className="dataset-card">
                <div className="dataset-badge nasa">NASA POWER</div>
                <h4>Daily Agroclimatology (1995–2025)</h4>
                <p>
                  Daily solar insolation (ALLSKY_SFC_SW_DWN), 2m temperatures (T2M, Tmax, Tmin),
                  relative humidity, wind speed, and precipitation at county scale.
                </p>
                <div className="dataset-use">
                  <strong>Application:</strong> Daily FAO-56 Penman-Monteith reference ET (ET0),
                  heat stress windows (Tmax &gt; 35°C), and rainfall erosivity (R).
                </div>
              </div>

              <div className="dataset-card">
                <div className="dataset-badge nasa">NASA SMAP</div>
                <h4>Soil Moisture Active Passive</h4>
                <p>
                  SPL3SMP_E enhanced 9km passive soil moisture monitoring root-zone moisture
                  anomalies.
                </p>
                <div className="dataset-use">
                  <strong>Application:</strong> Quantifying crop reproductive moisture stress
                  windows.
                </div>
              </div>

              <div className="dataset-card">
                <div className="dataset-badge nasa">NASA MODIS</div>
                <h4>MOD13Q1 250m NDVI Composites</h4>
                <p>
                  16-day Normalized Difference Vegetation Index tracking crop canopy development and
                  bare-soil exposure.
                </p>
                <div className="dataset-use">
                  <strong>Application:</strong> Detecting bare-soil periods between harvest and
                  canopy closure.
                </div>
              </div>

              <div className="dataset-card">
                <div className="dataset-badge nasa">NASA SRTM</div>
                <h4>30m Digital Elevation Model</h4>
                <p>Digital elevation and slope gradient calculations across Finney County.</p>
                <div className="dataset-use">
                  <strong>Application:</strong> Calculating field slope and topographic LS factor in
                  RUSLE.
                </div>
              </div>

              <div className="dataset-card">
                <div className="dataset-badge usda">USDA CDL</div>
                <h4>Cropland Data Layer (2008–2025)</h4>
                <p>
                  30m satellite-derived annual crop classification by USDA NASS, tracking 18 years
                  of field rotations.
                </p>
                <div className="dataset-use">
                  <strong>Application:</strong> Baseline crop histories and center-pivot boundary
                  delineation.
                </div>
              </div>

              <div className="dataset-card">
                <div className="dataset-badge usda">USDA SSURGO</div>
                <h4>Soil Survey Geographic Database</h4>
                <p>
                  NRCS soil survey data providing dominant soil texture, organic matter (OM%),
                  erodibility (Kf), and available water capacity (AWC).
                </p>
                <div className="dataset-use">
                  <strong>Application:</strong> Field water holding capacity and soil conditioning
                  baseline.
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
                  Calculates daily crop evapotranspiration (ETc = Kc × ET0) across initial,
                  vegetative, mid-season reproductive, and late maturation stages.
                </p>
              </div>
              <div className="model-item">
                <h4>2. Simplified RUSLE (Water Erosion)</h4>
                <p>
                  Estimates annual sheet and rill water erosion (A = R × K × LS × C × P) based on
                  POWER rainfall energy (R), SSURGO erodibility (K), SRTM slope (LS), and crop
                  residue cover (C).
                </p>
              </div>
              <div className="model-item">
                <h4>3. Soil Conditioning Index (SCI)</h4>
                <p>
                  Evaluates organic matter trajectory based on biomass residue inputs, tillage
                  frequency, and erosion losses.
                </p>
              </div>
              <div className="model-item">
                <h4>4. Multi-Criteria Decision Analysis (MCDA)</h4>
                <p>
                  Combines normalized scores across water conservation, net return, soil health,
                  erosion prevention, and labour requirements, weighting by farmer preference
                  sliders with Dirichlet uncertainty sampling.
                </p>
              </div>
            </div>
          </section>

          {/* Section 5: Ground-Truthing & Attributions */}
          <section className="modal-section">
            <h3>Ground-Truthing & Attributions</h3>
            <ul className="guidance-list">
              <li>
                <strong>Groundwater Management District No. 3 (GMD3):</strong> Consult GMD3 in
                Garden City regarding authorized well flow rates, annual allocation reporting, and
                Multi-Year Flex Accounts (MYFA).
              </li>
              <li>
                <strong>K-State Research & Extension:</strong> Consult the Southwest
                Research-Extension Center in Garden City for locally calibrated hybrid trials and
                plant-back restrictions.
              </li>
              <li>
                <strong>Icon Attribution:</strong>{' '}
                <a
                  href="https://www.flaticon.com/free-icons/yield"
                  title="yield icons"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="attribution-link"
                >
                  Yield icons created by Eucalyp - Flaticon
                </a>
              </li>
            </ul>
          </section>
        </div>

        <div className="modal-footer">
          <span className="modal-footer-attribution">
            <a
              href="https://www.flaticon.com/free-icons/yield"
              title="yield icons"
              target="_blank"
              rel="noopener noreferrer"
            >
              Yield icons created by Eucalyp - Flaticon
            </a>
          </span>
          <button type="button" className="btn-primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
