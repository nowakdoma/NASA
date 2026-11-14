import { useMemo } from 'react';
import type { FieldFeature, BarePeriod, StressWindow } from '../types/contracts';
import { cropCss, cropLabel } from '../lib/colors';
import { IconInfo } from './Icons';
import { fieldLabel } from '../lib/units';

interface Props {
  field: FieldFeature;
  year: number;
  onSelectYear?: (year: number) => void;
  onOpenAbout?: () => void;
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

export function FieldPanel({ field, year, onSelectYear, onOpenAbout }: Props) {
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
      {/* Header with Title, Field Selector, and Print Action */}
      <div className="passport-header">
        <div className="passport-title-wrap">
          <div className="passport-badge-row">
            <span className="passport-badge">Field Passport</span>
          </div>
          <h2 id="passport-title" className="passport-id">
            {fieldLabel(p)} {p.name && <small className="passport-name">· {p.name}</small>}
          </h2>
        </div>
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
        <span className="chip soil-chip">{p.soil.texture}</span>
      </div>

      {/* 18-Year Historical Sequence */}
      <div className="crop-history-section">
        <div className="section-title-row">
          <h3>Crop History (2008–2025)</h3>
          <span className="active-crop-pill">
            <span className="swatch inline" style={{ background: cropCss(currentCrop) }} />
            <strong>{year}:</strong> {cropLabel(currentCrop ?? 'n/a')}
          </span>
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
                title={`${y}: ${cropLabel(c)} · Click to switch`}
                aria-label={`${y}: ${cropLabel(c)}${isCurrent ? ' (selected)' : ''}`}
              >
                <span className="cell-year">{y.slice(2)}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Soil Characteristics Grid */}
      <div className="soil-profile-section">
        <div className="section-title-row">
          <h3>Soil Profile (SSURGO)</h3>
          <button
            type="button"
            className="info-icon-btn"
            onClick={onOpenAbout}
            title="Learn more about SSURGO data"
            aria-label="Soil data info"
          >
            <IconInfo />
          </button>
        </div>

        <dl className="kv-grid">
          <div className="kv-item" title="Dominant USDA soil texture class">
            <dt>Texture</dt>
            <dd>{p.soil.texture}</dd>
          </div>
          <div className="kv-item" title="Soil Organic Matter percentage in upper horizon">
            <dt>Organic Matter</dt>
            <dd>{p.soil.om_pct} %</dd>
          </div>
          <div className="kv-item" title="RUSLE Kf erodibility factor of fine-earth fraction">
            <dt>Erodibility (Kf)</dt>
            <dd>{p.soil.kffact}</dd>
          </div>
          <div className="kv-item" title="Available Water Capacity in the root zone">
            <dt>Available Water</dt>
            <dd>{p.soil.awc_mm} mm</dd>
          </div>
          <div className="kv-item" title="Average slope percentage derived from SRTM">
            <dt>Avg Slope</dt>
            <dd>{p.soil.slope_pct} %</dd>
          </div>
          {p.soil.map_unit && (
            <div className="kv-item" title="SSURGO Map Unit Identifier">
              <dt>Map Unit</dt>
              <dd>{p.soil.map_unit}</dd>
            </div>
          )}
        </dl>
      </div>

      {/* Satellite Season Monitoring Timeline */}
      <div className="season-timeline-section">
        <div className="section-title-row">
          <h3>Satellite Season Monitoring ({year})</h3>
          <span
            className={`stress-pill ${
              stressIdx !== undefined && stressIdx > 0.6
                ? 'high'
                : stressIdx !== undefined && stressIdx > 0.3
                  ? 'mid'
                  : 'low'
            }`}
            title="Combined annual stress index (0 = none, 1 = extreme)"
          >
            Stress Index: {stressIdx !== undefined ? stressIdx.toFixed(2) : 'n/a'}
          </span>
        </div>

        {/* Visual Seasonal Timeline Chart */}
        <div className="seasonal-calendar-chart">
          <div className="calendar-axis">
            {MONTHS.map((m) => (
              <span key={m} className="month-tick">
                {m}
              </span>
            ))}
          </div>

          <div className="calendar-tracks">
            {/* Bare soil track */}
            <div className="track-row">
              <span
                className="track-label"
                title="NASA MODIS 250 m greenness (NDVI < 0.3); includes dormant alfalfa and stalks"
              >
                No green cover
              </span>
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
                      title={`No green cover: ${b.start} → ${b.end} (${days}d)\n${b.source}${b.note ? ` · ${b.note}` : ''}`}
                    >
                      {width >= 8 && <span className="bar-text">{days} d</span>}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Water stress track — only when the data has water-stress windows */}
            {waterStress.length > 0 && (
              <div className="track-row">
                <span className="track-label" title="Soil water balance below crop need">
                  Water stress
                </span>
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
                          opacity: 0.65 + s.severity * 0.35,
                        }}
                        title={`Water Stress: ${s.start} → ${s.end} (${days}d)\nSeverity: ${(s.severity * 100).toFixed(0)}%\nSource: ${s.source}`}
                      >
                        {width >= 12 && <span className="bar-text">{days} d</span>}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Heat stress track */}
            <div className="track-row">
              <span className="track-label" title="NASA POWER: 2+ days at or above 35 °C (95 °F)">
                Heat stress
              </span>
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
                        opacity: 0.65 + s.severity * 0.35,
                      }}
                      title={`Heat Stress (Tmax > 35°C): ${s.start} → ${s.end} (${days}d)\nSeverity: ${(s.severity * 100).toFixed(0)}%\nSource: ${s.source}`}
                    >
                      {width >= 12 && <span className="bar-text">{days} d</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Compact Event Pills */}
        {barePeriods.length + stressWindows.length === 0 ? (
          <p className="no-events-notice">
            No periods without green cover and no heat or water stress found for {year}.
          </p>
        ) : (
          <div className="events-compact-grid">
            {barePeriods.map((b, i) => (
              <div
                key={`b-${i}`}
                className="compact-event-card bare"
                title={`${b.source} · ${b.note ?? ''}`}
              >
                <span className="tag-pill bare">No green cover</span>
                <span className="event-date-text">
                  {b.start.slice(5)} → {b.end.slice(5)}
                </span>
                <span className="event-duration-badge">{calculateDays(b.start, b.end)}d</span>
              </div>
            ))}
            {stressWindows.map((s, i) => (
              <div
                key={`s-${i}`}
                className={`compact-event-card ${s.type}`}
                title={`${s.source} · Severity ${(s.severity * 100).toFixed(0)}%`}
              >
                <span className={`tag-pill ${s.type}`}>
                  {s.type === 'water' ? 'Water' : s.type === 'frost' ? 'Frost-free season' : 'Heat'}
                </span>
                <span className="event-date-text">
                  {s.start.slice(5)} → {s.end.slice(5)}
                </span>
                <span className="event-duration-badge">{calculateDays(s.start, s.end)} d</span>
              </div>
            ))}
          </div>
        )}

        {/* Historical 2008–2025 Stress Sparkline */}
        <div className="stress-history-chart">
          <div className="section-title-row">
            <h4>Multi-Year Stress Trend (2008–2025)</h4>
            <span className="chart-legend-label">Click bar to select year</span>
          </div>
          <div className="sparkline-wrapper">
            {stressHistory.map((item) => {
              const isSelected = item.year === year;
              const heightPct = Math.max(item.score * 100, 6);
              const color = item.score > 0.6 ? '#dc2626' : item.score > 0.3 ? '#d97706' : '#16a34a';
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
