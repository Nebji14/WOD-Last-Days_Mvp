/** Appels API des images : bibliothèque du MJ (04b) et images de la table (03-A2). */
import { ApiError, apiRequest, isRecord, uploadFile } from "@/shared/api/client";

export interface ImageFolder {
  readonly id: string;
  readonly name: string;
  readonly parentId: string | null;
}

export interface LibraryImage {
  readonly id: string;
  readonly name: string;
  readonly folderId: string | null;
  /** Lien de lecture signé, à durée limitée ; `null` si le fichier est introuvable. */
  readonly url: string | null;
  readonly isShown: boolean;
  readonly onTable: boolean;
}

export interface Library {
  readonly folders: readonly ImageFolder[];
  readonly images: readonly LibraryImage[];
}

export interface TableScene {
  readonly shown: LibraryImage | null;
  /** Images posées, la plus récente en premier. */
  readonly pile: readonly LibraryImage[];
}

const invalid = (): ApiError => new ApiError(502, "internal_error");
const isNullableString = (value: unknown): value is string | null =>
  value === null || typeof value === "string";

export function parseImage(data: unknown): LibraryImage {
  if (
    isRecord(data) &&
    typeof data.id === "string" &&
    typeof data.name === "string" &&
    isNullableString(data.folder_id) &&
    isNullableString(data.url) &&
    typeof data.is_shown === "boolean" &&
    isNullableString(data.on_table_at)
  ) {
    return {
      id: data.id,
      name: data.name,
      folderId: data.folder_id,
      url: data.url,
      isShown: data.is_shown,
      onTable: data.on_table_at !== null,
    };
  }
  throw invalid();
}

function parseFolder(data: unknown): ImageFolder {
  if (
    isRecord(data) &&
    typeof data.id === "string" &&
    typeof data.name === "string" &&
    isNullableString(data.parent_id)
  ) {
    return { id: data.id, name: data.name, parentId: data.parent_id };
  }
  throw invalid();
}

function parseLibrary(data: unknown): Library {
  if (isRecord(data) && Array.isArray(data.folders) && Array.isArray(data.images)) {
    return { folders: data.folders.map(parseFolder), images: data.images.map(parseImage) };
  }
  throw invalid();
}

export function parseScene(data: unknown): TableScene {
  if (isRecord(data) && Array.isArray(data.pile)) {
    return {
      shown: data.shown === null ? null : parseImage(data.shown),
      pile: data.pile.map(parseImage),
    };
  }
  throw invalid();
}

function parseCreated(data: unknown): string {
  if (isRecord(data) && typeof data.id === "string") {
    return data.id;
  }
  throw invalid();
}

// --- Bibliothèque (MJ) ------------------------------------------------------------------

export function fetchLibrary(): Promise<Library> {
  return apiRequest("/api/images", { parse: parseLibrary });
}

/** Ajoute une image au dossier ouvert, avec progression de l'envoi (04b-I1). */
export function uploadImage(
  file: File,
  folderId: string | null,
  onProgress: (ratio: number) => void,
): Promise<LibraryImage> {
  const query = new URLSearchParams({ filename: file.name });
  if (folderId !== null) {
    query.set("folder_id", folderId);
  }
  return uploadFile(`/api/images?${query.toString()}`, file, onProgress, parseImage);
}

export function renameImage(imageId: string, name: string): Promise<void> {
  return apiRequest(`/api/images/${imageId}`, { method: "PATCH", body: { name } });
}

export function moveImage(imageId: string, folderId: string | null): Promise<void> {
  return apiRequest(`/api/images/${imageId}/folder`, {
    method: "PUT",
    body: { folder_id: folderId },
  });
}

export function deleteImage(imageId: string): Promise<void> {
  return apiRequest(`/api/images/${imageId}`, { method: "DELETE" });
}

export function createFolder(name: string, parentId: string | null): Promise<string> {
  return apiRequest("/api/image-folders", {
    method: "POST",
    body: { name, parent_id: parentId },
    parse: parseCreated,
  });
}

export function renameFolder(folderId: string, name: string): Promise<void> {
  return apiRequest(`/api/image-folders/${folderId}`, { method: "PATCH", body: { name } });
}

export function moveFolder(folderId: string, parentId: string | null): Promise<void> {
  return apiRequest(`/api/image-folders/${folderId}/parent`, {
    method: "PUT",
    body: { parent_id: parentId },
  });
}

export function deleteFolder(folderId: string): Promise<void> {
  return apiRequest(`/api/image-folders/${folderId}`, { method: "DELETE" });
}

// --- Table ------------------------------------------------------------------------------

export function fetchScene(): Promise<TableScene> {
  return apiRequest("/api/table/images", { parse: parseScene });
}

export function showImage(imageId: string): Promise<void> {
  return apiRequest(`/api/table/images/${imageId}/show`, { method: "POST" });
}

export function putDownImage(): Promise<void> {
  return apiRequest("/api/table/images/put-down", { method: "POST" });
}

export function removeFromTable(imageId: string): Promise<void> {
  return apiRequest(`/api/table/images/${imageId}`, { method: "DELETE" });
}
