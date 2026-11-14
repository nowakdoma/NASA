import { useMemo } from 'react';
import type { FieldFeature } from '../types/contracts';
import { bareHeadline, bareSummary } from '../lib/bare';

/** One plain-language finding from MODIS no-green-cover periods: recent years vs the first years. */
export function FieldHeadline({ field }: { field: FieldFeature }) {
  const p = field.properties;
  const summary = useMemo(() => bareSummary(field), [field]);

  if (!summary) {
    return (
      <p className="field-headline-sub">
        NASA MODIS saw green cover on this field all year round. Check the timeline below.
      </p>
    );
  }
  const h = bareHeadline(summary);
  return (
    <div className="field-headline">
      <h2>{h.title}</h2>
      <p className="field-headline-sub">
        {h.compare} Seen from orbit by NASA MODIS every 16 days. This also counts dormant alfalfa
        and standing stalks, so the soil may not be fully bare. Uncovered {p.soil.texture} on a{' '}
        {p.soil.slope_pct.toFixed(1)} % slope is when this soil erodes most easily.
      </p>
    </div>
  );
}
