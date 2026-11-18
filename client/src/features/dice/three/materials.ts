/**
 * Apparence des dés, dessinée face par face.
 *
 * Joueurs : bronze cuivré brossé, rayures, vert-de-gris dans les creux,
 * chiffres gravés et remplis d'émail ivoire.
 * MJ : obsidienne vernie, veinée d'or et de rouge, chiffres à la feuille d'or.
 *
 * Chaque face reçoit quatre textures : couleur, relief (chiffre creusé, arêtes
 * adoucies), rugosité et métal (le métal brille, l'émail et la pierre non).
 */
import {
  CanvasTexture,
  Color,
  MeshPhysicalMaterial,
  NoColorSpace,
  SRGBColorSpace,
  type Texture,
} from "three";

import { FACE_COUNT, faceUvs, faceValue } from "./d10";

export type DieStyle = "player" | "gm";

const COLOR_SIZE = 768;
const DETAIL_SIZE = 512;
const SUCCESS_GLOW = new Color("#e6b45a");

type Draw = (context: CanvasRenderingContext2D, size: number) => void;

/** Tirage reproductible : chaque face garde le même grain d'une partie à l'autre. */
function seeded(seed: number): () => number {
  let state = seed * 7919 + 104729;
  return () => {
    state = (state * 16807) % 2147483647;
    return state / 2147483647;
  };
}

function texture(size: number, color: boolean, draw: Draw): CanvasTexture {
  const element = document.createElement("canvas");
  element.width = size;
  element.height = size;
  const context = element.getContext("2d");
  if (context !== null) {
    draw(context, size);
  }
  const result = new CanvasTexture(element);
  result.colorSpace = color ? SRGBColorSpace : NoColorSpace;
  result.anisotropy = 8;
  return result;
}

/** Contour de la face (la texture est retournée : v monte vers le haut). */
function facePath(context: CanvasRenderingContext2D, face: number, size: number): void {
  context.beginPath();
  faceUvs(face).forEach(([u, v], index) => {
    const [x, y] = [u * size, (1 - v) * size];
    if (index === 0) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });
  context.closePath();
}

function numberShape(context: CanvasRenderingContext2D, value: number, size: number): void {
  const half = size / 2;
  const scale = size / 512;
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.font = `bold ${(value === 10 ? 150 : 182) * scale}px Georgia, "Times New Roman", serif`;
  context.fillText(String(value), half, half + 10 * scale);
  // 6 et 9 se lisent dans les deux sens : un trait les distingue.
  if (value === 6 || value === 9) {
    context.fillRect(half - 42 * scale, half + 104 * scale, 84 * scale, 12 * scale);
  }
}

/** Chiffre gravé : creux sombre, remplissage, reflet sur la lèvre haute. */
function engrave(
  context: CanvasRenderingContext2D,
  value: number,
  size: number,
  fill: CanvasGradient | string,
): void {
  const scale = size / 512;
  context.save();
  context.fillStyle = "rgb(0 0 0 / 0.75)";
  context.translate(5 * scale, 6 * scale);
  numberShape(context, value, size);
  context.restore();
  context.save();
  context.fillStyle = "rgb(255 255 255 / 0.25)";
  context.translate(-2 * scale, -2 * scale);
  numberShape(context, value, size);
  context.restore();
  context.fillStyle = fill;
  numberShape(context, value, size);
}

/** Biseau : ombre juste à l'intérieur de l'arête, liseré de lumière sur l'arête. */
function bevel(context: CanvasRenderingContext2D, face: number, size: number, light: string): void {
  const scale = size / 512;
  facePath(context, face, size);
  context.lineJoin = "round";
  context.strokeStyle = "rgb(0 0 0 / 0.5)";
  context.lineWidth = 40 * scale;
  context.stroke();
  context.strokeStyle = light;
  context.lineWidth = 10 * scale;
  context.stroke();
}

// --- Joueurs : bronze cuivré -----------------------------------------------------------

function bronzeColor(face: number): Draw {
  return (context, size) => {
    const random = seeded(face + 1);
    const half = size / 2;
    const body = context.createRadialGradient(half * 0.8, half * 0.7, 10, half, half, size * 0.62);
    body.addColorStop(0, "#b8714a");
    body.addColorStop(0.55, "#8c4a2f");
    body.addColorStop(1, "#3b1a0e");
    context.fillStyle = body;
    context.fillRect(0, 0, size, size);
    // Brossage du métal : traits fins presque horizontaux.
    for (let index = 0; index < 1400; index += 1) {
      const y = random() * size;
      const x = random() * size;
      context.strokeStyle = random() > 0.5 ? "rgb(255 210 180 / 0.05)" : "rgb(40 15 5 / 0.07)";
      context.lineWidth = random() * 1.6 + 0.4;
      context.beginPath();
      context.moveTo(x, y);
      context.lineTo(x + 40 + random() * 120, y + (random() - 0.5) * 6);
      context.stroke();
    }
    // Rayures d'usage.
    for (let index = 0; index < 26; index += 1) {
      const x = random() * size;
      const y = random() * size;
      context.strokeStyle = "rgb(255 225 200 / 0.18)";
      context.lineWidth = 1.2;
      context.beginPath();
      context.moveTo(x, y);
      context.quadraticCurveTo(
        x + (random() - 0.5) * 80,
        y + (random() - 0.5) * 80,
        x + (random() - 0.5) * 160,
        y + (random() - 0.5) * 160,
      );
      context.stroke();
    }
    // Vert-de-gris déposé le long des arêtes.
    facePath(context, face, size);
    context.lineJoin = "round";
    context.strokeStyle = "rgb(70 120 95 / 0.22)";
    context.lineWidth = 70 * (size / 512);
    context.stroke();
    bevel(context, face, size, "rgb(255 205 165 / 0.55)");
    const enamel = context.createLinearGradient(0, half - size * 0.18, 0, half + size * 0.18);
    enamel.addColorStop(0, "#fbf1dc");
    enamel.addColorStop(1, "#d8c7a6");
    engrave(context, faceValue(face), size, enamel);
  };
}

// --- MJ : obsidienne veinée d'or -------------------------------------------------------

function obsidianColor(face: number): Draw {
  return (context, size) => {
    const random = seeded(face + 101);
    const half = size / 2;
    const body = context.createRadialGradient(
      half * 0.75,
      half * 0.65,
      10,
      half,
      half,
      size * 0.65,
    );
    body.addColorStop(0, "#2b1418");
    body.addColorStop(0.5, "#130a0c");
    body.addColorStop(1, "#030102");
    context.fillStyle = body;
    context.fillRect(0, 0, size, size);
    // Veines : un halo rouge, puis un filet d'or.
    for (let vein = 0; vein < 5; vein += 1) {
      const point = (): [number, number] => [random() * size, random() * size];
      const [start, control1, control2, end] = [point(), point(), point(), point()];
      const trace = () => {
        context.beginPath();
        context.moveTo(...start);
        context.bezierCurveTo(...control1, ...control2, ...end);
        context.stroke();
      };
      context.strokeStyle = "rgb(150 20 18 / 0.28)";
      context.lineWidth = 10 + random() * 10;
      trace();
      context.strokeStyle = "rgb(230 190 100 / 0.55)";
      context.lineWidth = 1 + random() * 1.8;
      trace();
    }
    bevel(context, face, size, "rgb(232 196 110 / 0.7)");
    const gold = context.createLinearGradient(0, half - size * 0.18, 0, half + size * 0.18);
    gold.addColorStop(0, "#fff0b0");
    gold.addColorStop(0.45, "#e2b54e");
    gold.addColorStop(1, "#8e6420");
    engrave(context, faceValue(face), size, gold);
  };
}

// --- Relief, rugosité, métal -----------------------------------------------------------

function bumpDraw(face: number): Draw {
  return (context, size) => {
    context.fillStyle = "#909090";
    context.fillRect(0, 0, size, size);
    facePath(context, face, size);
    context.lineJoin = "round";
    context.strokeStyle = "#404040";
    context.lineWidth = 34 * (size / 512);
    context.stroke();
    context.fillStyle = "#151515";
    numberShape(context, faceValue(face), size);
  };
}

/** Gris uniforme pour la face, autre gris pour le chiffre. */
function twoTone(face: number, body: string, number: string): Draw {
  return (context, size) => {
    context.fillStyle = body;
    context.fillRect(0, 0, size, size);
    context.fillStyle = number;
    numberShape(context, faceValue(face), size);
  };
}

interface StyleSpec {
  readonly color: (face: number) => Draw;
  /** Rugosité de la face, puis du chiffre (noir = lisse). */
  readonly roughness: readonly [string, string];
  /** Métal de la face, puis du chiffre (blanc = métal). */
  readonly metal: readonly [string, string];
  readonly clearcoat: number;
}

const STYLES: Record<DieStyle, StyleSpec> = {
  player: {
    color: bronzeColor,
    roughness: ["#5c5c5c", "#9c9c9c"],
    metal: ["#ffffff", "#101010"],
    clearcoat: 0.2,
  },
  gm: {
    color: obsidianColor,
    roughness: ["#262626", "#3a3a3a"],
    metal: ["#141414", "#ffffff"],
    clearcoat: 1,
  },
};

const cache = new Map<DieStyle, readonly MeshPhysicalMaterial[]>();

function material(style: StyleSpec, face: number): MeshPhysicalMaterial {
  const detail = (draw: Draw): Texture => texture(DETAIL_SIZE, false, draw);
  return new MeshPhysicalMaterial({
    map: texture(COLOR_SIZE, true, style.color(face)),
    bumpMap: detail(bumpDraw(face)),
    bumpScale: 2.6,
    roughnessMap: detail(twoTone(face, ...style.roughness)),
    roughness: 1,
    metalnessMap: detail(twoTone(face, ...style.metal)),
    metalness: 1,
    clearcoat: style.clearcoat,
    clearcoatRoughness: 0.12,
    envMapIntensity: 1.2,
  });
}

/** Matériaux partagés des dix faces d'un style. */
export function faceMaterials(style: DieStyle): readonly MeshPhysicalMaterial[] {
  const known = cache.get(style);
  if (known !== undefined) {
    return known;
  }
  const materials = Array.from({ length: FACE_COUNT }, (_, face) => material(STYLES[style], face));
  cache.set(style, materials);
  return materials;
}

/**
 * Matériaux propres à un dé du gros plan : une réussite brille, un échec
 * s'assombrit.
 */
export function highlightedMaterials(style: DieStyle, success: boolean): MeshPhysicalMaterial[] {
  return faceMaterials(style).map((source) => {
    const copy = source.clone();
    if (success) {
      copy.emissive = SUCCESS_GLOW;
      copy.emissiveMap = copy.map;
      copy.emissiveIntensity = 0.4;
    } else {
      copy.color = new Color("#5c5c5c");
      copy.envMapIntensity = 0.4;
    }
    return copy;
  });
}
