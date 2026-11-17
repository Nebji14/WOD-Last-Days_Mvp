/**
 * Lecture de la piste de santé pour l'affichage : malus de blessure et état
 * critique. Le serveur reste seul à modifier la piste.
 */

/** Nombre de cases, en partant de la droite, qui portent un malus. */
export const PENALTY_BOXES = 3;

/**
 * Malus de la case `index` (0 = la plus à gauche) : −1, −2 puis −3 sur les
 * trois dernières cases, 0 ailleurs.
 */
export function boxPenalty(index: number, capacity: number): number {
  const fromRight = capacity - index;
  return fromRight <= PENALTY_BOXES ? fromRight - PENALTY_BOXES - 1 : 0;
}

/**
 * Malus de blessure en cours : celui de la case blessée la plus à droite.
 * Les malus ne se cumulent pas.
 */
export function woundPenalty(track: string, capacity: number): number {
  return track.length === 0 ? 0 : boxPenalty(track.length - 1, capacity);
}

export type HealthState = "fine" | "unconscious" | "bleeding" | "dead";

/**
 * État critique d'après la dernière case : contondante, jet de Vigueur pour
 * rester conscient ; létale, hémorragie ; tout aggravé, mort.
 */
export function healthState(track: string, capacity: number): HealthState {
  if (track.length < capacity || capacity === 0) {
    return "fine";
  }
  const last = track[capacity - 1];
  if (last === "/") {
    return "unconscious";
  }
  return last === "X" ? "bleeding" : "dead";
}
