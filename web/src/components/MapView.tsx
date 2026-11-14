import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { GeoJsonLayer } from '@deck.gl/layers';
import type { FieldCollection, FieldFeature } from '../types/contracts';
import { cropColor } from '../lib/colors';

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
}

export function MapView({ fields, year, selectedId, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const overlay = useRef<MapboxOverlay | null>(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

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
      fitBoundsOptions: { padding: 20 },
    });
    let fellBack = false;
    map.on('error', () => {
      if (!fellBack && !map.isStyleLoaded()) {
        fellBack = true;
        map.setStyle(BLANK);
      }
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    overlay.current = new MapboxOverlay({ interleaved: false, layers: [] });
    map.addControl(overlay.current);
    return () => {
      overlay.current = null;
      map.remove();
    };
  }, [fields.county.bbox]);

  useEffect(() => {
    const key = String(year);
    overlay.current?.setProps({
      layers: [
        new GeoJsonLayer<FieldFeature['properties']>({
          id: 'fields',
          data: fields as unknown as GeoJSON.FeatureCollection,
          pickable: true,
          stroked: true,
          filled: true,
          getFillColor: (f) => [...cropColor(f.properties.crop_history[key]), 210],
          getLineColor: (f) =>
            f.properties.field_id === selectedId ? [20, 20, 20, 255] : [80, 80, 80, 160],
          getLineWidth: (f) => (f.properties.field_id === selectedId ? 3 : 1),
          lineWidthUnits: 'pixels',
          updateTriggers: { getFillColor: key, getLineColor: selectedId, getLineWidth: selectedId },
          onClick: (info) => {
            const id = info.object?.properties?.field_id;
            if (id) onSelectRef.current(id);
          },
        }),
      ],
      getTooltip: ({ object }) =>
        object
          ? `${object.properties.field_id} · ${object.properties.crop_history[key] ?? 'n/a'} (${year})`
          : null,
    });
  }, [fields, year, selectedId]);

  return <div ref={container} className="map" />;
}
