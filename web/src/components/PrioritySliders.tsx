import { PRIORITY_KEYS, type PriorityKey } from '../types/contracts';
import type { Priorities } from '../lib/ranking';
import { IconRefresh, IconScales } from './Icons';

const LABELS: Record<PriorityKey, { label: string; desc: string }> = {
  water: { label: 'Irrigation Water', desc: 'Reduce seasonal pumping volume from Ogallala' },
  income: { label: 'Net Return', desc: 'Maximize revenue potential per hectare' },
  soil: { label: 'Soil Health', desc: 'Build or maintain Soil Organic Matter trend' },
  erosion: { label: 'Erosion Limit', desc: 'Protect topsoil from water/wind losses' },
  labour: { label: 'Labour Ease', desc: 'Minimize peak field machinery & management hours' },
};

export const DEFAULT_PRIORITIES: Priorities = {
  water: 3,
  income: 3,
  soil: 3,
  erosion: 3,
  labour: 3,
};

export const PRESETS: { name: string; desc: string; priorities: Priorities }[] = [
  {
    name: 'Balanced',
    desc: 'Equal weight across all 5 dimensions',
    priorities: { water: 3, income: 3, soil: 3, erosion: 3, labour: 3 },
  },
  {
    name: 'Save Water',
    desc: 'Prioritize water conservation for GMD3 limits',
    priorities: { water: 5, income: 2, soil: 4, erosion: 3, labour: 2 },
  },
  {
    name: 'Maximize Return',
    desc: 'Focus on short-term net return',
    priorities: { water: 2, income: 5, soil: 2, erosion: 1, labour: 2 },
  },
  {
    name: 'Soil Stewardship',
    desc: 'Max Soil Organic Matter & minimal erosion',
    priorities: { water: 3, income: 2, soil: 5, erosion: 5, labour: 2 },
  },
];

interface Props {
  value: Priorities;
  onChange: (p: Priorities) => void;
  /** Hide the preset row when the presets are already shown elsewhere (guided flow). */
  showPresets?: boolean;
}

const SCALE_DESCRIPTIONS = ['Off', 'Low', 'Moderate', 'High', 'Very High', 'Critical'];

export function PrioritySliders({ value, onChange, showPresets = true }: Props) {
  // Check which preset matches current values (if any)
  const isDefault = PRIORITY_KEYS.every((k) => value[k] === 3);

  return (
    <section className="panel priority-panel" aria-labelledby="priorities-heading">
      <div className="section-title-row">
        <div className="title-with-icon">
          <IconScales className="panel-title-icon" />
          <h3 id="priorities-heading">Decision Priorities</h3>
        </div>
        <button
          type="button"
          className="reset-btn"
          disabled={isDefault}
          onClick={() => onChange(DEFAULT_PRIORITIES)}
          title="Reset all priorities to balanced (3/5)"
          aria-label="Reset priorities to balanced"
        >
          <IconRefresh />
          <span>Reset</span>
        </button>
      </div>

      {/* Preset quick buttons — Hick's Law sensible defaults */}
      {showPresets && (
        <div className="preset-buttons-row" role="group" aria-label="Priority presets">
          {PRESETS.map((preset) => {
            const isActive = PRIORITY_KEYS.every((k) => value[k] === preset.priorities[k]);
            return (
              <button
                key={preset.name}
                type="button"
                className={`preset-chip${isActive ? ' active-preset' : ''}`}
                onClick={() => onChange(preset.priorities)}
                title={preset.desc}
              >
                {preset.name}
              </button>
            );
          })}
        </div>
      )}

      <div className="sliders-list">
        {PRIORITY_KEYS.map((k) => {
          const val = value[k];
          const info = LABELS[k];
          return (
            <label key={k} className="priority-slider-item" title={info.desc}>
              <div className="slider-label-row">
                <span className="slider-title">{info.label}</span>
                <span className="slider-value-pill">
                  {val}/5 · {SCALE_DESCRIPTIONS[val]}
                </span>
              </div>
              <div className="slider-input-wrapper">
                <input
                  type="range"
                  min={0}
                  max={5}
                  step={1}
                  value={val}
                  aria-label={`${info.label} priority weight`}
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
