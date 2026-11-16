/** Point d'accès unique aux libellés de l'interface. */
import { fr } from "./fr";

export const labels = fr;

export type ErrorLabelKey = keyof typeof fr.errors;

/** Retourne le message à afficher pour un code d'erreur, connu ou non. */
export function errorLabel(code: string): string {
  return code in fr.errors ? fr.errors[code as ErrorLabelKey] : fr.errors.internal_error;
}
