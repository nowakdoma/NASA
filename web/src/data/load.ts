import type { FieldCollection, GraceFile, StrategiesFile } from '../types/contracts';

export type { GraceFile };

const BASE = `${import.meta.env.BASE_URL}data`;

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}/${path}`);
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return (await res.json()) as T;
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
