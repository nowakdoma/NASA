import { useRef, useState } from 'react';
import { MapErrorBoundary } from './MapErrorBoundary';
import type { AppData } from '../data/load';
import { STEPS } from '../lib/flow';
import { MapView } from './MapView';
import { GraceSparkline } from './GraceSparkline';
import { IconSatellite, IconSprout } from './Icons';

interface Props {
  data: AppData;
  exampleId: string;
  onStart: (fieldId: string) => void;
  onOpenAbout: () => void;
}

/** Screen A: one promise, one primary action (pick your field), one safe default (example). */
export function StartScreen({ data, exampleId, onStart, onOpenAbout }: Props) {
  const [pickHint, setPickHint] = useState(false);
  const mapRef = useRef<HTMLElement>(null);
  const [y0, y1] = data.fields.years;
  const [w0, w1] = data.strategies.weather_years;
  const year = y1;

  const findField = () => {
    setPickHint(true);
    mapRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    mapRef.current?.focus({ preventScroll: true });
  };

  return (
    <div className="start">
      <header className="start-header">
        <div className="header-brand">
          <div className="logo-badge" aria-hidden="true">
            <IconSprout className="logo-svg" />
          </div>
          <span className="start-brand">FieldShift</span>
          <span className="region-chip">
            {data.fields.county.name}, {data.fields.county.state} · more regions planned
          </span>
        </div>
        <button type="button" className="about-nav-btn" onClick={onOpenAbout}>
          <IconSatellite />
          <span>How we know (NASA data)</span>
        </button>
      </header>

      <main className="start-main">
        <section className="start-copy">
          <ol className="start-steps" aria-label="What you will do">
            {STEPS.map((s, i) => (
              <li key={s} className={i === 0 ? 'first' : ''}>
                {i + 1} {s}
              </li>
            ))}
          </ol>
          <h1 className="start-title">
            What could a different rotation do for <span>your field</span>?
          </h1>
          <p className="start-lede">
            The water under these pivots is going down, and satellites show many fields without
            green cover for months. Pick your field to see its satellite history and compare four
            rotations across {w1 - w0 + 1} years of NASA weather. You get ranges, not promises, plus
            what to check on the ground.
          </p>
          <div className="start-actions">
            <button type="button" className="btn-cta btn-lg" onClick={findField}>
              Find my field on the map
            </button>
            <button
              type="button"
              className="btn-secondary btn-lg"
              onClick={() => onStart(exampleId)}
            >
              Try an example field ({exampleId})
            </button>
          </div>
          <p className="start-fine">
            About 3 minutes. Nothing to install, no account. Decision support only: you and your
            adviser decide.
          </p>
          <dl className="start-stats">
            <div>
              <dd>{data.fields.features.length}</dd>
              <dt>irrigated fields mapped</dt>
            </div>
            <div>
              <dd>{y1 - y0 + 1} yrs</dd>
              <dt>crop history per field</dt>
            </div>
            <div>
              <dd>{w1 - w0 + 1} yrs</dd>
              <dt>NASA weather tested</dt>
            </div>
          </dl>
          {data.grace && <GraceSparkline grace={data.grace} />}
        </section>

        <section
          ref={mapRef}
          tabIndex={-1}
          className={`start-map${pickHint ? ' picking' : ''}`}
          aria-label="Map of fields. Click your field to start."
        >
          <MapErrorBoundary>
            <MapView
              fields={data.fields}
              year={year}
              selectedId={null}
              onSelect={onStart}
              highlightCrop={null}
            />
          </MapErrorBoundary>
          <div className="start-map-hint" aria-live="polite">
            {pickHint
              ? `Click your field to start. Colours show the ${year} crop.`
              : `Colours show the ${year} crop (USDA crop map). Click any field to start.`}
          </div>
        </section>
      </main>
    </div>
  );
}
