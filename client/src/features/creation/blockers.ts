/**
 * Raison qui empêche de passer à l'étape suivante de la création.
 *
 * Le bouton « Suivant » reste désactivé tant qu'une raison est renvoyée : on ne
 * peut pas créer une fiche incohérente.
 */
import { fill, labels } from "@/shared/i18n";

import { firstIncomplete, firstInvalidSpecialty, type TraitKind } from "./rules";
import { type CreationState, STEPS } from "./useCreationWizard";

function allocationBlocker(state: CreationState, kind: TraitKind): string | null {
  const incomplete = firstIncomplete(kind, state.priorities[kind], state.traits[kind]);
  if (incomplete === null) {
    return null;
  }
  const text = labels.creation.blockers;
  const category = labels.categories[incomplete.category];
  return Math.abs(incomplete.left) === 1
    ? fill(text.remainingOne, { category })
    : fill(text.remaining, { left: incomplete.left, category });
}

export function stepBlocker(state: CreationState): string | null {
  const text = labels.creation.blockers;
  switch (STEPS[state.step]) {
    case "identity":
      return state.identity.name.trim() === "" ? text.name : null;
    case "attributes":
      return allocationBlocker(state, "attributes");
    case "skills":
      return allocationBlocker(state, "skills");
    case "specialties": {
      const index = firstInvalidSpecialty(state.specialties, state.traits.skills);
      return index === null ? null : fill(text.specialty, { number: index + 1 });
    }
    default:
      return null;
  }
}
