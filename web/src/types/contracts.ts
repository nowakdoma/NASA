// Hand-written mirror of contracts/*.schema.json (v0.3).
// Change only together with the schemas (human approval required, see AGENTS.md).

export type CropCode = string;
export type YearKey = string; // "2008"

export interface Soil {
  map_unit?: string;
  texture: string;
  om_pct: number;
  kffact: number;
  awc_mm: number;
  slope_pct: number;
}

export interface DateRange {
  year: number;
  start: string; // YYYY-MM-DD
  end: string;
  source: string;
  note?: string;
}

export type BarePeriod = DateRange;

export interface StressWindow extends DateRange {
  type: 'water' | 'heat' | 'frost';
  severity: number; // 0..1
}

export interface FieldProperties {
  field_id: string;
  name?: string;
  area_ha: number;
  irrigated: boolean;
  irrigation_type?: 'center_pivot' | 'flood' | 'drip' | 'none' | 'unknown';
  crop_history: Record<YearKey, CropCode>;
  soil: Soil;
  season_calendar: { bare_periods: BarePeriod[]; stress_windows: StressWindow[] };
  stress_index_by_year: Record<YearKey, number>;
}

export interface FieldFeature {
  type: 'Feature';
  id?: string;
  geometry: { type: 'Polygon' | 'MultiPolygon'; coordinates: unknown };
  properties: FieldProperties;
}

export interface FieldCollection {
  type: 'FeatureCollection';
  schema_version: string;
  mock?: boolean;
  county: { name: string; state: string; fips: string; bbox: [number, number, number, number] };
  years: [number, number];
  features: FieldFeature[];
}

export const METRIC_KEYS = [
  'water_use_mm',
  'erosion_t_ha',
  'soil_index',
  'income_usd_ha',
  'labour_index',
] as const;
export type MetricKey = (typeof METRIC_KEYS)[number];

export const PRIORITY_KEYS = ['water', 'income', 'soil', 'erosion', 'labour'] as const;
export type PriorityKey = (typeof PRIORITY_KEYS)[number];

export interface Interval {
  p10: number;
  p50: number;
  p90: number;
}

export interface MetricMeta {
  label: string;
  unit: string;
  better: 'higher' | 'lower';
  priority?: PriorityKey;
  description?: string;
}

export interface SoilHealthTraits {
  n_fixing_years: number;
  pest_break: boolean;
  forage: boolean;
}

export interface Strategy {
  id: string;
  name: string;
  description?: string;
  why_considered?: string;
  benefits?: string[];
  soil_health_traits?: SoilHealthTraits;
  is_current: boolean;
  rotation: CropCode[];
  metrics: Record<MetricKey, Interval>;
  evidence: { dataset: string; note: string; url?: string }[];
  data_gaps: string[];
  verify_locally: string[];
}

export interface StrategiesFile {
  schema_version: string;
  mock?: boolean;
  generated_by: string;
  generated_at?: string;
  weather_years: [number, number];
  metric_meta: Record<MetricKey, MetricMeta>;
  fields: Record<string, Strategy[]>;
}

/** contracts/grace.schema.json (v0.3): regional TOTAL water storage, not groundwater. */
export interface GraceFile {
  schema_version: string;
  mock?: boolean;
  source: string;
  units: string;
  region: { name: string; fips: string; bbox: [number, number, number, number] };
  trend: { cm_per_year: number; r2: number; stderr_cm_per_year?: number };
  series: { date: string; tws_cm: number; uncertainty_cm?: number }[];
  data_gaps: string[];
}
