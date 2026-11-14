import type { MetricKey, MetricMeta } from '../types/contracts';
import type { RankedStrategy } from '../lib/ranking';
import { cropLabel } from '../lib/colors';
import {
  MM_PER_IN,
  WATER_FLAG_TEXT,
  waterFlag,
  waterLimitLabel,
  type WaterLimitIn,
} from '../lib/flow';

interface Props {
  ranked: RankedStrategy[];
  meta: Record<MetricKey, MetricMeta>;
  weatherYears: [number, number];
  presetLabel: string;
  waterLimitIn: WaterLimitIn;
  onOpenAbout: () => void;
}

const SHOWN: MetricKey[] = ['water_use_mm', 'income_usd_ha', 'erosion_t_ha'];

const fmt = (m: MetricKey, x: number) => {
  if (m === 'income_usd_ha') return `${x < 0 ? '−' : ''}$${Math.abs(Math.round(x))}`;
  if (m === 'water_use_mm') return String(Math.round(x));
  return x.toFixed(2);
};

/** Step 3: one card per rotation, shared scales so bars compare across cards. */
export function CompareStep({
  ranked,
  meta,
  weatherYears,
  presetLabel,
  waterLimitIn,
  onOpenAbout,
}: Props) {
  if (ranked.length === 0) return <p className="flow-sub">No rotations computed for this field.</p>;
  const lead = ranked[0];

  const domain = Object.fromEntries(
    SHOWN.map((m) => {
      let lo = Math.min(...ranked.map((r) => r.strategy.metrics[m].p10));
      let hi = Math.max(...ranked.map((r) => r.strategy.metrics[m].p90));
      if (m === 'water_use_mm' && waterLimitIn !== null)
        hi = Math.max(hi, waterLimitIn * MM_PER_IN);
      if (lo > 0) lo = 0;
      const pad = (hi - lo || 1) * 0.04;
      return [m, [lo, hi + pad]];
    }),
  ) as Record<MetricKey, [number, number]>;
  const pct = (m: MetricKey, x: number) => {
    const [lo, hi] = domain[m];
    return Math.max(0, Math.min(100, ((x - lo) / (hi - lo)) * 100));
  };

  return (
    <div className="flow-step">
      <div className="flow-eyebrow">Step 3 · Compare four rotations</div>
      <p className="compare-lead" aria-live="polite">
        Under <strong>{presetLabel}</strong> priorities, <strong>{lead.strategy.name}</strong>{' '}
        scores highest in <strong>{Math.round(lead.pBest * 100)} %</strong> of weather and priority
        samples.
      </p>
      <p className="flow-sub">
        Water limit: {waterLimitLabel(waterLimitIn)}. Bars run from a 1-in-10 low to a 1-in-10 high
        year ({weatherYears[0]}–{weatherYears[1]} weather); the tick is a typical year. Decision
        support, not a recommendation.
      </p>

      <ol className="strategy-cards">
        {ranked.map(({ strategy: s, pBest }) => {
          const flag = waterFlag(s.metrics.water_use_mm, waterLimitIn);
          return (
            <li key={s.id} className={`strategy-card${flag ? ' flagged' : ''}`}>
              <div className="card-head">
                <span className="card-name">
                  {s.name}
                  {s.is_current && <span className="tag current-tag">now</span>}
                </span>
                <span
                  className="card-pct"
                  title="Share of weather × priority samples in which this rotation scores highest"
                >
                  {Math.round(pBest * 100)} %
                </span>
              </div>
              <div className="card-seq">{s.rotation.map(cropLabel).join(' → ')}</div>
              {s.description && <p className="card-why">{s.description}</p>}
              {flag && (
                <p className="card-flag" role="note">
                  ⚠ {WATER_FLAG_TEXT[flag]}
                </p>
              )}

              <div className="card-bars">
                {SHOWN.map((m) => {
                  const q = s.metrics[m];
                  const l = pct(m, q.p10);
                  const r = pct(m, q.p90);
                  return (
                    <div className="card-bar-row" key={m}>
                      <span className="card-bar-label">
                        {meta[m].label}
                        <small> {meta[m].unit}</small>
                      </span>
                      <span
                        className="card-bar-track"
                        role="img"
                        aria-label={`${meta[m].label}: ${fmt(m, q.p10)} to ${fmt(m, q.p90)}, typical ${fmt(m, q.p50)} ${meta[m].unit}`}
                      >
                        <span
                          className="card-bar-range"
                          style={{ left: `${l}%`, width: `${Math.max(r - l, 1.5)}%` }}
                        />
                        <span className="card-bar-tick" style={{ left: `${pct(m, q.p50)}%` }} />
                        {m === 'water_use_mm' && waterLimitIn !== null && (
                          <span
                            className="card-bar-limit"
                            style={{ left: `${pct(m, waterLimitIn * MM_PER_IN)}%` }}
                            title={`Your limit: ${waterLimitLabel(waterLimitIn)}`}
                          />
                        )}
                      </span>
                      <span className="card-bar-val">
                        {q.p10 === q.p90 ? fmt(m, q.p50) : `${fmt(m, q.p10)}–${fmt(m, q.p90)}`}
                      </span>
                    </div>
                  );
                })}
              </div>

              <details className="card-details">
                <summary>Check locally, evidence and what we don't know</summary>
                <div className="card-details-grid">
                  <div>
                    <h4>Check locally</h4>
                    <ul>
                      {s.verify_locally.map((v) => (
                        <li key={v}>{v}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4>What we don't know</h4>
                    <ul>
                      {s.data_gaps.map((g) => (
                        <li key={g}>{g}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                <p className="card-evidence">
                  Evidence: {s.evidence.map((e) => e.dataset).join(' · ')}.{' '}
                  <button type="button" className="text-link-btn" onClick={onOpenAbout}>
                    How we know
                  </button>
                </p>
              </details>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
