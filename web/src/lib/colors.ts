// Earthy, high-contrast agricultural cartographic palette (USGS / USDA inspired).
export const CROP_COLORS: Record<string, [number, number, number]> = {
  corn: [229, 169, 39], // Rich warm maize gold
  sorghum: [194, 65, 12], // Warm grain terracotta / amber
  winter_wheat: [168, 117, 43], // Deep bronze wheat / harvest gold
  soybeans: [46, 125, 50], // Deep healthy agricultural green
  alfalfa: [142, 92, 163], // Muted clover / heather purple
  cotton: [212, 107, 78], // Dusty warm coral / desert rose
  sunflower: [237, 138, 25], // Sunny ochre
  rye_cover: [21, 94, 53], // Forest pine conservation cover
  fallow: [168, 160, 149], // Warm sandstone / fallow silt
  grass_pasture: [122, 158, 126], // Prairie sage / pasture green
};

const UNKNOWN: [number, number, number] = [140, 145, 150];

export const cropColor = (crop: string | undefined): [number, number, number] =>
  (crop && CROP_COLORS[crop]) || UNKNOWN;

export const cropCss = (crop: string | undefined): string => `rgb(${cropColor(crop).join(',')})`;

const CROP_LABELS: Record<string, string> = {
  corn: 'Corn (grain)',
  sorghum: 'Grain sorghum',
  winter_wheat: 'Winter wheat',
  soybeans: 'Soybeans',
  alfalfa: 'Alfalfa (hay)',
  cotton: 'Cotton',
  sunflower: 'Sunflower',
  rye_cover: 'Cereal rye (cover)',
  fallow: 'Fallow / idle',
  grass_pasture: 'Grass / pasture',
};

export const cropLabel = (crop: string): string => CROP_LABELS[crop] ?? crop.replace(/_/g, ' ');
