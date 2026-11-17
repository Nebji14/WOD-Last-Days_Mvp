/**
 * Arborescence des dossiers et recherche de la bibliothèque d'images (04b).
 *
 * Fonctions pures : le serveur reste seul garant des règles (dossier sans
 * cycle), le client les reflète pour l'ergonomie.
 */
import type { ImageFolder, LibraryImage } from "./api";

/** Comparaison de noms sans tenir compte de la casse ni des accents. */
function normalize(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}

const byName = (left: { name: string }, right: { name: string }): number =>
  left.name.localeCompare(right.name, "fr", { sensitivity: "base" });

/** Sous-dossiers directs d'un dossier (`null` : racine), par nom. */
export function childrenOf(
  folders: readonly ImageFolder[],
  parentId: string | null,
): ImageFolder[] {
  return folders.filter((folder) => folder.parentId === parentId).sort(byName);
}

/** Images rangées directement dans ce dossier ; `null` : toutes les images. */
export function imagesIn(
  images: readonly LibraryImage[],
  folderId: string | null,
): LibraryImage[] {
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

/** Chemin d'un dossier, de la racine jusqu'à lui ([Fil d'Ariane]). */
export function folderPath(folders: readonly ImageFolder[], folderId: string | null): ImageFolder[] {
  const byId = new Map(folders.map((folder) => [folder.id, folder]));
  const path: ImageFolder[] = [];
  let current = folderId === null ? undefined : byId.get(folderId);
  while (current !== undefined && !path.includes(current)) {
    path.unshift(current);
    current = current.parentId === null ? undefined : byId.get(current.parentId);
  }
  return path;
}

/** Indique si `candidateId` est `folderId` lui-même ou l'un de ses descendants (04b-I10). */
export function isWithin(
  folders: readonly ImageFolder[],
  folderId: string,
  candidateId: string | null,
): boolean {
  return folderPath(folders, candidateId).some((folder) => folder.id === folderId);
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
      const names = [image.name, ...folderPath(folders, image.folderId).map((f) => f.name)];
      return names.some((name) => normalize(name).includes(wanted));
    })
    .sort(byName);
}
