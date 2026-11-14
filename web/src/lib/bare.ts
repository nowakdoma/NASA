// Bare-soil months per year from MODIS bare periods (shared by screen step 1 and the printout).
import type { FieldFeature } from '../types/contracts';

const DAY = 86_400_000;
export const DAYS_PER_MONTH = 30.4;
export const spanDays = (a: string, b: string) =>
  Math.max(0, (Date.parse(b) - Date.parse(a)) / DAY + 1);

export interface BareSummary {
  years: number[];
  daysByYear: Map<number, number>;
  early: number[];
  recent: number[];
  earlyMonths: number;
  recentMonths: number;
}

export function bareSummary(field: FieldFeature): BareSummary | null {
  const p = field.properties;
  const years = Object.keys(p.crop_history)
    .map(Number)
    .sort((a, b) => a - b);
  const daysByYear = new Map<number, number>(years.map((y) => [y, 0]));
  for (const b of p.season_calendar.bare_periods)
    if (daysByYear.has(b.year))
      daysByYear.set(b.year, (daysByYear.get(b.year) ?? 0) + spanDays(b.start, b.end));
  if (years.length < 6 || p.season_calendar.bare_periods.length === 0) return null;
  const mean = (ys: number[]) =>
    ys.reduce((s, y) => s + (daysByYear.get(y) ?? 0), 0) / ys.length / DAYS_PER_MONTH;
  const early = years.slice(0, 5);
  const recent = years.slice(-5);
  return {
    years,
    daysByYear,
    early,
    recent,
    earlyMonths: mean(early),
    recentMonths: mean(recent),
  };
}

export const roundMonths = (x: number) => (x < 1 ? 'under 1' : x.toFixed(0));

/** One plain sentence pair, e.g. "Bare soil about 6 months a year in 2021–2025" + comparison. */
export function bareHeadline(s: BareSummary): { title: string; compare: string } {
  const r = s.recent;
  const e = s.early;
  const diff = s.recentMonths - s.earlyMonths;
  return {
    title:
      s.recentMonths < 1
        ? `Bare soil under 1 month a year in ${r[0]}–${r[r.length - 1]}`
        : `Bare soil about ${roundMonths(s.recentMonths)} month${s.recentMonths >= 1.5 ? 's' : ''} a year in ${r[0]}–${r[r.length - 1]}`,
    compare:
      Math.abs(diff) >= 1
        ? `${diff > 0 ? 'Up' : 'Down'} from about ${roundMonths(s.earlyMonths)} in ${e[0]}–${e[e.length - 1]}.`
        : `Similar to ${e[0]}–${e[e.length - 1]}.`,
  };
}
