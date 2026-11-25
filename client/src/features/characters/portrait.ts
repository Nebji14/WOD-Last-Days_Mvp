/**
 * Portrait d'une forme : préparation de l'image choisie, envoi et retrait.
 *
 * L'image est réduite dans le navigateur, ce qui efface aussi ses données
 * cachées (lieu, appareil). Deux fichiers sont envoyés : le portrait cadré,
 * affiché partout, et la photo entière, relue pour recadrer plus tard.
 */
import { ApiError, apiRequest, fetchBlob, uploadFile } from "@/shared/api/client";

import { type Character, parseCharacter } from "./model";
import type { SquareCrop } from "./portraitCrop";

/** Formats proposés dans le choix de fichier. */
export const PORTRAIT_ACCEPT = "image/png,image/jpeg,image/webp,image/gif";

const PORTRAIT_SIZE = 512;
const ORIGINAL_MAX_SIDE = 1600;
const QUALITY = 0.85;

/** Photo à cadrer : le fichier à conserver et son image décodée. */
export interface PortraitSource {
  readonly original: Blob;
  readonly bitmap: ImageBitmap;
}

/** Fichiers prêts à l'envoi. */
export interface PortraitFiles {
  readonly portrait: Blob;
  readonly original: Blob;
}

async function decode(file: Blob): Promise<ImageBitmap> {
  try {
    return await createImageBitmap(file);
  } catch {
    throw new ApiError(415, "unsupported_image");
  }
}

/** Dessine une partie de l'image à la taille voulue et l'encode. */
async function encode(
  bitmap: ImageBitmap,
  area: { readonly x: number; readonly y: number; readonly width: number; readonly height: number },
  width: number,
  height: number,
): Promise<Blob> {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  canvas
    .getContext("2d")
    ?.drawImage(bitmap, area.x, area.y, area.width, area.height, 0, 0, width, height);
  const blob = await new Promise<Blob | null>((resolve) =>
    canvas.toBlob(resolve, "image/webp", QUALITY),
  );
  if (blob === null) {
    throw new ApiError(415, "unsupported_image");
  }
  return blob;
}

/** Ouvre une photo choisie sur l'appareil. */
export async function openFile(file: File): Promise<PortraitSource> {
  const full = await decode(file);
  const scale = Math.min(1, ORIGINAL_MAX_SIDE / Math.max(full.width, full.height));
  const original = await encode(
    full,
    { x: 0, y: 0, width: full.width, height: full.height },
    Math.max(1, Math.round(full.width * scale)),
    Math.max(1, Math.round(full.height * scale)),
  );
  full.close();
  return { original, bitmap: await decode(original) };
}

/**
 * Rouvre la photo d'un portrait déjà enregistré, pour la recadrer. À défaut de
 * photo entière, reprend le portrait cadré.
 */
export async function openExisting(name: string): Promise<PortraitSource> {
  const path = `/api/portraits/${name}`;
  const original = await fetchBlob(`${path}/original`).catch((error: unknown) => {
    if (error instanceof ApiError && error.status === 404) {
      return fetchBlob(path);
    }
    throw error;
  });
  return { original, bitmap: await decode(original) };
}

/** Prépare les fichiers à envoyer, d'après le cadre choisi. */
export async function cropPortrait(
  source: PortraitSource,
  crop: SquareCrop,
): Promise<PortraitFiles> {
  const size = Math.max(1, Math.min(PORTRAIT_SIZE, Math.round(crop.side)));
  const area = { x: crop.x, y: crop.y, width: crop.side, height: crop.side };
  return {
    portrait: await encode(source.bitmap, area, size, size),
    original: source.original,
  };
}

const ignoreProgress = (): void => undefined;

/**
 * Garde la photo entière d'un portrait. Un échec n'annule pas le portrait déjà
 * enregistré : seul un recadrage ultérieur sera limité.
 */
export async function keepOriginal(name: string | null, original: Blob): Promise<void> {
  if (name === null) {
    return;
  }
  try {
    await uploadFile(
      `/api/portraits/${name}/original`,
      original,
      ignoreProgress,
      () => undefined,
      "PUT",
    );
  } catch (error) {
    console.warn("Photo entière non conservée", error);
  }
}

/** Envoie un portrait cadré et retourne la réponse validée. */
export function uploadPortrait<T>(
  path: string,
  portrait: Blob,
  parse: (data: unknown) => T,
): Promise<T> {
  return uploadFile(path, portrait, ignoreProgress, parse, "PUT");
}

/** Donne une image à une forme, à la place de la précédente. */
export async function setPortrait(sheetId: string, files: PortraitFiles): Promise<Character> {
  const character = await uploadPortrait(
    `/api/sheets/${sheetId}/portrait`,
    files.portrait,
    parseCharacter,
  );
  const sheet = character.sheets.find((candidate) => candidate.id === sheetId);
  await keepOriginal(sheet?.portrait ?? null, files.original);
  return character;
}

/** Retire l'image d'une forme. */
export function removePortrait(sheetId: string): Promise<Character> {
  return apiRequest(`/api/sheets/${sheetId}/portrait`, {
    method: "DELETE",
    parse: parseCharacter,
  });
}
