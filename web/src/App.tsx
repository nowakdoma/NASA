import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { MapErrorBoundary } from './components/MapErrorBoundary';
import { loadData, type AppData } from './data/load';
import { MapView } from './components/MapView';
import { YearSlider } from './components/YearSlider';
import { CropLegend } from './components/CropLegend';
import { FieldPanel } from './components/FieldPanel';
import { DEFAULT_PRIORITIES } from './components/PrioritySliders';
import { Stepper } from './components/Stepper';
import { StartScreen } from './components/StartScreen';
import { FieldStep } from './components/FieldStep';
import { PrioritiesStep, presetName } from './components/PrioritiesStep';
import { CompareStep } from './components/CompareStep';
import { SummaryStep } from './components/SummaryStep';
import { readHash, writeHash, type Step, type WaterLimitIn } from './lib/flow';
import './flow.css';
import { StrategyComparison } from './components/StrategyComparison';
import { AboutModal } from './components/AboutModal';
import { PrintReport } from './components/PrintReport';
import { rankStrategies, type Priorities } from './lib/ranking';
import { IconClipboard, IconMap, IconSatellite, IconSprout } from './components/Icons';

type MobileTab = 'map' | 'steps';

const NEXT_LABEL = ['Next: what matters to you', 'Compare rotations', 'Make adviser summary'];

export default function App() {
  const initial = useMemo(readHash, []);
  const [data, setData] = useState<AppData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [year, setYear] = useState<number>(2025);
  const [selectedId, setSelectedId] = useState<string | null>(initial.fieldId);
  const [highlightCrop, setHighlightCrop] = useState<string | null>(null);
  const [priorities, setPriorities] = useState<Priorities>(
    initial.priorities ?? DEFAULT_PRIORITIES,
  );
  const [waterLimitIn, setWaterLimitIn] = useState<WaterLimitIn>(initial.waterLimitIn);
  const [step, setStep] = useState<Step>(initial.step);
  // Screen A until a field is chosen; a shared/reloaded link (#f=…) skips straight to the flow.
  const [started, setStarted] = useState<boolean>(initial.fieldId !== null);
  const [isAboutOpen, setIsAboutOpen] = useState(false);
  const [mobileTab, setMobileTab] = useState<MobileTab>('map');
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadData()
      .then((d) => {
        setData(d);
        setYear(d.fields.years[1]);
        setSelectedId((id) =>
          id && d.fields.features.some((f) => f.properties.field_id === id)
            ? id
            : (d.fields.features[0]?.properties.field_id ?? null),
        );
      })
      .catch((e: unknown) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!started) return;
    writeHash({ fieldId: selectedId, step, priorities, waterLimitIn });
  }, [started, selectedId, step, priorities, waterLimitIn]);

  const goTo = (s: Step) => {
    setStep(s);
    panelRef.current?.scrollTo({ top: 0 });
    panelRef.current?.focus({ preventScroll: true });
  };

  const selected = useMemo(
    () => data?.fields.features.find((f) => f.properties.field_id === selectedId) ?? null,
    [data, selectedId],
  );

  const ranked = useMemo(() => {
    if (!data || !selectedId) return [];
    const strategies = data.strategies.fields[selectedId] ?? [];
    return rankStrategies(strategies, data.strategies.metric_meta, priorities);
  }, [data, selectedId, priorities]);

  const closeAbout = useCallback(() => setIsAboutOpen(false), []);
  const presetLabel = (presetName(priorities) ?? 'your custom').toLowerCase();

  const handleSelectField = (fieldId: string) => {
    setSelectedId(fieldId);
    if (window.innerWidth < 850 && mobileTab === 'map') {
      setMobileTab('steps');
    }
  };

  if (error) {
    return (
      <div className="status error" role="alert">
        <h2>Failed to load application data</h2>
        <p>{error}</p>
        <button type="button" className="btn-primary" onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="status loading" aria-live="polite">
        <div className="spinner" />
        <p>Loading NASA satellite & field data for Finney County, KS…</p>
      </div>
    );
  }

  const isMock = data.fields.mock || data.strategies.mock;

  if (!started) {
    const exampleId =
      data.fields.features.find((f) => f.properties.field_id === 'FIN-001')?.properties.field_id ??
      data.fields.features[0]?.properties.field_id ??
      '';
    return (
      <>
        <StartScreen
          data={data}
          exampleId={exampleId}
          onStart={(id) => {
            setSelectedId(id);
            setStep(0);
            setStarted(true);
            setMobileTab('steps');
          }}
          onOpenAbout={() => setIsAboutOpen(true)}
        />
        <AboutModal isOpen={isAboutOpen} onClose={closeAbout} grace={data.grace} />
      </>
    );
  }

  return (
    <div className="app">
      <header className="app-header no-print">
        <div className="header-brand">
          <div className="logo-badge" aria-hidden="true">
            <IconSprout className="logo-svg" />
          </div>
          <div>
            <h1>
              <button
                type="button"
                className="brand-home"
                onClick={() => setStarted(false)}
                title="Back to the start screen"
              >
                FieldShift
              </button>
            </h1>
            <span className="subtitle">
              {data.fields.county.name}, {data.fields.county.state} · more regions planned
            </span>
          </div>
        </div>

        <Stepper step={step} onStep={goTo} />

        <div className="header-actions">
          {isMock && (
            <span className="badge-mock" title="Rendering mock contract data">
              MOCK DATA (v{data.fields.schema_version})
            </span>
          )}
          <button
            type="button"
            className="about-nav-btn"
            onClick={() => setIsAboutOpen(true)}
            aria-label="How we know: NASA data sources and uncertainty"
          >
            <IconSatellite />
            <span>How we know</span>
          </button>
        </div>
      </header>

      <nav className="mobile-tab-nav no-print" aria-label="View sections">
        <button
          type="button"
          className={`tab-item${mobileTab === 'map' ? ' active' : ''}`}
          onClick={() => setMobileTab('map')}
        >
          <IconMap />
          <span>Field map</span>
        </button>
        <button
          type="button"
          className={`tab-item${mobileTab === 'steps' ? ' active' : ''}`}
          onClick={() => setMobileTab('steps')}
        >
          <IconClipboard />
          <span>
            Step {step + 1} of 4 {selectedId ? `· ${selectedId}` : ''}
          </span>
        </button>
      </nav>

      <main className="app-main no-print">
        <section
          className={`map-col${mobileTab !== 'map' ? ' mobile-hidden' : ''}`}
          aria-label="Interactive map view"
        >
          <MapErrorBoundary>
            <MapView
              fields={data.fields}
              year={year}
              selectedId={selectedId}
              onSelect={handleSelectField}
              highlightCrop={highlightCrop}
            />
          </MapErrorBoundary>
          <div className="map-controls">
            <YearSlider
              min={data.fields.years[0]}
              max={data.fields.years[1]}
              value={year}
              onChange={setYear}
            />
            <CropLegend
              fields={data.fields}
              year={year}
              highlightCrop={highlightCrop}
              onHighlightCrop={setHighlightCrop}
            />
          </div>
        </section>

        <aside
          className={`side-col flow-col${mobileTab === 'map' ? ' mobile-hidden' : ''}`}
          aria-label="Guided field analysis"
        >
          {selected ? (
            <>
              <div className="flow-scroll" ref={panelRef} tabIndex={-1}>
                {step === 0 && (
                  <>
                    <FieldStep field={selected} year={year} onSelectYear={setYear} />
                    <details className="flow-details">
                      <summary>Season-by-season detail for {year}</summary>
                      <FieldPanel
                        field={selected}
                        year={year}
                        onSelectYear={setYear}
                        onOpenAbout={() => setIsAboutOpen(true)}
                        allFields={data.fields.features}
                        onSelectField={handleSelectField}
                      />
                    </details>
                  </>
                )}
                {step === 1 && (
                  <PrioritiesStep
                    priorities={priorities}
                    onPriorities={setPriorities}
                    waterLimitIn={waterLimitIn}
                    onWaterLimit={setWaterLimitIn}
                  />
                )}
                {step === 2 && (
                  <>
                    <CompareStep
                      ranked={ranked}
                      meta={data.strategies.metric_meta}
                      weatherYears={data.strategies.weather_years}
                      presetLabel={presetLabel}
                      waterLimitIn={waterLimitIn}
                      onOpenAbout={() => setIsAboutOpen(true)}
                    />
                    <details className="flow-details flow-details-wide">
                      <summary>Detailed charts for all five measures</summary>
                      <StrategyComparison
                        ranked={ranked}
                        meta={data.strategies.metric_meta}
                        weatherYears={data.strategies.weather_years}
                        onOpenAbout={() => setIsAboutOpen(true)}
                      />
                    </details>
                  </>
                )}
                {step === 3 && (
                  <SummaryStep
                    field={selected}
                    ranked={ranked}
                    presetLabel={presetLabel}
                    waterLimitIn={waterLimitIn}
                  />
                )}
                <footer className="side-footer">
                  <a
                    href="https://www.flaticon.com/free-icons/yield"
                    title="yield icons"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Yield icons created by Eucalyp - Flaticon
                  </a>
                </footer>
              </div>

              <div className="flow-footer">
                <button
                  type="button"
                  className="text-link-btn"
                  onClick={() => setIsAboutOpen(true)}
                >
                  How we know this
                </button>
                <div className="flow-footer-actions">
                  {step > 0 && (
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => goTo((step - 1) as Step)}
                    >
                      Back
                    </button>
                  )}
                  {step < 3 && (
                    <button
                      type="button"
                      className="btn-cta"
                      onClick={() => goTo((step + 1) as Step)}
                    >
                      {NEXT_LABEL[step]}
                    </button>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <p className="hint">Click a field on the map to start.</p>
            </div>
          )}
        </aside>
      </main>

      {/* About & Uncertainty Dialog */}
      <AboutModal
        isOpen={isAboutOpen}
        onClose={closeAbout}
        grace={data.grace}
        ranked={ranked}
        fieldId={selectedId}
        weatherYears={data.strategies.weather_years}
      />

      {/* Printable PDF Report (rendered in print media only) */}
      {selected && (
        <PrintReport
          field={selected}
          county={data.fields.county}
          priorities={priorities}
          presetLabel={presetLabel}
          waterLimitIn={waterLimitIn}
          ranked={ranked}
          meta={data.strategies.metric_meta}
          weatherYears={data.strategies.weather_years}
          grace={data.grace}
        />
      )}
    </div>
  );
}
