/** Jet de dés tel qu'il arrive du serveur, et lecture de ses faces. */
import { isRecord } from "@/shared/api/client";

export type RollKind = "pool" | "initiative" | "consciousness" | "trait" | "free";
export type Outcome = "dramatic_failure" | "failure" | "success" | "exceptional";

export interface RollPart {
  readonly key: string;
  readonly value: number;
}

export interface Roll {
  readonly id: string;
  readonly roller_id: string;
  readonly roller_role: "player" | "gm";
  readonly roller_name: string;
  readonly character_id: string | null;
  readonly kind: RollKind;
  readonly parts: readonly RollPart[];
  readonly chance: boolean;
  readonly again: number;
  readonly rote: boolean;
  readonly secret: boolean;
  /** Faces de chaque vague : le lancer, puis les relances. */
  readonly stages: readonly (readonly number[])[];
  /** Dés qui restent à relancer ; 0 quand le jet est terminé. */
  readonly pending: number;
  readonly successes: number;
  readonly outcome: Outcome | null;
  readonly total: number | null;
}

const SUCCESS_THRESHOLD = 8;
const KINDS: readonly RollKind[] = ["pool", "initiative", "consciousness", "trait", "free"];

function isFaces(value: unknown): value is readonly number[] {
  return Array.isArray(value) && value.every((face) => typeof face === "number");
}

/** Valide un jet reçu ; `null` s'il est mal formé. */
export function parseRoll(data: unknown): Roll | null {
  if (
    !isRecord(data) ||
    typeof data.id !== "string" ||
    typeof data.roller_id !== "string" ||
    (data.roller_role !== "player" && data.roller_role !== "gm") ||
    typeof data.roller_name !== "string" ||
    !KINDS.includes(data.kind as RollKind) ||
    !Array.isArray(data.parts) ||
    !Array.isArray(data.stages) ||
    !data.stages.every(isFaces) ||
    typeof data.pending !== "number" ||
    typeof data.successes !== "number"
  ) {
    return null;
  }
  return data as unknown as Roll;
}

/** Le dé réussit : 8 et plus, ou seulement 10 pour un dé de chance. */
export function isSuccess(face: number, chance: boolean): boolean {
  return chance ? face === 10 : face >= SUCCESS_THRESHOLD;
}

/** Le dé repart à la vague suivante (10, ou 9 et 8 avec les options). */
export function isReroll(face: number, roll: Roll): boolean {
  return roll.kind !== "initiative" && face >= (roll.chance ? 10 : roll.again);
}

/** Réserve affichée : somme des éléments, 0 au minimum. */
export function poolSize(parts: readonly RollPart[]): number {
  return Math.max(
    0,
    parts.reduce((sum, part) => sum + part.value, 0),
  );
}
