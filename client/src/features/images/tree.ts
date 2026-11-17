/**
 * Contenu des dossiers et recherche de la bibliothèque d'images (04b).
 * L'arborescence elle-même vient de `@/shared/tree`.
 */
import { byName, nodePath } from "@/shared/tree";

import type { ImageFolder, LibraryImage } from "./api";

/** Comparaison de textes sans tenir compte de la casse ni des accents. */
function normalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

export { childrenOf, nodePath as folderPath, isWithin } from "@/shared/tree";

/** Images rangées directement dans ce dossier ; `null` : toutes les images. */
export function imagesIn(images: readonly LibraryImage[], folderId: string | null): LibraryImage[] {
  const shown = folderId === null ? [...images] : images.filter((i) => i.folderId === folderId);
  return shown.sort(byName);
}

/** Nombre d'images rangées directement dans chaque dossier (Q04b-5). */
export function imageCounts(images: readonly LibraryImage[]): Map<string, number> {
  const counts = new Map<string, number>();
  for (const image of images) {
    if (image.folderId !== null) {
      counts.set(image.folderId, (counts.get(image.folderId) ?? 0) + 1);
    }
  }
  return counts;
}

/**
 * Filtre les images sur leur nom ET sur le nom de leurs dossiers, dans tous les
 * dossiers (04b-I8). Une recherche vide ne retourne rien.
 */
export function searchImages(
  images: readonly LibraryImage[],
  folders: readonly ImageFolder[],
  query: string,
): LibraryImage[] {
  const wanted = normalize(query.trim());
  if (wanted === "") {
    return [];
  }
  return images
    .filter((image) => {
      const names = [image.name, ...nodePath(folders, image.folderId).map((f) => f.name)];
      return names.some((name) => normalize(name).includes(wanted));
    })
    .sort(byName);
}
