/**
 * Résumés affichés sur les cartes du profil.
 */
import type { Character } from "@/features/characters/model";
import { fill, labels } from "@/shared/i18n";

/**
 * Résume les formes d'un personnage : « 2 formes : principale, Loup-garou ».
 * La forme principale vient toujours en premier.
 */
export function formsSummary(character: Character): string {
  const text = labels.profile.characters;
  const ordered = [...character.sheets].sort(
    (left, right) => Number(right.is_main) - Number(left.is_main),
  );
  const names = ordered
    .map((sheet) => (sheet.is_main ? text.mainForm : sheet.form_name))
    .join(", ");
  const count = ordered.length;
  return fill(count === 1 ? text.oneForm : text.manyForms, { count, names });
}

/**
 * Range les personnages pour l'affichage : celui qui est à la table d'abord,
 * puis les autres dans l'ordre reçu du serveur.
 */
export function playedFirst(characters: readonly Character[]): Character[] {
  return [...characters].sort((left, right) => Number(right.is_played) - Number(left.is_played));
}
