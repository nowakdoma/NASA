import { useMemo } from 'react';
import { fieldLabel } from '../lib/units';
import type { FieldFeature } from '../types/contracts';
import { cropCss, cropLabel } from '../lib/colors';
import { FieldHeadline } from './FieldHeadline';

const DAY = 86_400_000;
const spanDays = (a: string, b: string) => Math.max(0, (Date.parse(b) - Date.parse(a)) / DAY + 1);

interface Props {
  field: FieldFeature;
  year: number;
  onSelectYear: (y: number) => void;
}

/** Step 1 (design canvas B): headline finding, crop strip, bare-months bars, sourced facts. */
export function FieldStep({ field, year, onSelectYear }: Props) {
  const p = field.properties;
  const years = useMemo(
    () =>
      Object.keys(p.crop_history)
        .map(Number)
        .sort((a, b) => a - b),
    [p.crop_history],
  );

  const bareDays = useMemo(() => {
    const m = new Map<number, number>(years.map((y) => [y, 0]));
    for (const b of p.season_calendar.bare_periods)
      if (m.has(b.year)) m.set(b.year, (m.get(b.year) ?? 0) + spanDays(b.start, b.end));
    return m;
  }, [p.season_calendar.bare_periods, years]);
  const maxBare = Math.max(1, ...bareDays.values());

  const lastYear = years[years.length - 1];
  const heatDays = p.season_calendar.stress_windows
    .filter((w) => w.type === 'heat' && w.year === lastYear)
    .reduce((s, w) => s + spanDays(w.start, w.end), 0);

  const crops = [...new Set(years.map((y) => p.crop_history[String(y)]).filter(Boolean))];

  const facts = [
    {
      label: 'Soil',
      value: `${p.soil.texture}, ${p.soil.om_pct} % organic matter`,
      src: 'USDA SSURGO',
    },
    {
      label: 'Water the soil can hold',
      value: `${(p.soil.awc_mm / 25.4).toFixed(1)} in (${p.soil.awc_mm} mm) in the root zone`,
      src: 'USDA SSURGO',
    },
    { label: 'Slope', value: `${p.soil.slope_pct.toFixed(1)} %`, src: 'NASA SRTM 30 m' },
    {
      label: `Heat-stress days ${lastYear}`,
      value: `${Math.round(heatDays)} days`,
      src: 'NASA POWER',
    },
  ];

  return (
    <div className="flow-step">
      <div className="flow-eyebrow">Step 1 · {fieldLabel(p)}</div>
      <FieldHeadline field={field} />

      <div>
        <div className="strip-head">
          <span>Crop each year · USDA crop map (CDL)</span>
          <span>
            {years[0]} → {lastYear}
          </span>
        </div>
        <div
          className="year-strip"
          style={{ gridTemplateColumns: `repeat(${years.length}, minmax(0, 1fr))` }}
        >
          {years.map((y) => {
            const c = p.crop_history[String(y)];
            return (
              <button
                key={y}
                type="button"
                className={`crop-cell${y === year ? ' active' : ''}`}
                style={{ background: c ? cropCss(c) : undefined }}
                title={`${y}: ${c ? cropLabel(c) : 'unknown'}`}
                aria-label={`${y}: ${c ? cropLabel(c) : 'unknown'}. Show on map`}
                aria-pressed={y === year}
                onClick={() => onSelectYear(y)}
              />
            );
          })}
        </div>
        <div className="strip-legend">
          {crops.map((c) => (
            <span key={c}>
              <span className="swatch" style={{ background: cropCss(c) }} aria-hidden="true" />
              {cropLabel(c)}
            </span>
          ))}
        </div>

        <div className="strip-head" style={{ marginTop: 14 }}>
          <span>Months without green cover · NASA MODIS</span>
          <span className="strip-key">
            <span className="swatch bare-hi" aria-hidden="true" /> 5+ months
          </span>
        </div>
        <div
          className="bare-bars"
          style={{ gridTemplateColumns: `repeat(${years.length}, minmax(0, 1fr))` }}
          role="img"
          aria-label={`Months without green cover per year: ${years
            .map((y) => `${y} ${((bareDays.get(y) ?? 0) / 30.4).toFixed(1)}`)
            .join(', ')}`}
        >
          {years.map((y) => {
            const d = bareDays.get(y) ?? 0;
            const mo = d / 30.4;
            return (
              <span
                key={y}
                className={`bare-bar${mo >= 5 ? ' hi' : ''}`}
                style={{ height: `${Math.max(3, (d / maxBare) * 100)}%` }}
                title={`${y}: about ${mo.toFixed(1)} months without green cover`}
              />
            );
          })}
        </div>
        <div className="strip-axis">
          <span>{years[0]}</span>
          <span>{lastYear}</span>
        </div>
      </div>

      <dl className="fact-grid">
        {facts.map((f) => (
          <div key={f.label} className="fact-card">
            <dt>{f.label}</dt>
            <dd className="fact-value">{f.value}</dd>
            <dd className="fact-src">{f.src}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
