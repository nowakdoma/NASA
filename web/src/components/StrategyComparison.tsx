import { useState } from 'react';
import { METRIC_KEYS, type MetricKey, type MetricMeta } from '../types/contracts';
import type { RankedStrategy } from '../lib/ranking';
import { cropLabel } from '../lib/colors';
import { US } from '../lib/units';
import { outOfTen, tenths } from '../lib/explain';
import {
  IconAlertTriangle,
  IconArrowRight,
  IconInfo,
  IconPin,
  IconSatellite,
  IconScales,
} from './Icons';

interface Props {
  ranked: RankedStrategy[];
  meta: Record<MetricKey, MetricMeta>;
  weatherYears: [number, number];
  onOpenAbout?: () => void;
}

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

/** SVG interval chart displaying [p10, p90] uncertainty span with p50 median tick */
function IntervalPlot({
  rows,
  meta,
  fmt,
}: {
  rows: IntervalRow[];
  meta: MetricMeta;
  fmt: (x: number) => string;
}) {
  const minVal = Math.min(...rows.map((r) => r.p10));
  const maxVal = Math.max(...rows.map((r) => r.p90));

  // Add 6% padding to scale domain
  const span = Math.max(maxVal - minVal, 1e-4);
  const domainMin = minVal < 0 ? minVal - span * 0.06 : Math.max(0, minVal - span * 0.06);
  const domainMax = maxVal + span * 0.06;
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
          const widthPct = Math.max(rightPct - leftPct, 1.8);
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
                    {r.deltaP50 > 0 ? '+' : r.deltaP50 < 0 ? '−' : ''}
                    {fmt(Math.abs(r.deltaP50))}{' '}
                    {meta.unit.startsWith('score')
                      ? 'vs now'
                      : `${meta.unit} (${r.deltaPct! > 0 ? '+' : ''}${r.deltaPct} %)`}
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
                  title={`${r.name}\n1-in-10 low: ${fmt(r.p10)} · typical: ${fmt(r.p50)} · 1-in-10 high: ${fmt(r.p90)} ${meta.unit}`}
                />

                {/* Median marker (p50) */}
                <div
                  className="interval-median-marker"
                  style={{ left: `${midPct}%` }}
                  title={`Typical year: ${fmt(r.p50)} ${meta.unit}`}
                />
              </div>

              {/* Exact numeric readout */}
              <div className="interval-row-values">
                <span className="val-p10">low {fmt(r.p10)}</span>
                <span className="val-p50" title="Typical year (median)">
                  typical <strong>{fmt(r.p50)}</strong>
                </span>
                <span className="val-p90">high {fmt(r.p90)}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Axis markers */}
      <div className="interval-axis-row">
        <span>{fmt(domainMin)}</span>
        <span className="axis-title">
          1-in-10 low · typical · 1-in-10 high year (1995–2025 weather)
        </span>
        <span>{fmt(domainMax)}</span>
      </div>
    </div>
  );
}

export function StrategyComparison({ ranked, meta, weatherYears, onOpenAbout }: Props) {
  const [activeMetricTab, setActiveMetricTab] = useState<MetricKey | 'all'>('all');
  const [expandedSection, setExpandedSection] = useState<'verify' | 'gaps' | 'evidence' | null>(
    null,
  );

  if (ranked.length === 0) return <p className="muted">No strategies for this field.</p>;

  const lead = ranked[0];
  const currentRanked = ranked.find((r) => r.strategy.is_current) ?? ranked[0];

  const toggleSection = (section: 'verify' | 'gaps' | 'evidence') => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  return (
    <section className="panel strategy-comparison-panel" aria-labelledby="strat-title">
      <div className="strat-header">
        <div className="title-with-icon">
          <IconScales className="panel-title-icon" />
          <h3 id="strat-title">Rotation Strategy Evaluation</h3>
        </div>
        <span
          className="weather-years-pill"
          title="Evaluated across 30 years of NASA POWER historical weather"
        >
          {weatherYears[0]}–{weatherYears[1]} Climate Range
        </span>
      </div>

      {/* Decision-support callout box */}
      <div className="decision-support-box">
        <div className="box-icon">
          <IconScales />
        </div>
        <div className="box-content">
          <div className="box-lead-text">
            Under these priorities, <strong>{lead.strategy.name}</strong> came out on top in{' '}
            <strong>{outOfTen(lead.pBest)}</strong> (2,000 runs of weather years and slightly varied
            priorities).
          </div>
          <div className="disclaimer">
            Decision support, not a prescription. Final decisions rest with farm management
            judgment.
          </div>
        </div>
      </div>

      {/* Ranking Summary Table */}
      <div className="strategy-table-wrapper">
        <table className="strategy-table" aria-label="Strategy comparison table">
          <thead>
            <tr>
              <th>Strategy</th>
              <th>Rotation Sequence</th>
              <th title="Out of 10 runs (weather year and slightly varied priorities), how often this rotation came first">
                On top (of 10 runs)
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
                  </td>
                  <td className="rotation-sequence">
                    {strategy.rotation.map((c, i) => (
                      <span key={i} className="crop-seq-item">
                        {cropLabel(c)}
                        {i < strategy.rotation.length - 1 && (
                          <IconArrowRight className="seq-arrow" />
                        )}
                      </span>
                    ))}
                  </td>
                  <td className="pbest-cell">
                    <div
                      className="pbest-gauge"
                      title={`Came first in ${Math.round(pBest * 2000).toLocaleString('en-US')} of 2,000 runs`}
                    >
                      <div className="pbest-fill" style={{ width: `${pBest * 100}%` }} />
                      <span className="pbest-percent">{tenths(pBest)}</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Metric Interval Plots with Filter Tabs */}
      <div className="interval-section">
        <div className="interval-tabs-row">
          <button
            type="button"
            className={`tab-btn${activeMetricTab === 'all' ? ' active' : ''}`}
            onClick={() => setActiveMetricTab('all')}
          >
            All 5 Metrics
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
            const u = US[m].f;
            const currentP50 = u(currentRanked.strategy.metrics[m].p50);
            const rows: IntervalRow[] = ranked.map(({ strategy, pBest }) => {
              const raw = strategy.metrics[m];
              const q = { p10: u(raw.p10), p50: u(raw.p50), p90: u(raw.p90) };
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

            return (
              <IntervalPlot
                key={m}
                rows={rows}
                meta={{ ...meta[m], unit: US[m].unit }}
                fmt={US[m].fmt}
              />
            );
          })}
        </div>
      </div>

      {/* Compact Ground-Truthing Accordion Section */}
      <div className="ground-truth-accordion">
        {/* Verify Locally Accordion */}
        <div className="accordion-item">
          <button
            type="button"
            className={`accordion-trigger${expandedSection === 'verify' ? ' open' : ''}`}
            onClick={() => toggleSection('verify')}
            aria-expanded={expandedSection === 'verify'}
          >
            <span className="trigger-label">
              <IconPin className="section-icon" /> Check locally (water district · K-State · NRCS)
            </span>
            <span className="accordion-toggle-indicator">
              {expandedSection === 'verify' ? '−' : '+'}
            </span>
          </button>
          {expandedSection === 'verify' && (
            <div className="accordion-content">
              <ul className="clean-bullet-list">
                <li>
                  <strong>
                    Southwest Kansas Groundwater Management District 3 (GMD3, Garden City):
                  </strong>{' '}
                  Confirm authorized well appropriation & flow meter limits.
                </li>
                <li>
                  <strong>K-State SW Center:</strong> Review local variety trial yields, planting
                  windows, and disease cycles.
                </li>
                <li>
                  <strong>USDA NRCS:</strong> Check EQIP/CSP cost-share eligibility for cover crops
                  & reduced tillage.
                </li>
                <li>
                  <strong>Grain Elevator / Basis:</strong> Review Garden City Co-op bids for
                  sorghum, corn, and wheat.
                </li>
              </ul>
            </div>
          )}
        </div>

        {/* Model Limitations Accordion */}
        <div className="accordion-item">
          <button
            type="button"
            className={`accordion-trigger${expandedSection === 'gaps' ? ' open' : ''}`}
            onClick={() => toggleSection('gaps')}
            aria-expanded={expandedSection === 'gaps'}
          >
            <span className="trigger-label">
              <IconAlertTriangle className="section-icon warning" /> Model Assumptions & Data Gaps
            </span>
            <span className="accordion-toggle-indicator">
              {expandedSection === 'gaps' ? '−' : '+'}
            </span>
          </button>
          {expandedSection === 'gaps' && (
            <div className="accordion-content">
              <ul className="clean-bullet-list">
                <li>
                  <strong>Wind Erosion:</strong> RUSLE models water erosion; SW Kansas wind erosion
                  is not dynamically coupled.
                </li>
                <li>
                  <strong>Well Pumping Lift:</strong> Live pumping rate (GPM/acre) changes as
                  Ogallala levels decline.
                </li>
                <li>
                  <strong>Subsurface Hardpan:</strong> Caliche layers affect deep drainage beyond
                  SSURGO averages.
                </li>
              </ul>
            </div>
          )}
        </div>

        {/* Evidence Sources Accordion */}
        <div className="accordion-item">
          <button
            type="button"
            className={`accordion-trigger${expandedSection === 'evidence' ? ' open' : ''}`}
            onClick={() => toggleSection('evidence')}
            aria-expanded={expandedSection === 'evidence'}
          >
            <span className="trigger-label">
              <IconSatellite className="section-icon info" /> NASA & USDA Data Sources
            </span>
            <span className="accordion-toggle-indicator">
              {expandedSection === 'evidence' ? '−' : '+'}
            </span>
          </button>
          {expandedSection === 'evidence' && (
            <div className="accordion-content">
              <p className="evidence-summary">
                Built on NASA POWER (weather), NASA MODIS (green cover), NASA SRTM (slope), NASA
                GRACE/GRACE-FO (regional water storage), the USDA crop map (CDL) and USDA soil
                survey (SSURGO).
              </p>
              <button type="button" className="text-link-btn" onClick={onOpenAbout}>
                <IconInfo /> View Complete Methodology & Dataset Documentation
              </button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
