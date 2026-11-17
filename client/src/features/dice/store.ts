/**
 * Jets à montrer sur la table, joués l'un après l'autre.
 *
 * Chaque vague reçue met à jour son jet. Tant qu'un jet est à l'écran, son
 * message reste masqué dans le chat : le résultat ne s'y affiche qu'une fois
 * l'animation terminée.
 */
import { create } from "zustand";

import type { Roll } from "./model";

interface DiceState {
  /** Jets en attente ou en cours d'affichage, le premier est à l'écran. */
  readonly queue: readonly Roll[];
  /** Jets dont le message de chat attend la fin de l'animation. */
  readonly hidden: ReadonlySet<string>;
  readonly receive: (roll: Roll) => void;
  /** Le jet à l'écran est terminé : il quitte la file et apparaît dans le chat. */
  readonly done: (rollId: string) => void;
  readonly reset: () => void;
}

export const useDiceStore = create<DiceState>()((set) => ({
  queue: [],
  hidden: new Set(),
  receive: (roll) =>
    set((state) => {
      const known = state.queue.some((entry) => entry.id === roll.id);
      const queue = known
        ? state.queue.map((entry) =>
            entry.id === roll.id && roll.stages.length >= entry.stages.length ? roll : entry,
          )
        : [...state.queue, roll];
      return { queue, hidden: new Set(state.hidden).add(roll.id) };
    }),
  done: (rollId) =>
    set((state) => {
      const hidden = new Set(state.hidden);
      hidden.delete(rollId);
      return { queue: state.queue.filter((entry) => entry.id !== rollId), hidden };
    }),
  reset: () => set({ queue: [], hidden: new Set() }),
}));
