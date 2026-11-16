/** Garde des pages de l'accès MJ (composants serveur). */
import { notFound } from "next/navigation";

import { configuredGmAccessPath } from "./gmAccess";

/** Chemin public de l'accès MJ (`/…`). Répond 404 si l'accès n'est pas configuré. */
export function requireGmBasePath(): string {
  const value = configuredGmAccessPath();
  if (value === null) {
    notFound();
  }
  return `/${value}`;
}
