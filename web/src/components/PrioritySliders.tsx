import { PRIORITY_KEYS, type PriorityKey } from '../types/contracts';
import type { Priorities } from '../lib/ranking';

const LABELS: Record<PriorityKey, { label: string; desc: string }> = {
  water: { label: 'Save Water', desc: 'Reduce irrigation extraction' },
  income: { label: 'Net Income', desc: 'Maximize crop margins' },
  soil: { label: 'Soil Health', desc: 'Maintain or build SOM' },
  erosion: { label: 'Limit Erosion', desc: 'Protect topsoil from water/wind' },
  labour: { label: 'Manage Labour', desc: 'Minimize peak field operations' },
};

export const DEFAULT_PRIORITIES: Priorities = {
  water: 3,
  income: 3,
  soil: 3,
  erosion: 3,
  labour: 3,
};

const PRESETS: { name: string; priorities: Priorities }[] = [
  {
    name: 'Balanced',
    priorities: { water: 3, income: 3, soil: 3, erosion: 3, labour: 3 },
  },
  {
    name: 'Water Conservation',
    priorities: { water: 5, income: 2, soil: 4, erosion: 3, labour: 2 },
  },
  {
    name: 'Profit Focus',
    priorities: { water: 2, income: 5, soil: 2, erosion: 1, labour: 2 },
  },
  {
    name: 'Soil Stewardship',
    priorities: { water: 3, income: 2, soil: 5, erosion: 5, labour: 2 },
  },
];

interface Props {
  value: Priorities;
  onChange: (p: Priorities) => void;
}

const SCALE_DESCRIPTIONS = ['Ignore', 'Low', 'Moderate', 'Important', 'High', 'Critical'];

export function PrioritySliders({ value, onChange }: Props) {
  return (
    <section className="panel priority-panel" aria-labelledby="priorities-heading">
      <div className="section-title-row">
        <h3 id="priorities-heading">Farmer Decision Priorities</h3>
        <button
          type="button"
          className="reset-btn"
          onClick={() => onChange(DEFAULT_PRIORITIES)}
          title="Reset all priorities to 3"
        >
          Reset
        </button>
      </div>

      <p className="muted priority-hint">
        Adjust weights to reflect your operational goals. MCDA ranks rotation trade-offs
        accordingly.
      </p>

      {/* Preset quick buttons */}
      <div className="preset-buttons-row" role="group" aria-label="Priority presets">
        {PRESETS.map((preset) => (
          <button
            key={preset.name}
            type="button"
            className="preset-chip"
            onClick={() => onChange(preset.priorities)}
          >
            {preset.name}
          </button>
        ))}
      </div>

      <div className="sliders-list">
        {PRIORITY_KEYS.map((k) => {
          const val = value[k];
          const info = LABELS[k];
          return (
            <label key={k} className="priority-slider-item">
              <div className="slider-label-row">
                <span className="slider-title">{info.label}</span>
                <span className="slider-desc muted">{info.desc}</span>
                <span className="slider-value-pill">
                  {val} · {SCALE_DESCRIPTIONS[val]}
                </span>
              </div>
              <div className="slider-input-wrapper">
                <input
                  type="range"
                  min={0}
                  max={5}
                  step={1}
                  value={val}
                  aria-label={`${info.label} priority`}
                  aria-valuemin={0}
                  aria-valuemax={5}
                  aria-valuenow={val}
                  aria-valuetext={`${val} of 5 (${SCALE_DESCRIPTIONS[val]})`}
                  onChange={(e) => onChange({ ...value, [k]: Number(e.target.value) })}
                />
              </div>
            </label>
          );
        })}
      </div>
    </section>
  );
}
