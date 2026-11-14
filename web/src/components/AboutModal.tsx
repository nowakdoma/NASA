import { useEffect, useRef } from 'react';
import type { GraceFile } from '../data/load';
import type { RankedStrategy } from '../lib/ranking';
import { IconClose } from './Icons';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  /** Optional context so the explanations use the user's own field and region. */
  grace?: GraceFile | null;
  ranked?: RankedStrategy[];
  fieldId?: string | null;
  weatherYears?: [number, number];
}

interface Dataset {
  name: string;
  agency: 'NASA' | 'USDA';
  what: string;
  detail: string;
  limit: string;
  pending?: boolean;
}

const SOIL = [
  {
    t: 'Nitrogen-fixing',
    c: '#4f7d3a',
    d: 'Alfalfa, soybeans and other legumes pull nitrogen from the air, so the next corn needs less fertiliser.',
  },
  {
    t: 'Cover crops',
    c: '#2b7a9b',
    d: 'A winter cover such as rye keeps sandy soil from blowing and feeds soil life between cash crops.',
  },
  {
    t: 'Deep-rooting',
    c: '#a4472a',
    d: 'Alfalfa roots reach 2 m or more, open the subsoil and add organic matter deep down.',
  },
  {
    t: 'Drought-tolerant',
    c: '#e2b33c',
    d: 'Sorghum and wheat need less water than corn, so the well and the aquifer last longer.',
  },
];

const JUDGE = [
  'Your water right, well capacity and pumping lift',
  'Local prices, basis and contracts, including a hay buyer',
  'Wind erosion on bare sand (not modelled)',
  'Herbicide carryover between crops',
  'Your labour and equipment',
  'Whether the crop map got your past crops right',
];

const SCALE: [string, string, string, string][] = [
  ['Weather', 'NASA POWER', 'NASA POWER', 'NASA POWER'],
  ['Bare soil, slope, water storage', 'MODIS · SRTM · GRACE-FO', 'same', 'same'],
  ['Crop history', 'USDA CDL', 'USDA CDL', 'ESA WorldCereal'],
  ['Soil', 'USDA SSURGO', 'USDA SSURGO', 'ISRIC SoilGrids'],
  ['Prices and costs', 'K-State budgets', 'State extension budgets', 'Local extension / FAO'],
];

/** "How we know" (design canvas C): data, ranges, soil, your judgment, scaling. */
export function AboutModal({ isOpen, onClose, grace, ranked, fieldId, weatherYears }: Props) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const prev = document.activeElement as HTMLElement | null;
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      prev?.focus?.();
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const [w0, w1] = weatherYears ?? [1995, 2025];
  const datasets: Dataset[] = [
    {
      name: 'NASA POWER',
      agency: 'NASA',
      what: `Daily heat, rain, sun, humidity and wind ${w0}–${w1} → crop water need (FAO-56 Penman-Monteith), heat-stress days (≥ 35 °C for 2+ days), rain erosion.`,
      detail: '~50 km grid (MERRA-2), daily',
      limit: 'Model-based, not a gauge on your farm; it smooths cold nights and local storms.',
    },
    {
      name: 'MODIS NDVI',
      agency: 'NASA',
      what: 'Greenness every 16 days since 2007 → the months your field lies bare.',
      detail: '250 m, 16-day (MOD13Q1)',
      limit: 'A pivot is only ~10 pixels; light residue can read as bare.',
    },
    {
      name: 'SRTM elevation',
      agency: 'NASA',
      what: 'Terrain → field slope for water-erosion risk.',
      detail: '30 m',
      limit: 'Year-2000 surface; misses terraces built since.',
    },
    grace
      ? {
          name: 'GRACE / GRACE-FO',
          agency: 'NASA',
          what: `Changes in all water stored in the region → ${grace.trend.cm_per_year.toFixed(2)} cm per year since ${grace.series[0].date.slice(0, 4)}.`,
          detail: '~300 km mascons, monthly',
          limit: 'Total storage (soil moisture included), regional. Not your well.',
        }
      : {
          name: 'GRACE / GRACE-FO',
          agency: 'NASA',
          what: 'Changes in all water stored in the region → the long-term water-storage trend.',
          detail: '~300 km mascons, monthly',
          limit: 'Not loaded in this build yet. Regional, not your well.',
          pending: true,
        },
    {
      name: 'Cropland Data Layer',
      agency: 'USDA',
      what: 'Which crop grew on each field, 2008–2025 → your current rotation; pivot circles are detected from it.',
      detail: '30 m, yearly',
      limit: 'Some classes are misread, and fields are idealised circles. Check your own records.',
    },
    {
      name: 'SSURGO soils',
      agency: 'USDA',
      what: 'Texture, organic matter, erodibility and how much water the soil can hold.',
      detail: 'Soil survey map units',
      limit: 'Mapped decades ago; a soil test is better.',
    },
  ];

  const water = ranked?.map((r) => ({
    name: r.strategy.name,
    q: r.strategy.metrics.water_use_mm,
  }));
  const wMax = water ? Math.max(1, ...water.map((w) => w.q.p90)) * 1.05 : 1;
  const pct = (x: number) => (x / wMax) * 100;
  const lead = ranked?.[0];

  return (
    <div
      className="modal-backdrop no-print"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="about-modal-title"
    >
      <div className="modal-card about-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-title">
            <div className="flow-eyebrow">How we know</div>
            <h2 id="about-modal-title" className="about-title">
              What the satellites see, what we compute, and what only you can judge
            </h2>
          </div>
          <button
            ref={closeRef}
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close"
          >
            <IconClose />
          </button>
        </div>

        <div className="modal-body about-body">
          <p className="about-lede">
            Every number in FieldShift comes from open data. Here is where each one comes from, how
            fine-grained it is, and where it can be wrong.
          </p>

          <section aria-labelledby="ab-data">
            <h3 id="ab-data">1 · The data behind your field</h3>
            <div className="about-data-grid">
              {datasets.map((d) => (
                <article key={d.name} className={`about-data${d.pending ? ' pending' : ''}`}>
                  <div className="about-data-head">
                    <h4>{d.name}</h4>
                    <span className={`about-tag ${d.agency.toLowerCase()}`}>{d.agency}</span>
                  </div>
                  <p>{d.what}</p>
                  <p className="about-meta">
                    <strong>Detail:</strong> {d.detail}
                  </p>
                  <p className="about-meta">
                    <strong>Limit:</strong> {d.limit}
                  </p>
                </article>
              ))}
            </div>
            <p className="about-note">
              <strong>Considered, not used:</strong> NASA SMAP soil moisture (9–36 km cells are much
              coarser than one pivot, and the county box had no valid retrievals on the day
              sampled), so crop water stress comes from the daily FAO-56 water balance on POWER
              weather instead. GPM IMERG rainfall was not available to our account in time.
            </p>
          </section>

          <section aria-labelledby="ab-range" className="about-range">
            <div>
              <h3 id="ab-range">2 · Why you see ranges, not one number</h3>
              <p>
                We replay each rotation through every weather year from {w0} to {w1}. A bar spans a
                1-in-10 low year to a 1-in-10 high year; the tick is a typical year. Then we vary
                your priorities slightly, 2,000 times.{' '}
                {lead
                  ? `"Scores highest in ${Math.round(lead.pBest * 100)} %" means ${lead.strategy.name} came first in ${Math.round(lead.pBest * 100)} % of those weather and priority samples.`
                  : '"Scores highest in 58 %" means the rotation came first in 58 % of those samples.'}{' '}
                It shows how sure we can be, not a verdict.
              </p>
            </div>
            {water && water.length > 0 && (
              <figure className="about-figure">
                <figcaption>Irrigation water, {fieldId}, mm per year</figcaption>
                {water.map((w) => (
                  <div className="about-bar-row" key={w.name}>
                    <span className="about-bar-name">{w.name}</span>
                    <span
                      className="card-bar-track"
                      role="img"
                      aria-label={`${w.name}: ${Math.round(w.q.p10)} to ${Math.round(w.q.p90)} mm, typical ${Math.round(w.q.p50)}`}
                    >
                      <span
                        className="card-bar-range"
                        style={{
                          left: `${pct(w.q.p10)}%`,
                          width: `${Math.max(pct(w.q.p90) - pct(w.q.p10), 1.2)}%`,
                        }}
                      />
                      <span className="card-bar-tick" style={{ left: `${pct(w.q.p50)}%` }} />
                    </span>
                    <span className="card-bar-val">
                      {w.q.p10 === w.q.p90
                        ? Math.round(w.q.p50)
                        : `${Math.round(w.q.p10)}–${Math.round(w.q.p90)}`}
                    </span>
                  </div>
                ))}
              </figure>
            )}
          </section>

          <section aria-labelledby="ab-soil">
            <h3 id="ab-soil">3 · How rotations build soil</h3>
            <div className="about-soil-grid">
              {SOIL.map((s) => (
                <div key={s.t} className="about-soil" style={{ borderTopColor: s.c }}>
                  <h4>{s.t}</h4>
                  <p>{s.d}</p>
                </div>
              ))}
            </div>
          </section>

          <section aria-labelledby="ab-you" className="about-judge">
            <h3 id="ab-you">4 · Where your judgment matters most</h3>
            <ul>
              {JUDGE.map((j) => (
                <li key={j}>{j}</li>
              ))}
            </ul>
          </section>

          <section aria-labelledby="ab-scale">
            <h3 id="ab-scale">5 · From one county to any farm</h3>
            <p className="about-meta">The method is the same everywhere. Only the inputs change.</p>
            <div className="about-table-wrap">
              <table className="about-table">
                <thead>
                  <tr>
                    <th>Input</th>
                    <th>Finney County (now)</th>
                    <th>All US counties</th>
                    <th>Worldwide</th>
                  </tr>
                </thead>
                <tbody>
                  {SCALE.map((r) => (
                    <tr key={r[0]}>
                      <th scope="row">{r[0]}</th>
                      <td>{r[1]}</td>
                      <td>{r[2]}</td>
                      <td>{r[3]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <details className="flow-details">
            <summary>Model details</summary>
            <ul className="about-models">
              <li>
                <strong>Water:</strong> FAO-56 Penman-Monteith reference ET × single crop
                coefficient by growth stage, daily soil-water bucket (SSURGO water-holding capacity,
                rain first, irrigation tops up the deficit).
              </li>
              <li>
                <strong>Erosion:</strong> simplified RUSLE (A = R × K × LS × C): rain erosivity from
                POWER, K from SSURGO, LS from SRTM slope, C from crop cover. Water erosion only.
              </li>
              <li>
                <strong>Soil:</strong> simplified, uncalibrated NRCS Soil Conditioning Index
                (residue, tillage, erosion).
              </li>
              <li>
                <strong>Money:</strong> K-State 2027 SW Kansas planning budgets; return over direct
                costs (no land rent or pivot capital).
              </li>
              <li>
                <strong>Ranking:</strong> weighted score of the five measures; weights drawn around
                your sliders (Dirichlet), measures drawn from each p10–p90 range; share of 2,000
                draws in which each rotation comes first.
              </li>
            </ul>
          </details>
        </div>

        <div className="modal-footer">
          <span className="modal-footer-attribution">
            <a
              href="https://www.flaticon.com/free-icons/yield"
              title="yield icons"
              target="_blank"
              rel="noopener noreferrer"
            >
              Yield icons created by Eucalyp - Flaticon
            </a>
          </span>
          <button type="button" className="btn-cta" onClick={onClose}>
            {fieldId ? 'Back to my field' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
}
