import { useMemo, useState } from 'react';
import type { GraceFile } from '../data/load';

const W = 320;
const H = 84;
const PAD = 4;

/** Regional water-storage anomaly (GRACE/GRACE-FO) with its linear trend. One series → no legend. */
export function GraceSparkline({ grace }: { grace: GraceFile }) {
  const [hover, setHover] = useState<number | null>(null);
  const pts = useMemo(() => {
    const t = grace.series.map((s) => Date.parse(s.date));
    const v = grace.series.map((s) => s.tws_cm);
    const t0 = Math.min(...t);
    const t1 = Math.max(...t);
    const lo = Math.min(...v);
    const hi = Math.max(...v);
    const x = (d: number) => PAD + ((d - t0) / (t1 - t0)) * (W - 2 * PAD);
    const y = (c: number) => PAD + (1 - (c - lo) / (hi - lo)) * (H - 2 * PAD);
    // Least-squares line in date space, drawn from the data (matches the pipeline's trend).
    const n = t.length;
    const mt = t.reduce((a, b) => a + b, 0) / n;
    const mv = v.reduce((a, b) => a + b, 0) / n;
    const slope =
      t.reduce((s, ti, i) => s + (ti - mt) * (v[i] - mv), 0) /
      t.reduce((s, ti) => s + (ti - mt) ** 2, 0);
    const fit = (d: number) => mv + slope * (d - mt);
    return {
      xy: grace.series.map((_, i) => [x(t[i]), y(v[i])] as const),
      line: grace.series
        .map((_, i) => `${i ? 'L' : 'M'}${x(t[i]).toFixed(1)},${y(v[i]).toFixed(1)}`)
        .join(''),
      trend: [x(t0), y(fit(t0)), x(t1), y(fit(t1))],
      zeroY: lo < 0 && hi > 0 ? y(0) : null,
    };
  }, [grace]);

  const first = grace.series[0].date.slice(0, 4);
  const last = grace.series[grace.series.length - 1].date.slice(0, 4);
  const h = hover !== null ? grace.series[hover] : null;

  const onMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - r.left) / r.width) * W;
    let best = 0;
    pts.xy.forEach(([x], i) => {
      if (Math.abs(x - px) < Math.abs(pts.xy[best][0] - px)) best = i;
    });
    setHover(best);
  };

  return (
    <figure className="grace-card">
      <figcaption>
        <span className="grace-kicker">
          Water stored underground and in soil · NASA GRACE/GRACE-FO
        </span>
        <span className="grace-hero">
          {grace.trend.cm_per_year.toFixed(2).replace('-', '−')} cm per year
        </span>
        <span className="grace-sub">
          since {first}, every month measured from orbit (trend fits{' '}
          {Math.round(grace.trend.r2 * 100)} % of the variation)
        </span>
      </figcaption>
      <div className="grace-plot">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          role="img"
          aria-label={`Water-storage anomaly ${first}–${last}, falling ${Math.abs(grace.trend.cm_per_year)} cm per year`}
          onPointerMove={onMove}
          onPointerLeave={() => setHover(null)}
        >
          {pts.zeroY !== null && (
            <line x1={0} x2={W} y1={pts.zeroY} y2={pts.zeroY} className="grace-zero" />
          )}
          <path d={pts.line} className="grace-line" />
          <line
            x1={pts.trend[0]}
            y1={pts.trend[1]}
            x2={pts.trend[2]}
            y2={pts.trend[3]}
            className="grace-trend"
          />
          {hover !== null && (
            <>
              <line
                x1={pts.xy[hover][0]}
                x2={pts.xy[hover][0]}
                y1={0}
                y2={H}
                className="grace-cross"
              />
              <circle cx={pts.xy[hover][0]} cy={pts.xy[hover][1]} r={4} className="grace-dot" />
            </>
          )}
        </svg>
        {h && (
          <div
            className="grace-tip"
            style={{ left: `${(pts.xy[hover!][0] / W) * 100}%` }}
            role="status"
          >
            {h.date.slice(0, 7)}: {h.tws_cm > 0 ? '+' : ''}
            {h.tws_cm.toFixed(1)} cm
          </div>
        )}
        <div className="grace-axis">
          <span>{first}</span>
          <span>{last}</span>
        </div>
      </div>
      <p className="grace-note">
        Regional signal (~300 km), not your well. Total water storage, so soil moisture is included,
        not only groundwater.
      </p>
    </figure>
  );
}
