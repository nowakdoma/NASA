import { useEffect, useMemo, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { GeoJsonLayer } from '@deck.gl/layers';
import type { FieldCollection, FieldFeature } from '../types/contracts';
import { cropColor, cropLabel } from '../lib/colors';

// Free vector basemap; if it fails to load (offline demo) we fall back to a plain background.
const BASEMAP = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';
const BLANK: maplibregl.StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#eef0ea' } }],
};

interface Props {
  fields: FieldCollection;
  year: number;
  selectedId: string | null;
  onSelect: (fieldId: string) => void;
  highlightCrop?: string | null;
}

export function MapView({ fields, year, selectedId, onSelect, highlightCrop }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const overlay = useRef<MapboxOverlay | null>(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  // County boundary polygon from bbox
  const countyGeoJson = useMemo<GeoJSON.FeatureCollection>(() => {
    const [minLon, minLat, maxLon, maxLat] = fields.county.bbox;
    return {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [
              [
                [minLon, minLat],
                [maxLon, minLat],
                [maxLon, maxLat],
                [minLon, maxLat],
                [minLon, minLat],
              ],
            ],
          },
          properties: {
            name: `${fields.county.name}, ${fields.county.state}`,
            fips: fields.county.fips,
          },
        },
      ],
    };
  }, [fields.county]);

  useEffect(() => {
    if (!container.current) return;
    const [minLon, minLat, maxLon, maxLat] = fields.county.bbox;
    const map = new maplibregl.Map({
      container: container.current,
      style: BASEMAP,
      bounds: [
        [minLon, minLat],
        [maxLon, maxLat],
      ],
      fitBoundsOptions: { padding: 30 },
    });
    let fellBack = false;
    map.on('error', () => {
      if (!fellBack && !map.isStyleLoaded()) {
        fellBack = true;
        map.setStyle(BLANK);
      }
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    map.addControl(new maplibregl.ScaleControl({ unit: 'imperial' }), 'bottom-left');

    overlay.current = new MapboxOverlay({ interleaved: false, layers: [] });
    map.addControl(overlay.current);
    return () => {
      overlay.current = null;
      map.remove();
    };
  }, [fields.county.bbox]);

  useEffect(() => {
    const key = String(year);

    const layers = [
      // County boundary outline
      new GeoJsonLayer({
        id: 'county-boundary',
        data: countyGeoJson,
        pickable: false,
        stroked: true,
        filled: true,
        getFillColor: [80, 120, 80, 8],
        getLineColor: [50, 75, 55, 170],
        getLineWidth: 2,
        lineWidthUnits: 'pixels',
      }),
      // Irrigated & dryland crop fields
      new GeoJsonLayer<FieldFeature['properties']>({
        id: 'fields',
        data: fields as unknown as GeoJSON.FeatureCollection,
        pickable: true,
        autoHighlight: true,
        highlightColor: [255, 255, 255, 90],
        stroked: true,
        filled: true,
        getFillColor: (f) => {
          const crop = f.properties.crop_history[key];
          const rgb = cropColor(crop);
          // If a crop is highlighted in legend, dim other crops slightly
          const alpha = highlightCrop && crop !== highlightCrop ? 90 : 215;
          return [...rgb, alpha];
        },
        getLineColor: (f) =>
          f.properties.field_id === selectedId ? [15, 23, 42, 255] : [70, 80, 70, 180],
        getLineWidth: (f) => (f.properties.field_id === selectedId ? 3.5 : 1.5),
        lineWidthUnits: 'pixels',
        updateTriggers: {
          getFillColor: [key, highlightCrop],
          getLineColor: selectedId,
          getLineWidth: selectedId,
        },
        onClick: (info) => {
          const id = info.object?.properties?.field_id;
          if (id) onSelectRef.current(id);
        },
      }),
    ];

    overlay.current?.setProps({
      layers,
      getTooltip: ({ object }) => {
        if (!object) return null;
        const p = object.properties as FieldFeature['properties'];
        const crop = p.crop_history[key];
        const acres = (p.area_ha * 2.47105).toFixed(0);
        const stress = p.stress_index_by_year?.[key];
        const stressText =
          stress !== undefined
            ? `${stress.toFixed(2)} (${stress > 0.6 ? 'High' : stress > 0.3 ? 'Moderate' : 'Low'})`
            : 'n/a';
        const irrig =
          p.irrigation_type === 'center_pivot'
            ? 'Center Pivot'
            : p.irrigated
              ? 'Irrigated'
              : 'Dryland';

        return {
          html: `
            <div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; line-height: 1.45; min-width: 180px;">
              <div style="font-size: 13px; font-weight: 700; color: #f8fafc; border-bottom: 1px solid #334155; padding-bottom: 4px; margin-bottom: 6px;">
                ${p.field_id} ${p.name ? `<span style="font-weight: 400; color: #94a3b8; font-size: 11px;"> · ${p.name}</span>` : ''}
              </div>
              <div style="display: grid; grid-template-columns: auto 1fr; gap: 2px 8px; margin-bottom: 4px;">
                <span style="color: #94a3b8;">Crop (${year}):</span>
                <strong style="color: #f1f5f9;">${cropLabel(crop ?? 'unknown')}</strong>
                <span style="color: #94a3b8;">Acreage:</span>
                <span style="color: #f1f5f9;">${p.area_ha} ha (${acres} ac)</span>
                <span style="color: #94a3b8;">System:</span>
                <span style="color: #f1f5f9;">${irrig}</span>
                <span style="color: #94a3b8;">Soil:</span>
                <span style="color: #f1f5f9;">${p.soil.texture} (${p.soil.om_pct}% OM)</span>
                <span style="color: #94a3b8;">Stress idx:</span>
                <span style="color: ${stress && stress > 0.6 ? '#f87171' : stress && stress > 0.3 ? '#fbbf24' : '#4ade80'};">${stressText}</span>
              </div>
              <div style="font-size: 10px; color: #cbd5e1; background: #334155; padding: 2px 6px; border-radius: 3px; text-align: center; margin-top: 4px;">
                Click to inspect passport & rotations
              </div>
            </div>
          `,
          style: {
            backgroundColor: '#0f172a',
            color: '#f8fafc',
            borderRadius: '6px',
            padding: '8px 10px',
            boxShadow: '0 4px 14px rgba(0,0,0,0.35)',
            pointerEvents: 'none',
          },
        };
      },
    });
  }, [fields, year, selectedId, highlightCrop, countyGeoJson]);

  return (
    <div className="map-wrapper">
      <div ref={container} className="map" />
      <div className="county-badge">
        <strong>
          {fields.county.name}, {fields.county.state}
        </strong>{' '}
        (FIPS {fields.county.fips})<span className="county-sub"> · County Boundary</span>
      </div>
    </div>
  );
}
