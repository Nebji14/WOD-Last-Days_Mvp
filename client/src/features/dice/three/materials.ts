/**
 * Apparence des dés : cuivre et chiffres ivoire pour les joueurs, obsidienne et
 * chiffres dorés pour le MJ. Une texture par face, dessinée une seule fois.
 */
import { CanvasTexture, Color, MeshStandardMaterial, SRGBColorSpace } from "three";

import { FACE_COUNT, faceValue } from "./d10";

export type DieStyle = "player" | "gm";

interface Palette {
  readonly body: string;
  readonly edge: string;
  readonly ink: string;
  readonly roughness: number;
  readonly metalness: number;
}

const PALETTES: Record<DieStyle, Palette> = {
  player: { body: "#9a5a33", edge: "#5e3119", ink: "#f3e3c3", roughness: 0.35, metalness: 0.55 },
  gm: { body: "#17110f", edge: "#050303", ink: "#d9bd6a", roughness: 0.2, metalness: 0.3 },
};

const TEXTURE_SIZE = 256;
const SUCCESS_GLOW = new Color("#e6b45a");

function faceTexture(value: number, palette: Palette): CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = TEXTURE_SIZE;
  canvas.height = TEXTURE_SIZE;
  const context = canvas.getContext("2d");
  if (context !== null) {
    const half = TEXTURE_SIZE / 2;
    const gradient = context.createRadialGradient(half, half, 10, half, half, half * 1.2);
    gradient.addColorStop(0, palette.body);
    gradient.addColorStop(1, palette.edge);
    context.fillStyle = gradient;
    context.fillRect(0, 0, TEXTURE_SIZE, TEXTURE_SIZE);
    context.fillStyle = palette.ink;
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.font = `bold ${value === 10 ? 74 : 92}px Georgia, "Times New Roman", serif`;
    context.fillText(String(value), half, half + 6);
    // 6 et 9 se lisent dans les deux sens : un trait les distingue.
    if (value === 6 || value === 9) {
      context.fillRect(half - 22, half + 50, 44, 7);
    }
  }
  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace;
  texture.anisotropy = 4;
  return texture;
}

const cache = new Map<DieStyle, readonly MeshStandardMaterial[]>();

/** Matériaux partagés des dix faces d'un style. */
export function faceMaterials(style: DieStyle): readonly MeshStandardMaterial[] {
  const known = cache.get(style);
  if (known !== undefined) {
    return known;
  }
  const palette = PALETTES[style];
  const materials = Array.from(
    { length: FACE_COUNT },
    (_, face) =>
      new MeshStandardMaterial({
        map: faceTexture(faceValue(face), palette),
        roughness: palette.roughness,
        metalness: palette.metalness,
      }),
  );
  cache.set(style, materials);
  return materials;
}

/**
 * Matériaux propres à un dé du gros plan : une réussite brille, un échec
 * s'assombrit.
 */
export function highlightedMaterials(style: DieStyle, success: boolean): MeshStandardMaterial[] {
  return faceMaterials(style).map((material) => {
    const copy = material.clone();
    if (success) {
      copy.emissive = SUCCESS_GLOW;
      copy.emissiveIntensity = 0.35;
    } else {
      copy.color = new Color("#6d6d6d");
    }
    return copy;
  });
}
