import type { FieldCollection } from '../types/contracts';
import { cropCss, cropLabel } from '../lib/colors';

export function CropLegend({ fields, year }: { fields: FieldCollection; year: number }) {
  const crops = [
    ...new Set(fields.features.map((f) => f.properties.crop_history[String(year)])),
  ].filter(Boolean);
  return (
    <ul className="legend">
      {crops.sort().map((c) => (
        <li key={c}>
          <span className="swatch" style={{ background: cropCss(c) }} />
          {cropLabel(c)}
        </li>
      ))}
    </ul>
  );
}
