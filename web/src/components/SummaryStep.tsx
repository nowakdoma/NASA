import { useState } from 'react';
import type { FieldFeature } from '../types/contracts';
import type { RankedStrategy } from '../lib/ranking';
import { outOfTen, type LeadExplanation } from '../lib/explain';
import { WATER_FLAG_TEXT, waterFlag, waterLimitLabel, type WaterLimitIn } from '../lib/flow';

interface Props {
  field: FieldFeature;
  ranked: RankedStrategy[];
  presetLabel: string;
  waterLimitIn: WaterLimitIn;
  explanation: LeadExplanation;
}

/** Step 4: a clear end state — what was explored, what to verify, how to take it along. */
export function SummaryStep({ field, ranked, presetLabel, waterLimitIn, explanation }: Props) {
  const [copied, setCopied] = useState<'ok' | 'fail' | null>(null);
  const lead = ranked[0];
  const checks = [...new Set(ranked.flatMap((r) => r.strategy.verify_locally))];
  const flagged = ranked.filter((r) => waterFlag(r.strategy.metrics.water_use_mm, waterLimitIn));

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied('ok');
    } catch {
      setCopied('fail');
    }
  };

  return (
    <div className="flow-step">
      <div className="flow-eyebrow">Step 4 · Take to your adviser</div>
      <h2 className="flow-title">Your field summary is ready</h2>
      <ul className="summary-list">
        <li>
          Field <strong>{field.properties.field_id}</strong>, {field.properties.area_ha.toFixed(0)}{' '}
          ha, {field.properties.soil.texture}
        </li>
        <li>
          Priorities: <strong>{presetLabel}</strong> · water limit:{' '}
          <strong>{waterLimitLabel(waterLimitIn)}</strong>
        </li>
        {lead && (
          <li>
            {explanation.noneFits ?? (
              <>
                <strong>{lead.strategy.name}</strong> came out on top in {outOfTen(lead.pBest)}.{' '}
                {explanation.why}
              </>
            )}{' '}
            All four rotations, with ranges and data gaps, are in the printout.
          </li>
        )}
        {flagged.map((r) => (
          <li key={r.strategy.id}>
            {r.strategy.name}:{' '}
            {WATER_FLAG_TEXT[
              waterFlag(r.strategy.metrics.water_use_mm, waterLimitIn)!
            ].toLowerCase()}
          </li>
        ))}
      </ul>

      <div className="flow-block">
        <h3>{checks.length} questions to check with your adviser or water district</h3>
        <ul className="summary-checks">
          {checks.map((c) => (
            <li key={c}>{c}</li>
          ))}
        </ul>
      </div>

      <div className="choice-row">
        <button type="button" className="btn-cta" onClick={() => window.print()}>
          Print or save as PDF
        </button>
        <button type="button" className="btn-secondary" onClick={copy}>
          Copy share link
        </button>
        <span className="copy-status" aria-live="polite">
          {copied === 'ok' && 'Link copied.'}
          {copied === 'fail' && 'Could not copy. Use the address bar link instead.'}
        </span>
      </div>

      <p className="summary-next">
        <strong>What happens next:</strong> this is a starting point for a conversation, not a plan.
        Prices, your well and wind erosion are things only local people can judge.
      </p>
    </div>
  );
}
