/**
 * Répartition des sièges autour de la table.
 *
 * Neuf emplacements : trois à gauche, trois à droite, trois en bas. Un
 * emplacement vide n'affiche rien.
 *
 * - Côté joueur : mon siège est toujours en bas au centre, les autres joueurs
 *   remplissent les huit emplacements restants.
 * - Côté MJ : le bas au centre est une place comme les autres.
 *
 * Les emplacements suivent l'ordre des places attribuées par le serveur : un
 * joueur garde le même emplacement tant qu'il garde sa place.
 */
import type { Seat } from "./state";

export type SeatSlot =
  | "left-1"
  | "left-2"
  | "left-3"
  | "right-1"
  | "right-2"
  | "right-3"
  | "bottom-left"
  | "bottom-center"
  | "bottom-right";

const SIDE_SLOTS: readonly SeatSlot[] = [
  "left-1",
  "right-1",
  "left-2",
  "right-2",
  "left-3",
  "right-3",
];
const PLAYER_VIEW_SLOTS: readonly SeatSlot[] = [...SIDE_SLOTS, "bottom-left", "bottom-right"];
const GM_VIEW_SLOTS: readonly SeatSlot[] = [
  ...SIDE_SLOTS,
  "bottom-center",
  "bottom-left",
  "bottom-right",
];

export interface PlacedSeat {
  readonly slot: SeatSlot;
  readonly seat: Seat;
  /** Siège du joueur qui regarde l'écran. */
  readonly mine: boolean;
}

/**
 * Attribue un emplacement d'écran à chaque siège.
 *
 * @param seats sièges diffusés par le serveur.
 * @param viewerAccountId compte du joueur qui regarde, ou `null` pour le MJ.
 */
export function arrangeSeats(seats: readonly Seat[], viewerAccountId: string | null): PlacedSeat[] {
  const ordered = [...seats].sort((a, b) => a.position - b.position);
  if (viewerAccountId === null) {
    return ordered.flatMap((seat, index) => {
      const slot = GM_VIEW_SLOTS[index];
      return slot ? [{ slot, seat, mine: false }] : [];
    });
  }
  const placed: PlacedSeat[] = [];
  let next = 0;
  for (const seat of ordered) {
    if (seat.accountId === viewerAccountId) {
      placed.push({ slot: "bottom-center", seat, mine: true });
      continue;
    }
    const slot = PLAYER_VIEW_SLOTS[next];
    next += 1;
    if (slot) {
      placed.push({ slot, seat, mine: false });
    }
  }
  return placed;
}

/** Initiales affichées dans un avatar : deux lettres au plus, en capitales. */
export function initials(name: string): string {
  const words = name.split(/[\s._-]+/).filter(Boolean);
  const letters =
    words.length >= 2 ? `${words[0]?.[0] ?? ""}${words[1]?.[0] ?? ""}` : name.slice(0, 2);
  return letters.toUpperCase();
}
