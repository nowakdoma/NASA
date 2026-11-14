interface Props {
  min: number;
  max: number;
  value: number;
  onChange: (year: number) => void;
}

export function YearSlider({ min, max, value, onChange }: Props) {
  return (
    <label className="year-slider">
      <span>
        CDL year <strong>{value}</strong>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}
