import { useEffect, useState } from 'react';

interface Props {
  min: number;
  max: number;
  value: number;
  onChange: (year: number) => void;
}

export function YearSlider({ min, max, value, onChange }: Props) {
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      onChange(value >= max ? min : value + 1);
    }, 900);
    return () => clearInterval(interval);
  }, [isPlaying, value, min, max, onChange]);

  return (
    <div className="year-slider-widget" role="region" aria-label="Crop history timeline control">
      <div className="year-slider-controls">
        <button
          type="button"
          className="year-nav-btn"
          disabled={value <= min}
          onClick={() => onChange(Math.max(min, value - 1))}
          aria-label="Previous year"
          title="Previous year"
        >
          ‹
        </button>

        <button
          type="button"
          className={`year-play-btn${isPlaying ? ' playing' : ''}`}
          onClick={() => setIsPlaying(!isPlaying)}
          aria-label={isPlaying ? 'Pause animation' : 'Play multi-year animation'}
          title={isPlaying ? 'Pause animation' : 'Play crop history animation (2008–2025)'}
        >
          {isPlaying ? '⏸' : '▶'}
        </button>

        <button
          type="button"
          className="year-nav-btn"
          disabled={value >= max}
          onClick={() => onChange(Math.min(max, value + 1))}
          aria-label="Next year"
          title="Next year"
        >
          ›
        </button>

        <div className="year-display">
          <span className="year-sub">Cropland Data Layer</span>
          <strong className="year-val">{value}</strong>
        </div>
      </div>

      <div className="year-slider-track-wrap">
        <input
          type="range"
          min={min}
          max={max}
          step={1}
          value={value}
          aria-label="Select year for Cropland Data Layer"
          aria-valuemin={min}
          aria-valuemax={max}
          aria-valuenow={value}
          onChange={(e) => {
            setIsPlaying(false);
            onChange(Number(e.target.value));
          }}
          className="year-range-input"
        />
        <div className="year-ticks">
          <span>{min}</span>
          <span>2012 (drought)</span>
          <span>2018</span>
          <span>2022</span>
          <span>{max}</span>
        </div>
      </div>
    </div>
  );
}
