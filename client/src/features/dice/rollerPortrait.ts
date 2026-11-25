/** Photo montrée pendant un jet. */
import type { Seat } from "@/features/table/state";

import type { Roll } from "./model";

/**
 * Photo du personnage qui lance, prise sur son siège : elle est déjà visible de
 * toute la table. Pour un jet libre du MJ ou un PNJ, c'est celle du MJ : le
 * visage d'un PNJ reste secret. `null` sans photo.
 */
export function rollerPortrait(
  roll: Roll,
  seats: readonly Seat[],
  gmPortrait: string | null,
): string | null {
  const seat = seats.find(
    (candidate) => candidate.character !== null && candidate.character.id === roll.character_id,
  );
  if (seat !== undefined) {
    return seat.character?.portrait ?? null;
  }
  return roll.roller_role === "gm" ? gmPortrait : null;
}
