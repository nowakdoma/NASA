// US display units. The engine computes in metric (mm, t/ha, USD/ha); the screen and the
// printout show what a Kansas farmer reads on a meter, a budget and a soil-loss sheet.
import type { MetricKey } from '../types/contracts';
import { MM_PER_IN } from './flow';

export const AC_PER_HA = 2.47105;
const SHORT_TON_PER_T = 1.10231;

interface UsUnit {
  unit: string;
  /** Metric engine value → US display value (linear, so ranges and deltas convert too). */
  f: (x: number) => number;
  fmt: (x: number) => string;
  /** Extra qualifier for the label, shown where space allows. */
  note?: string;
}

const signed = (s: string, x: number) => (x < 0 ? `−${s}` : s);

export const US: Record<MetricKey, UsUnit> = {
  water_use_mm: {
    unit: 'in/yr',
    f: (x) => x / MM_PER_IN,
    fmt: (x) => (Math.abs(x) < 10 && x !== 0 ? x.toFixed(1) : String(Math.round(x))),
  },
  income_usd_ha: {
    unit: '$/ac/yr',
    f: (x) => x / AC_PER_HA,
    fmt: (x) => signed(`$${Math.abs(Math.round(x))}`, x),
    note: 'before land rent & pivot/well costs',
  },
  erosion_t_ha: {
    unit: 'tons/ac/yr',
    f: (x) => (x * SHORT_TON_PER_T) / AC_PER_HA,
    fmt: (x) => (Math.abs(x) >= 10 ? x.toFixed(0) : Math.abs(x) >= 1 ? x.toFixed(1) : x.toFixed(2)),
  },
  soil_index: { unit: 'score −1 to 1', f: (x) => x, fmt: (x) => x.toFixed(2) },
  labour_index: { unit: 'score 0 to 1', f: (x) => x, fmt: (x) => x.toFixed(2) },
};

/** Convert a metric engine value and format it in US units (no unit suffix). */
export const usVal = (m: MetricKey, x: number) => US[m].fmt(US[m].f(x));

/** "−$12,300" style whole-field dollars. */
export const fieldDollars = (usdPerHa: number, areaHa: number) => {
  const v = Math.round((usdPerHa * areaHa) / 100) * 100;
  return signed(`$${Math.abs(v).toLocaleString('en-US')}`, v);
};

export const acres = (ha: number) => Math.round(ha * AC_PER_HA);

/** Footnote for print: how to get back to the engine's metric numbers. */
export const METRIC_FOOTNOTE =
  'Model works in metric; shown here in US units. 1 in = 25.4 mm · $1/ac = $2.47/ha · 1 ton/ac = 2.24 t/ha.';
