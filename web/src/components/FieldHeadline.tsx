import { useMemo } from 'react';
import type { FieldFeature } from '../types/contracts';

const DAY = 86_400_000;
const months = (days: number) => days / 30.4;

/** One plain-language finding from MODIS bare-soil periods: recent years vs the first years. */
export function FieldHeadline({ field }: { field: FieldFeature }) {
  const p = field.properties;
  const summary = useMemo(() => {
    const years = Object.keys(p.crop_history)
      .map(Number)
      .sort((a, b) => a - b);
    if (years.length < 6) return null;
    const bare = new Map<number, number>(years.map((y) => [y, 0]));
    for (const b of p.season_calendar.bare_periods) {
      if (!bare.has(b.year)) continue;
      const d = (Date.parse(b.end) - Date.parse(b.start)) / DAY + 1;
      bare.set(b.year, (bare.get(b.year) ?? 0) + Math.max(0, d));
    }
    const mean = (ys: number[]) =>
      months(ys.reduce((s, y) => s + (bare.get(y) ?? 0), 0) / ys.length);
    const early = years.slice(0, 5);
    const recent = years.slice(-5);
    return { early, recent, earlyM: mean(early), recentM: mean(recent) };
  }, [p]);

  if (!summary || p.season_calendar.bare_periods.length === 0) {
    return (
      <p className="field-headline-sub">
        No bare-soil periods detected by MODIS for this field. Check the timeline below.
      </p>
    );
  }
  const { early, recent, earlyM, recentM } = summary;
  const r = (x: number) => (x < 1 ? 'under 1' : x.toFixed(0));
  const diff = recentM - earlyM;
  return (
    <div className="field-headline">
      <h2>
        Bare soil about {r(recentM)} month{recentM >= 1.5 ? 's' : ''} a year in {recent[0]}–
        {recent[recent.length - 1]}
      </h2>
      <p className="field-headline-sub">
        {Math.abs(diff) >= 1
          ? `${diff > 0 ? 'Up' : 'Down'} from about ${r(earlyM)} in ${early[0]}–${early[early.length - 1]}. `
          : `Similar to ${early[0]}–${early[early.length - 1]}. `}
        Seen by MODIS NDVI (16-day, 250 m). Bare {p.soil.texture} on a {p.soil.slope_pct.toFixed(1)}{' '}
        % slope is the most erodible state for this soil.
      </p>
    </div>
  );
}
