import type { FieldFeature, MetricKey, MetricMeta } from '../types/contracts';
import { METRIC_KEYS } from '../types/contracts';
import type { RankedStrategy, Priorities } from '../lib/ranking';
import { cropLabel } from '../lib/colors';

interface Props {
  field: FieldFeature;
  year: number;
  priorities: Priorities;
  ranked: RankedStrategy[];
  meta: Record<MetricKey, MetricMeta>;
  weatherYears: [number, number];
}

const fmt = (x: number) => {
  if (Math.abs(x) >= 100) return x.toFixed(0);
  if (Math.abs(x) >= 10) return x.toFixed(1);
  return x.toFixed(2);
};

export function PrintReport({ field, year, priorities, ranked, meta, weatherYears }: Props) {
  const p = field.properties;
  const years = Object.keys(p.crop_history).sort();
  const acres = Math.round(p.area_ha * 2.47105);
  const barePeriods = p.season_calendar.bare_periods.filter((b) => b.year === year);
  const stressWindows = p.season_calendar.stress_windows.filter((s) => s.year === year);
  const lead = ranked[0];

  return (
    <div className="print-report-container print-only">
      {/* Print Document Header */}
      <div className="print-header">
        <div className="print-brand">
          <div className="print-logo-mark">🌱 FieldShift</div>
          <div className="print-title-group">
            <h1>Field Decision Support Dossier</h1>
            <p className="print-subtitle">
              Finney County, Kansas (FIPS 20055) · NASA Space Apps Challenge 2026
            </p>
          </div>
        </div>
        <div className="print-meta-box">
          <div>
            <strong>Date:</strong>{' '}
            {new Date().toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
            })}
          </div>
          <div>
            <strong>Evaluation Weather Period:</strong> {weatherYears[0]}–{weatherYears[1]}
          </div>
          <div>
            <strong>Active Season:</strong> {year}
          </div>
        </div>
      </div>

      {/* Field Identification & Soil Summary */}
      <div className="print-section-grid">
        <div className="print-card">
          <h2>Field Identification</h2>
          <table className="print-kv-table">
            <tbody>
              <tr>
                <th>Field ID / Name:</th>
                <td>
                  <strong>{p.field_id}</strong> {p.name ? `(${p.name})` : ''}
                </td>
              </tr>
              <tr>
                <th>Acreage:</th>
                <td>
                  {p.area_ha} ha ({acres} acres)
                </td>
              </tr>
              <tr>
                <th>Irrigation System:</th>
                <td>
                  {p.irrigation_type === 'center_pivot'
                    ? 'Center Pivot'
                    : (p.irrigation_type ?? (p.irrigated ? 'Irrigated' : 'Dryland'))}
                </td>
              </tr>
              <tr>
                <th>County Centroid:</th>
                <td>Finney County, SW Kansas (Ogallala Aquifer)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="print-card">
          <h2>Soil Characteristics (SSURGO)</h2>
          <table className="print-kv-table">
            <tbody>
              <tr>
                <th>Dominant Texture:</th>
                <td>{p.soil.texture}</td>
              </tr>
              <tr>
                <th>Organic Matter (OM):</th>
                <td>{p.soil.om_pct} %</td>
              </tr>
              <tr>
                <th>Erodibility (Kf factor):</th>
                <td>{p.soil.kffact}</td>
              </tr>
              <tr>
                <th>Available Water (AWC):</th>
                <td>{p.soil.awc_mm} mm</td>
              </tr>
              <tr>
                <th>Average Slope:</th>
                <td>{p.soil.slope_pct} %</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Historical Crop Sequence Table */}
      <div className="print-card print-full-width">
        <h2>18-Year Historical Crop Sequence (USDA Cropland Data Layer 2008–2025)</h2>
        <div className="print-history-grid">
          {years.map((y) => (
            <div
              key={y}
              className={`print-history-item${Number(y) === year ? ' active-year' : ''}`}
            >
              <div className="print-year-lbl">{y}</div>
              <div className="print-crop-val">{cropLabel(p.crop_history[y])}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Satellite Season Monitoring */}
      <div className="print-card print-full-width">
        <h2>Season {year} Satellite Monitoring Events</h2>
        {barePeriods.length + stressWindows.length === 0 ? (
          <p className="print-muted">
            No severe bare-soil exposure or stress windows recorded for {year}.
          </p>
        ) : (
          <table className="print-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Date Window</th>
                <th>Severity</th>
                <th>Observation Source</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {barePeriods.map((b, i) => (
                <tr key={`b-${i}`}>
                  <td>
                    <span className="print-pill bare">Bare Soil</span>
                  </td>
                  <td>
                    {b.start} → {b.end}
                  </td>
                  <td>Elevated erosion risk</td>
                  <td>{b.source}</td>
                  <td>{b.note ?? 'Pre-plant / post-harvest exposure'}</td>
                </tr>
              ))}
              {stressWindows.map((s, i) => (
                <tr key={`s-${i}`}>
                  <td>
                    <span className={`print-pill ${s.type}`}>
                      {s.type === 'water' ? 'Water Stress' : 'Heat Stress'}
                    </span>
                  </td>
                  <td>
                    {s.start} → {s.end}
                  </td>
                  <td>{(s.severity * 100).toFixed(0)}%</td>
                  <td>{s.source}</td>
                  <td>
                    {s.type === 'heat'
                      ? 'Tmax > 35°C during reproductive phase'
                      : 'Root-zone moisture deficit'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Decision Priority Weights */}
      <div className="print-card print-full-width">
        <h2>Decision Priorities (0–5 Weight Scale)</h2>
        <div className="print-priorities-summary">
          <span>
            <strong>Save Water:</strong> {priorities.water}/5
          </span>
          <span>
            <strong>Net Return:</strong> {priorities.income}/5
          </span>
          <span>
            <strong>Soil Organic Matter:</strong> {priorities.soil}/5
          </span>
          <span>
            <strong>Limit Erosion:</strong> {priorities.erosion}/5
          </span>
          <span>
            <strong>Manage Labour:</strong> {priorities.labour}/5
          </span>
        </div>
      </div>

      {/* Rotation Strategies Comparison Table */}
      <div className="print-card print-full-width">
        <h2>Rotation Strategies Evaluated Across 30-Year Weather Uncertainty (1995–2025)</h2>
        <table className="print-table strat-print-table">
          <thead>
            <tr>
              <th>Strategy</th>
              <th>Rotation Sequence</th>
              <th>P(best)</th>
              {METRIC_KEYS.map((m) => (
                <th key={m}>
                  {meta[m].label}
                  <small className="th-unit">({meta[m].unit})</small>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ranked.map(({ strategy, pBest }) => (
              <tr key={strategy.id} className={strategy.is_current ? 'current-strat-row' : ''}>
                <td>
                  <strong>{strategy.name}</strong>
                  {strategy.is_current && <span className="print-pill current">Current</span>}
                </td>
                <td className="print-rot-col">{strategy.rotation.map(cropLabel).join(' → ')}</td>
                <td>
                  <strong>{Math.round(pBest * 100)}%</strong>
                </td>
                {METRIC_KEYS.map((m) => {
                  const q = strategy.metrics[m];
                  return (
                    <td key={m} className="interval-td">
                      <div className="p50-val">{fmt(q.p50)}</div>
                      <div className="range-val">
                        [{fmt(q.p10)} – {fmt(q.p90)}]
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Decision Support Finding & Ground Truthing */}
      <div className="print-card print-full-width print-callout">
        <h3>Decision Support Finding (Uncertainty-Aware, Not Prescriptive)</h3>
        <p>
          Under your specified operational weights, <strong>{lead.strategy.name}</strong> achieves
          the highest composite rank in <strong>{Math.round(lead.pBest * 100)}%</strong> of 2,000
          simulated scenarios crossing 30 years of NASA POWER climate variability with weight
          uncertainty.
        </p>
        <p className="print-disclaimer">
          <strong>Important:</strong> This tool illustrates relative trade-offs across historical
          weather risk. It does not replace local agronomic expertise. Final cropping decisions rest
          with the farm operator.
        </p>
      </div>

      <div className="print-card print-full-width print-local-verify">
        <h3>Local Verification Points (Finney County, KS)</h3>
        <ul className="print-verify-bullets">
          <li>
            <strong>Groundwater Management District No. 3 (GMD3):</strong> Verify annual well
            allocations, multi-year flex accounts (MYFA), and flow meter limits for this quarter
            section.
          </li>
          <li>
            <strong>K-State Research & Extension (Garden City Center):</strong> Check localized
            hybrid trial performance, planting moisture windows, and rotational disease cycles.
          </li>
          <li>
            <strong>USDA NRCS Service Center:</strong> Assess EQIP/CSP conservation cost-share
            eligibility for cover crops, residue management, and irrigation efficiency.
          </li>
          <li>
            <strong>Garden City Co-op:</strong> Confirm local basis, storage contracts, and
            marketing bids for sorghum, corn, and wheat.
          </li>
        </ul>
      </div>

      {/* Print Footer with Attribution */}
      <div className="print-footer">
        <div>
          FieldShift · NASA Space Apps Challenge 2026 · Finney County, Kansas Decision Support
        </div>
        <div>
          <a
            href="https://www.flaticon.com/free-icons/yield"
            title="yield icons"
            target="_blank"
            rel="noopener noreferrer"
          >
            Yield icons created by Eucalyp - Flaticon
          </a>
        </div>
      </div>
    </div>
  );
}
