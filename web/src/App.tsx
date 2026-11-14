import { useEffect, useMemo, useState } from 'react';
import { loadData, type AppData } from './data/load';
import { MapView } from './components/MapView';
import { YearSlider } from './components/YearSlider';
import { CropLegend } from './components/CropLegend';
import { FieldPanel } from './components/FieldPanel';
import { PrioritySliders, DEFAULT_PRIORITIES } from './components/PrioritySliders';
import { StrategyComparison } from './components/StrategyComparison';
import { AboutModal } from './components/AboutModal';
import { rankStrategies, type Priorities } from './lib/ranking';

type MobileTab = 'map' | 'passport' | 'strategies';

export default function App() {
  const [data, setData] = useState<AppData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [year, setYear] = useState<number>(2025);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [highlightCrop, setHighlightCrop] = useState<string | null>(null);
  const [priorities, setPriorities] = useState<Priorities>(DEFAULT_PRIORITIES);
  const [isAboutOpen, setIsAboutOpen] = useState(false);
  const [mobileTab, setMobileTab] = useState<MobileTab>('map');

  useEffect(() => {
    loadData()
      .then((d) => {
        setData(d);
        setYear(d.fields.years[1]);
        setSelectedId(d.fields.features[0]?.properties.field_id ?? null);
      })
      .catch((e: unknown) => setError(String(e)));
  }, []);

  const selected = useMemo(
    () => data?.fields.features.find((f) => f.properties.field_id === selectedId) ?? null,
    [data, selectedId],
  );

  const ranked = useMemo(() => {
    if (!data || !selectedId) return [];
    const strategies = data.strategies.fields[selectedId] ?? [];
    return rankStrategies(strategies, data.strategies.metric_meta, priorities);
  }, [data, selectedId, priorities]);

  const handleSelectField = (fieldId: string) => {
    setSelectedId(fieldId);
    // On small screens, if on map tab, switch to passport to view details
    if (window.innerWidth < 850 && mobileTab === 'map') {
      setMobileTab('passport');
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

  return (
    <div className="app">
      {/* Top Header */}
      <header className="app-header">
        <div className="header-brand">
          <div className="logo-icon" aria-hidden="true">
            🌱
          </div>
          <div>
            <h1>FieldShift</h1>
            <span className="subtitle">
              {data.fields.county.name}, {data.fields.county.state} · Adaptive Crop Rotation
              Decision Support
            </span>
          </div>
        </div>

        <div className="header-actions">
          {isMock && (
            <span
              className="badge-mock"
              title="Currently rendering verified contract mocks pending final pipeline run"
            >
              MOCK DATA (v{data.fields.schema_version})
            </span>
          )}

          <button
            type="button"
            className="about-nav-btn"
            onClick={() => setIsAboutOpen(true)}
            aria-label="About data, NASA sources, and uncertainty methodology"
          >
            🛰️ About the Data & Uncertainty
          </button>
        </div>
      </header>

      {/* Mobile / Tablet Tab Navigation Bar */}
      <nav className="mobile-tab-nav" aria-label="View sections">
        <button
          type="button"
          className={`tab-item${mobileTab === 'map' ? ' active' : ''}`}
          onClick={() => setMobileTab('map')}
        >
          🗺️ Field Map
        </button>
        <button
          type="button"
          className={`tab-item${mobileTab === 'passport' ? ' active' : ''}`}
          onClick={() => setMobileTab('passport')}
        >
          📋 Passport {selectedId ? `(${selectedId})` : ''}
        </button>
        <button
          type="button"
          className={`tab-item${mobileTab === 'strategies' ? ' active' : ''}`}
          onClick={() => setMobileTab('strategies')}
        >
          ⚖️ Priorities & Strategies
        </button>
      </nav>

      {/* Main Content Workspace */}
      <main className="app-main">
        {/* Left Column: Interactive Map & Map Controls */}
        <section
          className={`map-col${mobileTab !== 'map' ? ' mobile-hidden' : ''}`}
          aria-label="Interactive map view"
        >
          <MapView
            fields={data.fields}
            year={year}
            selectedId={selectedId}
            onSelect={handleSelectField}
            highlightCrop={highlightCrop}
          />
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

        {/* Right Column: Field Passport, Priorities, and Strategy Comparisons */}
        <aside
          className={`side-col${mobileTab === 'map' ? ' mobile-hidden' : ''}`}
          aria-label="Field evaluation and rotation analysis"
        >
          {selected ? (
            <>
              <div className={mobileTab === 'strategies' ? 'mobile-hidden-section' : ''}>
                <FieldPanel field={selected} year={year} onSelectYear={setYear} />
              </div>

              <div className={mobileTab === 'passport' ? 'mobile-hidden-section' : ''}>
                <PrioritySliders value={priorities} onChange={setPriorities} />
                <StrategyComparison
                  ranked={ranked}
                  meta={data.strategies.metric_meta}
                  weatherYears={data.strategies.weather_years}
                />
              </div>
            </>
          ) : (
            <div className="empty-state">
              <p className="hint">
                Select a field on the map to inspect its passport and rotation options.
              </p>
            </div>
          )}
        </aside>
      </main>

      {/* About & Uncertainty Dialog */}
      <AboutModal isOpen={isAboutOpen} onClose={() => setIsAboutOpen(false)} />
    </div>
  );
}
