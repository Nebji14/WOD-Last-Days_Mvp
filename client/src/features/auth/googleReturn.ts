/**
 * Erreur rapportée par le serveur au retour de Google.
 *
 * La connexion Google se termine par une redirection vers la page de connexion
 * avec `?erreur=<code>` ; le MJ qui s'est trompé de page reçoit aussi
 * `acces=<chemin de sa page>`. Seuls les codes attendus sont repris, et le
 * chemin doit être un chemin simple du site (jamais une autre adresse).
 */
import { ApiError } from "@/shared/api/client";

const RETURNED_CODES = new Set([
  "google_failed",
  "invalid_credentials",
  "wrong_portal_gm",
  "wrong_portal_player",
  "rate_limited",
  "service_unavailable",
]);

const GM_PATH_PATTERN = /^\/[A-Za-z0-9-]{1,64}$/;

export type SearchParams = Readonly<Record<string, string | string[] | undefined>>;

function single(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

/** Retourne l'erreur à afficher, ou `null` si l'adresse n'en porte pas. */
export function googleReturnError(params: SearchParams): ApiError | null {
  const code = single(params.erreur);
  if (code === undefined || !RETURNED_CODES.has(code)) {
    return null;
  }
  const gmPath = single(params.acces);
  const details =
    code === "wrong_portal_gm" && gmPath !== undefined && GM_PATH_PATTERN.test(gmPath)
      ? [{ gm_access_path: gmPath }]
      : [];
  return new ApiError(0, code, details);
}
