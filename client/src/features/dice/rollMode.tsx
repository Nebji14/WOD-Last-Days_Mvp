"use client";

/**
 * Mode jet de la fiche : un clic sur un trait l'ajoute à la réserve.
 *
 * Hors de ce mode, les noms des traits restent du texte simple.
 */
import { createContext, type ReactNode, useContext } from "react";

import type { AttributeName, SkillName } from "@/features/characters/model";

import type { NpcTrait, RollChoice } from "./pool";
import { pickTrait } from "./pool";

interface RollModeValue {
  readonly choice: RollChoice;
  readonly onChoice: (choice: RollChoice) => void;
}

const RollModeContext = createContext<RollModeValue | null>(null);
export const RollModeProvider = RollModeContext.Provider;

type Pickable =
  | { readonly kind: "trait"; readonly name: AttributeName | SkillName }
  | { readonly kind: "npc"; readonly name: NpcTrait };

const IDLE = "cursor-pointer rounded-xs px-1 -mx-1 outline-1 outline-dashed outline-gold/40";
const PICKED = "cursor-pointer rounded-xs px-1 -mx-1 bg-gold text-abyss";

/** Nom d'un trait : sélectionnable en mode jet, texte simple sinon. */
export function TraitPick({
  pick,
  className,
  children,
}: {
  readonly pick: Pickable;
  readonly className: string;
  readonly children: ReactNode;
}) {
  const mode = useContext(RollModeContext);
  if (mode === null) {
    return <span className={className}>{children}</span>;
  }
  const { choice, onChoice } = mode;
  const picked =
    pick.kind === "npc"
      ? choice.trait === pick.name
      : choice.attribute === pick.name || choice.second === pick.name;
  return (
    <button
      type="button"
      aria-pressed={picked}
      onClick={() =>
        onChoice(
          pick.kind === "npc"
            ? { ...choice, trait: picked ? null : pick.name, attribute: null, second: null }
            : pickTrait(choice, pick.name),
        )
      }
      className={`${className} text-left ${picked ? PICKED : IDLE}`}
    >
      {children}
    </button>
  );
}
