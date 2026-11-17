/**
 * Page de connexion réservée au MJ, côté serveur du client uniquement.
 *
 * Le MJ ouvre l'application par un chemin secret (`GM_ACCESS_PATH`). Le proxy
 * réécrit ce chemin vers le segment interne `INTERNAL_GM_SEGMENT`, qui n'est
 * pas accessible directement. Ce module ne dépend pas de Next.js : le proxy le
 * charge aussi.
 */
export const INTERNAL_GM_SEGMENT = "gm-gate";

const GM_ACCESS_PATH_PATTERN = /^[A-Za-z0-9-]{1,64}$/;

/** Retourne le chemin réservé configuré, ou `null` s'il est absent ou invalide. */
export function configuredGmAccessPath(): string | null {
  const value = process.env.GM_ACCESS_PATH ?? "";
  return GM_ACCESS_PATH_PATTERN.test(value) ? value : null;
}
