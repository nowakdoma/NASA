import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { fieldLabel } from '../lib/units';
import maplibregl from 'maplibre-gl';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { GeoJsonLayer, ScatterplotLayer } from '@deck.gl/layers';
import type { FieldCollection, FieldFeature } from '../types/contracts';
import { cropColor, cropLabel } from '../lib/colors';
import { IconPin } from './Icons';

// Free vector basemap; if it fails to load (offline demo) we fall back to a plain background.
const BASEMAP = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';
// Satellite view: USGS National Map imagery with roads and place names (US public domain, no
// key). Lets a farmer recognise their own pivot by the roads and farmstead around it.
const SATELLITE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    usgs: {
      type: 'raster',
      tiles: [
        'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      maxzoom: 16,
      attribution: 'Imagery: USGS The National Map',
    },
  },
  layers: [{ id: 'usgs', type: 'raster', source: 'usgs' }],
};
type Base = 'map' | 'satellite';
const BASE_KEY = 'fieldshift.basemap';
const readBase = (): Base => {
  try {
    return localStorage.getItem(BASE_KEY) === 'satellite' ? 'satellite' : 'map';
  } catch {
    return 'map';
  }
};

const BLANK: maplibregl.StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#eef0ea' } }],
};

// Each field also gets a marker drawn at its real size (radius from area) but never smaller
// than MARKER_MIN_PX, so zoomed out a ~850 m pivot stays clickable (Fitts: the start screen
// asks users to click their field) and zoomed in the marker matches the field's footprint.
// Past MARKER_MAX_ZOOM the field is far larger than the minimum and the polygon takes over.
const MARKER_MIN_PX = 7;
const MARKER_MAX_ZOOM = 12;

interface Marker {
  position: [number, number];
  properties: FieldFeature['properties'];
}

/** Mean of the outer ring; good enough for compact pivot polygons. */
function centroid(f: FieldFeature): [number, number] {
  const c = f.geometry.coordinates as number[][][] | number[][][][];
  const ring = (
    f.geometry.type === 'MultiPolygon' ? (c as number[][][][])[0][0] : (c as number[][][])[0]
  ) as number[][];
  const n = ring.length - 1 || 1;
  let x = 0;
  let y = 0;
  for (let i = 0; i < n; i++) {
    x += ring[i][0];
    y += ring[i][1];
  }
  return [x / n, y / n];
}

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
  const mapObj = useRef<maplibregl.Map | null>(null);
  const [base, setBase] = useState<Base>(readBase);
  const baseRef = useRef(base);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const [isMapLoading, setIsMapLoading] = useState(true);
  const [zoom, setZoom] = useState(0);
  // Wheel zoom (and one-finger pan on touch) stay off until the map is clicked/tapped, so
  // scrolling the page never gets trapped by the map.
  const [armed, setArmed] = useState(false);
  const [hint, setHint] = useState(false);
  const markers = useMemo<Marker[]>(
    () => fields.features.map((f) => ({ position: centroid(f), properties: f.properties })),
    [fields.features],
  );

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
      style: baseRef.current === 'satellite' ? SATELLITE : BASEMAP,
      bounds: [
        [minLon, minLat],
        [maxLon, maxLat],
      ],
      fitBoundsOptions: { padding: 30 },
    });

    // Only swap to the blank style if the basemap never loaded (offline demo). Tile errors
    // after load (e.g. fast zooming) must not wipe the basemap.
    let fellBack = false;
    let loaded = false;
    map.on('error', () => {
      if (!fellBack && !loaded) {
        fellBack = true;
        map.setStyle(BLANK);
      }
      setIsMapLoading(false);
    });

    map.on('load', () => {
      loaded = true;
      setIsMapLoading(false);
      setZoom(map.getZoom());
    });
    mapObj.current = map;
    let raf = 0;
    map.on('zoom', () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => setZoom(map.getZoom()));
    });

    // Fallback timeout to ensure loader smoothly dismisses even if tile network is slow
    const timer = setTimeout(() => {
      setIsMapLoading(false);
    }, 1800);

    const coarse = window.matchMedia('(pointer: coarse)').matches;
    map.scrollZoom.disable();
    if (coarse) map.dragPan.disable();
    let hintTimer = 0;
    const arm = () => {
      map.scrollZoom.enable();
      map.dragPan.enable();
      setArmed(true);
      setHint(false);
    };
    const disarm = () => {
      if (coarse) return;
      map.scrollZoom.disable();
      setArmed(false);
    };
    const onWheel = () => {
      if (map.scrollZoom.isEnabled()) return;
      setHint(true);
      clearTimeout(hintTimer);
      hintTimer = window.setTimeout(() => setHint(false), 1800);
    };
    map.on('click', arm);
    const el = map.getContainer();
    el.addEventListener('mouseleave', disarm);
    el.addEventListener('wheel', onWheel, { passive: true });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    map.addControl(new maplibregl.ScaleControl({ unit: 'imperial' }), 'bottom-left');

    overlay.current = new MapboxOverlay({ interleaved: false, layers: [], pickingRadius: 6 });
    map.addControl(overlay.current);

    return () => {
      clearTimeout(timer);
      clearTimeout(hintTimer);
      el.removeEventListener('mouseleave', disarm);
      el.removeEventListener('wheel', onWheel);
      cancelAnimationFrame(raf);
      overlay.current = null;
      mapObj.current = null;
      map.remove();
    };
  }, [fields.county.bbox]);

  // Basemap toggle (remembered per browser).
  useEffect(() => {
    if (baseRef.current === base) return;
    baseRef.current = base;
    mapObj.current?.setStyle(base === 'satellite' ? SATELLITE : BASEMAP);
    try {
      localStorage.setItem(BASE_KEY, base);
    } catch {
      /* private mode: toggle still works for this visit */
    }
  }, [base]);

  // Zoom to the chosen field so the farmer can check it is really theirs.
  const selectedBounds = useMemo(() => {
    const f = fields.features.find((x) => x.properties.field_id === selectedId);
    if (!f) return null;
    const c = f.geometry.coordinates;
    const ring =
      f.geometry.type === 'Polygon' ? (c as number[][][])[0] : (c as number[][][][])[0][0];
    const xs = ring.map((c) => c[0]);
    const ys = ring.map((c) => c[1]);
    return [
      [Math.min(...xs), Math.min(...ys)],
      [Math.max(...xs), Math.max(...ys)],
    ] as [[number, number], [number, number]];
  }, [fields.features, selectedId]);
  const zoomToField = useCallback(
    (duration = 700) => {
      if (selectedBounds)
        mapObj.current?.fitBounds(selectedBounds, { padding: 60, maxZoom: 14, duration });
    },
    [selectedBounds],
  );
  useEffect(() => zoomToField(), [zoomToField]);
  const showCounty = () => {
    const [a, b, c, d] = fields.county.bbox;
    mapObj.current?.fitBounds(
      [
        [a, b],
        [c, d],
      ],
      { padding: 30, duration: 700 },
    );
  };

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
        getFillColor: [247, 245, 239, 0],
        getLineColor: [28, 42, 57, 150],
        getLineWidth: 2,
        lineWidthUnits: 'pixels',
      }),
      // Irrigated & dryland crop fields
      new GeoJsonLayer<FieldFeature['properties']>({
        id: 'fields',
        data: fields as unknown as GeoJSON.FeatureCollection,
        pickable: true,
        autoHighlight: true,
        highlightColor: [255, 255, 255, 95],
        stroked: true,
        filled: true,
        getFillColor: (f) => {
          const crop = f.properties.crop_history[key];
          const rgb = cropColor(crop);
          // If a crop is highlighted in legend, dim other crops slightly
          // On satellite the fill is see-through so the farmer can check what is under it.
          const full = base === 'satellite' ? 90 : 220;
          const alpha = highlightCrop && crop !== highlightCrop ? 60 : full;
          return [...rgb, alpha];
        },
        getLineColor: (f) =>
          f.properties.field_id === selectedId ? [28, 42, 57, 255] : [28, 42, 57, 110],
        getLineWidth: (f) => (f.properties.field_id === selectedId ? 4 : 1),
        lineWidthUnits: 'pixels',
        updateTriggers: {
          getFillColor: [key, highlightCrop, base],
          getLineColor: selectedId,
          getLineWidth: selectedId,
        },
        onClick: (info) => {
          const id = info.object?.properties?.field_id;
          if (id) onSelectRef.current(id);
        },
      }),
      new ScatterplotLayer<Marker>({
        id: 'field-markers',
        data: markers,
        visible: zoom < MARKER_MAX_ZOOM,
        pickable: true,
        autoHighlight: true,
        highlightColor: [255, 255, 255, 110],
        stroked: true,
        filled: true,
        radiusUnits: 'meters',
        radiusMinPixels: MARKER_MIN_PX,
        lineWidthUnits: 'pixels',
        getPosition: (m) => m.position,
        getRadius: (m) => Math.sqrt((m.properties.area_ha * 10_000) / Math.PI),
        getFillColor: (m) => {
          const crop = m.properties.crop_history[key];
          return [...cropColor(crop), highlightCrop && crop !== highlightCrop ? 75 : 235];
        },
        getLineColor: [28, 42, 57, 230],
        getLineWidth: (m) => (m.properties.field_id === selectedId ? 3 : 1.25),
        updateTriggers: {
          getFillColor: [key, highlightCrop],
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
            <div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; line-height: 1.45; min-width: 190px;">
              <div style="font-size: 13px; font-weight: 700; color: #fdfdfd; border-bottom: 1px solid #38463c; padding-bottom: 4px; margin-bottom: 6px;">
                ${fieldLabel(p)} ${p.name ? `<span style="font-weight: 400; color: #b4c2b8; font-size: 11px;"> · ${p.name}</span>` : ''}
              </div>
              <div style="display: grid; grid-template-columns: auto 1fr; gap: 2px 8px; margin-bottom: 4px;">
                <span style="color: #9cb0a2;">Crop (${year}):</span>
                <strong style="color: #f7faf7;">${cropLabel(crop ?? 'unknown')}</strong>
                <span style="color: #9cb0a2;">Acreage:</span>
                <span style="color: #f7faf7;">${p.area_ha} ha (${acres} ac)</span>
                <span style="color: #9cb0a2;">System:</span>
                <span style="color: #f7faf7;">${irrig}</span>
                <span style="color: #9cb0a2;">Soil:</span>
                <span style="color: #f7faf7;">${p.soil.texture} (${p.soil.om_pct}% OM)</span>
                <span style="color: #9cb0a2;">Stress idx:</span>
                <span style="color: ${stress && stress > 0.6 ? '#f87171' : stress && stress > 0.3 ? '#facc15' : '#4ade80'};">${stressText}</span>
              </div>
              <div style="font-size: 10px; color: #cbd7cf; background: #2a382e; padding: 2px 6px; border-radius: 3px; text-align: center; margin-top: 5px;">
                Click field to inspect passport
              </div>
            </div>
          `,
          style: {
            backgroundColor: '#19241d',
            color: '#f8fafc',
            borderRadius: '6px',
            padding: '8px 10px',
            boxShadow: '0 6px 18px rgba(0,0,0,0.3)',
            border: '1px solid #334538',
            pointerEvents: 'none',
          },
        };
      },
    });
  }, [fields, year, selectedId, highlightCrop, countyGeoJson, markers, zoom, base]);

  return (
    <div className="map-wrapper">
      {/* Map Loader Overlay */}
      {isMapLoading && (
        <div className="map-loader-overlay">
          <div className="map-loader-card">
            <div className="map-spinner" />
            <div className="map-loader-text">Loading Finney County satellite layers…</div>
            <div className="map-loader-sub">NASA POWER · MODIS · GRACE · USDA crop map</div>
          </div>
        </div>
      )}

      <div ref={container} className="map" />
      <div className="map-tools" role="group" aria-label="Map view">
        <div className="seg" role="radiogroup" aria-label="Background">
          {(['map', 'satellite'] as const).map((b) => (
            <button
              key={b}
              type="button"
              role="radio"
              aria-checked={base === b}
              className={base === b ? 'on' : ''}
              onClick={() => setBase(b)}
            >
              {b === 'map' ? 'Map' : 'Satellite'}
            </button>
          ))}
        </div>
        {selectedBounds && (
          <button type="button" onClick={() => zoomToField()}>
            Zoom to field
          </button>
        )}
        <button type="button" onClick={showCounty}>
          Whole county
        </button>
      </div>
      {!armed && (
        <div className={`map-gesture-hint${hint ? ' show' : ''}`} aria-hidden="true">
          {window.matchMedia('(pointer: coarse)').matches
            ? 'Tap the map to move and zoom it'
            : 'Click the map, then scroll to zoom'}
        </div>
      )}

      <div className="county-badge">
        <IconPin className="county-icon" />
        <strong>
          {fields.county.name}, {fields.county.state}
        </strong>{' '}
        (FIPS {fields.county.fips})<span className="county-sub"> · County Boundary</span>
      </div>
    </div>
  );
}
