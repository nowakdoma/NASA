import { STEPS, type Step } from '../lib/flow';

interface Props {
  step: Step;
  onStep: (s: Step) => void;
}

/** Progress bar of the guided flow. Every step stays clickable so users can jump back. */
export function Stepper({ step, onStep }: Props) {
  return (
    <nav aria-label="Progress" className="stepper">
      <ol>
        {STEPS.map((label, i) => {
          const state = i === step ? 'current' : i < step ? 'done' : 'todo';
          return (
            <li key={label}>
              <button
                type="button"
                className={`stepper-btn ${state}`}
                aria-current={i === step ? 'step' : undefined}
                onClick={() => onStep(i as Step)}
              >
                <span className="stepper-dot" aria-hidden="true">
                  {state === 'done' ? '✓' : i + 1}
                </span>
                <span className="stepper-label">{label}</span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
