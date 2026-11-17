/** Textes d'un jet : composition de la réserve et résultat. */
import { fill, labels } from "@/shared/i18n";

import type { Roll, RollPart } from "./model";

type Named = Readonly<Record<string, string>>;

/** Nom affiché d'un élément de la réserve : trait de la fiche ou bonus. */
export function partLabel(key: string): string {
  const sources: readonly Named[] = [
    labels.attributes,
    labels.skills,
    labels.npcSheet.traits,
    labels.dice.parts,
  ];
  return sources.find((source) => key in source)?.[key] ?? key;
}

/** « Force 3 + Bagarre 2 − Blessures 1 ». */
export function describeParts(parts: readonly RollPart[]): string {
  return parts
    .map((part, index) => {
      const text = `${partLabel(part.key)} ${Math.abs(part.value)}`;
      if (index === 0) {
        return part.value < 0 ? `− ${text}` : text;
      }
      return `${part.value < 0 ? "−" : "+"} ${text}`;
    })
    .join(" ");
}

/** Nombre de réussites en toutes lettres. */
export function successesLabel(count: number): string {
  if (count === 0) {
    return labels.dice.successNone;
  }
  return count === 1 ? labels.dice.successOne : fill(labels.dice.successes, { count });
}

/** Résultat final : issue du jet, ou total d'initiative. */
export function resultLabel(roll: Roll): string {
  if (roll.total !== null) {
    return fill(labels.dice.initiativeTotal, { total: roll.total });
  }
  return roll.outcome === null
    ? successesLabel(roll.successes)
    : labels.dice.outcomes[roll.outcome];
}
