// Topographic ink crop palette (design canvas, Look 3).
export const CROP_COLORS: Record<string, [number, number, number]> = {
  corn: [226, 179, 60], // Topo maize #E2B33C
  sorghum: [164, 71, 42], // Topo terracotta #A4472A
  winter_wheat: [216, 204, 160], // Topo straw #D8CCA0
  soybeans: [122, 140, 64], // Olive
  alfalfa: [79, 125, 58], // Topo alfalfa green #4F7D3A
  cotton: [212, 107, 78], // Dusty warm coral / desert rose
  sunflower: [237, 138, 25], // Sunny ochre
  rye_cover: [43, 122, 155], // Topo accent blue (cover)
  fallow: [168, 160, 149], // Warm sandstone / fallow silt
  grass_pasture: [122, 158, 126], // Prairie sage / pasture green
  // contracts v0.2 classes: tints of the parent crop so double crops read as related
  triticale: [190, 170, 110], // darker straw (wheat family)
  winwht_corn: [238, 208, 128], // light maize
  triticale_corn: [238, 208, 128], // light maize
  winwht_sorghum: [198, 122, 96], // light terracotta
  winwht_soybeans: [154, 166, 98], // light olive
  other_hay: [120, 150, 96], // hay green, lighter than alfalfa
  potatoes: [140, 112, 96], // soil brown
  other_crops: [170, 165, 150], // neutral
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
  triticale: 'Triticale',
  potatoes: 'Potatoes',
  other_hay: 'Other hay',
  other_crops: 'Other crops',
  winwht_corn: 'Wheat / corn (double crop)',
  triticale_corn: 'Triticale / corn (double crop)',
  winwht_sorghum: 'Wheat / sorghum (double crop)',
  winwht_soybeans: 'Wheat / soybeans (double crop)',
};

export const cropLabel = (crop: string): string => CROP_LABELS[crop] ?? crop.replace(/_/g, ' ');

const CROP_SHORT: Record<string, string> = {
  corn: 'Corn',
  sorghum: 'Sorghum',
  winter_wheat: 'Wheat',
  alfalfa: 'Alfalfa',
  rye_cover: 'Rye cover',
  fallow: 'Fallow',
  grass_pasture: 'Grass',
  other_hay: 'Hay',
  other_crops: 'Other',
  winwht_corn: 'Wht/corn',
  triticale_corn: 'Trit/corn',
  winwht_sorghum: 'Wht/sorg',
  winwht_soybeans: 'Wht/soy',
};

/** Compact label for dense tables (print year grid). */
export const cropShort = (crop: string | undefined): string =>
  crop ? (CROP_SHORT[crop] ?? cropLabel(crop)) : '—';
