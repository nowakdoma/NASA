// Crop colours loosely follow the USDA CDL legend so farmers recognise them.
export const CROP_COLORS: Record<string, [number, number, number]> = {
  corn: [255, 211, 0],
  sorghum: [255, 158, 10],
  winter_wheat: [166, 112, 0],
  soybeans: [38, 112, 0],
  alfalfa: [255, 168, 227],
  cotton: [255, 38, 38],
  sunflower: [255, 255, 0],
  rye_cover: [172, 0, 124],
  fallow: [191, 191, 122],
  grass_pasture: [232, 255, 191],
};
const UNKNOWN: [number, number, number] = [150, 150, 150];

export const cropColor = (crop: string | undefined): [number, number, number] =>
  (crop && CROP_COLORS[crop]) || UNKNOWN;

export const cropCss = (crop: string | undefined): string => `rgb(${cropColor(crop).join(',')})`;

export const cropLabel = (crop: string): string =>
  ({ winter_wheat: 'winter wheat', rye_cover: 'rye cover', grass_pasture: 'grass/pasture' })[
    crop
  ] ?? crop;
