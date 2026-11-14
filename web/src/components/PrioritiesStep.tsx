import { PRIORITY_KEYS } from '../types/contracts';
import type { Priorities } from '../lib/ranking';
import { WATER_LIMIT_OPTIONS, type WaterLimitIn } from '../lib/flow';
import { PRESETS, PrioritySliders } from './PrioritySliders';

interface Props {
  priorities: Priorities;
  onPriorities: (p: Priorities) => void;
  waterLimitIn: WaterLimitIn;
  onWaterLimit: (w: WaterLimitIn) => void;
}

export function presetName(p: Priorities): string | null {
  return PRESETS.find((pr) => PRIORITY_KEYS.every((k) => pr.priorities[k] === p[k]))?.name ?? null;
}

/** Step 2: one preset choice, one constraint, fine-tuning folded away (Hick / Tesler). */
export function PrioritiesStep({ priorities, onPriorities, waterLimitIn, onWaterLimit }: Props) {
  const active = presetName(priorities);
  return (
    <div className="flow-step">
      <div className="flow-eyebrow">Step 2 · What matters to you</div>
      <h2 className="flow-title">What matters most this time?</h2>
      <p className="flow-sub">Pick one to start. You can fine-tune below.</p>
      <div className="choice-row" role="group" aria-label="Priority presets">
        {PRESETS.map((pr) => (
          <button
            key={pr.name}
            type="button"
            className="choice-pill"
            aria-pressed={active === pr.name}
            title={pr.desc}
            onClick={() => onPriorities(pr.priorities)}
          >
            {pr.name}
          </button>
        ))}
      </div>

      <div className="flow-block">
        <h3>How much water can you pump in a year?</h3>
        <p className="flow-sub">
          From your water right or well capacity. If you're not sure, leave it and nothing is ruled
          out. Rotations above your limit are flagged, not hidden.
        </p>
        <div className="choice-row" role="group" aria-label="Yearly water limit">
          {WATER_LIMIT_OPTIONS.map((o) => (
            <button
              key={o.label}
              type="button"
              className="choice-chip"
              aria-pressed={waterLimitIn === o.value}
              onClick={() => onWaterLimit(o.value)}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      <details className="flow-details">
        <summary>Fine-tune the five priorities{active ? '' : ' (custom mix in use)'}</summary>
        <PrioritySliders value={priorities} onChange={onPriorities} showPresets={false} />
      </details>
    </div>
  );
}
