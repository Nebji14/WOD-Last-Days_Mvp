/**
 * Cadrage d'un portrait : carré choisi dans l'image, en pixels de l'image.
 *
 * Le cadre reste toujours entièrement dans l'image.
 */

export interface Size {
  readonly width: number;
  readonly height: number;
}

export interface SquareCrop {
  readonly x: number;
  readonly y: number;
  readonly side: number;
}

/** Grossissement maximal : le cadre couvre au moins un cinquième du petit côté. */
export const MAX_ZOOM = 5;

// Part de la hauteur en trop laissée au-dessus du cadre : sur une photo en
// hauteur, le visage est plus souvent en haut.
const TOP_SHARE = 0.25;

function clamp(value: number, low: number, high: number): number {
  return Math.min(Math.max(value, low), high);
}

function within(crop: SquareCrop, image: Size): SquareCrop {
  return {
    x: clamp(crop.x, 0, image.width - crop.side),
    y: clamp(crop.y, 0, image.height - crop.side),
    side: crop.side,
  };
}

/** Cadre proposé au départ : le plus grand carré, centré en largeur et plutôt haut. */
export function initialCrop(image: Size): SquareCrop {
  const side = Math.min(image.width, image.height);
  return {
    x: (image.width - side) / 2,
    y: (image.height - side) * TOP_SHARE,
    side,
  };
}

/** Déplace le cadre, sans sortir de l'image. */
export function moveCrop(crop: SquareCrop, dx: number, dy: number, image: Size): SquareCrop {
  return within({ ...crop, x: crop.x + dx, y: crop.y + dy }, image);
}

/** Grossissement du cadre : 1 pour le plus grand carré possible. */
export function zoomOf(crop: SquareCrop, image: Size): number {
  return Math.min(image.width, image.height) / crop.side;
}

/** Change le grossissement en gardant le centre du cadre autant que possible. */
export function zoomCrop(crop: SquareCrop, zoom: number, image: Size): SquareCrop {
  const side = Math.min(image.width, image.height) / clamp(zoom, 1, MAX_ZOOM);
  const shift = (crop.side - side) / 2;
  return within({ x: crop.x + shift, y: crop.y + shift, side }, image);
}
