// Client-side MCDA mirroring engine/mcda.py: Dirichlet-sampled weights around the slider
// values + split-normal draws from each metric's p10/p50/p90, then count how often each
// strategy has the highest weighted score ("P(best)"). Decision support, not advice.
import {
  METRIC_KEYS,
  type MetricKey,
  type MetricMeta,
  type PriorityKey,
  type Strategy,
} from '../types/contracts';

export type Priorities = Record<PriorityKey, number>;

export const PRIORITY_TO_METRIC: Record<PriorityKey, MetricKey> = {
  water: 'water_use_mm',
  income: 'income_usd_ha',
  soil: 'soil_index',
  erosion: 'erosion_t_ha',
  labour: 'labour_index',
};

export interface RankedStrategy {
  strategy: Strategy;
  medianScore: number; // weighted score at p50 with exact slider weights, 0..1
  pBest: number; // 0..1, share of samples where this rotation is best AND within the water limit
  /** Share of samples whose drawn irrigation water stays within the limit (1 without a limit). */
  pWithinLimit: number;
  /** Normalised 0..1 score per metric at p50 (1 = best of the four), for "why it wins". */
  p50Scores: Record<MetricKey, number>;
}

export interface Ranking {
  ranked: RankedStrategy[];
  /** Share of samples in which none of the four rotations fits the water limit. */
  pNoneFits: number;
  weights: Record<MetricKey, number>;
}

/** A rotation may exceed the farmer's limit by this fraction before it counts as over. */
export const WATER_TOLERANCE = 0.05;

const Z90 = 1.2815515655446004;

// Seeded PRNG so the ranking does not flicker between renders.
function mulberry32(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function normal(rand: () => number): number {
  const u = Math.max(rand(), 1e-12);
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rand());
}

// Marsaglia–Tsang gamma sampler (shape a > 0, scale 1).
function gamma(a: number, rand: () => number): number {
  if (a < 1) return gamma(a + 1, rand) * Math.pow(rand(), 1 / a);
  const d = a - 1 / 3;
  const c = 1 / Math.sqrt(9 * d);
  for (;;) {
    let x: number, v: number;
    do {
      x = normal(rand);
      v = 1 + c * x;
    } while (v <= 0);
    v = v * v * v;
    const u = rand();
    if (u < 1 - 0.0331 * x ** 4 || Math.log(u) < 0.5 * x * x + d * (1 - v + Math.log(v)))
      return d * v;
  }
}

function dirichlet(alpha: number[], rand: () => number): number[] {
  const g = alpha.map((a) => gamma(a, rand));
  const s = g.reduce((x, y) => x + y, 0);
  return g.map((x) => x / s);
}

function weightsFromPriorities(p: Priorities): number[] {
  const byMetric = METRIC_KEYS.map(
    (m) =>
      p[
        (Object.keys(PRIORITY_TO_METRIC) as PriorityKey[]).find((k) => PRIORITY_TO_METRIC[k] === m)!
      ],
  );
  const s = byMetric.reduce((a, b) => a + b, 0);
  return s > 0 ? byMetric.map((w) => w / s) : byMetric.map(() => 1 / byMetric.length);
}

/** Score matrix rows = strategies, cols = METRIC_KEYS; returns normalised 0..1 (1 = best). */
function normalise(values: number[][], meta: Record<MetricKey, MetricMeta>): number[][] {
  const out = values.map((r) => r.slice());
  METRIC_KEYS.forEach((m, j) => {
    const col = values.map((r) => r[j]);
    const lo = Math.min(...col);
    const hi = Math.max(...col);
    values.forEach((r, i) => {
      const x = hi > lo ? (r[j] - lo) / (hi - lo) : 0.5;
      out[i][j] = meta[m].better === 'lower' ? 1 - x : x;
    });
  });
  return out;
}

const weighted = (row: number[], w: number[]) => row.reduce((s, x, j) => s + x * w[j], 0);

/**
 * P(best) under uncertain weather and priorities. With `waterLimitMm`, a rotation whose drawn
 * irrigation water exceeds the limit (+ WATER_TOLERANCE) cannot win that sample — the farmer
 * cannot pump it — and samples where nothing fits are counted in `pNoneFits` instead.
 */
export function rankWithLimit(
  strategies: Strategy[],
  meta: Record<MetricKey, MetricMeta>,
  priorities: Priorities,
  waterLimitMm: number | null,
  { samples = 2000, concentration = 20, seed = 42 } = {},
): Ranking {
  const w = weightsFromPriorities(priorities);
  const weights = Object.fromEntries(METRIC_KEYS.map((m, j) => [m, w[j]])) as Record<
    MetricKey,
    number
  >;
  if (strategies.length === 0) return { ranked: [], pNoneFits: 0, weights };
  const p50 = strategies.map((s) => METRIC_KEYS.map((m) => s.metrics[m].p50));
  const p50Norm = normalise(p50, meta);
  const median = p50Norm.map((row) => weighted(row, w));
  const cap = waterLimitMm === null ? Infinity : waterLimitMm * (1 + WATER_TOLERANCE);
  const iWater = METRIC_KEYS.indexOf('water_use_mm');

  const rand = mulberry32(seed);
  const alpha = w.map((x) => Math.max(concentration * x, 1e-3));
  const wins = new Array(strategies.length).fill(0);
  const within = new Array(strategies.length).fill(0);
  let noneFits = 0;
  for (let n = 0; n < samples; n++) {
    const draw = strategies.map((s) =>
      METRIC_KEYS.map((m) => {
        const { p10, p50: mid, p90 } = s.metrics[m];
        const z = normal(rand);
        return mid + (z < 0 ? (z * (mid - p10)) / Z90 : (z * (p90 - mid)) / Z90);
      }),
    );
    const wn = dirichlet(alpha, rand);
    const scores = normalise(draw, meta).map((row) => weighted(row, wn));
    let best = -1;
    scores.forEach((sc, i) => {
      if (draw[i][iWater] > cap) return;
      within[i]++;
      if (best < 0 || sc > scores[best]) best = i;
    });
    if (best < 0) noneFits++;
    else wins[best]++;
  }
  const ranked = strategies
    .map((strategy, i) => ({
      strategy,
      medianScore: median[i],
      pBest: wins[i] / samples,
      pWithinLimit: within[i] / samples,
      p50Scores: Object.fromEntries(METRIC_KEYS.map((m, j) => [m, p50Norm[i][j]])) as Record<
        MetricKey,
        number
      >,
    }))
    .sort((a, b) => b.pBest - a.pBest || b.medianScore - a.medianScore);
  return { ranked, pNoneFits: noneFits / samples, weights };
}

/** Back-compatible: no water limit (mirrors engine/mcda.py rank_strategies). */
export function rankStrategies(
  strategies: Strategy[],
  meta: Record<MetricKey, MetricMeta>,
  priorities: Priorities,
  opts: { samples?: number; concentration?: number; seed?: number } = {},
): RankedStrategy[] {
  return rankWithLimit(strategies, meta, priorities, null, opts).ranked;
}
