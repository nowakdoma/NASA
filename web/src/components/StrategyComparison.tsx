import { useState } from 'react';
import { METRIC_KEYS, type MetricKey, type MetricMeta } from '../types/contracts';
import type { RankedStrategy } from '../lib/ranking';
import { cropLabel } from '../lib/colors';

interface Props {
  ranked: RankedStrategy[];
  meta: Record<MetricKey, MetricMeta>;
  weatherYears: [number, number];
}

const fmt = (x: number) => {
  if (Math.abs(x) >= 100) return x.toFixed(0);
  if (Math.abs(x) >= 10) return x.toFixed(1);
  return x.toFixed(2);
};

interface IntervalRow {
  id: string;
  name: string;
  isCurrent: boolean;
  p10: number;
  p50: number;
  p90: number;
  pBest: number;
  deltaP50?: number;
  deltaPct?: number;
}

/** Pixel-perfect SVG interval chart displaying [p10, p90] uncertainty span with p50 median tick */
function IntervalPlot({ rows, meta }: { rows: IntervalRow[]; meta: MetricMeta }) {
  const minVal = Math.min(...rows.map((r) => r.p10));
  const maxVal = Math.max(...rows.map((r) => r.p90));

  // Add 5% padding to scale domain
  const span = Math.max(maxVal - minVal, 1e-4);
  const domainMin = minVal < 0 ? minVal - span * 0.05 : Math.max(0, minVal - span * 0.05);
  const domainMax = maxVal + span * 0.05;
  const domainSpan = domainMax - domainMin;

  const toPct = (val: number) => ((val - domainMin) / domainSpan) * 100;

  return (
    <div className="interval-plot-wrapper">
      <div className="interval-plot-header">
        <div className="metric-info">
          <span className="metric-label">{meta.label}</span>
          <span className="metric-unit">({meta.unit})</span>
        </div>
        <span className={`direction-badge ${meta.better}`}>
          {meta.better === 'lower' ? '↓ Lower is better' : '↑ Higher is better'}
        </span>
      </div>

      <div className="interval-rows-container">
        {rows.map((r) => {
          const leftPct = toPct(r.p10);
          const rightPct = toPct(r.p90);
          const widthPct = Math.max(rightPct - leftPct, 1.5);
          const midPct = toPct(r.p50);

          return (
            <div
              key={r.id}
              className={`interval-row-item${r.isCurrent ? ' current-strategy' : ''}`}
            >
              <div className="interval-row-label">
                <span className="strat-name">{r.name}</span>
                {r.isCurrent && <span className="current-badge">Current</span>}
                {r.deltaP50 !== undefined && !r.isCurrent && (
                  <span
                    className={`delta-badge ${
                      (meta.better === 'lower' && r.deltaP50 < 0) ||
                      (meta.better === 'higher' && r.deltaP50 > 0)
                        ? 'favorable'
                        : 'unfavorable'
                    }`}
                  >
                    {r.deltaP50 > 0 ? '+' : ''}
                    {fmt(r.deltaP50)} {meta.unit} ({r.deltaPct! > 0 ? '+' : ''}
                    {r.deltaPct}%)
                  </span>
                )}
              </div>

              <div className="interval-track-container">
                {/* Background track line */}
                <div className="interval-track-bg" />

                {/* Range span (p10 to p90) */}
                <div
                  className="interval-span"
                  style={{
                    left: `${leftPct}%`,
                    width: `${widthPct}%`,
                  }}
                  title={`Strategy: ${r.name}\np10: ${fmt(r.p10)} · p50: ${fmt(r.p50)} · p90: ${fmt(r.p90)} ${meta.unit}`}
                />

                {/* Median marker (p50) */}
                <div
                  className="interval-median-marker"
                  style={{ left: `${midPct}%` }}
                  title={`Median (p50): ${fmt(r.p50)} ${meta.unit}`}
                />
              </div>

              {/* Exact numeric readout */}
              <div className="interval-row-values">
                <span className="val-p10">{fmt(r.p10)}</span>
                <span className="val-p50" title="Median (p50)">
                  <strong>{fmt(r.p50)}</strong>
                </span>
                <span className="val-p90">{fmt(r.p90)}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Axis markers */}
      <div className="interval-axis-row">
        <span>{fmt(domainMin)}</span>
        <span className="axis-title">1995–2025 Weather Uncertainty Interval (p10 · p50 · p90)</span>
        <span>{fmt(domainMax)}</span>
      </div>
    </div>
  );
}

export function StrategyComparison({ ranked, meta, weatherYears }: Props) {
  const [activeMetricTab, setActiveMetricTab] = useState<MetricKey | 'all'>('all');

  if (ranked.length === 0) return <p className="muted">No strategies for this field.</p>;

  const lead = ranked[0];
  const currentRanked = ranked.find((r) => r.strategy.is_current) ?? ranked[0];

  return (
    <section className="panel strategy-comparison-panel" aria-labelledby="strat-title">
      <div className="strat-header">
        <h3 id="strat-title">Rotation Strategy Evaluation</h3>
        <span className="weather-years-pill">
          Weather Distribution: {weatherYears[0]}–{weatherYears[1]}
        </span>
      </div>

      <p className="muted strat-explanation">
        Quantifies performance intervals (p10 / p50 / p90) across 30 years of NASA POWER weather
        variability. <strong>P(best)</strong> measures the proportion of 2,000 simulated weather and
        farmer-weight scenarios where a rotation scores highest.
      </p>

      {/* Ranking Summary Table */}
      <div className="strategy-table-wrapper">
        <table className="strategy-table" aria-label="Strategy comparison table">
          <thead>
            <tr>
              <th>Strategy</th>
              <th>Crop Rotation Sequence</th>
              <th title="Probability of achieving highest composite score under current priorities">
                P(best)
              </th>
            </tr>
          </thead>
          <tbody>
            {ranked.map(({ strategy, pBest }) => {
              const isLead = strategy.id === lead.strategy.id;
              const isCurrent = strategy.is_current;
              return (
                <tr
                  key={strategy.id}
                  className={`${isCurrent ? 'current ' : ''}${isLead ? 'lead-row' : ''}`}
                >
                  <td className="strat-cell">
                    <div className="strat-name-wrapper">
                      <strong>{strategy.name}</strong>
                      {isCurrent && <span className="tag current-tag">current</span>}
                      {isLead && <span className="tag lead-tag">lead</span>}
                    </div>
                    {strategy.description && (
                      <span className="strat-desc">{strategy.description}</span>
                    )}
                  </td>
                  <td className="rotation-sequence">
                    {strategy.rotation.map((c, i) => (
                      <span key={i} className="crop-seq-item">
                        {cropLabel(c)}
                        {i < strategy.rotation.length - 1 && <span className="arrow"> → </span>}
                      </span>
                    ))}
                  </td>
                  <td className="pbest-cell">
                    <div className="pbest-gauge">
                      <div className="pbest-fill" style={{ width: `${pBest * 100}%` }} />
                      <span className="pbest-percent">{Math.round(pBest * 100)}%</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Decision-support callout box strictly following AGENTS.md guidelines */}
      <div className="decision-support-box">
        <div className="box-icon">⚖️</div>
        <div className="box-content">
          <strong>Decision Support Finding:</strong>
          <p>
            Under your chosen priority weights, <strong>{lead.strategy.name}</strong> scores highest
            in <strong>{Math.round(lead.pBest * 100)}%</strong> of simulated weather (1995–2025) and
            preference samples.
          </p>
          <p className="disclaimer">
            This tool highlights trade-offs across historical climate risk. It provides decision
            support, not prescriptive advice. Final planting decisions rest with your local
            management judgment.
          </p>
        </div>
      </div>

      {/* Metric Interval Plots */}
      <div className="interval-section">
        <div className="interval-tabs-row">
          <button
            type="button"
            className={`tab-btn${activeMetricTab === 'all' ? ' active' : ''}`}
            onClick={() => setActiveMetricTab('all')}
          >
            All Metrics
          </button>
          {METRIC_KEYS.map((m) => (
            <button
              key={m}
              type="button"
              className={`tab-btn${activeMetricTab === m ? ' active' : ''}`}
              onClick={() => setActiveMetricTab(m)}
            >
              {meta[m].label}
            </button>
          ))}
        </div>

        <div className="plots-list">
          {(activeMetricTab === 'all' ? METRIC_KEYS : [activeMetricTab]).map((m) => {
            const currentP50 = currentRanked.strategy.metrics[m].p50;
            const rows: IntervalRow[] = ranked.map(({ strategy, pBest }) => {
              const q = strategy.metrics[m];
              const deltaP50 = q.p50 - currentP50;
              const deltaPct =
                currentP50 !== 0 ? Math.round((deltaP50 / Math.abs(currentP50)) * 100) : 0;
              return {
                id: strategy.id,
                name: strategy.name,
                isCurrent: strategy.is_current,
                p10: q.p10,
                p50: q.p50,
                p90: q.p90,
                pBest,
                deltaP50: strategy.is_current ? undefined : deltaP50,
                deltaPct: strategy.is_current ? undefined : deltaPct,
              };
            });

            return <IntervalPlot key={m} rows={rows} meta={meta[m]} />;
          })}
        </div>
      </div>

      {/* Ground-Truthing & Local Verification */}
      <div className="ground-truth-section">
        <div className="ground-box verify-locally">
          <h4>📍 Verify Locally (Finney County, KS)</h4>
          <p className="ground-intro">
            Check local conditions with regional agricultural and water institutions:
          </p>
          <ul>
            <li>
              <strong>Groundwater Management District No. 3 (GMD3):</strong> Verify authorized well
              appropriation, multi-year flex accounts (MYFA), and flow meter limits for this
              quarter/section.
            </li>
            <li>
              <strong>
                K-State Research & Extension (SW Research-Extension Center, Garden City):
              </strong>{' '}
              Review localized hybrid/variety trial yields, disease/pest cycles, and planting
              moisture thresholds.
            </li>
            <li>
              <strong>USDA NRCS Finney County Service Center:</strong> Assess EQIP / CSP
              conservation cost-share eligibility for cover crops, reduced tillage, and water
              conservation.
            </li>
            <li>
              <strong>Garden City Grain Handlers & Feed Yards:</strong> Confirm local basis, storage
              options, and delivery contracts for grain sorghum, wheat, and corn.
            </li>
            <li>
              <strong>Herbicide & Herbicide Carryover:</strong> Review multi-year chemical history
              for plant-back restrictions between broadleaf and grass crops.
            </li>
          </ul>
        </div>

        <div className="ground-box data-gaps">
          <h4>⚠️ What We Don’t Know (Model Limitations & Gaps)</h4>
          <ul>
            {[...new Set(ranked.flatMap((r) => r.strategy.data_gaps))].map((g, i) => (
              <li key={i}>{g}</li>
            ))}
            <li>
              <strong>Subsurface Soil Variation:</strong> Caliche layers and compaction hardpans
              vary within fields and affect actual root-zone drainage.
            </li>
            <li>
              <strong>Live Well Flow Rates:</strong> Saturated thickness decline in the Ogallala
              aquifer alters peak mid-summer pumping capacity (GPM/acre).
            </li>
          </ul>
        </div>

        <div className="ground-box evidence">
          <h4>🛰️ NASA & USDA Datasets Used</h4>
          <ul className="evidence-list">
            {[
              ...new Map(
                ranked.flatMap((r) => r.strategy.evidence).map((e) => [e.dataset, e]),
              ).values(),
            ].map((e) => (
              <li key={e.dataset}>
                <span className="dataset-name">{e.dataset}</span>
                <span className="dataset-note">{e.note}</span>
              </li>
            ))}
            <li>
              <span className="dataset-name">NASA SMAP & MODIS</span>
              <span className="dataset-note">
                Root-zone soil moisture anomalies and 250m NDVI vegetation cover dynamics.
              </span>
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}
