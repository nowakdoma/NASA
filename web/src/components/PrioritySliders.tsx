import { PRIORITY_KEYS, type PriorityKey } from '../types/contracts';
import type { Priorities } from '../lib/ranking';

const LABELS: Record<PriorityKey, string> = {
  water: 'Save water',
  income: 'Income',
  soil: 'Soil organic matter',
  erosion: 'Limit erosion',
  labour: 'Less labour',
};

export const DEFAULT_PRIORITIES: Priorities = {
  water: 3,
  income: 3,
  soil: 3,
  erosion: 3,
  labour: 3,
};

interface Props {
  value: Priorities;
  onChange: (p: Priorities) => void;
}

export function PrioritySliders({ value, onChange }: Props) {
  return (
    <section className="panel">
      <h3>Your priorities</h3>
      {PRIORITY_KEYS.map((k) => (
        <label key={k} className="priority">
          <span>{LABELS[k]}</span>
          <input
            type="range"
            min={0}
            max={5}
            step={1}
            value={value[k]}
            onChange={(e) => onChange({ ...value, [k]: Number(e.target.value) })}
          />
          <output>{value[k]}</output>
        </label>
      ))}
    </section>
  );
}
