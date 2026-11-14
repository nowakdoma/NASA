// Guided-flow state (step, field, priorities, water limit) kept in the URL hash so progress
// survives a reload and the adviser summary can be shared as a link.
import { PRIORITY_KEYS } from '../types/contracts';
import { WATER_TOLERANCE, type Priorities } from './ranking';

export const STEPS = ['Your field', 'What matters', 'Compare', 'Adviser summary'] as const;
export type Step = 0 | 1 | 2 | 3;

/** Yearly pumping limit in inches; null = not sure / no limit (nothing is flagged). */
export type WaterLimitIn = number | null;
export const WATER_LIMIT_OPTIONS: { value: WaterLimitIn; label: string }[] = [
  { value: null, label: 'Not sure / no limit' },
  { value: 18, label: '18 in' },
  { value: 14, label: '14 in' },
  { value: 8, label: '8 in' },
  { value: 0, label: 'None (dryland)' },
];
export const MM_PER_IN = 25.4;

export interface FlowState {
  fieldId: string | null;
  step: Step;
  priorities: Priorities | null;
  waterLimitIn: WaterLimitIn;
}

export function readHash(): FlowState {
  const q = new URLSearchParams(window.location.hash.replace(/^#/, ''));
  const s = Number(q.get('s'));
  const p = (q.get('p') ?? '').split(',').map(Number);
  const w = q.get('w');
  return {
    fieldId: q.get('f'),
    step: (s >= 0 && s <= 3 ? s : 0) as Step,
    priorities:
      p.length === PRIORITY_KEYS.length && p.every((x) => Number.isInteger(x) && x >= 0 && x <= 5)
        ? (Object.fromEntries(PRIORITY_KEYS.map((k, i) => [k, p[i]])) as Priorities)
        : null,
    waterLimitIn: w === null || w === '' || Number.isNaN(Number(w)) ? null : Number(w),
  };
}

/** `push` adds a history entry (step changes, so Back returns to the previous step);
 *  `replace` updates the link in place (slider and limit changes). */
export function writeHash(s: FlowState & { priorities: Priorities }, mode: 'push' | 'replace') {
  const q = new URLSearchParams();
  if (s.fieldId) q.set('f', s.fieldId);
  q.set('s', String(s.step));
  q.set('p', PRIORITY_KEYS.map((k) => s.priorities[k]).join(','));
  if (s.waterLimitIn !== null) q.set('w', String(s.waterLimitIn));
  const url = `#${q.toString()}`;
  if (mode === 'push') window.history.pushState(null, '', url);
  else window.history.replaceState(null, '', url);
}

export type WaterFlag = 'typical' | 'dry' | null;

/** Compare a strategy's irrigation interval (mm) with the farmer's limit. */
export function waterFlag(water: { p50: number; p90: number }, limitIn: WaterLimitIn): WaterFlag {
  if (limitIn === null) return null;
  const limit = limitIn * MM_PER_IN * (1 + WATER_TOLERANCE);
  if (water.p50 > limit) return 'typical';
  if (water.p90 > limit) return 'dry';
  return null;
}

export const WATER_FLAG_TEXT: Record<'typical' | 'dry', string> = {
  typical: 'Needs more water than your limit in a typical year',
  dry: 'Goes over your limit in about 1 dry year in 10',
};

export function waterLimitLabel(limitIn: WaterLimitIn): string {
  if (limitIn === null) return 'not set';
  if (limitIn === 0) return 'none (dryland)';
  return `${limitIn} in/yr (${Math.round(limitIn * MM_PER_IN)} mm)`;
}
