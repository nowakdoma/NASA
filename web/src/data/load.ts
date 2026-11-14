import type { FieldCollection, StrategiesFile } from '../types/contracts';

const BASE = `${import.meta.env.BASE_URL}data`;

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}/${path}`);
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return (await res.json()) as T;
}

/** Optional regional context from pipeline/grace.py (not yet in contracts/ — see TASKS.md). */
export interface GraceFile {
  source: string;
  units: string;
  trend: { cm_per_year: number; r2: number };
  series: { date: string; tws_cm: number; uncertainty_cm?: number }[];
  data_gaps?: string[];
}

export interface AppData {
  fields: FieldCollection;
  strategies: StrategiesFile;
  grace: GraceFile | null;
}

export async function loadData(): Promise<AppData> {
  const [fields, strategies, grace] = await Promise.all([
    getJson<FieldCollection>('fields.geojson'),
    getJson<StrategiesFile>('strategies.json'),
    // Optional: the start screen simply omits the card when the file is absent.
    getJson<GraceFile>('grace_water_storage.json').catch(() => null),
  ]);
  return { fields, strategies, grace: grace?.series?.length ? grace : null };
}
