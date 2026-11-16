/**
 * Accès dédié du MJ (US-023, décision T-4), côté serveur du client uniquement.
 *
 * Le MJ ouvre l'application par un chemin réservé, défini par la variable
 * `GM_ACCESS_PATH`. Le proxy (src/proxy.ts) réécrit ce chemin vers le segment
 * interne `INTERNAL_GM_SEGMENT`, lui-même inaccessible directement.
 *
 * Ce module ne dépend pas de Next.js : il est aussi chargé par le proxy.
 */
export const INTERNAL_GM_SEGMENT = "gm-gate";

const GM_ACCESS_PATH_PATTERN = /^[A-Za-z0-9-]{1,64}$/;

/** Retourne le chemin réservé configuré, ou `null` s'il est absent ou invalide. */
export function configuredGmAccessPath(): string | null {
  const value = process.env.GM_ACCESS_PATH ?? "";
  return GM_ACCESS_PATH_PATTERN.test(value) ? value : null;
}
