/** Appels API d'authentification. */
import { ApiError, apiRequest, isRecord } from "@/shared/api/client";

export type Role = "player" | "gm";

export interface Account {
  readonly id: string;
  readonly username: string;
  readonly displayName: string;
  readonly role: Role;
}

export interface Credentials {
  readonly username: string;
  readonly password: string;
}

/** Valide la forme d'un compte renvoyé par l'API. */
export function parseAccount(data: unknown): Account {
  if (
    isRecord(data) &&
    typeof data.id === "string" &&
    typeof data.username === "string" &&
    typeof data.display_name === "string" &&
    (data.role === "player" || data.role === "gm")
  ) {
    return {
      id: data.id,
      username: data.username,
      displayName: data.display_name,
      role: data.role,
    };
  }
  throw new ApiError(502, "internal_error");
}

/** Crée un compte joueur. N'ouvre pas de session. */
export function register(credentials: Credentials, passwordConfirmation: string): Promise<Account> {
  return apiRequest("/api/auth/register", {
    method: "POST",
    body: { ...credentials, password_confirmation: passwordConfirmation },
    parse: parseAccount,
  });
}

/** Connexion depuis la page des joueurs ou la page du MJ. */
export function login(credentials: Credentials, portal: Role): Promise<Account> {
  return apiRequest(portal === "gm" ? "/api/auth/gm/login" : "/api/auth/login", {
    method: "POST",
    body: credentials,
    parse: parseAccount,
  });
}

/** Ferme la session. */
export function logout(): Promise<void> {
  return apiRequest("/api/auth/logout", { method: "POST" });
}

/** Retourne le compte de la session en cours, ou `null` s'il n'y en a pas. */
export async function fetchCurrentAccount(): Promise<Account | null> {
  try {
    return await apiRequest("/api/auth/me", { parse: parseAccount });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return null;
    }
    throw error;
  }
}
