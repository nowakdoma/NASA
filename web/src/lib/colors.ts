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
