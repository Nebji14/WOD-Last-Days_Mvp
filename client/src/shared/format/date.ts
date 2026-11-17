/** Mise en forme des dates affichées dans l'interface (français). */

/** Date en toutes lettres : « 17 novembre 2026 ». */
export function longDate(date: Date): string {
  return date.toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });
}
