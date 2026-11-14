import type { MetricKey, MetricMeta, Strategy } from '../types/contracts';
import type { RankedStrategy } from '../lib/ranking';
import { outOfTen, tenths, type LeadExplanation } from '../lib/explain';
import { cropLabel } from '../lib/colors';
import { US, acres, fieldDollars, usVal } from '../lib/units';
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
  explanation: LeadExplanation;
  areaHa: number;
  onOpenAbout: () => void;
}

/** Soil-health traits from the engine (brief: N-fixing, pest-cycle break, forage). Only
 *  traits a rotation has are shown, so a missing chip never reads as a negative claim. */
function TraitChips({ s }: { s: Strategy }) {
  const t = s.soil_health_traits;
  if (!t) return null;
  const chips: { label: string; title: string }[] = [];
  if (t.n_fixing_years > 0)
    chips.push({
      label:
        t.n_fixing_years >= s.rotation.length
          ? 'Fixes nitrogen · every year'
          : `Fixes nitrogen · ${t.n_fixing_years} of ${s.rotation.length} yrs`,
      title: 'Legume years that add nitrogen for the next crop',
    });
  if (t.pest_break)
    chips.push({
      label: 'Breaks pest cycles',
      title: 'Two or more crop families, so pests and weeds adapted to one crop lose their host',
    });
  if (t.forage) chips.push({ label: 'Forage', title: 'Produces hay, silage or grazing' });
  if (!chips.length) return null;
  return (
    <ul className="trait-chips" aria-label="Soil-health traits">
      {chips.map((c) => (
        <li key={c.label} title={c.title}>
          {c.label}
        </li>
      ))}
    </ul>
  );
}

const SHOWN: MetricKey[] = ['water_use_mm', 'income_usd_ha', 'erosion_t_ha'];

/** Step 3: one card per rotation, shared scales so bars compare across cards. */
export function CompareStep({
  ranked,
  meta,
  weatherYears,
  presetLabel,
  waterLimitIn,
  explanation,
  areaHa,
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
      <div className="compare-lead" aria-live="polite">
        {explanation.noneFits ? (
          <p className="compare-nonefits">{explanation.noneFits}</p>
        ) : (
          <p>
            Under <strong>{presetLabel}</strong> priorities
            {waterLimitIn !== null
              ? waterLimitIn === 0
                ? ' with no irrigation'
                : ` and your ${waterLimitIn} in limit`
              : ''}
            , <strong>{lead.strategy.name}</strong> came out on top in{' '}
            <strong>{outOfTen(lead.pBest)}</strong>
            {explanation.close ? ', only just ahead of the next one' : ''}.
          </p>
        )}
        {explanation.why && !explanation.noneFits && (
          <p className="compare-why">{explanation.why}</p>
        )}
        {explanation.excluded.length > 0 && (
          <ul className="compare-excluded">
            {explanation.excluded.map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        )}
      </div>
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
                  title={`On top in ${Math.round(pBest * 100)} % of 2,000 runs (31 weather years × slightly varied priorities)`}
                >
                  {tenths(pBest)}
                  <small> in 10 runs</small>
                </span>
              </div>
              <div className="card-seq">{s.rotation.map(cropLabel).join(' → ')}</div>
              {(s.why_considered ?? s.description) && (
                <p className="card-why">
                  <span className="card-why-label">Why it's here: </span>
                  {s.why_considered ?? s.description}
                </p>
              )}
              <TraitChips s={s} />
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
                        <small> {US[m].unit}</small>
                      </span>
                      <span
                        className="card-bar-track"
                        role="img"
                        aria-label={`${meta[m].label}: ${usVal(m, q.p10)} to ${usVal(m, q.p90)}, typical ${usVal(m, q.p50)} ${US[m].unit}`}
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
                        {q.p10 === q.p90
                          ? usVal(m, q.p50)
                          : `${usVal(m, q.p10)}–${usVal(m, q.p90)}`}
                      </span>
                    </div>
                  );
                })}
              </div>
              <p className="card-total">
                Typical year ≈ <strong>{fieldDollars(s.metrics.income_usd_ha.p50, areaHa)}</strong>{' '}
                net for this {acres(areaHa)}-ac field, {US.income_usd_ha.note}.
              </p>

              <details className="card-details">
                <summary>
                  {s.benefits?.length ? 'Benefits, ' : ''}what to check locally and what we don't
                  know
                </summary>
                {s.benefits && s.benefits.length > 0 && (
                  <div className="card-benefits">
                    <h4>Benefits</h4>
                    <ul>
                      {s.benefits.map((b) => (
                        <li key={b}>{b}</li>
                      ))}
                    </ul>
                  </div>
                )}
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
