import type { FieldCollection, FieldFeature, MetricKey, MetricMeta } from '../types/contracts';
import { METRIC_KEYS, PRIORITY_KEYS } from '../types/contracts';
import type { RankedStrategy, Priorities } from '../lib/ranking';
import type { GraceFile } from '../data/load';
import { cropLabel, cropShort } from '../lib/colors';
import { METRIC_FOOTNOTE, US, acres, fieldDollars, usVal } from '../lib/units';
import { outOfTen, tenths, type LeadExplanation } from '../lib/explain';
import { bareHeadline, bareSummary, DAYS_PER_MONTH } from '../lib/bare';
import { WATER_FLAG_TEXT, waterFlag, waterLimitLabel, type WaterLimitIn } from '../lib/flow';

interface Props {
  field: FieldFeature;
  county: FieldCollection['county'];
  priorities: Priorities;
  presetLabel: string;
  waterLimitIn: WaterLimitIn;
  ranked: RankedStrategy[];
  meta: Record<MetricKey, MetricMeta>;
  weatherYears: [number, number];
  grace: GraceFile | null;
  explanation: LeadExplanation;
}

const PRIORITY_LABEL: Record<(typeof PRIORITY_KEYS)[number], string> = {
  water: 'Save water',
  income: 'Net return',
  soil: 'Soil organic matter',
  erosion: 'Less erosion',
  labour: 'Less labour',
};

/**
 * Printed adviser summary (step 4 → "Print or save as PDF"). Same content and order as the
 * screen: what was explored, the field finding, all four rotations with ranges, what to check,
 * what we don't know. Decision support only — no recommendation wording.
 */
export function PrintReport({
  field,
  county,
  priorities,
  presetLabel,
  waterLimitIn,
  ranked,
  meta,
  weatherYears,
  grace,
  explanation,
}: Props) {
  const p = field.properties;
  const lead = ranked[0];
  const bare = bareSummary(field);
  const head = bare ? bareHeadline(bare) : null;
  const years = Object.keys(p.crop_history).sort();
  const checks = [...new Set(ranked.flatMap((r) => r.strategy.verify_locally))];
  const gaps = [...new Set(ranked.flatMap((r) => r.strategy.data_gaps))];
  const sources = [
    ...new Set(ranked.flatMap((r) => r.strategy.evidence.map((e) => e.dataset))),
    'NASA MODIS MOD13Q1 NDVI (bare soil)',
    ...(grace ? ['NASA JPL GRACE/GRACE-FO mascons (regional water storage)'] : []),
  ];
  const nWeather = weatherYears[1] - weatherYears[0] + 1;
  const today = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  return (
    <div className="print-report-container print-only">
      <header className="print-header">
        <div>
          <div className="print-logo-mark">FieldShift</div>
          <h1 className="print-h1">Field summary for your adviser</h1>
          <p className="print-subtitle">
            {county.name}, {county.state} (FIPS {county.fips}) · decision support, not a
            recommendation
          </p>
        </div>
        <div className="print-meta-box">
          <div>{today}</div>
          <div className="print-url">{window.location.href}</div>
        </div>
      </header>

      <section className="print-card">
        <h2>What was explored</h2>
        <table className="print-kv-table">
          <tbody>
            <tr>
              <th>Field</th>
              <td>
                <strong>{p.field_id}</strong>
                {p.name ? ` (${p.name})` : ''} · {acres(p.area_ha)} ac ({p.area_ha.toFixed(1)} ha) ·{' '}
                {p.irrigation_type === 'center_pivot'
                  ? 'centre pivot'
                  : p.irrigated
                    ? 'irrigated'
                    : 'dryland'}
              </td>
            </tr>
            <tr>
              <th>Soil (USDA SSURGO)</th>
              <td>
                {p.soil.map_unit ?? p.soil.texture} · {p.soil.om_pct} % organic matter · holds{' '}
                {(p.soil.awc_mm / 25.4).toFixed(1)} in ({p.soil.awc_mm} mm) · slope{' '}
                {p.soil.slope_pct.toFixed(1)} % (NASA SRTM)
              </td>
            </tr>
            <tr>
              <th>Priorities</th>
              <td>
                <strong>{presetLabel}</strong> —{' '}
                {PRIORITY_KEYS.map((k) => `${PRIORITY_LABEL[k]} ${priorities[k]}/5`).join(' · ')}
              </td>
            </tr>
            <tr>
              <th>Water you can pump</th>
              <td>{waterLimitLabel(waterLimitIn)}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section className="print-card">
        <h2>What the satellites show for this field</h2>
        {head && (
          <p className="print-finding">
            <strong>{head.title}.</strong> {head.compare} (NASA MODIS NDVI &lt; 0.3, 16-day, 250 m)
          </p>
        )}
        <table className="print-table print-history">
          <thead>
            <tr>
              <th>Year</th>
              {years.map((y) => (
                <th key={y}>{y.slice(2)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <th>Crop (CDL)</th>
              {years.map((y) => (
                <td key={y}>{cropShort(p.crop_history[y])}</td>
              ))}
            </tr>
            {bare && (
              <tr>
                <th>Bare months</th>
                {years.map((y) => (
                  <td key={y}>
                    {((bare.daysByYear.get(Number(y)) ?? 0) / DAYS_PER_MONTH).toFixed(1)}
                  </td>
                ))}
              </tr>
            )}
          </tbody>
        </table>
        {grace && (
          <p className="print-muted">
            Regional water storage (NASA GRACE/GRACE-FO): {grace.trend.cm_per_year.toFixed(2)} cm
            per year since {grace.series[0].date.slice(0, 4)}. A ~300 km regional signal of total
            water storage, not this well.
            {grace.mock ? ' (Sample data, not the measured series.)' : ''}
          </p>
        )}
      </section>

      <section className="print-card">
        <h2>
          Four rotations across {nWeather} years of NASA POWER weather ({weatherYears[0]}–
          {weatherYears[1]})
        </h2>
        {lead && (
          <p className="print-finding">
            {explanation.noneFits ?? (
              <>
                Under <strong>{presetLabel}</strong> priorities
                {waterLimitIn !== null
                  ? waterLimitIn === 0
                    ? ' with no irrigation'
                    : ` and a ${waterLimitIn} in water limit`
                  : ''}
                , <strong>{lead.strategy.name}</strong> came out on top in{' '}
                <strong>{outOfTen(lead.pBest)}</strong> (2,000 runs of {nWeather} weather years with
                slightly varied priorities). {explanation.why}
              </>
            )}{' '}
            {explanation.excluded.join(' ')} Values: typical year, with 1-in-10 low – 1-in-10 high
            in brackets.
          </p>
        )}
        <table className="print-table strat-print-table">
          <thead>
            <tr>
              <th>Rotation</th>
              <th>On top (of 10 runs)</th>
              {METRIC_KEYS.map((m) => (
                <th key={m}>
                  {meta[m].label}
                  <small className="th-unit"> ({US[m].unit})</small>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ranked.map(({ strategy: s, pBest }) => (
              <tr key={s.id} className={s.is_current ? 'current-strat-row' : ''}>
                <td>
                  <strong>{s.name}</strong>
                  {s.is_current && <span className="print-pill current">now</span>}
                  <div className="print-rot-col">{s.rotation.map(cropLabel).join(' → ')}</div>
                  <div className="print-rot-col">
                    ≈ {fieldDollars(s.metrics.income_usd_ha.p50, p.area_ha)} net for the field
                  </div>
                </td>
                <td>
                  <strong>{tenths(pBest)}</strong>
                </td>
                {METRIC_KEYS.map((m) => {
                  const q = s.metrics[m];
                  return (
                    <td key={m} className="interval-td">
                      <div className="p50-val">{usVal(m, q.p50)}</div>
                      <div className="range-val">
                        [{usVal(m, q.p10)} – {usVal(m, q.p90)}]
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {ranked.map(({ strategy: s }) => {
        const flag = waterFlag(s.metrics.water_use_mm, waterLimitIn);
        const t = s.soil_health_traits;
        const traits = t
          ? [
              t.n_fixing_years > 0 &&
                (t.n_fixing_years >= s.rotation.length
                  ? 'fixes nitrogen every year'
                  : `fixes nitrogen ${t.n_fixing_years} of ${s.rotation.length} yrs`),
              t.pest_break && 'breaks pest cycles',
              t.forage && 'forage',
            ].filter(Boolean)
          : [];
        return (
          <section key={s.id} className="print-card print-strategy">
            <h3>
              {s.name}
              {s.is_current ? ' (now)' : ''}
            </h3>
            {(s.why_considered ?? s.description) && (
              <p>
                <strong>Why it's here:</strong> {s.why_considered ?? s.description}
              </p>
            )}
            {traits.length > 0 && <p className="print-muted">Soil health: {traits.join(' · ')}</p>}
            {flag && <p className="print-flag">⚠ {WATER_FLAG_TEXT[flag]}</p>}
            <div className="print-two-col">
              {s.benefits && s.benefits.length > 0 && (
                <div>
                  <h4>Benefits</h4>
                  <ul>
                    {s.benefits.map((b) => (
                      <li key={b}>{b}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div>
                <h4>Check locally</h4>
                <ul>
                  {s.verify_locally.map((v) => (
                    <li key={v}>{v}</li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        );
      })}

      <section className="print-card print-callout">
        <h2>{checks.length} questions to take to your adviser or water district</h2>
        <ol>
          {checks.map((c) => (
            <li key={c}>{c}</li>
          ))}
        </ol>
        <p className="print-muted">
          Who can help locally: your groundwater management district (well allocation and meter
          limits), K-State Research and Extension (local trials, planting windows), the USDA NRCS
          service centre (cover-crop and conservation cost-share), your elevator or buyer (basis and
          contracts).
        </p>
      </section>

      <section className="print-card">
        <h2>What we don't know</h2>
        <ul>
          {gaps.map((g) => (
            <li key={g}>{g}</li>
          ))}
        </ul>
      </section>

      <footer className="print-footer">
        <p className="print-disclaimer">
          This summary shows ranges and trade-offs under the weather of {weatherYears[0]}–
          {weatherYears[1]}. It supports, and does not replace, your judgment and local expertise.
        </p>
        <div>
          Net return is {US.income_usd_ha.note}. {METRIC_FOOTNOTE}
        </div>
        <div>Data: {sources.join(' · ')}.</div>
        <div>
          FieldShift · NASA Space Apps Challenge 2026 ·{' '}
          <a href="https://www.flaticon.com/free-icons/yield" title="yield icons">
            Yield icons created by Eucalyp - Flaticon
          </a>
        </div>
      </footer>
    </div>
  );
}
