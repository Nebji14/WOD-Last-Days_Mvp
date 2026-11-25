/** Parcours des images posées sur la table, dans la vue en grand. */
import type { LibraryImage } from "./api";

/**
 * Image voisine dans la pile, en repartant de l'autre bout à la fin.
 *
 * @param step `1` pour la suivante, `-1` pour la précédente.
 * @returns `null` si l'image n'est plus dans la pile.
 */
export function neighbour(
  pile: readonly LibraryImage[],
  imageId: string,
  step: 1 | -1,
): LibraryImage | null {
  const index = pile.findIndex((image) => image.id === imageId);
  return index < 0 ? null : (pile[(index + step + pile.length) % pile.length] ?? null);
}
