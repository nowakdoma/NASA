import { useMemo } from 'react';
import type { FieldFeature } from '../types/contracts';
import { bareHeadline, bareSummary } from '../lib/bare';

/** One plain-language finding from MODIS bare-soil periods: recent years vs the first years. */
export function FieldHeadline({ field }: { field: FieldFeature }) {
  const p = field.properties;
  const summary = useMemo(() => bareSummary(field), [field]);

  if (!summary) {
    return (
      <p className="field-headline-sub">
        No bare-soil periods detected by MODIS for this field. Check the timeline below.
      </p>
    );
  }
  const h = bareHeadline(summary);
  return (
    <div className="field-headline">
      <h2>{h.title}</h2>
      <p className="field-headline-sub">
        {h.compare} Seen by MODIS NDVI (16-day, 250 m). Bare {p.soil.texture} on a{' '}
        {p.soil.slope_pct.toFixed(1)} % slope is the most erodible state for this soil.
      </p>
    </div>
  );
}
