import { useMemo } from 'react';
import type { FieldFeature, BarePeriod, StressWindow } from '../types/contracts';
import { cropCss, cropLabel } from '../lib/colors';

interface Props {
  field: FieldFeature;
  year: number;
  onSelectYear?: (year: number) => void;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function getPctOfYear(dateStr: string, activeYear: number): number {
  const [y, m, d] = dateStr.split('-').map(Number);
  if (y < activeYear) return 0;
  if (y > activeYear) return 100;
  const startOfYear = new Date(Date.UTC(activeYear, 0, 1)).getTime();
  const endOfYear = new Date(Date.UTC(activeYear, 11, 31, 23, 59, 59)).getTime();
  const target = new Date(Date.UTC(y, m - 1, d)).getTime();
  const pct = ((target - startOfYear) / (endOfYear - startOfYear)) * 100;
  return Math.max(0, Math.min(100, pct));
}

function calculateDays(startStr: string, endStr: string): number {
  const start = new Date(startStr).getTime();
  const end = new Date(endStr).getTime();
  return Math.max(1, Math.round((end - start) / (1000 * 60 * 60 * 24)));
}

export function FieldPanel({ field, year, onSelectYear }: Props) {
  const p = field.properties;
  const years = Object.keys(p.crop_history).sort();
  const currentCrop = p.crop_history[String(year)];
  const acres = Math.round(p.area_ha * 2.47105);

  const barePeriods = useMemo(
    () => p.season_calendar.bare_periods.filter((b) => b.year === year),
    [p.season_calendar.bare_periods, year],
  );

  const stressWindows = useMemo(
    () => p.season_calendar.stress_windows.filter((s) => s.year === year),
    [p.season_calendar.stress_windows, year],
  );

  const waterStress = useMemo(
    () => stressWindows.filter((s) => s.type === 'water'),
    [stressWindows],
  );
  const heatStress = useMemo(() => stressWindows.filter((s) => s.type === 'heat'), [stressWindows]);

  const stressIdx = p.stress_index_by_year[String(year)];

  // Multi-year stress entries
  const stressHistory = useMemo(() => {
    return years.map((y) => ({
      year: Number(y),
      score: p.stress_index_by_year[y] ?? 0,
      crop: p.crop_history[y],
    }));
  }, [years, p.stress_index_by_year, p.crop_history]);

  return (
    <section className="panel field-passport" aria-labelledby="passport-title">
      <div className="passport-header">
        <div>
          <span className="passport-badge">Field Passport</span>
          <h2 id="passport-title" className="passport-id">
            {p.field_id} {p.name && <small className="passport-name">· {p.name}</small>}
          </h2>
        </div>
        <div className="field-meta-chips">
          <span className="chip area">
            {p.area_ha} ha <span className="muted-text">({acres} ac)</span>
          </span>
          <span className="chip irrig">
            {p.irrigation_type === 'center_pivot'
              ? 'Center Pivot'
              : (p.irrigation_type ?? (p.irrigated ? 'Irrigated' : 'Dryland'))}
          </span>
        </div>
      </div>

      <div className="crop-history-section">
        <div className="section-title-row">
          <h3>Historical Crop Sequence (2008–2025)</h3>
          <span className="hint-label">Click year to inspect</span>
        </div>
        <div className="history-strip" role="list" aria-label="Crop history by year">
          {years.map((y) => {
            const isCurrent = Number(y) === year;
            const c = p.crop_history[y];
            return (
              <button
                key={y}
                type="button"
                role="listitem"
                className={`history-cell${isCurrent ? ' current' : ''}`}
                style={{ background: cropCss(c) }}
                onClick={() => onSelectYear?.(Number(y))}
                title={`${y}: ${cropLabel(c)}`}
                aria-label={`${y}: ${cropLabel(c)}${isCurrent ? ' (selected)' : ''}`}
              >
                <span className="cell-year">{y.slice(2)}</span>
              </button>
            );
          })}
        </div>
        <div className="active-crop-summary">
          <strong>{year} Crop:</strong>{' '}
          <span className="swatch inline" style={{ background: cropCss(currentCrop) }} />
          <span>{cropLabel(currentCrop ?? 'n/a')}</span>
        </div>
      </div>

      <div className="soil-profile-section">
        <h3>Soil Characteristics (SSURGO)</h3>
        <dl className="kv-grid">
          <div className="kv-item">
            <dt>Dominant Texture</dt>
            <dd>{p.soil.texture}</dd>
          </div>
          <div className="kv-item">
            <dt>Organic Matter (OM)</dt>
            <dd>{p.soil.om_pct} %</dd>
          </div>
          <div className="kv-item">
            <dt>Erodibility (Kf factor)</dt>
            <dd>{p.soil.kffact}</dd>
          </div>
          <div className="kv-item">
            <dt>Available Water (AWC)</dt>
            <dd>{p.soil.awc_mm} mm</dd>
          </div>
          <div className="kv-item">
            <dt>Average Slope</dt>
            <dd>{p.soil.slope_pct} %</dd>
          </div>
          {p.soil.map_unit && (
            <div className="kv-item">
              <dt>Map Unit</dt>
              <dd>{p.soil.map_unit}</dd>
            </div>
          )}
        </dl>
      </div>

      <div className="season-timeline-section">
        <div className="section-title-row">
          <h3>Season {year} Satellite Monitoring</h3>
          <span
            className={`stress-pill ${
              stressIdx !== undefined && stressIdx > 0.6
                ? 'high'
                : stressIdx !== undefined && stressIdx > 0.3
                  ? 'mid'
                  : 'low'
            }`}
          >
            Annual Stress Index: {stressIdx !== undefined ? stressIdx.toFixed(2) : 'n/a'}
          </span>
        </div>

        <p className="timeline-caption muted">
          MODIS NDVI bare-soil exposure, SMAP root-zone moisture deficits, and NASA POWER heat
          windows.
        </p>

        {/* Visual Seasonal Timeline Chart */}
        <div className="seasonal-calendar-chart">
          {/* Months header */}
          <div className="calendar-axis">
            {MONTHS.map((m) => (
              <span key={m} className="month-tick">
                {m}
              </span>
            ))}
          </div>

          {/* Timeline Tracks */}
          <div className="calendar-tracks">
            {/* Bare soil track */}
            <div className="track-row">
              <span className="track-label">Bare Soil</span>
              <div className="track-lane">
                {barePeriods.map((b: BarePeriod, i: number) => {
                  const left = getPctOfYear(b.start, year);
                  const right = getPctOfYear(b.end, year);
                  const width = Math.max(right - left, 2);
                  const days = calculateDays(b.start, b.end);
                  return (
                    <div
                      key={`bare-${i}`}
                      className="timeline-bar bare-soil-bar"
                      style={{ left: `${left}%`, width: `${width}%` }}
                      title={`Bare Soil: ${b.start} → ${b.end} (${days} days)\n${b.source}${b.note ? ` · ${b.note}` : ''}`}
                    >
                      <span className="bar-text">{days}d</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Water stress track */}
            <div className="track-row">
              <span className="track-label">Water Stress</span>
              <div className="track-lane">
                {waterStress.map((s: StressWindow, i: number) => {
                  const left = getPctOfYear(s.start, year);
                  const right = getPctOfYear(s.end, year);
                  const width = Math.max(right - left, 2);
                  const days = calculateDays(s.start, s.end);
                  return (
                    <div
                      key={`water-${i}`}
                      className="timeline-bar water-stress-bar"
                      style={{
                        left: `${left}%`,
                        width: `${width}%`,
                        opacity: 0.6 + s.severity * 0.4,
                      }}
                      title={`Water Stress: ${s.start} → ${s.end} (${days} days)\nSeverity: ${(s.severity * 100).toFixed(0)}%\nSource: ${s.source}`}
                    >
                      <span className="bar-text">Sev {(s.severity * 100).toFixed(0)}%</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Heat stress track */}
            <div className="track-row">
              <span className="track-label">Heat Stress</span>
              <div className="track-lane">
                {heatStress.map((s: StressWindow, i: number) => {
                  const left = getPctOfYear(s.start, year);
                  const right = getPctOfYear(s.end, year);
                  const width = Math.max(right - left, 2);
                  const days = calculateDays(s.start, s.end);
                  return (
                    <div
                      key={`heat-${i}`}
                      className="timeline-bar heat-stress-bar"
                      style={{
                        left: `${left}%`,
                        width: `${width}%`,
                        opacity: 0.6 + s.severity * 0.4,
                      }}
                      title={`Heat Stress (Tmax > 35°C): ${s.start} → ${s.end} (${days} days)\nSeverity: ${(s.severity * 100).toFixed(0)}%\nSource: ${s.source}`}
                    >
                      <span className="bar-text">Sev {(s.severity * 100).toFixed(0)}%</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Detailed text event list */}
        {barePeriods.length + stressWindows.length === 0 ? (
          <p className="no-events-notice">
            No bare-soil exposure or severe stress windows recorded for {year}.
          </p>
        ) : (
          <div className="events-detail-list">
            {barePeriods.map((b, i) => (
              <div key={`b-${i}`} className="event-item bare">
                <span className="event-tag bare">Bare Soil</span>
                <span className="event-dates">
                  {b.start} → {b.end} ({calculateDays(b.start, b.end)} days)
                </span>
                <span className="event-meta">
                  {b.source}
                  {b.note ? ` · ${b.note}` : ''}
                </span>
              </div>
            ))}
            {stressWindows.map((s, i) => (
              <div key={`s-${i}`} className={`event-item ${s.type}`}>
                <span className={`event-tag ${s.type}`}>
                  {s.type === 'water' ? 'Water Stress' : 'Heat Stress (Tmax > 35°C)'}
                </span>
                <span className="event-dates">
                  {s.start} → {s.end} ({calculateDays(s.start, s.end)} days)
                </span>
                <span className="event-meta">
                  Severity: <strong>{(s.severity * 100).toFixed(0)}%</strong> · {s.source}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Historical 2008–2025 Stress Sparkline */}
        <div className="stress-history-chart">
          <div className="section-title-row">
            <h4>Historical Stress Index (2008–2025)</h4>
            <span className="chart-legend-label">Higher = more stress</span>
          </div>
          <div className="sparkline-wrapper">
            {stressHistory.map((item) => {
              const isSelected = item.year === year;
              const heightPct = Math.max(item.score * 100, 6);
              const color = item.score > 0.6 ? '#ef4444' : item.score > 0.3 ? '#f59e0b' : '#10b981';
              return (
                <div
                  key={item.year}
                  className={`sparkline-col${isSelected ? ' current' : ''}`}
                  onClick={() => onSelectYear?.(item.year)}
                  title={`${item.year}: Stress Index ${item.score.toFixed(2)} (${cropLabel(item.crop)})`}
                >
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{
                        height: `${heightPct}%`,
                        backgroundColor: color,
                      }}
                    />
                  </div>
                  <span className="sparkline-year">{String(item.year).slice(2)}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
