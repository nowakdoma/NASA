import type { FieldFeature } from '../types/contracts';
import { cropCss, cropLabel } from '../lib/colors';

// Field "passport": crop history strip, soil, bare-soil periods and stress windows.
export function FieldPanel({ field, year }: { field: FieldFeature; year: number }) {
  const p = field.properties;
  const years = Object.keys(p.crop_history).sort();
  const bare = p.season_calendar.bare_periods.filter((b) => b.year === year);
  const stress = p.season_calendar.stress_windows.filter((s) => s.year === year);
  const stressIdx = p.stress_index_by_year[String(year)];

  return (
    <section className="panel">
      <h2>
        {p.field_id} <small>{p.name}</small>
      </h2>
      <p className="muted">
        {p.area_ha} ha · {p.irrigation_type ?? (p.irrigated ? 'irrigated' : 'dryland')}
      </p>

      <h3>Crop history</h3>
      <div className="history-strip" role="list">
        {years.map((y) => (
          <div
            key={y}
            role="listitem"
            className={`history-cell${Number(y) === year ? ' current' : ''}`}
            style={{ background: cropCss(p.crop_history[y]) }}
            title={`${y}: ${cropLabel(p.crop_history[y])}`}
          >
            {y.slice(2)}
          </div>
        ))}
      </div>

      <h3>Soil</h3>
      <dl className="kv">
        <dt>Texture</dt>
        <dd>{p.soil.texture}</dd>
        <dt>Organic matter</dt>
        <dd>{p.soil.om_pct} %</dd>
        <dt>K factor</dt>
        <dd>{p.soil.kffact}</dd>
        <dt>AWC</dt>
        <dd>{p.soil.awc_mm} mm</dd>
        <dt>Slope</dt>
        <dd>{p.soil.slope_pct} %</dd>
      </dl>

      <h3>Season {year}</h3>
      <p className="muted">
        Stress index: {stressIdx !== undefined ? stressIdx.toFixed(2) : 'n/a'} (0 none – 1 extreme)
      </p>
      {bare.length + stress.length === 0 ? (
        <p className="muted">No bare-soil or stress windows recorded for this year.</p>
      ) : (
        <ul className="windows">
          {bare.map((b, i) => (
            <li key={`b${i}`}>
              <span className="tag bare">bare soil</span> {b.start} → {b.end}
              {b.note && <span className="muted"> · {b.note}</span>}
            </li>
          ))}
          {stress.map((s, i) => (
            <li key={`s${i}`}>
              <span className={`tag ${s.type}`}>{s.type} stress</span> {s.start} → {s.end} ·
              severity {s.severity}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
