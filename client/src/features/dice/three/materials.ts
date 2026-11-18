/**
 * Apparence des dés : bronze patiné et chiffres ivoire pour les joueurs,
 * obsidienne vernie et chiffres dorés pour le MJ.
 *
 * Chaque face reçoit une texture dessinée une fois : arêtes biseautées
 * (lumière sur le bord, ombre juste dedans), patine, chiffre gravé. Une
 * seconde texture en niveaux de gris creuse le chiffre et adoucit les arêtes
 * sous la lumière.
 */
import { CanvasTexture, Color, MeshPhysicalMaterial, NoColorSpace, SRGBColorSpace } from "three";

import { FACE_COUNT, faceUvs, faceValue } from "./d10";

export type DieStyle = "player" | "gm";

interface Palette {
  readonly body: string;
  readonly core: string;
  readonly edge: string;
  readonly bevelLight: string;
  readonly speckle: string;
  readonly inkLight: string;
  readonly inkDark: string;
  readonly roughness: number;
  readonly metalness: number;
  readonly clearcoat: number;
}

const PALETTES: Record<DieStyle, Palette> = {
  player: {
    body: "#a5683b",
    core: "#c58a55",
    edge: "#4a2412",
    bevelLight: "rgb(255 214 170 / 0.55)",
    speckle: "rgb(70 95 70 / 0.16)",
    inkLight: "#fff3da",
    inkDark: "#d9bf93",
    roughness: 0.38,
    metalness: 0.7,
    clearcoat: 0.25,
  },
  gm: {
    body: "#1c1315",
    core: "#2e1d20",
    edge: "#040202",
    bevelLight: "rgb(217 189 106 / 0.45)",
    speckle: "rgb(150 25 20 / 0.14)",
    inkLight: "#f7e08f",
    inkDark: "#a8812f",
    roughness: 0.18,
    metalness: 0.25,
    clearcoat: 1,
  },
};

const SIZE = 512;
const SUCCESS_GLOW = new Color("#e6b45a");

/** Contour de la face sur la texture (la texture est retournée : v monte vers le haut). */
function facePath(context: CanvasRenderingContext2D, face: number): void {
  context.beginPath();
  faceUvs(face).forEach(([u, v], index) => {
    const x = u * SIZE;
    const y = (1 - v) * SIZE;
    if (index === 0) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });
  context.closePath();
}

/** Grain du métal ou de la pierre : petites taches réparties au hasard. */
function speckles(context: CanvasRenderingContext2D, color: string, seed: number): void {
  let state = seed * 9301 + 49297;
  const random = () => {
    state = (state * 9301 + 49297) % 233280;
    return state / 233280;
  };
  context.fillStyle = color;
  for (let index = 0; index < 900; index += 1) {
    const radius = random() * 3.2 + 0.4;
    context.beginPath();
    context.arc(random() * SIZE, random() * SIZE, radius, 0, Math.PI * 2);
    context.fill();
  }
}

function canvas(): [HTMLCanvasElement, CanvasRenderingContext2D | null] {
  const element = document.createElement("canvas");
  element.width = SIZE;
  element.height = SIZE;
  return [element, element.getContext("2d")];
}

function writeNumber(context: CanvasRenderingContext2D, value: number): void {
  const half = SIZE / 2;
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.font = `bold ${value === 10 ? 150 : 180}px Georgia, "Times New Roman", serif`;
  context.fillText(String(value), half, half + 10);
  // 6 et 9 se lisent dans les deux sens : un trait les distingue.
  if (value === 6 || value === 9) {
    context.fillRect(half - 42, half + 104, 84, 12);
  }
}

function colorTexture(face: number, palette: Palette): CanvasTexture {
  const [element, context] = canvas();
  if (context !== null) {
    const half = SIZE / 2;
    const body = context.createRadialGradient(half, half * 0.9, 20, half, half, half * 1.15);
    body.addColorStop(0, palette.core);
    body.addColorStop(0.6, palette.body);
    body.addColorStop(1, palette.edge);
    context.fillStyle = body;
    context.fillRect(0, 0, SIZE, SIZE);
    speckles(context, palette.speckle, face + 1);

    // Biseau : un liseré clair sur l'arête, une ombre juste à l'intérieur.
    facePath(context, face);
    context.lineJoin = "round";
    context.strokeStyle = "rgb(0 0 0 / 0.45)";
    context.lineWidth = 34;
    context.stroke();
    context.strokeStyle = palette.bevelLight;
    context.lineWidth = 12;
    context.stroke();

    // Chiffre gravé : creux sombre décalé, puis le chiffre en dégradé.
    const value = faceValue(face);
    context.fillStyle = "rgb(0 0 0 / 0.6)";
    context.save();
    context.translate(4, 5);
    writeNumber(context, value);
    context.restore();
    const ink = context.createLinearGradient(0, half - 90, 0, half + 90);
    ink.addColorStop(0, palette.inkLight);
    ink.addColorStop(1, palette.inkDark);
    context.fillStyle = ink;
    writeNumber(context, value);
  }
  const texture = new CanvasTexture(element);
  texture.colorSpace = SRGBColorSpace;
  texture.anisotropy = 8;
  return texture;
}

function bumpTexture(face: number): CanvasTexture {
  const [element, context] = canvas();
  if (context !== null) {
    context.fillStyle = "#808080";
    context.fillRect(0, 0, SIZE, SIZE);
    facePath(context, face);
    context.lineJoin = "round";
    context.strokeStyle = "#3a3a3a";
    context.lineWidth = 30;
    context.stroke();
    context.fillStyle = "#1a1a1a";
    writeNumber(context, faceValue(face));
  }
  const texture = new CanvasTexture(element);
  texture.colorSpace = NoColorSpace;
  return texture;
}

const cache = new Map<DieStyle, readonly MeshPhysicalMaterial[]>();

/** Matériaux partagés des dix faces d'un style. */
export function faceMaterials(style: DieStyle): readonly MeshPhysicalMaterial[] {
  const known = cache.get(style);
  if (known !== undefined) {
    return known;
  }
  const palette = PALETTES[style];
  const materials = Array.from(
    { length: FACE_COUNT },
    (_, face) =>
      new MeshPhysicalMaterial({
        map: colorTexture(face, palette),
        bumpMap: bumpTexture(face),
        bumpScale: 2.2,
        roughness: palette.roughness,
        metalness: palette.metalness,
        clearcoat: palette.clearcoat,
        clearcoatRoughness: 0.15,
        envMapIntensity: 1.1,
      }),
  );
  cache.set(style, materials);
  return materials;
}

/**
 * Matériaux propres à un dé du gros plan : une réussite brille, un échec
 * s'assombrit.
 */
export function highlightedMaterials(style: DieStyle, success: boolean): MeshPhysicalMaterial[] {
  return faceMaterials(style).map((material) => {
    const copy = material.clone();
    if (success) {
      copy.emissive = SUCCESS_GLOW;
      copy.emissiveMap = copy.map;
      copy.emissiveIntensity = 0.45;
    } else {
      copy.color = new Color("#5c5c5c");
      copy.envMapIntensity = 0.4;
    }
    return copy;
  });
}
