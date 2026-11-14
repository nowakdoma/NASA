import type { FieldCollection, StrategiesFile } from '../types/contracts';

const BASE = `${import.meta.env.BASE_URL}data`;

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}/${path}`);
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return (await res.json()) as T;
}

export interface AppData {
  fields: FieldCollection;
  strategies: StrategiesFile;
}

export async function loadData(): Promise<AppData> {
  const [fields, strategies] = await Promise.all([
    getJson<FieldCollection>('fields.geojson'),
    getJson<StrategiesFile>('strategies.json'),
  ]);
  return { fields, strategies };
}
