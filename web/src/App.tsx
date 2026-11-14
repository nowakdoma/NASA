import { useEffect, useMemo, useState } from 'react';
import { loadData, type AppData } from './data/load';
import { MapView } from './components/MapView';
import { YearSlider } from './components/YearSlider';
import { CropLegend } from './components/CropLegend';
import { FieldPanel } from './components/FieldPanel';
import { PrioritySliders, DEFAULT_PRIORITIES } from './components/PrioritySliders';
import { StrategyComparison } from './components/StrategyComparison';
import { rankStrategies, type Priorities } from './lib/ranking';

export default function App() {
  const [data, setData] = useState<AppData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [year, setYear] = useState<number>(2025);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [priorities, setPriorities] = useState<Priorities>(DEFAULT_PRIORITIES);

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

  if (error) return <div className="status error">Could not load data: {error}</div>;
  if (!data) return <div className="status">Loading…</div>;

  const isMock = data.fields.mock || data.strategies.mock;
  return (
    <div className="app">
      <header className="app-header">
        <h1>FieldShift</h1>
        <span className="subtitle">
          {data.fields.county.name}, {data.fields.county.state} — decision support, not a
          recommendation
        </span>
        {isMock && <span className="badge-mock">MOCK DATA</span>}
      </header>
      <main className="app-main">
        <section className="map-col">
          <MapView
            fields={data.fields}
            year={year}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
          <div className="map-controls">
            <YearSlider
              min={data.fields.years[0]}
              max={data.fields.years[1]}
              value={year}
              onChange={setYear}
            />
            <CropLegend fields={data.fields} year={year} />
          </div>
        </section>
        <aside className="side-col">
          {selected ? (
            <>
              <FieldPanel field={selected} year={year} />
              <PrioritySliders value={priorities} onChange={setPriorities} />
              <StrategyComparison
                ranked={ranked}
                meta={data.strategies.metric_meta}
                weatherYears={data.strategies.weather_years}
              />
            </>
          ) : (
            <p className="hint">Click a field on the map.</p>
          )}
        </aside>
      </main>
    </div>
  );
}
