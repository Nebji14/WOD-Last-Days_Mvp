/**
 * Résultat d'un aller-retour vers Google depuis le profil, lu dans `?google=…`.
 * Seules les valeurs attendues sont reprises.
 */
export type GoogleResult =
  { readonly kind: "linked" | "confirmed" } | { readonly kind: "error"; readonly code: string };

const ERROR_CODES = new Set([
  "google_failed",
  "google_already_linked",
  "rate_limited",
  "service_unavailable",
]);

export function parseGoogleResult(value: string | string[] | undefined): GoogleResult | null {
  if (value === "linked" || value === "confirmed") {
    return { kind: value };
  }
  return typeof value === "string" && ERROR_CODES.has(value)
    ? { kind: "error", code: value }
    : null;
}
