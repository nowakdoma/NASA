import { useMemo } from 'react';
import type { FieldCollection } from '../types/contracts';
import { cropCss, cropLabel } from '../lib/colors';

interface Props {
  fields: FieldCollection;
  year: number;
  highlightCrop?: string | null;
  onHighlightCrop?: (crop: string | null) => void;
}

export function CropLegend({ fields, year, highlightCrop, onHighlightCrop }: Props) {
  const cropStats = useMemo(() => {
    const key = String(year);
    const map = new Map<string, { count: number; area: number }>();

    for (const f of fields.features) {
      const crop = f.properties.crop_history[key];
      if (!crop) continue;
      const current = map.get(crop) ?? { count: 0, area: 0 };
      current.count += 1;
      current.area += f.properties.area_ha;
      map.set(crop, current);
    }

    return Array.from(map.entries())
      .map(([crop, stats]) => ({
        crop,
        count: stats.count,
        areaHa: Math.round(stats.area * 10) / 10,
        areaAc: Math.round(stats.area * 2.47105),
      }))
      .sort((a, b) => b.areaHa - a.areaHa);
  }, [fields, year]);

  return (
    <div className="crop-legend-container">
      <div className="crop-legend-header">
        <span className="crop-legend-title">Crops in {year}</span>
        <span className="crop-legend-sub">Click crop to highlight</span>
      </div>
      <ul className="legend" role="list">
        {cropStats.map(({ crop, count, areaHa, areaAc }) => {
          const isSelected = highlightCrop === crop;
          return (
            <li
              key={crop}
              role="listitem"
              tabIndex={0}
              className={`legend-item${isSelected ? ' active' : ''}`}
              onClick={() => onHighlightCrop?.(isSelected ? null : crop)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onHighlightCrop?.(isSelected ? null : crop);
                }
              }}
              title={`${cropLabel(crop)}: ${count} field${count > 1 ? 's' : ''}, ${areaHa} ha (${areaAc} ac)`}
            >
              <span className="swatch" style={{ background: cropCss(crop) }} />
              <span className="crop-name">{cropLabel(crop)}</span>
              <span className="crop-stat">
                {count} <span className="stat-unit">({areaHa} ha)</span>
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
