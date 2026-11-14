// Plain-language "why does this rotation come out on top?" from the ranking's own numbers.
import { METRIC_KEYS, type MetricKey } from '../types/contracts';
import type { Ranking } from './ranking';
import { MM_PER_IN } from './flow';

const STRENGTH: Record<MetricKey, string> = {
  water_use_mm: 'less water',
  income_usd_ha: 'higher net return',
  soil_index: 'a better soil score',
  erosion_t_ha: 'less erosion',
  labour_index: 'less work',
};

export interface LeadExplanation {
  /** e.g. "Wins mainly on a better soil score and less work." */
  why: string | null;
  /** e.g. ["Alfalfa–corn needs about 18 in in a typical year, over your 14 in."] */
  excluded: string[];
  /** Shown instead of a winner when most samples have nothing within the limit. */
  noneFits: string | null;
  close: boolean;
}

export function explainLead(r: Ranking, waterLimitIn: number | null): LeadExplanation {
  const [lead, second] = r.ranked;
  const out: LeadExplanation = { why: null, excluded: [], noneFits: null, close: false };
  if (!lead) return out;

  if (waterLimitIn !== null) {
    out.excluded = r.ranked
      .filter((x) => x.pWithinLimit < 0.5)
      .map(
        (x) =>
          `${x.strategy.name} needs about ${Math.round(x.strategy.metrics.water_use_mm.p50 / MM_PER_IN)} in of irrigation in a typical year${waterLimitIn === 0 ? '; you chose no irrigation.' : `, over your ${waterLimitIn} in.`}`,
      );
    if (r.pNoneFits >= 0.5)
      out.noneFits = `In ${outOfTen(r.pNoneFits)} none of the four rotations stays within ${limitPhrase(waterLimitIn)}. Check your allocation, or ask your adviser about lower-water options not listed here.`;
  }

  const others = r.ranked.slice(1);
  if (others.length) {
    const gains = METRIC_KEYS.map((m) => {
      const avg = others.reduce((s, o) => s + o.p50Scores[m], 0) / others.length;
      return { m, g: r.weights[m] * (lead.p50Scores[m] - avg) };
    })
      .filter((x) => x.g > 0.01)
      .sort((a, b) => b.g - a.g)
      .slice(0, 2)
      .map((x) => STRENGTH[x.m]);
    if (gains.length) out.why = `Wins mainly on ${gains.join(' and ')}.`;
  }
  out.close = !!second && lead.pBest - second.pBest < 0.1;
  return out;
}

/** "about 5 of every 10 runs" — farmer-readable share. */
export const outOfTen = (p: number) => {
  if (p >= 0.995) return 'every run';
  if (p >= 0.95) return 'almost every run';
  const n = Math.round(p * 10);
  return n === 0 ? 'fewer than 1 in 10 runs' : `about ${n} of every 10 runs`;
};

/** Card badge: "6", "<1", "10". */
export const tenths = (p: number) => (p > 0 && p < 0.05 ? '<1' : String(Math.round(p * 10)));

/** "14 in" or "no irrigation" for the dryland choice. */
export const limitPhrase = (limitIn: number) => (limitIn === 0 ? 'no irrigation' : `${limitIn} in`);
