/**
 * Glisser-déposer interne de la bibliothèque (04b-I10) : une vignette ou un
 * dossier glissé sur une ligne de l'arborescence. Les fichiers venant de
 * l'ordinateur passent par la zone de dépôt (04b-I1).
 */
import type { DragEvent } from "react";

const IMAGE_TYPE = "application/x-hunter-image";
const FOLDER_TYPE = "application/x-hunter-folder";

export type DraggedItem =
  | { readonly kind: "image"; readonly id: string }
  | { readonly kind: "folder"; readonly id: string };

export function startDrag(event: DragEvent, item: DraggedItem): void {
  event.dataTransfer.setData(item.kind === "image" ? IMAGE_TYPE : FOLDER_TYPE, item.id);
  event.dataTransfer.effectAllowed = "move";
}

/** Un élément de la bibliothèque est en cours de glisser (et non un fichier). */
export function carriesItem(event: DragEvent): boolean {
  const types = Array.from(event.dataTransfer.types);
  return types.includes(IMAGE_TYPE) || types.includes(FOLDER_TYPE);
}

export function droppedItem(event: DragEvent): DraggedItem | null {
  const imageId = event.dataTransfer.getData(IMAGE_TYPE);
  if (imageId !== "") {
    return { kind: "image", id: imageId };
  }
  const folderId = event.dataTransfer.getData(FOLDER_TYPE);
  return folderId === "" ? null : { kind: "folder", id: folderId };
}
