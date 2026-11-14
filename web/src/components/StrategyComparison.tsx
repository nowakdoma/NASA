import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { METRIC_KEYS, type MetricKey, type MetricMeta } from '../types/contracts';
import type { RankedStrategy } from '../lib/ranking';
import { cropLabel } from '../lib/colors';

interface Props {
  ranked: RankedStrategy[];
  meta: Record<MetricKey, MetricMeta>;
  weatherYears: [number, number];
}

const fmt = (x: number) => (Math.abs(x) >= 10 ? x.toFixed(0) : x.toFixed(2));

/** p10–p90 range as a floating bar (stacked: invisible offset + visible span), p50 in label. */
function MetricIntervalChart({
  ranked,
  metric,
  meta,
}: {
  ranked: RankedStrategy[];
  metric: MetricKey;
  meta: MetricMeta;
}) {
  const rows = ranked.map(({ strategy }) => {
    const q = strategy.metrics[metric];
    return { name: strategy.id, offset: q.p10, span: q.p90 - q.p10, ...q };
  });
  const lo = Math.min(0, ...rows.map((r) => r.p10));
  return (
    <div className="metric-chart">
      <div className="metric-title">
        {meta.label}{' '}
        <span className="muted">
          ({meta.unit}, {meta.better} is better)
        </span>
      </div>
      <ResponsiveContainer width="100%" height={22 * rows.length + 24}>
        <BarChart data={rows} layout="vertical" margin={{ left: 0, right: 8, top: 0, bottom: 0 }}>
          <XAxis type="number" domain={[lo, 'auto']} tick={{ fontSize: 10 }} />
          <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 10 }} />
          <Tooltip
            formatter={(_v, _n, item) => {
              const r = item.payload as (typeof rows)[number];
              return [`p10 ${fmt(r.p10)} · p50 ${fmt(r.p50)} · p90 ${fmt(r.p90)}`, meta.label];
            }}
          />
          <Bar dataKey="offset" stackId="a" fill="transparent" isAnimationActive={false} />
          <Bar dataKey="span" stackId="a" fill="#5b8c5a" isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function StrategyComparison({ ranked, meta, weatherYears }: Props) {
  if (ranked.length === 0) return <p className="muted">No strategies for this field.</p>;
  const lead = ranked[0];
  return (
    <section className="panel">
      <h3>Rotation strategies</h3>
      <p className="muted">
        Intervals = p10–p90 over {weatherYears[0]}–{weatherYears[1]} weather. P(best) = share of
        samples (weather × uncertain priority weights) in which a strategy scores highest.
      </p>
      <table className="strategy-table">
        <thead>
          <tr>
            <th>Strategy</th>
            <th>Rotation</th>
            <th title="Probability of scoring highest">P(best)</th>
          </tr>
        </thead>
        <tbody>
          {ranked.map(({ strategy, pBest }) => (
            <tr key={strategy.id} className={strategy.is_current ? 'current' : undefined}>
              <td>
                {strategy.name}
                {strategy.is_current && <span className="tag">current</span>}
              </td>
              <td className="muted">{strategy.rotation.map(cropLabel).join(' → ')}</td>
              <td>
                <div className="pbest">
                  <div className="pbest-bar" style={{ width: `${pBest * 100}%` }} />
                  <span>{Math.round(pBest * 100)} %</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="note">
        Under the priorities above, <strong>{lead.strategy.name}</strong> scores highest in{' '}
        {Math.round(lead.pBest * 100)} % of samples. This describes trade-offs; the decision stays
        with you.
      </p>

      {METRIC_KEYS.map((m) => (
        <MetricIntervalChart key={m} ranked={ranked} metric={m} meta={meta[m]} />
      ))}

      <div className="unknowns">
        <h4>What we don’t know</h4>
        <ul>
          {[...new Set(ranked.flatMap((r) => r.strategy.data_gaps))].map((g) => (
            <li key={g}>{g}</li>
          ))}
        </ul>
        <h4>Verify locally</h4>
        <ul>
          {[...new Set(ranked.flatMap((r) => r.strategy.verify_locally))].map((v) => (
            <li key={v}>{v}</li>
          ))}
        </ul>
        <h4>Evidence</h4>
        <ul>
          {[
            ...new Map(
              ranked.flatMap((r) => r.strategy.evidence).map((e) => [e.dataset, e]),
            ).values(),
          ].map((e) => (
            <li key={e.dataset}>
              <strong>{e.dataset}</strong> — {e.note}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
