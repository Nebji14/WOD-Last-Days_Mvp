/** Point d'accès unique aux libellés de l'interface. */
import { fr } from "./fr";
import { frCreation } from "./fr-creation";
import { frImages } from "./fr-images";
import { frNpcs } from "./fr-npcs";
import { frPlayers } from "./fr-players";
import { frProfile } from "./fr-profile";
import { frSheet } from "./fr-sheet";

export const labels = {
  ...fr,
  ...frSheet,
  ...frCreation,
  ...frProfile,
  ...frPlayers,
  ...frImages,
  ...frNpcs,
};

export type ErrorLabelKey = keyof typeof fr.errors;
type RuleLabelKey = keyof typeof frSheet.sheet.rules;

/** Retourne le message à afficher pour un code d'erreur, connu ou non. */
export function errorLabel(code: string): string {
  return code in fr.errors ? fr.errors[code as ErrorLabelKey] : fr.errors.internal_error;
}

/** Retourne le message court expliquant la règle qui a refusé une saisie (05-E2). */
export function ruleLabel(rule: string): string {
  return rule in frSheet.sheet.rules
    ? frSheet.sheet.rules[rule as RuleLabelKey]
    : frSheet.sheet.rules.range;
}

/** Remplace les repères `{nom}` d'un libellé par leurs valeurs. */
export function fill(template: string, values: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) =>
    key in values ? String(values[key]) : match,
  );
}
